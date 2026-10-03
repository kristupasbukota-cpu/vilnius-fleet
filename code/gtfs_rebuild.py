#!/usr/bin/env python3
"""Rebuild every timetable version in gtfs/ as a full zip.

From October 2026 most versions in gtfs/ are stored as patches against the version
before them (see gtfs_patch.py for why and how). This turns the folder back into one
zip per version, which is what every analysis in docs/ expects:

    python3 code/gtfs_rebuild.py                       # gtfs/ -> gtfs-full/
    python3 code/gtfs_rebuild.py --src gtfs --out /tmp/gtfs-full

Whole zips are copied unchanged. Each patched version is rebuilt from the version
before it, and every file inside it is checked against its recorded sha256 and the
version against its fingerprint, so a rebuilt version has exactly the contents the
city published. The zip container itself is repacked, so its file hash differs from
the city's original.

Needs only the Python standard library and gtfs_patch.py beside this file.
"""
import glob, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gtfs_patch as gp

NAME = re.compile(r"^(gtfs-(\d{8})(?:-(\d+))?)\.(zip|patch\.xz)$")


def arg(flag, default):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default


def main():
    src = arg("--src", "gtfs")
    out = arg("--out", "gtfs-full")
    os.makedirs(out, exist_ok=True)
    items = []
    for p in glob.glob(os.path.join(src, "gtfs-*")):
        m = NAME.match(os.path.basename(p))
        if m:
            items.append(((m.group(2), int(m.group(3) or 0)), m.group(1), m.group(4), p))
    items.sort()
    full = {}            # version name -> path of its full zip in out/
    copied = rebuilt = 0
    for _, stem, kind, p in items:
        dst = os.path.join(out, stem + ".zip")
        if kind == "zip":
            if not (os.path.exists(dst) and os.path.getsize(dst) == os.path.getsize(p)):
                shutil.copyfile(p, dst)
            full[stem + ".zip"] = dst
            copied += 1
            continue
        raw = open(p, "rb").read()
        man, _ = gp.read_patch(raw)
        base = full.get(man["base"])
        if base is None:
            raise SystemExit(f"{stem}: its base {man['base']} is not in {src}")
        data, _ = gp.rebuild(open(base, "rb").read(), raw)
        open(dst + ".part", "wb").write(data)
        os.replace(dst + ".part", dst)
        full[stem + ".zip"] = dst
        rebuilt += 1
        print(f"{stem}.zip rebuilt from {man['base']}, fingerprint {man['fingerprint']} checked")
    print(f"{copied} copied, {rebuilt} rebuilt, into {out}/")


if __name__ == "__main__":
    main()
