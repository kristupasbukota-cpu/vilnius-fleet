# The routes 56 and 73 early-departure defect is not a route defect. It is one stop.

20 September 2026. Task #8, closing the loose end left by the 29 August departure
repair. Four days of per-trip departures (37,870 rows), matched against the GTFS
version archived on 24 August.

> **Refined 24 September.** The 2.09% below was reached by excluding the 290 trips
> that start at stop 19255. Measured instead at both bays of every terminal loop,
> keeping every trip, the network figure is **1.85%** (1.83% on working days).
> Antakalnio žiedas, listed below as a milder member of the class, turned out to
> be the same defect. The description of the mechanism in section 1 also had the
> direction backwards and is corrected in place. See
> `departure-timing-point-2026-09-24.md`.

**Result.** The defect is not a property of routes 56 and 73 at all. It belongs to
a single stop id, **19255 "Vilkpėdės žiedas"**, and it affects every trip that
begins there regardless of route. 290 departures start at that stop across the
four days. **52.4% of them read as leaving more than a minute early. The rest of
the network reads 1.8%.** Sibling trips on the very same routes that start
somewhere else read 0.0%.

The network early-departure figure moves from **2.47% to 2.09%** once those 290
trips are excluded, which confirms the "about 2.1%" estimated by judgement on
29 August and now lets the exclusion be made by rule instead.

---

## 1. The mechanism

Vilkpėdės žiedas is a terminal loop with two bays, published in GTFS as two
separate stops **49 m apart with the same name**:

| stop_id | name | role in the trip |
|---|---|---|
| 19255 | Vilkpėdės žiedas | sequence 1, where the bus stands |
| 8311 | Vilkpėdės žiedas | sequence 2, 60 s later |

A representative route 73 trip reads: arrive 19255 at 05:58, depart 06:07 after a
nine minute layover, then 8311 at 06:08. Route 56: depart 19255 at 05:53, 8311 at
05:54. In both cases GTFS puts exactly 60 s between the two bays.

`departure.py` samples the live deviation at the scheduled departure from the
trip's **first** stop_time. For these trips that is the standing bay. The
operator's own clock evidently runs from the second one, so at the moment we look
the bus is already standing at the bay the timetable only reaches a minute later,
and the feed reports it as a minute early. *(Corrected 24 September. This first
said the bus was "a minute short of where the operator's schedule expects it",
which is the wrong direction: short would read late, not early.)*

The arithmetic matches. Median deviation on those 290 trips is **-62 s**, against
a published 60 s gap. The spread below that, down to -108 s, tracks how far the
nearest available reading sits from the scheduled moment: the correlation between
the measured deviation and `nearest_offset_s − 60` is **+0.75**.

## 2. It is the stop, not the route

Splitting each affected route-direction by which stop its trips actually start at:

| route, direction | trips starting at 19255 | early there | trips starting elsewhere | early there |
|---|---|---|---|---|
| 56 dir 1 | 127 | **53.5%** | 17 | 0.0% |
| 73 dir 1 | 141 | **48.9%** | 20 | 0.0% |
| 13 dir 1 | 14 | **57.1%** | 63 | 4.8% |
| 29 dir 0 | 8 | **87.5%** | 151 | 6.6% |

Routes 13 and 29 were the next two names on the 29 August ranking after 56, 73 and
61, and nobody had asked why. They are the same defect in smaller doses: only a
minority of their trips begin at that bay. Within a single route and direction the
split is close to total, which is about as clean as a natural experiment gets here.

## 3. The wider class, and why the layout alone is not enough

Scanning the whole timetable for the signature, a first hop under 120 m with at
least 60 s allowed for it, finds 830 of 18,496 trips, clustered at eight terminal
loops. Over the four observed days:

| first stop | departures | early >60 s |
|---|---|---|
| 19255 Vilkpėdės žiedas | 290 | **52.4%** |
| 5483 Antakalnio žiedas | 487 | 13.3% |
| 8275 Pašilaičių žiedas | 245 | 13.1% |
| 18504 Antavilių sodai | 120 | 6.7% |
| 8441 Skalvių žiedas | 46 | 6.5% |
| 6356 Lukiškės | 176 | 6.2% |
| 7716 Šumsko kryptis | 155 | 0.6% |
| 5827 Ateities st. | 189 | 0.5% |
| everything else | 36,069 | **1.8%** |

The class as a whole reads 15.9% against 1.8%, so the layout matters. But it is
necessary, not sufficient: Ateities st. and Šumsko kryptis have the same two-bay
structure and behave normally. What separates them is presumably which bay the
operator treats as the timing point, which we cannot read directly. Vilkpėdės
žiedas is an outlier even inside its own class, by a factor of four.

## 4. One case this does not explain

Route 61 direction 1 is now the worst remaining, at **20.5%** early over 156 trips.
It does not fit. Its first hop is 7874 Kuprioniškės to 9585 Vilties st., **398 m
in 60 s**, so the two stops are genuinely different places. 24 km/h from a
standstill is tight but not impossible. This is either a too-short first hop in the
timetable or something real, and it stays open rather than being folded into the
finding above.

## 5. What to change

**In the measure.** `departure.py` should take the scheduled departure from the
first stop_time whose stop is more than about 150 m from the trip's starting bay,
rather than from sequence 1. That fixes all eight loops by rule and needs no
route list. Until that is done, excluding trips whose first stop is 19255 is a
one-line filter and is defensible on the evidence above.

**In the published figure.** The corrected network early-departure rate over the
four days is **2.09%**, or about one trip in forty-eight. The 29 August note's
2.1% was right; it is now measured rather than estimated.

**In how the ranking is read.** The 29 August note warned that a systematic defect
reproduces perfectly and that high day-to-day agreement is therefore not evidence
of something real. That warning has now cashed out twice: r = 0.92 across days was
produced in part by a stop that does not move.

## Sources

`analysis/dep-2026-08-22|24|25|26.csv.gz` and `gtfs/gtfs-20260824.zip` in
`kristupasbukota-cpu/vilnius-fleet`. Nothing on the box or the Mac was needed.
