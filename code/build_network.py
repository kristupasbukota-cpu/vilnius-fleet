#!/usr/bin/env python3
"""Extract the route network from GTFS shapes.txt as a simplified basemap.

The city's own route geometry, drawn faintly, replaces external map tiles , 
so the finished HTML makes no network requests at all.
"""
import csv, io, json, math, os, sys, zipfile
sys.setrecursionlimit(50000)
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
LAT0 = 54.70
M_PER_DEG_LAT = 111320.0
M_PER_DEG_LON = 111320.0 * math.cos(math.radians(LAT0))


def dp(pts, tol_m):
    """Douglas-Peucker, tolerance in metres."""
    if len(pts) < 3:
        return pts
    ax, ay = pts[0][1] * M_PER_DEG_LON, pts[0][0] * M_PER_DEG_LAT
    bx, by = pts[-1][1] * M_PER_DEG_LON, pts[-1][0] * M_PER_DEG_LAT
    dx, dy = bx - ax, by - ay
    den = math.hypot(dx, dy)

    worst_i, worst_d = 0, -1.0
    for i in range(1, len(pts) - 1):
        px, py = pts[i][1] * M_PER_DEG_LON, pts[i][0] * M_PER_DEG_LAT
        d = math.hypot(px - ax, py - ay) if den == 0 else \
            abs(dy * px - dx * py + bx * ay - by * ax) / den
        if d > worst_d:
            worst_i, worst_d = i, d

    if worst_d <= tol_m:
        return [pts[0], pts[-1]]
    return dp(pts[:worst_i + 1], tol_m)[:-1] + dp(pts[worst_i:], tol_m)


def main(tol_m=22.0):
    z = zipfile.ZipFile(os.path.join(HERE, "gtfs.zip"))

    shapes = defaultdict(list)
    for r in csv.DictReader(io.TextIOWrapper(z.open("shapes.txt"), "utf-8-sig")):
        shapes[r["shape_id"]].append(
            (int(r["shape_pt_sequence"]), float(r["shape_pt_lat"]), float(r["shape_pt_lon"])))

    routes = {}
    for r in csv.DictReader(io.TextIOWrapper(z.open("routes.txt"), "utf-8-sig")):
        routes[r["route_id"]] = r.get("route_type", "3")

    # one shape per route+direction. the longest, which is the full-length pattern
    best = {}
    for r in csv.DictReader(io.TextIOWrapper(z.open("trips.txt"), "utf-8-sig")):
        sid = r.get("shape_id")
        if not sid or sid not in shapes:
            continue
        key = (r.get("route_id"), r.get("direction_id"))
        if key not in best or len(shapes[sid]) > len(shapes[best[key]]):
            best[key] = sid

    lines, raw_n = [], 0
    for (route_id, _), sid in best.items():
        pts = [(lat, lon) for _, lat, lon in sorted(shapes[sid])]
        raw_n += len(pts)
        simp = dp(pts, tol_m)
        # route_type 4 is the ferry. it traces the Neris, worth its own styling
        lines.append({"t": 1 if routes.get(route_id) == "4" else 0,
                      "p": [[round(a, 5), round(b, 5)] for a, b in simp]})

    kept = sum(len(l["p"]) for l in lines)
    out = os.path.join(HERE, "network.json")
    with open(out, "w") as f:
        json.dump(lines, f, separators=(",", ":"))
    print(f"{len(lines)} lines | {raw_n} -> {kept} points ({kept/raw_n:.0%}) | "
          f"{os.path.getsize(out)/1024:.0f} KB")


if __name__ == "__main__":
    import sys
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 22.0)
