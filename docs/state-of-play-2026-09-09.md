# State of play, 9 September 2026

Three and a half weeks in. This continues the 18 August document, which remains the
best account of how the thing was built and why. This one covers what changed after
19 August and what is true now.

---

## 1. Where it stands

| | |
|---|---|
| snapshots | 206,062 |
| readings | about 80 million |
| on disk | 3.0 GB compressed on the box |
| span | 15 August to 9 September, 26 days |
| complete days exported | 22, from 18 August to 8 September, no gaps |
| traversals published | 3.5 million |
| uptime | 3 weeks, 19 hours |
| faults since 25 August | none |

The collector has not missed a beat. The nightly chain has summarised, joined,
exported and pushed every night for fourteen consecutive nights with nobody watching.

---

## 2. The Mac is gone

Retired 27 August. It ran as a bare foreground process with no launchd job, so
stopping it was two PIDs, and nothing will restart it.

Before stopping it I checked what would be lost. Comparing filenames is misleading:
the two collectors sampled the same feed at different instants, so 39,740 of the Mac's
files had no identically named twin while covering the same seconds. By coverage, the
Mac held **19 minutes the box did not**, all on 18 August between 08:45 and 09:03, the
window before the box came up. Those were transferred and verified.

Its archive stays frozen on the Mac: 60,815 files, 929 MB, a complete offline copy
through 27 August and nothing after.

A footnote worth keeping. A bare `caffeinate -i` from 15 August was still holding a
wake assertion after the collector was gone, because it had no child process to exit
with and did not match a `collect.py` grep. 309 hours of it. Found by checking `pmset
-g assertions` rather than the process list. The lesson generalises: verify the effect,
not the process.

---

## 3. What the findings became

Two results were tested hard enough to change.

**Compounding is dead, and more firmly than first claimed.** The hypothesis was that
the evening collapse is a vehicle-level mechanism, a bus on its sixth trip carrying
what it lost on the previous five. The cell fixed-effects estimator says -0.123 s per
hour into shift. Adding vehicle-day fixed effects, which removes the block selection
that design cannot rule out, gives **-0.629 s/h [-0.841, -0.417]**. A placebo that
shuffles shift position within each vehicle-day returns +0.004. Buses deep in a shift
recover slightly. Nothing accumulates in them. Recovery time mid-shift would fix a
problem this network does not have.

**Early departure was a measurement artefact.** The claim was that 13.5% of trips leave
more than a minute early. That figure read the deviation at the first sighting of a
trip id, and the feed flips the trip id at the *arrival* of the previous trip, a median
of ten seconds after its last sighting, with the deviation running continuously across
the flip. So for nine trips in ten it was measuring an arrival.

Measured properly, by sampling the deviation at each trip's scheduled departure time
(median 3 seconds from it), across 37,870 trips: **2.5%**, not 13.5%. On the same trips
the old method gives 9.1%. A third method, the last reading before the scheduled time,
gives 2.4%. And 56.8% of trips read exactly zero at their scheduled departure, which is
the bus still parked, confirming the semantics independently.

Two routes then made the ranking look better than it was. Routes 56 and 73 showed 30.8%
and 25.8% early departure against a network median of 1.7%, with day-to-day agreement of
r = 0.92. But their early cases run **67 to 1 in one direction**, cluster at a fixed
offset near -80 seconds with a 30-second spread, and appear evenly across nineteen
hours. That is a first-stop defect, not behaviour. Excluding them takes the network
figure to about 2.1%.

> **Confirmed 20 September.** The defect is one stop, not two routes: stop 19255
> "Vilkpėdės žiedas", the standing bay of a two-bay terminal loop, 49 m and 60 s
> before the bay the operator times from. It also affects routes 13 and 29. The
> corrected network figure, measured rather than estimated, is 2.09%. See
> `vilkpedes-ziedas-defect-2026-09-20.md`.

The general lesson: **a systematic defect reproduces perfectly**, so high reproducibility
is not evidence that something is real.

What survives untouched: the evening collapse, its concentration on the Neris crossings,
and trips *ending* early at 10 to 13% a day, rising to 18.5% on the last run of a shift.

---

## 4. The city changed the network, and the archive caught it

On 21 August JUDU announced that from 1 September there would be **633 buses and
trolleybuses, 18% more than in summer**. Nobody told the collector.

| working day | distinct vehicles | peak on the road |
|---|---|---|
| Wed 19 Aug | 594 | 553 |
| Wed 26 Aug | 597 | 550 |
| Mon 31 Aug | 594 | 559 |
| **Tue 1 Sep** | **690** | **645** |
| **Wed 2 Sep** | **681** | **652** |

**+17.0% at peak**, against their stated 18%. The archive reproduced the city's own
number to within a percentage point, from the outside, with no prior knowledge.

This is the first external validation the project has had, and it changes what the
project is for. The city has now published specific, checkable promises: express routes
every 5 to 10 minutes and main routes every 10 to 25, 46.1 km of bus lanes with junction
priority, and more service for five named districts. This is the only independent
instrument in the city that can test them.

It also created something better than a promise to check. The same city put 17% more
vehicles on unchanged roads overnight. Every finding above comes from the summer
network and can now be re-asked against the autumn one.

One honest limit. A commenter accused JUDU of lying, claiming fewer vehicles than last
year. The summer-to-September increase is confirmed. The year-over-year claim cannot be
tested here and will not be, because the archive starts on 15 August 2026.

---

## 5. What protects the data now, and what does not

**Derived tables are safe.** `export.py` writes each complete local day once and never
rewrites it, so git only grows by addition. It is wired into the nightly chain ahead of
the publish step. `blocks.py` takes `--day`, so cost scales with new data rather than
archive size, which matters at 200,000 snapshots and would have mattered a great deal
at a million.

**The raw archive has one and a half copies.** The box holds everything. The Mac holds a
frozen copy through 27 August. A manual full boot volume backup was taken on 29 August,
which is a photograph of the disk as it was that day. There is still **no recurring
backup**, so everything recorded since is single-copy.

The recurring policy is the open item. It must be a custom weekly policy with 28-day
retention. Oracle's ready-made Bronze, Silver and Gold policies all accumulate past the
Always Free limit of five backups and then fail silently, Bronze at about month five.

**The Oracle account is safer than it looked.** The instance and its 100 GB boot volume
both carry the Always Free badge, confirmed in the console, and a tenancy-wide search
returns those two resources and nothing else. The trial expiry that looked like a
deadline does not apply to either. What remains is idle reclamation, which applies
*because* they are Always Free: measured 0.45% CPU and about 0.01% network against a
20% threshold over seven days. Pay As You Go removes the policy and keeps Always Free
resources free.

---

## 6. The storage question, and a failed attempt at it

Since 29 August the city has republished its timetable **every single day**. Twenty-one
versions are now archived, 78 MB, and the repository has grown from 67 MB on 3 September
to 148 MB today, with 250 MB of git history.

We keep every version on the argument that a dropped timetable can never be recovered.
That argument still holds. The arithmetic does not: at one version a day this alone adds
1.4 GB a year, and GitHub gets uncomfortable past about 1 GB.

Consecutive versions are nearly identical. On 6 September, 184 trips were removed and
none added out of 25,016. On 5 September, 367 added and 809 removed. The same rows over
and over, in a binary container that git cannot delta.

**So I published them as text instead, and it made things worse.** Measured in the cloud
container, eight versions went from 31.7 MB of zips to 8.8 MB of git history, a 72%
saving. Deployed to the box, it added 120 MB rather than saving anything.

The cause is in the box's own git configuration, set after the 18 August outage to stop
git from taking the machine down: `pack.window 1`, `pack.windowMemory 16m`,
`core.compression 1`, single-threaded. A window of one candidate is delta compression
switched off, and a 16 MB window cannot hold a 30 MB file as a delta base under any
circumstances. The saving I measured depended on delta compression the box is
deliberately forbidden from doing.

Reverted the same morning. The zips are back, the working tree is 148 MB again, and the
nightly chain is unchanged. **The 120 MB stays in the history**, because removing it
needs a force-push against what is currently the only off-box copy of the derived data.

The real lesson is not about git. It is that the benchmark was run in an environment
that did not share the constraint that mattered. The 946 MB box is the constraint on
everything here, and it was designed out of the test.

If this is worth solving later, the safe route is to repack in the cloud container,
where memory is not scarce, and force-push once deliberately. That is a decision, not a
maintenance task.

---

## 7. What is open

**Four claims to check**, all newly possible: the promised frequencies against
`IntervalasPaskui`, the bus lane network against the delay map, the five named
districts against a control, and every summer finding re-asked on the autumn fleet.

**Five analysis threads** carried over: the one-directional finding, a day-over-day
trend in the report, roads against vehicles, weather, and confirming the routes 56 and
73 defect against the GTFS shapes.

**Three housekeeping items**, all requiring a console login: the weekly backup policy,
the Pay As You Go decision, and a monthly login to keep the account from being deemed
abandoned.

---

## Recommendation

The weekly backup policy first, because it is the only open item where the downside is
losing data rather than losing time.

Then the autumn re-run. An unannounced 17% capacity change on unchanged roads is the
closest thing to an experiment this project will ever get for free, and the window for
a clean before-and-after closes as the network settles.
