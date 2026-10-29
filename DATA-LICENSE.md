# Data and documents

The [MIT licence](LICENSE) covers the code in `code/` and `.github/`.

**Documents.** The writing in `docs/` and `STATE-OF-PLAY.md` is licensed under the
[Creative Commons Attribution 4.0 International licence (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
Quote and republish it freely. Please credit
"vilnius-fleet, github.com/kristupasbukota-cpu/vilnius-fleet".

**Data. All rights reserved.** The derived tables in `analysis/`, `segments/` and
`summaries/`, and the collection they are built from, are
© 2026 Kristupas Bukota, all rights reserved, from 21 October 2026. This covers
copyright and the database right in the collection. They are published so that the
findings can be checked: you may download them and rerun the scripts in `code/` to
verify a published result. Any other use, including copying them into another
dataset, publishing them, or using them commercially, needs written permission.
To ask, open an issue on this repository.
Because the repository is public, GitHub's terms of service also let any GitHub user
view and fork it on GitHub; that does not grant any other right to use the data.

Copies of these tables taken between 21 October 2026 11:31 UTC and the time of this
change were offered under CC BY 4.0, and those copies keep that licence.

Not covered by the reservation, because they contain other people's data under
share-alike licences: `report/` (it includes daily rain totals from LHMT) is under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), and the basemaps
`analysis/basemap-*.json` (from OpenStreetMap) are under the
[Open Database Licence (ODbL)](https://opendatacommons.org/licenses/odbl/),
© OpenStreetMap contributors. The third-party files listed below also keep their own
terms.

The raw snapshot archive is not published. The one exception is `samples/`, which holds a
single raw snapshot as an example of the feed's format (listed below).

Files that come from other people keep their own terms:

| folder | source | terms |
|---|---|---|
| `weather/` | Lietuvos hidrometeorologijos tarnyba (LHMT), api.meteo.lt, station Vilniaus AMS | CC BY-SA 4.0 |
| `gtfs/` | Vilnius city timetable, stops.lt | the city's open-data terms |
| `samples/` | one snapshot of the city's live vehicle feed (stops.lt), 20 August 2026 16:10 UTC | the city's open-data terms |
| `analysis/h8/schools-vilnius-2026-10-18.csv` | Lithuanian Ministry of Education open data | the Ministry's open-data terms |
| `analysis/basemap-*.json` | OpenStreetMap contributors | ODbL |
| `analysis/h1/bus-lanes-2026-10-18.json` | Vilniaus planas, layer "Viešojo transporto A juostos (Esamos)" | Vilniaus planas terms |

The derived tables are built from the city's live vehicle feed (stops.lt). They hold
vehicle positions and timetable deviations only, nothing about passengers or drivers.
