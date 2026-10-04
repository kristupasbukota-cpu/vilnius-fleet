#!/usr/bin/env python3
"""H5, part 1: is spacing already uneven when buses leave the terminus?

Reproduces sections 1 and 3 of docs/even-spacing-2026-10-04.md. Run from the
repository root:

    python3 code/even_spacing_ends.py

Inputs: analysis/dep-*.csv.xz (departure.py, 21 Sep to 2 Oct 2026),
analysis/blocks-*.json.gz, and the timetable zips in gtfs/ (or gtfs-full/ if
code/gtfs_rebuild.py has been run). Needs pandas and numpy.

For every route-direction and working day, 21 September to 2 October 2026, 07:00 to
19:00, compares the excess waiting time at the first stop (departures, from
departure.py at the scheduled time) with the excess at the last stop (trip ends, from
the block tables), over the same set of trips.

"""
import csv, glob, gzip, io, json, os, re, sys, zipfile
import numpy as np
import pandas as pd

REPO = sys.argv[1] if len(sys.argv) > 1 else "."
GTFS_DIR = "gtfs-full" if os.path.isdir(os.path.join(REPO, "gtfs-full")) else "gtfs"
OUTDIR = sys.argv[2] if len(sys.argv) > 2 else "."
DAYS = ["2026-09-21", "2026-09-22", "2026-09-23", "2026-09-24", "2026-09-25",
        "2026-09-28", "2026-09-29", "2026-09-30", "2026-10-01", "2026-10-02"]
LO, HI = 7 * 3600, 19 * 3600
rng = np.random.default_rng(1)


def s2(x):
    h, m, s = x.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s)


_gt = {}


def gtfs_for(day):
    """Latest version dated no later than the day after, as everywhere else."""
    lim = (pd.Timestamp(day) + pd.Timedelta(days=1)).strftime("%Y%m%d")
    zs = sorted(p for p in glob.glob(os.path.join(REPO, GTFS_DIR, "gtfs-*.zip"))
                if re.search(r"gtfs-(\d{8})", p).group(1) <= lim)
    zp = zs[-1]
    if zp in _gt:
        return _gt[zp]
    z = zipfile.ZipFile(zp)
    rd = lambda n: csv.DictReader(io.TextIOWrapper(z.open(n), "utf-8-sig"))
    routes = {r["route_id"]: r["route_short_name"] for r in rd("routes.txt")}
    trips = {r["trip_id"]: (routes.get(r["route_id"], "?"), r.get("direction_id", "")) for r in rd("trips.txt")}
    first, last = {}, {}
    for r in rd("stop_times.txt"):
        t, q = r["trip_id"], int(r["stop_sequence"])
        if t not in first or q < first[t][0]:
            first[t] = (q, r["stop_id"], s2(r["departure_time"]))
        if t not in last or q > last[t][0]:
            last[t] = (q, r["stop_id"], s2(r["arrival_time"]))
    g = pd.DataFrame([(t, trips[t][0], trips[t][1], first[t][1], first[t][2], last[t][1], last[t][2])
                      for t in first if t in trips],
                     columns=["trip_id", "route", "dir", "stop0", "sched0", "stop1", "sched1"])
    _gt[zp] = (os.path.basename(zp), g)
    return _gt[zp]


rows = []
for day in DAYS:
    zname, g = gtfs_for(day)
    d = pd.read_csv(glob.glob(os.path.join(REPO, "analysis", f"dep-{day}.csv*"))[0], dtype={"vehicle": str, "route": str})
    # departure at the timing point (the boarding bay where a loop has two)
    d["a0_dev"] = np.where(d.dev_at_timing.notna(), d.dev_at_timing, d.dev_at_departure)
    d["t0s"] = np.where(d.dev_at_timing.notna(), d.sched_timing_s, d.sched_dep_s)
    d = d[d.a0_dev.notna()][["trip_id", "vehicle", "a0_dev", "t0s"]]
    b = pd.DataFrame(json.load(gzip.open(os.path.join(REPO, "analysis", f"blocks-{day}.json.gz"))))
    b = b[["trip_id", "veh", "block", "trip", "t0", "t1", "dev1"]]
    x = g.merge(d, on="trip_id").merge(b, on="trip_id")
    x["day"] = day
    x["gtfs"] = zname
    rows.append(x)
    print(day, zname, "gtfs trips", len(g), "with departure and end", len(x), flush=True)
X = pd.concat(rows, ignore_index=True)
# Buses and trolleybuses share route numbers (bus 7 and trolleybus 7 are different
# lines), so the line is named with its mode, read from the trip id's first letter.
X["route"] = X.trip_id.str[0].map({"A": "bus ", "T": "trolleybus "}).fillna("other ") + X.route.astype(str)
X["a0"] = X.t0s + X.a0_dev
X["a1"] = X.sched1 + X.dev1
X["obs_end_gap"] = X.t1 * 60 - X.a1          # sanity: last sighting against sched end + dev1
print("last sighting minus (scheduled end + dev1), s: median %.0f, IQR %s" % (
    X.obs_end_gap.median(), X.obs_end_gap.quantile([.25, .75]).round(0).tolist()))
X = X[(X.t0s >= LO) & (X.t0s < HI)].copy()
print("first sighting under the trip id minus scheduled departure, min: median %.1f, IQR %s" % (
    (X.t0 * 60 - X.t0s).median() / 60, ((X.t0 * 60 - X.t0s).quantile([.25, .75]) / 60).round(1).tolist()))

# main pattern per route-direction: the modal first and last stop
pat = X.groupby(["route", "dir", "stop0", "stop1"]).size().reset_index(name="n")
pat = pat.sort_values("n").groupby(["route", "dir"]).tail(1)
X = X.merge(pat[["route", "dir", "stop0", "stop1"]], on=["route", "dir", "stop0", "stop1"])

express = X.route.str.match(r"^bus \d+G")
busiest = (X[~express].groupby("route").size().sort_values(ascending=False).head(25).index)
X["group"] = np.where(express, "express", np.where(X.route.isin(busiest), "trunk", "rest"))


def waits(times, maxgap=90 * 60):
    t = np.sort(np.asarray(times, float))
    gp = np.diff(t)
    gp = gp[gp <= maxgap]
    return (gp ** 2).sum(), 2 * gp.sum(), len(gp), (gp < 60).sum()


recs = []
for (rt, dr, day), s in X.groupby(["route", "dir", "day"]):
    if len(s) < 10:
        continue
    r = {"route": rt, "dir": dr, "day": day, "group": s.group.iat[0], "n": len(s)}
    s = s.assign(first_seen=s.t0 * 60)
    for k, col in [("S0", "t0s"), ("A0", "a0"), ("S1", "sched1"), ("A1", "a1"), ("F0", "first_seen")]:
        r[k + "_num"], r[k + "_den"], r[k + "_gaps"], r[k + "_lt1"] = waits(s[col])
    ne = s.t0s + s.a0_dev.clip(lower=0)               # no early departures
    r["N0_num"], r["N0_den"], _, _ = waits(ne)
    recs.append(r)
R = pd.DataFrame(recs)
R.to_csv(os.path.join(OUTDIR, "even-spacing-ends-routedays.csv"), index=False)


def pooled(df):
    w = lambda k: df[k + "_num"].sum() / df[k + "_den"].sum() / 60
    return {k: w(k) for k in ["S0", "A0", "S1", "A1", "N0", "F0"]}


def boot(df, f, k=2000):
    days = df.day.unique()
    out = []
    for _ in range(k):
        pick = rng.choice(days, len(days))
        out.append(f(pd.concat([df[df.day == d] for d in pick])))
    return np.percentile(out, [2.5, 97.5])


print("\nroute-direction-days:", len(R), "trips:", R.n.sum())
for grp in ["express", "trunk", "rest"]:
    df = R[R.group == grp]
    p = pooled(df)
    e0, e1 = p["A0"] - p["S0"], p["A1"] - p["S1"]
    ci0 = boot(df, lambda q: (lambda p: p["A0"] - p["S0"])(pooled(q)))
    ci1 = boot(df, lambda q: (lambda p: p["A1"] - p["S1"])(pooled(q)))
    cig = boot(df, lambda q: (lambda p: (p["A1"] - p["S1"]) - (p["A0"] - p["S0"]))(pooled(q)))
    early = p["A0"] - p["N0"]
    lt1_0 = df.A0_lt1.sum() / df.A0_gaps.sum()
    lt1_1 = df.A1_lt1.sum() / df.A1_gaps.sum()
    print(f"\n== {grp}: {df.route.nunique()} routes, {len(df)} route-dir-days, {df.n.sum()} trips")
    print(f"  scheduled wait at start {p['S0']:.2f} min, actual {p['A0']:.2f}: excess {e0:+.2f} {ci0.round(2)}")
    print(f"  scheduled wait at end   {p['S1']:.2f} min, actual {p['A1']:.2f}: excess {e1:+.2f} {ci1.round(2)}")
    print(f"  built up along the route {e1-e0:+.2f} {cig.round(2)}; share of end excess already at start {e0/e1:.0%}")
    print(f"  of the start excess, removed by stopping early departures: {early:+.2f} min ({early/e0:.0%})")
    print(f"  gaps under 1 minute: start {lt1_0:.1%}, end {lt1_1:.1%}")
    print(f"  the 2 October measure on the same trips (first sighting under the trip id): "
          f"excess {p['F0'] - p['S0']:+.2f}")

# by route, express and trunk
P = []
for (rt, grp), df in R[R.group != "rest"].groupby(["route", "group"]):
    p = pooled(df)
    P.append({"route": rt, "group": grp, "days": df.day.nunique(), "trips": df.n.sum(),
              "S0": p["S0"], "excess_start": p["A0"] - p["S0"], "excess_end": p["A1"] - p["S1"],
              "early_part": p["A0"] - p["N0"]})
P = pd.DataFrame(P).sort_values("excess_end", ascending=False)
P.to_csv(os.path.join(OUTDIR, "even-spacing-ends-routes.csv"), index=False)
pd.set_option("display.width", 200)
print("\n", P.round(2).to_string(index=False))

# Late departures: inherited from the previous trip of the same block?
X = X.sort_values(["day", "block", "trip"])
X["prev_dev1"] = X.groupby(["day", "block"]).dev1.shift()
X["prev_route"] = X.groupby(["day", "block"]).route.shift()
y = X[X.prev_dev1.notna()]
print("\ncorrelation, departure deviation vs previous trip's end deviation, same vehicle: r = %.2f (n=%d)"
      % (np.corrcoef(y.a0_dev.clip(-600, 1800), y.prev_dev1.clip(-600, 1800))[0, 1], len(y)))
late = y[y.a0_dev > 60]
print("departures more than 60 s late: %.1f%%; of those, previous trip ended more than 60 s late: %.0f%%"
      % (100 * (y.a0_dev > 60).mean(), 100 * (late.prev_dev1 > 60).mean()))
print("departures more than 60 s early: %.1f%%" % (100 * (y.a0_dev < -60).mean()))
