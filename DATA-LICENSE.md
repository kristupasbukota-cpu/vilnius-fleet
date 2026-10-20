# Data and documents

The [MIT licence](LICENSE) covers the code in `code/` and `.github/`.

Everything else this project wrote, the documents in `docs/`, `STATE-OF-PLAY.md`
and the derived tables in `analysis/`, `segments/`, `summaries/` and `report/`, is
licensed under the
[Creative Commons Attribution 4.0 International licence (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
Please credit "vilnius-fleet, github.com/kristupasbukota-cpu/vilnius-fleet".

Files that come from other people keep their own terms:

| folder | source | terms |
|---|---|---|
| `weather/` | Lietuvos hidrometeorologijos tarnyba (LHMT), api.meteo.lt, station Vilniaus AMS | CC BY-SA 4.0 |
| `gtfs/` | Vilnius city timetable, stops.lt | the city's open-data terms |
| `analysis/h8/schools-vilnius-2026-10-18.csv` | Lithuanian Ministry of Education open data | the Ministry's open-data terms |
| `analysis/h1/bus-lanes-2026-10-18.json` | Vilniaus planas, layer "Viešojo transporto A juostos (Esamos)" | Vilniaus planas terms |

The derived tables are built from the city's live vehicle feed (stops.lt). They hold
vehicle positions and timetable deviations only, nothing about passengers or drivers.
