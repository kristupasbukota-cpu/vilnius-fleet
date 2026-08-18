#!/usr/bin/env python3
"""Check that placing a vehicle by arithmetic lands it where it physically is.

segments.py never looks at a coordinate. It puts a vehicle between stop i and stop
i+1 purely from MatavimoLaikas minus NuokrypisSekundemis, which is a claim about the
timetable, not about the road. If that claim is wrong the whole attribution is
charged to the wrong piece of tarmac and every number downstream is fiction.

So: take the same rows, work out where the vehicle actually is from its GPS, and ask
which of its trip's stops it is nearest. If the arithmetic is sound the nearest stop
should be i or i+1 almost always, and the vehicle should sit between the two rather
than somewhere else on the line.

    python3 validate_seg.py [--stride 25]
"""
import bisect, csv, glob, gzip, io, math, os, sys
from collections import Counter
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from segments import load_gtfs, as_int, DEV_MAX, STALE_MAX, TZ

STRIDE = int(sys.argv[sys.argv.index("--stride") + 1]) if "--stride" in sys.argv else 25


def metres(la1, lo1, la2, lo2):
    """Equirectangular is plenty over a few kilometres and far cheaper than haversine."""
    x = math.radians(lo2 - lo1) * math.cos(math.radians((la1 + la2) / 2))
    y = math.radians(la2 - la1)
    return 6371000 * math.hypot(x, y)


def main():
    trips, sched, stops = load_gtfs()
    files = sorted(glob.glob(os.path.join(HERE, "snapshots", "*.csv.gz")))[::STRIDE]
    print(f"{len(files)} snapshots, every {STRIDE}th", flush=True)

    offs = Counter()
    between = ontop = rows = 0
    d_to_seg = []

    for path in files:
        base = os.path.basename(path).split(".")[0]
        local = datetime.strptime(base, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc) + TZ
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
        need = ("ReisoIdGTFS", "NuokrypisSekundemis", "MatavimoLaikas", "Platuma", "Ilguma")
        if any(k not in ix for k in need):
            continue
        iT, iD, iM, iLa, iLo = (ix[k] for k in need)

        for r in rd:
            if len(r) <= max(iT, iD, iM, iLa, iLo):
                continue
            tid = r[iT].strip()
            if tid not in sched:
                continue
            dev, meas = as_int(r[iD]), as_int(r[iM])
            la, lo = as_int(r[iLa]), as_int(r[iLo])
            if dev is None or meas is None or la is None or lo is None or abs(dev) > DEV_MAX:
                continue
            la, lo = la / 1e6, lo / 1e6
            if not (54.4 < la < 55.1 and 24.8 < lo < 25.8):
                continue
            if meas - now > 43200:
                meas -= 86400
            elif now - meas > 43200:
                meas += 86400
            if now - meas > STALE_MAX or meas > now + 30:
                continue

            arrs, sids = sched[tid]
            p = meas - dev
            if arrs[-1] > 86400 and p < 14400:
                p += 86400
            elif arrs[-1] <= 86400 and p > 86400 + 14400:
                p -= 86400
            i = bisect.bisect_right(arrs, p) - 1
            if i < 0 or i >= len(arrs) - 1:
                continue

            best, bd = None, 1e18
            for k, sid in enumerate(sids):
                s = stops.get(sid)
                if not s:
                    continue
                d = metres(la, lo, s[1], s[2])
                if d < bd:
                    best, bd = k, d
            if best is None:
                continue

            rows += 1
            offs[best - i] += 1
            if best in (i, i + 1):
                between += 1
            # How far is the vehicle from the two stops it is claimed to be between?
            a, b = stops.get(sids[i]), stops.get(sids[i + 1])
            if a and b:
                da = metres(la, lo, a[1], a[2])
                db = metres(la, lo, b[1], b[2])
                gap = metres(a[1], a[2], b[1], b[2])
                # Excess over the straight line between them. Zero means the vehicle
                # is on the segment; a big number means it is somewhere else entirely.
                d_to_seg.append(max(0.0, da + db - gap))
            if bd < 40:
                ontop += 1

    d_to_seg.sort()
    def q(f):
        return d_to_seg[min(int(len(d_to_seg) * f), len(d_to_seg) - 1)] if d_to_seg else 0

    print(f"\n{rows} placed rows checked against their own GPS")
    print(f"nearest stop is the segment's own start or end: {100*between/max(rows,1):.1f}%")
    print(f"{100*ontop/max(rows,1):.1f}% were within 40 m of some stop (ie standing at one)")
    print("\noffset of nearest stop from the placement, in stops:")
    for k in sorted(offs):
        if abs(k) <= 4:
            print(f"  {k:+d}  {offs[k]:7d}  {100*offs[k]/rows:5.1f}%")
    far = sum(v for k, v in offs.items() if abs(k) > 4)
    print(f"  beyond +/-4: {far} ({100*far/max(rows,1):.1f}%)")
    print("\ndetour past the claimed segment, metres (0 = on it):")
    for f in (0.5, 0.75, 0.9, 0.95):
        print(f"  p{int(f*100)}  {q(f):7.0f}")


if __name__ == "__main__":
    main()
