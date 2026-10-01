# Checking the weather record

1 October 2026. An audit of the weather data added on 30 September, prompted by a
suspicion that it might be inaccurate.

**Result: the weather record is sound, and the main weather results survive an
independent instrument. Three things were wrong or overstated, and are corrected
here:** the station's distance from the city centre, a line implying the station
sits at the airport, and how firmly the day-level "wet morning" effect was stated.
One real limitation was found: the station's rain gauge misses light drizzle.

Everything below is reproduced by [`code/weather_audit.py`](../code/weather_audit.py).

---

## 1. The record itself

| check | result |
|---|---|
| hours, 14 Aug to 30 Sep | 1,152, none missing, none duplicated |
| null precipitation or temperature | none |
| total rain | 162.0 mm |
| values changed between the 30 Sep fetch, the nightly files and a fresh fetch on 1 Oct | none, in any field |

The service did not revise anything after publishing it, and what is on GitHub is
exactly what the service returns today.

## 2. Is each row filed under the right hour?

This is where an error would do the most damage, and the 30 September analysis had
assumed the answer without testing it: that the row stamped T describes the hour
**ending** at T, in UTC. The service's documentation says only "sum per hour".

Tested against an instrument with nothing in common with the station: the METAR
reports of **Vilnius airport (EYVI)**, issued at :20 and :50 past every hour, from
the Iowa Environmental Mesonet archive. If the airport reports rain during the hour
from H to H+1, which LHMT row agrees best?

| LHMT row stamped | agreement with airport rain (Jaccard) |
|---|---|
| H-1 | 0.299 |
| H | 0.431 |
| **H+1** | **0.564** |
| H+2 | 0.479 |

The best match is the row stamped at the **end** of the hour, which is the reading
used throughout. Temperature agrees: the airport's H:20 and H:50 readings sit 0.66°C
from the LHMT reading at H+1 and 0.79°C from the one at H, against 2.34°C if the
timestamps were three hours off, as they would be if they were really local time.
**Timestamps are UTC and mark the end of the hour, as assumed.**

## 3. What was wrong

**The station is not where the 30 September document said.** It said Vilniaus AMS
is "about 9 km south-west of the old town". It is **13.4 km west-south-west of
Cathedral Square**, and 11.5 km from the airport. The same document said "a shower
can soak Žirmūnai and miss the airport", which reads as if the station were at the
airport. It is not. Both are corrected in place there, with the original wording
quoted.

**The rain gauge misses light drizzle.** In 52 of the 199 hours whose condition code
says rain, the gauge measured 0 mm. 31 of the 52 sit next to an hour with measured rain, the edges of
showers; 21 stand alone. Over the same 1,152 hours the airport reported rain in 204
and the station's gauge measured it in 148. Light rain under the gauge's 0.1 mm
step is being counted as dry.

**On three days the station recorded no rain at all while the airport reported
it**: 24 August, 18 September and 30 September. On a fourth, 24 September, the
airport reported drizzle and light rain between 06:20 and 07:20 local that the
station, 13 km away, never measured,
so a morning filed as dry was wet in the city.

Misfiling some wet hours as dry blurs the comparison, so it tends to understate the
rain effect, not invent it.

## 4. Do the results survive?

The three weather results re-run under four definitions of a wet hour. For a like-for-like comparison,
a wet morning here means any wet hour in 07-09; the published model used 0.5 mm or
more over the two hours, which gave the +2.96 below.

| definition of a wet hour | wet hours | a wet hour, within its day | wet morning, day level | dry-morning trend, s per week |
|---|---|---|---|---|
| A. as published, LHMT 0.1 mm | 73 | +1.31 [+0.29, +2.15] | +2.40 [+0.41, +4.31] | -1.06 [-1.85, -0.54] |
| B. LHMT 0.1 mm or a rain code | 92 | +1.56 [+0.43, +2.53] | +2.40 [+0.46, +4.31] | -1.06 [-1.86, -0.55] |
| C. **airport METAR** | 95 | **+1.39 [+0.33, +2.56]** | **+1.44 [-0.45, +3.41]** | **-1.19 [-2.01, -0.34]** |
| D. LHMT read the wrong way | 73 | +1.20 [+0.33, +2.04] | +2.96 [+0.92, +4.65] | -1.06 [-1.84, -0.54] |

Autumn morning jump with rain held fixed: +6.8 to +7.2 s per hop under every
definition.

**Holds under every definition:**

- A wet hour adds about 1.2 to 1.6 s per hop within its own day. With the airport as
  the instrument, +1.39, its interval clear of zero.
- The autumn morning jump is not weather.
- On dry Monday-to-Thursday mornings the morning has eased since the first school
  weeks. With the airport, -1.19 s per week, still clear of zero.

**Does not hold firmly: the day-level wet-morning effect.** The published +2.96
[+0.92, +4.65] depends on which instrument decides what a wet morning is. With the
airport it is +1.44 [-0.45, +3.41], and the interval includes zero. The airport adds
24 September, a modest +7.91 morning, to the wet list. The three worst autumn
mornings, 10, 17 and 23 September, are wet under every definition, so "the worst
mornings were the wet ones" stands. The size of a wet morning's penalty, measured
day by day, is not established. The hour-level estimate, which compares hours within
the same day, is the one to quote.

## 5. Something coming that is not a weather error yet

Lithuania leaves summer time on **25 October 2026**. From then local time is UTC+2,
not UTC+3. The weather join in `weather_effect.py` and the explorer page assume
UTC+3, and so does the bus side: `segments.py` and `blocks.py` fix the offset at
three hours when filing each hop under a local hour. From 25 October every hour
label in the record would be one hour late, and the weather would be joined to the
wrong hour. That needs fixing before 25 October. It is task #30.

---

## Corrections made

- `weather-2026-09-30.md`: station distance and the airport sentence corrected in
  place with the old wording quoted; a banner points here; the day-level wet-morning
  figure is marked as instrument-dependent.
- `code/weather.py`: the docstring's station description corrected.
- The explorer page footer: station distance corrected.
- `STATE-OF-PLAY.md`: notes that the rain result was checked against the airport.

## Method

`code/weather_audit.py`, run from the repository root, fetches the airport METARs
from `mesonet.agron.iastate.edu` and prints every number above. A METAR counts as
rain when its present-weather group contains RA or DZ, with any intensity, shower or
thunderstorm prefix. Bootstrap seeds are fixed.
