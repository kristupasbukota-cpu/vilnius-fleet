# Bus lanes, matched, and in the rain

18 October 2026. The fourth and fifth tests of the [hypotheses](hypotheses-2026-10-04.md):
H1, *inbound peak-hour bus lanes on the worst links would cut delay*, and H9, *bus lanes
protect against rain*.

**Results: H1 inconclusive, leaning towards the lanes. H9 supported in a modest form.**

- **The lane advantage does not disappear once matched.** On inbound hops between 07:00
  and 08:59, a link with a bus lane loses **7.2 s less per hop** than links without one
  at the same hour, the same distance from the centre and the same number of buses.
  Unmatched, the gap is 2.2 s. So the lanes were not simply built on easier roads,
  which is what would have refuted H1.
- **But the uncertainty is wide.** Only 59 inbound links with a lane have enough morning
  buses to compare. Resampling those links gives a 95% interval of **−20 to +5 s**, so the
  data cannot rule out no effect. A second matching method gives −4.7 s, interval
  −22 to +8.
- **Timetable effects shrink it.** With the padded links found in H7 and their
  neighbours left out, the matched gap is −4.4 s (−17 to +10). Measured as speed, which
  the timetable cannot distort, lane links are +0.3 km/h faster (−1.7 to +2.4): no clear
  difference.
- **Rain hurts lane links about half as much.** A wet hour adds **+1.3 s** per hop on
  links with a lane and **+2.4 s** on links without one at the same distance from the
  centre, in the same hour of the same day. The difference, **−1.1 s**, has a 95% interval
  of −1.8 to −0.4. In heavier rain, 1 mm or more in the hour, it is −1.2 s
  (−2.3 to −0.04).
- **Compared with every other link, not only nearby ones, the rain advantage vanishes**
  (−0.3 s, −1.1 to +0.4), because rain slows the outer network less than the centre,
  where most lanes are. The like-for-like comparison is the one that answers H9.

H1: 33 working days, 2 September to 16 October 2026, 369,394 inbound morning hops on
725 links. H9: 43 working days, 18 August to 16 October (1 September left out), 688
day-hours from 06:00 to 21:59, 95 of them wet.

---

## 1. The lanes

The city's layer **"Viešojo transporto A juostos (Esamos)"** from Vilniaus planas,
downloaded again today: 78 sections, 42.8 km of lane line. As in the
[first bus-lane note](bus-lanes-2026-10-02.md), a link has a lane alongside if at least
five of nine points along it lie within 30 m of a lane running within 30° of parallel.
The layer does not say which direction a lane serves, so "has a lane" means a lane
runs alongside in either direction. That overstates coverage, which works against
finding an effect.

155 of 2,047 links have a lane. Inbound means the hop ends more than 100 m closer to
Cathedral Square ([one direction](one-direction-2026-10-02.md)).

## 2. H1: matched comparison

Each link is measured separately in each of the two morning hours, if at least about
1.5 buses an hour run inbound on it. Lane links are compared with non-lane links in
the same cell of hour (07 or 08), distance from the centre (0-1, 1-2, 2-3, 3-4, 4-5,
5-7, 7-10 and over 10 km) and bus volume (fifths). Every lane link found a match.

Seconds lost per hop, lane links minus non-lane links:

| comparison | gap | 95% interval |
|---|---|---|
| unmatched | −2.2 | |
| **matched on hour, centre distance and volume** | **−7.2** | **−20.3 to +5.2** |
| matched, also on link length | −7.7 | |
| nearest three non-lane links per lane link | −4.7 | −21.7 to +8.1 |
| matched, padded-neighbour links left out | −4.4 | −16.8 to +9.8 |
| matched, busiest half of links | −8.6 | −23.5 to +5.1 |
| matched, within 5 km of the centre | −11.8 | −31.2 to +5.9 |
| speed instead of delay, km/h | +0.3 | −1.7 to +2.4 |

Intervals resample whole links, 500 times, because the question is about roads and
links differ far more than days do ([roads, not vehicles](roads-not-vehicles-2026-10-02.md)).

Lane links sit closer to the centre than other links (median 3.9 km against 6.0 km) and
carry four times the buses (median 17.9 an hour against 4.3), so the unmatched gap
understated the lanes. Matching widens it.

**Padded neighbours.** H7 found links that look slow only because the timetable gives
the link next to them too much time. 34 links run at least 25 s under schedule on
average on inbound mornings. Leaving them and the 42 links next to them out takes about
two fifths off the matched gap.

**Speed.** Delay is measured against the timetable, so a generous timetable on a lane
link would look like a lane benefit. Average speed is free of that. Matched, it shows
no clear difference. Part of the delay gap is therefore the timetable giving lane
links a little more time, not the bus moving faster.

For context, the same matched gap outside the inbound morning: outbound 07-08 −0.8 s,
inbound 16-18 −8.4 s, outbound 16-18 −2.3 s.

## 3. H9: rain

Following the [weather](weather-2026-09-30.md) method: for every working-day hour, the
mean delay on lane links and on non-lane links, then a least-squares fit with a level
for every day and every hour of the day, summer and autumn apart. An hour is wet at
0.1 mm or more at Vilniaus AMS (LHMT, CC BY-SA 4.0). Intervals resample whole days,
1,000 times.

In the main version, non-lane links are taken from the same centre-distance bands as
the lane links and weighted the same way, so both sides of the comparison sit in the
same parts of the city.

Extra seconds per hop in a wet hour:

| hours | lane links | non-lane, same bands | difference | 95% interval |
|---|---|---|---|---|
| **all, 06-21** | **+1.29** | **+2.42** | **−1.13** | **−1.81 to −0.43** |
| peaks, 07-08 and 16-18 | +2.39 | +3.10 | −0.71 | −2.14 to +0.81 |
| off-peak | +0.25 | +1.12 | −0.87 | −1.64 to −0.08 |
| autumn only | +1.55 | +2.28 | −0.73 | −1.39 to −0.06 |
| rain of 1 mm or more | | | −1.18 | −2.32 to −0.04 |
| against all non-lane links | +1.29 | +1.64 | −0.34 | −1.07 to +0.42 |

The protection is clearest off-peak. In the peaks the point estimate points the same
way, but 34 wet peak hours are too few to settle it.

## 4. What it means for the city

- The case for lanes holds up against the obvious objection: lanes are not on easy
  roads, they are on the hardest, central and busy ones, and they still lose less
  there. How much less cannot be pinned down from 59 links. The honest range runs from
  a large benefit to none.
- Rain is where the lanes show most clearly. They roughly halve the extra delay a wet
  hour brings. One working-day hour in seven was wet over these weeks.
- The worst lane-less links named in H1, Čiurlionio st. to Tumo-Vaižganto st., the
  approach to Žaliasis tiltas from Europos aikštė and the Šeimyniškių st. corridor,
  remain the places to try. The only test that can settle H1 is a lane the city
  actually opens, measured before and after. The collection is running, so one would
  be measurable from its first day.

## 5. Limits

- It compares different roads. Matching on hour, centre distance and volume removes
  the obvious differences, not all of them: junctions, parking and stop layout differ.
- A lane in either direction counts. A link whose lane serves the other direction is
  counted as having one.
- Five lane sections apply only on working days 07:00 to 20:00. The H1 hours fall
  inside that; for H9, the hours 06:00 and 20:00 to 21:59 count those five as lanes
  when they are not in force, which works against finding an effect.
- One weather station, 13 km from the centre. Rain it misses blurs the result towards
  zero.

## Method and files

`code/bus_lanes_test.py`, run from the repository root as
`python3 code/bus_lanes_test.py LANES OUT_DIR`, reproduces the H1 table and the last row
of the H9 table, and writes `OUT_DIR/lane-links.csv`. Then
`python3 code/bus_lanes_checks.py OUT_DIR/lane-links.csv` gives the rest of the H9 table.
Both read `analysis/trav-*.csv.*`, `gtfs/gtfs-20261001.zip` and `weather/weather-*.csv`,
and need pandas and numpy.
Lane layer: `https://gis.vplanas.lt/arcgis/rest/services/Interaktyvus_zemelapis2/Transportas_public/MapServer/9`,
78 features, queried 18 October 2026, coordinates rounded to 5 decimals
(sha256 187e7c8b80116db900824df9a04a93f7b369539d38983e3eceddecc27dbb337c).
