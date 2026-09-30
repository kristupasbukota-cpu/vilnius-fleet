# The morning has settled, not grown

> **Updated later on 30 September 2026.** With weather joined to the record, the easing
> this document called suggestive is real once wet mornings are set aside: dry
> Monday-to-Thursday mornings fell from about +11 to about +8 s per hop between the
> second and third week of term, trend -1.06 s per week [-1.86, -0.53]. The
> Wednesday and Thursday swings in section 2 are mostly rain. See
> [`weather-2026-09-30.md`](weather-2026-09-30.md). The text below is unchanged.

30 September 2026. Task #14: is the autumn morning still getting worse?

**Result: no. The morning peak stopped deteriorating after the first school week and
has held at a high level since, with a slight drift down that is not yet
distinguishable from noise.** It is still about 4.6 times the summer morning and
still the worse of the two peaks.

The [18 September rerun](autumn-rerun-2026-09-18.md) found that delay in the 07-08
window went from +1.65 to +8.99 s per stop-to-stop hop when the autumn network
started, and said whether it was still growing "needs another fortnight". This is
that check, run two days early on the eight working days available, 18 to 29
September. Friday 1 October and Thursday 2 October would complete the fortnight; a
one-line update will follow if they change the conclusion.

Same data and the same measure as the rerun: the per-traversal tables
`analysis/trav-*.csv.gz`, mean `lost_s` per traversal, days as the unit. The
reproduction is exact: 18 August +4.37, 11 September +2.53, 17 September +14.13, all
matching the published figures to the hundredth.

---

## 1. Three periods, Monday to Thursday

Fridays are a different kind of day (section 3), and with two or three of them per
period they would move the averages by which week had more. So the comparison uses
Monday to Thursday only, with 1 September excluded as before.

Mean seconds of delay per hop:

| window | summer 18-31 Aug | early autumn 2-17 Sep | late autumn 18-29 Sep | late minus early, 95% CI |
|---|---|---|---|---|
| **morning 07-08** | +1.93 | **+10.72** | **+8.89** | **-1.83 [-3.90, +0.45]** |
| midday 09-15 | +3.71 | +3.21 | +2.15 | -1.05 [-1.95, -0.18] |
| evening 16-18 | +9.28 | +9.37 | +7.22 | -2.15 [-5.36, +1.20] |
| whole day | +3.46 | +4.23 | +3.23 | -0.99 [-1.94, -0.01] |
| days | 8 | 10 | 6 | |

Intervals are a day-level bootstrap, 20,000 resamples.

The morning is not growing. If anything it is lower, but the interval includes zero.
The same day-level design that found a +7.35 s jump on 18 September cannot find a
change here.

**Nothing has returned to summer.** Every late-autumn Monday to Thursday morning, the
lowest at +6.59 on 21 September, is still above every summer working day, the highest
at +4.37 on 18 August. The separation the rerun found is intact.

**The morning is still the worse peak**, +8.89 against +7.22 in the evening.

## 2. The trend, with the weekday held fixed

Monday to Thursday mornings, s per hop:

| | wk 1 (2-3 Sep) | wk 2 (7-10) | wk 3 (14-17) | wk 4 (21-24) | wk 5 (28-29) |
|---|---|---|---|---|---|
| Mon | | +10.2 | +7.5 | +6.6 | +6.9 |
| Tue | | +12.2 | +9.9 | +9.6 | +9.3 |
| Wed | +11.5 | +11.1 | +7.3 | +13.1 | |
| Thu | +10.1 | +13.2 | +14.1 | +7.9 | |

A linear trend across all 16 autumn Monday-to-Thursday mornings, with a separate
level for each weekday: **-0.62 s per hop per week, 95% CI [-1.69, +0.49]**. Flat,
within a band that allows a modest decline.

Two rows are more suggestive than the fit. Mondays have come down steadily, 10.2 to
about 6.7, and Tuesdays from 12.2 to about 9.4. Wednesdays and Thursdays swing by 5 to
6 s from one week to the next with no direction. The largest single mornings of the
autumn are still recent: +13.1 on 23 September.

## 3. Friday holds

The rerun rested its Friday finding on two autumn Fridays and flagged n. There are now
four:

| | 4 Sep | 11 Sep | 18 Sep | 25 Sep |
|---|---|---|---|---|
| Friday morning | +7.21 | +2.53 | +3.28 | +3.89 |

Against a Monday-to-Thursday autumn mean of about +10. Three of the four Fridays sit
below every autumn Monday-to-Thursday morning. The two new ones point the same way as
the first two. This is firmer than it was, and still only six Fridays across both
networks.

## 4. The rest of the day eased a little

Midday fell by about 1 s per hop and the whole day by about 1 s, both with intervals
that just exclude zero. The evening fell by 2 s but its interval is wide. The service
run did not change: morning traversals stayed at about 24,500 a day throughout.

This is the kind of small, borderline movement that weather or one unusual week could
produce, and four comparisons with bootstrap intervals on six days are not strong
evidence. It is recorded, not claimed.

---

## What this means

**Established.** The autumn morning deterioration was a step, not a slope. It arrived
on 2 September and has not grown since. It has not gone away either.

**Suggestive, not established.** A slow easing, about half a second per hop per week,
most visible on Mondays and Tuesdays. That is what people and drivers settling into
the new term would look like, and also what later sunrises and drier weather could
look like. Nothing here separates them.

**Unchanged.** The framing from 18 September holds: the evening failure is a property
of specific roads, the morning failure is a property of demand, and the morning is
currently the larger of the two.

## Next

- Add 1 and 2 October when they are processed and note any change here.
- Weather (#12) is now the most useful confounder to remove, since both the easing and
  the Wednesday-Thursday swings are the size weather could produce.
- The pupils' autumn holiday, 2 to 8 November 2026 per the Ministry of Education's
  published calendar, is a natural experiment: if the morning falls back towards
  summer that week, as it did on 1 September, the school-run explanation gets much
  stronger. A task for the second week of November.

---

## Method, for reproduction

```python
import pandas as pd, glob, os
for p in sorted(glob.glob("analysis/trav-*.csv.gz")):
    df = pd.read_csv(p, usecols=["hour_local", "lost_s"])
    h = df.hour_local
    morning = df.lost_s[h.isin([7, 8])].mean()      # 07-08 window
    midday  = df.lost_s[h.between(9, 15)].mean()
    evening = df.lost_s[h.between(16, 18)].mean()
    whole   = df.lost_s.mean()
```

Working days only, 1 September excluded, Monday to Thursday for the period
comparison. Confidence intervals: bootstrap over days, 20,000 resamples, seed 1. The
trend: least squares of the daily morning mean on weeks since 2 September plus one
indicator per weekday, with a bootstrap over days for the interval.
