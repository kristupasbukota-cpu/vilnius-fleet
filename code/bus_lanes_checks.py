#!/usr/bin/env python3
"""Follow-up checks for docs/bus-lanes-matched-2026-10-18.md: the H9 rows by period and for
heavier rain, and H1 scheduled against actual speed. Run from the repository root after
bus_lanes_test.py:

    python3 code/bus_lanes_checks.py OUT_DIR/lane-links.csv
"""
import glob, os, sys, math
import numpy as np, pandas as pd
rng = np.random.default_rng(2)
L = pd.read_csv(sys.argv[1], dtype={"link": str})
cols = ["day", "trip_id", "stop_from_id", "stop_to_id", "hour_local", "sched_s", "lost_s"]
parts = []
for p in sorted(glob.glob("analysis/trav-*.csv.*")):
    day = os.path.basename(p)[5:15]
    if not ("2026-08-18" <= day <= "2026-10-16") or pd.Timestamp(day).dayofweek >= 5:
        continue
    parts.append(pd.read_csv(p, usecols=cols, dtype={"trip_id": str, "stop_from_id": str, "stop_to_id": str}))
T = pd.concat(parts, ignore_index=True)
T["link"] = T.stop_from_id + ">" + T.stop_to_id
T = T.merge(L[["link", "lane", "inbound", "centre_km", "len_km"]], on="link")
T["act"] = T.sched_s + T.lost_s
CB = [0, 1, 2, 3, 4, 5, 7, 10, 99]

A = T[(T.day >= "2026-09-02") & T.hour_local.isin([7, 8]) & T.inbound]
nd = A.day.nunique()
M = A.groupby(["link", "hour_local"]).agg(n=("lost_s", "size"), lost=("lost_s", "mean"),
      act=("act", "mean"), sched=("sched_s", "mean")).reset_index() \
      .merge(L[["link", "lane", "centre_km", "len_km"]], on="link")
M = M[M.n >= 3 * nd / 2]; M["per_day"] = M.n / nd
M["v_act"] = M.len_km / (M.act / 3600); M["v_sched"] = M.len_km / (M.sched / 3600)
M["s_per_km_act"] = M.act / M.len_km; M["s_per_km_sched"] = M.sched / M.len_km
M["cb"] = pd.cut(M.centre_km, CB, labels=False)
M["vb"] = pd.qcut(np.log(M.per_day), 5, labels=False, duplicates="drop")
def strat(d, c):
    g = d.groupby(["hour_local", "cb", "vb", "lane"]).apply(
        lambda x: pd.Series({"m": np.average(x[c], weights=x.n), "n": x.n.sum()}),
        include_groups=False).unstack("lane").dropna()
    return float(np.average(g[("m", True)] - g[("m", False)], weights=g[("n", True)]))
for c in ["lost", "v_act", "v_sched", "s_per_km_act", "s_per_km_sched", "len_km"]:
    print(f"H1 stratified lane minus other, {c}: {strat(M, c):+.2f}")
lw, nl = M[M.lane], M[~M.lane]
for c in ["v_act", "v_sched", "len_km"]:
    print(f"  {c}: lane {np.average(lw[c], weights=lw.n):.2f}, other {np.average(nl[c], weights=nl.n):.2f}")
# share of strata: how many lane links, per centre band
print(M[M.lane].groupby("cb").link.nunique().to_dict(), M[~M.lane].groupby("cb").link.nunique().to_dict())

# the lane links that lose the most on inbound mornings
print(lw.sort_values("lost", ascending=False).head(8)[["link", "hour_local", "n", "lost", "centre_km"]])

# H9: wet penalty on lane and non-lane links within centre band, by period
w = pd.concat(pd.read_csv(p) for p in sorted(glob.glob("weather/weather-*.csv")))
st = (pd.to_datetime(w.observationTimeUtc) - pd.Timedelta(hours=1)).dt.tz_localize("UTC").dt.tz_convert("Europe/Vilnius")
W = pd.DataFrame({"day": st.dt.strftime("%Y-%m-%d"), "hour": st.dt.hour, "rain": w.precipitation.values}) \
    .groupby(["day", "hour"], as_index=False).rain.sum()
H = T[(T.day != "2026-09-01") & T.hour_local.between(6, 21)].copy()
H["cb"] = pd.cut(H.centre_km, CB, labels=False)
G = H.groupby(["day", "hour_local", "cb", "lane"]).lost_s.agg(["mean", "size"]).unstack("lane").dropna()
G.columns = ["m_o", "m_l", "n_o", "n_l"]; G = G.reset_index()
def agg(x):
    wt = x.n_l
    return pd.Series({"m_l": np.average(x.m_l, weights=wt), "m_o": np.average(x.m_o, weights=wt)})
G = G.groupby(["day", "hour_local"]).apply(agg, include_groups=False).reset_index() \
     .rename(columns={"hour_local": "hour"}).merge(W, on=["day", "hour"], how="left")
G["wet"] = (G.rain >= 0.1).astype(float); G["aut"] = (G.day >= "2026-09-01").astype(int)
G["gap"] = G.m_l - G.m_o
def fe(df, y):
    D = pd.get_dummies(df.day).astype(float)
    Hh = pd.get_dummies(df.hour.astype(str) + "_" + df.aut.astype(str), drop_first=True).astype(float)
    X = np.column_stack([df[["wet"]].values, D.values, Hh.values])
    return np.linalg.lstsq(X, df[y].values, rcond=None)[0][0]
def boot(df, y, k=1000):
    days = df.day.unique(); out = []
    for _ in range(k):
        pick = rng.choice(days, len(days))
        p = pd.concat([df[df.day == d].assign(day=f"{d}#{i}") for i, d in enumerate(pick)])
        out.append(fe(p, y))
    return np.percentile(out, [2.5, 97.5])
for lab, q in (("all", G.hour >= 0), ("peaks", G.hour.isin([7, 8, 16, 17, 18])),
               ("off-peak", ~G.hour.isin([7, 8, 16, 17, 18])), ("autumn only", G.aut == 1)):
    g = G[q]; ci = boot(g, "gap")
    print(f"H9 matched {lab}: wet lane {fe(g,'m_l'):+.2f}, wet other same bands {fe(g,'m_o'):+.2f}, "
          f"gap {fe(g,'gap'):+.2f} [{ci[0]:+.2f},{ci[1]:+.2f}], hours {len(g)}, wet {int(g.wet.sum())}")
# heavier rain: 1 mm or more
G["wet"] = (G.rain >= 1.0).astype(float)
ci = boot(G, "gap")
print(f"H9 matched, rain >= 1 mm: gap {fe(G,'gap'):+.2f} [{ci[0]:+.2f},{ci[1]:+.2f}], wet {int(G.wet.sum())}")
