"""RehaKnee host server. Reads the brace over USB serial (or a simulator), runs core.py,
serves the dashboard and a live Server-Sent Events stream. Stdlib only, plus pyserial for the brace.

    python3 server.py --sim                 # no hardware
    python3 server.py                       # auto-detect the Arduino
    python3 server.py --serial /dev/ttyACM0
"""
import argparse
import csv
import json
import os
import pickle
import queue
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import core

ROOT = os.path.dirname(os.path.abspath(__file__))
SESSIONS = os.path.join(ROOT, "sessions")
PROFILES = os.path.join(ROOT, "profiles.json")
MODEL = os.path.join(ROOT, "model.pkl")
HAPTIC = {"target": 1, "hold": 10, "set_done": 14}  # DRV2605 ERM library effects: click, double click, buzz
CALIB_SAMPLES = 200  # 2 s at 100 Hz
PROFILE_FIELDS = {"target_deg": float, "tol_deg": float, "hold_s": float,
                  "min_ext_s": float, "min_ret_s": float, "reps": int}


def clean_profile(p):
    out = {"name": str(p.get("name", "Custom"))[:60] or "Custom"}
    for k, typ in PROFILE_FIELDS.items():
        v = typ(p[k])
        if not 0 <= v <= 360:
            raise ValueError(f"{k} out of range")
        out[k] = v
    if out["target_deg"] < 10 or out["reps"] < 1:
        raise ValueError("target must be >= 10 deg and reps >= 1")
    return out


class Brace:
    """All live state. One brace, one user. ponytail: a single lock, fine at 100 Hz."""

    def __init__(self, source):
        self.lock = threading.Lock()
        self.source = source
        self.connected = source == "sim"
        self.send = lambda cmd: None  # replaced by the serial/sim source
        self.sim_style = "controlled"
        self.filt = core.TiltFilter()
        self.calib_buf = None
        self.calibration = None
        self.counter = None
        self.session = None
        self.model = None
        self.clients = []
        self.last_t = None
        self.n = 0

    # --- streaming --------------------------------------------------------------------
    def broadcast(self, msg):
        data = json.dumps(msg)
        for q in list(self.clients):
            try:
                q.put_nowait(data)
            except queue.Full:
                pass

    def status(self):
        return {"type": "status", "source": self.source, "connected": self.connected,
                "calibrated": self.calibration is not None, "calibration": self.calibration,
                "calibrating": self.calib_buf is not None, "recording": self.session is not None,
                "session": self.session and {k: self.session[k] for k in ("id", "profile", "label")},
                "reps": self.counter.reps if self.session else [],
                "sim_style": self.sim_style, "model": self.model is not None}

    def set_connected(self, ok):
        self.connected = ok
        self.broadcast(self.status())

    def on_sample(self, row):
        t = row[0] / 1000
        with self.lock:
            dt = 0.0 if self.last_t is None else min(max(t - self.last_t, 0.0), 0.05)
            self.last_t = t
            if self.calib_buf is not None:
                self.calib_buf.append(row)
                if len(self.calib_buf) >= CALIB_SAMPLES:
                    self.calibration = self.filt.calibrate(self.calib_buf)
                    self.calib_buf = None
                    self.broadcast(self.status())
                return
            if self.filt.g0 is None:
                return
            angle = self.filt.update(t, row[1:4], row[4:7], dt)
            if self.session:
                self.session["raw"].append((*row, round(angle, 2)))
                for ev in self.counter.update(t, angle):
                    if ev in HAPTIC:
                        self.buzz(HAPTIC[ev], t)
                        self.broadcast({"type": "event", "event": ev})
                    if ev == "rep":
                        rep = self.counter.reps[-1]
                        rep["n"] = len(self.counter.reps)
                        rep["label"] = self.session["label"]
                        rep["ai"] = self.predict(rep)
                        self.broadcast({"type": "rep", "rep": rep})
            self.n += 1
            if self.n % 4 == 0:  # 25 Hz to the browser is plenty
                hold = self.counter.hold_elapsed(t) if self.session else 0
                self.broadcast({"type": "live", "t": t, "angle": round(angle, 1), "hold": round(hold, 2)})

    def buzz(self, effect, t=None):
        self.send(f"B{effect}\n")
        if t is not None:
            self.filt.mute_until = t + 0.5  # the motor shakes the accelerometer

    def predict(self, rep):
        if not self.model:
            return None
        clf = self.model["model"]
        proba = clf.predict_proba([rep["features"]])[0]
        i = max(range(len(proba)), key=proba.__getitem__)
        return {"label": clf.classes_[i], "conf": round(float(proba[i]), 2)}

    # --- commands -----------------------------------------------------------------------
    def calibrate(self):
        with self.lock:
            if self.session:
                raise ValueError("stop the set before recalibrating")
            self.calib_buf = []
        self.broadcast(self.status())

    def start(self, profile, label):
        if label not in core.LABELS:
            label = None
        with self.lock:
            if self.calibration is None:
                raise ValueError("calibrate first")
            if self.session:
                raise ValueError("a set is already running")
            self.model = None
            if os.path.exists(MODEL):
                try:
                    with open(MODEL, "rb") as f:  # our own file, written by train.py
                        self.model = pickle.load(f)
                except Exception as e:  # sklearn missing or version mismatch: rules still work
                    print("model not loaded:", e)
            self.counter = core.RepCounter(profile)
            self.session = {"id": time.strftime("%Y%m%d-%H%M%S"), "started": time.time(),
                            "profile": profile, "label": label, "source": self.source,
                            "calibration": self.calibration, "raw": []}
        self.broadcast(self.status())

    def stop(self):
        with self.lock:
            s, self.session = self.session, None
            if not s:
                raise ValueError("no set running")
            reps = self.counter.reps
        os.makedirs(SESSIONS, exist_ok=True)
        with open(os.path.join(SESSIONS, s["id"] + ".csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["t_ms", "ax", "ay", "az", "gx", "gy", "gz", "angle"])
            w.writerows(s.pop("raw"))
        s.update(ended=time.time(), reps=reps, summary=core.summarize(reps))
        with open(os.path.join(SESSIONS, s["id"] + ".json"), "w") as f:
            json.dump(s, f, indent=1)
        self.broadcast(self.status())
        return s


# --- sources ----------------------------------------------------------------------------
def run_sim(brace):
    brace.send = lambda cmd: print("haptic", cmd.strip())
    t0 = time.time()
    for i, (row, _) in enumerate(core.sim_stream(lambda: brace.sim_style if brace.session else None)):
        brace.on_sample(row)
        delay = t0 + (i + 1) / 100 - time.time()
        if delay > 0:
            time.sleep(delay)


def find_port():
    from serial.tools import list_ports
    for p in list_ports.comports():
        if p.vid == 0x2341 or "usbmodem" in p.device or "ttyACM" in p.device:
            return p.device
    raise IOError("no Arduino found (plug it in, or pass --serial PORT)")


def run_serial(brace, port):
    import serial
    while True:  # reconnect forever: cables get yanked during demos
        try:
            with serial.Serial(port or find_port(), 115200, timeout=1) as ser:
                print("connected", ser.port)
                brace.send = lambda cmd: ser.write(cmd.encode())
                brace.set_connected(True)
                for line in ser:
                    line = line.decode(errors="ignore").strip()
                    if not line or line[0] == "#":
                        if line:
                            print("arduino:", line)
                        continue
                    parts = line.split(",")
                    if len(parts) != 7:
                        continue
                    try:
                        row = (int(parts[0]), *(float(x) for x in parts[1:]))
                    except ValueError:
                        continue
                    brace.on_sample(row)
        except Exception as e:
            print("serial:", e)
        brace.send = lambda cmd: None
        brace.set_connected(False)
        time.sleep(1)


# --- http -------------------------------------------------------------------------------
def load_profiles():
    with open(PROFILES) as f:
        return json.load(f)


def list_sessions():
    out = []
    if os.path.isdir(SESSIONS):
        for name in sorted(os.listdir(SESSIONS)):
            if name.endswith(".json"):
                with open(os.path.join(SESSIONS, name)) as f:
                    s = json.load(f)
                out.append({k: s.get(k) for k in ("id", "started", "profile", "label", "source", "summary")})
    return out


class Handler(SimpleHTTPRequestHandler):
    brace = None

    def __init__(self, *a, **k):
        super().__init__(*a, directory=os.path.join(ROOT, "static"), **k)

    def log_message(self, *a):
        pass

    def reply(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/events":
            return self.events()
        if self.path == "/api/profiles":
            return self.reply(load_profiles())
        if self.path == "/api/sessions":
            return self.reply(list_sessions())
        if self.path.startswith("/api/sessions/"):
            path = os.path.join(SESSIONS, os.path.basename(self.path) + ".json")
            if not os.path.isfile(path):
                return self.reply({"error": "not found"}, 404)
            with open(path) as f:
                return self.reply(json.load(f))
        super().do_GET()

    def do_POST(self):
        b = self.brace
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
            if self.path == "/api/calibrate":
                b.calibrate()
            elif self.path == "/api/start":
                b.start(clean_profile(body["profile"]), body.get("label"))
            elif self.path == "/api/stop":
                s = b.stop()
                return self.reply({"id": s["id"], "summary": s["summary"]})
            elif self.path == "/api/profiles":
                p = clean_profile(body)
                profiles = [x for x in load_profiles() if x["name"] != p["name"]] + [p]
                with open(PROFILES, "w") as f:
                    json.dump(profiles, f, indent=1)
                return self.reply(profiles)
            elif self.path == "/api/sim":
                if body.get("style") not in core.SIM_STYLES:
                    raise ValueError("unknown style")
                b.sim_style = body["style"]
                b.broadcast(b.status())
            elif self.path == "/api/buzz":  # hardware test button
                b.buzz(int(body.get("effect", 1)))
            else:
                return self.reply({"error": "not found"}, 404)
            return self.reply({"ok": True})
        except (ValueError, KeyError, TypeError) as e:
            return self.reply({"error": str(e)}, 400)

    def events(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        q = queue.Queue(maxsize=500)
        self.brace.clients.append(q)
        q.put(json.dumps(self.brace.status()))
        try:
            while True:
                try:
                    self.wfile.write(f"data: {q.get(timeout=15)}\n\n".encode())
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            self.brace.clients.remove(q)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim", action="store_true", help="simulated brace, no hardware")
    ap.add_argument("--serial", help="serial port (default: auto-detect)")
    ap.add_argument("--port", type=int, default=8000, help="http port")
    args = ap.parse_args()

    brace = Brace("sim" if args.sim else "serial")
    target = run_sim if args.sim else (lambda b: run_serial(b, args.serial))
    threading.Thread(target=target, args=(brace,), daemon=True).start()

    Handler.brace = brace
    ThreadingHTTPServer.daemon_threads = True
    srv = ThreadingHTTPServer(("0.0.0.0", args.port), Handler)
    print(f"RehaKnee on http://localhost:{args.port}  ({brace.source})")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
