# Two results: compounding is dead, and early running is real

20 August 2026. Both analyses run on the handover package (five days of joined
feed data, 15 to 20 August), with the three archived GTFS versions pulled from
the project repository for scheduled trip start and end times. Everything below
was checked a second way per section 7 of the handover.

> **Later corrections.** Section 1 was independently replicated on 24 August and
> then strengthened: adding vehicle-day fixed effects gives -0.629 s/h
> [-0.841, -0.417]. Section 2's departure claim did not survive. The 13.5% was
> reading the previous trip's arrival; measured at the scheduled departure it is
> 2.5%, and 2.09% once the Vilkpėdės žiedas stop defect is excluded. See
> `verification-2026-08-24-of-the-20-august-findings.md`,
> `departure-repair-2026-08-29.md` and `vilkpedes-ziedas-defect-2026-09-20.md`.
> The *ending* early results in section 2 stand.

---

## 1. Lateness does not compound through a shift. Settled.

The project's oldest hypothesis was that the evening collapse is a vehicle-level
mechanism: a bus on its sixth trip carries what it lost on the previous five.
The crude tercile pass in the handover said no. The proper version now says no
with confidence intervals, at both levels the question can be asked.

### Design

Within-cell (fixed-effects) estimator on the traversals-to-blocks join
(99.4% of 339,361 traversals resolve, both complete working days). A cell is
(day, route, direction, stop_from, stop_to, hour_local): within a cell, the
road, the hour, the route and the direction are all identical, and the only
thing left varying is where each crossing vehicle sat in its own shift. Demean
seconds lost and shift position inside every cell, pool, regress. Inference by
cluster bootstrap over vehicle-days (1,141 of them) and by permutation of shift
position within cells. 293,791 traversals in 91,285 usable cells.

### Result: null, with a tiny lean the wrong way

| shift-position measure | slope | 95% CI | permutation p |
|---|---|---|---|
| hours into shift | **-0.123 s per hour** | [-0.203, -0.047] | < 0.005 |
| trip index | -0.099 s per trip | [-0.167, -0.020] | 0.010 |
| fraction through shift | -1.50 s first-to-last | [-4.02, +0.98] | 0.26 |

A vehicle deep in its shift loses very slightly *less* per crossing than a
fresh one on the same road at the same hour. The effect is real enough to be
statistically distinguishable from zero and small enough to be operationally
meaningless: over a whole 12-hour shift it amounts to about -1.5 s per
crossing, against a mean of +4.5 s and a standard deviation of 53 s. The upper
confidence bounds exclude any positive compounding larger than ~0.02 s per
trip. The binned profile is flat with no rise anywhere; the tercile split
replicated on this join gives the same picture as the handover's crude pass
(later worse in 48.4% of 25,702 groups, a coin flip).

The same holds for the *level* of lateness, not just the per-crossing rate.
Within (day, route, direction, departure-hour) cells over 18,939 working-day
trips: deviation at trip start moves -1.8 s per hour on shift, at trip end
-3.4 s per hour. Later in the shift is very slightly better off, not worse.

Both days agree independently (18 Aug: -0.101 s/h; 19 Aug: -0.143 s/h).
Vehicles that *started* a trip more than 3 minutes down show a slightly more
negative slope (-0.194 s/h) than those that started clean, which reads as mild
catch-up behaviour, not accumulation.

**Conclusion.** The evening collapse is a property of specific roads at
specific hours, full stop. Nothing accumulates in the vehicles. Recovery time
mid-shift would fix a problem this network does not have. (Why slightly
negative? Could be drivers pushing when deep in a shift, or selection: blocks
that survive to a tenth trip are the well-scheduled ones. The design cannot
tell these apart and the size does not warrant chasing it.)

---

## 2. Early running: about one trip in eight ends ahead of schedule

Never counted before. Counted now, on all six days, 49,551 vehicle-trips
passing quality filters (≥5 observations, observed span ≥ half the scheduled
duration; scheduled times joined from the correct GTFS version per the
oldest-first loading convention).

**Semantics check first**, because the whole measure hangs on it: a vehicle
assigned to a trip that has not started yet reports a deviation of exactly 0,
not a countdown (30 of 30 pre-departure vehicles in the sample snapshot). So a
negative deviation observed on-trip is genuine early running, and 0 at first
sighting is ambiguous rather than "on time" (only 7% of departure-window
observations, so the bias is small and toward *under*counting earliness).

### The numbers

Share of trips more than 60 s ahead of schedule at their last observation:

| day | early >60 s | early >120 s | late >60 s |
|---|---|---|---|
| Sat 15 (holiday) | 10.0% | 2.7% | 42.3% |
| Sun 16 | 10.9% | 2.8% | 36.1% |
| Mon 17 | 13.3% | 4.2% | 40.7% |
| Tue 18 | 11.2% | 3.3% | 50.5% |
| Wed 19 | 12.1% | 3.7% | 48.9% |
| Thu 20 (partial) | 10.8% | 3.2% | 48.8% |

That is roughly **1,000 to 1,250 trips per working day ending more than a
minute early**, on the observed sample alone.

**Departures are worse than endings.** Among working-day trips caught at their
start (first seen within -10 to +3 min of scheduled departure, 22,147 trips):
**13.5% left more than a minute early**, 4.2% more than two minutes. Weekend:
10.6% and 2.5%. This is the number that matters to a passenger, because a bus
that has already gone cannot be caught, and unlike a late bus it never becomes
catchable again. *(Withdrawn. See the correction at the top.)*

### Early running is not congestion's mirror image, it is congestion's absence

The lateness numbers swing violently between weekend and working day. The
early-running share barely moves. And within the working day it is
**U-shaped**: lowest exactly when the network is most congested (5-8% at
16:00-18:00), highest in the late evening (17-20% at 22:00-24:00) and elevated
in the early morning (11-15% at 05:00-08:00). Reproduced in every one of the
six days separately. Empty roads plus a timetable padded for traffic that is
not there equals buses running ahead. The same padding that fails to protect
the 17:00 peak actively produces early running at 22:00.

### Where it concentrates

Routes 31, 26, 78, 50, 76, 57, 55 run 25-32% of working-day trips early at
last observation, against a network median around 11%. The route-level ranking
is indicative rather than settled: day-to-day correlation of route early-share
is r = 0.54 (n = 86 routes) and five of the top ten reproduce across both
complete working days: 26, 31, 50, 55, 57. Frequency explains little of it
(r = -0.14 against log trips/day), so this is not simply an infrequent-route
disease, though it hurts most there, where the next bus is 20+ minutes away.

### Checks run against this result

The pre-departure-zero semantics were verified on the snapshot. The carryover
artifact (deviation values inherited from the previous trip at the moment the
feed switches trip ids) was tested and cleared: among early leavers the
correlation of departure deviation with the previous trip's ending deviation is
-0.06, and trips first seen after a clean layover of 3+ minutes still leave
early at 11.3% against 13.5% overall. Early departure is also predictive, not
noise: trips leaving >60 s early are still early at last observation 27.9% of
the time, against 12.2% for on-time leavers. And the overall share is steady
across all six days including the holiday, which is what a schedule-behaviour
property should look like and a congestion artifact should not.

*(The carryover test above is the one that failed on 24 August. Restricting to
early leavers crushes the correlation; on all consecutive pairs it is +0.748.)*

### Caveats that survive

The last observation of a trip is usually near its end, and arriving early at
a terminus is harmless; the harm happened at the intermediate stops passed
early, which endpoint data cannot localise. Localising *where* along the route
earliness builds needs per-stop deviation, which the raw archive has and the
handover tables do not. The departure measure undercounts slightly (the 7%
ambiguous zeros). Thu 20 August is a partial day throughout.

---

## 3. What this sets up next

The two results point the same direction: both the evening lateness and the
off-peak earliness are properties of the *timetable against the road*, not of
vehicles or drivers. The remaining open questions from the handover, in the
order I would now take them: roads vs vehicles residual (question 4), which
this compounding machinery already half-builds, the within-cell design needs
only vehicle demeaning added; Tuesday's severity (question 3), which needs
Thursday's complete day plus weather (question 5) to be more than a
three-point series. For early running specifically, the one-join upgrade is
per-stop deviation from the raw archive on one working day, which would turn
"13.5% leave early" into "these stops, on these routes, at these hours, are
where passengers get stranded".

## Files

Analysis scripts alongside this note: `compounding.py` (within-cell estimator,
bootstrap, permutation), `early.py` (GTFS join, filters, all shares). Both run
against the handover `data/` directory unchanged.
