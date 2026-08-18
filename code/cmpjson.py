#!/usr/bin/env python3
"""Compare two runs of the same output, before and after a change to the inputs.

Written to answer one question honestly: 7% of the snapshot archive turned out to be
duplicated, so how much did that actually move? Guessing is not an answer and neither
is "probably not much".

    python3 cmpjson.py baseline a.json b.json
    python3 cmpjson.py segments a.json b.json
"""
import json, sys, statistics as st

mode, pa, pb = sys.argv[1], sys.argv[2], sys.argv[3]
A, B = json.load(open(pa)), json.load(open(pb))


def report(name, pairs, unit):
    if not pairs:
        print(f"  {name}: nothing shared")
        return
    d = sorted(abs(b - a) for a, b in pairs)
    same = sum(1 for a, b in pairs if a == b)
    print(f"  {name}: {len(pairs)} shared, {100*same/len(pairs):.1f}% identical")
    print(f"    median |change| {d[len(d)//2]:.1f}{unit}, "
          f"p90 {d[int(len(d)*.9)]:.1f}{unit}, max {d[-1]:.1f}{unit}")
    big = sum(1 for x in d if x > (60 if unit == 's' else 5))
    print(f"    {big} ({100*big/len(d):.1f}%) moved by more than "
          f"{'a minute' if unit == 's' else '5' + unit}")


if mode == "baseline":
    a, b = A["base"], B["base"]
    print(f"baseline: {len(a)} keys before, {len(b)} after, "
          f"{len(set(b) - set(a))} new, {len(set(a) - set(b))} gone")
    report("median headway", [(a[k], b[k]) for k in a if k in b], "s")
elif mode == "segments":
    ka = {(r["r"], r["d"], r["a"], r["b"]): r for r in A}
    kb = {(r["r"], r["d"], r["a"], r["b"]): r for r in B}
    sh = [k for k in ka if k in kb]
    print(f"segments: {len(ka)} before, {len(kb)} after, {len(sh)} shared")
    report("seconds lost per traversal", [(ka[k]["lost"], kb[k]["lost"]) for k in sh], "s")
    report("traversals counted", [(ka[k]["n"], kb[k]["n"]) for k in sh], "")
    x = [ka[k]["lost"] for k in sh]
    y = [kb[k]["lost"] for k in sh]
    n, mx, my = len(x), sum(x)/len(x), sum(y)/len(y)
    sx, sy = st.pstdev(x), st.pstdev(y)
    r = sum((p-mx)*(q-my) for p, q in zip(x, y)) / (n*sx*sy)
    print(f"  correlation between the two runs: r = {r:+.4f}")
else:
    raise SystemExit("mode must be baseline or segments")
