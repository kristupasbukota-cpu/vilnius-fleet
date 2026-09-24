# Early departure, measured at the right bay: 1.85%

24 September 2026. Task #24, the fix promised on 20 September. Same four August days,
same 37,870 departures, re-run on the box with a corrected `departure.py`.

**Result.** Measured so that neither of two timetable artefacts can count, **1.85% of
departures leave more than a minute early** across all four days, and **1.83% on
working days**. That replaces 2.5% (29 August) and 2.09% (20 September). It is no
longer an estimate or an exclusion: every trip is kept and one rule applies to all
of them.

The larger finding is what the correction did to the route ranking. **Day-to-day
agreement between routes falls from r = 0.92 to 0.54.** Much of what looked like a
stable list of routes that leave early was one timetable defect repeating itself
reliably.

---

## 1. What changed in the measure

The old measure read the live deviation at the scheduled departure from the trip's
first stop in GTFS. At terminal loops, GTFS often lists two bays of the same
terminus as the first and second stop, up to 150 m and up to 180 s apart. Which
bay the bus actually stands at, and which one the operator's clock runs from,
varies by loop. That produces two opposite errors:

| | what happens | what the old or naive measure sees |
|---|---|---|
| **standing at bay 2** | the bus already sits where the timetable puts it a minute later | early at bay 1's time, though it has not moved. Vilkpėdės žiedas, 52% "early". |
| **padded first hop** | the bus leaves bay 1 on time and covers 100 m in 20 s | fine at bay 1, but early at bay 2's time. Šumsko kryptis goes from 0.6% to 4.5% if you move the measurement to bay 2. |

Moving the measurement point fixes the first error and creates the second. So the
measure now reads the deviation at **both** points and counts a departure as early
only if it is early at both:

- **bay 1:** the scheduled departure from the first stop, as before
- **timing bay:** the last of the leading stops within 150 m of the first one. For
  94% of observed departures that is the first stop itself and nothing changes.

A bus that really does leave early is still caught, because the deviation runs
continuously and a bus that pulled out early is still ahead of schedule a minute
later. A bus that is merely parked at the second bay, or has merely run ahead on a
padded first hop, is not.

## 2. The check that it changed nothing it should not have

The script keeps every original column and adds five new ones, so the old result
can be recomputed from the new files. Against the files published on 29 August:

- **37,870 of 37,870 rows present, every original column identical.** The
  regression check is exact.
- **35,453 trips have no second bay, and their new value equals the old one
  exactly.**
- 2,417 trips are timed from a later bay. Only 4 have no reading within 90 s of it.

## 3. The numbers

| | network | Vilkpėdės žiedas | the other loops | ordinary trips |
|---|---|---|---|---|
| old: first bay only | 2.47% | 52.4% | 6.2% | 1.84% |
| second bay only | 1.98% | 4.2% | 4.1% | 1.84% |
| **both bays must read early** | **1.85%** | **3.4%** | **1.9%** | **1.84%** |

The last row is the test that matters. Once both artefacts are ruled out, trips
that start at terminal loops (1.9%) behave like every other trip (1.84%). No class
of stop stands out any more, which is what a measure of driver behaviour rather
than of timetable layout should show.

Per day:

| day | departures | early > 60 s | early > 120 s |
|---|---|---|---|
| Sat 22 Aug | 7,703 | 1.93% | 0.48% |
| Mon 24 Aug | 10,088 | 2.05% | 0.41% |
| Tue 25 Aug | 10,117 | 1.66% | 0.27% |
| Wed 26 Aug | 9,962 | 1.78% | 0.31% |
| **working days pooled** | 30,167 | **1.83%** | **0.33%** |

About one departure in fifty-five leaves more than a minute early, and one in three
hundred more than two minutes early.

**Antakalnio žiedas was the same defect.** It read 13.3% early under the old
measure and was listed on 20 September as a milder member of the class. At its
timing bay, 91 m and 180 s after the first, it reads 2.9%. The first bay there
is also a standing bay.

**Pašilaičių žiedas is not.** 16 of its 245 departures are early at both bays. If
anything at the loops is genuine early departure, it is there.

**The padded-hop cases are recognisable.** At Šumsko kryptis, Povilo Lukšio st.
and Titnago žiedas, the departures that read early only at the second bay read a
median of exactly 0 at the first, which is the parked-before-departure value, and about
-70 s at the second. That is a bus leaving on time and then running ahead on a
generous first hop: early running, not early departure.

## 4. What it did to the route ranking

Working days, routes with at least 150 departures:

| route | departures | early > 60 s |
|---|---|---|
| **61** | 271 | **11.8%** |
| 16 | 735 | 5.9% |
| 29 | 249 | 4.4% |
| 5G | 700 | 3.7% |
| 24 | 299 | 3.7% |
| network median | | **1.4%** |

Routes 56 and 73, first and second on 29 August at 30.8% and 25.8%, are gone from
the top of the list.

**Day-to-day agreement of route early share, 25 against 26 August:**

| routes with at least ... departures each day | old measure | new measure |
|---|---|---|
| 1 | 0.86 | 0.37 |
| 50 | 0.91 | 0.43 |
| 75 | **0.92** | **0.54** |

The 0.92 reproduces the figure published on 29 August exactly. That note had warned
that "a systematic defect reproduces perfectly, so high reproducibility is not by
itself evidence that something is real." This quantifies how much of the 0.92 was
the defect. With it removed, most routes' early share on one day predicts the next
day's only weakly. Outside route 61, four days are not enough to rank routes on
early departure, and the ranking should not be quoted as if they were.

**Route 61 direction 1 survives every version of the measure**, at 19.2% of 167
departures. It has no second bay and its first hop is 398 m, so neither artefact
applies. It is now the clearest open question in this thread.

## 5. One residual

At Vilkpėdės žiedas, the deviation at the timing bay has a median of -22 s, not 0,
and only 15% of readings are exactly zero. The operator's clock there may not line
up exactly with either published bay. Requiring both bays makes this irrelevant at
the 60 s threshold: 10 of 290 departures are early at both. It would matter to
anyone measuring at a finer threshold.

---

## Corrections this makes

- **20 September:** the network figure 2.09% becomes **1.85%**. Its description of
  the mechanism also said the bus was "a minute short of where the operator's
  schedule expects it". That is backwards: the bus is already standing at the bay
  the timetable reaches a minute later, so it reads a minute *ahead*. Corrected there.
- **29 August:** 2.5% becomes **1.83%** on working days. The route table and the
  r = 0.92 both need the caveat in section 4.

## Files

`code/departure.py`, now with `--cluster` (default 150 m) and `--gtfs-until`.
The previous version is kept on the box as `departure.py.bak-20260924`. Outputs in
`analysis/dep-2026-08-22|24|25|26.csv.gz`, replaced in place: every original
column is unchanged and five are added (`timing_seq`, `timing_stop`,
`sched_timing_s`, `timing_offset_s`, `dev_at_timing`). The both-bays value is
`max(dev_at_departure, dev_at_timing)` where the two differ, else
`dev_at_departure`. Run with `--gtfs-until 20260829`, the timetable versions the
original run could see.
