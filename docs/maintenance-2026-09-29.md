# Maintenance, 29 September

Operations note. Two items off the board (#25, #11), one weakness found on the
way, and one note for whoever next moves files to the box.

---

## 1. departure.py loads only the timetables in force (#25)

The same change `segments.py` got on 26 September, for the same reason: loading
the union of every archived timetable version is what slowed the nightly chain
until it failed. `departure.py` is not in the nightly chain, but it had the same
loader. By default it now keeps the last four versions that can be in force on
`--day`. `--gtfs-until` still reproduces an old union run exactly, so the
published August files remain reproducible, and `--gtfs-all` loads everything.

Regression on 24 August against the published file:

| | published (12-version union) | new default (4 versions) |
|---|---|---|
| departures | 10,088 | 10,088 |
| every deviation, scheduled time and timing stop | | **identical** |
| early-departure share, both-bays rule | 2.052% | **2.052%**, no flag changes |
| run time | | 59 s, 165 MB peak |

Two bookkeeping columns differ, and both differences favour the new loader:

- **Route 114, 5 trips:** `direction` is 0 in the timetable in force on 24 August
  and 1 in a version published afterwards.
- **Route 59, 25 trips:** the same stop at the same time is `timing_seq` 1 then
  and 2 later, because a later version inserted a stop in front of it.

So the union loader was not only slow. It let timetables published after a day
rewrite that day's metadata. The published August files were left as they are.

## 2. The nightly report now shows every day (#11)

The report computed a total for every day and never displayed it. It now has a
section "6. Day by day": one bar per complete day since 15 August, net
vehicle-hours of lateness, weekdays and weekends in the report's existing blue
and orange (both pass all six colour checks in light and dark), the 1 September
network change marked, a hover on every bar and a table view.

Building it exposed that the report could only see the three or four days whose
working files were still on disk, because `export.py` compresses each finished
day into `pub/segments/` and removes the working copy. The history is now read
from there, **each day once, ever**, and remembered in `daily_totals.json`. The
nightly cost is one day's file however long the archive gets.

Regression against the old builder on the same inputs: every part of the report
identical, totals for the days the old builder could see identical, history 46
days (45 complete), 11.5 s on the first run while it builds the history and
9.4 s after, peak memory unchanged at 109 MB.

## 3. A panel that could blank the page

The "Is it real?" panel read its comparison grid without checking that a second
working day existed. When one did not, it threw, and because every panel was drawn
in one sequence, everything after it went blank too. The panel now steps aside
when there is nothing to compare, and each panel is drawn on its own, so one that
fails cannot take the others with it. The nightly report has always had a
comparison day, so this never showed in production; the test harness hit it.

## 4. For whoever next moves files to the box

Sending a file through the Mac under a name already used earlier in a session
delivered the **earlier** file while reporting success. The box ran a stale test
script before the hash check caught it. Every transfer today was therefore sent
under a fresh name and checked by `sha256sum` at each hop. Do both.

## Files

`code/departure.py` (`departure.py.bak-20260929`), `code/build_report.py`
(`build_report.py.bak-20260929`), `code/report_template.html`
(`report_template.html.bak-20260929`). Test and patch scripts from 20 to 29
September are in `~/vilnius/scratch/` on the box.
