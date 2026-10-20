#!/usr/bin/env python3
"""H8 groundwork: which stop-to-stop links run near schools, and the baseline before the
pupils' autumn holiday. Run from the vilnius-fleet repository root:

    python3 code/school_links.py analysis/h8/schools-vilnius-2026-10-18.csv OUT_DIR

The schools file is analysis/h8/schools-vilnius-2026-10-18.csv (Ministry of Education open data, active
general-education schools in Vilniaus m., copied 18 October 2026). Writes
OUT_DIR/school-links.csv and prints the baseline tables.
"""
import glob, os, sys, zipfile, math
import pandas as pd, numpy as np
SCH, OUT = sys.argv[1], sys.argv[2]
LAT0 = 54.6857; KX = 111.2*math.cos(math.radians(LAT0)); KY = 111.2
sch = pd.read_csv(SCH)
sch = sch[(sch.branch == 0) & (sch.pupils >= 100)].reset_index(drop=True)
z = zipfile.ZipFile("gtfs/gtfs-20261001.zip")
S = pd.read_csv(z.open("stops.txt"), dtype={"stop_id": str}).set_index("stop_id")

cols = ["day", "trip_id", "route", "direction", "stop_from_id", "stop_to_id", "hour_local", "lost_s"]
parts = []
for p in sorted(glob.glob("analysis/trav-*.csv.*")):
    day = os.path.basename(p)[5:15]
    if not ("2026-09-02" <= day <= "2026-10-16") or pd.Timestamp(day).dayofweek >= 5:
        continue
    parts.append(pd.read_csv(p, usecols=cols, dtype={"route": str, "direction": str, "trip_id": str,
                                                      "stop_from_id": str, "stop_to_id": str}))
T = pd.concat(parts, ignore_index=True)
print(len(T), "hops,", T.day.nunique(), "working days")

L = T.groupby(["stop_from_id", "stop_to_id"]).size().rename("hops").reset_index()
L = L[L.stop_from_id.isin(S.index) & L.stop_to_id.isin(S.index)]
for end in ("from", "to"):
    s = S.loc[L[f"stop_{end}_id"]]
    L[f"x_{end}"] = s.stop_lon.values*KX; L[f"y_{end}"] = s.stop_lat.values*KY
sx, sy, sp = sch.lon.values*KX, sch.lat.values*KY, sch.pupils.values

def seg_dist(px, py, ax, ay, bx, by):
    """km from points p to segments a-b (broadcast: links x schools)."""
    dx, dy = bx-ax, by-ay
    t = np.clip(((px-ax)*dx+(py-ay)*dy)/np.maximum(dx*dx+dy*dy, 1e-12), 0, 1)
    return np.hypot(px-(ax+t*dx), py-(ay+t*dy))

D = seg_dist(sx[None, :], sy[None, :], L.x_from.values[:, None], L.y_from.values[:, None],
             L.x_to.values[:, None], L.y_to.values[:, None])
L["school_km"] = D.min(axis=1)
L["nearest_school"] = sch.name.values[D.argmin(axis=1)]
L["pupils_300m"] = (np.where(D <= 0.3, sp[None, :], 0)).sum(axis=1)
L["pupils_500m"] = (np.where(D <= 0.5, sp[None, :], 0)).sum(axis=1)
L["near"] = np.where(L.school_km <= 0.3, "near", np.where(L.school_km > 0.8, "far", "middle"))
L["centre_km"] = np.hypot((L.x_from+L.x_to)/2-25.2876*KX, (L.y_from+L.y_to)/2-LAT0*KY)
L.drop(columns=["x_from", "y_from", "x_to", "y_to"]).round(4).to_csv(os.path.join(OUT, "school-links.csv"), index=False)
print(f"{len(sch)} schools with 100+ pupils; {len(L)} links:",
      L.near.value_counts().to_dict(), "; hops share near:", round(L.hops[L.near == 'near'].sum()/L.hops.sum(), 3))

T = T.merge(L[["stop_from_id", "stop_to_id", "near", "centre_km"]], on=["stop_from_id", "stop_to_id"])
T["dow"] = pd.to_datetime(T.day).dt.dayofweek
T["band"] = pd.cut(T.hour_local, [0, 7, 9, 15, 19, 24], right=False, labels=["<07", "07-08", "09-14", "15-18", "19+"])
T["dist"] = pd.cut(T.centre_km, [0, 2, 5, 10, 99], labels=["0-2", "2-5", "5-10", "10+"])
print("\nSeconds lost per hop, working days 2 Sep to 16 Oct, by school proximity and hour")
print(T.groupby(["near", "band"], observed=True).lost_s.mean().unstack().round(2))
print("\nSame, 07-08 only, by distance from centre (near minus far)")
g = T[T.band == "07-08"].groupby(["dist", "near"], observed=True).lost_s.mean().unstack()
g["near-far"] = g["near"]-g["far"]; print(g.round(2))
print("\n07-08, Friday against Monday-Thursday")
T["fri"] = np.where(T.dow == 4, "Fri", "Mon-Thu")
print(T[T.band == "07-08"].groupby(["near", "fri"], observed=True).lost_s.mean().unstack().round(2))
print("\n07-08 daily means near and far (for the before/after comparison)")
dd = T[T.band == "07-08"].groupby(["day", "near"], observed=True).lost_s.mean().unstack()
print(dd[["near", "far"]].describe().round(2))
