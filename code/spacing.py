#!/usr/bin/env python3
"""When does each bus pass five fixed points along its route? H5, 4 October 2026.

For every trip on a local day, the points are the stops at 5%, 25%, 50%, 75% and 95%
of the way along its stop sequence. The live feed gives, for each vehicle and fix,
NuokrypisSekundemis: how many seconds it is behind its timetable. So at measurement
time `meas` with deviation `dev`, the bus is where the timetable puts it at
`meas - dev`. The reading whose `meas - dev` is nearest a point's scheduled time,
within 60 s, gives the time the bus passed that point:

    passed = meas + (scheduled time at the point - (meas - dev))

The same reconstruction segments.py uses for every hop. It keeps five slots per
trip, never the readings themselves, so a whole day fits in a few tens of MB.

    python3 spacing.py --day 2026-09-22 --out spacing-2026-09-22.csv

Timetable: the versions that can be in force on the day (dated no later than the
day after), at most four, later versions winning, as in departure.py.
"""
import csv, glob, gzip, io, os, sys, time, zipfile
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
VILNIUS = ZoneInfo("Europe/Vilnius")
DAY = sys.argv[sys.argv.index("--day") + 1]
OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else f"spacing-{DAY}.csv"
FRACS = (0.05, 0.25, 0.50, 0.75, 0.95)
NEAR = 60            # a reading must place the bus within 60 s of the point
DEV_MAX = 3600
STALE_MAX = 120
FROM_S, TO_S = 6 * 3600 + 1800, 19 * 3600 + 1800   # trips departing 06:30-19:30


def hms(s):
    try:
        h, m, x = s.split(":")
        return int(h) * 3600 + int(m) * 60 + int(x)
    except Exception:
        return None


def versions():
    lim = (datetime.strptime(DAY, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y%m%d")
    def vdate(p):
        b = os.path.basename(p)
        if b == "gtfs.zip":
            return datetime.fromtimestamp(os.stat(p).st_mtime, timezone.utc).strftime("%Y%m%d")
        return b[5:13]
    zs = [p for p in glob.glob(os.path.join(HERE, "gtfs*.zip")) if vdate(p) <= lim]
    zs.sort(key=lambda p: (vdate(p), os.path.basename(p) == "gtfs.zip"))
    return zs[-4:]


def load():
    """trip_id -> [route, dir, first stop, last stop, nstops, [5 scheduled times]]"""
    trips = {}
    zs = versions()
    for zp in zs:
        z = zipfile.ZipFile(zp)
        rd = lambda n: csv.DictReader(io.TextIOWrapper(z.open(n), "utf-8-sig"))
        routes = {r["route_id"]: r.get("route_short_name") or r["route_id"] for r in rd("routes.txt")}
        meta = {r["trip_id"]: (routes.get(r["route_id"], ""), r.get("direction_id", ""))
                for r in rd("trips.txt")}
        st = {}
        for row in csv.reader(io.TextIOWrapper(z.open("stop_times.txt"), "utf-8-sig")):
            if row[0] == "trip_id":
                continue
            a = hms(row[1]) if row[1] else hms(row[2])
            if a is None:
                continue
            st.setdefault(row[0], []).append((int(row[4]), a, row[3]))
        for tid, L in st.items():
            L.sort()
            if L[0][1] < FROM_S or L[0][1] > TO_S or len(L) < 5:
                continue
            n = len(L)
            pts = [L[round(f * (n - 1))][1] for f in FRACS]
            route, d = meta.get(tid, ("", ""))
            trips[tid] = [route, d, L[0][2], L[-1][2], n, pts]
        del st
    print(f"gtfs: {len(zs)} version(s), {len(trips)} trips departing 06:30-19:30", flush=True)
    return trips


def day_files():
    d = datetime.strptime(DAY, "%Y-%m-%d")
    lo = d.replace(tzinfo=VILNIUS).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    hi = (d + timedelta(days=1)).replace(tzinfo=VILNIUS).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = []
    for u in {lo[:8], hi[:8]}:      # list only the two UTC dates involved
        out += [p for p in glob.glob(os.path.join(HERE, "snapshots", f"{u}T*.csv.gz"))
                if lo <= os.path.basename(p)[:16] < hi]
    return sorted(out)


def main():
    t0 = time.time()
    trips = load()
    best = {}        # (veh, tid) -> [[dist, passed] x 5]
    files = day_files()
    print(f"{DAY}: {len(files)} snapshots", flush=True)
    for n, p in enumerate(files):
        stamp = os.path.basename(p)[:15]
        local = datetime.strptime(stamp, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc).astimezone(VILNIUS)
        snap_s = local.hour * 3600 + local.minute * 60 + local.second
        try:
            txt = gzip.open(p, "rt", encoding="utf-8", errors="replace").read().replace("\r", "\n")
        except Exception:
            continue
        rd = csv.reader(io.StringIO(txt))
        hdr = next(rd, None)
        if not hdr:
            continue
        ix = {k: i for i, k in enumerate(hdr)}
        need = ("MasinosNumeris", "ReisoIdGTFS", "NuokrypisSekundemis", "MatavimoLaikas")
        if any(k not in ix for k in need):
            continue
        iV, iT, iD, iM = (ix[k] for k in need)
        for r in rd:
            if len(r) <= max(iV, iT, iD, iM):
                continue
            tid = r[iT].strip()
            tr = trips.get(tid)
            if tr is None:
                continue
            try:
                dev = int(r[iD]); meas = int(r[iM])
            except ValueError:
                continue
            if abs(dev) > DEV_MAX or (snap_s > meas and snap_s - meas > STALE_MAX):
                continue
            s = meas - dev
            pts = tr[5]
            if s < pts[0] - NEAR or s > pts[-1] + NEAR:
                continue
            key = (r[iV].strip(), tid)
            b = best.get(key)
            for k, P in enumerate(pts):
                dist = abs(s - P)
                if dist <= NEAR:
                    if b is None:
                        b = best[key] = [None] * len(FRACS)
                    if b[k] is None or dist < b[k][0]:
                        b[k] = (dist, meas + (P - s))
        if n % 2000 == 0:
            print(f"  {n}/{len(files)} {local:%H:%M} {time.time()-t0:.0f}s, {len(best)} trips", flush=True)
    with open(os.path.join(HERE, OUT), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["day", "vehicle", "trip_id", "route", "direction", "stop0", "stop1", "nstops"]
                   + [f"sched_{int(x*100)}" for x in FRACS] + [f"passed_{int(x*100)}" for x in FRACS])
        for (veh, tid), b in best.items():
            tr = trips[tid]
            w.writerow([DAY, veh, tid, tr[0], tr[1], tr[2], tr[3], tr[4]] + tr[5]
                       + [round(x[1]) if x else "" for x in b])
    print(f"{len(best)} trips written to {OUT} in {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
