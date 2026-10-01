#!/usr/bin/env python3
"""Is the weather record right? Reproduces docs/weather-audit-2026-10-01.md.

Run from the root of the published repository:

    python3 code/weather_audit.py

Checks the LHMT station record in weather/ against itself (gaps, nulls, condition
codes against measured rain), against an independent instrument (the METAR reports
of Vilnius airport, EYVI, fetched from the Iowa Environmental Mesonet archive), and
then re-runs the three weather results under four definitions of a wet hour.
Needs pandas and numpy, and network access to mesonet.agron.iastate.edu.
"""
import glob, io, math, os, sys, time, urllib.error, urllib.request
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from weather_effect import within_day, FIRST, LAST, SKIP, HOURS   # same panel rules

rng = np.random.default_rng(7)
IEM = ("https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=EYVI&data=tmpc"
       "&data=metar&year1=2026&month1=8&day1=14&year2=2026&month2=10&day2=1&tz=Etc%2FUTC"
       "&format=onlycomma&latlon=no&missing=M&trace=T&direct=no&report_type=3&report_type=4")
RAIN_RE = r"\s(?:\+|-|VC)?(?:SH|TS)?(?:RA|DZ)\b"


def km(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def jaccard(a, b):
    both = ((a == 1) & (b == 1)).sum()
    either = ((a == 1) | (b == 1)).sum()
    return both / either if either else float("nan")


def main():
    w = pd.concat(pd.read_csv(p) for p in sorted(glob.glob("weather/weather-*.csv")))
    w["t"] = pd.to_datetime(w.observationTimeUtc)
    w = w.drop_duplicates("t").set_index("t").sort_index()
    w = w.loc["2026-08-14":"2026-09-30 23:00"]
    full = pd.date_range("2026-08-14", "2026-09-30 23:00", freq="h")
    P = w.precipitation
    print("1. Completeness: %d hours, %d missing, %.1f mm in total, null precipitation %d"
          % (len(w), len(set(full) - set(w.index)), P.sum(), P.isna().sum()))
    code = w.conditionCode.fillna("").str.contains("rain|shower|drizzle|thunder", regex=True)
    print("2. Condition code against measured rain: %d hours with 0.1 mm or more, %d with a rain code, "
          "%d rain-code hours measured 0 mm" % ((P >= 0.1).sum(), code.sum(), (code & (P == 0)).sum()))

    for attempt in range(5):           # the archive rate-limits with HTTP 429
        try:
            raw = urllib.request.urlopen(IEM, timeout=60).read().decode()
            break
        except urllib.error.HTTPError as err:
            if err.code != 429 or attempt == 4:
                raise
            time.sleep(30 * (attempt + 1))
    e = pd.read_csv(io.StringIO(raw))
    e["t"] = pd.to_datetime(e.valid)
    e["rain"] = e.metar.str.contains(RAIN_RE, regex=True).astype(int)
    e["tmpc"] = pd.to_numeric(e.tmpc, errors="coerce")
    mh = e.groupby(e.t.dt.floor("h")).agg(rain=("rain", "max"), tmpc=("tmpc", "mean"))
    mh = mh.loc["2026-08-14":"2026-09-30 22:00"]
    wet = (P >= 0.1).astype(int)
    print("3. Which hour does an LHMT timestamp describe? Airport rain in [H, H+1) against LHMT "
          "rain stamped H+k (Jaccard):")
    for k in [-1, 0, 1, 2]:
        s = wet.reindex(mh.index + pd.Timedelta(hours=k)).values
        ok = ~np.isnan(s)
        print("   k=%+d  %.3f" % (k, jaccard(mh.rain.values[ok], s[ok])))
    print("   Temperature, airport hour H against LHMT at H+k (mean absolute difference):")
    for k in [-3, 0, 1, 3]:
        s = w.airTemperature.reindex(mh.index + pd.Timedelta(hours=k)).values
        ok = ~np.isnan(s) & ~np.isnan(mh.tmpc.values)
        print("   k=%+d  %.2f C" % (k, np.mean(np.abs(mh.tmpc.values[ok] - s[ok]))))
    st, cath = (54.625992, 25.107064), (54.6857, 25.2876)
    print("4. Station to Cathedral Square: %.1f km" % km(*st, *cath))

    # panel of working-day hours, as in weather_effect.py
    parts = []
    for p in sorted(glob.glob("analysis/trav-*.csv.gz")):
        day = os.path.basename(p)[5:15]
        if not (FIRST <= day <= LAST):
            continue
        df = pd.read_csv(p, usecols=["hour_local", "lost_s"])
        g = df.groupby("hour_local").lost_s.agg(["mean", "size"]).reset_index()
        g.columns = ["hour", "lost", "n"]
        g.insert(0, "day", day)
        parts.append(g)
    x0 = pd.concat(parts)
    x0["wd"] = pd.to_datetime(x0.day).dt.dayofweek
    x0 = x0[(x0.wd < 5) & ~x0.day.isin(SKIP) & x0.hour.isin(HOURS)].copy()
    x0["aut"] = (x0.day >= "2026-09-01").astype(int)
    x0["ts"] = pd.to_datetime(x0.day) + pd.to_timedelta(x0.hour, unit="h")

    def local(flag, shift):
        """UTC-indexed flags to naive Vilnius local hour starts. shift=-1 for LHMT, whose
        stamp T ends the hour; 0 for an index that already marks the hour's start. Local
        time follows summer time; until 1 October 2026 this was a fixed offset."""
        idx = (flag.index + pd.Timedelta(hours=shift)).tz_localize("UTC") \
            .tz_convert("Europe/Vilnius").tz_localize(None)
        return pd.Series(flag.values, index=idx).groupby(level=0).max()
    defs = {
        "A. as published: LHMT 0.1 mm or more": local(wet, -1),
        "B. LHMT 0.1 mm or a rain condition code": local(((P >= 0.1) | code).astype(int), -1),
        "C. Vilnius airport METAR reports rain": local(mh.rain, 0),
        "D. LHMT read the wrong way, as start of hour": local(wet, 0),
    }
    print("5. The three results under each definition of a wet hour:")
    for name, flag in defs.items():
        x = x0.copy()
        x["wet"] = flag.reindex(x.ts).fillna(0).values.astype(float)
        est = within_day(x, ["wet"])[0]
        days = x.day.unique(); bs = []
        for _ in range(300):
            pick = rng.choice(days, len(days)); ps = []
            for i, d in enumerate(pick):
                q = x[x.day == d].copy(); q["day"] = "%s#%d" % (d, i); ps.append(q)
            bs.append(within_day(pd.concat(ps), ["wet"])[0])
        xm = x[x.hour.isin([7, 8])]
        m = xm.groupby("day").agg(wet=("wet", "max"), aut=("aut", "first"), wd=("wd", "first"))
        m["lost"] = (xm.lost * xm.n).groupby(xm.day).sum() / xm.n.groupby(xm.day).sum()
        m["fri"] = (m.wd == 4).astype(float)
        X = np.column_stack([np.ones(len(m)), m.aut, m.fri, m.wet])
        b = np.linalg.lstsq(X, m.lost.values, rcond=None)[0]
        bb = np.array([np.linalg.lstsq(X[i], m.lost.values[i], rcond=None)[0]
                       for i in (rng.integers(0, len(m), len(m)) for _ in range(5000))])
        a = m[(m.aut == 1) & (m.fri == 0) & (m.wet == 0)]
        t = (pd.to_datetime(a.index) - pd.Timestamp("2026-09-02")).days / 7
        XA = np.column_stack([t] + [(a.wd == k).astype(float) for k in range(4)])
        sl = np.linalg.lstsq(XA, a.lost.values, rcond=None)[0][0]
        sb = [np.linalg.lstsq(XA[i], a.lost.values[i], rcond=None)[0][0]
              for i in (rng.integers(0, len(a), len(a)) for _ in range(5000))]
        q = lambda v: "[%+.2f, %+.2f]" % (np.percentile(v, 2.5), np.percentile(v, 97.5))
        print("   %s" % name)
        print("     wet hours %d of %d | wet hour within its day %+.2f %s" % (x.wet.sum(), len(x), est, q(bs)))
        print("     morning: autumn %+.2f %s | wet morning %+.2f %s (%d wet mornings)"
              % (b[1], q(bb[:, 1]), b[3], q(bb[:, 3]), m.wet.sum()))
        print("     dry autumn Mon-Thu mornings: trend %+.2f s per week %s, n=%d" % (sl, q(sb), len(a)))


if __name__ == "__main__":
    main()
