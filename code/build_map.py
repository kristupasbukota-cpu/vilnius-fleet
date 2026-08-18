#!/usr/bin/env python3
"""Turn collected snapshots into a self-contained HTML replay of the Vilnius fleet."""
import argparse, csv, glob, gzip, io, json, os, zipfile
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
VILNIUS_TZ = timedelta(hours=3)  # EEST

LAT0, LON0 = 54.4, 24.8       # corner of the accepted region, see the lat/lon guard
TYPE_MAP = {"Autobusai": 0, "Troleibusai": 1, "Laivai": 2}
TYPE_NAMES = ["Bus", "Trolleybus", "Ferry"]


def load_routes():
    """route_short_name -> long name, from the static GTFS feed."""
    out = {}
    zp = os.path.join(HERE, "gtfs.zip")
    if not os.path.exists(zp):
        return out
    z = zipfile.ZipFile(zp)
    for r in csv.DictReader(io.TextIOWrapper(z.open("routes.txt"), "utf-8-sig")):
        sn = (r.get("route_short_name") or "").strip()
        if sn and sn not in out:
            out[sn] = (r.get("route_long_name") or "").strip()
    return out


def read_snapshot(path):
    txt = gzip.open(path, "rt", encoding="utf-8", errors="replace").read().replace("\r", "\n")
    return list(csv.DictReader(io.StringIO(txt)))


def as_int(s):
    s = (s or "").strip()
    return int(s) if s.lstrip("-").isdigit() else None


def pct(sorted_vals, q):
    if not sorted_vals:
        return None
    i = min(int(len(sorted_vals) * q), len(sorted_vals) - 1)
    return sorted_vals[i]


def build_arc(files):
    """The day's shape: fleet size and lateness distribution at every snapshot.

    Computed over every file available, not just the map frames, so the
    standstill and other short events survive the downsampling.
    """
    arc = []
    for p in files:
        stamp = os.path.basename(p).split(".")[0]
        local = datetime.strptime(stamp, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc) + VILNIUS_TZ
        rows = read_snapshot(p)
        rows = [r for r in rows if (r.get("Marsrutas") or "").strip()]
        d = sorted(x for x in (as_int(r.get("NuokrypisSekundemis")) for r in rows) if x is not None)
        arc.append([
            local.hour * 60 + local.minute + local.second / 60,   # minutes since local midnight
            len(rows),
            round((pct(d, .50) or 0) / 60, 2),
            round((pct(d, .90) or 0) / 60, 2),
            len(d),
        ])
    return arc


def stamp_of(path):
    return datetime.strptime(os.path.basename(path).split(".")[0], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)


def sample_by_time(files, spacing_s):
    """Pick roughly one file per `spacing_s` of wall-clock time.

    Sampling by time, not by file index. The collector's interval changes over the
    life of a dataset, so index-based sampling would quietly cover a 30-second
    stretch and a 10-second stretch at different real-world rates.
    """
    if spacing_s <= 0:
        return files
    out, next_ok = [], None
    for f in files:
        t = stamp_of(f)
        if next_ok is None or t >= next_ok:
            out.append(f)
            next_ok = t + timedelta(seconds=spacing_s)
    return out


def build(spacing, max_frames):
    files = sorted(glob.glob(os.path.join(HERE, "snapshots", "*.csv.gz")))
    if not files:
        raise SystemExit("no snapshots yet")
    # Prefer a precomputed arc.json (built over the FULL snapshot set, usually on
    # the collecting machine) so the charts keep every short event even when the
    # map frames here are a sparse sample.
    cached = os.path.join(HERE, "arc.json")
    if os.path.exists(cached):
        arc = json.load(open(cached, encoding="utf-8"))
    else:
        arc = build_arc(files)
    files = sample_by_time(files, spacing)
    if max_frames and len(files) > max_frames:
        step = len(files) / max_frames
        files = [files[int(i * step)] for i in range(max_frames)]

    routes, frames = load_routes(), []
    route_idx, route_list = {}, []
    # Vehicle ids and destination names repeat in every frame a vehicle appears in,
    # which over three days is most of the file. Interned once and referenced by
    # index instead: about 500 ids and 400 destinations against 240k positions.
    veh_idx, veh_list = {}, []
    dir_idx, dir_list = {}, []

    def intern(s, idx, lst):
        if s not in idx:
            idx[s] = len(lst)
            lst.append(s)
        return idx[s]

    day0 = (stamp_of(files[0]) + VILNIUS_TZ).date() if files else None

    for p in files:
        stamp = os.path.basename(p).split(".")[0]
        t_utc = datetime.strptime(stamp, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        local = t_utc + VILNIUS_TZ

        vehicles = []
        for r in read_snapshot(p):
            lat, lon = as_int(r.get("Platuma")), as_int(r.get("Ilguma"))
            route = (r.get("Marsrutas") or "").strip()
            if lat is None or lon is None or not route:
                continue
            lat, lon = lat / 1e6, lon / 1e6
            if not (54.4 < lat < 55.1 and 24.8 < lon < 25.8):
                continue  # outside the Vilnius region. bad row
            if route not in route_idx:
                route_idx[route] = len(route_list)
                route_list.append([route, routes.get(route, "")])
            vehicles.append([
                # Packed as integer offsets from a corner of the region: "20345"
                # instead of "54.70345" is six characters saved per position, and
                # there are a quarter of a million of them. Unpacked once on load.
                round((lat - LAT0) * 1e5), round((lon - LON0) * 1e5),
                as_int(r.get("NuokrypisSekundemis")),
                route_idx[route],
                as_int(r.get("Greitis")) or 0,
                TYPE_MAP.get((r.get("Transportas") or "").strip(), 0),
                intern((r.get("MasinosNumeris") or "").strip(), veh_idx, veh_list),
                intern((r.get("KryptiesPavadinimas") or "").strip()[:44], dir_idx, dir_list),
                as_int(r.get("IntervalasPries")),      # seconds to the vehicle ahead
            ])
        # Minutes on a continuous axis shared with the arc. Past midnight keeps
        # counting (24:40 rather than 00:40) so the chart cursor and the click-to-seek
        # stay correct across the date boundary.
        mins = local.hour * 60 + local.minute + local.second / 60
        if day0 is not None and local.date() > day0:
            mins += 1440 * (local.date() - day0).days
        frames.append({"t": local.strftime("%H:%M:%S"), "d": local.strftime("%a %d %b"),
                       "m": round(mins, 3), "v": vehicles})

    # label for each midnight boundary crossed, keyed by day offset
    day_labels = {}
    if day0 is not None:
        for f in files:
            loc = (stamp_of(f) + VILNIUS_TZ)
            off = (loc.date() - day0).days
            if off > 0:
                day_labels[off] = loc.strftime("%a %d %b")

    return {"frames": frames, "routes": route_list, "arc": arc, "dayLabels": day_labels,
            "veh": veh_list, "dirs": dir_list, "org": [LAT0, LON0],
            "generated": (datetime.now(timezone.utc) + VILNIUS_TZ).strftime("%Y-%m-%d %H:%M")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spacing", type=float, default=0,
                    help="seconds of real time between map frames (0 = every snapshot)")
    ap.add_argument("--max-frames", type=int, default=900)
    ap.add_argument("--out", default=os.path.join(HERE, "vilnius-fleet.html"))
    a = ap.parse_args()

    data = build(a.spacing, a.max_frames)
    tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()

    # inline Leaflet so the file works with no network beyond the map tiles
    for token, fn in (("/*__LEAFLET_CSS__*/", "leaflet.css"), ("/*__LEAFLET_JS__*/", "leaflet.js")):
        p = os.path.join(HERE, fn)
        if os.path.exists(p):
            tpl = tpl.replace(token, open(p, encoding="utf-8").read())

    bl = os.path.join(HERE, "baseline.json")
    if os.path.exists(bl):
        tpl = tpl.replace("/*__BASELINE__*/null", open(bl, encoding="utf-8").read())

    dg = os.path.join(HERE, "delaygrid.json")
    if os.path.exists(dg):
        tpl = tpl.replace("/*__DELAYGRID__*/[]", open(dg, encoding="utf-8").read())

    net = os.path.join(HERE, "network.json")
    if os.path.exists(net):
        tpl = tpl.replace("/*__NETWORK__*/[]", open(net, encoding="utf-8").read())

    html = tpl.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(html)

    n = sum(len(f["v"]) for f in data["frames"])
    print(f"{len(data['frames'])} frames | {n} vehicle positions | "
          f"{data['frames'][0]['t']} to {data['frames'][-1]['t']} | "
          f"{os.path.getsize(a.out)/1024:.0f} KB -> {a.out}")


if __name__ == "__main__":
    main()
