"""The autumn morning runs one way (docs/one-direction-2026-10-02.md).

Rebuilt on 8 November 2026 from the method in that document; the original script
was never saved.

    python3 code/one_direction.py [TRAV_DIR] [GTFS_DIR]

Defaults: analysis/ and gtfs/. Reads analysis/trav-*.csv.gz for Monday to Thursday,
18 August to 1 October 2026, 1 September excluded (8 summer days, 18 autumn days), and
stop positions from every whole timetable zip in gtfs/.

A hop is inbound if it ends more than 100 m closer to Cathedral Square than it
started, outbound if more than 100 m further, otherwise tangential. Sections 1 and the
hour table use hops starting 0.5 to 10 km from the square; section 2 uses every hop.
Intervals are a bootstrap over days.
"""
import io
import math
import sys
import zipfile
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

TRAV = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("analysis")
GTFS = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("gtfs")
LAT0, LON0 = 54.68566, 25.28767                  # Cathedral Square
BOOT = 2000
rng = np.random.default_rng(20261002)


def weekdays(a, b):
    out, d = [], a
    while d <= b:
        if d.weekday() <= 3 and d != date(2026, 9, 1):
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


SUMMER = weekdays(date(2026, 8, 18), date(2026, 8, 31))
AUTUMN = weekdays(date(2026, 9, 2), date(2026, 10, 1))

# Stop positions: every whole timetable zip, latest version wins.
stops = {}
for z in sorted(GTFS.glob("gtfs-*.zip")):
    with zipfile.ZipFile(z) as zf:
        s = pd.read_csv(io.BytesIO(zf.read("stops.txt")), dtype={"stop_id": str},
                        encoding="utf-8-sig")
    stops.update(zip(s["stop_id"], zip(s["stop_lat"], s["stop_lon"])))
kx = 111_200 * math.cos(math.radians(LAT0))


def dist(ids):
    lat = ids.map(lambda i: stops.get(i, (np.nan, np.nan))[0])
    lon = ids.map(lambda i: stops.get(i, (np.nan, np.nan))[1])
    return np.hypot((lon - LON0) * kx, (lat - LAT0) * 111_200)


frames = []
for day in SUMMER + AUTUMN:
    f = pd.read_csv(TRAV / f"trav-{day}.csv.gz",
                    usecols=["day", "stop_from_id", "stop_to_id", "hour_local", "lost_s"],
                    dtype={"stop_from_id": str, "stop_to_id": str})
    frames.append(f[f["day"] == day])
h = pd.concat(frames, ignore_index=True).dropna(subset=["lost_s"])
h["d0"], h["d1"] = dist(h["stop_from_id"]), dist(h["stop_to_id"])
h = h.dropna(subset=["d0", "d1"])
h["dir"] = np.where(h["d1"] < h["d0"] - 100, "in",
                    np.where(h["d1"] > h["d0"] + 100, "out", "tan"))
h["season"] = np.where(h["day"].isin(SUMMER), "summer", "autumn")
h["window"] = pd.cut(h["hour_local"], [6.5, 8.5, 15.5, 18.5],
                     labels=["morning 07-09", "midday 09-16", "evening 16-19"])
ring = h[(h["d0"] >= 500) & (h["d0"] <= 10_000)]
print(f"{len(SUMMER)} summer and {len(AUTUMN)} autumn days, {len(h):,} hops "
      f"({len(ring):,} starting 0.5 to 10 km out)")


def day_sums(df, keys):
    """Sum and count of lost_s per day and key, as arrays indexed by the day list."""
    return df.groupby(["day"] + keys)["lost_s"].agg(["sum", "size"])


def boot_days(days):
    return [list(rng.choice(days, size=len(days))) for _ in range(BOOT)]


def pooled(t, days, key):
    sub = t.loc[t.index.get_level_values("day").isin(days)]
    try:
        x = sub.xs(key, level=1)
    except KeyError:
        return np.nan
    x = x.reindex(days).fillna(0)
    return x["sum"].sum() / x["size"].sum()


# Section 1: inbound against outbound.
print("\n1. Mean seconds of delay per hop, 0.5 to 10 km")
print(f"{'':16s} {'sum in':>8s} {'sum out':>8s} {'aut in':>8s} {'aut out':>8s}  autumn in-out, 95% CI")
bs = boot_days(AUTUMN)
for w in ring["window"].cat.categories:
    t = day_sums(ring[ring["window"] == w], ["dir"])
    vals = [pooled(t, SUMMER, "in"), pooled(t, SUMMER, "out"),
            pooled(t, AUTUMN, "in"), pooled(t, AUTUMN, "out")]
    diffs = [pooled(t, b, "in") - pooled(t, b, "out") for b in bs]
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    print(f"{w:16s} " + " ".join(f"{v:+8.2f}" for v in vals) +
          f"  {vals[2] - vals[3]:+.2f} [{lo:+.2f}, {hi:+.2f}]")

print("\nAutumn, hour by hour")
a = ring[ring["season"] == "autumn"]
hr = a.groupby(["dir", "hour_local"])["lost_s"].mean().unstack()
show = [6, 7, 8, 9, 12, 15, 16, 17, 18]
print("hour     " + " ".join(f"{x:>6d}" for x in show))
for k, name in (("in", "inbound "), ("out", "outbound")):
    print(name + " " + " ".join(f"{hr.loc[k, x]:+6.1f}" for x in show))

# Section 2: vehicle-hours created 07-09 per morning, every hop.
print("\n2. Vehicle-hours of delay created 07-09 per morning, every hop")
m = h[h["hour_local"].isin([7, 8])]
vh = m.groupby(["day", "dir"])["lost_s"].sum().unstack().fillna(0) / 3600
bs_s, bs_a = boot_days(SUMMER), boot_days(AUTUMN)
changes = {}
for k, name in (("in", "inbound"), ("out", "outbound"), ("tan", "tangential")):
    s, au = vh.loc[SUMMER, k].mean(), vh.loc[AUTUMN, k].mean()
    d = [vh.loc[x, k].mean() - vh.loc[y, k].mean() for x, y in zip(bs_a, bs_s)]
    lo, hi = np.percentile(d, [2.5, 97.5])
    changes[name] = (s, au, au - s, lo, hi)
total = sum(v[2] for v in changes.values())
for name, (s, au, c, lo, hi) in changes.items():
    print(f"{name:11s} summer {s:5.1f}  autumn {au:5.1f}  change {c:+.1f} [{lo:+.1f}, {hi:+.1f}]  "
          f"share {c / total:.0%}")

for k, name in (("in", "inbound"), ("out", "outbound")):
    t = day_sums(m[m["dir"] == k], [])
    t = t["sum"] / 1, t["size"]
    s_, n_ = t
    per = lambda days: s_.reindex(days).sum() / n_.reindex(days).sum()
    d = [per(x) - per(y) for x, y in zip(bs_a, bs_s)]
    lo, hi = np.percentile(d, [2.5, 97.5])
    print(f"per {name} hop, autumn minus summer: {per(AUTUMN) - per(SUMMER):+.1f} s "
          f"[{lo:+.1f}, {hi:+.1f}]")
