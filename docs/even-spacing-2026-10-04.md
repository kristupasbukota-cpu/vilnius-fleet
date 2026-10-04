# Even spacing: the terminus is fine, the road is not

4 October 2026. The first test of the [hypotheses published this morning](hypotheses-2026-10-04.md):
H5, *even spacing would cut passenger waiting more than adding buses*.

**Result: partly supported, and smaller than this project said two days ago.**

- **Buses leave the terminus evenly spaced.** At the first stop the excess wait is
  0.1 minutes. Dispatching is not the problem.
- **The unevenness builds steadily along the route.** On the express routes the
  excess wait grows from +0.2 minutes near the start to +0.65 near the end. So the
  fix, where there is one, is holding buses at points along the route, not at the
  terminus.
- **The prize is real but modest.** Averaged along the route, perfectly even
  spacing would save an express passenger about **0.5 minutes**, 8% of the
  scheduled wait. That is worth about as much as running 8% more buses. On the
  trunk routes it is 0.3 minutes, 3%. In the morning peak it roughly doubles.
- **This corrects the [2 October excess-wait finding](excess-wait-2026-10-02.md).**
  Its +1.2 minutes (+24%) for express routes was not measured at departure, as it
  said, but at the moment each trip id first appears. That is a median 10.5 minutes
  before the scheduled departure, while the bus is still finishing its previous
  trip. On the same trips the real departure gives +0.1. The section *Corrections*
  below has the details.

Ten working days, 21 September to 2 October 2026, 07:00 to 19:00, 104 lines, main
route pattern of each line and direction only: 64,000 trips with a departure and an
end, 58,000 placed at all five points along the route.

---

## 1. Departures are regular

**The measure.** Excess waiting time, as on 2 October: the average wait of a
passenger arriving at random, from the gaps that actually ran, minus the same from
the timetable. It is computed over the same trips at the first stop and at the last,
so trips that were missing or not seen cannot affect the comparison.

- **Departure:** the bus's position against its timetable at the scheduled departure
  time, from `departure.py`, measured at the boarding bay where a loop has two.
- **End:** scheduled end plus the deviation when last seen on the trip.

| | lines | trips | scheduled wait | excess at the first stop | excess at the last stop | built up along the route, 95% CI |
|---|---|---|---|---|---|---|
| express | 7 | 10,904 | 5.6 min | **+0.10** [+0.09, +0.12] | **+0.65** [+0.54, +0.77] | +0.54 [+0.43, +0.66] |
| trunk, 25 busiest others | 25 | 24,476 | 9.1 min | +0.07 [+0.02, +0.14] | +0.47 [+0.44, +0.50] | +0.39 [+0.31, +0.48] |
| the rest | 72 | 28,626 | 19.5 min | +0.03 | +0.32 | +0.30 |

Intervals are a bootstrap over days.

About 85% of the irregularity at the end of the route is created on the road. Gaps of
under one minute, two buses effectively together, are 1.0% of gaps at the express
routes' first stop and 2.9% at the last.

**What little irregularity there is at departure is mostly inherited.**

- 1.5% of departures leave more than a minute early. Holding those back would remove
  about 0.01 minutes of the express excess.
- 8.4% leave more than a minute late. In 78% of those the same vehicle's previous
  trip had already ended more than a minute late. A bus that arrives late leaves
  late. That is a layover question, see H6 and H7, not a dispatching one.

## 2. Where along the route the gaps open

To see the build-up, every trip's passage time was reconstructed at five points:
the stops 5%, 25%, 50%, 75% and 95% of the way along its route. The feed says how
many seconds each bus is behind its timetable, so a reading places the bus at a
point in its timetable. The reading nearest each point, within 60 s, gives the time
it passed. 84% of trips were placed at all five points, and only those are used.

| | 5% | 25% | 50% | 75% | 95% | mean of the five | as a share of the scheduled wait |
|---|---|---|---|---|---|---|---|
| express | +0.22 | +0.39 | +0.51 | +0.60 | +0.65 | **+0.47** [+0.40, +0.56] | **8%** |
| trunk | +0.11 | +0.17 | +0.29 | +0.37 | +0.46 | **+0.28** [+0.22, +0.33] | **3%** |
| the rest | +0.08 | +0.07 | +0.10 | +0.17 | +0.22 | +0.13 [+0.11, +0.15] | 1% |

Minutes of excess waiting time. Scheduled waits: express 6.2, trunk 10.2, the rest
19.8.

The growth is steady, not a jump at one place. There is no single bottleneck where
buses bunch, so holding at one stop would not fix it.

**By time of day**, at the 50% point:

| | 07–09 | 09–16 | 16–19 |
|---|---|---|---|
| express | **+0.73 (15%)** | +0.38 (6%) | +0.63 (9%) |
| trunk | **+0.58 (7%)** | +0.24 (2%) | +0.39 (4%) |

The morning peak is where uneven spacing costs most. That fits the [autumn
morning finding](morning-settled-2026-09-30.md): the slower and more variable the
road, the faster buses drift together.

## 3. By line

Excess waiting time at the five points, express and trunk lines, worst at mid-route
first:

| line | trips | 5% | 50% | 95% | scheduled wait at 50% |
|---|---|---|---|---|---|
| bus 3G | 1,805 | +0.43 | **+0.85** | **+1.19** | 4.5 min |
| bus 2G | 1,436 | +0.54 | +0.76 | +0.86 | 6.1 |
| trolleybus 7 | 1,847 | +0.38 | +0.64 | +0.86 | 4.7 |
| bus 33 | 851 | +0.46 | +0.58 | +0.74 | 9.9 |
| bus 40 | 808 | +0.36 | +0.54 | **+1.14** | 10.6 |
| bus 1G | 1,896 | +0.18 | +0.54 | +0.57 | 4.3 |
| trolleybus 2 | 2,009 | +0.28 | +0.52 | +0.67 | 4.0 |
| bus 6G | 1,518 | +0.35 | +0.48 | +0.58 | 5.3 |
| bus 7 | 1,086 | +0.25 | +0.46 | +0.76 | 7.1 |
| bus 87 | 706 | +0.31 | +0.41 | +0.76 | 10.9 |
| ... | | | | | |
| bus 119 | 775 | +0.03 | +0.05 | +0.06 | 10.7 |

All lines: `analysis/excess-wait-points-2026-10-04.csv`.

On bus 3G and trolleybus 7, the busiest frequent lines, a passenger at mid-route
waits about 15 to 20% longer than the timetable implies. Those two, with 2G, 1G and
trolleybus 2, are where headway control would be noticed.

Two lines come out negative, bus 52 and bus 3G-A: their buses run more evenly than
their own timetable. I have not checked why; uneven gaps in the timetable itself
would do it. 3G-A is a small branch. Neither changes the totals.

## 4. Verdict on H5

**The mechanism is supported, the size is not.**

- Supported: passenger waiting is lost to uneven spacing, and it is created on the
  road, growing along every frequent line. It is a scheduling and operations problem
  the city could address without new buses: holding buses at a few points to restore
  the gap, with signal priority on the worst roads.
- Not supported as stated: "more than adding buses". Perfect spacing on the express
  lines is worth about as much as 8% more buses, and on the trunk lines about 3%. The
  city added about 17% more service on 1 September. Real headway control achieves
  part of the perfect figure, not all of it.
- Refuted: the version of H5 that blamed dispatching at the terminus. Departures are
  on time, and early departures cost almost nothing.

**What it means for the city.** Headway management is worth trying where it pays:
in the morning peak, on bus 3G, 2G, 1G and trolleybuses 7 and 2. There it would
recover 0.5 to 1 minute per passenger. Across the network it is a modest gain, not
the main lever. The main lever remains the road: the same morning hours and inbound
links where delay is concentrated ([one direction](one-direction-2026-10-02.md)).

## 5. Corrections

**[Excess wait, 2 October](excess-wait-2026-10-02.md).** Its starts were the moment
each trip id first appears in the feed, `t0` in the block tables. The [August
departure work](departure-repair-2026-08-29.md) had already shown that this moment
lands near the previous trip's arrival, not at the departure. Here it is a median
10.5 minutes before the scheduled departure, interquartile range 5.8 to 15.8. The
2 October note used it anyway and called its result a floor. It was not a floor.

| on the same trips | express | trunk | the rest |
|---|---|---|---|
| first sighting, the 2 October method | +1.23 | +0.83 | +0.25 |
| real departure | +0.10 | +0.07 | +0.03 |
| mean along the route, the passenger's figure | **+0.47** | **+0.28** | +0.13 |

The 2 October headline, express passengers wait 1.2 minutes (24%) longer than the
timetable implies, becomes **about 0.5 minutes (8%)**, and trunk 0.9 minutes (11%)
becomes **about 0.3 minutes (3%)**. Its ordering stands: express worst, the
infrequent tail least affected.

What the first sighting was measuring is how irregularly buses finish their previous
trip and start the next one. That is real, but it is not what a passenger waits for.
The new measure also leaves out trips that were never seen, so it measures
irregularity only. Whether missing trips add to the wait is not settled here.

**[Frequency promise, 18 September](frequency-promise-2026-09-18.md), section 3.** It
used the same first sighting and said the shift "largely cancels" between
consecutive buses. It does not: the time between finishing one trip and starting the
next varies too much. On these ten days, main patterns only, under half and over
double each line's own median gap:

| | bunched, first sighting | gapped, first sighting | bunched, mid-route | gapped, mid-route |
|---|---|---|---|---|
| express | 14.8% | 8.2% | **9.9%** | **5.9%** |
| trunk | 11.7% | 7.6% | **7.9%** | **6.4%** |

So on the trunk lines, about one gap in thirteen is under half the usual gap at
mid-route, and one in sixteen more than double. That compares with "one in five" and
"almost one in ten" on 18 September. Those earlier figures also mixed in short-turn
variants. Even the mid-route figures overstate true bunching, because gaps that
vary by timetable from hour to hour count against a single daily median. The verdict
of 18 September, that the frequency promise is kept, does not depend on this and
stands.

Both documents carry a banner pointing here.

## Limits

- Ten working days, 07:00 to 19:00, main pattern of each line and direction.
- Passage times come from the feed's deviation, placed within 60 s of each point.
  The trips not placed at all five points, 16%, are left out of both the actual and
  the scheduled waits.
- Trips never seen at all are not counted, so this is irregularity among trips that
  ran, not the cost of missing ones.
- Passengers are assumed to arrive at random. That holds on lines every 10 minutes or
  so, not on the tail, where people use the timetable.
- Crowding is not included.

## Method and files

- `code/spacing.py`, run on the box: passage times at five points for every trip.
  Output `analysis/spacing-YYYY-MM-DD.csv.xz`, ten days.
- `code/departure.py`: departures, `analysis/dep-YYYY-MM-DD.csv.xz`, the same ten days.
- `code/even_spacing_ends.py`: sections 1 and 5, first stop against last stop, and the
  first-sighting comparison.
- `code/even_spacing_points.py`: sections 2, 3 and 5, the five points, the line table
  and the bunching shares.
- Both scripts run from the repository root with pandas and numpy and reproduce every
  number here. Excess waiting time is pooled as the sum of squared gaps over twice
  the sum of gaps; gaps over 90 minutes are dropped. Groups as on 2 October: express
  are the G lines, trunk the 25 busiest other lines by trips seen. Buses and
  trolleybuses that share a number are separate lines.
