# How late is Vilnius?

A study of the Vilnius public transport fleet, built from the city's own live GPS feed.

## The data

The city publishes every tracked vehicle's position, continuously, with no API key:

- **Live positions**. `https://www.stops.lt/vilnius/gps_full.txt`
  CSV, one row per vehicle. Roughly 380 vehicles at night, more in the daytime.
- **Static timetable**. `http://www.stops.lt/vilnius/vilnius/gtfs.zip`
  Standard GTFS. 115 routes, 1538 stops, official route colours.

### Fields that matter

| Field | Meaning |
|---|---|
| `Marsrutas` | Route short name, joins to GTFS `route_short_name` |
| `Platuma` / `Ilguma` | Latitude / longitude, **integers. divide by 1 000 000** |
| `Greitis` | Speed in km/h |
| `NuokrypisSekundemis` | **Deviation from timetable in seconds. Positive is late.** Empty when no timetabled trip is matched to the vehicle. See the correction below: that is *mostly* but not only depot running. |
| `KryptiesPavadinimas` | Where it is heading. Depot names here mean it is off-service. |
| `MasinosNumeris` | Vehicle number, stable across snapshots, so vehicles can be tracked over time |

### Verified, not assumed

- Feed is genuinely live: 183 of 379 vehicles changed position across 90 seconds.
- Coordinate scaling `/1e6` puts every vehicle inside 54.63–54.86 N, 25.18–25.49 E.
- Deviation has a median of 0.0 min, so it is a real schedule comparison, not noise.

## Files

| File | What it does |
|---|---|
| `collect.py` | Polls the feed every 30 s, writes `snapshots/<UTC timestamp>.csv.gz`. Backs off if the feed fails, never longer than 5 minutes. |
| `build_map.py` | Reads all snapshots, joins GTFS route names, emits a self-contained HTML replay. |
| `template.html` | The map itself. Leaflet is inlined, so the only network call is for map tiles. |

## Restarting

```bash
python3 -m pip install playwright --break-system-packages   # only if you want screenshots
curl -sL http://www.stops.lt/vilnius/vilnius/gtfs.zip -o gtfs.zip
curl -sfL https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js  -o leaflet.js
curl -sfL https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css -o leaflet.css

nohup python3 -u collect.py &          # start collecting
python3 build_map.py                   # rebuild the map from whatever exists
python3 build_map.py --every 4         # thin it out once you have hours of data
```

Storage is about 15 KB per snapshot, so roughly 1.8 MB per hour, 30 MB for a full day.

## Design notes

Deviation is a **diverging** quantity: early and late are opposites with a real
"nothing" in the middle. So the scale is two single-hue arms meeting at a neutral
grey, never a rainbow. Both arms and both poles were checked with the palette
validator in light and dark against the actual basemap colours, rather than by eye.

Vehicles with no timetable are drawn as **hollow rings**, not a second shade of
grey, so "no schedule" rides a shape channel instead of colliding with the grey
that means "on time".

## What the first ten hours showed

Collected Sat 15 Aug 2026 (Zoline, a public holiday), 03:03 to 13:19, 1231 snapshots, 99.9% coverage.

**Vilnius stops completely for 18.5 minutes.** From 03:57:25 to 04:15:25 the feed returns a
valid CSV header and zero rows, across 37 consecutive snapshots. Not a dropout. The last
vehicle is seen at 03:56:55 and 27 reappear at 04:15:55.

**The median deviation is useless.** It reads +0.0 min at every hour of the day, because half
the fleet is always exactly on time. It reports a perfect city at 4am and a perfect city at
noon. Use the 90th percentile instead: +0.0 min at 04:33, rising steadily to +4.6 min at
11:54. Lateness in Vilnius does not live in the average bus, it lives in the tail, and the
tail stretches from dawn to midday.

Caveat that matters: before roughly 04:40 fewer than 120 vehicles are on a timetable, so p90
swings on single vehicles. Peak detection filters to frames with at least 120 scheduled
vehicles for that reason.

## The evening answer

Collected through 19:30. The prediction was that a public holiday would show one
lateness hump rather than the two a working weekday produces. It holds:

| window | p90 mean | p90 max |
|---|---|---|
| morning  09:00 to 12:00 | **+3.26 min** | +4.6 min |
| evening  16:00 to 19:30 | **+2.21 min** | +3.0 min |

There is no second hump. The evening is materially calmer than the morning, not
busier. Fleet size is flat at ~360 across both windows, so this is not a supply
effect: the same number of vehicles are simply having an easier time of it.

Whether that is the holiday or is just how Vilnius behaves needs an ordinary
weekday to answer, which is the obvious next collection.

## The shutdown has two phases

Collected to 21:37. The evening wind-down is invisible in the headline count and
only appears once scheduled vehicles are separated from deadheading ones.

| time | tracked | scheduled | deadheading | share |
|---|---|---|---|---|
| 16:00 | 363 | 360 | 3 | 1% |
| 19:00 | 356 | 331 | 25 | 7% |
| 20:40 | 344 | 293 | 51 | 15% |
| 21:26 | 311 | 284 | 27 | 9% |

**Phase one, roughly 19:00 to 20:40.** Vehicles finish their last scheduled run and
start driving to the depot. Deadheading climbs from 25 to 51 while the tracked
count barely moves: they are still on the road, just no longer buses.

**Phase two, from about 20:40.** Those vehicles reach the depot and stop reporting
at all, so they leave the feed entirely. Tracked falls 344 -> 311 while deadheading
falls back 51 -> 27.

The arithmetic closes exactly. Between 20:40 and 21:26 the tracked count drops 33.
Of that, 24 is deadheaders arriving at depots and disappearing, and 9 is further
vehicles going off-schedule. 24 + 9 = 33.

So deadheading is not a level, it is a **queue**: vehicles enter when they finish
service and leave when they get home. Its length is the arrival rate multiplied by
the drive time, which is why it peaks mid-shutdown and then drains.

Throughout all of this p90 holds between +2.0 and +2.7 min. The vehicles still in
service are entirely unbothered.

## A prediction that was wrong

Collected to 23:03, 20.0 hours, 2589 snapshots, still zero failures.

I predicted the fleet would shut down around 23:00. It did not. At 23:01 there are
287 vehicles tracked, 271 of them still on a timetable, and 172 actively moving.
Vilnius is running a reduced late service, not stopping.

**`tracked` turns out to be a poor measure and `moving` is the honest one.**
Parked vehicles linger in the feed for a while before they stop reporting, so the
tracked count is inflated by buses that are already home:

| time | tracked | moving | stationary |
|---|---|---|---|
| 20:00 | 351 | 162 | 189 (54%) |
| 21:40 | 300 | 191 | 109 (36%) |
| 23:01 | 287 | 172 | 115 (40%) |

The moving count actually *rises* through the evening while tracked falls. The
decline in `tracked` is largely parked vehicles ageing out of the feed, not
service being withdrawn.

The same trap catches the comparison with the previous night. At 00:07 on 15 Aug
there were 379 tracked, which looks busier than 23:01's 287, but 241 of those were
stationary. On the moving measure it is 138 then against 172 now, the opposite
ordering. Any claim built on `tracked` alone would have been backwards.

So the real collapse is later than expected, somewhere between midnight and 03:00,
converging on the 18.5-minute standstill already recorded at 03:57.

## The collapse, and the most punctual hour of the day

Collected to 01:00 on Sun 16 Aug. 3289 snapshots, 44 MB, 22.0 hours, zero failures.

The shutdown I wrongly predicted for 23:00 begins almost exactly at midnight:

| time | tracked | scheduled | moving | p90 |
|---|---|---|---|---|
| 23:40 | 289 | 265 | 148 | +2.1m |
| 00:00 | 277 | 239 | 105 | +1.6m |
| 00:20 | 264 | 213 | 63 | +1.5m |
| 00:40 | 245 | 155 | 45 | **+0.5m** |
| 01:00 | 226 | 109 | 36 | +0.6m |

Moving vehicles fall from 148 to 36 in eighty minutes.

**The last buses of the night are the most punctual of the entire day.** At 00:40,
with 155 vehicles still on a timetable, p90 is +0.5 min. The midday figure is
+4.6 min. The unluckiest tenth of the fleet at midnight is nine times closer to
schedule than the unluckiest tenth at noon, on the same day, running the same
network. Nothing is in the way, so nothing goes wrong.

### A chart bug worth recording

Crossing midnight broke two things that had been silently correct all day. Hour
labels ran off the end as `24:00` and `25:00`, and the chart cursor parsed a frame
stamped `00:40` as *earlier* than the 03:03 start, so click-to-seek jumped to the
wrong place. Fixed by giving each frame an explicit `m` field: minutes on one
continuous axis that keeps counting past 1440 rather than wrapping. Wall-clock
strings are for display only; never compute on them.

## Panel rework

Four changes, after the `tracked` vs `moving` finding made the old page misleading.

**Stat tiles.** The page led with "Vehicles tracked", the number proven unreliable.
Now it leads with **On the move**, with the reporting count demoted to the note
underneath, and a second tile splits scheduled from depot-bound.

**Day chart.** The fleet plot now carries two series: *reporting* as a filled area,
*actually moving* as a line on top. Area against line is a shape channel, so the
pair never depends on colour to be told apart, and the gap between them reads
directly as "parked but still transmitting". Added a hover crosshair with exact
figures, and rotated titles on both y-axes, which were previously unlabelled.

**Table.** Sortable on every column, ascending and descending, with an |Deviation|
column so the furthest-from-schedule sort is explicit rather than implied. 60 rows
instead of 25, horizontally scrollable on narrow screens.

**Layout.** Everything is a panel on a consistent surface. Map height is now
`min(58vh, 560px)` rather than a fixed 540px. Resize is debounced and calls
`map.invalidateSize()`, without which Leaflet keeps a stale projection after a
phone rotates.

### What the new chart shows

At 12:54: **361 reporting, 212 actually moving.** So roughly 40% of the fleet is
stationary at any given midday instant, at stops, at lights, at termini. That gap
is visible at a glance now and was completely hidden before.

## Two days: the controlled comparison

Collected to Sun 16 Aug 10:58. **6760 snapshots, 80 MB, 32 hours, one failure.**

### The standstill happens at the same minute both nights, and lasts 37x longer on one

| night | window | duration |
|---|---|---|
| Fri 14 -> Sat 15 | 03:57:25 to 04:15:25 | **18.5 min** |
| Sat 15 -> Sun 16 | 03:57 | **0.5 min** |

Both begin at 03:57. That minute looks structural: the last night service finishes
and the first morning service has not begun. But the gap it opens is wildly
different, 18.5 minutes against a single 10-second snapshot.

### Sunday runs better than the holiday, at every hour, with the same fleet

Zoline was a public holiday. Sunday 16th was an ordinary Sunday. Matched hours:

| hour | Sat 15 (Zoline) | Sun 16 |
|---|---|---|
| 05:00 | p90 +2.00, moving 134 | p90 +1.70, moving 130 |
| 06:00 | p90 +2.21, moving 178 | p90 +1.61, moving 177 |
| 07:00 | p90 +1.98, moving 181 | p90 +1.42, moving 178 |
| 08:00 | p90 +2.07, moving 183 | p90 +1.46, moving 179 |
| 09:00 | p90 +2.78, moving 170 | p90 +1.91, moving 167 |
| 10:00 | p90 +3.29, moving 194 | p90 +1.90, moving 190 |

**Sunday is better in all six hours, and the number of vehicles moving is within
2% every time.** This is close to a controlled experiment: consecutive days, same
network, same operator, near-identical supply. The only variable is the day.

By 10:00 the holiday is 73% worse than the Sunday (+3.29 against +1.90) with four
fewer vehicles on the road. So the lateness is not an operational property of the
fleet, it is a property of the traffic around it. Zoline puts people in cars.

That answers the question the project opened with, and it did it by accident: the
control group was the next morning.

## Filters now drive the chart

Selecting a mode or route redraws the day chart for that selection.

**Two sources, chosen automatically.** Unfiltered, the chart uses the precomputed
arc built over every snapshot collected (7172 points, full resolution). Filtered,
that series no longer describes what is on screen, so one is derived client-side
from the map frames (304 points) and cached per filter. The subtitle always states
which is in use, so the resolution drop is never silent.

### The bug this exposed: implausible deviations

Filtering to trolleybuses produced a peak p90 of **588 minutes**. Investigating the
raw distribution:

| quantile | deviation |
|---|---|
| p50 | +0.0 min |
| p90 | +2.1 min |
| p99 | +18.0 min |
| p99.9 | +77.5 min |
| max | **+665.3 min** |
| min | **-388.3 min** |

A vehicle reporting +665 min is not late, it is carrying a stale trip assignment.
Route 49 is the worst offender. These are **0.19% of readings**, so they never
moved the whole-fleet p90, whose tail is far larger than 0.19%: **every earlier
finding in this file stands unchanged.** But a single route has ~14 vehicles, so
its p90 is roughly the second-worst bus and one bad reading defines it.

Readings beyond +/-60 min are now excluded from every percentile and **counted**
rather than silently dropped. The count appears in the chart subtitle and the
hover tooltip.

### Robust axis scaling for small selections

Even within the cap, a single route spikes. Route 7 has a median p90 of 2.0 min
but 2 frames of 282 exceed 20 min, and those two would define the whole y-axis.
So when the maximum exceeds 3x the 95th percentile, the axis scales to the bulk
instead and reports how many frames run above it. On the whole fleet the maximum
is never an outlier, so the unfiltered view is untouched.

Worth a look once loaded: **trolleybuses peak at +5.5 min at 22:18**, a completely
different shape from the bus fleet's late-morning hump.

## Correction: "no deviation" does not mean "heading to a depot"

I labelled every vehicle with an empty `NuokrypisSekundemis` as depot-bound.
Checked against the data, that is right for three-quarters of them and wrong for
the rest. Of 5014 sampled rows with no deviation value:

| destination | share |
|---|---|
| looks like a depot (`...parkas`, `AP2`, `Transrevis`) | 3700, **74%** |
| an ordinary passenger stop | 1314, **26%** |

Examples from the second group: route 69 to Lazdyneliai, route 2 to Stotis,
route 75 to Santariskes. Ordinary destinations, no timetable attached.

The reverse also holds. Every destination in that list *also* appears on vehicles
that do report a deviation. "Autobusu parkas (Verkiu g.)" shows up 3253 times
without one and 2457 times with, so a depot run is not automatically unmatched.

**The field means: the operator has no timetabled trip matched to this vehicle
right now.** Usually because it is driving to or from a depot. Sometimes because it
is between trips, running an extra, or simply unassigned.

Nothing numerical changes: these rows were always excluded from every percentile,
because the deviation value is what is missing. Only the wording was wrong.

## Bunching, from two fields we never opened

`IntervalasPries` and `IntervalasPaskui` are the headways in seconds to the vehicle
ahead and behind on the same route. 94% populated. Median 1154 s, about 19 minutes.
They had been sitting in every snapshot since the first one.

A vehicle counts as **bunched** when its gap to the vehicle ahead has collapsed
below half the median gap for that route in that hour. The baseline is computed
over every snapshot collected, so it reflects what the route actually runs rather
than what the timetable claims. Ferries are excluded: three boats on a river make
the idea meaningless.

**Fleet-wide, 2.7% of observations are bunched.** By route:

| route | bunched | n | what it is |
|---|---|---|---|
| 51 | 30.9% | 440 | Zemieji Paneriai-Traku Voke-Pagiriai |
| 125 | 9.8% | 387 | Gabijos progimnazija-Visoriu g.-Bajorai |
| 4G | 8.1% | 1431 | Pilaite-Konstitucijos pr.-Sauletekis |
| 3G | 7.0% | 2121 | Perkunkiemis-Seskine-Centras-Oro uostas |
| 19 | 5.8% | 1633 | Pasilaiciai-Konstitucijos pr.-Antakalnis (trolleybus) |

**Treat route 51 as suspect.** It is a peripheral route, and on an irregular
timetable half the median gap may simply be the timetable rather than bunching.
The figure to trust is 3G at 7.0% on n=2121: a high-frequency airport route where
an even headway genuinely is the design intent. Verifying 51's vehicle count and
gap distribution is unfinished.

### Bunching and lateness are different problems at different times

| hour | bunched |
|---|---|
| 07:00 | 1.3% |
| 12:00 | 2.0% |
| 17:00 | 4.9% |
| 18:00 | **7.0%** |

Lateness peaks in the late morning. Bunching peaks in the early evening. They do
not coincide, so they are not the same failure wearing two hats.

In the tool: a **Bunched** tile, an outer ring on bunched vehicles on the map
(shape, so it stacks on the deviation colour rather than fighting it), the gap in
the hover tooltip, and a ranked panel of the worst routes.

## Where the schedule is lost and won

Collected to Sun 16 Aug 22:06. **8587 snapshots, 108 MB, 41 hours, one failure.**

Every vehicle is followed minute to minute by `MasinosNumeris` and asked how its
deviation changed between consecutive observations. The change is attributed to the
midpoint of the two positions and binned onto a ~250 m grid. Jumps beyond 10 minutes
in one minute are dropped as trip reassignments rather than delay.

**1114 cells cleared 40 transits**, out of 3469 seen.

| | seconds gained per vehicle-minute | transits |
|---|---|---|
| worst well-sampled cell | **+73.4** | 808 |
| best well-sampled cell | **-63.6** | 89 |

Toggle it with the **Delay map** button. Same diverging scale as the vehicles: red
is time lost, blue is time recovered, grey is where the timetable holds.

**Read it as where the timetable is won and lost, not as a congestion map.** A
terminus with recovery time built into the schedule shows blue because the
timetable allows it, not because the road is quick. Genuine congestion and
scheduled slack both live on this map and it does not separate them.

### A stacking bug worth recording

The first version called `heatLayer.bringToBack()`. `LayerGroup` has no such
method, so the call threw and the grid rendered *on top of* the vehicles, hiding
the thing the map is about. Fixed with explicit Leaflet panes (`heatPane` 350,
`netPane` 360, vehicles in the default 400) rather than trusting insertion order.
Caught only because the console was checked; the screenshot looked plausible.

## The weekday, at last: the claim survives and gets much bigger

Monday 17 August, an ordinary working day, collected from 00:00 to 20:43 with one
4.5 h hole in the middle when the laptop slept. Every earlier conclusion in this file
rested on a public holiday and a Sunday, so this is the first real test.

The whole-fleet 90th percentile, median across the frames in each hour, over frames
with at least a quarter of the day's peak timetabled fleet behind them:

| hour | Sat 15 (holiday) | Sun 16 | Mon 17 |
|------|-----|-----|-----|
| 07:00 | 1.96 | 1.35 | 1.97 |
| 08:00 | 2.05 | 1.40 | **3.14** |
| 09:00 | 2.73 | 1.87 | **3.73** |
| 15:00 | 2.48 | 2.23 | 3.35 |
| 16:00 | 2.18 | 2.17 | **5.49** |
| 17:00 | 1.98 | 2.02 | **7.03** |
| 18:00 | 2.02 | 3.33 | **5.17** |
| 19:00 | 2.38 | 3.10 | 2.08 |

Collapsed into two windows:

| day | morning 07-10 | afternoon 16-19 | difference |
|-----|-----|-----|-----|
| Sat 15 | 2.12 | 2.05 | **-0.08** |
| Sun 16 | 1.55 | 2.08 | +0.53 |
| Mon 17 | 2.30 | **5.82** | **+3.52** |

On a non-working day the afternoon is indistinguishable from the morning. The claim
was true but almost invisible: half a minute, well inside what two days of noise can
produce. On a working day the same comparison is 3.5 minutes, and Monday's 17:00 hour
is worse than the worst hour either weekend day produced anywhere.

So the finding is not "Vilnius runs late in the afternoon". It is that **the afternoon
penalty is a property of the working week, not of the time of day.**

### The asymmetry nobody would guess

Monday's morning peak moves 320 vehicles, against Saturday's 181, and arrives 0.18 min
worse. Nearly double the fleet, the same punctuality. Monday's evening peak moves 309,
essentially the same number as the morning, and arrives 3.5 min worse.

Whatever is failing in the evening is not volume. Both peaks run a similar fleet into a
similar city. The likely story is compounding: a morning bus starts its first trip from
a depot on time by construction, while an evening bus is on its fifth or sixth trip of
the day carrying whatever it lost on the previous four. That is testable against the
data already collected. It is the first question in the list below.

At the moment of the worst frame, Mon 17:30, the fleet reads: 536 vehicles on a
timetable, 19% of them more than 5 minutes late, 90th percentile +7.9 min, median
+1.0 min. Half the fleet is fine. The tail is what breaks.

## Corrections this round

### Route 51's 27% bunching was an artefact, and the fix removes a third of the chart

Route 51 topped the bunching table at 30.9%, then 27.0%. It was flagged as suspect
rather than reported. Settled now, and it was wrong.

Route 51 runs **4 vehicles on a weekday, 6 at the weekend**, with a baseline gap
between 24 and 48 minutes. Within a single hour its observed gaps run from 1.5 min to
57 min. The median gap is not a headway that anything regresses to. It is just the
middle of a wide, irregular spread, so "gap under half the median" fires on ordinary
timetable structure roughly a third of the time.

Bunching is only a meaningful idea where service is frequent enough that passengers
turn up without consulting a timetable. The rule is now **route-hours with a baseline
gap of 15 minutes or less**. That drops 51, 125, 28, 49 and 115 out entirely and leaves
17 routes:

| route | bunched | observations | vehicles | median baseline |
|-------|-----|-----|-----|-----|
| 3G | 9.3% | 5911 | 34 | 8.2 min |
| 4G | 7.6% | 4471 | 20 | 10.9 min |
| 6G | 7.0% | 3504 | 20 | 10.3 min |
| 2G | 5.6% | 4414 | 33 | 9.7 min |
| 7 | 5.2% | 6889 | 40 | 10.0 min |
| 1G | 5.2% | 6173 | 32 | 8.9 min |
| 6 | 2.8% | 3039 | 18 | 11.7 min |
| 2 | 2.7% | 4750 | 25 | 8.9 min |

Now it says something. The express routes (`G` for *greitasis*) bunch at two to three
times the rate of the trolleybus trunk routes, on comparable headways. Express routes
skip stops, so their running time depends more on traffic and less on boarding, which
should make them *more* regular, not less. That inversion is worth chasing.

### The baseline had to be split by day type

The headway baseline was a median per route and hour, pooled. With a weekday in the set
that breaks: route 51 runs every 25 min on Monday and every 42 min on Sunday, and the
pooled median calls neither of them normal. Keys are now `route|wd|hour` and
`route|we|hour`, with a pooled `route|*|hour` fallback for thin cells. 4276 keys.

### The chart was drawing straight lines through 13 hours of missing data

45 gaps, totalling 13.0 h of the 65.8 h span. Most are short wifi dropouts on Saturday
evening and Sunday afternoon; one is the 4.5 h Monday hole. A single polyline through
those prints a dead-flat segment, which reads as *the city held perfectly steady* when
the truth is *we were not looking*. Every line is now broken at any gap over 3 minutes,
the gap is shaded, and the total is printed in the scope line rather than left to be
noticed. This did not change a single number. It changed what the picture claims.

### Vehicle ids and destinations are interned

Three days of frames repeat the same 597 vehicle ids and 173 destination strings in
every frame they appear in. Stored once in `DATA.veh` / `DATA.dirs` and referenced by
index, which took the file from 15.4 MB to 10.9 MB with no loss.

### Hour ticks now scale to the span

66 hourly labels in 1100 px is a grey smear. The step is chosen from the span so labels
stay at least 52 px apart, and the peak annotation carries a day name now that "17:37"
is ambiguous three times over.

## The block test: the compounding hypothesis, answered

The evening question was: Monday's evening peak runs the same fleet as its morning and
arrives 3.5 minutes worse, so what fails? The proposed mechanism was compounding, a bus
on its sixth trip carrying everything it lost on the previous five.

The live feed's `ReisoIdGTFS` matches `trip_id` in the static GTFS feed for **90% of
readings**, and `trips.txt` carries `block_id`, one vehicle's whole day of work. Joining
them reconstructs **22,095 vehicle-trips** across 595 vehicles, 889 blocks and three days,
each trip knowing where it sat in its own shift, what it carried in, and what it lost.

### Test 1: refuted

Comparing a bus on its tenth trip with one on its second is worthless if the tenth runs
at 17:00. So the comparison is made **inside one route, in one hour, on one day**: same
line, same traffic, same moment, only the shift depth differs.

| | |
|---|---|
| route-hours compared | 448 |
| median difference, deeper-in-shift minus shallower | **-0.06 min** |
| cells where deeper-in-shift was worse | **43%** |

If shift depth mattered this would be clearly positive. It is not. On Monday alone it is
-0.20 min. **The evening problem is not tired buses.**

### Test 2: something larger

Take every trip that arrived more than a minute late and look at the same vehicle starting
its next trip. Trip pairs straddling a collection gap are discarded, 1,265 of them.

| day | arrived | starts next trip | survives | n |
|---|---|---|---|---|
| Mon 17 | +2.60 min | +2.35 min | **90%** | 2,837 |
| Sun 16 | +1.98 min | +1.77 min | 89% | 1,279 |
| Sat 15 | +2.22 min | +1.82 min | 82% | 2,190 |

The observed gap between one trip ending and the next starting is **10 seconds**. There is
essentially nowhere to put recovered time.

### The two results are consistent

A 90% carry-over does not explode, it converges. Each trip loses a little and keeps most of
what it had, so lateness settles at roughly ten times the per-trip loss and stops growing.
A bus on its twelfth trip is no worse than one on its sixth because both hit the ceiling
hours earlier. That is exactly what test 1 measured.

### Where the damage is actually done

Splitting each Monday trip into what it carried in and what it lost while running:

| hour | carried in at start | lost during the trip |
|---|---|---|
| 05:00 | +0.00 | +0.26 |
| 07:00 | +0.03 | +0.31 |
| 14:00 | +0.25 | +0.45 |
| 15:00 | +0.40 | **+0.82** |
| 16:00 | +1.29 | +0.78 |
| 17:00 | **+1.83** | **-0.54** |
| 18:00 | +0.60 | -0.35 |

**17:00 trips recover time.** The fleet's worst moment is not where the loss happens; it is
where the loss arrives. The deficit is built between 14:00 and 16:30 and then carried in,
because the 10 second turnaround gives it nowhere to go.

Which changes what the finding argues for. Not more vehicles at 17:00. **Recovery time in
the schedule from 14:00 to 16:30.**

### The trap this nearly fell into

The first run of this analysis showed Sunday afternoon layovers of 17 to 31 minutes and
lateness dropping to 0% carried, a spectacular result. It was entirely an artefact: Sunday
15:00 to 20:00 is exactly where the laptop's wifi dropped out, so consecutive observed
"trips" were separated by holes in the collection rather than by layovers. Filtering trip
pairs against the known gap list removed it. Anything that looks like a discovery in the
window where collection failed is a bug until proven otherwise.

## The summariser is now incremental, and the archive lives in two places

Two pieces of plumbing, neither visible in any chart, both of which decide whether
this project still exists in six months.

### The nightly job no longer reads the whole archive

Measured on the box itself: holding every headway reading costs **42.7 bytes each**
and **2.7 million arrive per day**, about 110 MB of memory daily on a machine with
1 GB. The old summariser rebuilt from the first snapshot every night, so it would
have been killed by the kernel around **26 August**.

It now keeps a state file and processes only what is new. The three outputs needed
three different tricks:

| output | shape | how it becomes incremental |
|---|---|---|
| arc | one row per snapshot, independent | append |
| delaygrid | a sum and a count per map cell | sums add |
| baseline | a **median** per route-hour | medians do not add: a sparse tally of 5 s buckets |

The tally is the interesting one. A median normally needs every value, so instead of
storing 2.7 million numbers a day it counts how many gaps fell in each 5-second
bucket. That is fixed in size forever and returns the median to within half a bucket.

Verified rather than assumed:

- **Identical output.** The same 752 snapshots processed in one pass and in three
  incremental passes produce byte-identical `arc.json`, `baseline.json`,
  `delaygrid.json` and `framelist.txt`.
- **On the real box**, with the delay grid actually populated, an incremental run and
  a full rebuild agree on **all 2,077 shared arc rows** and on **every one of 493
  grid cells**. The 24 baseline keys that differ by 5 to 20 s differ because the
  rebuild caught one extra snapshot, not because the algorithms disagree.
- **Accuracy against the exact median**: across 3,897 route-hours the tally is off by
  a flat **2 seconds**, which is the bucket-centre offset. 100% land within half a
  bucket. 16 route-hours sit exactly on the 15-minute frequent-service threshold and
  can fall on either side of it; on a route whose median headway is exactly 900 s
  that classification was always arbitrary.
- **Cost**: a full rebuild of 20,429 snapshots takes **105 s and peaks at 79 MB**. A
  nightly run over one day takes about 40 s. Neither grows with the size of the
  archive.

Two bugs found by testing rather than by reading:

The tally originally covered 0 to 30 minutes in 360 buckets. The **typical route-hour
headway is 29 minutes**, so most of the distribution piled into the last bucket and
medians came out up to **38 minutes wrong**. Widened to 1440 buckets, two hours.

The tally used `cumulative >= n/2` where the exact code used `v[n//2]`. On an even
count with a bimodal route-hour those two conventions can pick values **half an hour
apart**. Changing one comparison to `>` removed the entire class of difference.

### The first three days existed on one laptop

The box started collecting on Monday evening. Saturday, Sunday and most of Monday
lived only in `~/Downloads` on a MacBook. That is not an archive, it is a single
point of failure with a lid.

All **20,428 snapshots, 234 MB** are now on the box as well, and the state was rebuilt
over the whole set. The collection now has two independent copies and the laptop is
genuinely disposable.

## Open questions for the analysis

- Which routes are chronically late, and is it the route or a specific vehicle?
- Does lateness compound along a route, or does slack in the timetable absorb it?
- Where in the city does delay accumulate? Junctions should show up as red clusters.
- ~~15 August is Žolinė, a public holiday. Worth collecting an ordinary weekday.~~
  Done, 17 August. See above.
- ~~Does the evening penalty come from compounding?~~ Answered above. No, but the
  carry-over between trips is 90% and the turnaround is 10 seconds.
- **Join to `stop_times.txt`.** The trip id is already matching. 437,389 scheduled stop
  times would move the delay map from a 250 m grid to named segments between named stops,
  and separate congestion from scheduled recovery time.
- **Where in the 14:00 to 16:30 window is the time actually lost?** The block test says
  when. The stop-times join would say where.
- Why do the express `G` routes bunch two to three times more than the trolleybuses
  they run alongside?
- Buses running *early* are arguably the worse failure. How common is it?
