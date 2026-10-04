#!/usr/bin/env python3
"""Vector basemaps for this project's map pages, from OpenStreetMap.

Every map in the project is drawn on the same kind of basemap: streets, water,
forest and parks, railways, district and street names, as SVG paths in metres
around one fixed origin (ORIGIN below), so overlays from any page line up.

Two steps:

    python3 code/basemap.py query  WEST SOUTH EAST NORTH > q.txt
    curl -A 'vilnius-fleet-research/1.0' --data-urlencode data@q.txt \
         https://overpass-api.de/api/interpreter -o osm.json
    python3 code/basemap.py build osm.json WEST SOUTH EAST NORTH basemap.json [--no-minor]

`query` writes the Overpass request for a box, with a margin of about 1 km.
`build` clips to the box, simplifies, and writes basemap.json for code/vmap.js.
--no-minor leaves out residential streets, for city-wide maps where they would
only be noise and weight. Needs shapely.

Map data © OpenStreetMap contributors, ODbL. Pages that use it must show that credit
(code/vmap.js does).
"""
import json, math, sys
from shapely.geometry import LineString, Polygon, box, MultiPolygon, GeometryCollection
from shapely.ops import linemerge, polygonize, unary_union

ORIGIN = (25.215, 54.685)                     # lon, lat; fixed for the whole project
KX, KY = 111320 * math.cos(math.radians(ORIGIN[1])), 110574
P = lambda lon, lat: ((lon - ORIGIN[0]) * KX, -(lat - ORIGIN[1]) * KY)

ROAD = {"motorway": "major", "trunk": "major", "primary": "major", "motorway_link": "link",
        "trunk_link": "link", "primary_link": "link", "secondary": "mid", "tertiary": "mid",
        "secondary_link": "link", "tertiary_link": "link", "residential": "minor",
        "unclassified": "minor", "living_street": "minor"}
TOL = {"water": 6, "green": 10, "river": 4, "rail": 5, "minor": 3, "link": 3, "mid": 3, "major": 3}
MINAREA = {"water": 400, "green": 6000}


def query(w, s, e, n):
    m = 0.012
    b = f"({s - m:.4f},{w - m:.4f},{n + m:.4f},{e + m:.4f})"
    hw = "|".join(ROAD)
    return f"""[out:json][timeout:240];
(
  way["highway"~"^({hw})$"]{b};
  way["natural"="water"]{b}; relation["natural"="water"]{b};
  way["waterway"="river"]{b};
  way["landuse"="forest"]{b}; relation["landuse"="forest"]{b};
  way["natural"="wood"]{b}; relation["natural"="wood"]{b};
  way["leisure"="park"]{b};
  way["railway"="rail"]{b};
  node["place"~"^(suburb|neighbourhood|quarter)$"]{b};
);
out geom;
"""


def area_kind(t):
    if t.get("natural") == "water":
        return "water"
    if t.get("landuse") == "forest" or t.get("natural") == "wood" or t.get("leisure") == "park":
        return "green"
    return None


def path(cs, close):
    pts = [(round(x), round(y)) for x, y in cs]
    out = [pts[0]]
    for p in pts[1:]:
        if p != out[-1]:
            out.append(p)
    if len(out) < (3 if close else 2):
        return ""
    s, prev = "M%d %d" % out[0], out[0]
    for p in out[1:]:
        s += "l%d %d" % (p[0] - prev[0], p[1] - prev[1])
        prev = p
    return s + ("z" if close else "")


def polys(g):
    if isinstance(g, Polygon):
        return [g]
    if isinstance(g, (MultiPolygon, GeometryCollection)):
        return [q for x in g.geoms for q in polys(x)]
    return []


def lines(g):
    if g.geom_type == "LineString":
        return [g]
    if hasattr(g, "geoms"):
        return [q for x in g.geoms for q in lines(x)]
    return []


def merged(gs):
    u = unary_union(gs)
    return linemerge(u) if u.geom_type == "MultiLineString" else u


def build(src, w, s, e, n, minor=True):
    clip = box(*P(w, n), *P(e, s))
    d = json.load(open(src))["elements"]
    layers = {k: [] for k in TOL}
    places, streets = [], {}
    coords = lambda geom: [P(p["lon"], p["lat"]) for p in geom if p]
    for el in d:
        t = el.get("tags", {})
        if el["type"] == "node":
            if t.get("name"):
                x, y = P(el["lon"], el["lat"])
                places.append({"n": t["name"], "x": round(x), "y": round(y),
                               "k": 1 if t.get("place") == "suburb" else 2})
            continue
        if el["type"] == "way":
            c = coords(el.get("geometry", []))
            if len(c) < 2:
                continue
            ak = area_kind(t)
            if ak and len(c) >= 4 and c[0] == c[-1]:
                layers[ak].append(Polygon(c).buffer(0))
            elif t.get("highway") in ROAD:
                k = ROAD[t["highway"]]
                if k == "minor" and not minor:
                    continue
                layers[k].append(LineString(c))
                if t.get("name") and k in ("major", "mid"):
                    streets.setdefault(t["name"], []).append(LineString(c))
            elif t.get("waterway") == "river":
                layers["river"].append(LineString(c))
            elif t.get("railway") == "rail" and t.get("service") is None:
                layers["rail"].append(LineString(c))
        elif el["type"] == "relation":
            ak = area_kind(t)
            if not ak:
                continue
            outer, inner = [], []
            for m in el.get("members", []):
                if m.get("type") == "way" and m.get("geometry"):
                    c = coords(m["geometry"])
                    if len(c) >= 2:
                        (inner if m.get("role") == "inner" else outer).append(LineString(c))
            try:
                po = list(polygonize(linemerge(outer))) if outer else []
                pi = list(polygonize(linemerge(inner))) if inner else []
            except Exception:
                continue
            if po:
                g = unary_union(po)
                if pi:
                    g = g.difference(unary_union(pi))
                layers[ak].append(g.buffer(0))

    out = {"origin": list(ORIGIN), "k": [KX, KY], "bbox": [w, s, e, n], "layers": {},
           "credit": "© OpenStreetMap contributors"}
    for k, gs in layers.items():
        if not gs:
            out["layers"][k] = ""
        elif k in MINAREA:
            u = unary_union([g for g in gs if not g.is_empty]).intersection(clip).simplify(TOL[k])
            out["layers"][k] = "".join(path(p.exterior.coords, True) + "".join(path(i.coords, True) for i in p.interiors)
                                       for p in polys(u) if p.area >= MINAREA[k])
        else:
            u = merged(gs).intersection(clip).simplify(TOL[k])
            out["layers"][k] = "".join(path(l.coords, False) for l in lines(u))
    out["places"] = [p for p in places if clip.contains(LineString([(p["x"], p["y"]), (p["x"] + 1, p["y"])]))]
    labs = []
    for nm, ls in streets.items():
        for l in sorted(lines(merged(ls).intersection(clip)), key=lambda l: -l.length):
            if l.length < 500:
                continue
            k = max(1, int(l.length // 2500))
            for j in range(k):
                m = l.interpolate((j + 0.5) / k, normalized=True)
                if any(q["n"] == nm and math.hypot(q["x"] - m.x, q["y"] - m.y) < 1200 for q in labs):
                    continue
                a = l.interpolate(max(0, l.project(m) - 120))
                b = l.interpolate(min(l.length, l.project(m) + 120))
                ang = math.degrees(math.atan2(b.y - a.y, b.x - a.x))
                ang = ang - 180 if ang > 90 else ang + 180 if ang < -90 else ang
                labs.append({"n": nm, "x": round(m.x), "y": round(m.y), "a": round(ang), "L": round(l.length)})
    out["streets"] = labs
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "query" and len(a) == 5:
        print(query(*map(float, a[1:5])))
    elif a and a[0] == "build" and len(a) >= 7:
        o = build(a[1], *map(float, a[2:6]), minor="--no-minor" not in a)
        s = json.dumps(o, separators=(",", ":"), ensure_ascii=False)
        open(a[6], "w").write(s)
        print({k: len(v) for k, v in o["layers"].items()}, len(o["places"]), "places,",
              len(o["streets"]), "street labels,", len(s.encode()), "bytes")
    else:
        sys.exit(__doc__)
