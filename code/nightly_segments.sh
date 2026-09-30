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
# Weather for yesterday and today, beside the bus record. A failure here must not
# stop anything else, so it runs last and its exit status is only reported.
python3 weather.py >> /tmp/weather-nightly.log 2>&1 \
  && echo "weather: ok" || echo "weather: FAILED"
