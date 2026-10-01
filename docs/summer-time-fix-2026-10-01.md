# Summer time: a fix before it broke

1 October 2026. Task #30, found during the weather audit the same day.

**Result: from 25 October the nightly chain would have produced empty days, not
merely mislabelled ones. It now follows Vilnius local time through the change, and
every output for the days already published is byte-for-byte unchanged.**

Lithuania leaves summer time on **25 October 2026**: local time goes from UTC+3 to
UTC+2. Every script on the box that turns a UTC snapshot into local time did it by
adding a fixed three hours.

---

## 1. What would have happened

The [weather audit](weather-audit-2026-10-01.md) said every hour label would be one
hour late. That understated it.

`segments.py`, which produces every per-hop table in this project, checks each GPS
fix against the snapshot's own clock: a fix more than 120 seconds older than "now" is
discarded as stale. The fix's time comes from the feed itself, `MatavimoLaikas`,
which is Vilnius wall-clock time. "Now" came from the snapshot's UTC stamp plus three
hours. From 25 October those two would disagree by an hour, and **every fix would
look an hour old.**

Tested on the box: the new `segments.py`, run on 29 September with its clock
deliberately set one hour wrong, read 173,345 rows and placed **0** of them.
`departure.py` has the same stale check and would have found no departures at all.
Nothing would have crashed. The nightly report and the published tables would simply
have gone empty from 26 October, with no alarm.

`blocks.py`, `summarize.py`, `export.py`, `build_report.py` and `build_map.py` would
have put every snapshot in the wrong local hour, and on the change night in the wrong
local day.

## 2. The fix

Every one of those scripts, plus `gapstat.py` and `validate_seg.py`, now converts with
Python's time-zone database, `Europe/Vilnius`, instead of adding three hours. A local
day is now computed as its real span in UTC: 24 hours most of the year, **25 hours on
25 October 2026** (21:00 UTC on the 24th to 22:00 UTC on the 25th) and **23 hours on
28 March 2027**.

The two weather analysis scripts, `weather_effect.py` and `weather_audit.py`, joined
the weather to bus hours with a fixed offset as well. They now convert the same way.

`segments.py` also now prints a warning when more than half of a day's fixes are
dropped as stale, so a clock disagreement can never again pass as a quiet day.

## 3. Checks

| check | result |
|---|---|
| old and new conversion, every 7 minutes from 14 Aug to 25 Oct 01:00 UTC | 14,820 timestamps, 0 differences |
| local-day bounds for summer days, old against new | identical |
| `segments.py` and `blocks.py`, old and new, on 29 September | segments, traversals and blocks files **identical**, sha256 2016f278…, 61ef563b…, 1a59b973… |
| `weather_effect.py` and `weather_audit.py` on the published data | output identical to the published documents |
| the new stale warning, with the clock set one hour wrong | 100% dropped, warning printed |

## 4. Also fixed

Run by hand late in the evening, `build_report.py` crashed. It took the day still in
progress as a finished one, because by evening the day has 20 hours of coverage, and
loaded that day's working file from 00:20, which holds three hours and no roads. The
nightly run, just after midnight, never hit it. A day is now only complete once it
has ended in Vilnius. Run again after the fix: primary 30 September, compared with
29 September, r = 0.913.

## 5. What remains imperfect

- **The repeated hour.** On 25 October the hour from 03:00 to 04:00 happens twice. The
  feed's own clock repeats with it, so a vehicle's chain of fixes breaks for about an
  hour and restarts, and the two hours share the label 03. This affects a handful of
  night trips on one night a year.
- **Night timetables on the two change nights.** GTFS measures times from "noon minus
  12 hours", which on 25 October is 01:00 summer time, not midnight. For trips before
  04:00 on 25 October and 28 March only, timetable positions may be an hour out. Every
  other day of the year is unaffected.
- **The map replay** in `summarize.py` numbers frames by wall-clock minute, so on 25
  October an hour of frames repeats its minute labels.
- `matchhour.py` and `probe.py` are one-off diagnostics hard-coded to 20 August and
  were left as they are.

## 6. The first day to check

**26 October**, the first full day in winter time. The day's segments log should show
almost no stale drops (29 September: 29,852 of 3.46 million rows, under 1%), and its
morning peak should sit at 07:00 to 09:00 local, not shifted an hour. A check is
scheduled.

Old versions of every changed script are kept on the box in `scratch/t30/bak-20261001`.
