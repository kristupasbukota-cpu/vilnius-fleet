"""H3 and H4: does delay follow the number of buses, or the time of day?

Run from the repository root:  python3 code/bus_count_tests.py
Reads analysis/trav-*.csv.* and gtfs/gtfs-*.zip (stop positions).
Autumn Monday to Thursday working days, 2 September to 29 October 2026,
29 October from 20:00 local dropped (collection gap).
"""
import csv, gzip, lzma, glob, collections, json, zipfile, io, math, datetime, random
import statistics as st

CENTRE = (54.68566, 25.28767)          # Cathedral Square
OSLO = {('756', '437'), ('756', '7350'), ('6401', '6379')}   # Lazdynėliai exits via Oslo st.

def dist(a, b):
    la = math.radians((a[0] + b[0]) / 2)
    return 6371000 * math.hypot(math.radians(a[0] - b[0]), math.radians(a[1] - b[1]) * math.cos(la))

def autumn_day(d):
    dt = datetime.date.fromisoformat(d)
    return d > '2026-09-01' and d <= '2026-10-29' and dt.weekday() <= 3

stops = {}
for z in sorted(glob.glob('gtfs/gtfs-*.zip')):
    for r in csv.DictReader(io.TextIOWrapper(zipfile.ZipFile(z).open('stops.txt'), 'utf-8-sig')):
        stops[r['stop_id']] = (float(r['stop_lat']), float(r['stop_lon']), r['stop_name'])
dc = {s: dist(CENTRE, v[:2]) for s, v in stops.items()}

oslo = collections.defaultdict(list)                  # (day, hour) -> lost_s list
core = collections.defaultdict(lambda: [0, 0.0])      # (day, hour, a, b) -> n, sum lost
for p in sorted(glob.glob('analysis/trav-*.csv.*')):
    d = p.split('trav-')[1][:10]
    if not autumn_day(d):
        continue
    op = gzip.open if p.endswith('.gz') else lzma.open
    for r in csv.DictReader(op(p, 'rt')):
        h = int(r['hour_local'])
        if d == '2026-10-29' and h >= 20:
            continue
        a, b, lost = r['stop_from_id'], r['stop_to_id'], float(r['lost_s'])
        if (a, b) in OSLO:
            oslo[(d, h)].append(lost)
        if a in dc and b in dc and 500 <= dc[a] <= 2000:
            c = core[(d, h, a, b)]; c[0] += 1; c[1] += lost
days = sorted({k[0] for k in oslo}); nd = len(days)
print(f'autumn Mon-Thu days: {nd}')

def boot(f, B=1000, seed=1):
    random.seed(seed); out = []
    for _ in range(B):
        pick = collections.Counter(random.choice(days) for _ in days)
        out.append(f(pick))
    out.sort(); return out[int(.025 * B)], out[int(.975 * B)]

# ---------- H3 ----------
print('\nH3  Oslo st. exit links: buses per hour and mean seconds lost per hop')
for h in range(5, 23):
    v = [l for d in days for l in oslo.get((d, h), [])]
    if v: print(f'  {h:02d}  {len(v)/nd:5.1f} buses/h  {st.mean(v):+6.1f} s')
def peak_minus_busy(w):
    def m(hs):
        s = n = 0
        for d, k in w.items():
            for h in hs:
                v = oslo.get((d, h), []); s += k * sum(v); n += k * len(v)
        return s / n
    return m([7, 8]) - m([6, 18])
allw = collections.Counter(days)
lo, hi = boot(peak_minus_busy)
print(f'  07-08 minus 06 and 18 (as many buses): {peak_minus_busy(allw):+.1f} s, 95% [{lo:+.1f}, {hi:+.1f}]')
def fe_slope(w, hours=range(5, 23)):
    num = den = 0
    for h in hours:
        pts = [(len(oslo[(d, h)]), st.mean(oslo[(d, h)])) for d, k in w.items() for _ in range(k) if oslo.get((d, h))]
        if len(pts) < 3: continue
        mx = st.mean(x for x, _ in pts); my = st.mean(y for _, y in pts)
        num += sum((x - mx) * (y - my) for x, y in pts); den += sum((x - mx) ** 2 for x, _ in pts)
    return num / den
lo, hi = boot(fe_slope)
print(f'  slope per extra bus/h, hour held fixed: {fe_slope(allw):+.2f} s, 95% [{lo:+.2f}, {hi:+.2f}]')

# ---------- H4 ----------
print('\nH4  hops starting 0.5-2 km from Cathedral Square')
lh = collections.defaultdict(lambda: [0, 0.0])
for (d, h, a, b), (n, s) in core.items():
    x = lh[(a, b, h)]; x[0] += n; x[1] += s
bins = [0, 4, 8, 12, 20, 30, 45, 999]
for name, hs in [('midday 11-13', [11, 12, 13]), ('evening 16-18', [16, 17, 18])]:
    acc = collections.defaultdict(lambda: [0, 0.0, 0])
    for (a, b, h), (n, s) in lh.items():
        if h not in hs: continue
        k = max(i for i in range(len(bins) - 1) if n / nd >= bins[i])
        q = acc[k]; q[0] += n; q[1] += s; q[2] += 1
    print(f'  {name}')
    for k, (n, s, links) in sorted(acc.items()):
        print(f'    {bins[k]:>2}-{bins[k+1]:<3} buses/h: {s/n:+6.1f} s/hop  ({links} link-hours, {n} hops)')
# within a link, across hours, with link and hour fixed effects
pts = [(a, b, h, n / nd, s / n) for (a, b, h), (n, s) in lh.items() if 6 <= h <= 21 and n >= nd]
X = [p[3] for p in pts]; Y = [p[4] for p in pts]
for _ in range(30):
    for key in (lambda p: (p[0], p[1]), lambda p: p[2]):
        for arr in (X, Y):
            g = collections.defaultdict(list)
            for i, p in enumerate(pts): g[key(p)].append(arr[i])
            mean = {k: st.mean(v) for k, v in g.items()}
            for i, p in enumerate(pts): arr[i] -= mean[key(p)]
print(f'  slope per extra bus/h within a link, link and hour held fixed: {sum(x*y for x,y in zip(X,Y))/sum(x*x for x in X):+.2f} s ({len(pts)} link-hours)')
print('  busiest links, buses/h and s/hop at 06, 13 and 17:')
for a, b in sorted({(a, b) for (a, b, h), (n, s) in lh.items() if n / nd >= 45}):
    row = '  '.join(f'{h:02d}: {lh[(a,b,h)][0]/nd:.0f} / {lh[(a,b,h)][1]/lh[(a,b,h)][0]:+.0f}' for h in (6, 13, 17) if (a, b, h) in lh)
    print(f'    {stops[a][2]} -> {stops[b][2]}: {row}')
