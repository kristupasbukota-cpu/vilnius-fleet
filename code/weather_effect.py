#!/usr/bin/env python3
"""How much does rain slow the network? Reproduces docs/weather-2026-09-30.md.

Run from the root of the published repository (the folder holding analysis/ and
weather/):

    python3 code/weather_effect.py

Inputs are only published files: analysis/trav-*.csv.gz or .csv.xz (one row per charged
stop-to-stop traversal) and weather/weather-*.csv (LHMT hourly observations,
CC BY-SA 4.0). Needs pandas and numpy. Takes a few minutes, mostly the bootstraps.
"""
import glob, os, sys
import numpy as np
import pandas as pd

FIRST, LAST = "2026-08-18", "2026-09-29"
SKIP = {"2026-09-01"}          # ceremonial first school day, no normal morning
HOURS = range(6, 22)           # 06:00 to 21:59 local
WET_MM = 0.1                   # an hour with any measurable rain
WET_MORNING_MM = 0.5           # a morning with real rain, 07-09 total
rng = np.random.default_rng(1)


def load():
    parts = []
    for p in sorted(glob.glob("analysis/trav-*.csv.*")):
        day = os.path.basename(p)[5:15]
        if not (FIRST <= day <= LAST):
            continue
        df = pd.read_csv(p, usecols=["hour_local", "lost_s"])
        g = df.groupby("hour_local").lost_s.agg(["mean", "size"]).reset_index()
        g.columns = ["hour", "lost", "n"]
        g.insert(0, "day", day)
        parts.append(g)
    dh = pd.concat(parts)
    w = pd.concat(pd.read_csv(p) for p in sorted(glob.glob("weather/weather-*.csv")))
    # The observation stamped T covers the hour ending at T (checked against the
    # airport in docs/weather-audit-2026-10-01.md), so it describes the local hour that
    # starts at T - 1 h. Local time follows summer time; until 1 October 2026 this was
    # a fixed +2 h, right only until 25 October. On the night summer time ends, two UTC
    # hours share the local label 03, and their rain is added together.
    start = (pd.to_datetime(w.observationTimeUtc) - pd.Timedelta(hours=1)) \
        .dt.tz_localize("UTC").dt.tz_convert("Europe/Vilnius")
    w = pd.DataFrame({"day": start.dt.strftime("%Y-%m-%d"), "hour": start.dt.hour,
                      "rain": w.precipitation.values}).groupby(["day", "hour"], as_index=False).rain.sum()
    x = dh.merge(w, on=["day", "hour"], how="left")
    x["wd"] = pd.to_datetime(x.day).dt.dayofweek
    x = x[(x.wd < 5) & ~x.day.isin(SKIP) & x.hour.isin(HOURS)].copy()
    x["aut"] = (x.day >= "2026-09-01").astype(int)
    x["wet"] = (x.rain >= WET_MM).astype(float)
    x = x.sort_values(["day", "hour"])
    x["wet_prev"] = x.groupby("day").wet.shift(1).fillna(0)
    return x


def within_day(df, terms):
    """Least squares with a level for every day and for every hour x period."""
    D = pd.get_dummies(df.day).astype(float)
    H = pd.get_dummies(df.hour.astype(str) + "_" + df.aut.astype(str), drop_first=True).astype(float)
    X = np.column_stack([df[terms].values, D.values, H.values])
    return np.linalg.lstsq(X, df.lost.values, rcond=None)[0][:len(terms)]


def cluster_boot(df, terms, k=1000):
    days = df.day.unique()
    out = []
    for _ in range(k):
        pick = rng.choice(days, len(days))
        parts = []
        for i, d in enumerate(pick):
            p = df[df.day == d].copy()
            p["day"] = "%s#%d" % (d, i)
            parts.append(p)
        out.append(within_day(pd.concat(parts), terms))
    return np.percentile(out, [2.5, 97.5], axis=0)


def show(label, df, terms):
    est = within_day(df, terms)
    lo, hi = cluster_boot(df, terms)
    print(label)
    for t, e, l, h in zip(terms, est, lo, hi):
        print("  %-10s %+.2f  [%+.2f, %+.2f]" % (t, e, l, h))


def main():
    x = load()
    print("%d day-hours, %d days, %d wet hours" % (len(x), x.day.nunique(), int(x.wet.sum())))
    peak = x.hour.isin([7, 8, 16, 17, 18])
    x["wet_morning"] = x.wet * x.hour.isin([7, 8])
    x["wet_evening"] = x.wet * x.hour.isin([16, 17, 18])
    x["wet_offpeak"] = x.wet * ~peak

    show("1. A wet hour, within its own day:", x, ["wet"])
    show("2. By window:", x, ["wet_morning", "wet_evening", "wet_offpeak"])
    show("3. This hour and the one before:", x, ["wet", "wet_prev"])

    # Placebo: give every day another day's weather, same hours.
    days = x.day.unique()
    wx = x.set_index(["day", "hour"]).wet
    real = within_day(x, ["wet"])[0]
    pl = []
    for _ in range(500):
        perm = dict(zip(days, rng.permutation(days)))
        y = x.copy()
        y["wet"] = [wx.get((perm[d], h), 0.0) for d, h in zip(y.day, y.hour)]
        pl.append(within_day(y, ["wet"])[0])
    pl = np.array(pl)
    print("4. Placebo, weather from another day: mean %+.3f, 95%% within [%+.2f, %+.2f], "
          "shuffles at or above the real %+.2f: %d of 500"
          % (pl.mean(), np.percentile(pl, 2.5), np.percentile(pl, 97.5), real, (pl >= real).sum()))

    # Day level, the 07-08 morning.
    m = x[x.hour.isin([7, 8])].groupby("day").agg(
        rain=("rain", "sum"), aut=("aut", "first"), wd=("wd", "first"))
    # Exact daily morning mean, weighted by traversals as in the published tables.
    xm = x[x.hour.isin([7, 8])]
    m["lost"] = (xm.lost * xm.n).groupby(xm.day).sum() / xm.n.groupby(xm.day).sum()
    m["fri"] = (m.wd == 4).astype(float)
    m["wetm"] = (m.rain >= WET_MORNING_MM).astype(float)
    cols = ["aut", "fri", "wetm"]

    def ols(df):
        X = np.column_stack([np.ones(len(df))] + [df[c].values for c in cols])
        return np.linalg.lstsq(X, df.lost.values, rcond=None)[0]
    est = ols(m)
    bs = np.array([ols(m.iloc[rng.integers(0, len(m), len(m))]) for _ in range(20000)])
    lo, hi = np.percentile(bs, [2.5, 97.5], axis=0)
    print("5. Morning 07-08, one row per working day (n=%d, %d wet):" % (len(m), int(m.wetm.sum())))
    for n, e, l, h in zip(["summer"] + cols, est, lo, hi):
        print("  %-7s %+.2f  [%+.2f, %+.2f]" % (n, e, l, h))

    # The autumn trend on dry Monday-to-Thursday mornings only.
    a = m[(m.aut == 1) & (m.fri == 0) & (m.wetm == 0)].copy()
    t = (pd.to_datetime(a.index) - pd.Timestamp("2026-09-02")).days / 7
    X = np.column_stack([t] + [(a.wd == k).astype(float) for k in range(4)])
    b = np.linalg.lstsq(X, a.lost.values, rcond=None)[0][0]
    bb = []
    for _ in range(20000):
        i = rng.integers(0, len(a), len(a))
        bb.append(np.linalg.lstsq(X[i], a.lost.values[i], rcond=None)[0][0])
    print("6. Dry autumn Monday-to-Thursday mornings (n=%d): %+.2f s per week [%+.2f, %+.2f]"
          % (len(a), b, np.percentile(bb, 2.5), np.percentile(bb, 97.5)))
    print(a.lost.round(2).to_string())


if __name__ == "__main__":
    sys.exit(main())
