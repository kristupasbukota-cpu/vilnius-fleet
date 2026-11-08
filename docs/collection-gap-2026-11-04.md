# Collection gap, Wednesday 4 November 2026 evening

8 November 2026. On 4 November from about 19:15 to 20:45 UTC (21:15 to 22:45 Vilnius time) the record is thin or unusable. The cause was the city's live feed, not the collector.

- 19:19 to 20:16 UTC: the feed refreshed only every 30 to 60 s instead of every 10 s, so 1 to 2 snapshots a minute were kept instead of 6 (the rest were exact repeats). It also lost most trip IDs: 89% of vehicles carried one at 19:00, 30% at 19:50. Vehicles kept positions and route numbers, but hops without a trip ID cannot be matched to the timetable.
- 20:19 to 20:40 UTC: the feed was empty (header only), apart from one normal copy at 20:28.
- From 20:43 UTC: normal again (483 vehicles, 94% with trip IDs).
- Earlier the same day, 01:57 to 02:15 UTC, the city's server answered with HTTP 522 errors; almost no buses run then.

The collector logged ok every minute, with no memory or network errors on the server.

Effect: hops recorded for trips starting 21:10 to 22:10 Vilnius time fell from about 1,600 per 10 minutes to almost none. Evening and daily totals for 4 November read low. Leave out or flag 19:15 to 20:45 UTC on 4 November in any analysis of that evening. The H8 holiday test is not affected: its latest measured hour ends at 18:59 Vilnius time.
