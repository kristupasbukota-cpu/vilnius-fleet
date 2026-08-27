#!/usr/bin/env python3
"""Export the derived tables for every complete local day that is not exported yet.

The raw archive lives on one free virtual machine. The repository is the only
copy of anything that is off it, and until today the repository held derived
tables for 18 and 19 August and nothing since, so the loss of the box would have
taken every day after the 19th with it. The raw snapshots cannot go: they are
about 2.3 GB a month of small binary files and would make the repository
unusable. The derived tables can, at roughly 4 MB a day compressed, and they are
the scientific product. The raw feed is the thing you would re-derive them from,
not the thing anyone reads.

Each day is written once and never rewritten, so the repository only ever grows
by addition and git never has to store a second version of anything.

    python3 export.py              # every complete day not yet done, at most 2
    python3 export.py --max 7      # a bigger catch-up
    python3 export.py --day 2026-08-20
    python3 export.py --dry
"""
import glob, gzip, os, shutil, subprocess, sys, time
from collections import defaultdict
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
PUB = os.path.join(HERE, "pub")
TZ = timedelta(hours=3)

# Twenty hours of coverage is the same bar the day summary uses. Below it the day
# is a fragment, and a fragment exported once would never be revisited because
# this script does not rewrite what it has already written.
MIN_MINUTES = 20 * 60

DRY = "--dry" in sys.argv
ONE = sys.argv[sys.argv.index("--day") + 1] if "--day" in sys.argv else None
MAX = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 2


def log(m):
    print(f"{datetime.now(timezone.utc):%H:%M:%S} {m}", flush=True)


def coverage():
    """local day -> how many distinct minutes the archive holds for it"""
    mins = defaultdict(set)
    for p in glob.glob(os.path.join(HERE, "snapshots", "*.csv.gz")):
        stamp = os.path.basename(p)[:15]
        try:
            t = datetime.strptime(stamp, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc) + TZ
        except ValueError:
            continue
        mins[t.strftime("%Y-%m-%d")].add(t.strftime("%H%M"))
    return {d: len(v) for d, v in mins.items()}


def already(day):
    return os.path.exists(os.path.join(PUB, "analysis", f"trav-{day}.csv.gz"))


def run(cmd):
    log("  " + " ".join(cmd))
    r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
    if r.returncode != 0:
        log(f"  FAILED rc={r.returncode}")
        log("  " + (r.stderr or r.stdout)[-500:])
        return False
    tail = [l for l in (r.stdout or "").splitlines() if l.strip()][-1:]
    if tail:
        log("  " + tail[0])
    return True


def squeeze(src, dst):
    """gzip src into dst, then drop the uncompressed original: this box has 75 GB
    free and a day of traversals is 12 MB, but there is no reason to keep both."""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(src, "rb") as f, gzip.open(dst, "wb", 9) as g:
        shutil.copyfileobj(f, g, 1 << 20)
    n = os.path.getsize(dst)
    os.unlink(src)
    log(f"  {os.path.basename(dst)}  {n/1024/1024:.1f} MB")
    return n


def export(day):
    log(f"exporting {day}")
    seg = f"segments-{day}.json"
    trav = f"trav-{day}.csv"
    blk = f"blocks-{day}.json"
    if not run(["python3", "segments.py", "--day", day, "--out", seg, "--traversals", trav]):
        return 0
    if not run(["python3", "blocks.py", "--day", day, "--out", blk]):
        return 0
    total = 0
    total += squeeze(os.path.join(HERE, seg), os.path.join(PUB, "segments", seg + ".gz"))
    total += squeeze(os.path.join(HERE, trav), os.path.join(PUB, "analysis", trav + ".gz"))
    total += squeeze(os.path.join(HERE, blk), os.path.join(PUB, "analysis", blk + ".gz"))
    return total


def main():
    t0 = time.time()
    cov = coverage()
    today = (datetime.now(timezone.utc) + TZ).strftime("%Y-%m-%d")

    if ONE:
        days = [ONE]
    else:
        days = sorted(d for d, n in cov.items()
                      if d < today and n >= MIN_MINUTES and not already(d))
        if len(days) > MAX:
            log(f"{len(days)} days pending, doing the oldest {MAX}: "
                f"{', '.join(days[MAX:])} left for the next run")
            days = days[:MAX]

    if not days:
        log("nothing to export")
        return

    log(f"to export: {', '.join(days)}")
    for d in days:
        log(f"{d}: {cov.get(d, 0)} minutes of coverage")
    if DRY:
        log("dry run, stopping here")
        return

    done, size = [], 0
    for d in days:
        n = export(d)
        if n:
            done.append(d)
            size += n
    log(f"exported {len(done)}/{len(days)} days, {size/1024/1024:.1f} MB, "
        f"{time.time()-t0:.0f}s")
    if not done:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
