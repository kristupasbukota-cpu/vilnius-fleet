# The nightly report was comparing every day against August

30 September 2026. A correction to the automatically built report,
`report/segments-report.html`. None of the finding documents relied on the
affected panels.

## What was wrong

The report shows one working day (the "primary" day) and checks it two ways:
against the previous working day ("Is it real?", with a correlation in the
headline stats) and against the most recent weekend day (the weekend column in
"The worst roads", and the second series in "When").

It chose those comparison days only from the segments files still on the box. Once
`export.py` began compressing each finished day and removing its working copy, the
only older files left were three stale ones from 15, 16 and 17 August. So from
early September **every nightly report compared the new day against Monday 17
August and Sunday 16 August**.

## What it changed

On the report built for Tuesday 29 September:

| | as published | corrected |
|---|---|---|
| comparison working day | 17 August | 28 September |
| comparison weekend day | 16 August | 27 September |
| day-to-day correlation, same segments | 0.50 | **0.90** |
| worst stretch, seconds lost at the weekend | 23.5 | 63.3 |

The report was **understating how well the network repeats itself**, because it was
comparing an autumn Tuesday with a summer Monday on a network that changed on 1
September. Everything derived from the primary day alone (the map, the worst roads,
the hourly shape, the concentration curve, the day-by-day chart, the headline
vehicle-hours) was unaffected and reproduces exactly.

## The fix

Comparison days are now chosen from every published day, not only the files still
on disk, and must be complete days before the primary one. A day's working file is
preferred where it exists, otherwise the published copy is read, and only the
three days the page draws are loaded. Existence is checked without parsing
anything. Tested against the report published at 00:27 UTC on 30 September: every
primary-derived figure identical, only the comparison parts changed, same days
chosen with and without an explicit date, 105 MB peak, about 10 seconds.

## Still stale

Some explanatory text in the report template was written by hand on 18 August and
never updated: a caveat about a 0.854 Monday-Tuesday agreement, a note on the
concentration chart, and a chart label reading "Monday against Tuesday". It no
longer describes what the page shows and is on the board to fix.

## Files

`code/build_report.py` (previous version on the box as `build_report.py.bak-20260930`).
