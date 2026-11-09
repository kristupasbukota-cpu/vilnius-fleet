"""Lateness belongs to roads, not to vehicles or routes (docs/roads-not-vehicles-2026-10-02.md).

Rebuilt on 8 November 2026 from the method in that document; the original script
was never saved.

    python3 code/roads_not_vehicles.py [TRAV_DIR]

TRAV_DIR defaults to analysis/. Reads analysis/trav-YYYY-MM-DD.csv.gz for the 18
autumn working days, Monday to Thursday, 2 September to 1 October 2026.

How much of the difference between links, routes and vehicles repeats: the days are
split into two alternating halves in date order, each unit gets a mean in each half,
and the covariance of those means across units is the variance of the lasting
effect. Its square root is the lasting spread in seconds per hop. Intervals are a
bootstrap over units.
"""
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

TRAV = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("analysis")
START, END = date(2026, 9, 2), date(2026, 10, 1)
MIN_LINK, MIN_UNIT = 30, 500
BOOT = 1000
rng = np.random.default_rng(20261002)

days = []
d = START
while d <= END:
    if d.weekday() <= 3:          # Monday to Thursday
        days.append(d.isoformat())
    d += timedelta(days=1)

cols = ["day", "vehicle", "trip_id", "route", "direction", "stop_from_id", "stop_to_id",
        "hour_local", "sched_s", "lost_s"]
frames = []
for day in days:
    f = pd.read_csv(TRAV / f"trav-{day}.csv.gz", usecols=cols,
                    dtype={"vehicle": str, "route": str})
    frames.append(f[f["day"] == day])
h = pd.concat(frames, ignore_index=True).dropna(subset=["lost_s"])
h["half"] = h["day"].map({x: i % 2 for i, x in enumerate(days)})
h["link"] = h["stop_from_id"].astype(str) + ">" + h["stop_to_id"].astype(str)
# A route is its mode and number (trolleybus 2 and bus 2 are different routes), which
# is the first part of the trip id: T2, A2, A2G.
h["mode_route"] = h["trip_id"].str.split("-").str[0]
h["rd"] = h["mode_route"] + "/" + h["direction"].astype(str)
print(f"{len(days)} days, {len(h):,} hops")


def lasting(df, unit, value, min_n):
    """Per-unit means in each half; covariance across units, r, bootstrap CI."""
    g = df.groupby(unit + ["half"])[value].agg(["mean", "size"]).unstack("half")
    g = g[(g[("size", 0)] >= min_n) & (g[("size", 1)] >= min_n)]
    a, b = g[("mean", 0)].to_numpy(), g[("mean", 1)].to_numpy()

    def spread(x, y):
        c = np.cov(x, y)[0, 1]
        return np.sign(c) * np.sqrt(abs(c))

    est = spread(a, b)
    idx = rng.integers(0, len(a), size=(BOOT, len(a)))
    boots = np.array([spread(a[i], b[i]) for i in idx])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return len(a), np.corrcoef(a, b)[0, 1], est, lo, hi


rows = []
rows.append(("the road: a link at a given hour",
             *lasting(h, ["link", "hour_local"], "lost_s", MIN_LINK)))

# Hold the road, the hour and the day fixed: each hop's difference from its cell mean.
cell = ["link", "hour_local", "day"]
h["cell_n"] = h.groupby(cell)["lost_s"].transform("size")
c = h[h["cell_n"] >= 2].copy()
c["resid"] = c["lost_s"] - c.groupby(cell)["lost_s"].transform("mean")
c["sched_resid"] = c["sched_s"] - c.groupby(cell)["sched_s"].transform("mean")

# Routes: only cells shared by more than one route-direction.
c["cell_rds"] = c.groupby(cell)["rd"].transform("nunique")
shared = c[c["cell_rds"] >= 2]
rows.append(("the route and direction, shared links",
             *lasting(shared, ["rd"], "resid", MIN_UNIT)))

rows.append(("the vehicle, same link, hour and day",
             *lasting(c, ["vehicle"], "resid", MIN_UNIT)))

# Vehicles with each route-direction's own effect (its mean residual in that half) removed.
c["resid_nr"] = c["resid"] - c.groupby(["rd", "half"])["resid"].transform("mean")
rows.append(("the vehicle, routes' effects removed",
             *lasting(c, ["vehicle"], "resid_nr", MIN_UNIT)))

print()
print(f"{'what is compared':40s} {'units':>7s} {'r':>6s} {'spread s':>9s}  95% CI")
for name, n, r, est, lo, hi in rows:
    print(f"{name:40s} {n:7,d} {r:6.2f} {est:9.1f}  [{lo:.1f}, {hi:.1f}]")

# Checks quoted in the text.
print()
print(f"hop residual vs scheduled-time residual: r = "
      f"{np.corrcoef(c['resid'], c['sched_resid'])[0, 1]:.2f}")
for m, name in (("T", "trolleybus"), ("A", "bus")):
    print(f"{name}es against their neighbours: {c.loc[c['mode_route'].str[0] == m, 'resid'].mean():+.2f} s")
rd_per_vehicle = c.groupby("vehicle")["rd"].nunique()
print(f"route-directions per vehicle, median: {rd_per_vehicle.median():.0f}")
tot = h["lost_s"].var()
cellmean = h.groupby(cell)["lost_s"].transform("mean")
print(f"share of single-hop variance that is link x hour x day: {cellmean.var() / tot:.0%}")
