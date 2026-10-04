# How late is Vilnius?

An independent measurement of Vilnius public transport punctuality, built entirely
from the city's own live GPS feed. No survey, no press release, no operator
dashboard. Every number here comes from the same file the JUDU journey planner
reads, polled every 10 seconds since 15 August 2026 and kept.

*Current as of 4 October 2026. The long account of how the instrument was built
and why is `docs/state-of-play-2026-08-18.md`; this page is the front door.*

---

## Where it stands

| | |
|---|---|
| snapshots | 353,100 |
| span | 15 August to 26 September 2026, 43 days |
| raw archive | about 5.9 GB compressed, on the box |
| complete days exported | 39, through 25 September, no gaps |
| uptime | 5 weeks, 4 days |
| collector faults since 25 August | none |
| nightly chain | failed 24 to 26 September, fixed and caught up on 26 September. See `docs/nightly-outage-2026-09-26.md` |
| timetable refresher | killed at its timeout every night 27 September to 3 October after installing each new timetable, so no version was lost; fixed 4 October. See `docs/timetable-refresher-2026-10-04.md` |

```
Oracle Cloud, Milan            github.com/                anywhere
VM.Standard.E2.1.Micro    →    kristupasbukota-cpu/  →    rebuilds the
1/8 OCPU, 1 GB, 83 GB disk     vilnius-fleet              visualization
always free

collect.py under systemd, restarts on crash and on reboot
summarize.py, nightly_segments.sh, export.py, publish.sh on a nightly timer
watchdog.py every 15 minutes, heartbeat to an orphan `status` branch
```

The push uses an SSH deploy key generated on the box itself, so no token was ever
typed anywhere.

---

## What is established

**The evening collapse is a property of roads, not vehicles.** Lateness does not
accumulate through a shift. Within one bus's own day, holding road, hour, route
and direction fixed, a crossing late in the shift gains **0.63 s less** than one
early in the shift, 95% CI [-0.84, -0.42], with a placebo returning +0.004.
Recovery time mid-shift would fix a problem this network does not have. Nor does
lateness belong to vehicles in any lasting way: the persistent difference between
one link at a given hour and another is **22.4 s per hop**, between vehicles on the
same link **1.5 s**, between routes **2.1 s** ([roads, not vehicles](docs/roads-not-vehicles-2026-10-02.md)).

**Since September the morning is the worse peak.** The city added about 17% more
service on 1 September. Delay per hop in the 07-08 window went from +1.65 s to
**+8.99 s**, difference [+5.02, +9.67]. The evening is unchanged at -0.52
[-3.55, +2.50], and the whole day did not move measurably. **91% of the extra
delay the autumn network creates falls in two morning hours**, across every
distance band, not one corridor. It was a step, not a slope, and it has since eased: on dry
Monday-to-Thursday mornings delay fell from about +11 to about +8 s per hop between
the second and third week of term and has held there with no trend through
1 October, still about five times the dry
summer morning ([morning](docs/morning-settled-2026-09-30.md), [weather](docs/weather-2026-09-30.md)).

**The autumn morning runs one way.** Between 07:00 and 09:00 a hop towards the
centre costs **+17.0 s**, a hop away from it **+2.1 s**. 74% of the extra morning
delay is on inbound hops, in every distance band and on 93 of 101 routes. The
evening has no matching outward rush; it is slow on the last 2 km into the core in
both directions ([one direction](docs/one-direction-2026-10-02.md)).

**Rain slows the network by about a third.** Within the same day, a wet hour adds
**+1.31 s per hop**, 95% CI [+0.26, +2.17], roughly 25 to 35% of the delay in every
window, and the road stays slow for the hour after. A placebo with each day given
another day's weather returns -0.03. Weather does not explain the autumn jump, which
is +6.8 s per hop with rain held fixed. Hourly LHMT observations are now part of the
record, nightly, back to 14 August. Checked on 1 October against Vilnius airport's own
weather reports: the timing is right and the hour-level result holds, +1.39 s with the
airport deciding which hours were wet ([audit](docs/weather-audit-2026-10-01.md)).

**Buses arrive early far more often than they leave early.** 10 to 13% of trips
end more than a minute ahead, 18.5% on the last run of a shift. But only
**1.85%** leave more than a minute early, once measured at the scheduled
departure rather than at the first sighting of a trip id, and at both bays of a
terminal loop rather than only the first one GTFS lists. The widely repeated
13.5% was reading the previous trip's arrival. The one route that stood out,
61 direction 1 at 19%, is two vehicles: on the same scheduled trips, 7020 and 7003
left early 29 times in 72 and 7017 never, from a terminus the timetable gives a
one-minute turnaround ([route 61](docs/route-61-early-2026-10-02.md)). On the autumn
network it persists at 24%, now with no scheduled stand at all; 7020 is still the worst
but other vehicles do it on some days and not others, which points at who is driving
rather than which bus.

**The city's published promises hold.** Express routes deliver a median gap of
7.9 minutes against a promised 5 to 10. Of the 25 busiest main routes, none is
slower than the promised 10 to 25 and eleven are faster. The archive also
reproduced the city's own "633 vehicles, 18% more" claim from the outside, at
+17.0%, with no prior knowledge. Of the five districts promised more frequent
routes, four got a larger rise in service than the rest of the city; Baltupiai did
not. In Lazdynėliai the extra buses now lose about half a minute more per hop
leaving the district each morning ([districts](docs/districts-2026-10-02.md)).

**What the averages hide, and what it costs.** Buses leave the terminus evenly
spaced, then drift together along the route. At mid-route on the trunk lines about one
gap in thirteen is under half the usual gap and one in sixteen more than double. A
passenger arriving at random waits about **0.5 minutes (8%)** longer than the
timetable implies on the express routes and **0.3 minutes (3%)** on the trunk routes,
about twice that in the morning peak, and up to a minute on bus 3G. Perfect spacing
would be worth about as much as 8% more express buses ([even spacing](docs/even-spacing-2026-10-04.md)).
These replace larger figures published on 18 September and 2 October, which timed each
trip from the moment its id first appeared in the feed rather than from its departure.

**The bus lanes are aimed at volume, not at the worst places.** Roads with a lane
carry 18% of hops on 5% of the length, but 15 of the 20 links that lose the most time
have no lane alongside, including the worst in the evening, Čiurlionio st. to
Tumo-Vaižganto st. ([bus lanes](docs/bus-lanes-2026-10-02.md)).

---

## What is open

- Ten hypotheses for improving the network, written before testing ([hypotheses](docs/hypotheses-2026-10-04.md)); H5 done, partly supported; nine to go
- Check 26 October, the first full winter-time day, came through the summer-time fix cleanly
- Whether the morning falls back during the pupils' autumn holiday, 2 to 8 November
- Repository growth: option B in place from 3 October, 1 GB pushed to about mid-June 2027; the history rewrite (C) is not chosen ([plan](docs/repo-growth-plan-2026-10-02.md))

---

## What is in this repository

| | |
|---|---|
| `docs/` | every finding, dated. Start with `docs/README.md`. |
| `analysis/` | per-day derived tables: traversals, blocks, departures; `.gz` to 2 October, `.xz` after |
| `segments/` | per-day stop-to-stop segment files |
| `summaries/` | the rolling summaries the visualization is built from |
| `gtfs/` | every timetable version the city has published since 14 August; from 3 October most as patches, rebuilt with `code/gtfs_rebuild.py` |
| `code/` | everything that runs on the box |
| `report/` | the generated segment report and its data |
| `status.json` | collector health, rewritten every night |

The raw snapshot archive is **not** here. It is 5 GB and growing by roughly
2.3 GB a month, which git would not survive. The derived tables are the
scientific product and they are what is kept.

The raw archive is protected instead by a weekly boot volume backup on Oracle,
policy `vilnius-weekly`: incremental, Sundays 10:00 UTC, kept 20 days, set on
24 September 2026. Always Free allows five volume backups in total, so the
retention keeps at most three from the policy plus the manual one from
29 August, leaving one slot free. The first ran on 27 September and was checked
on 29 September: available, 7 GB incremental, expiring 17 October, 2 of 5 slots
in use.

## How findings get here

Every finding is written to `docs/` on the box and pushed. A result that exists
only in a conversation is a result with one copy. See `docs/PUBLISHING.md`.
