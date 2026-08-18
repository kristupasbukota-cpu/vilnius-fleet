#!/usr/bin/env python3
"""Summarise the snapshots into arc / baseline / delaygrid, incrementally.

The first version of this read every snapshot ever collected, every night. That is
fine at 15,000 files and fatal at 3 million: measured on the collector box, holding
every headway reading costs 42.7 bytes each and 2.7 million arrive per day, so a
full rebuild would need about 40 GB on a machine with 1 GB.

So this keeps a state file instead. Three different tricks, because the three
outputs have three different shapes:

  arc        one row per snapshot, independent of every other row. Append.
  delaygrid  a sum and a count per map cell. Sums add. Append.
  baseline   a MEDIAN headway per route-hour, and medians do not add. Kept as a
             sparse tally of 5-second buckets, which is fixed in size forever and
             gives the median back to within half a bucket.

    python3 summarize.py             # process whatever is new
    python3 summarize.py --rebuild   # throw the state away and start again
"""
import csv, glob, gzip, io, json, os, sys, time
from collections import defaultdict
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
TZ = timedelta(hours=3)
DEV_MAX = 3600          # beyond an hour is a stale trip assignment, not lateness
CELL = 0.0025           # ~250 m of latitude
LONC = 0.577            # cos(54.7 deg)
GRID_STRIDE = 60        # seconds between the fixes the delay grid compares
GRID_MIN_DT, GRID_MAX_DT = 30, 180
FRAME_SPACING = 260     # seconds of real time between map frames
BUCKET = 5              # seconds per headway tally bucket
# The tally has to span the whole plausible range, not just the interesting part.
# At 360 buckets it topped out at 30 minutes, and since the typical route-hour
# headway is 29 minutes most of the distribution piled into the last bucket and the
# median came out up to 38 minutes wrong. 1440 buckets covers two hours; anything
# above that is not frequent service and its exact value does not matter.
NBUCKET = 1440
MIN_SAMPLES = 12        # a route-hour thinner than this has no usable median
ARC_KEEP_DAYS = 14      # full-resolution arc kept for the chart; the rest archived

STATE = os.path.join(HERE, "state.json.gz")
ARCHIVE = os.path.join(HERE, "arc_archive.jsonl")
REBUILD = "--rebuild" in sys.argv


def stamp_of(p):
    return datetime.strptime(os.path.basename(p).split(".")[0], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)


def as_int(s):
    s = s.strip()
    if not s:
        return None
    return int(s) if s.lstrip("-").isdigit() else None


def pct(v, q):
    return v[min(int(len(v) * q), len(v) - 1)] if v else None


def load_state():
    if REBUILD or not os.path.exists(STATE):
        return {"last": "", "day0": None, "arc": [], "hist": {}, "cell": {},
                "rtype": {}, "vlast": {}, "frames": [], "nextframe": 0.0, "nextgrid": 0.0}
    with gzip.open(STATE, "rt", encoding="utf-8") as f:
        return json.load(f)


def save_state(s):
    tmp = STATE + ".part"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(s, f, separators=(",", ":"))
    os.replace(tmp, STATE)


def median_from_tally(t):
    """t is {bucket index as str: count}. Returns seconds, to the bucket centre."""
    total = sum(t.values())
    if total < MIN_SAMPLES:
        return None
    # Strictly greater, not >=, so this lands on the same element as v[n//2] does
    # on a sorted list. With an even count and a bimodal route-hour the two
    # conventions can pick values half an hour apart, and matching them removes a
    # whole class of spurious difference against the old exact code.
    want, run = total / 2.0, 0
    for b in sorted(t, key=int):
        run += t[b]
        if run > want:
            return int(b) * BUCKET + BUCKET // 2
    return None


def main():
    st = load_state()
    files = sorted(glob.glob(os.path.join(HERE, "snapshots", "*.csv.gz")))
    todo = [p for p in files if os.path.basename(p) > st["last"]]
    if not todo:
        print(f"nothing new since {st['last'] or 'ever'} ({len(files)} on disk)")
        return
    t_start = time.time()

    if st["day0"] is None:
        st["day0"] = (stamp_of(files[0]) + TZ).date().isoformat()
    day0 = datetime.fromisoformat(st["day0"]).date()

    hist, cell, rtype, vlast = st["hist"], st["cell"], st["rtype"], st["vlast"]
    arc, frames = st["arc"], st["frames"]
    next_grid, next_frame = st["nextgrid"], st["nextframe"]

    for n, p in enumerate(todo):
        t_utc = stamp_of(p)
        secs = t_utc.timestamp()
        local = t_utc + TZ
        hour = local.hour
        dt_key = "we" if local.weekday() >= 5 else "wd"
        mins = local.hour * 60 + local.minute + local.second / 60 + 1440 * (local.date() - day0).days

        do_grid = secs >= next_grid
        if do_grid:
            next_grid = secs + GRID_STRIDE
        if secs >= next_frame:
            frames.append(os.path.basename(p))
            next_frame = secs + FRAME_SPACING

        try:
            txt = gzip.open(p, "rt", encoding="utf-8", errors="replace").read().replace("\r", "\n")
        except Exception:
            continue
        rows = csv.reader(io.StringIO(txt))
        hdr = next(rows, None)
        if not hdr:
            continue
        ix = {k: i for i, k in enumerate(hdr)}
        need = ("Transportas", "Marsrutas", "MasinosNumeris", "Ilguma", "Platuma",
                "Greitis", "NuokrypisSekundemis", "IntervalasPries")
        if any(k not in ix for k in need):
            continue
        iT, iR, iM, iLo, iLa, iG, iD, iI = (ix[k] for k in need)

        tracked = moving = bad = 0
        devs = []

        for r in rows:
            if len(r) <= iI:
                continue
            route = r[iR].strip()
            if not route:
                continue
            tracked += 1
            if route not in rtype:
                rtype[route] = r[iT].strip()
            if as_int(r[iG]):
                moving += 1
            d = as_int(r[iD])
            if d is not None:
                if abs(d) <= DEV_MAX:
                    devs.append(d)
                else:
                    bad += 1

            gap = as_int(r[iI])
            if gap and gap > 0:
                b = str(min(gap // BUCKET, NBUCKET - 1))
                for k in (f"{route}|{dt_key}|{hour}", f"{route}|*|{hour}"):
                    t = hist.setdefault(k, {})
                    t[b] = t.get(b, 0) + 1

            if do_grid:
                la, lo = as_int(r[iLa]), as_int(r[iLo])
                if la is None or lo is None:
                    continue
                la, lo = la / 1e6, lo / 1e6
                if not (54.4 < la < 55.1 and 24.8 < lo < 25.8):
                    continue
                vid = r[iM].strip()
                if not vid:
                    continue
                q = vlast.get(vid)
                vlast[vid] = [secs, la, lo, d]
                if q is None or d is None or q[3] is None:
                    continue
                gdt = secs - q[0]
                if not (GRID_MIN_DT <= gdt <= GRID_MAX_DT):
                    continue
                dd = d - q[3]
                if abs(dd) > 600:      # a jump this big is a new trip, not lost time
                    continue
                k = f"{round(((la + q[1]) / 2) / CELL)},{round(((lo + q[2]) / 2) / (CELL / LONC))}"
                c = cell.get(k)
                if c is None:
                    cell[k] = [dd / (gdt / 60.0), 1]
                else:
                    c[0] += dd / (gdt / 60.0)
                    c[1] += 1

        devs.sort()
        arc.append([round(mins, 3), tracked,
                    round((pct(devs, .50) or 0) / 60, 2),
                    round((pct(devs, .90) or 0) / 60, 2),
                    len(devs) + bad, moving, bad])

        if n and n % 5000 == 0:
            print(f"  {n}/{len(todo)}  {local:%a %H:%M}  {time.time()-t_start:.0f}s", flush=True)

    # Vehicles that stopped reporting hours ago will never pair again, and keeping
    # them would grow the state file forever.
    cutoff = stamp_of(todo[-1]).timestamp() - 3600
    for vid in [v for v, q in vlast.items() if q[0] < cutoff]:
        del vlast[vid]

    # The arc is the only unbounded output. Keep a window at full resolution for the
    # chart and push everything older to an append-only archive on disk.
    keep_from = (mins - ARC_KEEP_DAYS * 1440) if arc else 0
    old = [r for r in arc if r[0] < keep_from]
    if old:
        with open(ARCHIVE, "a", encoding="utf-8") as f:
            for r in old:
                f.write(json.dumps(r, separators=(",", ":")) + "\n")
        arc = [r for r in arc if r[0] >= keep_from]
    frames = frames[-4000:]

    st.update({"last": os.path.basename(todo[-1]), "arc": arc, "hist": hist, "cell": cell,
               "rtype": rtype, "vlast": vlast, "frames": frames,
               "nextgrid": next_grid, "nextframe": next_frame})
    save_state(st)

    base = {}
    for k, t in hist.items():
        m = median_from_tally(t)
        if m is not None:
            base[k] = m
    json.dump(arc, open(os.path.join(HERE, "arc.json"), "w"), separators=(",", ":"))
    json.dump({"base": base, "type": rtype},
              open(os.path.join(HERE, "baseline.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    grid = [[round(int(k.split(",")[0]) * CELL, 5), round(int(k.split(",")[1]) * (CELL / LONC), 5),
             round(v[0] / v[1], 3), v[1]] for k, v in cell.items() if v[1] >= 40]
    grid.sort(key=lambda r: -r[3])
    json.dump(grid, open(os.path.join(HERE, "delaygrid.json"), "w"), separators=(",", ":"))
    with open(os.path.join(HERE, "framelist.txt"), "w") as f:
        f.write("\n".join(frames) + "\n")

    rss = 0
    try:
        import resource
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    except Exception:
        pass
    print(f"+{len(todo)} snapshots | arc {len(arc)} rows (+{len(old)} archived) | "
          f"baseline {len(base)}/{len(hist)} keys | grid {len(grid)}/{len(cell)} cells | "
          f"frames {len(frames)} | state {os.path.getsize(STATE)/1024:.0f} KB | "
          f"peak {rss:.0f} MB | {time.time()-t_start:.0f}s")


if __name__ == "__main__":
    main()
