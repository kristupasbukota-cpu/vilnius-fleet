#!/bin/bash
# Push the summaries to GitHub so they can be read without anyone's laptop being on.
#
# Only the summaries go, not the raw snapshots. 300 MB a day of small binary files
# would make the repository unusable within weeks, and the summaries are enough to
# rebuild every chart except the map replay. The raw archive stays here and on the
# Mac, which is already two copies.
set -u
cd "$(dirname "$0")" || exit 1
SRC="$PWD"
PUB="$SRC/pub"
REMOTE="git@github.com:kristupasbukota-cpu/vilnius-fleet.git"

mkdir -p "$PUB/summaries" "$PUB/code" "$PUB/gtfs"

# A health file, so the state of the collector is visible without an SSH session.
python3 - "$SRC" > "$PUB/status.json" <<'PY'
import json, os, subprocess, sys, glob, datetime
src = sys.argv[1]
snaps = sorted(os.path.basename(p) for p in glob.glob(os.path.join(src, "snapshots", "*.csv.gz")))
def sh(c):
    try: return subprocess.run(c, shell=True, capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception: return ""
log = []
try:
    log = open(os.path.join(src, "collector.log")).read().splitlines()[-3:]
except Exception:
    pass
fails = sum(1 for l in open(os.path.join(src, "collector.log")) if "FAIL" in l) if os.path.exists(os.path.join(src,"collector.log")) else 0
json.dump({
    "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "uptime": sh("uptime -p"),
    "collector": sh("systemctl is-active vilnius-collector"),
    "timer": sh("systemctl is-active vilnius-summarize.timer"),
    "snapshots": len(snaps),
    "first": snaps[0] if snaps else None,
    "newest": snaps[-1] if snaps else None,
    "bytes_on_disk": int(sh("du -sb %s/snapshots | cut -f1" % src) or 0),
    "disk": sh("df -h %s | tail -1" % src),
    "memory_mb": sh("awk '/MemTotal/{t=$2}/MemAvailable/{a=$2}END{printf \"%d total, %d available\", t/1024, a/1024}' /proc/meminfo"),
    "collector_failures": fails,
    "log_tail": log,
}, sys.stdout, indent=1)
PY

for f in arc.json baseline.json delaygrid.json framelist.txt; do
  [ -f "$SRC/$f" ] && cp -f "$SRC/$f" "$PUB/summaries/$f"
done
for f in collect.py summarize.py blocks.py build_map.py build_network.py template.html \
         cloud_setup.sh status.sh publish.sh findrpm.py; do
  [ -f "$SRC/$f" ] && cp -f "$SRC/$f" "$PUB/code/$f"
done
[ -f "$SRC/README.md" ] && cp -f "$SRC/README.md" "$PUB/README.md"
[ -f "$SRC/STATE-OF-PLAY.md" ] && cp -f "$SRC/STATE-OF-PLAY.md" "$PUB/STATE-OF-PLAY.md"
[ -f "$SRC/gtfs.zip" ] && cp -f "$SRC/gtfs.zip" "$PUB/gtfs/gtfs.zip"

cd "$PUB" || exit 1
if [ ! -d .git ]; then
  git init -q -b main
  git remote add origin "$REMOTE"
fi
printf '%s\n' 'snapshots/' 'state.json.gz' '*.part' > .gitignore

git add -A
if git diff --cached --quiet; then
  echo "nothing changed, not pushing"
  exit 0
fi
N=$(python3 -c "import json;print(json.load(open('status.json'))['snapshots'])" 2>/dev/null || echo "?")
git commit -q -m "summaries $(date -u +%Y-%m-%d\ %H:%M) UTC, $N snapshots collected"
git push -q origin main 2>&1 | tail -3
echo "pushed: $(git rev-parse --short HEAD)  $(git log -1 --format=%s)"
