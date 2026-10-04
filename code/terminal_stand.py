#!/usr/bin/env python3
"""H6: do buses leave early more often where the timetable gives them no stand?

Reproduces docs/terminal-stand-2026-10-04.md. Run from the repository root:

    python3 code/terminal_stand.py

Inputs: analysis/dep-*.csv.xz (departure.py, 21 September to 2 October 2026),
analysis/blocks-*.json.gz, and the timetable zips in gtfs/ (or gtfs-full/ after
code/gtfs_rebuild.py). Needs pandas and numpy.

The scheduled stand of a trip is the time between the scheduled end of the previous
trip in the same timetable block (block_id: one vehicle's day of work) and this
trip's scheduled departure. A block belongs to a single service calendar, so the
previous trip is well defined without the calendar. The first trip of a block comes
from the depot and has no stand.

Early means the deviation at the scheduled departure, at the boarding bay where a
loop has two, more than 60 s ahead: the measure behind the network's 1.85%.
"""
import csv, glob, gzip, io, json, os, re, sys, zipfile
import numpy as np
import pandas as pd

REPO = sys.argv[1] if len(sys.argv) > 1 else "."
GDIR = "gtfs-full" if os.path.isdir(os.path.join(REPO, "gtfs-full")) else "gtfs"
DAYS = ["2026-09-21", "2026-09-22", "2026-09-23", "2026-09-24", "2026-09-25",
        "2026-09-28", "2026-09-29", "2026-09-30", "2026-10-01", "2026-10-02"]
EXCLUDE = "bus 61"          # the line that prompted the hypothesis
rng = np.random.default_rng(1)


def s2(x):
    h, m, s = x.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s)


_cache = {}


def timetable(day):
    lim = (pd.Timestamp(day) + pd.Timedelta(days=1)).strftime("%Y%m%d")
    zp = sorted(p for p in glob.glob(os.path.join(REPO, GDIR, "gtfs-*.zip"))
                if re.search(r"gtfs-(\d{8})", p).group(1) <= lim)[-1]
    if zp in _cache:
        return _cache[zp]
    z = zipfile.ZipFile(zp)
    rd = lambda n: csv.DictReader(io.TextIOWrapper(z.open(n), "utf-8-sig"))
    trips = {r["trip_id"]: r["block_id"] for r in rd("trips.txt")}
    first, last = {}, {}
    for r in rd("stop_times.txt"):
        t, q = r["trip_id"], int(r["stop_sequence"])
        if t not in first or q < first[t][0]:
            first[t] = (q, s2(r["departure_time"]), r["stop_id"])
        if t not in last or q > last[t][0]:
            last[t] = (q, s2(r["arrival_time"]), r["stop_id"])
    g = pd.DataFrame([(t, trips.get(t, ""), first[t][1], first[t][2], last[t][1], last[t][2])
                      for t in first], columns=["trip_id", "block_id", "dep_s", "stop0", "arr_s", "stop1"])
    g = g.sort_values(["block_id", "dep_s"])
    same = g.block_id.eq(g.block_id.shift()) & g.block_id.ne("")
    g["stand_s"] = np.where(same, g.dep_s - g.arr_s.shift(), np.nan)
    g["prev_trip"] = np.where(same, g.trip_id.shift(), None)
    g["prev_stop1"] = np.where(same, g.stop1.shift(), None)
    _cache[zp] = (os.path.basename(zp), g)
    return _cache[zp]


rows = []
for day in DAYS:
    zname, g = timetable(day)
    d = pd.read_csv(glob.glob(os.path.join(REPO, "analysis", f"dep-{day}.csv*"))[0],
                    dtype={"vehicle": str, "route": str})
    d["dev"] = np.where(d.dev_at_timing.notna() & (d.dev_at_timing != d.dev_at_departure),
                        np.maximum(d.dev_at_departure, d.dev_at_timing), d.dev_at_departure)
    d = d[d.dev.notna()]
    b = pd.DataFrame(json.load(gzip.open(os.path.join(REPO, "analysis", f"blocks-{day}.json.gz"))))
    b = b[["trip_id", "veh", "dev1"]].rename(columns={"trip_id": "prev_trip", "veh": "prev_veh",
                                                      "dev1": "prev_dev1"})
    x = d.merge(g, on="trip_id", how="left").merge(b, on="prev_trip", how="left")
    # the previous trip's end only counts if the same vehicle ran it
    x.loc[x.prev_veh != x.vehicle, "prev_dev1"] = np.nan
    x["day"] = day
    rows.append(x)
    print(f"{day} {zname}: {len(d)} departures, stand known for {x.stand_s.notna().sum()}", flush=True)
X = pd.concat(rows, ignore_index=True)
X["line"] = X.trip_id.str[0].map({"A": "bus ", "T": "trolleybus "}).fillna("other ") + X.route.astype(str)
X["early"] = (X.dev < -60).astype(float)
X["hour"] = (X.sched_dep_s // 3600).clip(upper=24).astype(int)
X["ld"] = X.line + "/" + X.direction.astype(str)
bins = [-1e9, 30, 90, 150, 270, 570, 1e9]
labels = ["0 min", "1 min", "2 min", "3-4 min", "5-9 min", "10+ min"]
X["stand"] = pd.cut(X.stand_s, bins, labels=labels).astype(object)
X.loc[X.stand_s.isna(), "stand"] = "first trip of the block"
X["same_terminal"] = X.prev_stop1 == X.stop0
print(f"\n{len(X)} departures; network early {X.early.mean():.2%}; "
      f"previous trip ends at this trip's first stop in {X.same_terminal[X.stand_s.notna()].mean():.0%}")

order = labels + ["first trip of the block"]


def table(df, title):
    print(f"\n{title}")
    t = df.groupby("stand").early.agg(["size", "sum", "mean"]).reindex(order)
    for k, r in t.iterrows():
        if r["size"] > 0:
            print(f"  {k:24s} {int(r['size']):7d} departures, {int(r['sum']):5d} early, {r['mean']:.2%}")
    return t


ex = X[X.line != EXCLUDE]
table(X, "1. All lines: early-departure rate by scheduled stand")
t2 = table(ex, f"2. Without {EXCLUDE}")
arrived_early = ex[ex.prev_dev1 <= -60]
table(arrived_early, "3. Without bus 61, previous trip by the same bus ended at least 60 s early")
arrived_ok = ex[(ex.prev_dev1 > -60) & (ex.prev_dev1 < 60)]
table(arrived_ok, "   ... previous trip ended within 60 s of time")


# 4. Within line and direction: linear probability of early on stand bins,
#    line-direction and hour held fixed, by alternating demeaning; bootstrap over days.
def within(df):
    df = df[df.stand.isin(labels)].copy()
    D = pd.get_dummies(df.stand)[["0 min", "1 min", "2 min", "3-4 min", "5-9 min"]].astype(float)
    Y = df.early.values.astype(float).copy()
    M = D.values.copy()
    g1, g2 = df.ld.values, df.hour.values
    for _ in range(10):
        for g in (g1, g2):
            Y = Y - pd.Series(Y).groupby(g).transform("mean").values
            M = M - pd.DataFrame(M).groupby(g).transform("mean").values
    return np.linalg.lstsq(M, Y, rcond=None)[0]   # against 10+ min


est = within(ex)
days = ex.day.unique()
bs = []
for _ in range(200):
    pick = rng.choice(days, len(days))
    bs.append(within(pd.concat([ex[ex.day == d] for d in pick])))
lo, hi = np.percentile(bs, [2.5, 97.5], axis=0)
print(f"\n4. Within line and direction, hour held fixed, without {EXCLUDE}: "
      "extra early-departure probability against a stand of 10+ min")
for k, e, a, b in zip(["0 min", "1 min", "2 min", "3-4 min", "5-9 min"], est, lo, hi):
    print(f"  {k:8s} {100*e:+.2f} points [{100*a:+.2f}, {100*b:+.2f}]")

# 5. Across line-directions: early rate against the share of departures with a stand
#    of 1 minute or less.
L = ex[ex.stand_s.notna()].groupby("ld").agg(n=("early", "size"), early=("early", "mean"),
                                             short=("stand_s", lambda s: (s <= 90).mean()),
                                             med_stand=("stand_s", "median"))
L = L[L.n >= 200]
r = L[["early", "short"]].corr(method="spearman").iloc[0, 1]
print(f"\n5. {len(L)} line-directions with 200+ departures: Spearman correlation of early rate "
      f"with the share of stands of 1 min or less = {r:+.2f}")
L["short_group"] = pd.cut(L.short, [-0.01, 0.1, 0.5, 1.0], labels=["under 10%", "10-50%", "over half"])
print(L.groupby("short_group", observed=True).agg(lines=("n", "size"), departures=("n", "sum"),
                                                  early=("early", "mean")).round(4).to_string())
print("\nline-directions with the highest early rate:")
print(L.sort_values("early", ascending=False).head(12).round(3).to_string())
L.round(4).to_csv("terminal-stand-lines-2026-10-04.csv")

# 6. Zero and one-minute stands: does the bus turn at the same stop?
print("\n6. Early rate by stand and whether the previous trip ends at this trip's first stop")
print(ex[ex.stand.isin(labels)].groupby(["stand", "same_terminal"]).early.agg(["size", "mean"])
      .round(4).to_string())

# 7. Not part of H6: the first trip of a block, out of the depot.
f = ex[ex.stand == "first trip of the block"]
o = ex[ex.stand != "first trip of the block"]
print(f"\n7. First trip of a block: {len(f)} departures, early {f.early.mean():.2%}; all other "
      f"trips {o.early.mean():.2%}. Of {int(ex.early.sum())} early departures, {int(f.early.sum())} are "
      f"first trips and {int(o[o.stand.isin(['0 min', '1 min'])].early.sum())} follow a stand of 1 min or less.")
h = f.groupby("hour").early.agg(["size", "mean"])
print("   by hour of scheduled departure:", {int(k): (int(v["size"]), round(100 * v["mean"], 1))
                                             for k, v in h.iterrows()})
print("   median deviation of the early ones: %.0f s; at the last reading before the scheduled "
      "time: %.0f s" % (f[f.early == 1].dev.median(), f[f.early == 1].dev_last_before.median()))
g = f.groupby("line").early.agg(["size", "sum", "mean"])
print(f"   lines with at least one early first trip: {(g['sum'] > 0).sum()} of {len(g)}")
