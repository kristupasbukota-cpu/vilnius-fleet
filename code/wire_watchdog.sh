#!/bin/bash
# Install the watchdog: a 15 minute timer, a tiny repository for the heartbeat, and
# the GitHub workflow that raises the alarm when the heartbeat stops.
#
# The watchdog is capped harder than anything else on this box. It exists because
# unbounded jobs have taken the machine down three times, so a watchdog that could
# do the same would be worse than none at all.
set -e
cd /home/opc/vilnius

REMOTE="git@github.com:kristupasbukota-cpu/vilnius-fleet.git"

echo "=== 1. the heartbeat repository"
# Its own repository, on its own branch, holding one file and one commit that gets
# amended forever. Keeping it out of pub/ means a heartbeat every 15 minutes cannot
# put 35,000 commits into the history that holds the actual summaries.
if [ ! -d hb/.git ]; then
  mkdir -p hb
  git init -q -b status hb
  git -C hb remote add origin "$REMOTE"
fi
git -C hb config user.name "vilnius-collector"
git -C hb config user.email "collector@localhost"
git -C hb config gc.auto 0
git -C hb config pack.threads 1
git -C hb config pack.windowMemory 8m
git -C hb config core.compression 1
echo "ok"

echo "=== 2. the workflow, staged for the next publish"
mkdir -p pub/.github/workflows
cp -f /home/opc/vilnius/heartbeat.yml pub/.github/workflows/heartbeat.yml
echo "staged pub/.github/workflows/heartbeat.yml"

echo "=== 3. the timer"
sudo tee /etc/systemd/system/vilnius-watchdog.service >/dev/null <<'UNIT'
[Unit]
Description=Check the Vilnius collector and send a heartbeat to GitHub

[Service]
Type=oneshot
User=opc
WorkingDirectory=/home/opc/vilnius
ExecStart=/usr/bin/python3 -u /home/opc/vilnius/watchdog.py
Nice=19
IOSchedulingClass=idle
IOWeight=10
CPUWeight=10
CPUQuota=10%
MemoryHigh=64M
MemoryMax=96M
MemorySwapMax=0
TimeoutStartSec=240
UNIT

sudo tee /etc/systemd/system/vilnius-watchdog.timer >/dev/null <<'UNIT'
[Unit]
Description=Run the Vilnius watchdog every 15 minutes

[Timer]
OnBootSec=3min
OnUnitActiveSec=15min
AccuracySec=30s

[Install]
WantedBy=timers.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now vilnius-watchdog.timer

echo
echo "=== result"
systemctl is-active vilnius-watchdog.timer
systemctl list-timers "vilnius*" --no-pager | sed -n '2,4p'
