# Weather

Hourly observations from Vilniaus AMS (station `vilniaus-ams`, 54.626 N 25.107 E),
one file per UTC day, written nightly by [`code/weather.py`](../code/weather.py).

**Source: Lietuvos hidrometeorologijos tarnyba (LHMT), [api.meteo.lt](https://api.meteo.lt).**
The data in this folder is licensed [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
by LHMT. Reuse must credit that source and keep the same licence.

- `observationTimeUtc` marks the end of the hour the row describes. Local time is UTC+3
  in summer time, UTC+2 in winter.
- `precipitation` is millimetres over that hour.
- Temperatures in °C, wind in m/s, pressure in hPa, cloud cover and humidity in %.

How it is used: [`docs/weather-2026-09-30.md`](../docs/weather-2026-09-30.md).
