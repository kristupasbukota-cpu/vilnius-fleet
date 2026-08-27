#!/usr/bin/env python3
"""Keep the timetable current, and keep every version we have ever held.

The live feed says where a vehicle is and how late it is. The GTFS feed says where
it was supposed to be. Every number this project produces is the difference between
the two, so a stale timetable does not fail loudly, it quietly measures against a
schedule that no longer exists.

Three things this deliberately does not do:

  It does not trust the download. A truncated or error-page response replacing a good
  timetable would corrupt everything downstream, so a candidate has to pass structure
  and size checks before it is allowed to become the current one.

  It does not store a copy unless the content changed. Zip files embed build
  timestamps, so comparing bytes is useless; the fingerprint is a hash of the archive
  directory, every member's name, size and CRC, sorted, which is stable no matter when
  it was packed. Checking daily therefore costs 3 MB of traffic and no disk.

  It does not throw old versions away. The city publishes only the present. Once a
  version is gone it cannot be obtained again, and every retrospective claim about
  August depends on August's schedule.

The health metric is the match rate against a live snapshot, not the file's age. If
the city stops republishing for three weeks an age check cries wolf; the fraction of
running vehicles whose trip we can resolve is the thing that actually matters.

    python3 refresh_gtfs.py            # check, install if new
    python3 refresh_gtfs.py --dry      # check and report, write nothing
    python3 refresh_gtfs.py --match    # only recompute the match rate
"""
import csv, glob, gzip, hashlib, io, json, os, shutil, sys, tempfile, time, zipfile
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
URLS = ["https://www.stops.lt/vilnius/vilnius/gtfs.zip",
        "http://www.stops.lt/vilnius/vilnius/gtfs.zip"]
CURRENT = os.path.join(HERE, "gtfs.zip")
STATE = os.path.join(HERE, "gtfs_state.json")
TIMEOUT = 90
MIN_BYTES = 1_000_000
NEED = ("trips.txt", "stop_times.txt", "stops.txt", "routes.txt")
MIN_ROWS = {"trips.txt": 5_000, "stop_times.txt": 100_000, "stops.txt": 500}

DRY = "--dry" in sys.argv
MATCH_ONLY = "--match" in sys.argv


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_state():
    try:
        return json.load(open(STATE))
    except Exception:
        return {"versions": [], "last_check": None, "last_change": None,
                "checks": 0, "failures": 0}


def fingerprint(path):
    """A hash of what is in the archive, not of how it was packed."""
    with zipfile.ZipFile(path) as z:
        parts = sorted(f"{i.filename}:{i.file_size}:{i.CRC}" for i in z.infolist())
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()[:16]


def count_rows(z, name):
    """Stream it. stop_times.txt is 437,000 lines and this box has 946 MB."""
    n = 0
    with z.open(name) as f:
        for _ in io.TextIOWrapper(f, "utf-8-sig", newline=""):
            n += 1
    return max(0, n - 1)


def validate(path):
    """Everything a candidate must prove before it is allowed to replace the
    timetable every number in this project is measured against."""
    size = os.path.getsize(path)
    if size < MIN_BYTES:
        return None, f"only {size} bytes, expected at least {MIN_BYTES}"
    try:
        with zipfile.ZipFile(path) as z:
            bad = z.testzip()
            if bad:
                return None, f"corrupt member {bad}"
            names = set(z.namelist())
            missing = [n for n in NEED if n not in names]
            if missing:
                return None, f"missing {', '.join(missing)}"
            rows = {n: count_rows(z, n) for n in MIN_ROWS}
    except zipfile.BadZipFile as e:
        return None, f"not a zip: {e}"
    for n, floor in MIN_ROWS.items():
        if rows[n] < floor:
            return None, f"{n} has {rows[n]} rows, expected at least {floor}"
    rows["bytes"] = size
    return rows, None


def download():
    last = None
    for url in URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "vilnius-fleet-study/1.0"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                if r.status != 200:
                    last = f"HTTP {r.status} from {url}"
                    continue
                fd, tmp = tempfile.mkstemp(dir=HERE, prefix=".gtfs-", suffix=".part")
                with os.fdopen(fd, "wb") as f:
                    shutil.copyfileobj(r, f, 64 * 1024)
                return tmp, url, None
        except Exception as e:
            last = f"{type(e).__name__}: {e} ({url})"
    return None, None, last or "no url worked"


def stamp_of(path):
    return datetime.strptime(os.path.basename(path).split(".")[0], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)


def trip_ids():
    """Every trip id across every version we hold, because neither the old nor the
    new feed is a superset of the other."""
    ids = set()
    for zp in sorted(glob.glob(os.path.join(HERE, "gtfs*.zip"))):
        try:
            with zipfile.ZipFile(zp) as z:
                with z.open("trips.txt") as f:
                    r = csv.reader(io.TextIOWrapper(f, "utf-8-sig"))
                    hdr = next(r, None)
                    if not hdr or "trip_id" not in hdr:
                        continue
                    i = hdr.index("trip_id")
                    for row in r:
                        if len(row) > i:
                            ids.add(row[i])
        except Exception:
            continue
    return ids


def match_rate():
    """What fraction of the vehicles actually running can we resolve to a trip?
    This, and not the file's age, is what tells us the join is still sound."""
    snaps = sorted(glob.glob(os.path.join(HERE, "snapshots", "*.csv.gz")))
    if not snaps:
        return None
    known = trip_ids()
    if not known:
        return None
    # Walk backwards until a snapshot has enough running vehicles to measure. The
    # first version looked only at the last dozen, which was a hidden dependency on
    # the time of day: the daily check runs at 02:40 local, and the median snapshot
    # then carries 19 vehicles with a trip id, one below the floor. The metric came
    # back null every single night and nothing said so.
    #
    # Raising the floor to 20 fixed the null and created a worse problem: it stopped
    # at the first snapshot that cleared it, which at 02:40 local is the newest one,
    # carrying about 20 vehicles. One unresolved bus then moved the reading five
    # points. On 24 August that produced 33 consecutive warnings off samples of three
    # to twenty-five vehicles, while the rate measured in real traffic that same
    # night ran between 88% and 100%. A percentage is only worth reading if its
    # denominator is large, so the floor is now high enough that one vehicle moves
    # the answer by less than a point, and the lookback is long enough to reach
    # traffic from the small hours.
    MIN_VEHICLES = 150
    step, span = 30, 4400                     # every ~5 minutes, up to ~12 hours back
    newest = stamp_of(snaps[-1])
    for path in reversed(snaps[-span:][::step] or snaps[-1:]):
        try:
            txt = gzip.open(path, "rt", encoding="utf-8", errors="replace").read().replace("\r", "\n")
        except Exception:
            continue
        rd = csv.reader(io.StringIO(txt))
        hdr = next(rd, None)
        if not hdr or "ReisoIdGTFS" not in hdr:
            continue
        i = hdr.index("ReisoIdGTFS")
        seen = {r[i].strip() for r in rd if len(r) > i and r[i].strip()}
        if len(seen) < MIN_VEHICLES:
            continue                          # too little running to measure anything
        hit = sum(1 for t in seen if t in known)
        age = round((newest - stamp_of(path)).total_seconds() / 60)
        return {"snapshot": os.path.basename(path), "vehicles_with_trip": len(seen),
                "matched": hit, "rate": round(100.0 * hit / len(seen), 1),
                "known_trips": len(known), "measured_minutes_back": age}
    return None


def record_match(st):
    """Measure, and keep the last two months of measurements.

    A single reading cannot tell drift from the time of day. Measured on 20 August
    with the timetables fixed, the rate ran from 89.4% at 09:00 to 100.0% at 07:00,
    so any threshold set from one midday sample would fire on an ordinary morning.
    The history is here so the question can eventually be answered with a trend
    instead of a guess.
    """
    m = match_rate()
    if m:
        h = st.setdefault("match_history", [])
        h.append({"utc": now(), "rate": m["rate"], "vehicles": m["vehicles_with_trip"]})
        st["match_history"] = h[-60:]
    return m


def main():
    st = load_state()

    if MATCH_ONLY:
        st["match"] = record_match(st)
        st["last_check"] = now()
        if not DRY:
            json.dump(st, open(STATE, "w"), indent=1)
        print(json.dumps(st.get("match"), indent=1))
        return

    st["checks"] = st.get("checks", 0) + 1
    tmp, url, err = download()
    if tmp is None:
        st["failures"] = st.get("failures", 0) + 1
        st["last_error"] = f"{now()} download failed: {err}"
        if not DRY:
            json.dump(st, open(STATE, "w"), indent=1)
        print(f"download failed: {err}")
        raise SystemExit(1)

    try:
        rows, why = validate(tmp)
        if rows is None:
            st["failures"] = st.get("failures", 0) + 1
            st["last_error"] = f"{now()} rejected: {why}"
            if not DRY:
                json.dump(st, open(STATE, "w"), indent=1)
            print(f"rejected, timetable left alone: {why}")
            raise SystemExit(1)

        fp = fingerprint(tmp)
        cur_fp = fingerprint(CURRENT) if os.path.exists(CURRENT) else None
        st["last_check"] = now()

        if fp == cur_fp:
            st["match"] = record_match(st)
            if not DRY:
                json.dump(st, open(STATE, "w"), indent=1)
            print(f"unchanged ({fp}), {rows['trips.txt']} trips; nothing stored")
            return

        if DRY:
            print(f"WOULD install new version {fp} (current {cur_fp}), "
                  f"{rows['trips.txt']} trips, {rows['stop_times.txt']} stop times")
            return

        # Archive the outgoing one under the date it was downloaded, keeping the
        # sort order the loaders depend on: dashes precede dots, so every archive
        # sorts before gtfs.zip and the current feed is always read last.
        archived = None
        if os.path.exists(CURRENT):
            d = datetime.fromtimestamp(os.stat(CURRENT).st_mtime, timezone.utc).strftime("%Y%m%d")
            archived = os.path.join(HERE, f"gtfs-{d}.zip")
            n = 1
            while os.path.exists(archived):
                archived = os.path.join(HERE, f"gtfs-{d}-{n}.zip")
                n += 1
            os.rename(CURRENT, archived)
        os.replace(tmp, CURRENT)
        tmp = None
        os.chmod(CURRENT, 0o644)

        st["versions"].append({
            "file": "gtfs.zip", "fingerprint": fp, "downloaded": now(), "url": url,
            "trips": rows["trips.txt"], "stop_times": rows["stop_times.txt"],
            "stops": rows["stops.txt"], "bytes": rows["bytes"],
            "replaced": os.path.basename(archived) if archived else None,
        })
        st["last_change"] = now()
        st["match"] = record_match(st)
        json.dump(st, open(STATE, "w"), indent=1)

        held = sorted(os.path.basename(p) for p in glob.glob(os.path.join(HERE, "gtfs*.zip")))
        print(f"installed {fp}: {rows['trips.txt']} trips, {rows['stop_times.txt']} stop times"
              + (f"; previous kept as {os.path.basename(archived)}" if archived else "")
              + f"\nholding {len(held)} version(s): {', '.join(held)}")
        if st.get("match"):
            print(f"match rate {st['match']['rate']}% of {st['match']['vehicles_with_trip']} vehicles")
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)


if __name__ == "__main__":
    main()
