#!/bin/bash
# Put the derived-table export into the nightly chain.
#
# Until now the repository held tables for 18 and 19 August and nothing after, so
# losing this machine meant losing every day since. The raw archive cannot be
# published, at roughly 2.3 GB a month of small binary files, but the tables
# derived from it can, at about 2.6 MB a day compressed, and those are what any
# analysis actually reads.
#
# It goes into the existing nightly unit rather than a timer of its own. Publishing
# has to happen after the export or the night's work sits on the box until the
# following night, and the two are already one job.
#
# The limits go up because the export is the heaviest thing in the chain: measured
# peak resident size 136 MB against a 260 MB ceiling that was set for the
# summariser, and about 2 minutes 20 seconds a day at 50% of one CPU, so roughly
# 5 minutes a day inside a 25% quota.
set -e
cd /home/opc/vilnius

echo "=== 1. rewrite the unit"
sudo tee /etc/systemd/system/vilnius-summarize.service >/dev/null <<'UNIT'
[Unit]
Description=Summarise the Vilnius snapshots, join them to the timetable, export, publish

[Service]
Type=oneshot
User=opc
WorkingDirectory=/home/opc/vilnius
ExecStart=/usr/bin/python3 -u /home/opc/vilnius/summarize.py
ExecStart=/bin/bash /home/opc/vilnius/nightly_segments.sh
ExecStart=/usr/bin/python3 -u /home/opc/vilnius/export.py
ExecStart=/bin/bash /home/opc/vilnius/publish.sh
Nice=19
IOSchedulingClass=idle
IOWeight=10
CPUWeight=10
CPUQuota=25%
MemoryHigh=260M
MemoryMax=360M
MemorySwapMax=0
TimeoutStartSec=2400
UNIT

echo "=== 2. reload and confirm"
sudo systemctl daemon-reload
systemctl cat vilnius-summarize.service | grep -E "ExecStart|Memory|Timeout"

echo
echo "=== 3. the timer is unchanged"
systemctl is-active vilnius-summarize.timer
systemctl list-timers --no-pager | grep summarize

echo
echo "=== 4. what the export would do on the next run"
nice -n 19 python3 export.py --dry
