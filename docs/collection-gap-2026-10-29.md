# A 76-minute hole in the 29 October evening

30 October 2026. An operations note, not a finding. The only collection gap since
15 August: one evening, 76 minutes, lost for good.

## 1. What happened

On Thursday 29 October a security update was started on the server while the
collector was running. The update ran the machine (1 GB of memory) out of memory
while reading its package lists, and the whole server froze. It came back only after
a forced reboot from the Oracle console. Nothing was installed.

| | UTC | Vilnius |
|---|---|---|
| last snapshot before | 18:49:50 | 20:49:50 |
| first snapshot after | 20:06:06 | 22:06:06 |
| gap | 76 min 16 s | |

## 2. What it costs

From `analysis/trav-2026-10-29.csv.xz`, against Thursday 22 October:

| local hour | hops, 22 Oct | hops, 29 Oct | share |
|---|---|---|---|
| 19 | 9,912 | 10,199 | 103% |
| 20 | 9,834 | 8,143 | 83% |
| 21 | 10,291 | 0 | 0% |
| 22 | 10,130 | 8,730 | 86% |
| 23 | 6,547 | 6,223 | 95% |
| whole day | 203,698 | 190,722 | 94% |

About 13,000 hops (6% of the day) and 450 trips are missing. Hours 20 and 22 are
partial: trips that straddle the gap lose their hops inside it.

## 3. What it touches

- **Nothing pre-registered.** The H8 school test uses 07:00 to 09:59 on weekdays; the
  gap is in the evening.
- **Evening and daily totals for 29 October** read about 6% low. Analyses of the
  evening (H4, the evening core slowdown) should drop 29 October 20:00 to 22:59 local,
  or the whole evening.
- Per-hop delays from the hours that survived are unaffected; they are averages over
  the hops that were seen.

## 4. What changed

- Server work now happens only with the collector protected first, at about 04:00
  Vilnius time when the feed is empty, with a memory cap on the job.
- A retry on 30 October 02:02 UTC paused the collector for 2 min 24 s with no buses in
  the feed and lost nothing. The update was stopped by its memory cap without
  freezing anything. It still does not fit; another way is being chosen.
- The cause of the uncapped run: a wrapper that limits `dnf` to 200 MB sits in
  `/usr/local/bin`, which `sudo` does not search.
