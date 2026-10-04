#!/usr/bin/env python3
"""H5, part 2: excess waiting time at five points along each route.

Reproduces section 2 and the route table of docs/even-spacing-2026-10-04.md. Run
from the repository root:

    python3 code/even_spacing_points.py

Input: analysis/spacing-*.csv.xz, written by code/spacing.py on the box. Same groups as h5.py: express
(G routes), trunk (the 25 busiest others by observed trips), rest. Same trips at
every point: only trips seen at all five points, main pattern per route-direction.
"""
import glob, sys
import numpy as np
import pandas as pd

SRC = sys.argv[1] if len(sys.argv) > 1 else "analysis"
OUT = sys.argv[2] if len(sys.argv) > 2 else "."
import os
PTS = [5, 25, 50, 75, 95]
rng = np.random.default_rng(1)
X = pd.concat([pd.read_csv(p, dtype={"vehicle": str, "route": str, "direction": str,
                                     "stop0": str, "stop1": str})
               for p in sorted(glob.glob(f"{SRC}/spacing-*.csv*"))], ignore_index=True)
X = X[(X.sched_5 >= 7 * 3600) & (X.sched_5 < 19 * 3600)]
# Buses and trolleybuses share route numbers (bus 7 and trolleybus 7 are different
# lines), so the line is named with its mode, read from the trip id's first letter.
X["route"] = X.trip_id.str[0].map({"A": "bus ", "T": "trolleybus "}).fillna("other ") + X.route.astype(str)
n_all = len(X)
X = X.dropna(subset=[f"passed_{k}" for k in PTS])
print(f"trips 07-19 seen at any point: {n_all}; at all five: {len(X)} ({len(X)/n_all:.0%})")
pat = X.groupby(["route", "direction", "stop0", "stop1"]).size().reset_index(name="n")
pat = pat.sort_values("n").groupby(["route", "direction"]).tail(1)
X = X.merge(pat[["route", "direction", "stop0", "stop1"]])
express = X.route.str.match(r"^bus \d+G")
busiest = X[~express].groupby("route").size().sort_values(ascending=False).head(25).index
X["group"] = np.where(express, "express", np.where(X.route.isin(busiest), "trunk", "rest"))


def waits(t, maxgap=5400):
    t = np.sort(np.asarray(t, float))
    g = np.diff(t)
    g = g[g <= maxgap]
    return (g ** 2).sum(), 2 * g.sum(), (g < 60).sum(), len(g)


recs = []
for (rt, dr, day), s in X.groupby(["route", "direction", "day"]):
    if len(s) < 10:
        continue
    r = {"route": rt, "dir": dr, "day": day, "group": s.group.iat[0], "n": len(s)}
    for k in PTS:
        for tag, col in [("S", f"sched_{k}"), ("A", f"passed_{k}")]:
            r[f"{tag}{k}_num"], r[f"{tag}{k}_den"], r[f"{tag}{k}_lt1"], r[f"{tag}{k}_g"] = waits(s[col])
    recs.append(r)
R = pd.DataFrame(recs)


def excess(df, k):
    S = df[f"S{k}_num"].sum() / df[f"S{k}_den"].sum() / 60
    A = df[f"A{k}_num"].sum() / df[f"A{k}_den"].sum() / 60
    return A - S, S


def boot(df, f, n=2000):
    days = df.day.unique()
    v = [f(pd.concat([df[df.day == d] for d in rng.choice(days, len(days))])) for _ in range(n)]
    return np.percentile(v, [2.5, 97.5])


print(f"route-direction-days: {len(R)}, trips {R.n.sum()}")
rows = []
for grp in ["express", "trunk", "rest"]:
    df = R[R.group == grp]
    line = [grp, df.route.nunique(), int(df.n.sum())]
    for k in PTS:
        e, S = excess(df, k)
        lo, hi = boot(df, lambda q, k=k: excess(q, k)[0])
        b = df[f"A{k}_lt1"].sum() / df[f"A{k}_g"].sum()
        rows.append({"group": grp, "point": k, "sched_wait": S, "excess": e, "lo": lo, "hi": hi,
                     "pct": e / S, "bunched_lt1min": b})
    mean_e = np.mean([excess(df, k)[0] for k in PTS])
    mean_s = np.mean([excess(df, k)[1] for k in PTS])
    lo, hi = boot(df, lambda q: np.mean([excess(q, k)[0] for k in PTS]))
    rows.append({"group": grp, "point": "mean of five", "sched_wait": mean_s, "excess": mean_e,
                 "lo": lo, "hi": hi, "pct": mean_e / mean_s, "bunched_lt1min": np.nan})
T = pd.DataFrame(rows)
pd.set_option("display.width", 200)
print(T.round(3).to_string(index=False))
T.to_csv(os.path.join(OUT, "even-spacing-points-summary.csv"), index=False)

P = []
for (rt, grp), df in R[R.group != "rest"].groupby(["route", "group"]):
    P.append({"route": rt, "group": grp, "trips": int(df.n.sum()),
              **{f"e{k}": excess(df, k)[0] for k in PTS},
              "sched_wait_50": excess(df, 50)[1]})
P = pd.DataFrame(P).sort_values("e50", ascending=False)
P.to_csv(os.path.join(OUT, "excess-wait-points-2026-10-04.csv"), index=False)
print(P.round(2).to_string(index=False))

# Mid-route excess by time of day, express and trunk (section 2 of the doc)
X["band"] = np.select([X.sched_50 < 9 * 3600, X.sched_50 < 16 * 3600, X.sched_50 < 19 * 3600],
                      ["07-09", "09-16", "16-19"], "19+")
print("\nexcess at the 50% point by time of day")
for (grp, band), df in X[X.group != "rest"].groupby(["group", "band"]):
    if band == "19+":
        continue
    a = np.zeros(4)
    for _, s in df.groupby(["route", "direction", "day"]):
        if len(s) < 4:
            continue
        n1, d1, _, _ = waits(s.passed_50)
        n2, d2, _, _ = waits(s.sched_50)
        a += [n1, d1, n2, d2]
    S, A = a[2] / a[3] / 60, a[0] / a[1] / 60
    print(f"  {grp:8s} {band}  scheduled wait {S:.2f} min, excess {A-S:+.2f} ({(A-S)/S:.0%})")

# The 18 September bunching shares, recomputed (section 5 of the doc): gaps under half
# and over double the route-direction's own median gap, 0.5 to 90 minutes, routes
# with at least 100 gaps, first sighting under the trip id against real positions.
import gzip, json
bl = sorted(glob.glob(f"{SRC}/blocks-*.json.gz"))
days = set(X.day)
B = pd.concat([pd.DataFrame(json.load(gzip.open(p)))[["trip_id", "day", "t0"]]
               for p in bl if p[-18:-8] in days])
Y = X.merge(B, on=["trip_id", "day"], how="left")
Y["first_seen"] = Y.t0 * 60
print("\nbunched (under half the median gap) and gapped (over double), share of gaps")
for col, label in [("first_seen", "first sighting, the 18 Sep method"), ("passed_5", "5% point"),
                   ("passed_50", "50% point"), ("passed_95", "95% point")]:
    for grp, df in Y.groupby("group"):
        G = []
        for _, s in df.groupby(["route", "direction"]):
            gg = []
            for _, q in s.groupby("day"):
                t = np.sort(q[col].dropna().values.astype(float))
                g = np.diff(t) / 60
                gg.append(g[(g >= 0.5) & (g <= 90)])
            gg = np.concatenate(gg)
            if len(gg) >= 100:
                G.append(pd.DataFrame({"g": gg, "med": np.median(gg)}))
        G = pd.concat(G)
        print(f"  {label:36s} {grp:8s} gaps {len(G):6d}  bunched {(G.g < 0.5 * G.med).mean():.1%}"
              f"  gapped {(G.g > 2 * G.med).mean():.1%}")
