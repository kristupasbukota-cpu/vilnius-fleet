# The early-departure claim, measured properly

29 August 2026. Task #33. Four days, 37,870 trips.

> **Update, 20 September 2026.** Section 5 below calls the routes 56 and 73 result
> "almost certainly a timetable defect" and estimates the corrected network figure
> at about 2.1%. That has now been confirmed against the archived GTFS, and the
> cause is narrower than described here: it is not a route defect but a single
> stop, 19255 "Vilkpėdės žiedas", which also affects routes 13 and 29. The
> measured corrected figure is **2.09%**. See
> `claude/vilkpedes-ziedas-defect-2026-09-20.md`. Route 61 remains unexplained.

**Result: 2.5% of trips leave more than a minute early, not 13.5%.** The old
figure was measuring the previous trip's arrival. And the two worst routes in the
new ranking are almost certainly a timetable defect rather than behaviour, which
takes the network figure closer to 2.1%.

---

## 1. What was wrong and what replaces it

The old measure read `dev_start`, the deviation at the first sighting of a trip
id. The feed flips the trip id when the bus reaches the terminus on its *previous*
trip, a median of ten seconds after that trip's last sighting, and the deviation
runs continuously across the flip instead of resetting. For roughly nine trips in
ten there is no real layover, so the first reading under a new trip id is the
previous trip's ending deviation. It describes an arrival.

The new measure lets the clock decide when to look rather than the feed. GTFS
gives each trip a scheduled departure T from its first stop. Sample the live
deviation at T:

- a bus still waiting at the terminus reads about 0, it has not gone
- a bus that pulled out 90 seconds ago sits where the timetable puts it at T+90,
  so it reads -90

No geometry, no first sighting, no dependence on when the id flipped.

The sampling is tight: the reading used sits a **median of 3 seconds** from the
scheduled departure, 6 seconds at the 90th percentile.

## 2. The two measures, on the very same trips

| day | trips | early >60 s **at departure** | early >60 s at first sighting | >120 s at departure | >120 s at first sighting |
|---|---|---|---|---|---|
| Sat 22 | 7,703 | **2.2%** | 9.9% | 0.5% | 2.8% |
| Mon 24 | 10,088 | **2.9%** | 9.1% | 0.4% | 2.6% |
| Tue 25 | 10,117 | **2.3%** | 9.2% | 0.3% | 2.7% |
| Wed 26 | 9,962 | **2.3%** | 8.9% | 0.4% | 2.5% |
| **working days pooled** | 30,167 | **2.5%** | 9.1% | | |

The first-sighting measure inflates early departure by a factor of about 3.6 on
identical trips. Asked a third way, taking the last reading strictly before the
scheduled time, the answer is **2.4%**, which agrees with the departure measure and
not with the old one.

## 3. The distribution says the feed is behaving exactly as described

Deviation at scheduled departure, working days:

| | |
|---|---|
| exactly zero | **56.8%** |
| median | 0 s |
| p5 | -32 s |
| p95 | +71 s |
| mean | +11.9 s |
| late by more than 60 s | 6.2% |

The 56.8% sitting at exactly zero is the parked bus that has not left yet,
independently confirming the semantics the earlier note found in a 30-vehicle
sample. The mass is at zero and the tail is on the late side.

## 4. The hourly shape survives, much flattened

| hour | early >60 s | late >60 s |
|---|---|---|
| 05 | 4.0% | 7.6% |
| 08 | 1.9% | 4.0% |
| 12 | 1.8% | 7.1% |
| **17** | 2.6% | **12.3%** |
| 21 | 1.3% | 4.1% |
| 23 | 4.7% | 3.2% |
| 00 | 7.6% | 5.1% |

Still U-shaped, still lowest in the middle of the day and highest in the small
hours, but between 1.3% and 7.6% rather than 5% and 20%. Late departure, by
contrast, peaks hard at 17:00, which is the same evening collapse everything else
in this project points at.

Saturday sits at 2.2% against 2.5% on working days, so early departure remains
close to indifferent to congestion. That part of the original reading holds.

## 5. Where it concentrates, and why two of those routes are probably not real

Working days, routes with at least 150 trips:

| route | trips | early >60 s |
|---|---|---|
| 56 | 221 | **30.8%** |
| 73 | 264 | **25.8%** |
| 61 | 271 | 11.8% |
| 16 | 735 | 7.9% |
| 39 | 255 | 7.8% |
| 17 | 716 | 5.6% |
| network median, 76 routes | | **1.7%** |

Day-to-day agreement across 25 and 26 August is **r = 0.92**, against r = 0.54 for
the old measure. That is a much better number, and it is also a warning: a
systematic defect reproduces perfectly, so high reproducibility is not by itself
evidence that something is real.

**Routes 56 and 73 do not look like behaviour.** Their early departures are:

- one-directional to an almost impossible degree, **67 in direction 1 against 1 in
  direction 0** on each route
- tightly clustered, route 73 at a median of -83 s with the 10th to 90th
  percentile spanning only -95 to -66 s
- spread evenly across every hour from 05:00 to 23:00

A fixed offset of 75 to 85 seconds, in one direction only, all day long, is the
signature of a first stop or a published departure time that does not match where
the trip actually begins. Drivers do not leave exactly 80 seconds early nineteen
hours a day in one direction only. Routes 61 and 16 look different: their early
cases spread over 257 and 316 seconds and split much more evenly between
directions, so those are plausibly genuine.

Removing 56 and 73 takes the network figure from 2.5% to about **2.1%**.

*Confirmed on 20 September. The cause is stop 19255, not the routes, and the
corrected figure measured rather than estimated is 2.09%.*

## 6. What this means

The passenger-facing claim in the 20 August note does not survive. "A bus that has
already gone cannot be caught" was the right thing to care about, but roughly one
trip in forty leaves more than a minute early, not one in seven, and half a
percentage point of that is a timetable defect on two routes.

What does survive is everything measured at the trip's own end: 10 to 13% of trips
finish more than a minute ahead, last runs of a shift do so 18.5% of the time, and
the padding argument behind it. Vilnius buses arrive early far more often than they
leave early, which is a different and much less harmful fact.

The remaining work on this thread is to check the first stop of routes 56 and 73
against the GTFS shape, which would confirm the defect and let it be excluded
cleanly rather than by judgement. *Done, 20 September.*

## Files

`departure.py` on the box. *Correction, 20 September: it is not in the repository.
`publish.sh` does not copy it, so it is single-copy.* Per-trip outputs for
22, 24, 25 and 26 August in `analysis/dep-*.csv.gz`, one row per vehicle-trip with
the deviation at scheduled departure, at first sighting, and at the last reading
before the scheduled time, so all three measures can be recomputed from the table.
