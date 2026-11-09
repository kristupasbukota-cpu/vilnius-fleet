"""Route 61's early departures (docs/route-61-early-2026-10-02.md).

Rebuilt on 8 November 2026 from the method in that document; the original script
was never saved. Covers the departure tables of sections 1 and 2 (22 and 24 to 26
August) and of the 3 October update (21 September to 2 October). The turnaround and
end-of-trip figures in section 3 are not rebuilt here.

    python3 code/route_61_early.py [DEP_DIR]

DEP_DIR defaults to analysis/. Early means the deviation at the scheduled departure,
taken at both bays where a loop has two (the later reading wins), reads more than 60 s
ahead.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DEP = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("analysis")


def load(pattern):
    d = pd.concat(pd.read_csv(p, dtype={"route": str, "vehicle": str})
                  for p in sorted(DEP.glob(pattern)))
    d["both"] = np.where(d.dev_at_timing.notna() & (d.dev_at_timing != d.dev_at_departure),
                         np.maximum(d.dev_at_departure, d.dev_at_timing), d.dev_at_departure)
    d = d[d["both"].notna()].copy()
    d["early"] = d["both"] < -60
    d["block"] = d["trip_id"].str.split("-").str[:3].str.join("-")
    return d


def summary(d, label):
    print(f"\n=== {label}")
    print(f"network: {len(d):,} departures, {d.early.mean():.2%} early > 60 s")
    rd = d.groupby(["route", "direction"]).early.agg(["size", "mean"])
    for dirn in (0, 1):
        n, m = rd.loc[("61", dirn)]
        print(f"route 61 direction {dirn}: {int(n)} departures, {m:.1%} early")
    big = rd[rd["size"] >= 300].sort_values("mean", ascending=False)
    print("worst route-directions with 300+ departures:")
    for (r, dr), row in big.head(3).iterrows():
        print(f"  {r} direction {dr}: {int(row['size'])}, {row['mean']:.1%}")
    r = d[(d.route == "61") & (d.direction == 1)]
    print("route 61 direction 1 by vehicle:")
    g = r.groupby("vehicle").agg(days=("day", "nunique"), deps=("early", "size"),
                                 early=("early", "sum"), median_dev=("both", "median"))
    print(g.sort_values("deps", ascending=False).to_string())
    print("early departures by vehicle and day:")
    for v, x in r.groupby("vehicle"):
        print(f"  {v}: " + ", ".join(str(int(s)) for s in x.groupby("day").early.sum()))
    e = r[r.early]
    print(f"early cases: median {e.both.median():.0f} s, middle half "
          f"{e.both.quantile(.25):.0f} to {e.both.quantile(.75):.0f} s, "
          f"range {e.both.min():.0f} to {e.both.max():.0f} s")
    print("blocks on direction 1: " + ", ".join(sorted(r.block.unique())))
    return r


aug = load("dep-2026-08-2*.csv.*")
r = summary(aug, "August: 22 and 24 to 26 August")
same = r[r.block.isin(["A61-01-1", "A61-02-1"])]
print("same two blocks, by vehicle:")
print(same.groupby("vehicle").early.agg(["size", "sum"]).to_string())
for v in ("7020", "7003"):
    x = aug[aug.vehicle == v]
    other = x[~((x.route == "61") & (x.direction == 1))]
    print(f"{v} elsewhere: " + "; ".join(
        f"route {rt} dir {dr} {g.early.mean():.0%} of {len(g)}"
        for (rt, dr), g in other.groupby(["route", "direction"])))

aut = load("dep-2026-09-*.csv.*")
aut = pd.concat([aut, load("dep-2026-10-0*.csv.*")])
summary(aut, "Autumn: 21 September to 2 October")
for v in ("7020", "7003"):
    x = aut[(aut.vehicle == v) & (aut.route != "61")]
    print(f"{v} on other routes: " + "; ".join(
        f"route {rt} {int(g.early.sum())} of {len(g)}" for rt, g in x.groupby("route")))
