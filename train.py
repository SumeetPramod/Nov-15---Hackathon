"""Train the per-rep movement classifier from labelled sets in sessions/.

Record sets with a training label (controlled / short / rushed) in the dashboard, then:
    python3 train.py
Held-out test = ~20% of whole sessions per label, so reps from one recording never sit
on both sides of the split. Prints test metrics, then refits on everything -> model.pkl.
The server picks up model.pkl at the next "Start set".
"""
import glob
import json
import os
import pickle
import random
import sys
from collections import defaultdict

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

import core

ROOT = os.path.dirname(os.path.abspath(__file__))

sessions = defaultdict(list)  # label -> [(session_id, X, y)]
for path in sorted(glob.glob(os.path.join(ROOT, "sessions", "*.json"))):
    with open(path) as f:
        s = json.load(f)
    if s.get("label") in core.LABELS and s.get("reps"):
        sessions[s["label"]].append((s["id"], [r["features"] for r in s["reps"]], [s["label"]] * len(s["reps"])))

for lab in core.LABELS:
    print(f"{lab:10s} {len(sessions[lab])} sessions, {sum(len(x[1]) for x in sessions[lab])} reps")
missing = [lab for lab in core.LABELS if len(sessions[lab]) < 2]
if missing:
    sys.exit(f"need at least 2 labelled sessions for each label; short on: {', '.join(missing)}")

rnd = random.Random(0)
train, test = [], []
for lab, group in sessions.items():
    rnd.shuffle(group)
    k = max(1, round(0.2 * len(group)))
    test += group[:k]
    train += group[k:]


def stack(groups):
    return [x for g in groups for x in g[1]], [y for g in groups for y in g[2]]


Xtr, ytr = stack(train)
Xte, yte = stack(test)
clf = RandomForestClassifier(n_estimators=200, random_state=0).fit(Xtr, ytr)
pred = clf.predict(Xte)
print(f"\ntrain {len(train)} sessions / {len(Xtr)} reps, test {len(test)} sessions / {len(Xte)} reps")
print("test sessions:", ", ".join(g[0] for g in test))
print(classification_report(yte, pred, labels=core.LABELS, zero_division=0))
print("confusion (rows = true, cols = predicted):", core.LABELS)
print(confusion_matrix(yte, pred, labels=core.LABELS))
print("\nfeature importance:")
for name, imp in sorted(zip(core.FEATURES, clf.feature_importances_), key=lambda x: -x[1]):
    print(f"  {name:10s} {imp:.2f}")

X, y = stack(train + test)
final = RandomForestClassifier(n_estimators=200, random_state=0).fit(X, y)
with open(os.path.join(ROOT, "model.pkl"), "wb") as f:
    pickle.dump({"model": final, "features": core.FEATURES}, f)
print("\nwrote model.pkl (refit on all sessions)")
