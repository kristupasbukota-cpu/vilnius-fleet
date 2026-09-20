# How late is Vilnius?

An independent measurement of Vilnius public transport punctuality, built entirely
from the city's own live GPS feed. No survey, no press release, no operator
dashboard. Every number here comes from the same file the JUDU journey planner
reads, polled every 10 seconds since 15 August 2026 and kept.

*Current as of 20 September 2026. The long account of how the instrument was built
and why is `docs/state-of-play-2026-08-18.md`; this page is the front door.*

---

## Where it stands

| | |
|---|---|
| snapshots | 303,842 |
| span | 15 August to 20 September 2026, 37 days |
| raw archive | 5.0 GB compressed, on the box |
| complete days exported | 33, no gaps |
| uptime | 4 weeks, 5 days |
| faults since 25 August | none |

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
Recovery time mid-shift would fix a problem this network does not have.

**Since September the morning is the worse peak.** The city added about 17% more
service on 1 September. Delay per hop in the 07-08 window went from +1.65 s to
**+8.99 s**, difference [+5.02, +9.67]. The evening is unchanged at -0.52
[-3.55, +2.50], and the whole day did not move measurably. **91% of the extra
delay the autumn network creates falls in two morning hours**, across every
distance band, not one corridor.

**Buses arrive early far more often than they leave early.** 10 to 13% of trips
end more than a minute ahead, 18.5% on the last run of a shift. But only
**2.09%** leave more than a minute early, once measured at the scheduled
departure rather than at the first sighting of a trip id. The widely repeated
13.5% was reading the previous trip's arrival.

**The city's published promises hold.** Express routes deliver a median gap of
7.9 minutes against a promised 5 to 10. Of the 25 busiest main routes, none is
slower than the promised 10 to 25 and eleven are faster. The archive also
reproduced the city's own "633 vehicles, 18% more" claim from the outside, at
+17.0%, with no prior knowledge.

**What the averages hide.** On trunk routes, one gap in five is under half the
advertised frequency and almost one in ten is more than double it. The promise is
about the service run, not about the wait, and on a frequent route those differ.

---

## What is open

- Whether the morning deterioration is still growing or has settled
- Weather joined to the record, which would remove a confounder
- Whether the 46.1 km of bus lanes sit where the delay actually is
- The five districts promised more service, against a control
- A passenger-experienced waiting time measure, as opposed to headway
- Route 61 direction 1, which reads 20.5% early departure and is unexplained
- A recurring boot volume backup. The raw archive is still effectively single-copy.

---

## What is in this repository

| | |
|---|---|
| `docs/` | every finding, dated. Start with `docs/README.md`. |
| `analysis/` | per-day derived tables: traversals, blocks, departures |
| `segments/` | per-day stop-to-stop segment files |
| `summaries/` | the rolling summaries the visualization is built from |
| `gtfs/` | every timetable version the city has published since 14 August |
| `code/` | everything that runs on the box |
| `report/` | the generated segment report and its data |
| `status.json` | collector health, rewritten every night |

The raw snapshot archive is **not** here. It is 5 GB and growing by roughly
2.3 GB a month, which git would not survive. The derived tables are the
scientific product and they are what is kept.

## How findings get here

Every finding is written to `docs/` on the box and pushed. A result that exists
only in a conversation is a result with one copy. See `docs/PUBLISHING.md`.
