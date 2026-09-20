# Findings

Every result this project has produced, dated, including the ones that were later
overturned. Newest first.

| date | document | what it says |
|---|---|---|
| 20 Sep 2026 | [`vilkpedes-ziedas-defect-2026-09-20.md`](vilkpedes-ziedas-defect-2026-09-20.md) | The early-departure outlier is one stop, not two routes. Corrected network figure 2.09%. |
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
  trip's arrival. The real answer is 2.09%.
- The routes 56 and 73 defect. Real, but it was never about those routes. It is
  one stop, and it also affects two other routes nobody had looked at.
- Publishing the timetables as text to save space. Benchmarked at a 72% saving in
  an environment that did not share the memory constraint that governs the box.
  It added 120 MB.

See [`PUBLISHING.md`](PUBLISHING.md) for how documents get here.
