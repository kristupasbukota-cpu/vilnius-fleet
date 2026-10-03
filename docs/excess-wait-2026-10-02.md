# How much longer passengers wait than the timetable promises

2 October 2026. Task #15, a passenger-experienced waiting time.

**Result: on the express routes, a passenger arriving at random waits on average
1.2 minutes longer than the timetable implies, about 24% more. On the 25 busiest
trunk routes, 0.9 minutes, 11% more.** This is excess waiting time, the measure
London uses for its frequent buses, applied to Vilnius for the first time as far as
I know. It turns the bunching found on 18 September into one number per route that
a passenger would recognise.

22 autumn working days, 2 September to 1 October, 07:00 to 19:00. 211 route
directions, comparing every observed trip with the timetable version in force that
day.

---

## 1. The measure

If buses run every 10 minutes exactly, a passenger who turns up at a random moment
waits 5 minutes on average. If they come in pairs, 2 minutes apart then 18, the
average is still one bus per 10 minutes but the average wait is 8.2 minutes, because
most passengers arrive during the long gap. The average wait for random arrivals is

  sum of squared gaps / (2 × sum of gaps)

computed once from the gaps the timetable plans (**scheduled wait**) and once from
the gaps that actually ran (**actual wait**). The difference is the **excess wait**:
time lost to irregularity and missing trips, beyond what the timetable itself
builds in.

## 2. By kind of route

| | routes | scheduled gap | scheduled wait | actual wait | **excess wait**, 95% CI | |
|---|---|---|---|---|---|---|
| express (G routes) | 7 | 8.6 min | 5.05 min | 6.24 min | **+1.19 [+1.12, +1.26]** | +24% |
| trunk, 25 busiest others | 25 | 12.6 min | 7.73 min | 8.59 min | **+0.86 [+0.78, +0.95]** | +11% |
| the rest | 74 | 31.6 min | 18.60 min | 19.20 min | +0.60 [+0.53, +0.67] | +3% |

Intervals are a bootstrap over days.

The ordering repeats the 18 September finding from the passenger's side. The more
frequent the route, the more of the wait is lost to bunching: express passengers
lose a quarter again on top of the planned wait, tail-route passengers almost
nothing. On routes running every 30 minutes people time their arrival rather than
turning up at random, so the last row is the least meaningful of the three.

Restricting to days when a route ran within 5% of its scheduled number of trips, so
that cancelled or unrecorded trips cannot drive the result, gives +1.04, +0.81 and
+0.46 minutes. Most of the excess is irregularity, not missing trips.

## 3. By route

Express and trunk routes, worst first:

| route | scheduled gap | scheduled wait | actual wait | **excess** |
|---|---|---|---|---|
| bus 33 | 15.4 | 8.1 | 10.0 | **+1.9** |
| bus 4G | 7.9 | 4.2 | 5.9 | **+1.7** |
| bus 3G | 6.7 | 3.8 | 5.3 | **+1.6** |
| bus 2G | 8.9 | 4.7 | 6.1 | +1.4 |
| bus 52 | 15.7 | 8.8 | 10.2 | +1.4 |
| trolleybus 7 | 6.2 | 3.6 | 4.8 | +1.2 |
| bus 3G-A | 18.5 | 9.6 | 10.8 | +1.2 |
| bus 24 | 19.2 | 10.7 | 11.9 | +1.2 |
| trolleybus 2 | 6.4 | 3.3 | 4.4 | +1.1 |
| ... | | | | |
| trolleybus 9 | 14.9 | 8.0 | 8.5 | +0.6 |
| bus 119 | 16.2 | 8.9 | 9.2 | +0.4 |
| bus 10 | 15.5 | 8.3 | 8.7 | +0.4 |
| bus 31 | 18.6 | 9.6 | 9.9 | +0.4 |

All minutes. The full table, all 106 routes, is `analysis/excess-wait-2026-10-02.csv`.

On 4G and 3G, the two most irregular express routes, the actual wait is 40% above
the scheduled one. On trolleybuses 7 and 2, the most frequent routes in the city,
it is about a third above.

## 4. What this is and is not

**It measures the wait at the start of each trip.** A trip's start is the moment the
feed assigns its trip id, the same timing used on 18 September. Bunching usually
grows along a route, so passengers at busy stops in the middle of a line probably
wait longer than this. Treat these figures as a floor.

**It assumes passengers arrive at random.** That is right for routes every 10
minutes or so and wrong for routes every 30, where people check the timetable.

**It does not include crowding.** A bus that arrives full and leaves people behind
does not show up as a gap.

## What it means

The city's frequency promise was kept (18 September). The wait the promise implies
was not: on the express routes a passenger loses about 70 seconds per journey to
irregularity, and on trolleybuses 7 and 2 more than a minute against a planned wait
of about three and a half. The fix for that is not more buses but more evenly spaced ones,
which is a question of dispatching and of the roads in section 1 of the 2 October
note on roads and vehicles.

## Method

Observed starts: `t0` in `analysis/blocks-*.json.gz`, by route and direction, trips
starting 07:00 to 19:00. Scheduled starts: the first departure of every trip active
that day, from the latest version in `gtfs/` dated no later than the day after,
using `calendar.txt` and `calendar_dates.txt`. Gaps outside 0.5 to 90 minutes are
dropped, as on 18 September. A route-direction-day needs at least 10 trips in both.
Express means a G route; trunk means the 25 non-express routes with the most
observed trips. Waits are pooled over days and directions as sum of squared gaps
over twice the sum of gaps.
