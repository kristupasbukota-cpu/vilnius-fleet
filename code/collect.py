#!/usr/bin/env python3
"""Poll the Vilnius live vehicle feed and archive every distinct update.

The feed refreshes roughly every 5.5 s (measured), and each refresh carries a new
GPS fix for nearly the whole fleet. Polling faster than that returns byte-identical
responses, so this writes a snapshot only when the content has actually changed.

    python3 collect.py            # default: poll every 4 s, store each new update
    python3 collect.py 30         # poll every 30 s (the original behaviour)
    python3 collect.py 4 --all    # store every response, duplicates included
"""
import gzip
import hashlib
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
URL = "https://www.stops.lt/vilnius/gps_full.txt"
OUT = os.path.join(HERE, "snapshots")
LOG = os.path.join(HERE, "collector.log")

INTERVAL = float(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1][0].isdigit() else 4.0
SKIP_DUPES = "--all" not in sys.argv

os.makedirs(OUT, exist_ok=True)


def log(msg):
    with open(LOG, "a") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {msg}\n")


def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": "vilnius-fleet-study/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


log(f"collector start interval={INTERVAL}s dedupe={SKIP_DUPES}")
fails = 0
last_hash = None
kept = dupes = 0
last_report = time.time()

while True:
    cycle = time.time()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    try:
        raw = fetch()
        if len(raw) < 200:
            raise ValueError(f"suspiciously small response: {len(raw)} bytes")

        h = hashlib.sha1(raw).hexdigest()
        if SKIP_DUPES and h == last_hash:
            dupes += 1
        else:
            path = os.path.join(OUT, f"{stamp}.csv.gz")
            if not os.path.exists(path):          # same-second collision, keep the first
                tmp = path + ".part"
                with gzip.open(tmp, "wb") as f:
                    f.write(raw)
                os.replace(tmp, path)
                kept += 1
            last_hash = h
        fails = 0

    except Exception as e:
        fails += 1
        log(f"FAIL {stamp} {type(e).__name__}: {e} (streak={fails})")
        raw = None

    # Reported separately from the fetch, so a bug in the bookkeeping can never
    # be logged as a failure of the feed. One line a minute, not one per poll.
    if time.time() - last_report >= 60:
        rows = (raw.count(b"\n") - 1) if raw else "?"
        size = len(raw) if raw else 0
        log(f"ok kept={kept} skipped_dupes={dupes} rows~{rows} bytes={size}")
        kept = dupes = 0
        last_report = time.time()

    delay = INTERVAL if fails <= 3 else min(INTERVAL * fails, 300)
    time.sleep(max(0.5, delay - (time.time() - cycle)))
