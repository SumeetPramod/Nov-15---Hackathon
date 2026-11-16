"""RehaKnee signal processing: tilt filter, rep detection, per-rep metrics, simulator.
Run `python3 core.py` for the self-check."""
import math
import random

FEATURES = ["peak_deg", "ext_s", "hold_s", "ret_s", "peak_vel", "mean_vel"]
LABELS = ["controlled", "short", "rushed"]


def norm(v):
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


class TiltFilter:
    """Tracks the gravity direction in the sensor frame (complementary filter).
    Angle = rotation away from the calibrated rest pose, so the sensor axes
    don't need to line up with the knee hinge. Rotation about the vertical
    (thigh twist) is invisible to it, which is what we want."""

    ALPHA = 0.98  # gyro trust per sample at 100 Hz, ~0.5 s time constant; tune if laggy/noisy

    def __init__(self):
        self.g0 = self.g = None
        self.bias = [0.0, 0.0, 0.0]
        self.mute_until = 0.0  # accel is ignored until this time (motor buzzing)

    def calibrate(self, rows):
        """rows: (t_ms, ax, ay, az, gx, gy, gz) recorded while the leg is still at rest."""
        n = len(rows)
        mean = [sum(r[i] for r in rows) / n for i in range(1, 7)]
        gyro_std = max(math.sqrt(sum((r[i] - mean[i - 1]) ** 2 for r in rows) / n) for i in (4, 5, 6))
        self.bias = mean[3:]
        self.g0 = norm(mean[:3])
        self.g = list(self.g0)
        return {"g0": self.g0, "gyro_bias": self.bias, "gyro_std": round(gyro_std, 3),
                "accel_g": round(math.sqrt(sum(x * x for x in mean[:3])), 3), "still": gyro_std < 3.0}

    def update(self, t, a, w, dt):
        g = self.g
        wx, wy, wz = (math.radians(w[i] - self.bias[i]) for i in range(3))
        # a world-fixed vector seen from a rotating body: dg/dt = -w x g
        g = [g[0] - dt * (wy * g[2] - wz * g[1]),
             g[1] - dt * (wz * g[0] - wx * g[2]),
             g[2] - dt * (wx * g[1] - wy * g[0])]
        amag = math.sqrt(sum(x * x for x in a))
        if t >= self.mute_until and abs(amag - 1.0) < 0.15:  # skip accel while buzzing / jerking
            g = [self.ALPHA * g[i] + (1 - self.ALPHA) * a[i] / amag for i in range(3)]
        self.g = norm(g)
        d = max(-1.0, min(1.0, sum(self.g[i] * self.g0[i] for i in range(3))))
        # ponytail: unsigned, so bending back past the rest pose also reads positive
        return math.degrees(math.acos(d))


def start_threshold(p):
    return min(10.0, 0.3 * p["target_deg"])


def rep_metrics(trace, p):
    """trace: [(t_s, angle_deg)] from leaving rest to returning. None if it was just noise."""
    t = [x[0] for x in trace]
    a = [x[1] for x in trace]
    peak = max(a)
    if peak < 1.5 * start_threshold(p) or t[-1] - t[0] < 0.5:
        return None
    hi = 0.9 * peak
    i_up = next(i for i, x in enumerate(a) if x >= hi)
    i_dn = max(i for i, x in enumerate(a) if x >= hi)
    i_end = max(i for i, x in enumerate(a) if x > start_threshold(p))
    band = p["target_deg"] - p["tol_deg"]
    hold, t0 = 0.0, None  # longest continuous time inside the target band
    for ti, x in trace:
        if x >= band:
            t0 = ti if t0 is None else t0
            hold = max(hold, ti - t0)
        else:
            t0 = None
    k = 5  # velocity over 5 samples to keep differencing noise down
    vel = [abs(a[i + k] - a[i]) / (t[i + k] - t[i]) for i in range(len(a) - k) if t[i + k] > t[i]] or [0.0]
    rep = {
        "peak_deg": round(peak, 1),
        # ext/ret are both timed between the rest threshold (<=10 deg) and 90% of peak
        "ext_s": round(t[i_up] - t[0], 2),
        "hold_s": round(hold, 2),
        "ret_s": round(t[i_end] - t[i_dn], 2),
        "peak_vel": round(max(vel), 1),
        "mean_vel": round(sum(vel) / len(vel), 1),
        "t_start": t[0],
    }
    rep["features"] = [rep[f] for f in FEATURES]
    rep["reached"] = peak >= band
    rep["held"] = hold >= p["hold_s"]
    rep["paced"] = rep["ext_s"] >= p["min_ext_s"] and rep["ret_s"] >= p["min_ret_s"]
    rep["verdict"] = ("short" if not rep["reached"] else "rushed" if not rep["paced"]
                      else "short hold" if not rep["held"] else "good")
    return rep


class RepCounter:
    """Streaming rep detector. update() returns events: target, hold, rep, set_done."""

    def __init__(self, profile):
        self.p = profile
        self.reps = []
        self.trace = None
        self.hold_t0 = None
        self.reached = self.held = False

    def hold_elapsed(self, t):
        return t - self.hold_t0 if self.hold_t0 is not None else 0.0

    def update(self, t, a):
        p, ev = self.p, []
        start = start_threshold(p)
        if self.trace is None:
            if a <= start:
                return ev
            self.trace, self.hold_t0, self.reached, self.held = [], None, False, False
        self.trace.append((t, a))
        if a >= p["target_deg"] - p["tol_deg"]:
            if not self.reached:
                self.reached = True
                ev.append("target")
            if self.hold_t0 is None:
                self.hold_t0 = t
            if not self.held and t - self.hold_t0 >= p["hold_s"]:
                self.held = True
                ev.append("hold")
        else:
            self.hold_t0 = None
        if a < 0.7 * start:  # hysteresis so noise at the threshold doesn't split a rep
            rep = rep_metrics(self.trace, p)
            self.trace, self.hold_t0 = None, None
            if rep:
                self.reps.append(rep)
                ev.append("rep")
                if len(self.reps) == p["reps"]:
                    ev.append("set_done")
        return ev


def summarize(reps):
    if not reps:
        return {"reps": 0}

    def mean(k):
        return sum(r[k] for r in reps) / len(reps)

    def sd(k):
        m = mean(k)
        return math.sqrt(sum((r[k] - m) ** 2 for r in reps) / len(reps))

    return {
        "reps": len(reps),
        "mean_peak": round(mean("peak_deg"), 1), "sd_peak": round(sd("peak_deg"), 1),
        "mean_ext": round(mean("ext_s"), 2), "sd_ext": round(sd("ext_s"), 2),
        "mean_hold": round(mean("hold_s"), 2), "mean_ret": round(mean("ret_s"), 2),
        "pct_reached": round(100 * sum(r["reached"] for r in reps) / len(reps)),
        "pct_good": round(100 * sum(r["verdict"] == "good" for r in reps) / len(reps)),
    }


# --- simulator: stands in for the brace until the hardware is ready -------------------------

SIM_STYLES = {  # peak deg, extend s, hold s, return s
    "controlled": (65, 2.5, 3.0, 2.5),
    "short": (40, 2.5, 2.0, 2.5),
    "rushed": (60, 0.6, 0.3, 0.6),
}


def sim_stream(get_style, hz=100, seed=None):
    """Yields ((t_ms, ax, ay, az, gx, gy, gz), true_angle) forever. Starts with ~2 s of rest.
    The sensor is mounted rotated 30 deg off the hinge to prove the filter doesn't care."""
    rnd = random.Random(seed)
    dt, t, prev = 1.0 / hz, 0.0, 0.0
    bias = (0.8, -0.5, 0.3)
    c, s = math.cos(math.radians(30)), math.sin(math.radians(30))

    def mount(v):
        return (c * v[0] - s * v[1], s * v[0] + c * v[1], v[2])

    while True:
        style = get_style()  # None = leg resting
        peak, ext, hold, ret = (x * rnd.uniform(0.9, 1.1) for x in SIM_STYLES[style or "controlled"])
        segs = ((rnd.uniform(1.8, 2.5), 0, 0), (ext, 0, 1), (hold, 1, 1), (ret, 1, 0)) if style else ((0.1, 0, 0),)
        for dur, f0, f1 in segs:
            n = max(1, int(dur * hz))
            for k in range(n):
                th = peak * (f0 + (f1 - f0) * (1 - math.cos(math.pi * k / n)) / 2)
                r = math.radians(th)
                acc = mount((0.0, math.sin(r), math.cos(r)))
                gyr = mount(((th - prev) / dt, 0.0, 0.0))
                prev = th
                row = (round(t * 1000),
                       *(x + rnd.gauss(0, 0.01) for x in acc),
                       *(x + b + rnd.gauss(0, 0.3) for x, b in zip(gyr, bias)))
                yield row, th
                t += dt


def _selfcheck():
    prof = {"target_deg": 60, "tol_deg": 5, "hold_s": 2, "min_ext_s": 1.0, "min_ret_s": 1.0, "reps": 5}
    expect = {"controlled": "good", "short": "short", "rushed": "rushed"}
    for style, verdict in expect.items():
        gen = sim_stream(lambda: style, seed=1)
        rest = [next(gen)[0] for _ in range(150)]
        f = TiltFilter()
        assert f.calibrate(rest)["still"]
        rc, err, last, events = RepCounter(prof), 0.0, rest[-1][0] / 1000, []
        while len(rc.reps) < 5:
            row, true = next(gen)
            t = row[0] / 1000
            ang = f.update(t, row[1:4], row[4:7], t - last)
            last = t
            err = max(err, abs(ang - true))
            events += rc.update(t, ang)
        assert err < 3.0, (style, err)
        got = [r["verdict"] for r in rc.reps]
        assert got == [verdict] * 5, (style, got)
        assert events.count("set_done") == 1
        assert events.count("target") == (5 if style != "short" else 0), (style, events)
        print(f"{style:10s} max err {err:.2f} deg  verdicts {got[0]}  {summarize(rc.reps)}")
    print("core self-check OK")


if __name__ == "__main__":
    _selfcheck()
