# How late is Vilnius?

An independent measurement of how punctual Vilnius buses and trolleybuses are, built
only from the city's own live GPS feed. A server has saved a copy of the feed about
every 10 seconds since 15 August 2026: more than 550,000 snapshots of the whole fleet so far.
Every number here can be rebuilt from the files in this repository.

## What it has found so far

- **Lateness belongs to the road, not the bus.** Two stretches of road at the same hour
  differ by 22.4 s per stop-to-stop hop on average. Two vehicles on the same stretch
  differ by 1.5 s, two routes by 2.1 s.
  [roads, not vehicles](docs/roads-not-vehicles-2026-10-02.md)
- **Since September the morning is the worst time.** Delay between 07:00 and 08:59 went
  from +1.65 s to +8.99 s per hop when the autumn network started, almost all of it on
  trips towards the centre. [morning](docs/morning-settled-2026-09-30.md),
  [one direction](docs/one-direction-2026-10-02.md)
- **Rain costs about a third.** A wet hour adds 1.3 s per hop. Bus lanes roughly halve
  that. [weather](docs/weather-2026-09-30.md), [bus lanes](docs/bus-lanes-matched-2026-10-18.md)
- **Buses rarely leave early.** 1.85% leave more than a minute early, not the 13.5% once
  quoted. Early departures are about ten times as common where the timetable gives
  no time to wait at the terminus. [departures](docs/departure-timing-point-2026-09-24.md),
  [terminal stand](docs/terminal-stand-2026-10-04.md)
- **The timetables are short, not padded.** Daytime trips need about 209 vehicle-hours a
  weekday more than scheduled. [spare time](docs/spare-time-2026-10-06.md)

The full current picture is in **[STATE-OF-PLAY.md](STATE-OF-PLAY.md)**. Every finding,
dated and including the ones later overturned, is listed in
**[docs/README.md](docs/README.md)**. Ten ideas for improving the network, written down
before testing, are in [docs/hypotheses-2026-10-04.md](docs/hypotheses-2026-10-04.md).

## How it works

```
the city's live feed        a small cloud server              this repository
stops.lt/vilnius      →     saves a snapshot about    →       derived tables, findings,
gps_full.txt                every 10 s, and builds the        code, every timetable,
                            day's tables each night           pushed every night
```

The raw snapshots (several GB) stay on the server. What is kept here is enough to repeat
every analysis. A check every 15 minutes writes to the `status` branch, and a GitHub
Action opens an issue if it stops.

## What is in each folder

| folder | what is in it |
|---|---|
| `docs/` | every finding as a dated document, plus how the project runs |
| `analysis/` | one table per day: every stop-to-stop hop (`trav-*`), every vehicle's day (`blocks-*`), departures and spacing; plus inputs for single findings |
| `gtfs/` | every timetable version the city has published since 14 August 2026, most stored as patches |
| `weather/` | hourly observations from the Vilnius weather station (LHMT) |
| `segments/`, `summaries/`, `report/` | nightly summaries and the generated report |
| `code/` | everything that runs on the server, and the script behind each finding |
| `status.json` | the server's health, rewritten every night |

## Running an analysis yourself

```bash
git clone https://github.com/kristupasbukota-cpu/vilnius-fleet.git
cd vilnius-fleet
python3 -m pip install -r requirements.txt
python3 code/gtfs_rebuild.py           # turns the timetable patches back into zips
python3 code/weather_effect.py         # for example: the rain result
```

[docs/REPRODUCE.md](docs/REPRODUCE.md) lists which script rebuilds which finding.

## Data and licence

- Live positions and timetables: Vilnius city, via [stops.lt](https://www.stops.lt/vilnius/).
- Weather: Lietuvos hidrometeorologijos tarnyba (LHMT), CC BY-SA 4.0.
- School locations: Lithuanian Ministry of Education open data.
- Bus lanes: Vilniaus planas map service.

Code is under the [MIT licence](LICENSE). The findings in `docs/` are under CC BY 4.0.
The data tables are **all rights reserved**: you may use them to check the findings,
but any other use needs permission. Details in [DATA-LICENSE.md](DATA-LICENSE.md).

The project's first days, when it ran on a laptop, are in
[the lab notebook](docs/lab-notebook-2026-08.md).
