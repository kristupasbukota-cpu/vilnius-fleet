# Keeping the repository under 1 GB

> **Decided and done, 3 October 2026.** Option B was chosen and is in place from the
> night of 3 to 4 October: new timetable versions go into `gtfs/` as verified
> patches, about 30 KB instead of 3.5 MB, with the first version of each month whole,
> and new hop and block tables are written as xz. Nothing already published changed.
> Option C, the history rewrite, was not chosen and stays open as task #13. See
> *3 October: option B in place* at the end. The proposal below is unchanged.

2 October 2026. Task #26. A proposal: nothing here has been changed yet.

**Result: at the current rate the repository passes 1 GB around 22 January 2027.
Two changes that keep every byte of information would push that to about mid-June
2027, and a one-off history clean-up, which needs your go-ahead, to about the end
of July.** Each step is independent.

---

## 1. Where the space goes

Measured on a full clone of the whole history today: **385.3 MiB**, 90 commits.

| folder | on disk | share |
|---|---|---|
| `gtfs/` timetable versions as zip files | 124.7 MiB | 32% |
| `gtfs/` timetables as text, the September experiment | **111.8 MiB** | 29% |
| `analysis/trav-*`, one row per hop | 101.2 MiB | 26% |
| `analysis/blocks-*` | 13.7 MiB | 4% |
| `segments/` | 11.8 MiB | 3% |
| `summaries/`, `report/`, everything else | 22.1 MiB | 6% |

New additions run at about **5.7 MiB a day**: a timetable version about 2.5, the
day's hop table 2.3, everything else about 0.9. The city publishes a new timetable
version almost daily, 41 in 49 days, and every one of them is different.

## 2. What changes from day to day

Comparing consecutive timetable versions, `stop_times.txt` row by row: the last
eight transitions each changed between 0 and 50,000 of about 430,000 rows, usually a
few thousand. Stored as the rows added and removed since the previous version,
compressed, a version costs **0.01 to 0.18 MiB instead of about 3.4 MiB, about 2% of
the size.**

The hop tables compress about **36% smaller with xz** than with gzip, 1.71 MiB
against 2.66 MiB for 29 September, at a memory cost the box can afford (xz level 6,
about 94 MB).

## 3. The options

| | what changes | growth per day | 1 GB reached | needs you? |
|---|---|---|---|---|
| **0. nothing** | | 5.7 MiB | **about 22 January 2027** | no |
| **A. timetables as patches** | each new version stored as rows added and removed since the previous one, with a full copy on the first of each month; a script rebuilds any version byte for byte | about 3.3 MiB | about mid-April 2027 | no |
| **B. A, plus xz for new hop and block tables** | new days as `.csv.xz`; old days stay as they are | about 2.5 MiB | **about mid-June 2027** | no |
| **C. B, plus removing the text timetables from history** (task #13) | rewrite history to drop the 111.8 MiB experiment; needs a force-push | about 2.5 MiB, from 273 MiB | about end of July 2027 | **yes** |
| D. a new repository each year | `vilnius-fleet-2027` from 1 January, this one frozen | resets | never, per repository | yes |

Nothing is lost under A, B or C: every timetable version and every table can be
rebuilt exactly. C removes only the text copies of timetables that are also stored
as zips.

## 4. What I would do

**A and B now.** They change only what is written from tomorrow on, keep every byte
reconstructable, and buy about five months. Before switching, each patch would be
verified by rebuilding the version and comparing it with the original, every night,
and a mismatch would store the full version instead.

**C when you are ready.** It is the only option that shrinks what already exists, and
it rewrites the repository's history: anyone with a clone would need to re-clone.
That is a decision for you, not for a nightly script.

**D as the long-term answer** if the project runs for years. A repository per year is
easy to explain and never needs history rewritten.

## Decisions needed

1. Go ahead with A and B? (I can do both without anything from you.)
2. Rewrite history to remove the text timetables (C, task #13)? Needs your explicit
   go-ahead for the force-push.
3. A new repository each year from 2027 (D)?

## Method

`git clone --bare` of the whole repository, `git count-objects -vH`, and the on-disk
size of every blob by path from `git cat-file --batch-check`. Timetable changes from
the archived zips themselves; xz measured on `trav-2026-09-29`.

## 3 October: option B in place

**What changed on the box.**

- `publish.sh` no longer copies every `gtfs*.zip` into the repository. It runs
  `gtfs_pub.py`. That stores a new version whole when it is the first of its calendar
  month, or when its exact bytes are already in the repository. Otherwise it stores
  `gtfs-YYYYMMDD.patch.xz`, the lines changed since the previous version. A patch is
  only written after the box has rebuilt the version from it and compared every file
  inside by sha256. Any difference and the version is stored whole.
- The current feed is published under the name it will be archived under. The old
  `gtfs/gtfs.zip`, a second copy of the newest version, leaves the working tree; git
  keeps it.
- `export.py` writes `trav-*.csv.xz` and `blocks-*.json.xz` for days from 3 October.
  Earlier days stay `.gz`.
- `weather_effect.py` and `weather_audit.py` read both.

**Tested before installing.** On the city's own versions: 30 September as a patch
against 29 September came to 33 KB instead of 3.4 MB, and 2 October against
1 October 28 KB instead of 3.7 MB. Both were rebuilt with `gtfs_rebuild.py`, every
file identical by sha256, fingerprints matching. Peak memory 181 MB. The hop table
for 2 October as xz is 1.8 MB against 2.8 MB, and it reads back identical.

**One thing the proposal overstated.** It said a script would rebuild any version
"byte for byte". The files inside are rebuilt byte for byte, and so is the
project's fingerprint of the version. The zip wrapper is not: the city compresses
with a deflate encoder that zlib does not reproduce, so a rebuilt zip is repacked.
Nothing here depends on the zip's own hash.

**For anyone reading the repository.** `python3 code/gtfs_rebuild.py` turns `gtfs/`
back into one zip per version in `gtfs-full/`. Read hop tables with
`analysis/trav-*.csv.*`. Both folders now have a README.

**Expected effect.** Growth falls from about 5.7 to about 2.5 MiB a day, and 1 GB moves
from about 22 January to about mid-June 2027. A check on 27 October will measure the
real rate after three weeks.
