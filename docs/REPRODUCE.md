# Rerunning a finding

Which script rebuilds which document, and what it reads. Run every command from the
repository root after:

```bash
python3 -m pip install -r requirements.txt
python3 code/gtfs_rebuild.py      # once: rebuilds every timetable version into gtfs-full/
```

Most scripts read `gtfs/gtfs-20261001.zip`, which is stored whole. The two that need
other versions (`even_spacing_ends.py`, `terminal_stand.py`) read them from `gtfs-full/`.

| finding | script and command | reads | notes |
|---|---|---|---|
| [Rain and delay](weather-2026-09-30.md) | `python3 code/weather_effect.py` | `analysis/trav-*`, `weather/` | a few minutes, mostly the bootstraps |
| [Weather audit](weather-audit-2026-10-01.md) | `python3 code/weather_audit.py` | `analysis/trav-*`, `weather/` | also downloads Vilnius airport METAR reports from mesonet.agron.iastate.edu |
| [H5, even spacing](even-spacing-2026-10-04.md), sections 1 and 3 | `python3 code/even_spacing_ends.py` | `analysis/dep-*`, `analysis/blocks-*`, `gtfs/` | |
| [H5, even spacing](even-spacing-2026-10-04.md), section 2 | `python3 code/even_spacing_points.py` | `analysis/spacing-*` | |
| [H6, terminal stand](terminal-stand-2026-10-04.md) | `python3 code/terminal_stand.py` | `analysis/dep-*`, `analysis/blocks-*`, `gtfs/` | |
| [Lines 118 and 32](lines-118-32-2026-10-04.md) | `python3 code/lines_118_32.py` | `analysis/trav-*`, `analysis/blocks-*`, `analysis/spacing-*` | |
| [H7, spare time](spare-time-2026-10-06.md) | `python3 code/spare_time.py` | `analysis/trav-*`, `gtfs/gtfs-20261001.zip` | prints every table in the document |
| [H1 and H9, bus lanes](bus-lanes-matched-2026-10-18.md) | `python3 code/bus_lanes_test.py analysis/h1/bus-lanes-2026-10-18.json OUT` then `python3 code/bus_lanes_checks.py OUT/lane-links.csv` | `analysis/trav-*`, `gtfs/gtfs-20261001.zip`, `weather/`, the lane map | `OUT` is any empty folder |
| [H8, school run plan](h8-groundwork-2026-10-18.md) | `python3 code/school_links.py analysis/h8/schools-vilnius-2026-10-18.csv OUT` | `analysis/trav-*`, `gtfs/gtfs-20261001.zip`, the school list | baseline only; the test runs after the holiday |

## Tables built on the server

These scripts run on the server every night against the raw snapshots, which are not in
the repository. Their outputs are what the scripts above read.

| output | script |
|---|---|
| `analysis/trav-*`, `analysis/blocks-*` | `code/export.py`, using `code/blocks.py` and `code/segments.py` |
| `analysis/dep-*` | `code/departure.py` |
| `analysis/spacing-*` | `code/spacing.py` |
| `segments/`, `report/` | `code/nightly_segments.sh`, `code/build_report.py` |
| `summaries/` | `code/summarize.py` |
| `gtfs/` | `code/refresh_gtfs.py`, then `code/gtfs_pub.py` at publish time |
| `weather/` | `code/weather.py` |

Older findings, from before October, were computed with scripts that are not all in
`code/` in the form used at the time. Their documents describe the method in full.
