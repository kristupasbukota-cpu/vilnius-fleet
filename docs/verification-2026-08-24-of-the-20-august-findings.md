# Verification of the 20 August findings, plus a system check

24 August 2026. Everything below was re-run independently against the same
handover tables, without looking at the analysis scripts that produced the note.

**Summary.** Section 1 replicates exactly and I can strengthen it: the one caveat
the note could not close is now closed, and it closes in the note's favour.
Section 2 splits in two. The measurement of trips *ending* early is sound. The
measurement of trips *departing* early is not, and it is the claim the note
singles out as the one that matters to a passenger. The 13.5% figure is not
buses leaving before their time. It is the previous trip arriving early, read
one snapshot later under a new trip id.

---

## 1. Compounding: confirmed, and the last caveat is now closed

### The replication

The cell fixed-effects estimator reproduces to the decimal:

| | rows | cells | slope | 95% CI |
|---|---|---|---|---|
| the note | 293,791 | 91,285 | -0.123 s/h | [-0.203, -0.047] |
| this run | 293,791 | 91,285 | **-0.123 s/h** | [-0.198, -0.048] |

Same join rate (99.4%), same usable sample, same answer. The small CI difference
is cluster-robust standard errors here against the note's bootstrap, which is the
expected gap between the two methods.

### The caveat the note flagged

The note is candid that inside a cell of (day, route, direction, stop pair,
hour), shift position is nearly determined by when the block started, so the
estimator compares different blocks against each other and inherits whatever
scheduling put a long early block on one road and a short late one on another.
The note calls this out and says the design cannot separate it from driver
behaviour.

It can, by adding vehicle-day fixed effects. The comparison then happens inside
one bus's own day, which is where compounding was always claimed to live, and
block selection cannot survive it because it is a level shift.

| estimator | slope | 95% CI |
|---|---|---|
| cell FE only | -0.123 s/h | [-0.198, -0.048] |
| **cell FE + vehicle-day FE** | **-0.629 s/h** | **[-0.841, -0.417]** |

Removing block selection does not reveal hidden compounding. It makes the lean
against compounding five times larger. Within one bus's own day, holding road,
hour, route and direction fixed, a crossing late in the shift gains about 0.63 s
less than one early in the shift, roughly 7.5 s per crossing across a 12-hour
shift against a mean of +4.9 s.

### Checks on that number

| variant | n | slope | 95% CI |
|---|---|---|---|
| all traversals | 293,791 | -0.629 | [-0.841, -0.417] |
| middle trips only, first and last dropped | 278,673 | -1.021 | [-1.280, -0.762] |
| shifts of 6 or more trips | 292,865 | -0.595 | [-0.795, -0.394] |
| 18 August alone | 143,970 | -0.656 | [-0.947, -0.365] |
| 19 August alone | 149,821 | -0.594 | [-0.899, -0.288] |
| winsorised at 1% and 99% | 293,791 | -0.313 | [-0.449, -0.177] |

Placebo: reassigning each vehicle-day's shift positions at random within that
same vehicle-day, leaving road, hour and vehicle structure untouched, gives
**+0.004 [-0.026, +0.033]**. The estimator returns zero when the signal is
removed, so it is not manufacturing a slope.

The binned profile falls monotonically across all ten deciles of residualised
shift position, so this is not one tail doing the work. Winsorising halves the
slope, which says the tails contribute, but the sign and significance survive
without them.

**Verdict: settled, and more firmly than the note claims.** Lateness does not
accumulate in vehicles. The mild negative is now large enough to be worth a
sentence, not just a footnote: buses deep in a shift recover slightly. The note's
two candidate explanations, drivers pushing and surviving blocks being the
well-scheduled ones, are still both alive, but vehicle-day fixed effects rule out
the second one *between* blocks. What is left is within-block: the same bus
behaving differently late in its own day.

---

## 2. Early running: the endings hold, the departures do not

### What the note reports

Trips more than 60 s ahead at last observation: 10 to 13% per day. Trips leaving
more than a minute early: 13.5%. The note calls the second one the number that
matters, because a bus that has already gone cannot be caught.

### Why the departure number does not measure departures

`dev_start_s` is the deviation at the **first sighting of a trip id**, not at
scheduled departure. Whether those are the same moment depends on when the feed
flips the trip id, and for the overwhelming majority of trips it flips at the
*arrival of the previous trip*, not at the departure of the next one.

Gap between one trip's last sighting and the next trip's first sighting, over
48,393 consecutive pairs: median **10 seconds**, which is one snapshot. 83% of
pairs are under a minute. Across that flip the deviation changes by a median of
11 s, which is what a stationary bus scored against an advancing timetable looks
like. The field runs continuously. It is not re-zeroed at the terminus.

So for most trips, the first reading under the new trip id is the previous trip's
ending deviation, one snapshot later.

The note tests this and clears it, but the test is restricted to early leavers,
and restricting a variable to one tail crushes its correlation with anything. On
all consecutive pairs:

| sample | r(dev at trip start, previous trip's dev at end) |
|---|---|
| every pair | **+0.748** |
| early leavers only | -0.241 |

The unrestricted correlation is the real one.

### The layover does the rest of the work

Splitting the same pairs by how long the bus actually sat at the terminus:

| layover | pairs | r | share starting >60 s early | share starting at exactly 0 |
|---|---|---|---|---|
| under 1 min | 40,411 (90%) | +0.864 | **13.5%** | 2.9% |
| 1 to 2 min | 112 | -0.041 | 7.1% | 50.9% |
| 2 to 3 min | 131 | -0.317 | 5.3% | 64.9% |
| 3 to 5 min | 221 | -0.007 | **2.7%** | 74.2% |
| 5 to 10 min | 702 | +0.053 | **2.3%** | 72.6% |
| 10 to 20 min | 944 | +0.266 | 2.9% | 53.8% |

Two things fall out. First, the note's headline 13.5% comes almost entirely from
the 90% of pairs with no real layover, where the reading is inherited. Second,
where a bus genuinely does sit at a terminus, the note's own semantics finding is
confirmed independently: about three quarters of those report exactly 0, and the
early share collapses to between 2 and 3%.

The cleanest case makes the same point. On the **first trip of a shift**, where
there is no previous trip to inherit from, the early share is **4.8%**, and 64%
report exactly 0. Later trips: 12.5% early, only 9.6% zero.

**Verdict on departures: not established.** Restated correctly, the 13.5% says
that 13.5% of trips *arrived at their terminus* more than a minute early on the
trip before, which the note itself, two paragraphs later, calls harmless. There
is no clean departure measurement anywhere in the handover tables, because both
endpoints of every trip are read at the trip-id flip and the flip lands at
arrival rather than departure.

### Why the endings still hold

`dev_end_s` is a genuine reading of that trip's deviation at its own terminus,
so section 2's day-by-day table stands, and so do the U-shape by hour and the
route ranking built on the same measure.

One extra piece of support. Splitting trip endings by whether anything follows:

| | n | ending >60 s early | ending >120 s early |
|---|---|---|---|
| followed by another trip | 48,393 | 10.9% | 3.1% |
| last trip of the shift | 2,983 | **18.5%** | **8.7%** |

Last runs of a shift end early nearly twice as often. Those are the late-evening
runs on empty roads, which is exactly the mechanism the note proposes: a
timetable padded for traffic that is not there. An artifact would not respect
that boundary, and this one goes the way the theory predicts.

### The fix, and it is cheap

The raw archive has every reading of every trip, not just its endpoints. Take, per
trip, the reading nearest the scheduled departure time from `stop_times` rather
than the first reading under that trip id, and the departure question becomes
answerable properly. That is one pass over one working day of snapshots on the
box, and it converts a broken headline into a real one.

---

## 3. System check

Both collectors are running and current.

**Oracle box.** Up 6 days. Heartbeat 2 seconds old at the time of checking,
71,576 snapshots, 432 vehicles in the last one, disk 10%, 496 MB of 946 MB
available, load 0.16. All four timers active. No fault events since 19 August,
and that one was the known nightly empty feed.

**Mac.** 57,463 snapshots, current to the second, no duplicates being written,
884 MB of archive. It has been running clean since 15 August alongside the box.
Given six days of the box carrying the load on its own without a single event,
the Mac has done its job and can be retired whenever you like.

### Two things worth knowing

**The timetable changed under us on 20 August.** Trips in the published feed went
from 19,600 to 22,624 that night, and the current `gtfs.zip` has a calendar
starting 23 August. The live feed no longer describes the days the analysis was
run on. All seven archived versions are retained on the box and nothing is being
pruned, so the study days are safe, but any re-analysis has to load the archived
version for the day in question rather than the current one. The note already
does this correctly.

**The GTFS match-rate alarm is measuring noise.** Last night it read 85.0%, which
sits exactly on the warn threshold. That 85.0% is 17 vehicles out of 20. The
measurement walks back from the newest snapshot and stops at the first one
carrying 20 vehicles, and since the check runs at 02:41 local it stops
immediately, at the smallest sample that clears the floor. One unresolved vehicle
moves the reading 5 percentage points. The threshold is fine, the sample is not.
Raising the floor to about 150 vehicles and widening the lookback to 12 hours
would put the measurement in real traffic and make a 5-point move mean something.
Not urgent, and nothing is wrong with the data.

---

## 4. Where this leaves the queue

The note's own next-step ordering is right, with one change of priority.

1. **Departure timing from the raw archive.** Promoted to first. It repairs the
   claim above and it is a single pass over one day.
2. **Roads against vehicles.** The two-way estimator above is this machinery
   already assembled. It is now a question of reporting variance shares rather
   than building anything.
3. **Tuesday's severity**, which still needs a fourth complete working day plus
   weather before three points can become a trend.
4. **Per-stop deviation**, which localises where earliness builds along a route
   and which the same raw-archive pass in step 1 would produce almost for free.
