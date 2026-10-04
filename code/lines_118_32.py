#!/usr/bin/env python3
"""Bus lines 118 and 32: the numbers in docs/lines-118-32-2026-10-04.md.

Run from the repository root:

    python3 code/lines_118_32.py

Inputs: analysis/trav-*.csv.(gz|xz) (stop-to-stop hops, 18 August to 2 October
2026), analysis/blocks-*.json.gz (trips) and analysis/spacing-*.csv.xz (passage times
at 5, 25, 50, 75 and 95% of the route, 21 September to 2 October). Needs pandas.

Bus only: trip_id starting with "A", so trolleybus lines with the same number are left
out. Working days are Monday to Friday. Summer is 18 to 31 August, autumn 2 September
to 2 October; 1 September, the changeover day, is left out.
"""
import glob, gzip, json, os, sys
import pandas as pd

REPO = sys.argv[1] if len(sys.argv) > 1 else "."
LINES = ("118", "32")
DIRN = {"0": "to Perkunkiemis", "1": "from Perkunkiemis"}


def period(day):
    return "summer" if day < "2026-09-01" else ("x" if day == "2026-09-01" else "autumn")


# ---- hops
cols = ["day", "trip_id", "route", "direction", "stop_from_id", "stop_to_id", "hour_local", "sched_s", "lost_s"]
parts = []
for p in sorted(glob.glob(os.path.join(REPO, "analysis", "trav-*.csv.*"))):
    d = pd.read_csv(p, usecols=cols, dtype={"route": str, "direction": str, "trip_id": str,
                                            "stop_from_id": str, "stop_to_id": str})
    parts.append(d[d.route.isin(LINES) & d.trip_id.str.startswith("A") & (d.day <= "2026-10-02")])
T = pd.concat(parts, ignore_index=True)
T["per"] = T.day.map(period)
T = T[(pd.to_datetime(T.day).dt.dayofweek < 5) & (T.per != "x")]
print(f"{len(T)} hops on working days, {T.day.nunique()} days")

# 1. The 07:00 hour, seconds lost per hop, by line, direction and period
print("\n1. Seconds lost per hop, working days")
for line in LINES:
    for d in ("0", "1"):
        x = T[(T.route == line) & (T.direction == d)]
        r = x.groupby(["per", "hour_local"]).lost_s.mean().unstack(0)
        row = "  ".join(f"{h:02d}h {r.loc[h, 'summer']:+5.1f}/{r.loc[h, 'autumn']:+5.1f}" for h in (6, 7, 8, 9))
        print(f"  bus {line:3s} {DIRN[d]:18s} summer/autumn  {row}")

# 2. Neighbouring links that offset each other (autumn): scheduled and actual seconds
print("\n2. Neighbouring links, autumn working days (scheduled s, mean actual s, hops)")
A = T[T.per == "autumn"]
g = A.groupby(["route", "direction", "stop_from_id", "stop_to_id"]).agg(
    sched=("sched_s", "median"), lost=("lost_s", "mean"), n=("lost_s", "size")).reset_index()
g = g[g.n >= 200]
for _, a in g[g.lost.abs() > 25].iterrows():
    nxt = g[(g.route == a.route) & (g.direction == a.direction) & (g.stop_from_id == a.stop_to_id)]
    for _, b in nxt.iterrows():
        if a.lost * b.lost < 0 and abs(b.lost) > 25:
            print(f"  bus {a.route} {DIRN[a.direction]}: stops {a.stop_from_id}>{a.stop_to_id}>{b.stop_to_id}: "
                  f"scheduled {a.sched:.0f}+{b.sched:.0f} s, taken {a.sched + a.lost:.0f}+{b.sched + b.lost:.0f} s, "
                  f"{a.lost:+.1f}/{b.lost:+.1f} per hop, pair {a.lost + b.lost:+.1f} s ({a.n}/{b.n} hops)")

# ---- trips
B = []
for p in sorted(glob.glob(os.path.join(REPO, "analysis", "blocks-*.json.gz"))):
    B += [r for r in json.load(gzip.open(p)) if r["route"] in LINES and r["trip_id"].startswith("A")]
B = pd.DataFrame(B)
B["dir"] = B.dir.astype(str)
B = B[(pd.to_datetime(B.day).dt.dayofweek < 5) & (B.day > "2026-09-01") & (B.day <= "2026-10-02")]

# 3. Vehicles, autumn working days
print("\n3. Vehicles, autumn working days")
for line in LINES:
    v = B[B.route == line].veh.value_counts()
    print(f"  bus {line}: {v.size} vehicles, {len(B[B.route == line])} trips; top three "
          f"{', '.join(v.index[:3])} ran {v.iloc[:3].sum() / v.sum():.0%}")

# 4. Trip end against the timetable, by hour of arrival
print("\n4. Median trip end against the timetable (s), autumn working days, 06-09h")
B["h"] = (B.t1 // 60).astype(int)
for line in LINES:
    for d in ("0", "1"):
        x = B[(B.route == line) & (B.dir == d)]
        q = x.groupby("h").dev1.agg(["median", "size"])
        print(f"  bus {line:3s} {DIRN[d]:18s} all {x.dev1.median():+5.0f} (n {len(x)})  " +
              "  ".join(f"{h:02d}h {q.loc[h, 'median']:+5.0f} (n {q.loc[h, 'size']})" for h in (6, 7, 8, 9) if h in q.index))

# 5. On time at five points along the route, 21 Sep to 2 Oct, trips from 06:00
print("\n5. Whole-route trips: early (>60 s ahead) / on time / late (>180 s behind) at 5, 25, 50, 75, 95% of the route")
S = pd.concat([pd.read_csv(p, dtype={"route": str, "direction": str, "trip_id": str, "stop0": str, "stop1": str})
               for p in sorted(glob.glob(os.path.join(REPO, "analysis", "spacing-*.csv.xz")))], ignore_index=True)
S = S[S.route.isin(LINES) & S.trip_id.str.startswith("A") & (S.sched_5 >= 6 * 3600)]
# whole-route trips only: the terminal pair most trips run between, per line and direction
# (leaves out short workings and the Apylanka variant)
main = S.groupby(["route", "direction", "stop0", "stop1"]).size().reset_index(name="n") \
        .sort_values("n").groupby(["route", "direction"]).tail(1)[["route", "direction", "stop0", "stop1"]]
S = S.merge(main, on=["route", "direction", "stop0", "stop1"])
for line in LINES:
    for d in ("0", "1"):
        x = S[(S.route == line) & (S.direction == d)]
        out = []
        for k in (5, 25, 50, 75, 95):
            dev = (x[f"passed_{k}"] - x[f"sched_{k}"]).dropna()
            out.append(f"{k}%: {(dev < -60).mean():.0%}/{((dev >= -60) & (dev <= 180)).mean():.0%}/{(dev > 180).mean():.0%}")
        print(f"  bus {line:3s} {DIRN[d]:18s} " + "  ".join(out))

# 6. 118 towards Perkunkiemis, 07-09: the links that lose the most (stop ids; names in gtfs/)
x = T[(T.route == "118") & (T.direction == "0") & (T.per == "autumn") & T.hour_local.between(7, 8)]
g = x.groupby(["stop_from_id", "stop_to_id"]).lost_s.agg(["mean", "size"])
g = g[g["size"] >= 20].sort_values("mean", ascending=False)
print("\n6. Bus 118 to Perkunkiemis, 07:00-08:59, autumn working days: links losing the most per hop")
for (a, b), r in g.head(4).iterrows():
    print(f"  {a}>{b}: {r['mean']:+.1f} s ({int(r['size'])} hops)")
