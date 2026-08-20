#!/usr/bin/env python3
"""Attribute lateness to specific stretches of road, between named stops.

Everything in this project so far has said *how* late Vilnius is and *when*. It has
never been able to say *where*, except on a 250 m grid that cannot tell a terminus
with built-in recovery time from a junction where the traffic happens to be kind.
Both show up as "time regained" and they mean opposite things.

The fix is the timetable, which has been sitting in gtfs.zip unopened since day one.
437,388 stop times, one row per scheduled call, and the live feed carries
ReisoIdGTFS, which is the trip_id those rows belong to.

The trick is that we do not need any geometry. Every live row carries

    MatavimoLaikas       when the GPS actually fixed, seconds past local midnight
    NuokrypisSekundemis  how many seconds late the vehicle is, right then

and their difference is the vehicle's position *on its own timetable*:

    p = MatavimoLaikas - NuokrypisSekundemis

A bus 6 minutes late at 17:20 is standing where it was scheduled to be at 17:14.
Look p up in that trip's stop_times and you know which pair of stops it is between,
without ever touching a coordinate. GTFS times and MatavimoLaikas are both seconds
past local midnight, so there is no timezone arithmetic anywhere in this file.

Between two consecutive fixes of one vehicle the schedule position advances from p0
to p1 while real time advances t0 to t1, and

    (t1 - t0) - (p1 - p0) = dd, the seconds of lateness gained over that interval.

So dd is shared out across whichever scheduled segments [p0, p1] covers, weighted by
how much of each one it covers. Time lost is charged to the segments the vehicle was
actually on while it lost it.

A segment is only counted, and only charged, once the vehicle is seen to leave it.
Half a traversal at the start or end of an observation chain would otherwise pull
the per-traversal average around.

    python3 segments.py                 # every snapshot in ./snapshots
    python3 segments.py --stride 5      # every fifth, for a quick look
    python3 segments.py --day 2026-08-18
"""
import bisect, csv, glob, gzip, io, json, os, sys, time, zipfile
from collections import defaultdict
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
TZ = timedelta(hours=3)

DEV_MAX = 3600      # beyond an hour is a stale trip assignment, not lateness
DT_MIN, DT_MAX = 15, 240      # seconds between two usable fixes of one vehicle
DD_MAX = 300        # a jump bigger than this between fixes is a reassignment
STALE_MAX = 120     # ignore a row whose GPS fix is older than this
MIN_TRAVERSALS = 20  # a segment thinner than this has no usable average

STRIDE = int(sys.argv[sys.argv.index("--stride") + 1]) if "--stride" in sys.argv else 1
ONLYDAY = sys.argv[sys.argv.index("--day") + 1] if "--day" in sys.argv else None
# Every run used to write the same segments.json and the caller renamed it
# afterwards. Two runs overlapping by a second is all it takes for one day's
# results to end up in another day's file, and nothing about the file would say so.
OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "segments.json"
# Optional per-traversal export. The aggregated table cannot answer whether lateness
# compounds through a vehicle's shift, because by the time a segment is a mean it has
# lost the identity of the vehicle and the trip that produced it. This keeps one row
# per charged traversal so shift position, road and hour can be held against each
# other. It is large, so it is off unless asked for.
TRAV = sys.argv[sys.argv.index("--traversals") + 1] if "--traversals" in sys.argv else None


def hms(s):
    """GTFS clock string to seconds past local midnight. 25:10:00 is legal and means
    01:10 the next morning, which is why this cannot go through a time type."""
    h, m, sec = s.split(":")
    return int(h) * 3600 + int(m) * 60 + int(sec)


def as_int(s):
    s = s.strip()
    if not s:
        return None
    return int(s) if s.lstrip("-").isdigit() else None


def load_gtfs():
    """Read every gtfs*.zip in the directory, later files winning.

    The city republishes the feed and drops the past when it does. The copy taken on
    14 August carries 21,825 trips and covers from the 14th; the copy the box holds
    carries 19,292 and starts on the 19th. Neither is a superset: 583 trips exist
    only in the newer one and 3,116 only in the older. Against a live snapshot they
    match 98.2% each, but our archive straddles both publications, so the honest
    thing is to read both. This is also the argument for never deleting one.
    """
    routes, stops, trips, raw, intern = {}, {}, {}, defaultdict(list), {}
    zips = sorted(glob.glob(os.path.join(HERE, "gtfs*.zip")))
    if not zips:
        raise SystemExit("no gtfs*.zip")
    for zp in zips:
        _read_gtfs(zipfile.ZipFile(zp), routes, stops, trips, raw, intern)
    sched = {}
    for tid, items in raw.items():
        items.sort()
        sched[tid] = ([i[1] for i in items], [i[3] for i in items])
    print(f"gtfs: {len(zips)} feed(s) {[os.path.basename(z) for z in zips]}")
    return trips, sched, stops


def _read_gtfs(z, routes, stops, trips, raw, intern):
    for r in csv.DictReader(io.TextIOWrapper(z.open("routes.txt"), "utf-8-sig")):
        routes[r["route_id"]] = r.get("route_short_name", "") or r["route_id"]

    for r in csv.DictReader(io.TextIOWrapper(z.open("stops.txt"), "utf-8-sig")):
        try:
            stops[r["stop_id"]] = (r["stop_name"], float(r["stop_lat"]), float(r["stop_lon"]))
        except (ValueError, KeyError):
            pass

    for r in csv.DictReader(io.TextIOWrapper(z.open("trips.txt"), "utf-8-sig")):
        trips[r["trip_id"]] = (routes.get(r["route_id"], r["route_id"]),
                               r.get("direction_id", ""))

    # trip_id -> (times, stop_ids) as parallel lists in stop_sequence order.
    # stop ids are interned, so 437,000 rows cost 1,538 distinct strings.
    # A trip present in both feeds must be replaced, not appended to, or its stop
    # list ends up doubled and every segment collapses to zero scheduled length.
    fresh = set()
    for row in csv.reader(io.TextIOWrapper(z.open("stop_times.txt"), "utf-8-sig")):
        if row[0] == "trip_id":
            continue
        tid = row[0]
        if tid not in fresh:
            fresh.add(tid)
            raw[tid] = []
        sid = intern.setdefault(row[3], row[3])
        raw[tid].append((int(row[4]), hms(row[1]), hms(row[2]), sid))


def main():
    t_load = time.time()
    trips, sched, stops = load_gtfs()
    print(f"gtfs: {len(trips)} trips, {len(sched)} with stop times, {len(stops)} stops "
          f"({time.time()-t_load:.0f}s)", flush=True)

    primary_day = ONLYDAY or "all"
    files = sorted(glob.glob(os.path.join(HERE, "snapshots", "*.csv.gz")))[::STRIDE]
    if ONLYDAY:
        files = [f for f in files if _localday(f) == ONLYDAY]
    if not files:
        raise SystemExit("no snapshots")
    print(f"{len(files)} snapshots", flush=True)
    t0 = time.time()

    # segment key -> [dd_sum, traversals, sched_sum, {hour: [dd, n]}]
    seg = {}
    # vehicle -> [p, dev, meas, trip, seg_index, {seg_index: dd}, opening_seg]
    live = {}
    rows_seen = matched = stale = 0
    events = [0, 0, 0.0]     # intervals used, segments charged, seconds attributed
    tw = None
    if TRAV:
        tf = open(os.path.join(HERE, TRAV), "w", newline="", encoding="utf-8")
        tw = csv.writer(tf)
        tw.writerow(["day", "vehicle", "trip_id", "route", "direction", "stop_from_id",
                     "stop_to_id", "hour_local", "sched_s", "lost_s", "trip_start_min"])

    for n, path in enumerate(files):
        base = os.path.basename(path).split(".")[0]
        utc = datetime.strptime(base, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        local = utc + TZ
        now = local.hour * 3600 + local.minute * 60 + local.second

        try:
            txt = gzip.open(path, "rt", encoding="utf-8", errors="replace").read().replace("\r", "\n")
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
            if len(r) <= iM:
                continue
            tid = r[iT].strip()
            if not tid or tid not in sched:
                continue
            veh = r[iV].strip()
            dev = as_int(r[iD])
            meas = as_int(r[iM])
            if not veh or dev is None or meas is None or abs(dev) > DEV_MAX:
                continue
            rows_seen += 1

            # MatavimoLaikas is local seconds past midnight and the snapshot may sit
            # either side of it, so pick the wrap that lands nearest to now.
            if meas - now > 43200:
                meas -= 86400
            elif now - meas > 43200:
                meas += 86400
            if now - meas > STALE_MAX or meas > now + 30:
                stale += 1
                continue
            matched += 1

            arrs, sids = sched[tid]
            p = meas - dev
            # A trip scheduled past midnight carries 24:xx times; drag p onto the
            # same side of the wrap as its own timetable before comparing.
            if arrs[-1] > 86400 and p < 14400:
                p += 86400
            elif arrs[-1] <= 86400 and p > 86400 + 14400:
                p -= 86400

            i = bisect.bisect_right(arrs, p) - 1
            if i < 0 or i >= len(arrs) - 1:
                live.pop(veh, None)          # before the first stop or past the last
                continue

            prev = live.get(veh)
            if prev is None or prev[3] != tid:
                # New chain. Its opening segment is only half observed, so it is
                # marked and will never be charged or counted.
                live[veh] = [p, dev, meas, tid, i, {}, i]
                continue

            # The feed republishes a vehicle every 5.5 seconds but its GPS fixes
            # arrive far less often, so most rows carry a MatavimoLaikas we have
            # already used. Those are not a break in the chain, they are silence.
            if meas <= prev[2]:
                continue
            dt = meas - prev[2]
            dd = dev - prev[1]
            if dt > DT_MAX or abs(dd) > DD_MAX:
                live[veh] = [p, dev, meas, tid, i, {}, i]   # real gap: start again
                continue
            if dt < DT_MIN:
                continue                     # too short to be worth it; keep waiting

            p0, i0, pend, first = prev[0], prev[4], prev[5], prev[6]
            events[0] += 1

            # Share dd across the scheduled segments that [p0, p] covers.
            span = p - p0
            if span <= 0:
                pend[i0] = pend.get(i0, 0.0) + dd
            else:
                for k in range(i0, min(i, len(arrs) - 2) + 1):
                    ov = min(p, arrs[k + 1]) - max(p0, arrs[k])
                    if ov > 0:
                        pend[k] = pend.get(k, 0.0) + dd * (ov / span)

            # Anything the vehicle has now left is a complete traversal, except the
            # segment the chain opened on, which we joined partway through.
            hour = ((prev[2] + meas) // 2 // 3600) % 24
            for k in [k for k in pend if k < i]:
                share = pend.pop(k)
                if k == first:
                    continue
                key = f"{trips[tid][0]}|{trips[tid][1]}|{sids[k]}|{sids[k+1]}"
                e = seg.get(key)
                if e is None:
                    e = seg[key] = [0.0, 0, 0, {}]
                if tw is not None:
                    tw.writerow([primary_day, veh, tid, trips[tid][0], trips[tid][1],
                                 sids[k], sids[k + 1], hour, arrs[k + 1] - arrs[k],
                                 round(share, 2), round(arrs[0] / 60.0, 1)])
                e[0] += share
                e[1] += 1
                e[2] += arrs[k + 1] - arrs[k]
                events[1] += 1
                events[2] += share
                h = e[3].setdefault(str(hour), [0.0, 0])
                h[0] += share
                h[1] += 1
            live[veh] = [p, dev, meas, tid, i, pend, first]

        if n % 2000 == 0:
            print(f"  {n}/{len(files)}  {local:%a %H:%M}  {len(seg)} segments  "
                  f"{time.time()-t0:.0f}s", flush=True)

    if tw is not None:
        tf.close()
        print(f"per-traversal rows written to {TRAV}")

    out = []
    for key, (dd, cnt, sc, hrs) in seg.items():
        if cnt < MIN_TRAVERSALS:
            continue
        route, direction, a, b = key.split("|")
        an, alat, alon = stops.get(a, ("?", None, None))
        bn, blat, blon = stops.get(b, ("?", None, None))
        out.append({
            "r": route, "d": direction, "a": a, "b": b, "an": an, "bn": bn,
            "alat": alat, "alon": alon, "blat": blat, "blon": blon,
            "n": cnt,
            "sched": round(sc / cnt, 1),          # mean scheduled seconds
            "lost": round(dd / cnt, 1),           # mean seconds lost per traversal
            # Lost as a fraction of what the timetable allows. A segment scheduled
            # for 60 seconds that reliably takes 90 is a worse piece of road than
            # one scheduled for 600 that takes 630, even though both lose 30.
            "rate": round(dd / sc, 3) if sc else None,
            "total": round(dd),                   # whole seconds lost across the day
            "hr": {h: [round(v[0] / v[1], 1), v[1]] for h, v in hrs.items() if v[1] >= 4},
        })
    out.sort(key=lambda r: -r["lost"])
    path = os.path.join(HERE, OUT)
    json.dump(out, open(path, "w"), ensure_ascii=False, separators=(",", ":"))

    print(f"\n{rows_seen} usable rows, {matched} placed, {stale} dropped as stale fixes")
    print(f"{events[0]} intervals used, {events[1]} segment traversals charged, "
          f"{events[2]/60:.0f} vehicle-minutes of lateness attributed")
    print(f"{len(seg)} segments seen, {len(out)} with >= {MIN_TRAVERSALS} traversals")
    print(f"{time.time()-t0:.0f}s -> {OUT} ({os.path.getsize(path)/1024:.0f} KB), "
          f"{'all days' if not ONLYDAY else ONLYDAY}")
    print("\n  worst by seconds lost per traversal")
    for r in out[:10]:
        print(f"  +{r['lost']:6.1f}s on {r['sched']:5.0f}s scheduled ({r['rate']:+.0%})  "
              f"n={r['n']:4d}  {r['r']:>4} {r['an']} -> {r['bn']}")
    print("\n  best, where the timetable gives time back")
    for r in out[-6:][::-1]:
        print(f"  {r['lost']:7.1f}s on {r['sched']:5.0f}s scheduled ({r['rate']:+.0%})  "
              f"n={r['n']:4d}  {r['r']:>4} {r['an']} -> {r['bn']}")
    tot = sum(r["total"] for r in out)
    print(f"\n  net across all reported segments: {tot/3600:+.1f} vehicle-hours")


def _localday(path):
    b = os.path.basename(path).split(".")[0]
    d = datetime.strptime(b, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc) + TZ
    return d.date().isoformat()


if __name__ == "__main__":
    main()
