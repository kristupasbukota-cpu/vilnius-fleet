"""The morning has settled, not grown (docs/morning-settled-2026-09-30.md).

Rebuilt on 8 November 2026 from the method in that document; the original script
was never saved. It rebuilds the tables of the 3 October update at the end of that
document, which supersede the 30 September ones, using the weather station only (the
airport readings come from code/weather_audit.py).

    python3 code/morning_settled.py [TRAV_DIR] [WEATHER_DIR]

Defaults: analysis/ and weather/. Days are the unit: each day's mean lost_s per
traversal in each window, and periods are the mean of their days. Intervals are a
day-level bootstrap, 20,000 resamples. 1 September is left out.
"""
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

TRAV = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("analysis")
WEATHER = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("weather")
BOOT = 20_000
WET_MORNING_MM = 0.5            # as in code/weather_effect.py
rng = np.random.default_rng(20261003)

WINDOWS = {"morning 07-08": [7, 8], "midday 09-15": list(range(9, 16)),
           "evening 16-18": [16, 17, 18], "whole day": None}


def days(a, b, wd=range(4)):
    out, d = [], a
    while d <= b:
        if d.weekday() in wd and d != date(2026, 9, 1):
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


SUMMER = days(date(2026, 8, 18), date(2026, 8, 31))
EARLY = days(date(2026, 9, 2), date(2026, 9, 17))
LATE = days(date(2026, 9, 18), date(2026, 10, 1))
FRIDAYS = days(date(2026, 9, 2), date(2026, 10, 2), wd=[4])

rows = []
for day in SUMMER + EARLY + LATE + FRIDAYS:
    f = pd.read_csv(TRAV / f"trav-{day}.csv.gz", usecols=["day", "hour_local", "lost_s"])
    f = f[f["day"] == day].dropna()
    r = {"day": day}
    for w, hrs in WINDOWS.items():
        x = f if hrs is None else f[f["hour_local"].isin(hrs)]
        r[w] = x["lost_s"].mean()
    r["morning_n"] = int(f["hour_local"].isin([7, 8]).sum())
    rows.append(r)
d = pd.DataFrame(rows).set_index("day")

# Rain at the station, 07:00 to 08:59 local, as in code/weather_effect.py.
w = pd.concat(pd.read_csv(p) for p in sorted(WEATHER.glob("weather-*.csv")))
start = (pd.to_datetime(w.observationTimeUtc) - pd.Timedelta(hours=1)) \
    .dt.tz_localize("UTC").dt.tz_convert("Europe/Vilnius")
w = pd.DataFrame({"day": start.dt.strftime("%Y-%m-%d"), "hour": start.dt.hour,
                  "rain": w.precipitation.values})
d["rain_0709"] = w[w.hour.isin([7, 8])].groupby("day").rain.sum().reindex(d.index)


def boot_mean_diff(a, b):
    a, b = np.asarray(a), np.asarray(b)
    da = a[rng.integers(0, len(a), (BOOT, len(a)))].mean(1)
    db = b[rng.integers(0, len(b), (BOOT, len(b)))].mean(1)
    return np.percentile(da - db, [2.5, 97.5])


print("Period comparison, Monday to Thursday, mean seconds of delay per hop")
print(f"{'window':16s} {'summer':>8s} {'early':>8s} {'late':>8s}  late minus early, 95% CI")
for wname in WINDOWS:
    s, e, l = d.loc[SUMMER, wname], d.loc[EARLY, wname], d.loc[LATE, wname]
    lo, hi = boot_mean_diff(l, e)
    print(f"{wname:16s} {s.mean():+8.2f} {e.mean():+8.2f} {l.mean():+8.2f}  "
          f"{l.mean() - e.mean():+.2f} [{lo:+.2f}, {hi:+.2f}]")
print(f"days: {len(SUMMER)} summer, {len(EARLY)} early, {len(LATE)} late")
print(f"lowest late-autumn morning {d.loc[LATE, 'morning 07-08'].min():+.2f} "
      f"({d.loc[LATE, 'morning 07-08'].idxmin()}); highest summer "
      f"{d.loc[SUMMER, 'morning 07-08'].max():+.2f} ({d.loc[SUMMER, 'morning 07-08'].idxmax()})")

print("\nMornings 07-08 by day")
for day in EARLY + LATE + FRIDAYS:
    dt = date.fromisoformat(day)
    print(f"  {day} {dt.strftime('%a')} {d.loc[day, 'morning 07-08']:+6.2f}  "
          f"traversals {d.loc[day, 'morning_n']:,}  rain {d.loc[day, 'rain_0709']:.1f} mm")

# Dry Monday-to-Thursday autumn mornings by the station.
aut = d.loc[EARLY + LATE].copy()
aut["dry"] = aut["rain_0709"] < WET_MORNING_MM
aut["wd"] = [date.fromisoformat(x).weekday() for x in aut.index]
aut["t"] = [(date.fromisoformat(x) - date(2026, 9, 2)).days / 7 for x in aut.index]


def slope(df):
    X = np.column_stack([df["t"]] + [(df["wd"] == k).astype(float) for k in range(4)])
    y = df["morning 07-08"].to_numpy()
    b = np.linalg.lstsq(X, y, rcond=None)[0][0]
    bb = []
    for _ in range(BOOT):
        i = rng.integers(0, len(df), len(df))
        bb.append(np.linalg.lstsq(X[i], y[i], rcond=None)[0][0])
    return b, *np.percentile(bb, [2.5, 97.5])


dry = aut[aut["dry"]]
print("\nDry Monday-to-Thursday mornings, by the station (slope with a level per weekday)")
print("  all autumn, n=%d: %+.2f [%+.2f, %+.2f]" % (len(dry), *slope(dry)))
first = dry[dry.index <= "2026-09-10"]
later = dry[dry.index >= "2026-09-14"]
print(f"  2 to 10 Sep, n={len(first)}: mean {first['morning 07-08'].mean():+.2f}")
print("  14 Sep to 1 Oct, n=%d: mean %+.2f, slope %+.2f [%+.2f, %+.2f]"
      % (len(later), later["morning 07-08"].mean(), *slope(later)))
lo, hi = boot_mean_diff(later["morning 07-08"], first["morning 07-08"])
print(f"  step, later minus first: {later['morning 07-08'].mean() - first['morning 07-08'].mean():+.2f} "
      f"[{lo:+.2f}, {hi:+.2f}]")
wk = dry.groupby([date.fromisoformat(x).isocalendar()[1] for x in dry.index])["morning 07-08"].mean()
print("  weekly means, calendar weeks: " + ", ".join(f"{v:+.1f}" for v in wk))
