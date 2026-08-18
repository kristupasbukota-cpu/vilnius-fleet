#!/bin/bash
# Install the Vilnius collector on a fresh always-on Linux box.
#
# Expects collect.py and summarize.py to already sit next to this script.
# Idempotent: safe to run again after a change.
#
#   bash cloud_setup.sh            -> 10 second polling (default)
#   bash cloud_setup.sh 4          -> 4 second polling, full feed resolution
set -euo pipefail

INTERVAL="${1:-10}"
DIR="$(cd "$(dirname "$0")" && pwd)"
USER_NAME="$(id -un)"
PY="$(command -v python3)"

[ -f "$DIR/collect.py" ]   || { echo "collect.py is not next to this script"; exit 1; }
[ -f "$DIR/summarize.py" ] || { echo "summarize.py is not next to this script"; exit 1; }
mkdir -p "$DIR/snapshots"

echo "==> python:   $PY ($("$PY" -V 2>&1))"
echo "==> project:  $DIR"
echo "==> user:     $USER_NAME"

# The collector itself. Restart=always is the whole point of moving off a laptop:
# if the process dies, systemd starts it again; if the machine reboots, it comes
# back on its own. caffeinate could do neither.
sudo tee /etc/systemd/system/vilnius-collector.service >/dev/null <<UNIT
[Unit]
Description=Vilnius live vehicle feed collector
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$DIR
ExecStart=$PY -u $DIR/collect.py $INTERVAL
Restart=always
RestartSec=10
# The feed is one small HTTP request every $INTERVAL s. If this ever uses real
# memory something has gone wrong, so cap it rather than let it take the box down.
MemoryMax=512M

[Install]
WantedBy=multi-user.target
UNIT

# Nightly summaries, so the expensive pass happens once on the box rather than
# every time anyone wants to look at the data.
sudo tee /etc/systemd/system/vilnius-summarize.service >/dev/null <<UNIT
[Unit]
Description=Summarise the Vilnius snapshots into arc/baseline/delaygrid

[Service]
Type=oneshot
User=$USER_NAME
WorkingDirectory=$DIR
ExecStart=$PY -u $DIR/summarize.py
Nice=10
UNIT

sudo tee /etc/systemd/system/vilnius-summarize.timer >/dev/null <<UNIT
[Unit]
Description=Run the Vilnius summariser nightly

[Timer]
OnCalendar=*-*-* 00:20:00 UTC
Persistent=true

[Install]
WantedBy=timers.target
UNIT

# One line a minute is ~40 MB a year. Small, but rotate it anyway so a runaway
# failure loop cannot fill the disk that the actual data needs.
sudo tee /etc/logrotate.d/vilnius >/dev/null <<ROT
$DIR/collector.log {
    weekly
    rotate 8
    compress
    missingok
    notifempty
    copytruncate
}
ROT

sudo systemctl daemon-reload
sudo systemctl enable --now vilnius-collector.service
sudo systemctl enable --now vilnius-summarize.timer

echo
echo "==> waiting 40 s to confirm it is actually collecting"
BEFORE=$(ls "$DIR/snapshots" | wc -l | tr -d ' ')
sleep 40
AFTER=$(ls "$DIR/snapshots" | wc -l | tr -d ' ')

echo
systemctl is-active --quiet vilnius-collector && echo "    service: active" || echo "    service: NOT ACTIVE"
echo "    snapshots: $BEFORE -> $AFTER (+$((AFTER-BEFORE)) in 40 s, expect about $((40/INTERVAL)))"
echo "    disk:"
df -h "$DIR" | tail -1 | sed 's/^/      /'
echo "    log tail:"
tail -3 "$DIR/collector.log" 2>/dev/null | sed 's/^/      /' || echo "      no log yet"
echo
if [ "$AFTER" -gt "$BEFORE" ]; then
  echo "==> collector is running at ${INTERVAL}s and survives reboots."
else
  echo "!!! nothing was written. check:  journalctl -u vilnius-collector -n 40 --no-pager"
  exit 1
fi
