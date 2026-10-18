# Spare time in the timetables: there is very little of it

6 October 2026. The third test of the [hypotheses](hypotheses-2026-10-04.md): H7,
*the timetables have spare time in the wrong places*.

**Result: refuted as stated, supported in a narrower form.**

- **The timetables are short, not padded.** Over a working day, buses and trolleybuses
  need about **209 vehicle-hours more** running time between first and last stop than
  the timetable gives them. Trips that consistently run faster than scheduled add up to
  about **10 vehicle-hours**. There is roughly one minute of spare time for every
  twenty that are missing.
- **Off-peak and outbound trips are not the reserve H7 expected.** Daytime trips run
  late in both directions. In the 07:00 to 08:59 hour, a typical inbound trip ends its
  running about **+1:41** over schedule, and an outbound one **+0:53**. Across the
  round trip, 83% of lines are more than a minute short and 7% more than a minute
  long. Only 4 of 104 lines have one direction clearly early and the other clearly
  late, which is the case where time could be moved with no extra buses.
- **Spare time exists only at the edges of the day.** Before 06:00 and after 19:00,
  trips run close to schedule (median −8 s and +1 s per trip). Of the 71 line, direction
  and hour cells that run more than a minute early, 51 start before 07:00 or after 19:00.
- **What does hold is the bus 32 pattern: time in the wrong place along the route.**
  On 70 of 1,223 cells, across 30 lines, the timetable gives one link far too much time
  and another far too little, by at least a minute over the trip once errors under 30 s
  per link are ignored. Moving that time between links would not change trip length,
  only make the times at the stops in between right. It is about **44 vehicle-hours** of
  misplaced time a weekday. Bus 32, 1G, 3G, 63 and 2G and trolleybus 10 carry the most.
- **The worst-link rankings mostly survive.** Of the 20 links that lose the most time
  a day, 4 sit next to a padded link on most of the lines using them, so part of their
  ranking is a timetable artefact: Europos aikštė to Žaliasis tiltas, Naujininkai to
  Vienaragių st., Vaivadiškės to Papiškės and Žvejų st. to Karaliaus Mindaugo tiltas.
  The two worst, Čiurlionio st. to Tumo-Vaižganto st. and Rūdninkų st. to MO muziejus,
  have no padded neighbour. Their delay is real.

24 working days, 2 September to 5 October 2026, 4.84 million stop-to-stop hops,
all lines.

---

## 1. The measure

- **Running-time error** of a link: actual time between two consecutive stops minus the
  time the timetable gives it (`lost_s` in `analysis/trav-*`). Positive is slower than
  scheduled.
- **Cell:** one line, one direction, one band of trip start time (before 06, 06, 07-08,
  09-14, 15-18, 19 and later). Bus and trolleybus lines with the same number are kept
  apart.
- **Trip error of a cell:** the sum, over the links on that cell's main pattern, of each
  link's mean error. Links seen fewer than 20 times, or on less than half as many trips
  as the busiest link in the cell, are left out. Cells with under 5 links are dropped.
  This uses every hop, not only trips seen from end to end, of which only 44% are.
  Measured on near-complete trips instead, the pattern by hour is the same.
- **Excluded:** the time a vehicle waits at the terminus, and lateness carried in from
  the previous trip. H7 is about running time, not departure punctuality.
- **Stable:** cell errors computed on odd and even days correlate at 0.95, link errors
  at 0.95.

## 2. By time of day

Median trip error per cell, and the share of cells more than a minute early or late:

| trip starts | cells | median | > 1 min early | > 1 min late |
|---|---|---|---|---|
| before 06 | 188 | −8 s | 13% | 7% |
| 06 | 206 | +44 s | 6% | 43% |
| 07-08 | 209 | +91 s | 6% | 61% |
| 09-14 | 208 | +30 s | 2% | 37% |
| 15-18 | 207 | +76 s | 2% | 63% |
| 19 and later | 205 | +1 s | 7% | 5% |

In vehicle-hours a working day (trip error times trips observed a day):

| trip starts | trips a day | short | long |
|---|---|---|---|
| before 06 | 782 | 3.5 | 4.9 |
| 06 | 813 | 17.3 | 1.6 |
| 07-08 | 1,316 | 48.1 | 1.8 |
| 09-14 | 3,308 | 50.7 | 5.6 |
| 15-18 | 2,543 | 76.7 | 2.6 |
| 19 and later | 2,645 | 12.8 | 9.7 |
| **all** | 11,405 | **209** | **26** |

"Long" here includes every cell below zero, however slightly. Cells more than a minute
early add up to 10.5 vehicle-hours.

The trip-level view, on the 117,860 trips seen over at least 90% of their stops, gives
the same shape: in 07-08, a median of +101 s inbound and +53 s outbound; after 19:00,
−4 s and −6 s.

## 3. Time in the wrong place along the route

For each cell, the misplaced time is the smaller of two sums: the links running more
than 30 s over schedule, and the links running more than 30 s under. That is the time
that could move from padded links to tight ones within the same trip. The 30 s floor
leaves out the error the timetable cannot avoid, since it is published to the minute.

- 70 cells reach at least a minute, on 30 lines.
- Together, about 44 vehicle-hours a weekday.
- Per line, the largest: bus 32 (2.7 vehicle-hours), 1G (2.7), 3G (2.4), 63 (2.3),
  2G (2.3), trolleybus 10 (1.9), bus 4G (1.8), trolleybus 17 (1.4).

Without the 30 s floor the figure is 232 vehicle-hours, most of it minute-rounding.

**Bus 63 is a case of its own.** It runs 2 to 5 minutes over schedule per trip at
every hour from 06:00, in both directions, and Vaivadiškės to Papiškės takes 7 minutes
more than scheduled while the link next to it runs 3 minutes early. That looks like a
diversion or stop change the timetable does not show. Not checked.

## 4. What it means for the city

- Moving spare time from off-peak to peak trips would recover very little: the spare
  time is not there.
- The cheap fix that remains is redistributing time along the route on about 30 lines,
  so that passengers at intermediate stops see the bus when the timetable says. It
  costs no extra vehicles.
- The larger finding is that peak trips run about 2 minutes longer than the
  timetable allows, on average. Buses recover it at the terminus, which is why
  stands matter so much ([terminal stand](terminal-stand-2026-10-04.md)). A timetable
  that showed the true running time would need either longer cycle times, meaning more
  vehicles at the same frequency, or less frequent service on paper.

## 5. Limits

- It compares hours and lines, not the same trip before and after a change.
- Trips observed, not trips scheduled: cells where the feed misses many trips are
  undercounted in vehicle-hours.
- Each link's error includes the dwell at one of its stops, so a crowded stop shows as
  a slow link.

## Method and files

`code/spare_time.py`, run from the repository root, reproduces every number here. It
reads `analysis/trav-*.csv.*` and `gtfs/gtfs-20261001.zip` and needs pandas.
