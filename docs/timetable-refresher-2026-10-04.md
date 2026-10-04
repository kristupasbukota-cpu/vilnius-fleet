# The timetable refresher was killed every night for a week

4 October 2026. Operations. Found by the first-night check of the repository
growth change, fixed the same day.

**What happened.** From 27 September to 3 October every nightly run of
`refresh_gtfs.py` was killed by systemd at its 180 s timeout. Each run had
already downloaded and installed any new timetable before it was stopped, so
**every version the city published is held, and every analysis used the right
timetable**. What the killed runs never got to do was write `gtfs_state.json`,
published as `gtfs/versions.json`. That file stopped at 26 September. The nightly
match rate, how many running vehicles resolve to a known trip, was not measured
for seven nights.

**Why.** After installing, the refresher measures the match rate on a recent
snapshot. To find one it listed and sorted the whole snapshot archive. By
27 September the archive held about 350,000 files, and that list alone needed
about 85 MB (100 MB at today's 420,000). The service is capped at 64 MB
(`MemoryHigh`) and 96 MB (`MemoryMax`) so it can never starve the collector. Over
the cap it was throttled to a crawl and killed at the timeout. It used about 1 s
of CPU in 3 minutes.

**Fix.**

- `refresh_gtfs.py` lists only the last two UTC days of snapshots. The lookback
  is at most about 12 hours, so nothing is lost.
- The service timeout is raised from 180 to 600 s with a systemd drop-in,
  `vilnius-gtfs.service.d/timeout.conf`. Under its 10% CPU quota the full run
  now takes 45 s with a peak of 54 MB.
- The five versions installed during the gap (downloaded 27, 29 and 30 September and
  1 and 2 October) were added to `gtfs_state.json` from their own archived files.
  They are marked `"backfilled"`, and their fingerprints match the archived zips.
  The match-rate history has no entries for those seven nights; nothing can recover
  them.
- After the fix: the run on 4 October 10:17 UTC succeeded, timetable unchanged,
  match rate **98.7%** of 375 vehicles.

**Why nobody noticed for a week.** The watchdog did see it. From late on 29 September its
heartbeat carried the warning "the timetable has not been checked for 3 days; no
error recorded". But warnings go to the `status` branch, which nothing reads, and
"no error recorded" was true: a killed process cannot record why it died. The
watchdog now asks systemd and adds the last run's result, for example "timeout",
to that warning. The gap that remains is that warnings reach no person. That is a
decision for the project, not something to change silently.

**The watchdog had the same flaw.** It too listed every snapshot, and also checked
each file's timestamp, every 15 minutes under the same 64 MB and 10% CPU caps. It
needed about 70 s of its 240 s and was getting slower. From the morning of
4 October it began timing out, so the heartbeat stopped updating. It now counts
the archive without holding the list and takes the newest snapshot from the file
names, which are UTC timestamps. Same checks, same output.

**What this changes in published results.** Nothing. The timetables used by
`segments.py`, `departure.py` and every finding were installed on time. Only the
metadata file and the health metric were missing.

## Files

- `code/refresh_gtfs.py`, `match_rate()`: the snapshot listing.
- `code/watchdog.py`: the refresher's systemd result in the warning, and the
  snapshot count without a full listing.
- On the box only: the drop-in, `backfill_state.py` (one-off), backups in
  `scratch/bak-20261004/`.
