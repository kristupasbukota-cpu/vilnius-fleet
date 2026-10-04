# Short stands at the terminus: buses that arrive early leave early

4 October 2026. The second test of the [hypotheses](hypotheses-2026-10-04.md): H6,
*every route with no scheduled stand at its terminus has more early departures*.

**Result: supported, with a narrower scope than stated.**

- **Where the timetable gives a bus 1 minute or less at the terminus, it leaves early
  about twice as often.** This holds on lines other than route 61 too: 2.5% at a zero
  stand and 4.3% at one minute, against 1.3% at ten minutes or more.
- **The effect is in buses that arrive early.** A bus that finishes its previous trip
  at least a minute early, then has 0 or 1 minute before its next departure, leaves
  early **13 to 17%** of the time. With ten minutes or more it does so 1.6% of the
  time. Given a minute to wait, most drivers do not.
- **Within the same line and direction, at the same hour,** a one-minute stand adds
  2.7 percentage points to the chance of leaving early and a two-minute stand 1.6,
  against ten minutes or more. Beyond two minutes the difference is gone.
- **The fix is cheap and the gain modest.** About 7% of departures follow a stand of
  1 minute or less. Raising them to 2 minutes would cost about 20 vehicle-hours a
  weekday across the city and remove roughly a tenth of all early departures,
  including most of route 61's.
- **A larger source turned up that H6 did not predict:** the first trip of a vehicle's
  day, out of the depot, departs early **6.3%** of the time, a quarter of all early
  departures. It is not tested yet, and it may be partly a measurement effect (section 5).

Ten working days, 21 September to 2 October 2026, 114,006 departures, all lines.

---

## 1. The measure

- **Scheduled stand:** the time between the scheduled end of the previous trip in the
  same timetable block and this trip's scheduled departure. A block is one vehicle's
  day of work in the city's timetable (`block_id`).
- **Early:** more than 60 s ahead of schedule at the scheduled departure time, measured
  at the boarding bay where a loop has two. The same measure as the network's 1.85%,
  and 1.91% here.
- **Route 61** prompted the hypothesis, so it is left out of every test below and
  shown separately where it matters.

## 2. Early departures by scheduled stand

All lines except route 61:

| scheduled stand | departures | early | rate |
|---|---|---|---|
| 0 min | 4,523 | 111 | **2.45%** |
| 1 min | 3,021 | 130 | **4.30%** |
| 2 min | 3,662 | 69 | 1.88% |
| 3–4 min | 7,564 | 104 | 1.37% |
| 5–9 min | 30,235 | 447 | 1.48% |
| 10+ min | 56,229 | 717 | 1.28% |
| first trip of the block | 8,069 | 505 | 6.26% |

With route 61 included, the one-minute rate is 5.9%.

Across line-directions with at least 200 departures, the early rate rises with the
share of short stands. Spearman correlation +0.27 over 198 line-directions:

| share of departures with a stand of 1 min or less | line-directions | departures | early |
|---|---|---|---|
| under 10% | 171 | 91,068 | 1.25% |
| 10 to 50% | 13 | 6,756 | 1.82% |
| over half | 14 | 5,523 | **2.87%** |

Short stands are not the only cause of early running. The line-directions with the
highest early rates, bus 50 direction 0 at 9.7%, bus 115 at 8.6% and trolleybus 16
at 8.5%, all have long stands. Their early departures are something else, possibly
the first-trip effect in section 5.

## 3. It happens when the bus arrives early

The same table split by how the same vehicle's previous trip ended:

| scheduled stand | previous trip ended 60 s or more early | previous trip ended on time, within 60 s |
|---|---|---|
| 0 min | **13.2%** of 521 | 1.2% of 2,369 |
| 1 min | **16.9%** of 409 | 3.8% of 1,389 |
| 2 min | 7.0% of 327 | 2.1% of 1,729 |
| 3–4 min | 2.5% of 1,113 | 1.3% of 3,580 |
| 5–9 min | 3.4% of 4,373 | 1.2% of 13,495 |
| 10+ min | 1.6% of 6,771 | 1.2% of 20,311 |

A bus that arrives early with a long stand waits for its time; the rate barely moves
from the on-time arrivals. A bus that arrives early with no time to wait
leaves early about one time in seven. It is the same mechanism found on route 61,
across the network.

## 4. Within the same line, at the same hour

Different lines differ in many ways, so the cleanest comparison is within one line and
direction, where stands vary through the day. A linear probability model with a level
for every line-direction and every hour, bootstrap over days:

| scheduled stand | extra chance of leaving early, against 10+ min, 95% CI |
|---|---|
| 0 min | +0.3 points [−1.4, +1.6] |
| **1 min** | **+2.7 points [+1.2, +3.7]** |
| **2 min** | **+1.6 points [+0.5, +2.5]** |
| 3–4 min | +0.3 points [−0.1, +0.7] |
| 5–9 min | +0.2 points [−0.1, +0.5] |

One and two-minute stands carry a clear effect. Zero-minute stands do not, within
their own lines. They cluster on a few lines, such as bus 6G direction 1 and bus 57
direction 1, and on those lines they are the norm, so there is little within-line
contrast to measure. The raw rate at a zero stand, 2.45%, is still about twice the
baseline.

## 5. Not part of H6: the first trip out of the depot

The first trip of each block leaves early 6.3% of the time, against 1.5% for all
other trips. That is 505 of the 2,083 early departures, a quarter, and more than
twice the 241 that follow short stands.

- It is concentrated in the morning pull-out: 7.6% of first trips scheduled at 05:00
  leave early, 11.2% at 07:00, and 1 to 2% in the middle of the day.
- It is widespread: 78 of 113 lines have at least one early first trip.
- The early ones are a median 84 s ahead, the same size as early departures elsewhere,
  and they are already ahead at the last reading before the scheduled time.

**Why this is not yet a finding.** The measure reads the bus's position against its
timetable. A bus that comes out of a depot onto the middle of its route, rather than
to the first stop, would read as ahead of schedule without having left early. Only
the vehicle positions, which are in the raw archive on the box, can tell the two
apart. That check comes before any claim.

## Verdict on H6

**Supported.** Early departures are more frequent after short stands across the
network, not only on route 61, and the mechanism is visible: buses that arrive early
with no time to wait leave early. The effect stops at about two minutes.

**What it means for the city.** A minimum scheduled stand of 2 to 3 minutes at every
terminus.

- About 7% of departures, some 750 a weekday, now follow a stand of a minute or less.
- Raising them to 2 minutes adds about 1,200 vehicle-minutes a weekday, around 20
  vehicle-hours. With 633 vehicles in service, that is a fraction of one percent.
- If those departures then behaved like today's two-minute stands, about 100 early
  departures in these ten days would not have happened, plus most of route 61's 93.
  That is roughly a tenth of all early departures.
- It costs no new buses where blocks already have slack later in the day. Where they
  do not, it costs a few minutes of running time.

**Not tested here:** whether a longer stand also makes the following trip more
punctual overall, and the first-trip effect in section 5.

## Limits

- An association across trips and lines, not a before-and-after test. Only a timetable
  change gives that.
- The previous trip's end is the deviation when last seen on that trip, used only when
  the same vehicle ran both trips. It is known for 98% of departures with a stand;
  section 3 leaves out the trips that arrived more than a minute late.
- "Arrived early" uses the scheduled end of the previous trip, which may sit at a
  different stop from this trip's start, an arrival bay against a departure bay. 44% of
  stands begin and end at the same stop. Section 6 of the script shows the split; it
  does not change the pattern.

## Method and files

- `code/terminal_stand.py`, from the repository root, reproduces every number here. It
  needs pandas and numpy, and reads `analysis/dep-*.csv.xz`,
  `analysis/blocks-*.json.gz` and the timetables in `gtfs/`.
- Per line-direction table: `analysis/terminal-stand-lines-2026-10-04.csv`.
- Stands come from the timetable version in force on each day: the latest dated no
  later than the day after. Lines are named with their mode, so bus 7 and trolleybus
  7 stay separate.
