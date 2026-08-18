#!/bin/bash
# One-screen health check for the collector box.
#   bash status.sh        -> sample the snapshot count over 25 s
#   bash status.sh 60     -> sample it over 60 s
cd "$(dirname "$0")" || exit 1
W="${1:-25}"

echo "UPTIME     $(uptime -p)"
echo "SERVICE    $(systemctl is-active vilnius-collector) / $(systemctl is-enabled vilnius-collector)"
echo "TIMER      $(systemctl is-active vilnius-summarize.timer), next $(systemctl list-timers vilnius-summarize.timer --no-pager 2>/dev/null | sed -n 2p | cut -c1-29)"
echo "MEM        $(awk '/MemTotal/{t=$2}/MemAvailable/{a=$2}END{printf "%d MB total, %d MB available", t/1024, a/1024}' /proc/meminfo)"

N1=$(ls snapshots 2>/dev/null | wc -l | tr -d ' ')
sleep "$W"
N2=$(ls snapshots 2>/dev/null | wc -l | tr -d ' ')
echo "SNAPSHOTS  $N1 -> $N2  (+$((N2-N1)) in ${W}s)"
echo "NEWEST     $(ls snapshots | tail -1)    clock $(date -u +%Y%m%dT%H%M%SZ)"
echo "SIZE       $(du -sh snapshots | cut -f1)"
echo "DISK       $(df -h . | tail -1 | awk '{print $3" used, "$4" free, "$5" full"}')"
echo "FAILS      $(grep -c FAIL collector.log 2>/dev/null; true)"
echo "LOG"
tail -3 collector.log 2>/dev/null | sed 's/^/           /'
