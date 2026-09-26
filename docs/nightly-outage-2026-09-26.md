# Three nights without a publish, and why nothing said so

26 September 2026. An operations note, not a finding. No data was lost: the
collector never stopped and every snapshot is on the box. What stopped was the
nightly chain that turns snapshots into published tables.

---

## 1. What happened

The nightly service runs four steps at 00:20 UTC: `summarize.py`,
`nightly_segments.sh`, `export.py`, `publish.sh`. Each step has a 40-minute limit.
On **24, 25 and 26 September** `export.py` hit that limit and was killed, so
nothing after it ran and nothing was pushed. Traversal tables for 23, 24 and 25
September were not published, and neither was `status.json`.

It was not sudden. The chain had been getting slower every night:

| night | before export | whole run |
|---|---|---|
| 17 Sep | 13 min | 27 min |
| 20 Sep | 15 min | 37 min |
| 22 Sep | 26 min | 62 min |
| 23 Sep | 26 min | 65 min |
| 24 Sep | 34 min | killed in export after 40 min |
| 25 Sep | 36 min | killed in export after 40 min |
| 26 Sep | 43 min | killed in export after 40 min |

## 2. Why

`segments.py` joined every day's readings to the timetable by loading the union
of **every timetable version ever archived**, later versions winning. That was the
right call on 18 August, with two versions. Since 29 August the city has
republished daily, so by 26 September it was loading 37 versions, 138 MB of zips,
one more each night, into a service with a soft memory limit of 260 MB. Past a soft
limit the kernel throttles a process rather than killing it, so the job did not fail
loudly. It just got slower until it stopped fitting. The step-change on 22
September is consistent with the union crossing that limit.

`segments.py` runs three times a night (yesterday, today, then again inside
`export.py` for the day being exported), so the cost was paid three times.

## 3. The fix

With `--day`, `segments.py` now loads only the versions that can describe that
day: archives are named by the UTC date they were downloaded at 23:40 UTC, which
is already the next local day, so it keeps the last four versions dated no later
than the day after. `--gtfs-all` restores the old behaviour.

Regression test on 22 September, a day already exported with the full union:

| | full union, as published | four versions |
|---|---|---|
| versions loaded | 37 at the time of the test | 4 |
| run time | about 20 to 35 min under the service limits | 2 min 23 s without them |
| peak memory | throttled at 260 MB | 171 MB |
| traversal rows | 202,779 | 202,779, **identical row for row** |
| segments file | | **identical byte for byte** |

The 33 extra versions contributed nothing to the output.

## 4. Why nothing said so

The watchdog was built on 18 August to catch exactly this, and it did not. Its
nightly check was the age of `arc.json`, which the **first** step writes, and the
first step kept succeeding. Its publish check fires when the local repository has
a commit GitHub lacks, but a chain that dies before `publish.sh` never makes one.
Both checks passed every 15 minutes for three days while the chain was dead.

I also missed it once directly. On the 24th I ran `publish.sh` by hand to push
the departure work, which refreshed `status.json`, and on the 22nd's status check
everything had been genuinely fine. The failure at 01:33 UTC on the 24th sat
between the two.

The watchdog now also raises an alarm if the last publish commit is more than 26
hours old, or if the nightly service is in the failed state. Run dry against the
broken state it reported both: `[publish_missed] [nightly_failed]`. The live
watchdog then raised `[publish_missed]` for real at 12:59 UTC, while the catch-up
was running, and cleared itself at 13:14, after the push landed.

## 4b. Catch-up

Two manual runs of the nightly service on 26 September, under its normal limits:

| run | exported | before export | whole run |
|---|---|---|---|
| 12:47 UTC | 23 and 24 September | 6 min | 17 min |
| 13:06 UTC | 25 September | 6 min | 11.5 min |

Against 43 minutes before export and a kill at 82 minutes the night before. 39
complete days are published, through 25 September, with no gaps.

## 5. What this says about the project

The lesson is the same as the git one on 9 September, from the other side. There,
a benchmark ignored the box's constraint. Here, a design choice that fit the
constraint on 18 August silently stopped fitting as the archive grew, and nothing
measured the growth. Two things follow:

- **Anything that loads "all versions" or "all days" is a scaling bug waiting for
  its date.** `departure.py` has the same union loader. It is not in the nightly
  chain and already takes `--gtfs-until`, but it should get the same selection
  before it ever is.
- **A check should watch the last step, not the first.** "Did the thing we
  ultimately want happen" is the only alarm that cannot be fooled by partial
  success.

## Files

`code/segments.py` (previous version on the box as `segments.py.bak-20260926`),
`code/watchdog.py` (`watchdog.py.bak-20260926`).
