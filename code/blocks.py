#!/usr/bin/env python3
"""Reconstruct every vehicle's working day, trip by trip.

The live feed carries ReisoIdGTFS, which matches trip_id in the static GTFS feed.
trips.txt carries block_id: the whole day of work one vehicle is assigned. Joining
the two turns a stream of positions into "this bus, on the fourth trip of its shift,
started 3 minutes down and finished 5 minutes down".

That is what the evening question needs. Vilnius falls apart at 17:00 with the same
number of vehicles it ran at 08:00, so the cause is not volume. The hypothesis is
compounding: a morning bus leaves a depot on time by construction, an evening bus is
on its sixth trip carrying whatever it lost on the previous five.

Output is one row per (vehicle, trip), written as JSON for slicing elsewhere.

    python3 blocks.py            # every snapshot
    python3 blocks.py --stride 3 # every third one, for a quick look
"""
import csv, glob, gzip, io, json, os, sys, time, zipfile
from collections import defaultdict
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
TZ = timedelta(hours=3)
DEV_MAX = 3600          # beyond an hour is a stale trip assignment, not lateness
MIN_OBS = 3             # a trip seen fewer times than this has no reliable endpoints

STRIDE = 1
if "--stride" in sys.argv:
    STRIDE = int(sys.argv[sys.argv.index("--stride") + 1])

# One local day at a time, and a name for the output. Reading the whole archive on
# every run was fine at nine days and will not be fine at ninety: the cost grows
# with the archive while the new information does not. With --day the loop opens
# only the snapshots that can fall inside that local day.
DAY = sys.argv[sys.argv.index("--day") + 1] if "--day" in sys.argv else None
OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "blocks.json"


def in_day(stamp, day):
    """Local day D runs from (D-1)T21:00:00Z to DT20:59:59Z, the archive being UTC
    and Vilnius being UTC+3 all summer. Compared as strings, which is exact for
    this format and avoids parsing every filename twice."""
    if day is None:
        return True
    d = datetime.strptime(day, "%Y-%m-%d")
    lo = (d - timedelta(hours=3)).strftime("%Y%m%dT%H%M%SZ")
    hi = (d + timedelta(hours=21)).strftime("%Y%m%dT%H%M%SZ")
    return lo <= stamp < hi


def load_trips():
    """trip_id -> (block_id, route_id, direction_id)"""
    out = {}
    z = zipfile.ZipFile(os.path.join(HERE, "gtfs.zip"))
    for r in csv.DictReader(io.TextIOWrapper(z.open("trips.txt"), "utf-8-sig")):
        out[r["trip_id"]] = (r.get("block_id", ""), r.get("route_id", ""),
                             r.get("direction_id", ""))
    return out


def as_int(s):
    s = s.strip()
    if not s:
        return None
    return int(s) if s.lstrip("-").isdigit() else None


def main():
    trips = load_trips()
    files = sorted(glob.glob(os.path.join(HERE, "snapshots", "*.csv.gz")))[::STRIDE]
    if not files:
        raise SystemExit("no snapshots")
    t0 = time.time()

    # (vehicle, date, gtfs trip) -> [t_first, dev_first, t_last, dev_last, n, route, speedsum]
    seen = {}
    matched = unmatched = norows = 0

    for n, p in enumerate(files):
        stamp = os.path.basename(p).split(".")[0]
        if not in_day(stamp, DAY):
            continue
        local = datetime.strptime(stamp, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc) + TZ
        day = local.strftime("%Y-%m-%d")
        mins = local.hour * 60 + local.minute + local.second / 60.0

        try:
            txt = gzip.open(p, "rt", encoding="utf-8", errors="replace").read().replace("\r", "\n")
        except Exception:
            continue
        rows = csv.reader(io.StringIO(txt))
        hdr = next(rows, None)
        if not hdr:
            continue
        ix = {k: i for i, k in enumerate(hdr)}
        need = ("MasinosNumeris", "ReisoIdGTFS", "NuokrypisSekundemis", "Marsrutas", "Greitis")
        if any(k not in ix for k in need):
            continue
        iV, iT, iD, iR, iG = (ix[k] for k in need)

        for r in rows:
            if len(r) <= max(iV, iT, iD, iR, iG):
                continue
            veh = r[iV].strip()
            trip = r[iT].strip()
            dev = as_int(r[iD])
            if not veh or not trip or dev is None or abs(dev) > DEV_MAX:
                continue
            if trip in trips:
                matched += 1
            else:
                unmatched += 1
                continue
            key = (veh, day, trip)
            spd = as_int(r[iG]) or 0
            e = seen.get(key)
            if e is None:
                seen[key] = [mins, dev, mins, dev, 1, r[iR].strip(), spd]
            else:
                if mins < e[0]:
                    e[0], e[1] = mins, dev
                if mins > e[2]:
                    e[2], e[3] = mins, dev
                e[4] += 1
                e[6] += spd

        if n % 2000 == 0:
            print(f"  {n}/{len(files)}  {local:%a %H:%M}  {time.time()-t0:.0f}s", flush=True)

    # order each vehicle's day by when the trip actually started
    by_veh_day = defaultdict(list)
    for (veh, day, trip), e in seen.items():
        if e[4] < MIN_OBS:
            continue
        by_veh_day[(veh, day)].append((trip, e))

    out = []
    for (veh, day), items in by_veh_day.items():
        items.sort(key=lambda x: x[1][0])
        shift_start = items[0][1][0]
        for idx, (trip, e) in enumerate(items, start=1):
            block, route_id, direction = trips[trip]
            out.append({
                "veh": veh,
                "day": day,
                # The GTFS trip id, kept so this table can be joined to the
                # per-traversal segment export. Without it, shift position and road
                # cannot be held against each other, which is the whole point of
                # having both tables.
                "trip_id": trip,
                "trip": idx,                       # trip number in this vehicle's day
                "of": len(items),                  # how many trips it did that day
                "block": block,
                "route": e[5],
                "dir": direction,
                "t0": round(e[0], 2),              # minutes past local midnight, trip start
                "t1": round(e[2], 2),              # trip end as observed
                "hrs": round((e[0] - shift_start) / 60.0, 3),   # hours into the shift
                "dev0": e[1],                      # seconds late when first seen on this trip
                "dev1": e[3],                      # seconds late when last seen
                "n": e[4],
                "mspd": round(e[6] / e[4], 1),
            })

    out.sort(key=lambda r: (r["day"], r["veh"], r["trip"]))
    with open(os.path.join(HERE, OUT), "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"))

    days = sorted(set(r["day"] for r in out))
    print(f"\n{len(out)} vehicle-trips over {len(days)} days {days}")
    print(f"vehicles {len(set(r['veh'] for r in out))}, blocks {len(set(r['block'] for r in out if r['block']))}")
    print(f"gtfs match {matched}/{matched+unmatched} = {100*matched/max(matched+unmatched,1):.1f}%")
    print(f"{time.time()-t0:.0f}s -> {OUT} ({os.path.getsize(os.path.join(HERE, OUT))/1024:.0f} KB)")


if __name__ == "__main__":
    main()
