#!/usr/bin/env python3
"""H8, the pre-registered school-holiday test (docs/h8-groundwork-2026-10-18.md, section 2).

Run from the root of the published repository:

    python3 code/h8_holiday_test.py

Holiday days: Tue 3 to Fri 6 November 2026 (pupils' autumn holiday; 2 Nov is a public
holiday). Comparison: Tue to Fri of 20 to 23 Oct, 27 to 30 Oct and 10 to 13 Nov.
Hours are Vilnius local time. Each day gets a mean seconds lost per hop in each window,
weighted by traversals; a period is the mean of its days, and the comparison is the
mean of the three weeks.

Rain adjustment (docs/weather-2026-09-30.md): an hour with 0.1 mm or more at the LHMT
station counts as wet, and the published within-day effect of a wet hour, +1.31 s per
hop, is taken off that hour's mean before the window means are formed. A second version
uses the window-specific effects (07-08 +2.22, 16-18 +2.73, other hours +0.74), and the
unadjusted numbers are shown too.

Intervals: bootstrap over days, resampling within the holiday week and within each
comparison week, 10,000 resamples.

Inputs: analysis/trav-*.csv.xz, weather/weather-*.csv, analysis/h8/school-links.csv,
analysis/h8/schools-vilnius-2026-10-18.csv and gtfs/gtfs-20261101.zip (stop positions).
Needs pandas and numpy.
"""
import io
import math
import zipfile

import numpy as np
import pandas as pd

HOLIDAY = ["2026-11-03", "2026-11-04", "2026-11-05", "2026-11-06"]
WEEKS = [["2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23"],
         ["2026-10-27", "2026-10-28", "2026-10-29", "2026-10-30"],
         ["2026-11-10", "2026-11-11", "2026-11-12", "2026-11-13"]]
COMP = [d for w in WEEKS for d in w]
WINDOWS = {"07-08": [7, 8], "09-14": list(range(9, 15)), "15-18": [15, 16, 17, 18]}
WET_MM = 0.1
FLAT = 1.31
BY_WINDOW = {7: 2.22, 8: 2.22, 16: 2.73, 17: 2.73, 18: 2.73}   # else 0.74
LAT0, LON0 = 54.68566, 25.28767                                # Cathedral Square
BOOT = 10_000
rng = np.random.default_rng(20261114)

# --- links: school class, nearest school's type, direction to the centre
links = pd.read_csv("analysis/h8/school-links.csv", dtype={"stop_from_id": str, "stop_to_id": str})
sch = pd.read_csv("analysis/h8/schools-vilnius-2026-10-18.csv")
sch = sch[(sch.branch == 0) & (sch.pupils >= 100)]
kind = dict(zip(sch.name, np.where(sch.type_group == "Gimnazija", "gimnazija", "younger")))
links["school_type"] = links.nearest_school.map(kind)
with zipfile.ZipFile("gtfs/gtfs-20261101.zip") as z:
    st = pd.read_csv(io.BytesIO(z.read("stops.txt")), dtype={"stop_id": str}, encoding="utf-8-sig")
kx = 111_200 * math.cos(math.radians(LAT0))
st["d"] = np.hypot((st.stop_lon - LON0) * kx, (st.stop_lat - LAT0) * 111_200)
dmap = dict(zip(st.stop_id, st.d))

# --- hops
cols = ["day", "stop_from_id", "stop_to_id", "hour_local", "lost_s"]
frames = []
for day in HOLIDAY + COMP:
    f = pd.read_csv(f"analysis/trav-{day}.csv.xz", usecols=cols,
                    dtype={"stop_from_id": str, "stop_to_id": str})
    frames.append(f[(f.day == day) & f.hour_local.between(7, 18)])
h = pd.concat(frames, ignore_index=True).dropna(subset=["lost_s"])
h = h.merge(links[["stop_from_id", "stop_to_id", "near", "school_type"]],
            on=["stop_from_id", "stop_to_id"], how="left")
h["d0"], h["d1"] = h.stop_from_id.map(dmap), h.stop_to_id.map(dmap)
h["dir"] = np.where(h.d1 < h.d0 - 100, "in", np.where(h.d1 > h.d0 + 100, "out", "tan"))
h.loc[h.d0.isna() | h.d1.isna() | (h.d0 < 500) | (h.d0 > 10_000), "dir"] = "other"
h["younger_near"] = np.where(h.near == "near", h.school_type, None)

# --- rain per local hour
# Local 07:00 to 18:59 lies inside the same UTC day, so each day's own file is enough.
w = pd.concat(pd.read_csv(f"weather/weather-{d}.csv") for d in HOLIDAY + COMP)
start = (pd.to_datetime(w.observationTimeUtc) - pd.Timedelta(hours=1)) \
    .dt.tz_localize("UTC").dt.tz_convert("Europe/Vilnius")
rain = pd.DataFrame({"day": start.dt.strftime("%Y-%m-%d"), "hour": start.dt.hour,
                     "rain": w.precipitation.values}).groupby(["day", "hour"]).rain.sum()


def dayhour(sub):
    g = sub.groupby(["day", "hour_local"]).lost_s.agg(["sum", "size"]).reset_index()
    g["rain"] = [rain.get((d, hr), np.nan) for d, hr in zip(g.day, g.hour_local)]
    g["wet"] = (g.rain >= WET_MM).astype(float)
    return g


def day_means(sub, adj):
    """Mean seconds per hop per day and window, rain adjusted per hour."""
    g = dayhour(sub)
    if adj == "flat":
        g["sum"] -= FLAT * g.wet * g["size"]
    elif adj == "window":
        g["sum"] -= g.hour_local.map(lambda x: BY_WINDOW.get(x, 0.74)) * g.wet * g["size"]
    out = {}
    for name, hrs in WINDOWS.items():
        x = g[g.hour_local.isin(hrs)].groupby("day")[["sum", "size"]].sum()
        out[name] = x["sum"] / x["size"]
    return pd.DataFrame(out)


def fall(dm, col):
    """Comparison mean minus holiday mean (positive = delay fell in the holiday)."""
    return dm.loc[COMP, col].mean() - dm.loc[HOLIDAY, col].mean()


def boot_index():
    hol = rng.choice(HOLIDAY, (BOOT, 4))
    comp = np.concatenate([rng.choice(wk, (BOOT, 4)) for wk in WEEKS], axis=1)
    return hol, comp


HOL_I, COMP_I = boot_index()


def boot_fall(dm, col, minus=None):
    v = dm[col] if minus is None else dm[col] - dm[minus]
    hv = v.loc[HOL_I.ravel()].to_numpy().reshape(HOL_I.shape).mean(1)
    cv = v.loc[COMP_I.ravel()].to_numpy().reshape(COMP_I.shape).mean(1)
    return np.percentile(cv - hv, [2.5, 97.5])


def ci(lo_hi):
    return f"[{lo_hi[0]:+.2f}, {lo_hi[1]:+.2f}]"


print(f"{len(h):,} hops 07:00 to 18:59 on {len(HOLIDAY)} holiday and {len(COMP)} comparison days")

# 0. rain in the windows
g = dayhour(h)
wet = g[g.wet == 1].groupby("day").hour_local.apply(list)
print("\n0. Wet hours (0.1 mm or more) 07:00 to 18:59:")
for d in HOLIDAY + COMP:
    print(f"  {d} {pd.Timestamp(d).day_name()[:3]}  {wet.get(d, [])}")

# 1. Primary and control, three versions of the rain adjustment
res = {}
print("\n1. Seconds lost per hop; fall = comparison minus holiday")
for adj in ("flat", "window", "none"):
    dm = day_means(h, adj)
    res[adj] = dm
    print(f"\n  rain adjustment: {adj}")
    print(f"  {'window':8s} {'Oct 20-23':>10s} {'Oct 27-30':>10s} {'Nov 10-13':>10s} {'comp':>8s} {'holiday':>8s}  fall, 95% CI")
    for col in WINDOWS:
        wk = [dm.loc[x, col].mean() for x in WEEKS]
        print(f"  {col:8s} " + " ".join(f"{v:+10.2f}" for v in wk) +
              f" {dm.loc[COMP, col].mean():+8.2f} {dm.loc[HOLIDAY, col].mean():+8.2f}  "
              f"{fall(dm, col):+.2f} {ci(boot_fall(dm, col))}")
    dd = fall(dm, "07-08") - fall(dm, "09-14")
    print(f"  07-08 fall minus 09-14 fall: {dd:+.2f} {ci(boot_fall(dm, '07-08', '09-14'))}")
    dd = fall(dm, "07-08") - fall(dm, "15-18")
    print(f"  07-08 fall minus 15-18 fall: {dd:+.2f} {ci(boot_fall(dm, '07-08', '15-18'))}")

# 2. near against far (condition 3)
print("\n2. 07-08 by school proximity (flat rain adjustment)")
near_far = {}
for cls in ("near", "middle", "far"):
    dm = day_means(h[h.near == cls], "flat")
    near_far[cls] = dm
    print(f"  {cls:7s} comp {dm.loc[COMP, '07-08'].mean():+6.2f}  holiday {dm.loc[HOLIDAY, '07-08'].mean():+6.2f}  "
          f"fall {fall(dm, '07-08'):+.2f} {ci(boot_fall(dm, '07-08'))}   "
          f"09-14 fall {fall(dm, '09-14'):+.2f}")
nf = pd.DataFrame({"n": near_far["near"]["07-08"], "f": near_far["far"]["07-08"]})
print(f"  near fall minus far fall: {fall(nf, 'n') - fall(nf, 'f'):+.2f} {ci(boot_fall(nf, 'n', 'f'))}")

# 3. supporting checks
print("\n3a. Inbound against outbound, hops starting 0.5 to 10 km out (flat rain adjustment)")
for k in ("in", "out"):
    dm = day_means(h[h.dir == k], "flat")
    print(f"  {k:4s} comp {dm.loc[COMP, '07-08'].mean():+6.2f}  holiday {dm.loc[HOLIDAY, '07-08'].mean():+6.2f}  "
          f"fall {fall(dm, '07-08'):+.2f} {ci(boot_fall(dm, '07-08'))}")
print("\n3b. Near links by the nearest school's type (flat rain adjustment)")
for k in ("younger", "gimnazija"):
    dm = day_means(h[h.younger_near == k], "flat")
    print(f"  {k:9s} comp {dm.loc[COMP, '07-08'].mean():+6.2f}  holiday {dm.loc[HOLIDAY, '07-08'].mean():+6.2f}  "
          f"fall {fall(dm, '07-08'):+.2f} {ci(boot_fall(dm, '07-08'))}")

print("\n4. Day by day, 07-08 (flat rain adjustment)")
dm = res["flat"]
for d in COMP[:8] + HOLIDAY + COMP[8:]:
    tag = "holiday" if d in HOLIDAY else ""
    print(f"  {d} {pd.Timestamp(d).day_name()[:3]}  {dm.loc[d, '07-08']:+6.2f}  09-14 {dm.loc[d, '09-14']:+6.2f}  {tag}")

# Verdict
dm = res["flat"]
f1, f2 = fall(dm, "07-08"), fall(dm, "07-08") - fall(dm, "09-14")
c3 = fall(nf, "n") > fall(nf, "f")
if f1 >= 3.5 and f2 >= 2 and c3:
    v = "SUPPORTED"
elif f1 < 1.5:
    v = "REFUTED"
else:
    v = "INCONCLUSIVE"
print(f"\nVerdict (flat rain adjustment): fall {f1:+.2f} (needs 3.5), against 09-14 {f2:+.2f} "
      f"(needs 2), near larger than far: {c3}  ->  {v}")
