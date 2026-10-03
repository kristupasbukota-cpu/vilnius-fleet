# Lateness belongs to roads, not to vehicles or routes

2 October 2026. Task #9.

**Result: where a bus is matters roughly fifteen times as much as which bus it is or
which route it runs.** The lasting difference between one stop-to-stop link at a
given hour and another has a spread of **22.4 s per hop**. The lasting difference
between one vehicle and another, on the same link at the same hour on the same day,
is **1.5 s per hop**. Between routes sharing the same link, **2.1 s**, and not because
their timetables differ.

This completes the picture from August, when lateness was shown not to accumulate
through a vehicle's shift. It does not belong to the vehicle in a lasting way either.

18 autumn working days, Monday to Thursday, 2 September to 1 October. 3.63 million
hops.

---

## 1. The test

The question is not how much each factor varies on a given day; a single day is
noisy. It is how much of the difference **repeats**. Split the days into two
alternating halves and ask whether a link, a vehicle or a route that was slow in one
half is slow in the other. The covariance between the halves is the part that
persists, and its square root is the spread of the lasting effect in seconds per hop.

| what is compared | units | agreement between alternate days | lasting spread, s per hop | 95% CI |
|---|---|---|---|---|
| **the road**: a stop-to-stop link at a given hour | 17,044 | r = 0.92 | **22.4** | [21.3, 23.7] |
| **the route and direction**, on links shared with other routes, same hour and day | 210 | r = 0.95 | **2.1** | [1.8, 2.3] |
| **the vehicle**, same link, hour and day | 725 | r = 0.78 | **1.7** | [1.5, 1.9] |
| **the vehicle**, with its routes' effects also removed | 725 | r = 0.75 | **1.5** | [1.3, 1.7] |

Vehicles need at least 500 hops in each half and routes the same, links 30.
Intervals are a bootstrap over units.

## 2. Reading it

**The road dominates.** Knowing the link and the hour predicts the other half of
the month closely, r = 0.92, and the lasting differences between links are wide:
22 s per hop is six times the network's mean delay.

**Vehicles differ, consistently but slightly.** A vehicle that loses more than its
neighbours on the same link in one half of the month does so in the other half too,
r = 0.75. The real spread is 1.5 s per hop. The most extreme vehicles sit about 5 to
7 s per hop either side of their neighbours, about 2.5 to 3.5 minutes over a 30-hop
trip.
This is not explained by the route: vehicles here run a median of 8 route-directions
each, and removing every route's own effect barely changes it. What it is cannot be
read from the feed. Driver habit, vehicle type and age would all look like this.
Trolleybuses and buses are level, +0.12 and -0.04 s against their neighbours.

**Routes differ a little on shared links, and not because of their timetables.** Two
routes crossing the same link in the same hour can have different scheduled times
for it, and lateness is measured against each one's own timetable, so that was the
obvious explanation. It is not: a hop's difference from its neighbours is unrelated
to its difference in scheduled time, r = -0.02, and adjusting for it leaves the
route spread at 2.1 s. What remains is something about how each route runs, such as
how full its buses are at that point and so how long they stand at stops. The feed
does not carry loads, so this cannot be split further.

**About 44% of the variation in a single hop is the link, the hour and the day
together.** The remaining 56% is individual traversals: a red light caught or
missed, a full stop or a quick one. Of that, the vehicle's lasting share is about
0.1% of the total variance.

## 3. What it means

Effort to improve punctuality pays at the level of roads and junctions. Vehicle-
or driver-level management can recover at most about 1.5 s per hop on average, and
the route 61 case (2 October) shows where it matters: not in how fast buses
travel, but in a handful of vehicles that leave early.

## Method

`analysis/trav-*.csv.gz`, autumn Monday to Thursday. A cell is one link
(`stop_from_id` to `stop_to_id`), one local hour, one day. The vehicle and route
tests use each hop's difference from its cell mean, in cells with at least two hops,
so the road, the hour and the day are held fixed. Days alternate between two halves
in date order. For each unit, the mean in each half; the covariance across units
between the halves is the variance of the lasting effect.
