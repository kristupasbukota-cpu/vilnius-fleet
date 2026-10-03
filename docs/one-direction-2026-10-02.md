# The autumn morning runs one way

2 October 2026. Task #10, the one-directional finding.

**Result: the autumn morning problem is almost entirely on the way into town.**
Between 07:00 and 09:00, a hop that takes a bus towards the centre now costs
**+17.0 s**, against **+2.1 s** for a hop heading out. Three quarters of the extra
morning delay the autumn network creates is on inbound hops. The evening is
different: it is slow on the approach to the core in both peaks, but it has no
outward rush to match the morning's inward one.

Mon to Thu working days, 18 August to 1 October, 1 September excluded: 8 summer
days and 18 autumn days. Hops starting between 0.5 and 10 km from Cathedral Square
unless stated. A hop is **inbound** if it ends more than 100 m closer to Cathedral
Square than it started, **outbound** if more than 100 m further, otherwise
tangential.

*On the August note this task was named after: the task list recorded a median
difference of 8.7 s and "9 of 583 extreme" between directions. No script or
document behind those numbers survives, so they cannot be checked and are not used.
This is a fresh measurement on a much larger archive.*

---

## 1. Inbound against outbound, by time of day

Mean seconds of delay per hop:

| | summer inbound | summer outbound | **autumn inbound** | **autumn outbound** | autumn, inbound minus outbound, 95% CI |
|---|---|---|---|---|---|
| morning 07-09 | +4.29 | -0.97 | **+16.98** | **+2.12** | **+14.85 [+13.02, +16.66]** |
| midday 09-16 | +5.76 | +1.38 | +3.13 | +1.77 | +1.37 [+0.70, +2.12] |
| evening 16-19 | +11.93 | +6.48 | +11.27 | +5.12 | +6.15 [+3.73, +8.75] |

Intervals are a bootstrap over days.

Autumn, hour by hour:

| hour | 06 | 07 | 08 | 09 | 12 | 15 | 16 | 17 | 18 |
|---|---|---|---|---|---|---|---|---|---|
| inbound | +2.7 | **+16.2** | **+17.8** | +5.1 | +2.1 | +5.9 | +13.6 | +15.4 | +3.8 |
| outbound | +1.0 | +3.8 | +0.4 | -1.4 | +0.9 | +6.0 | +9.1 | +7.8 | -1.6 |

## 2. Where the autumn morning went

Vehicle-hours of delay created on 07-09, per Monday-to-Thursday morning, every hop
whatever its distance from the centre:

| | summer | autumn | change, 95% CI | share of the change |
|---|---|---|---|---|
| **inbound hops** | 11.0 | 52.1 | **+41.0 [+34.4, +47.5]** | **74%** |
| outbound hops | -2.5 | 6.1 | +8.6 [+7.2, +10.0] | 15% |
| tangential hops | 2.6 | 8.5 | +5.9 [+4.8, +7.0] | 11% |

Per inbound hop the morning got worse by +12.3 s [+10.0, +14.5]; per outbound hop
by +3.2 s [+2.6, +3.7]. Outbound did get worse, but by a quarter as much.

The 18 September rerun found the extra morning delay spread across every distance
band and concluded it was "a property of demand", not of a corridor. That stands,
and this sharpens it: it is the **demand heading into town**.

## 3. Everywhere, and on almost every route

Autumn morning, by distance from Cathedral Square:

| | 0.5-2 km | 2-4 km | 4-6 km | 6-10 km |
|---|---|---|---|---|
| inbound | +31.3 | +16.1 | +14.0 | +11.7 |
| outbound | +1.9 | +2.3 | +2.7 | +1.3 |

Every band shows the same split, from the edge of the old town out to 10 km.

Of 101 routes with at least 300 inbound and 300 outbound morning hops, inbound is
worse on **93**, by more than 5 s per hop on 83. Outbound is worse by more than 5 s
on only 2. The largest gaps are bus 52 (+49 s), bus 121 (+41 s), trolleybus 21
(+33 s), bus 22 (+32 s) and trolleybus 17 (+31 s).

## 4. The evening is a different shape

In the evening, inbound is still slower overall, but only near the centre:

| autumn 16-19 | 0.5-2 km | 2-4 km | 4-6 km | 6-10 km |
|---|---|---|---|---|
| inbound | +40.3 | +9.0 | +4.1 | +1.3 |
| outbound | +7.9 | +8.2 | +2.5 | +2.1 |

Beyond 2 km the two directions are level. There is no outward rush mirroring the
morning's inward one. What is slow in the evening is the last two kilometres into
the core, whichever way the commute runs, which fits the long-standing finding
that the evening failure is a property of specific roads near Žaliasis tiltas.

## 5. Robustness

The split does not depend on where the 100 m line is drawn:

| threshold | autumn morning inbound | outbound |
|---|---|---|
| 50 m | +16.01 | +2.52 |
| 100 m | +16.50 | +2.14 |
| 250 m | +17.05 | +1.76 |
| 500 m | +17.85 | +0.71 |

*(These four use every distance from the centre; section 1 restricts to 0.5-10 km.)*

Distance to Cathedral Square is a blunt stand-in for "into town": a route crossing
the city tangentially passes the centre at some point. The tangential class, with
the clearest such hops, is reported separately and is not driving the result.

## What this means

**Established.** The autumn morning deterioration is directional. A morning bus
heading into town loses about eight times as much per hop as one heading out, and
three quarters of the new morning delay is on inbound hops, across the whole city
and on 93 of 101 routes.

**Not established: why.** Inbound general traffic, more boarding on inbound trips,
or both. Boarding volume is not in the feed. Weather, the school run and the bus
lanes (#6) all bear on it.

**What it suggests.** If the morning problem is inbound, measures aimed at it
should be inbound too: an inbound-only peak bus lane costs half the road space of a
two-way one.

## Method

`analysis/trav-*.csv.gz` for Monday to Thursday, 18 August to 1 October, with stop
coordinates from `gtfs/gtfs-20260824.zip`, `-20260901.zip` and `-20260929.zip`.
Distance to Cathedral Square (54.6857 N, 25.2876 E) on a local flat projection.
Means are per traversal; intervals resample whole days, 5,000 times.
