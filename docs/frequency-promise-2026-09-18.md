# The frequency promise is kept, and the average is doing a lot of work

18 September 2026. Task #5, the second of JUDU's public claims tested against the feed.

**The claim.** From the 21 August announcement: express routes will run on average every
5 to 10 minutes, main routes every 10 to 25.

**The verdict: both halves hold.** Measured on twelve autumn working days, 135,000
observed gaps between consecutive trips, 96 routes. This is delivered frequency, not
timetabled frequency: the gaps are between trips that actually ran.

---

## 1. Express routes: promised 5 to 10 minutes

| route | median gap | p25 | p75 | 07-09 | 16-18 |
|---|---|---|---|---|---|
| 1G | **6.5** | 4.0 | 8.8 | 5.4 | 5.0 |
| 3G | **6.7** | 3.7 | 9.8 | 5.7 | 7.5 |
| 4G | **7.8** | 4.5 | 11.2 | 7.3 | 6.8 |
| 2G | **8.2** | 5.2 | 11.5 | 8.0 | 8.3 |
| 6G | **8.5** | 6.2 | 10.7 | 8.8 | 8.3 |
| 5G | **9.0** | 5.9 | 12.2 | 8.2 | 8.0 |
| 3G-A | 18.2 | 13.7 | 21.3 | 17.4 | 16.4 |

Six of seven sit inside the promised band, and all six are better than promised at both
peaks, between 5.0 and 8.8 minutes. Pooled median 7.9 minutes.

The exception, 3G-A, runs at 18.2 minutes. Its name marks it as a branch variant of 3G
rather than a headline express service, so I would not call this a broken promise
without knowing how the city classifies it.

## 2. Main routes: promised 10 to 25 minutes

This half needs care, because "pagrindiniai" is a specific set of trunk routes and the
feed does not label them. Taking the 25 busiest non-express routes as the fairest
available proxy:

| | routes |
|---|---|
| inside 10-25 min | **14** |
| **faster** than 10 min | **11** |
| slower than 25 min | **0** |

**Not one of the 25 busiest routes is slower than promised.** Eleven are better than
promised: route 7 runs every 4.2 minutes, route 2 every 5.8, routes 16 and 18 every 6.7.
Median across the top 25 is 11.8 minutes.

Across all 85 non-express routes, 45 have medians above 25 minutes, between 26 and 60.
Those are the suburban tail, 33 to 50 trips a day, and the promise was plainly never
about them. Counting them as failures would be dishonest arithmetic.

## 3. What the average conceals

The promise is about averages and the averages are true. The gap a passenger actually
waits is a different question.

| | gaps | bunched, under half the route's own median | gapped, over double | p90 / median |
|---|---|---|---|---|
| express | 21,948 | **17.9%** | 6.5% | 1.79 |
| trunk (25 busiest) | 62,884 | **20.9%** | 8.7% | 1.93 |
| infrequent tail | 50,594 | 9.1% | 3.3% | 1.54 |

On the busiest routes, **one gap in five is less than half the advertised frequency and
almost one in ten is more than double it.** Concretely:

| route | median | one gap in ten exceeds | one in a hundred exceeds |
|---|---|---|---|
| 1G | 6.5 min | 11 min | 18 min |
| 3G | 6.7 min | 13 min | 22 min |
| 7 | 4.2 min | 10 min | 17 min |
| 2 | 5.8 min | 11 min | 22 min |
| 16 | 6.7 min | 14 min | 22 min |

A passenger told "every 5 to 10 minutes" who arrives at random will, one time in ten,
wait about twice that. The promise is honest about the service the city runs. It is not
a promise about the wait, and those are not the same thing on a frequent route.

**The irony is that frequency causes this.** The infrequent tail is the most reliable
relative to its own schedule, 9.1% bunched against 20.9% on the trunk routes, because
buses twenty minutes apart cannot easily catch each other and buses four minutes apart
can. Bunching is the price of frequency, and it is worst exactly where the city is
investing most.

---

## Verdict

**Claim confirmed.** Express routes average 7.9 minutes against a promised 5 to 10.
The busiest main routes average 11.8 against a promised 10 to 25, and none is slower
than promised.

This is the second JUDU claim the archive has checked and the second it has upheld,
after the 633-vehicle count on 1 September.

**The claim worth making next is not theirs but ours.** The city advertises headway.
Nobody advertises the distribution, and on the routes most people use, the distribution
is where the experience lives. That is a measurement the city does not publish and this
archive now can.

## Method

Delivered headway is the gap between consecutive observed trip starts on the same route
and direction, taken from the published `blocks-*.json.gz` tables. Gaps outside 0.5 to
90 minutes are dropped as artefacts. Twelve autumn working days, 1 September excluded
as a ceremonial day with no normal timetable. Routes with fewer than 100 observed gaps
are excluded.

The known weakness: a trip's start is the moment the feed assigns its trip id, which the
departure work in August showed lands near the previous trip's arrival rather than at
the scheduled departure. For measuring the interval between successive buses this
shifts every observation by a similar amount and largely cancels, but it is a reason to
treat single-minute differences between routes as noise.
