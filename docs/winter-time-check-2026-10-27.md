# The first winter-time days came through cleanly

27 October 2026. The check promised in the [summer-time fix](summer-time-fix-2026-10-01.md):
Lithuania left summer time on 25 October, and the nightly chain had to switch from
UTC+3 to UTC+2 without losing or shifting anything.

**Result: it did.** Nothing was lost, nothing moved by an hour, and weather joins to the
right local hours. One unrelated gap turned up and was repaired: the weather file for
21 October held 1 hour instead of 24.

## What was checked

| check | expected | found |
|---|---|---|
| Stale fixes dropped, 26 Oct | under about 1% | 34,391 of 3,470,154 rows, **0.99%**. Weekdays 16 to 23 October: 0.86 to 1.47% |
| Stale fixes dropped, 25 Oct | under about 1% | 14,603 of 2,286,683, **0.64%**. Sunday 18 October: 0.51% |
| WARNING lines in the segments log | none | **none** |
| `trav-2026-10-25` on GitHub | a normal Sunday | **142,376 hops, 8,474 trips**. Sunday 18 October: 139,458 and 8,309 |
| `trav-2026-10-26` on GitHub | a normal Monday | **203,020 hops, 11,743 trips**. Monday 19 October: 200,987 and 11,686 |
| Hops far off their timetable | none: an hour's error would show as ±3,600 s | **0.00%** off by more than 30 minutes on either day; median 0.0 s on the 26th |
| Hop hour against the trip's scheduled start hour | the same hour or the next | **99.2%** on 26 October, as on 19 October |
| Morning peak, 26 Oct | at 07 to 08 local | **07: +13.1 s per hop, 08: +10.7**. On 19 October: +11.7 and +7.9 |
| Weather join | 25 local hours on 25 October, hour 03 twice | **25 hours**, 03 from 01:00 and 02:00 UTC. On 26 October the 06:00 UTC reading lands on local 07 |

Hour by hour, the hop counts on Monday 26 October follow Monday 19 October to within
about 2% in every hour from 04 to 10. Had the clock been handled wrong, the profile
would have moved a whole hour. The morning of the 26th was wet (0.8 to 1.5 mm an hour
between 07 and 09), which fits its slightly higher delay.

The repeated hour on the night of the 25th behaved as the fix document described: hour
03 holds 632 hops against 576 a week earlier, not double. The timetable runs each
03:xx trip once, whichever of the two 03:00 hours it falls in, and none of those hops
reads as an hour early or late.

## The gap found on the way

`weather/weather-2026-10-21.csv` held only the 00:00 UTC reading. The nightly log shows
the full 24 hours were fetched on 22 October. Most likely they were then undone by
the publish step's reset, which until 22 October ran after the night's files were
written (`publish.sh` records the fix). Every other weather day is complete.

Repaired on 27 October with `python3 weather.py --from 2026-10-21 --to 2026-10-21`: now
24 hours. The short version is kept on the box in `scratch/`. Any weather result that
included 21 October was missing that day's rain. The published weather figures predate
it, so none changes.

## Method

Read-only checks on `/tmp/segments-nightly.log` and `/tmp/weather-nightly.log` on the
box. From the repository: `analysis/trav-2026-10-18.csv.xz` to `trav-2026-10-26.csv.xz`,
and `weather/weather-2026-10-*.csv` mapped to local hours exactly as
`code/weather_effect.py` does.
