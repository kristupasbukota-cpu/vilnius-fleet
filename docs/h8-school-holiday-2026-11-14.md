# H8: the autumn morning step is the school run. Supported.

14 November 2026. The test fixed on 18 October in section 2 of
[H8 groundwork](h8-groundwork-2026-10-18.md), run once, as registered.

**Result: in the pupils' autumn holiday the morning peak lost its delay almost
entirely.** Between 07:00 and 08:59 a hop lost **7.7 s less** than in the three
ordinary weeks around it (95% interval 5.9 to 9.6 s), against 0.3 s less at midday.
The fall was larger on links near schools (8.3 s) than on links far from them
(5.0 s). All three pre-registered conditions are met, with every version of the rain
adjustment.

## 1. Before the test

- **Winter time.** On 26 October, the first winter-time day, service starts at 04:00
  local as on 23 October, the hours carry the same traffic profile, and no hop is
  recorded more than 30 minutes before its trip's scheduled start (0.0% on 23, 26 and
  27 October). Local hours are right across the clock change.
- **No holiday timetable.** The holiday days ran the same service as ordinary days:
  1,712 to 1,716 trips with a hop between 07:00 and 08:59 (comparison days 1,663 to
  1,726), and the same scheduled time per hop (126.6 to 127.6 s against 125.3 to
  126.8 s). The comparison is like for like.
- **Data.** All 16 days are complete in 07:00 to 18:59 (2,153,805 hops). The thin
  evening of 4 November (21:00 to 22:59 local, [collection gap](collection-gap-2026-11-04.md))
  lies outside every window.

## 2. The test

Mean seconds lost per hop, all lines. Each day is weighted by its traversals, a period
is the mean of its days. Rain adjusted: each wet hour (0.1 mm or more) has the
published +1.31 s taken off ([weather](weather-2026-09-30.md)). The holiday week was
dry; the comparison weeks had 15 wet hours in the windows, 11 of them on Friday
23 October. Intervals: bootstrap over days within each week, 10,000 resamples.

| window | 20-23 Oct | 27-30 Oct | 10-13 Nov | comparison | holiday 3-6 Nov | fall, 95% CI |
|---|---|---|---|---|---|---|
| **07:00 to 08:59** | +6.94 | +5.01 | +10.18 | +7.38 | **−0.37** | **+7.75 [+5.88, +9.58]** |
| 09:00 to 14:59 | +1.39 | +2.39 | +1.99 | +1.92 | +1.59 | +0.34 [−0.46, +1.09] |
| 15:00 to 18:59 | +6.55 | +8.19 | +9.78 | +8.18 | +3.37 | +4.80 [+3.60, +5.94] |

| condition | needed | found | |
|---|---|---|---|
| 1. 07-08 fall | at least 3.5 s | +7.75 s | met |
| 2. 07-08 fall minus 09-14 fall | at least 2 s | +7.41 s [+5.30, +9.39] | met |
| 3. near-school fall larger than far | near > far | +8.29 against +4.98, difference +3.30 [+2.11, +4.57] | met |

**Verdict: supported.**

The same with the rain adjustment by window (07-08 +2.22, 16-18 +2.73, other hours
+0.74): fall +7.63, against midday +7.24. With no adjustment: +7.91 and +7.45. Against
each comparison week alone the 07-08 fall is +7.31, +5.38 and +10.55 s, each above the
3.5 s line.

Day by day, 07:00 to 08:59: the four holiday days were −0.91, −0.97, −0.38 and +0.79.
The lowest ordinary Tuesday to Thursday morning in the comparison was +4.03.

## 3. Supporting checks, not part of the verdict

| 07:00 to 08:59 | comparison | holiday | fall, 95% CI |
|---|---|---|---|
| links within 300 m of a school | +8.01 | −0.27 | +8.29 [+6.41, +10.18] |
| links 300 to 800 m | +10.21 | +1.23 | +8.98 [+6.16, +11.65] |
| links over 800 m | +2.13 | −2.85 | +4.98 [+3.48, +6.45] |
| inbound hops, 0.5 to 10 km out | +11.70 | −1.88 | **+13.58 [+9.75, +17.35]** |
| outbound hops, 0.5 to 10 km out | +2.96 | +1.18 | +1.78 [+1.13, +2.48] |
| near a primary, basic or progimnazija school | +9.22 | −0.67 | +9.90 [+7.67, +12.27] |
| near a gimnazija | +6.95 | +0.07 | +6.88 [+5.11, +8.58] |

- **Inbound carries it.** The inbound morning delay vanished; outbound barely moved.
  This matches [one direction](one-direction-2026-10-02.md), where the inbound gap
  carried 74% of the autumn step.
- **Younger pupils' schools fall more** than gimnazijos, which fits younger children
  being driven.
- **Far links fall too**, by 5 s. The road a bus drives far from a school still carries
  traffic heading to one, so the near/far split understates the school share rather
  than measuring it.

## 4. What this does and does not show

- The holiday morning, −0.37 s, sits below the summer morning measured on dry
  Monday to Thursday days (+2.32). The whole autumn step, and a little more, went away.
- **The evening also fell, by 4.8 s.** Pick-ups, after-school activities and parents
  on leave all go with the holiday, so this is the school-holiday week as a whole, not
  pupils alone (as section 3 of the groundwork warned). The morning fall is still
  2.9 s larger than the evening one [+1.1, +4.6], and midday did not move.
- One holiday week is one event. Its size, near-total, and the clean midday control
  make chance an unlikely explanation, but the autumn and winter holidays later this
  school year would be a free replication.
- The week after the holiday (10 to 13 November) was the slowest of the three
  comparison weeks (+10.2 s). The verdict holds against each week alone.

## Method and files

- `code/h8_holiday_test.py`, run from the repository root, reproduces every number
  here. It reads `analysis/trav-*.csv.xz` for the 16 days, `weather/weather-*.csv`,
  `analysis/h8/school-links.csv`, `analysis/h8/schools-vilnius-2026-10-18.csv` and
  `gtfs/gtfs-20261101.zip`, and needs pandas and numpy.
- Inbound and outbound follow [one direction](one-direction-2026-10-02.md): a hop
  starting 0.5 to 10 km from Cathedral Square, ending more than 100 m closer or further.
- School type is the type of the nearest school with 100 or more pupils.
