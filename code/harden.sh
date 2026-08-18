#!/bin/bash
# Stop the box killing itself.
#
# 18 August, 10:36 to 11:24 UTC: the whole machine stopped executing userspace for
# 48 minutes. Not sshd starving, not our job. The collector log has a hole of
# exactly that shape, and the kernel logged one line in the middle of it about the
# scheduler lagging. The cause is in the journal:
#
#   kernel: oom-kill: constraint=CONSTRAINT_NONE, global_oom,
#           task_memcg=/system.slice/dnf-makecache.service, task=dnf, pid=7429
#   kernel: Out of memory: Killed process 7429 (dnf) anon-rss:722748kB
#
# dnf-makecache is a stock Oracle Linux timer that refreshes package metadata. It
# ran on its own schedule, with no memory limit, and grew to 722 MB on a 946 MB
# machine. Everything else went into reclaim and stayed there until the global OOM
# killer finally got a slice of CPU at 11:24 and shot it.
#
# The two earlier freezes I blamed on myself were the same program, run by hand.
# Once I started capping my own dnf calls with systemd-run they were cleanly
# OOM-killed inside their cgroup and the box survived. This one was not capped
# because I never started it.
#
# So: dnf never runs unattended again, and if anyone runs it by hand it dies in a
# cgroup rather than taking the machine with it.
set -e

echo "=== 1. dnf: no unattended runs, and a hard cap when run by hand"
sudo systemctl disable --now dnf-makecache.timer 2>/dev/null || true
sudo systemctl mask dnf-makecache.timer dnf-makecache.service
sudo mkdir -p /etc/systemd/system/dnf-makecache.service.d
sudo tee /etc/systemd/system/dnf-makecache.service.d/cap.conf >/dev/null <<'D'
[Service]
MemoryMax=200M
MemorySwapMax=0
D

echo "=== 2. PCP: 60 MB of performance metrics nobody reads"
# pmcd alone holds 49.6 MB resident, plus four timers a day. This box has 946 MB
# and just died of memory exhaustion; the monitoring is not worth the memory.
for u in pmlogger pmie pmcd pmproxy; do
  sudo systemctl disable --now "$u" 2>/dev/null || true
done
for t in pmlogger_check pmlogger_farm_check pmie_check pmie_farm_check pmlogger_daily pmie_daily; do
  sudo systemctl disable --now "$t.timer" 2>/dev/null || true
done

echo "=== 3. updatedb: stop indexing 22,000 snapshot files every night"
sudo systemctl disable --now mlocate-updatedb.timer 2>/dev/null || true

echo "=== 4. the nightly job, on a leash it can actually feel"
# The old limits were MemoryMax=350M and CPUQuota=45%, which on a shape that gets
# about an eighth of a core are both looser than the hardware. Measured, the job
# needs 5 seconds of CPU and peaks at 66 MB, so these are generous and still bind.
sudo tee /etc/systemd/system/vilnius-summarize.service >/dev/null <<'UNIT'
[Unit]
Description=Summarise the Vilnius snapshots, then publish them to GitHub

[Service]
Type=oneshot
User=opc
WorkingDirectory=/home/opc/vilnius
ExecStart=/usr/bin/python3 -u /home/opc/vilnius/summarize.py
ExecStart=/bin/bash /home/opc/vilnius/publish.sh
Nice=19
IOSchedulingClass=idle
IOWeight=10
CPUWeight=10
CPUQuota=25%
MemoryHigh=180M
MemoryMax=260M
MemorySwapMax=0
TimeoutStartSec=900
UNIT

echo "=== 5. the collector outranks everything else on this box"
sudo mkdir -p /etc/systemd/system/vilnius-collector.service.d
sudo tee /etc/systemd/system/vilnius-collector.service.d/priority.conf >/dev/null <<'D'
[Service]
Nice=-5
CPUWeight=1000
IOWeight=1000
# Reclaim from anything else before touching the collector.
MemoryLow=120M
D

sudo systemctl daemon-reload
sudo systemctl restart vilnius-collector

echo
echo "=== result"
systemctl is-active vilnius-collector vilnius-summarize.timer
echo "-- masked/disabled:"
systemctl is-enabled dnf-makecache.timer pmcd pmlogger mlocate-updatedb.timer 2>&1 | tr '\n' ' '
echo
echo "-- timers left:"
systemctl list-timers --all --no-pager | sed -n '2,20p' | awk '{print $NF}' | sort -u | tr '\n' ' '
echo
free -m | sed -n 2p
