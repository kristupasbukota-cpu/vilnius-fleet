#!/usr/bin/env python3
"""H7, spare time in the wrong places: the numbers in docs/spare-time-2026-10-06.md.

Run from the repository root:

    python3 code/spare_time.py

Inputs: analysis/trav-*.csv.(gz|xz), working days 2 September to 5 October 2026, and
the stop positions in gtfs/gtfs-20261001.zip. Needs pandas. Bus and trolleybus lines
with the same number are kept apart by the first letter of trip_id (A bus, T trolleybus).
Writes nothing; prints every table in the document.
"""
import glob, os, sys, zipfile, io, math
import pandas as pd, numpy as np
REPO=sys.argv[1] if len(sys.argv)>1 else "."
cols=["day","vehicle","trip_id","route","direction","stop_from_id","stop_to_id","hour_local","sched_s","lost_s","trip_start_min"]
parts=[]
for p in sorted(glob.glob(os.path.join(REPO,"analysis","trav-*.csv.*"))):
    day=os.path.basename(p)[5:15]
    if not ("2026-09-02"<=day<="2026-10-05"): continue
    if pd.Timestamp(day).dayofweek>=5: continue
    d=pd.read_csv(p,usecols=cols,dtype={"route":str,"direction":str,"trip_id":str,"stop_from_id":str,"stop_to_id":str,"vehicle":str})
    parts.append(d)
T=pd.concat(parts,ignore_index=True)
print(len(T), T.day.nunique(), "days")
z=zipfile.ZipFile(os.path.join(REPO,"gtfs","gtfs-20261001.zip"))
S=pd.read_csv(z.open("stops.txt"),dtype={"stop_id":str})
lat0,lon0=54.6857,25.2876
S["km"]=np.hypot((S.stop_lat-lat0)*111.2,(S.stop_lon-lon0)*111.2*math.cos(math.radians(lat0)))
T["route"]=T.trip_id.str[0].map({"A":"bus ","T":"trolley "}).fillna("? ")+T.route
S=S.set_index("stop_id")

# ---- 1. route-direction-hour cells
T["h"]=(T.trip_start_min//60).astype(int)
T["band"]=pd.cut(T.h,[0,6,7,9,15,19,24],right=False,labels=["<06","06","07-08","09-14","15-18","19+"])
T["odd"]=pd.to_datetime(T.day).dt.day%2
L=T.groupby(["route","direction","band","stop_from_id","stop_to_id"],observed=True).agg(
   m=("lost_s","mean"),med=("lost_s","median"),n=("lost_s","size"),sched=("sched_s","median"),
   m_odd=("lost_s",lambda x: x[T.loc[x.index,"odd"]==1].mean()),m_even=("lost_s",lambda x: x[T.loc[x.index,"odd"]==0].mean())).reset_index()
L["nmax"]=L.groupby(["route","direction","band"],observed=True).n.transform("max")
L=L[(L.n>=20)&(L.n>=0.5*L.nmax)]
print(len(L),"links; split-half corr of link means:",L[["m_odd","m_even"]].corr().iloc[0,1].round(3))
C=L.groupby(["route","direction","band"],observed=True).agg(net=("m","sum"),sched=("sched","sum"),links=("m","size"),
   pos=("m",lambda x:x[x>0].sum()),neg=("m",lambda x:x[x<0].sum()),
   pos30=("m",lambda x:x[x>30].sum()),neg30=("m",lambda x:x[x<-30].sum()),
   net_odd=("m_odd","sum"),net_even=("m_even","sum"),n=("n","median")).reset_index()
C=C[C.links>=5]
C["movable"]=np.minimum(C.pos,-C.neg)
C["movable30"]=np.minimum(C.pos30,-C.neg30)
print("split-half corr of cell net:",C[["net_odd","net_even"]].corr().iloc[0,1].round(3))
print(C.groupby("band",observed=True).agg(cells=("net","size"),net_med=("net","median"),
  early=("net",lambda x:(x<-60).mean()),late=("net",lambda x:(x>60).mean()),movable_med=("movable","median"),movable30_med=("movable30","median")).round(2))

# ---- 2. vehicle-hours, misplaced time, early cells, the 07-08 round trip
T["h"]=(T.trip_start_min//60).astype(int)
T["band"]=pd.cut(T.h,[0,6,7,9,15,19,24],right=False,labels=["<06","06","07-08","09-14","15-18","19+"])
tpd=T.groupby(["route","direction","band"],observed=True).apply(lambda x: x[["day","vehicle","trip_id"]].drop_duplicates().shape[0]/24).rename("tpd").reset_index()
C=C.merge(tpd,on=["route","direction","band"])
C["vh"]=C.net*C.tpd/3600
print("vehicle-hours per weekday, net running-time error by band (observed trips):")
print(C.groupby("band",observed=True).agg(vh=("vh","sum"),trips=("tpd","sum"),
   vh_late=("vh",lambda x:x[x>0].sum()),vh_early=("vh",lambda x:x[x<0].sum())).round(1))
C["vh_mov30"]=C.movable30*C.tpd/3600
print("movable30 vh/weekday:",C.vh_mov30.sum().round(1),"; movable(all) vh:",(C.movable*C.tpd/3600).sum().round(1))
print("cells with movable30>=60s:",(C.movable30>=60).sum(),"of",len(C),"; routes:",C[C.movable30>=60].route.nunique())
print(C.sort_values("movable30",ascending=False).head(15)[["route","direction","band","net","movable30","links","tpd"]].round(1).to_string())
# consistently early cells
E2=C[(C.net<-60)]
print("\nearly cells:",len(E2)); print(E2.sort_values("net").head(15)[["route","direction","band","net","links","tpd"]].round(1).to_string())
# peak round trip: 07-08 in vs out per route
P=C[C.band=="07-08"].pivot_table(index="route",columns="direction",values="net")
P=P.dropna(); P["round"]=P.sum(axis=1)
print("\n07-08 routes:",len(P),"round trip >+60:",(P["round"]>60).mean().round(2),"<-60:",(P["round"]<-60).mean().round(2),"one dir early & other late (|.|>60):",(((P["0"]<-60)&(P["1"]>60))|((P["1"]<-60)&(P["0"]>60))).sum())

# ---- 3. worst-link ranking against padded neighbours
nm=lambda s: S.stop_name.get(s,s)
# daily vehicle-hours lost per stop pair, all routes, whole day
K=T.groupby(["stop_from_id","stop_to_id"]).agg(tot=("lost_s","sum"),n=("lost_s","size"),m=("lost_s","mean")).reset_index()
K["vh"]=K.tot/24/3600
top=K.sort_values("vh",ascending=False).head(20)
# route-direction level link means, whole day
R=T.groupby(["route","direction","stop_from_id","stop_to_id"]).agg(m=("lost_s","mean"),n=("lost_s","size"),sched=("sched_s","median")).reset_index()
R=R[R.n>=100]
art=0
for _,k in top.iterrows():
    rows=R[(R.stop_from_id==k.stop_from_id)&(R.stop_to_id==k.stop_to_id)]
    flags=[]; offs=[]
    for _,r in rows.iterrows():
        nb=R[(R.route==r.route)&(R.direction==r.direction)&((R.stop_from_id==r.stop_to_id)|(R.stop_to_id==r.stop_from_id))]
        off=nb[nb.m<=-25]
        if len(off): flags.append(r.route); offs.append(off.m.min())
    w=rows.n.sum()
    share=rows[rows.route.isin(flags)].n.sum()/w if w else 0
    if share>=0.5: art+=1
    print(f"{nm(k.stop_from_id)[:24]:24s} > {nm(k.stop_to_id)[:24]:24s} {k.vh:5.2f} vh/d  {k.m:+6.1f} s/hop  padded neighbour on {share:4.0%} of hops ({','.join(flags[:4])}) {min(offs) if offs else 0:+.0f}")
print("top-20 links where most hops have a padded neighbour:",art)
