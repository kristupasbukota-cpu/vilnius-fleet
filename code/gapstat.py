#!/usr/bin/env python3
"""Measure the real gap between consecutive snapshots, hour by hour.

The watchdog needs to know how long a silence has to last before it means
something. Guessing that number is how you get an alarm at 03:00 every night for
a fleet that is simply parked. So measure it: the worst gap actually observed in
each local hour, across the whole archive, excluding the hours the collector was
genuinely down.
"""
import glob, os, collections
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
TZ = timedelta(hours=3)

ts = sorted(datetime.strptime(os.path.basename(p).split(".")[0], "%Y%m%dT%H%M%SZ")
            .replace(tzinfo=timezone.utc)
            for p in glob.glob(os.path.join(HERE, "snapshots", "*.csv.gz")))
print(f"{len(ts)} snapshots, {ts[0]:%Y-%m-%d %H:%M} to {ts[-1]:%Y-%m-%d %H:%M} UTC\n")

byhour = collections.defaultdict(list)
for a, b in zip(ts, ts[1:]):
    byhour[(a + TZ).hour].append((b - a).total_seconds())

print("local hour   n      median   p99      max      >120s   >300s")
allg = []
for h in range(24):
    g = sorted(byhour.get(h, []))
    if not g:
        continue
    allg += g
    p99 = g[min(int(len(g) * .99), len(g) - 1)]
    print(f"  {h:02d}:00  {len(g):6d}   {g[len(g)//2]:6.1f}  {p99:7.1f}  {g[-1]:8.1f}"
          f"  {sum(1 for x in g if x > 120):6d}  {sum(1 for x in g if x > 300):6d}")

allg.sort()
print(f"\noverall: median {allg[len(allg)//2]:.1f}s, "
      f"p99 {allg[int(len(allg)*.99)]:.1f}s, "
      f"p999 {allg[int(len(allg)*.999)]:.1f}s, max {allg[-1]:.1f}s")
print(f"gaps over 120s: {sum(1 for x in allg if x > 120)} "
      f"({100*sum(1 for x in allg if x > 120)/len(allg):.3f}%)")
print(f"gaps over 300s: {sum(1 for x in allg if x > 300)} "
      f"({100*sum(1 for x in allg if x > 300)/len(allg):.3f}%)")
