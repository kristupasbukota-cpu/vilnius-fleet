# The morning peak is now the problem

18 September 2026. Task #4: every finding re-asked against the autumn network.

**Result: the oldest claim in this project is no longer true.** Since 17 August the
headline has been that Vilnius runs late in the afternoon, not the morning, and that
whatever fails at 17:00 is not volume. That was an accurate description of the summer
network. On the autumn network the morning is worse than the evening, and the evening
is unchanged.

Ten summer working days, 18 to 31 August, against thirteen autumn working days,
1 to 17 September. 1.72 million traversals against 2.61 million. Days are the unit of
analysis throughout, so the confidence intervals reflect day-to-day variation rather
than a spuriously large row count.

---

## 1. What changed on the street

The city put about 17% more service on unchanged roads.

| per working day | summer | autumn | |
|---|---|---|---|
| traversals | 172,483 | 200,906 | +16.5% |
| vehicle-trips | 10,398 | 11,843 | +13.9% |

## 2. Where the extra delay went

Vehicle-hours of delay created per working day:

| window | summer | autumn | change |
|---|---|---|---|
| **morning 07-08** | **9.5** | **60.7** | **+51.3** |
| midday 09-15 | 66.8 | 71.2 | +4.4 |
| evening 16-18 | 71.8 | 78.2 | +6.4 |
| whole day | 163.6 | 219.8 | +56.2 |

**Ninety-one percent of the additional delay the autumn network creates falls in two
morning hours.** Midday and evening absorbed the extra service almost perfectly.

## 3. The same thing per crossing, with intervals

Mean seconds of delay a bus picks up on one stop-to-stop hop:

| window | summer | autumn | difference | 95% CI |
|---|---|---|---|---|
| morning 07-08 | +1.65 | **+8.99** | **+7.35** | **[+5.02, +9.67]** |
| midday 09-15 | +3.94 | +3.56 | -0.38 | [-1.38, +0.62] |
| evening 16-18 | +8.38 | +7.86 | -0.52 | [-3.55, +2.50] |
| whole day | +3.46 | +3.97 | +0.51 | [-0.36, +1.38] |

The morning is a 5.4-fold increase and the interval is nowhere near zero. Everything
else is flat. Note the last row: **overall punctuality did not measurably change**. The
network absorbed 17% more service without getting worse on average. The delay moved
rather than grew.

And the comparison that matters: the autumn morning peak, at +8.99 s per hop, is now
**worse than the autumn evening peak** at +7.86.

## 4. The separation is almost total

Morning 07-08, every day measured:

| summer | | autumn | |
|---|---|---|---|
| 18 Aug | +4.37 | 1 Sep | **-0.00** |
| 19 Aug | +1.79 | 2 Sep | +11.52 |
| 20 Aug | +1.80 | 3 Sep | +10.10 |
| 21 Aug | +0.39 | 4 Sep | +7.21 |
| 24 Aug | +1.11 | 7 Sep | +10.16 |
| 25 Aug | +2.04 | 8 Sep | +12.23 |
| 26 Aug | +1.80 | 9 Sep | +11.14 |
| 27 Aug | +1.74 | 10 Sep | +13.16 |
| 28 Aug | +0.64 | 11 Sep | +2.53 |
| 31 Aug | +0.77 | 14 Sep | +7.54 |
| | | 15 Sep | +9.93 |
| | | 16 Sep | +7.28 |
| | | 17 Sep | +14.13 |

Eleven of thirteen autumn days exceed every one of the ten summer days. This is not a
shift in an average, it is two separated populations.

**The two exceptions are informative.** 1 September, the day the extra buses appeared,
reads exactly zero. In Lithuania that is Rugsėjo 1-oji, a ceremonial day with no normal
timetable of lessons, so there is no school run. The collapse begins on **2 September,
the first ordinary school morning**.

The other exception, 11 September, is a **Friday**, and Fridays turn out to be a
different kind of day. See section 7, added after this was first written.

## 7. Friday is a flatter day, in both networks

Mean seconds per hop, by weekday, with 1 September excluded:

| | summer morning | autumn morning | summer evening | autumn evening |
|---|---|---|---|---|
| Mon | +0.94 | +8.85 | +8.85 | +5.92 |
| Tue | +3.21 | +11.08 | +10.46 | +9.23 |
| Wed | +1.80 | +9.98 | +10.71 | +11.48 |
| Thu | +1.77 | +12.46 | +7.11 | +9.65 |
| **Fri** | **+0.51** | **+4.87** | **+4.79** | **+2.51** |

Friday against the rest of the week:

| | summer | autumn |
|---|---|---|
| morning | 73% lighter | 55% lighter |
| evening | 48% lighter | 73% lighter |
| **whole day** | **10% lighter** | **22% lighter** |

**The peaks collapse but the day does not.** Friday loses 151 vehicle-hours against 167
on other summer days, and 186 against 238 in autumn. The total is modestly lower while
the peaks are halved or better. That is the signature of a day where people travel at
more spread-out times rather than fewer people travelling: the demand is still there,
it is just not all arriving at 07:30 and 17:00.

Every autumn weekday is worse than its summer counterpart in the morning, Friday
included, so the main result of this document survives the weekday breakdown intact.

**The caveat is n.** There are two Fridays in each period, four in total. What makes
this credible is that the direction is identical across both periods and both peaks,
eight comparisons pointing the same way. What makes it provisional is that four days
is four days. Each passing week adds one, so this will firm up or fall apart quickly.

And Friday does not fully explain 11 September. At +2.53 it is low even for an autumn
Friday, against +7.21 on 4 September. Something else is in there too.

## 5. It is the whole network, not a corridor

The evening problem has always been geographic: four of the six worst stretches sit
within 900 m of Žaliasis tiltas. The morning problem is not.

Morning 07-08, by distance from the cathedral:

| band | summer | autumn | change | share of the extra delay |
|---|---|---|---|---|
| 0-2 km | +4.98 | +14.37 | +9.39 | 27% |
| 2-4 km | +3.62 | +11.58 | +7.96 | 25% |
| 4-6 km | -0.12 | +7.16 | +7.28 | 30% |
| 6-9 km | -0.93 | +4.76 | +5.69 | 13% |
| 9+ km | +0.52 | +4.68 | +4.16 | 5% |

Every band got worse by a broadly similar amount, and no band carries the increase.
The outer city is the starkest change in kind: beyond 4 km, a summer morning cost a bus
**nothing at all**, and now costs 5 to 7 seconds per hop.

I checked the ten individual stretches that deteriorated most and they looked
suburban, which suggested a peripheral story. The distance bands say that was the
extreme tail misleading me, not the pattern. The pattern is: everywhere.

## 6. What did not change

| | summer | autumn |
|---|---|---|
| trips ending more than 60 s early | 11.7% | 12.0% |
| trips ending more than 60 s late | 46.2% | 48.2% |
| median deviation at trip end | +48.8 s | +54.9 s |

None of these differences survive a day-level test. The early-running result from
August holds on the autumn network unchanged.

---

## What this means, and what it does not

**Established.** The morning peak deteriorated sharply and the evening peak did not.
The total delay the network creates rose 34%, and essentially all of it is in two
morning hours. Overall punctuality is statistically unchanged.

**Not established: the cause.** Summer and September differ in more than the school
year. There are more cars on the road, more people travelling at a fixed hour rather
than a flexible one, different weather and different daylight. The bus fleet grew 17%,
but so, presumably, did the traffic it sits in. This design cannot separate those, and
the 1 September result is suggestive of the school run specifically rather than of the
extra buses, since the buses were already running that day and the mornings were clean.

**What it changes.** The standing explanation of the evening collapse was that it is
not volume, since the morning ran the same fleet and arrived fine. That argument rested
on a summer morning. It is now weaker, because the same city with a normal morning
demand loses six times more time before 09:00 than it did a month ago, while the
evening sits exactly where it was.

The honest new framing: **the evening failure is a property of specific roads, and the
morning failure is a property of demand.** They are different problems and the project
has now measured both.

## Next

The obvious follow-up is weather, which would remove one of the confounders above and
might explain 11 September. The other is whether the morning deterioration is still
growing or has settled, which needs another fortnight.
