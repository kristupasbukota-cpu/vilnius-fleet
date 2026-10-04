# How the city could improve the network: ten hypotheses, before testing

4 October 2026. Written and published **before any of them was tested**, so that the
tests cannot be fitted to the results afterwards. Each one says what would confirm it
and what would refute it. Results will be added to this list as dated notes, with
links. Nothing below is a finding yet.

The starting point is what the record already shows:

- Lateness belongs to roads at particular hours, not to vehicles or routes.
- The autumn morning problem is inbound and sits in two hours.
- Passengers wait longer than the timetable implies mostly because buses are unevenly
  spaced, not because trips are missing.

So most hypotheses are about road space and junctions. Three are about scheduling and
dispatching, which the city controls directly and cheaply.

---

## Road space and junctions

**H1. Inbound peak-hour bus lanes on the worst links would cut delay.**
- *Basis:* 15 of the 20 links that lose the most time have no lane alongside. The
  worst evening link, Čiurlionio st. to Tumo-Vaižganto st., loses 6.2 vehicle-hours a
  day. The other gaps are the approach to Žaliasis tiltas from Europos aikštė and the
  Rinktinės, Šeimyniškių and Vasaros streets corridor. Lane links lose about 3 s less
  per hop ([bus lanes](bus-lanes-2026-10-02.md)).
- *Test:* lane against non-lane links matched on traffic volume, hour and distance
  from the centre, inbound morning hops only.
- *Refuted if:* the 3 s advantage disappears once matched. That would mean lanes were
  simply built on easier roads.
- *Limit:* this compares different roads. Only a lane the city actually opens gives a
  before-and-after test.

**H2. On the worst link that has a lane, Rūdninkų st. to MO muziejus, the problem is
the junction, not the lane.**
- *Basis:* it is first or second worst in both peaks despite the lane.
- *Test:* from the GPS positions, where along the link is the time lost?
- *Supported if:* most of it is in the last 100 to 200 m before the junction. Then
  traffic-signal priority is the fix.
- *Refuted if:* the loss is spread evenly along the link.

**H3. Lazdynėliai's morning problem is buses queuing behind each other on the way out,
not general traffic.**
- *Basis:* service rose about 19%. The two exit links via Oslo st. went from +6 and
  −5 s per hop to +55 and +50 s ([districts](districts-2026-10-02.md)).
- *Test:* hour by hour, does delay on those links follow the number of buses
  scheduled, or the time of day regardless of bus count?
- *Supported if:* delay follows bus count. Then a queue-jump lane or a second stopping
  bay at Oslo st. would recover most of the half minute.

**H4. The evening slowdown in the last 2 km into the core comes from too many buses
per stop.**
- *Basis:* it is symmetric in both directions, which a one-way commuter flow would not
  produce ([one direction](one-direction-2026-10-02.md)).
- *Test:* delay against scheduled buses per hour per central stop pair, with the hour
  held fixed.
- *Supported if:* delay rises steeply above some number of buses per hour.

## Scheduling and dispatching

**H5. Even spacing would cut passenger waiting more than adding buses.**
- *Basis:* express passengers wait 1.2 minutes (24%) longer than the timetable
  implies, still +1.04 on days with full service. On 4G and 3G the wait is 40% above
  plan ([excess wait](excess-wait-2026-10-02.md)).
- *Test, the first question:* are buses already unevenly spaced when they leave the
  terminus, or does it build up along the route?
  - Departure times from `departure.py` at the scheduled time.
  - Arrival times from the end of each trip in the block tables.
  - Excess waiting time and the share of bunched gaps computed at both ends, over the
    same pairs of consecutive trips.
- *Second question:* how much of the irregularity at departure is buses leaving early,
  which a dispatcher can stop, and how much is buses arriving late from the previous
  trip, which needs layover or holding?
- *Supported if:* a large share of the excess wait is already present at departure
  (dispatching problem), or most of it builds along the route (holding at midpoints).
  Either way it is a scheduling fix.
- *Refuted if:* gaps are regular at both ends and the excess wait only appears through
  missing trips.

**H6. Every route with no scheduled stand at its terminus has more early departures.**
- *Basis:* route 61 direction 1 gets 0 to 1 minute at Kuprioniškės and 24% of its
  departures leave early ([route 61](route-61-early-2026-10-02.md)).
- *Test:* across all route-directions, early-departure rate against the scheduled
  stand before departure, from GTFS block_id.
- *Refuted if:* there is no relationship outside route 61.

**H7. The timetables have spare time in the wrong places.**
- *Basis:* 10 to 13% of trips finish more than a minute early, and lateness does not
  build up through a shift. Meanwhile inbound morning hops lose 17 s each.
- *Test:* end-of-trip deviation by route, direction and hour. Where are trips
  consistently early, and where consistently late?
- *Supported if:* off-peak and outbound trips are systematically early, so their
  running time can be moved to inbound morning trips with no extra buses.

## Demand

**H8. The autumn morning step is the school run.**
- *Basis:* it arrived on 2 September, sits at 07–09 and inbound, and Friday mornings
  run at about +3 s per hop against about +8 on Monday to Thursday
  ([morning](morning-settled-2026-09-30.md)).
- *Test:*
  - The pupils' autumn holiday, 2 to 8 November, already scheduled.
  - Delay on links near schools against links far from them, with school locations
    from the Ministry of Education's open data.
- *Refuted if:* the holiday week is as slow as the weeks either side.

**H9. Bus lanes protect against rain.**
- *Basis:* a wet hour adds about 1.3 s per hop, and the road stays slow for the hour
  after ([weather](weather-2026-09-30.md)).
- *Test:* the interaction of wet hour and lane link, within each day.
- *Supported if:* the rain penalty is smaller on lane links. That would strengthen H1.

## A data fix

**H10. Correcting the city's timetable data at two-bay terminals would make
passenger information more accurate.**
- *Basis:* at eight terminal loops the timetable lists both bays as separate stops and
  times the departure from the wrong one. At Vilkpėdės žiedas half of all departures
  read as early when they are not ([Vilkpėdės žiedas](vilkpedes-ziedas-defect-2026-09-20.md)).
- *Limit:* testing it needs journey-planner predictions, which this project does not
  collect. A recommendation more than a hypothesis.

---

## Order of testing

| | likely impact | cost to the city | testable now |
|---|---|---|---|
| **H5** even spacing | high: minutes per passenger journey | low | yes |
| H6 terminal stands | medium | very low | yes |
| H8 school run | high | policy, not money | 10 November |
| H1 inbound lanes | high | medium | partly |
| H2 signal priority | medium | medium | yes |
| H3 Lazdynėliai | medium, local | low | yes |
| H7 spare time | medium | very low | yes |
| H4, H9 | medium | varies | yes |

H5 first. It is the cheapest fix with the largest effect a passenger would notice.

## The general caveat

Everything testable here compares different roads, hours or days, not the same road
before and after a change. Results will be associations. Only a change the city
actually makes gives cause and effect.

---

## Results so far

Added as each test is done. The hypotheses above are unchanged.

- **H5, 4 October: partly supported.** Departures from the terminus are even; the
  unevenness builds along the route. Perfect spacing would save an express passenger
  about 0.5 minutes (8%), a trunk passenger 0.3 minutes (3%), about twice that in the
  morning peak. That is worth about as much as 8% more express buses, not more than
  the 17% the city added. The terminus-dispatching version is refuted. The test also
  corrected the 2 October excess-wait figures. See
  [even spacing](even-spacing-2026-10-04.md).
