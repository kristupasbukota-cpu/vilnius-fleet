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

renice -n 19 -p $$ >/dev/null 2>&1
ionice -c 3 -p $$ >/dev/null 2>&1

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
         cloud_setup.sh status.sh segments.py validate_seg.py runseg.sh publish.sh findrpm.py harden.sh dedupe.py; do
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

git config gc.auto 0
git config gc.autoDetach false
git config maintenance.auto false
git config pack.threads 1
git config pack.windowMemory 16m
git config pack.deltaCacheSize 16m
git config core.compression 1
git config core.bigFileThreshold 512k

# If somebody has edited the repository on GitHub, adopt their version of the prose
# before overwriting it. Generated files stay ours; README.md and STATE-OF-PLAY.md
# are theirs the moment they touch them.
git fetch -q origin main 2>/dev/null
if [ -n "$(git log --oneline HEAD..origin/main 2>/dev/null)" ]; then
  echo "remote has moved, adopting its prose"
  for f in README.md STATE-OF-PLAY.md; do
    if git cat-file -e "origin/main:$f" 2>/dev/null; then
      git show "origin/main:$f" > "$SRC/$f" && cp -f "$SRC/$f" "$PUB/$f"
    fi
  done
  git reset -q --hard origin/main
  # the reset threw away this run's generated files; put them back
  for f in arc.json baseline.json delaygrid.json framelist.txt; do
    [ -f "$SRC/$f" ] && cp -f "$SRC/$f" "$PUB/summaries/$f"
  done
  cp -f "$SRC/README.md" "$PUB/README.md" 2>/dev/null
  cp -f "$SRC/STATE-OF-PLAY.md" "$PUB/STATE-OF-PLAY.md" 2>/dev/null
fi

git add -A
if git diff --cached --quiet; then
  echo "nothing changed, not pushing"
  exit 0
fi
N=$(python3 -c "import json;print(json.load(open('status.json'))['snapshots'])" 2>/dev/null || echo "?")
git commit -q -m "summaries $(date -u +%Y-%m-%d\ %H:%M) UTC, $N snapshots collected"
if git push -q origin main 2>&1 | tail -3; then
  echo "pushed: $(git rev-parse --short HEAD)  $(git log -1 --format=%s)"
else
  echo "PUSH FAILED, commit $(git rev-parse --short HEAD) is local only" >&2
  exit 1
fi
