# Timetables

Every version of the Vilnius GTFS timetable this project has held since 14 August
2026. The city publishes only the current one, so a version that is not kept here
cannot be obtained again, and every claim about a past day depends on that day's
timetable.

## How the versions are stored

- **`gtfs-YYYYMMDD.zip`**: a whole version, exactly as the city published it. Every
  version up to 2 October 2026 is stored this way, and from then on the first
  version of each calendar month.
- **`gtfs-YYYYMMDD.patch.xz`**: from 3 October 2026, every other version, stored as
  the lines that changed since the version before it. About 30 KB instead of
  3.5 MB. The city republishes almost daily and usually changes a few thousand of
  about 430,000 rows.
- **`versions.json`**: when each version was downloaded, its fingerprint, and its
  row counts.

`YYYYMMDD` is the UTC date the version was downloaded. A suffix `-1`, `-2` marks a
second or third version downloaded on the same day.

## Getting whole zips back

```
python3 code/gtfs_rebuild.py              # gtfs/ -> gtfs-full/, one zip per version
```

Standard library only. Each patched version is rebuilt from the one before it.
Every file inside it is checked against its recorded sha256, and the version
against its fingerprint, so the contents are exactly what the city published. The
zip wrapper is repacked, so its own file hash differs from the original. Nothing
in this project depends on that hash.

Before a patch is written, the box rebuilds the version from it and compares every
file. If anything differs, the version is stored whole instead.

Format: `code/gtfs_patch.py`. Writer: `code/gtfs_pub.py`. Why:
`docs/repo-growth-plan-2026-10-02.md`.

Source: Vilniaus viešasis transportas, `https://www.stops.lt/vilnius/vilnius/gtfs.zip`.
