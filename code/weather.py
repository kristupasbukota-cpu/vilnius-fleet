#!/usr/bin/env python3
"""Hourly weather observations for Vilnius, kept beside the bus record.

Rain is the obvious confounder for any comparison between days: a wet hour slows the
network by roughly a third on its own (docs/weather-2026-09-30.md). Without the
weather in the record, a wet week reads as a worse network.

Source: Lietuvos hidrometeorologijos tarnyba (LHMT), https://api.meteo.lt, station
vilniaus-ams (Vilniaus AMS, 54.626 N 25.107 E, about 9 km south-west of the old
town). Data licensed CC BY-SA 4.0; the source must be credited when it is reused.

One file per UTC day, pub/weather/weather-YYYY-MM-DD.csv, so a finished day is never
rewritten and git stores each one once. The observation stamped T covers the hour
ending at T, and precipitation is millimetres over that hour.

    python3 weather.py                          # yesterday and today (UTC), the nightly run
    python3 weather.py --from 2026-08-14 --to 2026-09-30   # backfill
"""
import csv, io, json, os, sys, time, urllib.request
from datetime import date, datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "pub", "weather")
STATION = "vilniaus-ams"
URL = "https://api.meteo.lt/v1/stations/%s/observations/%s"
COLS = ["observationTimeUtc", "airTemperature", "feelsLikeTemperature", "windSpeed",
        "windGust", "windDirection", "cloudCover", "seaLevelPressure",
        "relativeHumidity", "precipitation", "snowDepth", "conditionCode"]


def arg(name):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else None


def fetch(day):
    last = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(URL % (STATION, day),
                                         headers={"User-Agent": "vilnius-fleet research"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)["observations"]
        except Exception as e:   # the service resets connections now and then
            last = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("%s: %s" % (day, last))


def write(day, obs):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(COLS)
    for o in sorted(obs, key=lambda o: o.get("observationTimeUtc", "")):
        w.writerow(["" if o.get(c) is None else o.get(c) for c in COLS])
    path = os.path.join(OUT, "weather-%s.csv" % day)
    new = buf.getvalue()
    if os.path.exists(path) and open(path, encoding="utf-8").read() == new:
        return path, len(obs), False
    tmp = path + ".part"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(new)
    os.replace(tmp, path)
    return path, len(obs), True


def main():
    os.makedirs(OUT, exist_ok=True)
    today = datetime.now(timezone.utc).date()
    start = date.fromisoformat(arg("--from")) if arg("--from") else today - timedelta(days=1)
    end = date.fromisoformat(arg("--to")) if arg("--to") else today
    bad = 0
    d = start
    while d <= end:
        try:
            path, n, changed = write(d.isoformat(), fetch(d.isoformat()))
            print("weather %s: %d hours%s" % (d, n, "" if changed else ", unchanged"))
        except Exception as e:
            bad += 1
            print("weather %s: FAILED %s" % (d, e))
        d += timedelta(days=1)
        time.sleep(0.5)          # the service allows 180 requests a minute
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
