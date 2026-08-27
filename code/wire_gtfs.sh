#!/bin/bash
# Keep the timetable current, on its own timer and its own failure domain.
#
# Deliberately not folded into the nightly chain. That chain is entirely local work
# and finishes in under a minute; hanging a network download off the front of it
# means a slow server in Vilnius can delay the report. It runs 40 minutes earlier
# instead, so a new timetable is in place before the night's analysis uses it.
set -e
cd /home/opc/vilnius

echo "=== 1. publish every version, not just the current one"
python3 - <<'PY'
p = "/home/opc/vilnius/publish.sh"
s = open(p).read()
old = '[ -f "$SRC/gtfs.zip" ] && cp -f "$SRC/gtfs.zip" "$PUB/gtfs/gtfs.zip"'
new = '''# Every timetable version we have ever held. The city publishes only the present,
# so once a version is gone it cannot be obtained again, and every retrospective
# claim about a past month depends on that month's schedule. About 3 MB each, a
# handful a year, which is cheap for data that is otherwise unrecoverable.
for f in "$SRC"/gtfs*.zip; do
  [ -f "$f" ] && cp -f "$f" "$PUB/gtfs/$(basename "$f")"
done
[ -f "$SRC/gtfs_state.json" ] && cp -f "$SRC/gtfs_state.json" "$PUB/gtfs/versions.json"'''
if "gtfs*.zip" in s:
    print("publish.sh: already ships every version")
else:
    assert old in s, "gtfs copy line not found"
    s = s.replace(old, new, 1)
    open(p + ".new", "w").write(s)
    import os; os.rename(p + ".new", p)
    print("publish.sh: now ships every version plus a manifest")
PY
bash -n /home/opc/vilnius/publish.sh

echo "=== 2. the timer"
sudo tee /etc/systemd/system/vilnius-gtfs.service >/dev/null <<'UNIT'
[Unit]
Description=Refresh the Vilnius GTFS timetable, keeping every version
After=network-online.target

[Service]
Type=oneshot
User=opc
WorkingDirectory=/home/opc/vilnius
ExecStart=/usr/bin/python3 -u /home/opc/vilnius/refresh_gtfs.py
Nice=19
IOSchedulingClass=idle
IOWeight=10
CPUWeight=10
CPUQuota=10%
MemoryHigh=64M
MemoryMax=96M
MemorySwapMax=0
TimeoutStartSec=180
UNIT

sudo tee /etc/systemd/system/vilnius-gtfs.timer >/dev/null <<'UNIT'
[Unit]
Description=Check the Vilnius timetable daily

[Timer]
# 40 minutes before the nightly summarise, so a new timetable is already in place
# when the night's analysis runs against it.
OnCalendar=*-*-* 23:40:00 UTC
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now vilnius-gtfs.timer

echo
echo "=== result"
systemctl is-active vilnius-gtfs.timer
systemctl list-timers "vilnius*" --no-pager | sed -n '2,5p'
