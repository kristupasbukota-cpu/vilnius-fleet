# How late is Vilnius? State of play

Written 18 August 2026, 01:15 Vilnius time, three days into the project.

---

## 1. What this is

A study of how punctual Vilnius public transport actually is, built entirely from the
city's own live GPS feed. No survey, no press release, no operator dashboard. Every
number comes from the same file the JUDU journey planner reads, polled every 10
seconds and kept.

The one question it answers so far: **is the city late, when, and where.**

---

## 2. What happened, in order

| When | What |
|---|---|
| Sat 15 Aug, 03:03 | First snapshot. 15 August is Žolinė, a public holiday, so this is a holiday timetable. |
| Sat 15 Aug | Feed refresh rate measured empirically at 5.5 s, so polling faster is pointless. Collector started at 30 s, later tightened to 10 s. |
| Sun 16 Aug | First visualization. Map replay, day chart, filters. |
| Sun 16 Aug | Bunching analysis and the delay map added. |
| Mon 17 Aug | An ordinary working day collected, by accident rather than plan: the collector had simply never stopped. |
| Mon 17 Aug, 21:26 | An always-on machine created in Oracle's Milan region. Collector moved there. |
| Mon 17 Aug, 22:12 | Both collectors running in parallel for the overlap check. |

Total collected: **16,117 snapshots, 227 MB, covering 67 hours** across a holiday, a
Sunday and a weekday.

---

## 3. What we are actually collecting

**Source:** `https://www.stops.lt/vilnius/gps_full.txt`, published by SĮ "Susisiekimo
paslaugos" (JUDU). Plain CSV, no API key, no rate limit published. It refreshes every
5.5 seconds, measured, and carries roughly 300 to 550 vehicles depending on the hour.

Each row is one vehicle at one moment, with 17 fields. **We use 9 of them. Eight are
being written to disk and never read.** That is the single biggest opportunity in the
project, and it is covered in section 7.

### Fields we use

| Field | Meaning | What it gives us |
|---|---|---|
| `Marsrutas` | route short name | route filter, per-route stats |
| `Transportas` | bus / trolleybus / ferry | mode filter |
| `MasinosNumeris` | vehicle id | tracking one vehicle between snapshots |
| `Platuma` / `Ilguma` | latitude / longitude, ×10⁶ | the map, the delay grid |
| `Greitis` | speed, km/h | "actually moving" vs parked-but-transmitting |
| `NuokrypisSekundemis` | seconds behind schedule, negative = early | **every lateness number in the project** |
| `KryptiesPavadinimas` | destination text | tooltips, the table |
| `IntervalasPries` | seconds to the vehicle ahead | the bunching analysis |

### Fields we collect and ignore

| Field | Example | Filled | What it would unlock |
|---|---|---|---|
| `ReisoIdGTFS` | `T10-03-6-260620-ba-1000` | 98% | **Joins to the official timetable.** 94% match `trips.txt` exactly. |
| `ReisoPradziaMinutemis` | `598` (09:58) | 98% | Which trip of the day a vehicle is on. |
| `MatavimoLaikas` | `36892` (10:14:52) | 100% | The true GPS fix time, rather than when we happened to poll. |
| `Azimutas` | `0` to `360` | 100% | Direction of travel, so a road can be split inbound vs outbound. |
| `IntervalasPaskui` | seconds to the vehicle behind | 88% | The other half of the bunching picture. |
| `KryptiesTipas` | `A>B`, `D>A` | 100% | Which end of the route it is running toward. |
| `MasinosTipas` | `KWNZ`, `KZ` | 98% | Vehicle attributes, 8 distinct codes. |
| `ReisoID` | `26779640958` | 98% | The operator's own trip identifier. |

Nothing here needs re-collecting. It is all already on disk, in every snapshot since
Saturday morning.

### Also on disk

The **static GTFS feed** (`gtfs.zip`): 115 routes, 1,538 stops, **21,825 trips**,
**437,389 stop times**, plus route shapes and official colours. Currently used only
for route long names and to draw the route network as a basemap. This is the other
unopened box.

---

## 4. What we have actually found

**The headline.** Vilnius runs late in the afternoon, not the morning, and that is a
property of the working week rather than of the time of day.

| day | morning 07-10 | afternoon 16-19 | difference |
|-----|-----|-----|-----|
| Sat 15 (holiday) | 2.12 min | 2.05 min | -0.08 |
| Sun 16 | 1.55 min | 2.08 min | +0.53 |
| Mon 17 | 2.30 min | **5.82 min** | **+3.52** |

Figures are the 90th percentile of lateness across the whole fleet, in minutes.

**The asymmetry.** Monday's morning peak runs 320 vehicles against Saturday's 181, and
arrives 0.18 min worse. Nearly double the fleet, the same punctuality. Monday's evening
peak runs essentially the same number of vehicles as its own morning and arrives 3.5 min
worse. Whatever fails at 17:00 is not volume.

**Bunching.** Only meaningful on frequent service, so the measure is restricted to
route-hours with a usual gap of 15 minutes or less. That leaves 17 routes. The express
`G` routes bunch at two to three times the rate of the trolleybus trunk routes on
comparable headways, which is backwards from what skipping stops should do.

**Where delay is created.** Every vehicle tracked minute to minute, deviation change
attributed to the midpoint of consecutive positions, binned onto a 250 m grid. 1,597
cells with enough traffic to trust. Worst well-sampled cell loses 73 seconds per vehicle
minute; the best claws back 64.

**Things I got wrong and corrected.** Route 51's 27% bunching was an artefact of a
4-vehicle route with a 40-minute headway. "No deviation reported" does not mean "heading
to a depot": 26% are ordinary passenger destinations. Deviations beyond ±60 minutes are
stale trip assignments, 0.19% of readings, now excluded and counted rather than silently
dropped. The day chart was drawing straight lines through 13 hours of missing data.

---

## 5. Where it runs now

```
Oracle Cloud, Milan            GitHub or similar          this session
VM.Standard.E2.1.Micro    →    (not built yet)      →     rebuilds the
1/8 OCPU, 1 GB, 83 GB disk                                 visualization
always free

collect.py under systemd, restarts on crash and on reboot (both proved)
summarize.py on a nightly timer at 00:20 UTC
```

The Mac still collects in parallel. That is deliberate and temporary: two independent
machines watching one feed is the cheapest correctness check available, and once they
agree over the overlap the Mac stops.

---

## 6. What is wrong with the current situation

Ordered by how soon it bites.

1. **The summariser will run out of memory in about eight days.** Measured, not guessed:
   it holds every headway reading in a list, 2.7 million a day at 42.7 bytes each, about
   110 MB a day on a machine with 1 GB.
2. **Rebuilding the visualization still needs the Mac awake.** The collecting no longer
   does, but the publishing path does not exist yet.
3. **One weekday.** Every claim about working days rests on a single Monday, with a
   4.5 hour hole in the middle of it.
4. **13 hours of the weekend is missing**, across 45 gaps, from wifi dropouts on the
   laptop. Now shaded on the chart rather than hidden, but still absent.
5. **The GTFS snapshot is going stale.** 6% of live vehicles already fail to match a
   trip id. It is never re-downloaded.
6. **The delay map conflates two different things.** A terminus with built-in recovery
   time looks identical to a junction where traffic is kind. Both show as "time regained".
7. **Eight fields and the entire timetable are collected and unread.**

---

## 7. How to improve it

### Tier 1: keep what exists working

Not optional, and none of it needs you.

- **Rewrite the summariser as a running tally.** Histogram buckets instead of lists, a
  checkpoint instead of a full rescan. Turns a job that dies in eight days into one that
  takes 30 seconds a night forever.
- **Publish from the box.** A small repository the machine pushes summaries and sampled
  frames to each night, so the visualization can be rebuilt from anywhere with nothing of
  yours switched on.
- **Re-download the GTFS feed weekly** and keep the old ones. The timetable is the thing
  we are measuring against; a stale copy quietly corrupts every comparison.
- **Watchdog.** If the feed goes quiet for 10 minutes, or the disk passes 80%, say so.
  Right now a silent failure stays silent until somebody looks.

### Tier 2: open the fields we already have

This is where the real gain is. All of it works on data already on disk, retroactively,
back to Saturday.

- **Join `ReisoIdGTFS` to `stop_times.txt`.** 94% match rate, 437,389 stop times waiting.
  This converts "this bus is 6 minutes late" into "this bus is 6 minutes late *between
  these two specific stops*", which is the difference between a heatmap and a diagnosis.
  It also separates real congestion from scheduled recovery time, fixing problem 6.
- **Use `block_id` from `trips.txt` to test the compounding hypothesis.** A block is one
  vehicle's whole day of work. If a bus on its sixth trip is reliably worse than the same
  bus on its first, that is the mechanism behind the evening collapse, and it argues for
  recovery time mid-shift rather than more vehicles. This is the most interesting open
  question in the project and the data is already sitting there.
- **Split the delay map by `Azimutas`.** Averaging both directions in a 250 m cell hides
  the asymmetry. Inbound at 08:00 and outbound at 17:00 are different roads in practice.
- **Use `MatavimoLaikas` instead of the filename.** Right now every rate is computed
  against when we polled, not when the GPS actually fixed. It also exposes stale
  positions, which we currently treat as fresh.
- **Use `IntervalasPaskui` alongside `IntervalasPries`.** Bunching is a property of a
  pair of buses; we are only looking forward.

### Tier 3: new questions worth asking

- **Buses running early.** Arguably the worse failure, since you cannot catch a bus that
  has already gone. We have the data and have never counted it.
- **Per-vehicle effects.** Is chronic lateness a property of a route, or of specific
  vehicles? `MasinosNumeris` and `MasinosTipas` are both already collected.
- **Weather.** Free historical data exists for Vilnius. Rain against lateness is one join
  away and would be a genuinely new variable rather than a reslice of the same one.
- **The long baseline.** Everything above is analysis. The one thing that cannot be
  rushed is time. A month gives day-of-week patterns, a season gives school terms and
  darkness, a year gives snow. The machine in Milan exists so that this costs nothing but
  patience.

---

## Recommendation

Tier 1 first, because in eight days it stops being optional. Then **the GTFS join**,
which is the single change that would most improve what this project can say. Everything
else is worth doing and nothing else changes the questions we can ask.
