# H8, the school run: groundwork and test plan, written before the holiday

> Published 20 October 2026, before any holiday data exist. The test in section 2 is
> fixed as written on 18 October and will not be changed after the holiday.

18 October 2026. Preparation for H8 in the [hypotheses](hypotheses-2026-10-04.md):
*the autumn morning step is the school run*. This fixes the test before the data exists,
so that it cannot be fitted to the result afterwards. Nothing here tests H8 yet.

**In short**

- **The holiday dates are confirmed, with one correction.** The national calendar puts
  the pupils' autumn holiday on 2 to 8 November 2026, and pupils return on 9 November.
  But 2 November (Vėlinės) is a public holiday for everyone, so it says nothing about
  schools. The test uses **Tuesday 3 to Friday 6 November**: four working days without
  the school run. Schools may move their holiday with permission but may not shorten it.
- **School locations are in hand.** 190 active general-education schools and branches in
  Vilnius city from the Ministry of Education's open data, 147 of them with 100 or more
  pupils, 87,365 pupils in all.
- **Every link is now classed by distance to the nearest school.** Of 2,011 stop-to-stop
  links, 774 pass within 300 m of a school with 100 or more pupils ("near"), 732 are more
  than 800 m from one ("far") and 505 are in between. Near links carry 52% of all hops.
- **Near-school links are slower in the morning, but the comparison is confounded.**
  Between 07:00 and 08:59, near links lose **+9.7 s** per hop and far links **+3.4 s**.
  But near links are also much slower between 15:00 and 18:59 (+10.3 against +2.4), and
  they sit closer to the centre (median 3.6 km against 8.9 km). Schools are on busy
  streets. Only the holiday can separate the school run from the street.
- **Fridays do not single out schools.** On Friday mornings delay drops on near links by
  5.1 s and on far links by 4.0 s, about the same. The earlier Friday clue for H8 is
  real but does not point at schools in particular.

Working days 2 September to 16 October 2026, 6.66 million hops.

---

## 1. Baseline, before the holiday

Seconds lost per hop, by school proximity and hour of the hop:

| | before 07 | 07-08 | 09-14 | 15-18 | 19 and later |
|---|---|---|---|---|---|
| near (within 300 m) | +0.6 | **+9.7** | +2.6 | **+10.3** | +0.6 |
| middle (300 to 800 m) | +1.2 | +10.5 | +3.3 | +6.8 | +0.2 |
| far (over 800 m) | +0.2 | +3.4 | −0.3 | +2.4 | −0.8 |

07:00 to 08:59, near minus far, within distance bands from the centre:

| distance from centre | near | far | near minus far |
|---|---|---|---|
| 0 to 2 km | +14.2 | no far links | |
| 2 to 5 km | +7.6 | −2.5 | +10.0 |
| 5 to 10 km | +8.0 | +5.2 | +2.8 |
| over 10 km | +7.1 | +1.7 | +5.4 |

The gap survives inside each band, so it is not only distance from the centre. It is
still a comparison between different roads.

Day-to-day spread of the 07:00 to 08:59 mean: near links +9.7 s (standard deviation
3.5 s, 33 days), far links +3.4 s (2.1 s). A four-day mean has a standard error of
roughly 1.8 s near and 1.1 s far.

## 2. The test, fixed now

**Holiday days:** Tuesday 3 to Friday 6 November 2026.

**Comparison days:** the same weekdays, Tuesday to Friday, of three ordinary weeks:
20 to 23 October, 27 to 30 October and 10 to 13 November. One week before the clock
change, one after, and one after the holiday. Hours are Vilnius local time, which
follows the clock change since 1 October ([summer-time fix](summer-time-fix-2026-10-01.md)).
26 October, the first winter-time day, gets checked separately before it is used.

**Primary measure:** mean seconds lost per hop between 07:00 and 08:59, all lines.

**Controls:** the same measure between 09:00 and 14:59, and between 15:00 and 18:59,
which school holidays should change much less.

**Supported if**, against the mean of the three comparison weeks:

1. 07:00 to 08:59 delay falls by at least 3.5 s per hop, about half of the autumn step,
   which went from +1.65 to +8.99 s; and
2. it falls by at least 2 s more than the 09:00 to 14:59 control does; and
3. the fall is larger on near-school links than on far ones.

**Refuted if** the 07:00 to 08:59 fall is under 1.5 s, within ordinary week-to-week
noise. Between the two thresholds the result is reported as inconclusive.

**Supporting checks**, not part of the verdict: inbound against outbound hops, whose
gap carried 74% of the autumn step ([one direction](one-direction-2026-10-02.md));
links near primary schools against links near gimnazijos; and whether the city runs
a reduced holiday timetable that week, which would change the comparison and has to be
checked in the timetable versions first.

## 3. Limits

- The holiday week also removes parents' trips and some adults' leave, so a fall shows
  the school run together with what travels with it, not pupils alone.
- One week is one event. Weather that week matters, so the rain adjustment from
  [weather](weather-2026-09-30.md) is applied before the comparison.
- School locations are the registered address of each school or branch. A school using
  several buildings appears at one of them.
- The school list is a copy made today of one query of the Ministry's data; the
  warehouse download was blocked from this environment.

## Method and files

- `analysis/h8/schools-vilnius-2026-10-18.csv`: the school list, with coordinates and pupil counts.
- `analysis/h8/school-links.csv`: every link with its distance to the nearest school with 100 or
  more pupils, that school's name, pupils within 300 m and 500 m, and its class.
- `code/school_links.py`, run from the repository root, reproduces this document:
  `python3 code/school_links.py analysis/h8/schools-vilnius-2026-10-18.csv OUT_DIR`. It reads
  `analysis/trav-*.csv.*` and `gtfs/gtfs-20261001.zip` and needs pandas.

Sources for the dates: [Ministry of Education, 2026 to 2027 pupils' holidays](https://smsm.lrv.lt/lt/veiklos-sritys-1/smm-svietimas/20252026-m-m-ir-20262027-m-m-mokiniu-atostogos/),
[tavovaikas.lt](https://tavovaikas.lt/mokslai/2026-2027-m-m-mokiniu-atostogos-kada-laukia-rudens-kaledu-ziemos-ir-velyku-atostogos).
