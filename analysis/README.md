# Derived tables

One file per day, written once when the day is complete and never rewritten.

| file | one row per |
|---|---|
| `trav-YYYY-MM-DD.csv.*` | stop-to-stop hop: day, vehicle, trip_id, route, direction, stop_from_id, stop_to_id, hour_local, sched_s, lost_s, trip_start_min |
| `blocks-YYYY-MM-DD.json.*` | trip: veh, trip_id, route, dir, t0, t1, dev0, dev1 |
| `dep-YYYY-MM-DD.csv.gz` | departure, 22 and 24 to 26 August only (`code/departure.py`) |
| `excess-wait-2026-10-02.csv` | route, the table behind `docs/excess-wait-2026-10-02.md` |

**Compression.** Days up to 2 October 2026 are gzip (`.gz`). From 3 October 2026 the
hop and block tables are xz (`.xz`), about 36% smaller, to keep the repository under
1 GB (`docs/repo-growth-plan-2026-10-02.md`). pandas reads both from the extension,
so read every day with one pattern:

```python
for p in sorted(glob.glob("analysis/trav-*.csv.*")):
    df = pd.read_csv(p)
```

Method sections in `docs/` written before October say `trav-*.csv.gz`. For days from
3 October use `trav-*.csv.*`.

`hour_local` is Vilnius local time, following summer time
(`docs/summer-time-fix-2026-10-01.md`).
