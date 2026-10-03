# Findings

Every result this project has produced, dated, including the ones that were later
overturned. Newest first.

| date | document | what it says |
|---|---|---|
| 2 Oct 2026 | [`repo-growth-plan-2026-10-02.md`](repo-growth-plan-2026-10-02.md) | Proposal. The repository passes 1 GB around January; three options to push that to mid-2027. Decisions needed. |
| 2 Oct 2026 | [`districts-2026-10-02.md`](districts-2026-10-02.md) | Four of the five districts promised more frequent routes got more than the city; Baltupiai did not. Lazdynėliai's mornings got much slower. |
| 2 Oct 2026 | [`bus-lanes-2026-10-02.md`](bus-lanes-2026-10-02.md) | The bus lanes carry a fifth of bus traffic but sit alongside only 5 of the 20 worst links. |
| 2 Oct 2026 | [`excess-wait-2026-10-02.md`](excess-wait-2026-10-02.md) | Passengers wait 1.2 min longer than the timetable implies on express routes, 0.9 on trunk routes. |
| 2 Oct 2026 | [`roads-not-vehicles-2026-10-02.md`](roads-not-vehicles-2026-10-02.md) | Lateness belongs to roads: 22.4 s per hop between links, 1.5 s between vehicles, 2.1 s between routes. |
| 2 Oct 2026 | [`one-direction-2026-10-02.md`](one-direction-2026-10-02.md) | The autumn morning problem is inbound: +17.0 s per hop towards the centre, +2.1 s away. |
| 2 Oct 2026 | [`route-61-early-2026-10-02.md`](route-61-early-2026-10-02.md) | Route 61's early departures are two vehicles, on the same trips a third never leaves early on. Updated 3 October: on the autumn network still 24%, but by vehicle-day, not two vehicles. |
| 1 Oct 2026 | [`summer-time-fix-2026-10-01.md`](summer-time-fix-2026-10-01.md) | Operations. Every script now follows Vilnius local time through summer time; from 25 Oct the nightly tables would otherwise have come out empty. Published outputs unchanged. |
| 1 Oct 2026 | [`weather-audit-2026-10-01.md`](weather-audit-2026-10-01.md) | Audit. The weather record checks out against Vilnius airport; two statements corrected; the day-level wet-morning figure is instrument-dependent. Summer time ends 25 Oct and the hour labels need fixing first. |
| 30 Sep 2026 | [`weather-2026-09-30.md`](weather-2026-09-30.md) | Weather joined to the record. Rain adds about a third to delay; it does not explain the autumn jump, and it was hiding a real easing of the morning. |
| 30 Sep 2026 | [`morning-settled-2026-09-30.md`](morning-settled-2026-09-30.md) | The autumn morning was a step, not a slope. Flat since the first school week at about +9 s per hop, still 4.6 times summer. Updated 3 October: on dry mornings a second step down in mid-September to about +8, flat since. |
| 30 Sep 2026 | [`report-comparison-fix-2026-09-30.md`](report-comparison-fix-2026-09-30.md) | Correction. The nightly report compared every day against mid-August; corrected, its day-to-day agreement is 0.90, not 0.50. |
| 29 Sep 2026 | [`maintenance-2026-09-29.md`](maintenance-2026-09-29.md) | Operations. departure.py timetable loading, a day-by-day chart in the nightly report, a panel that could blank the page. |
| 26 Sep 2026 | [`nightly-outage-2026-09-26.md`](nightly-outage-2026-09-26.md) | Operations. Three nights without a publish, why the watchdog missed it, and the fix. |
| 24 Sep 2026 | [`departure-timing-point-2026-09-24.md`](departure-timing-point-2026-09-24.md) | Early departure measured at the right bay: 1.85%. Much of the route ranking was the defect. |
| 20 Sep 2026 | [`vilkpedes-ziedas-defect-2026-09-20.md`](vilkpedes-ziedas-defect-2026-09-20.md) | The early-departure outlier is one stop, not two routes. Corrected network figure 2.09%, since refined to 1.85%. |
| 18 Sep 2026 | [`frequency-promise-2026-09-18.md`](frequency-promise-2026-09-18.md) | The city's frequency promise holds. What the average hides does not. |
| 18 Sep 2026 | [`autumn-rerun-2026-09-18.md`](autumn-rerun-2026-09-18.md) | The morning peak is now worse than the evening. 91% of the new delay is in two hours. |
| 9 Sep 2026 | [`state-of-play-2026-09-09.md`](state-of-play-2026-09-09.md) | Three and a half weeks in. The Mac is gone, the city changed the network, and a storage experiment failed. |
| 29 Aug 2026 | [`departure-repair-2026-08-29.md`](departure-repair-2026-08-29.md) | Early departure measured properly: 2.5%, not 13.5%. |
| 27 Aug 2026 | [`oracle-risk-and-mac-retirement-2026-08-27.md`](oracle-risk-and-mac-retirement-2026-08-27.md) | What actually threatens the box, and it is not the outage. |
| 24 Aug 2026 | [`verification-2026-08-24-of-the-20-august-findings.md`](verification-2026-08-24-of-the-20-august-findings.md) | Independent re-run. Compounding confirmed and strengthened. The departure claim does not survive. |
| 20 Aug 2026 | [`findings-2026-08-20-compounding-and-early-running.md`](findings-2026-08-20-compounding-and-early-running.md) | The first two real results. One held, one did not. |
| 18 Aug 2026 | [`state-of-play-2026-08-18.md`](state-of-play-2026-08-18.md) | How the instrument was built and why. Still the best account of the design. |

## Reading order

If you want the current picture, read `../STATE-OF-PLAY.md` and stop there.

If you want to know whether to believe it, read the 18 August document for the
design, then 20 August for the first results, then 24 August and 29 August for
what happened when those results were attacked. Two of the three original
headlines changed under examination, which is the point.

## One thing worth knowing about this project

Findings here are corrected in public. A document that carried a wrong number
keeps the wrong number, with a banner saying what replaced it and why. Three
examples, all of them mistakes caught after publication:

- 13.5% of buses leave early. They do not. That figure was reading the previous
  trip's arrival. The real answer is 1.85%, reached in three steps.
- The routes 56 and 73 defect. Real, but it was never about those routes. It is
  one stop, and it also affects two other routes nobody had looked at.
- Publishing the timetables as text to save space. Benchmarked at a 72% saving in
  an environment that did not share the memory constraint that governs the box.
  It added 120 MB.

See [`PUBLISHING.md`](PUBLISHING.md) for how documents get here.
