#!/usr/bin/env python3
"""H1 and H9: do bus lanes cut delay once matched, and do they protect against rain?
Run from the vilnius-fleet repository root:

    python3 code/bus_lanes_test.py LANES_GEOJSON OUT_DIR

LANES_GEOJSON is the city's layer "Viešojo transporto A juostos (Esamos)" (gis.vplanas.lt,
Interaktyvus_zemelapis2/Transportas_public/MapServer/9), downloaded 18 October 2026,
coordinates rounded to 5 decimals. Reads analysis/trav-*.csv.*, gtfs/gtfs-20261001.zip
and weather/weather-*.csv. Needs pandas and numpy.
"""
import glob, os, sys, json, math, zipfile
import numpy as np, pandas as pd

LANES, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
LAT0, LON0 = 54.6857, 25.2876            # Cathedral Square
KX = 111.2 * math.cos(math.radians(LAT0)); KY = 111.2
rng = np.random.default_rng(1)

# ---------- lanes ----------
segs = []                                  # x1,y1,x2,y2 in km, per lane segment
for f in json.load(open(LANES))["features"]:
    g = f["geometry"]
    lines = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
    for ln in lines:
        for (a, b), (c, d) in zip(ln[:-1], ln[1:]):
            segs.append(((a - LON0) * KX, (b - LAT0) * KY, (c - LON0) * KX, (d - LAT0) * KY))
segs = np.array(segs)
lane_km = np.hypot(segs[:, 2] - segs[:, 0], segs[:, 3] - segs[:, 1]).sum()
print(f"lanes: {len(segs)} segments, {lane_km:.1f} km")

# ---------- hops ----------
cols = ["day", "trip_id", "route", "direction", "stop_from_id", "stop_to_id", "hour_local",
        "sched_s", "lost_s"]
parts = []
for p in sorted(glob.glob("analysis/trav-*.csv.*")):
    day = os.path.basename(p)[5:15]
    if not ("2026-08-18" <= day <= "2026-10-16") or pd.Timestamp(day).dayofweek >= 5:
        continue
    df = pd.read_csv(p, usecols=cols, dtype={"route": str, "direction": str, "trip_id": str,
                                             "stop_from_id": str, "stop_to_id": str})
    df["hour_local"] = df.hour_local.astype("int8")
    parts.append(df)
T = pd.concat(parts, ignore_index=True)
T["mode"] = T.trip_id.str[0]
T["link"] = T.stop_from_id + ">" + T.stop_to_id
print(len(T), "hops,", T.day.nunique(), "working days")

z = zipfile.ZipFile("gtfs/gtfs-20261001.zip")
S = pd.read_csv(z.open("stops.txt"), dtype={"stop_id": str}).set_index("stop_id")
L = T.groupby(["link", "stop_from_id", "stop_to_id"]).size().rename("hops").reset_index()
L = L[L.stop_from_id.isin(S.index) & L.stop_to_id.isin(S.index)].copy()
for e in ("from", "to"):
    s = S.loc[L[f"stop_{e}_id"]]
    L[f"x_{e}"] = (s.stop_lon.values - LON0) * KX; L[f"y_{e}"] = (s.stop_lat.values - LAT0) * KY
L["len_km"] = np.hypot(L.x_to - L.x_from, L.y_to - L.y_from)
L["d_from"] = np.hypot(L.x_from, L.y_from); L["d_to"] = np.hypot(L.x_to, L.y_to)
L["centre_km"] = np.hypot((L.x_from + L.x_to) / 2, (L.y_from + L.y_to) / 2)
L["inbound"] = (L.d_from - L.d_to) > 0.1
L = L[L.len_km > 0.03].copy()

# a link has a lane alongside if at least 5 of 9 points along it are within 30 m of a lane
# segment running within 30 degrees of parallel (same rule as docs/bus-lanes-2026-10-02.md)
sx1, sy1, sx2, sy2 = segs.T
sdx, sdy = sx2 - sx1, sy2 - sy1
sl2 = sdx**2 + sdy**2
sang = np.arctan2(sdy, sdx)
lane_pts = []
for r in L.itertuples():
    ang = math.atan2(r.y_to - r.y_from, r.x_to - r.x_from)
    dang = np.abs((sang - ang + np.pi / 2) % np.pi - np.pi / 2)    # undirected
    ok = dang <= math.radians(30)
    cnt = 0
    for t in np.linspace(0.1, 0.9, 9):
        px = r.x_from + t * (r.x_to - r.x_from); py = r.y_from + t * (r.y_to - r.y_from)
        u = np.clip(((px - sx1) * sdx + (py - sy1) * sdy) / np.where(sl2 > 0, sl2, 1), 0, 1)
        d = np.hypot(sx1 + u * sdx - px, sy1 + u * sdy - py)
        cnt += bool((d[ok] <= 0.03).any())
    lane_pts.append(cnt)
L["lane_pts"] = lane_pts
L["lane"] = L.lane_pts >= 5
big = L[L.hops >= 200 * T.day.nunique() / 18]
print(f"links: {len(L)}, with lane {L.lane.sum()}; busy links {len(big)}, with lane {big.lane.sum()}")
L[["link", "stop_from_id", "stop_to_id", "hops", "len_km", "centre_km", "inbound", "lane_pts",
   "lane"]].to_csv(f"{OUT}/lane-links.csv", index=False)

T = T.merge(L[["link", "lane", "inbound", "centre_km", "len_km"]], on="link", how="inner")
T["actual_s"] = T.sched_s + T.lost_s
ndays_all = T.day.nunique()

# ---------- H1 ----------
print("\n=== H1: inbound morning hops, 07:00-08:59, working days 2 Sep - 16 Oct ===")
A = T[(T.day >= "2026-09-02") & T.hour_local.isin([7, 8]) & T.inbound]
nd = A.day.nunique()
M = A.groupby(["link", "hour_local"]).agg(n=("lost_s", "size"), lost=("lost_s", "mean"),
                                          act=("actual_s", "mean"), sched=("sched_s", "mean")) \
    .reset_index().merge(L[["link", "lane", "centre_km", "len_km"]], on="link")
M = M[M.n >= 3 * nd / 2]                   # at least ~1.5 buses an hour in that hour
M["per_day"] = M.n / nd
M["speed"] = M.len_km / (M.act / 3600)
print(f"{nd} days; {M.link.nunique()} links, {M[M.lane].link.nunique()} with lane; "
      f"{M.n.sum():,} hops")

def wmean(d, c):
    return np.average(d[c], weights=d.n)

def raw(d):
    return wmean(d[d.lane], "lost") - wmean(d[~d.lane], "lost")

CB = [0, 1, 2, 3, 4, 5, 7, 10, 99]
def strata(d, extra=False):
    d = d.copy()
    d["cb"] = pd.cut(d.centre_km, CB, labels=False)
    d["vb"] = pd.qcut(np.log(d.per_day), 5, labels=False, duplicates="drop")
    keys = ["hour_local", "cb", "vb"] + (["lb"] if extra else [])
    if extra:
        d["lb"] = pd.qcut(d.len_km, 3, labels=False, duplicates="drop")
    return d, keys

def stratified(d, col="lost", extra=False):
    """lane minus non-lane, within strata, weighted by lane hops in each stratum."""
    d, keys = strata(d, extra)
    g = d.groupby(keys + ["lane"]).apply(
        lambda x: pd.Series({"m": np.average(x[col], weights=x.n), "n": x.n.sum()}),
        include_groups=False).unstack("lane").dropna()
    diff = g[("m", True)] - g[("m", False)]
    w = g[("n", True)]
    return float(np.average(diff, weights=w)), w.sum() / d[d.lane].n.sum()

def nn_match(d, col="lost", k=3):
    """each lane link-hour against its k nearest non-lane link-hours, same hour,
    on centre distance (per km) and log volume (per unit)."""
    out, w = [], []
    for h in (7, 8):
        a = d[(d.hour_local == h) & d.lane]; b = d[(d.hour_local == h) & ~d.lane]
        bx = np.column_stack([b.centre_km.values, np.log(b.per_day.values)])
        for r in a.itertuples():
            dist = np.hypot((bx[:, 0] - r.centre_km) / 1.0, (bx[:, 1] - math.log(r.per_day)) / 0.5)
            j = np.argsort(dist)[:k]
            out.append(getattr(r, col) - np.average(b[col].values[j], weights=b.n.values[j]))
            w.append(r.n)
    return float(np.average(out, weights=w))

def boot_links(fn, d, k=500):
    links = d.link.unique()
    res = []
    for _ in range(k):
        pick = rng.choice(links, len(links))
        cnt = pd.Series(pick).value_counts()
        dd = d[d.link.isin(cnt.index)].copy()
        dd["n"] = dd.n * dd.link.map(cnt)            # resample links with repetition
        try:
            res.append(fn(dd))
        except Exception:
            pass
    return np.percentile(res, [2.5, 97.5])

rows = []
def report(label, d):
    r = raw(d); s, cov = stratified(d); s2, cov2 = stratified(d, extra=True); nn = nn_match(d)
    ci_s = boot_links(lambda x: stratified(x)[0], d)
    ci_nn = boot_links(nn_match, d, k=200)
    print(f"{label}: raw {r:+.2f} | stratified {s:+.2f} [{ci_s[0]:+.2f},{ci_s[1]:+.2f}] "
          f"(covers {cov:.0%}) | +length {s2:+.2f} ({cov2:.0%}) | nearest-3 {nn:+.2f} "
          f"[{ci_nn[0]:+.2f},{ci_nn[1]:+.2f}] | lane links {d[d.lane].link.nunique()}")
    rows.append(dict(sample=label, raw=r, strat=s, strat_lo=ci_s[0], strat_hi=ci_s[1], cover=cov,
                     strat_len=s2, nn=nn, nn_lo=ci_nn[0], nn_hi=ci_nn[1],
                     lane_links=d[d.lane].link.nunique(), links=d.link.nunique()))

print("lane minus non-lane, seconds lost per hop (95% CI, bootstrap over links)")
report("all inbound links", M)
lw = M[M.lane]; nl = M[~M.lane]
print(f"  means: lane {wmean(lw,'lost'):+.2f} s, other {wmean(nl,'lost'):+.2f} s; "
      f"centre km lane median {lw.centre_km.median():.1f}, other {nl.centre_km.median():.1f}; "
      f"buses a day in hour, lane median {lw.per_day.median():.1f}, other {nl.per_day.median():.1f}")

# timetable-free measure: speed, km/h (net of how the timetable splits time between links)
s, cov = stratified(M, "speed"); ci = boot_links(lambda x: stratified(x, "speed")[0], M)
print(f"speed, km/h, lane minus non-lane, stratified: {s:+.2f} [{ci[0]:+.2f},{ci[1]:+.2f}]")
rows.append(dict(sample="speed km/h", strat=s, strat_lo=ci[0], strat_hi=ci[1], cover=cov))

# net out padded-neighbour links (H7): drop links whose next or previous link on most of
# their trips runs at least 25 s under schedule in the morning, and those neighbours
A2 = A.sort_values(["day", "trip_id"]).copy()
link_mean = A2.groupby("link").lost_s.mean()
A2["prev"] = A2.groupby(["day", "trip_id"]).link.shift(1)
A2["next"] = A2.groupby(["day", "trip_id"]).link.shift(-1)
pad = set(link_mean[link_mean <= -25].index)
nb = A2.assign(pp=A2.prev.isin(pad), pn=A2.next.isin(pad)).groupby("link")[["pp", "pn"]].mean()
flag = set(nb[(nb.pp >= 0.5) | (nb.pn >= 0.5)].index) | pad
print(f"padded links (morning inbound mean <= -25 s): {len(pad)}; with neighbours, {len(flag)} dropped")
report("without padded pairs", M[~M.link.isin(flag)])

# by volume: does the advantage hold on the busiest links, where H1 would put new lanes?
for lab, q in (("busiest half by volume", M.per_day >= M.per_day.median()),
               ("within 5 km of centre", M.centre_km <= 5)):
    report(lab, M[q])

# outbound and evening, for context
for lab, q in (("outbound 07-08", (T.hour_local.isin([7, 8])) & ~T.inbound),
               ("inbound 16-18", (T.hour_local.isin([16, 17, 18])) & T.inbound),
               ("outbound 16-18", (T.hour_local.isin([16, 17, 18])) & ~T.inbound)):
    B = T[(T.day >= "2026-09-02") & q]
    G = B.groupby(["link", "hour_local"]).agg(n=("lost_s", "size"), lost=("lost_s", "mean"),
                                              act=("actual_s", "mean")).reset_index() \
        .merge(L[["link", "lane", "centre_km", "len_km"]], on="link")
    G = G[G.n >= 3 * nd / 2]; G["per_day"] = G.n / nd
    s, cov = stratified(G)
    print(f"{lab}: raw {raw(G):+.2f}, stratified {s:+.2f} ({cov:.0%})")
    rows.append(dict(sample=lab, raw=raw(G), strat=s, cover=cov))
pd.DataFrame(rows).to_csv(f"{OUT}/h1-results.csv", index=False)

# ---------- H9 ----------
print("\n=== H9: wet hour x lane link, within each day ===")
w = pd.concat(pd.read_csv(p) for p in sorted(glob.glob("weather/weather-*.csv")))
start = (pd.to_datetime(w.observationTimeUtc) - pd.Timedelta(hours=1)) \
    .dt.tz_localize("UTC").dt.tz_convert("Europe/Vilnius")
W = pd.DataFrame({"day": start.dt.strftime("%Y-%m-%d"), "hour": start.dt.hour,
                  "rain": w.precipitation.values}).groupby(["day", "hour"], as_index=False).rain.sum()
H = T[(T.day != "2026-09-01") & T.hour_local.between(6, 21)]
# mean delay on lane and on non-lane links in each day-hour, against all non-lane links
G = H.groupby(["day", "hour_local", "lane"]).lost_s.agg(["mean", "size"]).unstack("lane")
G.columns = ["m_other", "m_lane", "n_other", "n_lane"]
G = G.reset_index().rename(columns={"hour_local": "hour"}).merge(W, on=["day", "hour"], how="left")
G["wet"] = (G.rain >= 0.1).astype(float)
G["gap"] = G.m_lane - G.m_other
G["aut"] = (G.day >= "2026-09-01").astype(int)
print(f"{G.day.nunique()} days, {len(G)} day-hours, {int(G.wet.sum())} wet")

def fe(df, y, terms=("wet",)):
    D = pd.get_dummies(df.day).astype(float)
    Hh = pd.get_dummies(df.hour.astype(str) + "_" + df.aut.astype(str), drop_first=True).astype(float)
    X = np.column_stack([df[list(terms)].values, D.values, Hh.values])
    return np.linalg.lstsq(X, df[y].values, rcond=None)[0][:len(terms)]

def boot_days(df, y, k=1000):
    days = df.day.unique(); out = []
    for _ in range(k):
        pick = rng.choice(days, len(days))
        p = pd.concat([df[df.day == d].assign(day=f"{d}#{i}") for i, d in enumerate(pick)])
        out.append(fe(p, y)[0])
    return np.percentile(out, [2.5, 97.5])

res = []
for lab, q in (("all hours 06-21", G.hour >= 0), ("peaks 07-08 and 16-18", G.hour.isin([7, 8, 16, 17, 18])),
               ("off-peak", ~G.hour.isin([7, 8, 16, 17, 18]))):
    g = G[q]
    e_l, e_o, e_g = fe(g, "m_lane")[0], fe(g, "m_other")[0], fe(g, "gap")[0]
    ci = boot_days(g, "gap")
    print(f"{lab}: wet hour adds {e_l:+.2f} s on lane links, {e_o:+.2f} s on others; "
          f"lane minus other {e_g:+.2f} [{ci[0]:+.2f},{ci[1]:+.2f}]")
    res.append(dict(sample=lab, wet_lane=e_l, wet_other=e_o, diff=e_g, lo=ci[0], hi=ci[1],
                    hours=len(g), wet_hours=int(g.wet.sum())))

# matched version: lane links against non-lane links in the same centre-distance band
H2 = H.assign(cb=pd.cut(H.centre_km, CB, labels=False))
G2 = H2.groupby(["day", "hour_local", "cb", "lane"]).lost_s.agg(["mean", "size"]).unstack("lane").dropna()
G2.columns = ["m_other", "m_lane", "n_other", "n_lane"]
G2 = G2.reset_index()
G2["gap_w"] = G2.m_lane - G2.m_other
G2 = G2.groupby(["day", "hour_local"]).apply(lambda x: np.average(x.gap_w, weights=x.n_lane),
                                              include_groups=False).rename("gap").reset_index() \
    .rename(columns={"hour_local": "hour"}).merge(W, on=["day", "hour"], how="left")
G2["wet"] = (G2.rain >= 0.1).astype(float); G2["aut"] = (G2.day >= "2026-09-01").astype(int)
e = fe(G2, "gap")[0]; ci = boot_days(G2, "gap")
print(f"same centre-distance band: lane minus other {e:+.2f} [{ci[0]:+.2f},{ci[1]:+.2f}]")
res.append(dict(sample="matched on centre distance", diff=e, lo=ci[0], hi=ci[1]))
pd.DataFrame(res).to_csv(f"{OUT}/h9-results.csv", index=False)
