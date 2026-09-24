#!/usr/bin/env python3
"""Did the bus leave early, measured at the time it was supposed to leave.

The existing early-departure number is read from `dev_start`, the deviation at the
first sighting of a trip id. That is not a departure. The feed flips the trip id at
the moment the bus reaches the terminus on its *previous* trip, a median of ten
seconds after the previous trip's last sighting, and the deviation runs continuously
across the flip rather than resetting. So for the roughly nine trips in ten that
turn round without a real layover, the first reading under a new trip id is the
previous trip's ending deviation. It says the bus arrived early. It says nothing
about when it left.

This measures the thing itself. GTFS gives each trip a scheduled departure from its
first stop, T. Every live row carries NuokrypisSekundemis, the seconds by which the
vehicle is behind where its timetable puts it right now. Sample that at T:

    a bus still waiting at the terminus reads about 0, it has not gone
    a bus that pulled out 90 seconds ago sits where it should be at T+90, so -90

No geometry, no first sighting, and no dependence on when the trip id flipped,
because the clock decides when to look rather than the feed.

The timing point, added 20 September 2026. "The first stop" is not always where
the bus leaves from. At eight terminal loops GTFS publishes two bays of the same
terminus as separate first and second stops, typically 30 to 100 m and 60 s
apart. At Vilkpedes ziedas the bus stands at the second bay, the one the operator
times from, so at the first bay's scheduled time it already sits where the
timetable puts it a minute later, and the feed reads -60 s: early, though it has
not moved. Half of all departures there read early for that reason alone.

So the departure is now also sampled at the timing point: the last of the leading
stops that lie within CLUSTER_M of the first stop. For an ordinary trip that is
the first stop and nothing changes. For a two-bay loop it is the second bay. A
bus that really does leave the first bay early is still caught, because the
deviation runs continuously and it is still ahead of schedule a minute later.
The original columns are kept unchanged, so earlier results stay reproducible.

    python3 departure.py --day 2026-08-26
    python3 departure.py --day 2026-08-26 --out dep-2026-08-26.csv
    python3 departure.py --day 2026-08-26 --gtfs-until 20260828 --cluster 150
"""
import csv, glob, gzip, io, math, os, sys, zipfile, time
from collections import defaultdict
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
TZ = timedelta(hours=3)

DEV_MAX = 3600        # beyond an hour is a stale trip assignment, not lateness
NEAR = 90             # a reading must fall within this of T to speak for T
WINDOW = 900          # keep readings this far either side of T, and no others
STALE_MAX = 120       # a GPS fix older than this is not about now
LEAD = 4              # leading stops inspected for the terminal cluster

DAY = sys.argv[sys.argv.index("--day") + 1] if "--day" in sys.argv else None
OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
if not DAY:
    raise SystemExit("need --day YYYY-MM-DD")
if not OUT:
    OUT = f"dep-{DAY}.csv"
CLUSTER_M = float(sys.argv[sys.argv.index("--cluster") + 1]) if "--cluster" in sys.argv else 150.0
# Only timetable versions published on or before this date. Reproducing an old run
# means loading the versions that run could see, since later versions win.
GTFS_UNTIL = sys.argv[sys.argv.index("--gtfs-until") + 1] if "--gtfs-until" in sys.argv else None


def hms(s):
    """GTFS clock time to seconds past local midnight. Values past 24:00 are legal
    and mean the small hours of the following service day, so they are kept."""
    try:
        h, m, sec = s.split(":")
        return int(h) * 3600 + int(m) * 60 + int(sec)
    except Exception:
        return None


def metres(a, b):
    (la1, lo1), (la2, lo2) = a, b
    return math.hypot(math.radians(lo2 - lo1) * 6371000 * math.cos(math.radians(la1)),
                      math.radians(la2 - la1) * 6371000)


def load_gtfs():
    """Scheduled departure from the first stop, per trip, over every feed version
    we hold, later files winning. The city drops the past when it republishes, so a
    day in the middle of the archive is only fully described by the union.

    Also the timing point: the last leading stop within CLUSTER_M of the first."""
    routes, first, seen, timing = {}, {}, {}, {}
    zips = sorted(glob.glob(os.path.join(HERE, "gtfs*.zip")))
    if GTFS_UNTIL:
        def stamp(p):
            b = os.path.basename(p)
            return b[5:13] if b[5:13].isdigit() else "99999999"
        zips = [p for p in zips if stamp(p) <= GTFS_UNTIL]
    if not zips:
        raise SystemExit("no gtfs*.zip")
    where = {}
    for zp in zips:
        z = zipfile.ZipFile(zp)
        for r in csv.DictReader(io.TextIOWrapper(z.open("stops.txt"), "utf-8-sig")):
            try:
                where[r["stop_id"]] = (float(r["stop_lat"]), float(r["stop_lon"]))
            except (KeyError, ValueError):
                pass
        for r in csv.DictReader(io.TextIOWrapper(z.open("routes.txt"), "utf-8-sig")):
            routes[r["route_id"]] = r.get("route_short_name", "") or r["route_id"]
        triproute = {}
        for r in csv.DictReader(io.TextIOWrapper(z.open("trips.txt"), "utf-8-sig")):
            triproute[r["trip_id"]] = (routes.get(r["route_id"], r["route_id"]),
                                       r.get("direction_id", ""))
        # A trip present in an earlier feed must be replaced wholesale, not merged,
        # so its first stop is this version's first stop.
        lead = {}
        for row in csv.reader(io.TextIOWrapper(z.open("stop_times.txt"), "utf-8-sig")):
            if row[0] == "trip_id":
                continue
            tid, seq, dep = row[0], int(row[4]), hms(row[2])
            if dep is None:
                continue
            L = lead.setdefault(tid, [])
            L.append((seq, dep, row[3]))
            if len(L) > LEAD:
                L.sort()
                del L[LEAD:]
        for tid, L in lead.items():
            L.sort()
            seq0, dep0, s0 = L[0]
            first[tid] = dep0
            seen[tid] = triproute.get(tid, ("", ""))
            k = 0
            for j in range(1, len(L)):
                a, b = where.get(s0), where.get(L[j][2])
                if a is None or b is None or metres(a, b) > CLUSTER_M:
                    break
                k = j
            timing[tid] = (L[k][0], L[k][2], L[k][1])
    moved = sum(1 for t in timing if timing[t][2] != first[t])
    print(f"gtfs: {len(zips)} feed(s), {len(first)} trips with a scheduled departure, "
          f"{moved} timed from a later bay within {CLUSTER_M:.0f} m", flush=True)
    return first, seen, timing


def day_files(day):
    """Local day D is (D-1)T21:00:00Z to DT20:59:59Z, Vilnius being UTC+3."""
    d = datetime.strptime(day, "%Y-%m-%d")
    lo = (d - timedelta(hours=3)).strftime("%Y%m%dT%H%M%SZ")
    hi = (d + timedelta(hours=21)).strftime("%Y%m%dT%H%M%SZ")
    out = []
    for p in sorted(glob.glob(os.path.join(HERE, "snapshots", "*.csv.gz"))):
        s = os.path.basename(p)[:16]
        if lo <= s < hi:
            out.append(p)
    return out


def main():
    t0 = time.time()
    first, meta, timing = load_gtfs()
    files = day_files(DAY)
    print(f"{DAY}: {len(files)} snapshots", flush=True)
    if not files:
        raise SystemExit("no snapshots for that day")

    # (vehicle, trip) -> {meas_seconds: deviation}, keyed by measurement time so a
    # vehicle reported unchanged across six snapshots counts once.
    keep = defaultdict(dict)
    rows_seen = no_trip = out_of_window = 0

    for n, p in enumerate(files):
        stamp = os.path.basename(p)[:15]
        local = datetime.strptime(stamp, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc) + TZ
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
            if not tid:
                continue
            rows_seen += 1
            T = first.get(tid)
            if T is None:
                no_trip += 1
                continue
            try:
                dev = int(r[iD]); meas = int(r[iM])
            except ValueError:
                continue
            if abs(dev) > DEV_MAX:
                continue
            # A row whose fix is stale is describing a position from minutes ago.
            if snap_s - meas > STALE_MAX and snap_s > meas:
                continue
            Tt = timing[tid][2]
            if meas < T - WINDOW or meas > max(T, Tt) + WINDOW:
                out_of_window += 1
                continue
            keep[(r[iV].strip(), tid)][meas] = dev

        if n % 2000 == 0:
            print(f"  {n}/{len(files)}  {local:%H:%M}  {time.time()-t0:.0f}s", flush=True)

    print(f"rows with a trip id: {rows_seen}, unmatched to gtfs: {no_trip}, "
          f"outside the departure window: {out_of_window}", flush=True)

    n_written = 0
    with open(os.path.join(HERE, OUT), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["day", "vehicle", "trip_id", "route", "direction", "sched_dep_s",
                    "readings", "nearest_offset_s", "dev_at_departure",
                    "first_seen_s", "dev_first_seen", "last_before_s", "dev_last_before",
                    "timing_seq", "timing_stop", "sched_timing_s", "timing_offset_s",
                    "dev_at_timing"])
        for (veh, tid), obs in keep.items():
            T = first[tid]
            times = sorted(obs)
            old_times = [t for t in times if abs(t - T) <= WINDOW]
            if not old_times:
                continue
            near = min(old_times, key=lambda t: abs(t - T))
            if abs(near - T) > NEAR:
                continue
            # The last reading strictly before T, which is the other honest way to
            # ask the question: was it still where it should be when it should have
            # been there.
            before = [t for t in times if t < T]
            lb = max(before) if before else ""
            route, direction = meta.get(tid, ("", ""))
            tseq, tstop, Tt = timing[tid]
            nt = min(times, key=lambda t: abs(t - Tt))
            ok = abs(nt - Tt) <= NEAR
            # Count readings in the original window only, so this column means what
            # it always meant; the extra readings exist only to reach a later bay.
            n_old = sum(1 for t in times if abs(t - T) <= WINDOW)
            w.writerow([DAY, veh, tid, route, direction, T, n_old,
                        near - T, obs[near], old_times[0], obs[old_times[0]],
                        lb, obs[lb] if lb != "" else "",
                        tseq, tstop, Tt, (nt - Tt) if ok else "",
                        obs[nt] if ok else ""])
            n_written += 1

    print(f"{n_written} trips written to {OUT} in {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
