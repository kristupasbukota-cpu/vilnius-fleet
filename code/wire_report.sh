#!/bin/bash
# Let the box build the report as well as the data.
#
# Until now segments-*.json rebuilt itself nightly while segments-report.html was
# built by hand, so the repository's data was current and its report was not. The
# report also had a date baked into every sentence, which is how a page quietly
# becomes a lie. build_report.py picks its own days, checks they are actually
# complete before comparing them, and writes every day-specific string from the
# numbers rather than from memory.
set -e
cd /home/opc/vilnius

echo "=== 1. run it after the segment join each night"
cat > /home/opc/vilnius/nightly_segments.sh <<'INNER'
#!/bin/bash
# Re-run the stop-segment join for the two days that can still change, then rebuild
# the report from whatever complete days now exist.
cd "$(dirname "$0")" || exit 1
for d in "$(date -u -d 'yesterday' +%F)" "$(date -u +%F)"; do
  python3 segments.py --day "$d" --out "segments-$d.json" >> /tmp/segments-nightly.log 2>&1 \
    && echo "segments: $d" || echo "segments: FAILED $d"
done
python3 build_report.py >> /tmp/segments-nightly.log 2>&1 \
  && echo "report: rebuilt" || echo "report: FAILED"
INNER
chmod +x /home/opc/vilnius/nightly_segments.sh

echo "=== 2. publish what it makes"
python3 - <<'PY'
p = "/home/opc/vilnius/publish.sh"
s = open(p).read()
if "pub/report" not in s:
    old = 'mkdir -p "$PUB/segments"'
    new = '''# The report and the data behind it. Gzipped because git keeps every version of
# every blob forever and the uncompressed pair is about 280 KB a night.
mkdir -p "$PUB/report"
[ -f "$SRC/segments-report.html" ] && cp -f "$SRC/segments-report.html" "$PUB/report/segments-report.html"
[ -f "$SRC/segdata.json" ] && gzip -9 -c "$SRC/segdata.json" > "$PUB/report/segdata.json.gz"

mkdir -p "$PUB/segments"'''
    assert old in s
    s = s.replace(old, new, 1)
    open(p + ".new", "w").write(s); import os; os.rename(p + ".new", p)
    print("publish.sh: report step added")
else:
    print("publish.sh: already publishes the report")
PY
bash -n /home/opc/vilnius/publish.sh
echo ok
