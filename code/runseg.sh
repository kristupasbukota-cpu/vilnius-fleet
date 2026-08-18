#!/bin/bash
# One segment file per day, plus one over everything. Kept per-day because a
# holiday, a Sunday and a working day are three different road networks wearing
# the same paint, and averaging them together gives a finding true of nothing.
#
# Each run names its own output. The first version of this wrote a shared
# segments.json and renamed it afterwards, which is a race the moment anything else
# touches the directory, and the resulting file looks perfectly normal.
cd "$(dirname "$0")" || exit 1
for d in "$@"; do
  python3 segments.py --day "$d" --out "segments-$d.json" > "/tmp/seg_$d.log" 2>&1 \
    && echo "done $d" || echo "FAILED $d"
done
python3 segments.py --out segments-all.json > /tmp/seg_all.log 2>&1 && echo "done all"
echo ALLDONE
