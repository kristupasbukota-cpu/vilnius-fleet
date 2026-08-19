#!/usr/bin/env python3
"""Notice when this box stops working, and say so somewhere it cannot suppress.

The hard part is not the checking. It is that a watchdog living on the box cannot
report the box being dead: on 18 August this machine stopped executing userspace
for 48 minutes and anything running here would have frozen with it.

So this does not send alarms. It sends a heartbeat, every 15 minutes, to a branch
on GitHub. A scheduled job on GitHub's side watches for that heartbeat to stop and
raises the alarm from infrastructure this box has no influence over. Silence is the
signal, which is the one thing a dead machine can still produce reliably.

The heartbeat also carries what the box thinks of itself, so a machine that is
alive but unhappy is just as visible as one that has gone quiet.

That was not enough on its own. The first version reported only the state at the
instant the watcher happened to look, and the watcher looks once an hour. On the
night of 18 August the feed went wrong at 01:04 and was well again by 01:15, so by
the time anything looked, everything was fine and the fault left no trace anywhere.
A single force-updated commit has no history to inspect either. So alongside the
heartbeat this now keeps a short log of every unhappy observation, and the watcher
reports faults that already healed as well as ones still running. An outage nobody
can see afterwards is the same as no monitoring at all.

One thing had to be learned rather than designed. Vilnius stops running buses at
about 03:57 and starts again at about 04:15, and during that window the feed answers
normally with a header and no vehicles. The collector stores one copy and correctly
skips the rest as unchanged, so snapshots stop arriving for eighteen minutes and the
row count is zero. The first version of this called that an alarm and would have done
so every night, which is how a watchdog gets muted and stops being worth having. An
empty feed is now read as what it is, the city saying there is nothing running, and
only becomes an alarm if it lasts longer than any plausible service gap.

Thresholds are measured, not guessed. Across 23,043 snapshots the gap between
consecutive writes is a median of 10 s and a p99 of 30 s, with no quiet period
overnight: the worst gap in any hour between midnight and 05:00 is 42 s. Every gap
over 300 s in the whole archive belongs to a known outage. So 300 s of silence
means something is wrong, and it will not fire at three in the morning because the
city has gone to bed.

    python3 watchdog.py            # check, act, push the heartbeat
    python3 watchdog.py --dry      # check and print, touch nothing
"""
import glob, json, os, re, subprocess, sys, time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
SNAPS = os.path.join(HERE, "snapshots")
CLOG = os.path.join(HERE, "collector.log")
WLOG = os.path.join(HERE, "watchdog.log")
HB = os.path.join(HERE, "hb")
EVENTS_KEEP = 100       # a fault log the hourly watcher can look back through
PUB = os.path.join(HERE, "pub")
STAMP = os.path.join(HERE, ".wd_last_restart")

# The collector writes roughly six snapshots a minute and one log line a minute.
SNAP_MAX_AGE = 300      # measured: no normal gap in the archive comes close
LOG_MAX_AGE = 180       # three missed log lines means the loop itself has stopped
EMPTY_OK_MIN = 45       # the city really does run no buses for a while before dawn
NIGHTLY_MAX_H = 26      # the summariser runs at 00:20 UTC
MEM_MIN_MB = 120        # below this the box is in the state it died in
DISK_MAX_PCT = 80
GTFS_MAX_DAYS = 7
RESTART_COOLDOWN = 3600  # never restart the collector more than once an hour

DRY = "--dry" in sys.argv
NOW = time.time()
checks = []


def add(level, code, detail):
    checks.append({"level": level, "code": code, "detail": detail})


def sh(cmd, timeout=20):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                              timeout=timeout).stdout.strip()
    except Exception:
        return ""


def age_of(path):
    try:
        return NOW - os.stat(path).st_mtime
    except OSError:
        return None


# ---------------------------------------------------------------- the checks

snaps = glob.glob(os.path.join(SNAPS, "*.csv.gz"))
newest = max(snaps, key=os.path.getmtime) if snaps else None
snap_age = age_of(newest) if newest else None

# The collector keeps logging once a minute even while the feed is refusing it,
# because it backs off rather than exits. That is what separates "the city's feed
# is down", which we must not react to, from "our process has hung", which we can
# actually fix.
clog_age = age_of(CLOG)
tail = []
try:
    with open(CLOG, "rb") as f:
        # enough lines to see an hour and a half of a once-a-minute log, so a long
        # empty stretch can be measured rather than merely noticed.
        f.seek(max(0, os.path.getsize(CLOG) - 24000))
        tail = f.read().decode("utf-8", "replace").splitlines()[-100:]
except OSError:
    pass
recent_fail = sum(1 for l in tail[-6:] if " FAIL " in l)

ok_lines = [l for l in tail if " ok kept=" in l]
rows_last = kept_last = dupes_last = None
if ok_lines:
    m = re.search(r"rows~(\d+)", ok_lines[-1])
    rows_last = int(m.group(1)) if m else None
    m = re.search(r"kept=(\d+)", ok_lines[-1])
    kept_last = int(m.group(1)) if m else None
    m = re.search(r"skipped_dupes=(\d+)", ok_lines[-1])
    dupes_last = int(m.group(1)) if m else None

# How many consecutive recent minutes reported no vehicles at all. This is the
# difference between "the city is asleep" and "the feed is broken".
empty_min = 0
for l in reversed(ok_lines):
    if re.search(r"rows~0\b", l):
        empty_min += 1
    else:
        break

# The collector fetching happily and storing nothing because nothing changed. Not
# staleness: the pipeline is working and the world is standing still.
static = kept_last == 0 and (dupes_last or 0) > 0

collector = sh("systemctl is-active vilnius-collector") or "unknown"
stuck = False

if snap_age is None:
    add("alarm", "no_snapshots", "the snapshot directory is empty")
elif snap_age > SNAP_MAX_AGE:
    if clog_age is not None and clog_age > LOG_MAX_AGE:
        stuck = True
        add("alarm", "collector_hung",
            f"no snapshot for {snap_age:.0f}s and no log line for {clog_age:.0f}s")
    elif recent_fail:
        add("warn", "feed_down",
            f"no snapshot for {snap_age:.0f}s, but the collector is still logging "
            f"and reporting {recent_fail} recent failures, so this is the feed")
    elif static:
        add("ok", "feed_static",
            f"nothing stored for {snap_age:.0f}s because the feed has not changed; "
            f"the collector is fetching and discarding duplicates as designed")
    else:
        add("warn", "snapshots_stale",
            f"no snapshot for {snap_age:.0f}s with no failures logged")
else:
    add("ok", "feed", f"newest snapshot {snap_age:.0f}s old")

if collector != "active":
    add("alarm", "collector_down", f"systemd reports the collector {collector}")

if rows_last == 0:
    if empty_min > EMPTY_OK_MIN:
        add("alarm", "feed_empty",
            f"the feed has carried no vehicles for {empty_min} minutes, far longer "
            f"than the pre-dawn gap in service, so this is not the city being quiet")
    else:
        add("ok", "service_stopped",
            f"no vehicles in the feed for {empty_min} minute(s); before dawn this is "
            f"the city having stopped rather than anything being wrong")

arc_age = age_of(os.path.join(HERE, "arc.json"))
if arc_age is None:
    add("warn", "no_summary", "arc.json has never been written")
elif arc_age > NIGHTLY_MAX_H * 3600:
    add("alarm", "nightly_missed",
        f"the summariser last produced output {arc_age/3600:.1f}h ago")

# Unpushed work. ls-remote is one round trip and needs no fetch.
unpushed = False
if os.path.isdir(os.path.join(PUB, ".git")):
    local = sh(f"git -C {PUB} rev-parse HEAD")
    remote = sh(f"git -C {PUB} ls-remote origin main").split()
    if local and remote and local != remote[0]:
        unpushed = True
        add("warn", "unpushed", "the publish repository is ahead of GitHub")

mem_avail = 0
try:
    for l in open("/proc/meminfo"):
        if l.startswith("MemAvailable:"):
            mem_avail = int(l.split()[1]) // 1024
except OSError:
    pass
if mem_avail and mem_avail < MEM_MIN_MB:
    add("alarm", "memory", f"only {mem_avail} MB available")

st = os.statvfs(HERE)
disk_pct = round(100 * (1 - st.f_bavail / st.f_blocks))
if disk_pct > DISK_MAX_PCT:
    add("warn", "disk", f"the filesystem is {disk_pct}% full")

gtfs_days = None
g = age_of(os.path.join(HERE, "gtfs.zip"))
if g is not None:
    gtfs_days = round(g / 86400, 1)
    if gtfs_days > GTFS_MAX_DAYS:
        add("warn", "gtfs_stale",
            f"the timetable is {gtfs_days} days old and is what every "
            f"lateness number is measured against")

# ---------------------------------------------------------------- the one action

restarted = None
if stuck and not DRY:
    last = 0.0
    try:
        last = float(open(STAMP).read().strip())
    except Exception:
        pass
    if NOW - last > RESTART_COOLDOWN:
        out = sh("sudo systemctl restart vilnius-collector", timeout=45)
        open(STAMP, "w").write(str(NOW))
        restarted = "restarted the collector"
        add("warn", "restarted", f"collector restarted by the watchdog {out}".strip())
    else:
        restarted = "restart suppressed"
        add("alarm", "restart_suppressed",
            f"collector still hung, but it was already restarted "
            f"{(NOW-last)/60:.0f} minutes ago; not looping on it")

state = "alarm" if any(c["level"] == "alarm" for c in checks) else \
        "warn" if any(c["level"] == "warn" for c in checks) else "ok"

hb = {
    "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "state": state,
    "checks": [c for c in checks if c["level"] != "ok"] or [{"level": "ok",
               "code": "all_clear", "detail": "every check passed"}],
    "snapshots": len(snaps),
    "newest": os.path.basename(newest) if newest else None,
    "newest_age_s": round(snap_age) if snap_age is not None else None,
    "rows_last": rows_last,
    "empty_minutes": empty_min,
    "feed_static": static,
    "collector": collector,
    "mem_available_mb": mem_avail,
    "disk_used_pct": disk_pct,
    "summary_age_h": round(arc_age / 3600, 1) if arc_age else None,
    "gtfs_age_days": gtfs_days,
    "unpushed": unpushed,
    "uptime": sh("uptime -p"),
    "action": restarted,
}


line = (f"{hb['utc']} {state} snaps={len(snaps)} age={hb['newest_age_s']}s "
        f"rows={rows_last}{'/empty' + str(empty_min) if empty_min else ''} "
        f"mem={mem_avail}MB disk={disk_pct}% "
        + " ".join(f"[{c['code']}]" for c in checks if c["level"] != "ok"))

if DRY:
    print(json.dumps(hb, indent=1))
    print("\n" + line)
    sys.exit(0)

with open(WLOG, "a") as f:
    f.write(line + "\n")

# ---------------------------------------------------------------- the heartbeat

os.makedirs(HB, exist_ok=True)
with open(os.path.join(HB, "heartbeat.json"), "w") as f:
    json.dump(hb, f, indent=1)

# The fault log. Only unhappy observations go in, so a healthy month costs nothing,
# and a fault that fixes itself between two hourly checks is still on the record.
evpath = os.path.join(HB, "events.json")
events = []
try:
    events = json.load(open(evpath))
except Exception:
    pass
if state != "ok":
    events.append({
        "utc": hb["utc"], "state": state,
        "codes": [c["code"] for c in checks if c["level"] != "ok"],
        "detail": next((c["detail"] for c in checks if c["level"] == "alarm"),
                       next((c["detail"] for c in checks if c["level"] == "warn"), "")),
        "action": restarted,
    })
    events = events[-EVENTS_KEEP:]
with open(evpath, "w") as f:
    json.dump(events, f, indent=1)

if os.path.isdir(os.path.join(HB, ".git")):
    sh(f"git -C {HB} add -A")
    # One commit, amended forever, so a heartbeat every 15 minutes does not turn
    # into 35,000 commits a year in a repository meant to hold summaries.
    has_head = sh(f"git -C {HB} rev-parse --verify HEAD 2>/dev/null")
    msg = f"heartbeat {hb['utc']} {state}"
    if has_head:
        sh(f'git -C {HB} commit -q --amend -m "{msg}"')
    else:
        sh(f'git -C {HB} commit -q -m "{msg}"')
    push = sh(f"git -C {HB} push -qf origin status 2>&1", timeout=60)
    if push:
        with open(WLOG, "a") as f:
            f.write(f"{hb['utc']} push output: {push[:200]}\n")
    # Amending forever leaves the old objects behind. Once a day is plenty.
    if datetime.now(timezone.utc).hour == 4 and datetime.now(timezone.utc).minute < 15:
        sh(f"git -C {HB} reflog expire --expire=now --all", timeout=60)
        sh(f"nice -n 19 git -C {HB} gc --prune=now -q", timeout=120)

print(line)
