#!/usr/bin/env python3
"""Build the segment report from whatever days are on disk, with no human in it.

The data has rebuilt itself nightly since 18 August. The report did not: it was
built by hand from Monday's numbers with half of Tuesday, and it stayed that way,
so the repository's data was current and its report was not. This closes that.

It picks its own days rather than being told:

  primary   the most recent local day that is a working day and reasonably complete
  compare   the working day before it, for the "does this reproduce" panel
  weekend   the most recent Saturday or Sunday, for the "is it the commute" column

Completeness is measured from the snapshot filenames rather than assumed, because
a day that stops at lunchtime would otherwise be silently compared against a full
one and every conclusion drawn from it would be wrong in the same direction.

    python3 build_report.py                 # newest complete weekday
    python3 build_report.py --primary 2026-08-18
"""
import collections, glob, json, math, os, statistics as st, sys
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
TZ = timedelta(hours=3)
LON = math.cos(math.radians(54.69))
MIN_HOURS = 20          # a "complete" day; anything thinner is not compared
CLAMP = 120
DAYNAME = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTH = ["January", "February", "March", "April", "May", "June", "July",
         "August", "September", "October", "November", "December"]

# Stops on or immediately either side of the Neris crossings at Žaliasis tiltas and
# Konstitucijos prospektas. The corridor sentence is only written if the data
# actually puts several of these at the top, so it can never become a stale claim.
CORRIDOR = {"Žaliasis tiltas", "Lvivo st.", "Kražių st.", "Rinktinės st.",
            "Juozo Tumo-Vaižganto st.", "Operos ir baleto teatras", "Šeimyniškių st.",
            "Tuskulėnų rimties parkas", "Europos aikštė", "Konstitucijos pr.",
            "Mikalojaus Konstantino Čiurlionio st.", "Karaliaus Mindaugo tiltas"}


def local_day(basename):
    d = datetime.strptime(basename.split(".")[0], "%Y%m%dT%H%M%SZ")
    return (d.replace(tzinfo=timezone.utc) + TZ)


def pretty(day):
    d = datetime.fromisoformat(day)
    return f"{DAYNAME[d.weekday()]} {d.day} {MONTH[d.month-1]} {d.year}"


def short(day):
    d = datetime.fromisoformat(day)
    return f"{DAYNAME[d.weekday()][:3]} {d.day}"


def coverage():
    """local day -> (snapshots, distinct hours covered)"""
    out = collections.defaultdict(lambda: [0, set()])
    for p in glob.glob(os.path.join(HERE, "snapshots", "*.csv.gz")):
        t = local_day(os.path.basename(p))
        e = out[t.date().isoformat()]
        e[0] += 1
        e[1].add(t.hour)
    return {k: (v[0], len(v[1])) for k, v in out.items()}


def metres(a, b):
    x = math.radians(b[1] - a[1]) * math.cos(math.radians((a[0] + b[0]) / 2))
    return 6371000 * math.hypot(x, math.radians(b[0] - a[0]))


def mmss(sec):
    sec = int(round(sec))
    return f"{sec//60}:{sec%60:02d}"


def load(day):
    p = os.path.join(HERE, f"segments-{day}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def key(r):
    return (r["r"], r["d"], r["a"], r["b"])


def corr(x, y):
    n = len(x)
    if n < 3:
        return None
    mx, my = sum(x) / n, sum(y) / n
    sx, sy = st.pstdev(x), st.pstdev(y)
    if not sx or not sy:
        return None
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (n * sx * sy)


def hourly(rows):
    h = collections.defaultdict(lambda: [0.0, 0])
    for r in rows:
        for k, (l, n) in r["hr"].items():
            h[int(k)][0] += l * n
            h[int(k)][1] += n
    return {str(k): [round(t / 60, 1), n, round(t / n, 2)]
            for k, (t, n) in sorted(h.items()) if n >= 200}


def main():
    cov = coverage()
    have = sorted(d for d in cov if load(d))
    if not have:
        raise SystemExit("no segments-*.json on disk")

    def complete(d):
        return cov.get(d, (0, 0))[1] >= MIN_HOURS

    def weekday(d):
        return datetime.fromisoformat(d).weekday() < 5

    if "--primary" in sys.argv:
        primary = sys.argv[sys.argv.index("--primary") + 1]
    else:
        wd = [d for d in have if weekday(d) and complete(d)]
        if not wd:
            raise SystemExit(f"no complete working day yet (need {MIN_HOURS} hours). "
                             f"coverage: { {d: cov[d][1] for d in have} }")
        primary = wd[-1]

    others = [d for d in have if d != primary]
    compare = next((d for d in reversed(others) if weekday(d) and complete(d)), None)
    weekend = next((d for d in reversed(others) if not weekday(d)), None)

    P = load(primary)
    C = load(compare) if compare else None
    W = load(weekend) if weekend else None
    print(f"primary {primary} ({cov[primary][0]} snapshots, {cov[primary][1]}h), "
          f"compare {compare}, weekend {weekend}")

    # ---- map
    lines = []
    for r in P:
        if None in (r["alat"], r["blat"]):
            continue
        lines.append([round(r["alon"] * LON, 5), round(r["alat"], 5),
                      round(r["blon"] * LON, 5), round(r["blat"], 5),
                      round(r["lost"], 1), r["n"]])

    # ---- hours, for every day we have
    hours = {d: hourly(load(d)) for d in have}

    # ---- worst roads, collapsed over the routes that use them
    road = collections.defaultdict(lambda: {"t": 0.0, "n": 0, "r": set(), "sched": 0.0,
                                            "hr": collections.defaultdict(lambda: [0.0, 0])})
    for r in P:
        e = road[(r["an"], r["bn"])]
        e["t"] += r["total"]; e["n"] += r["n"]; e["r"].add(r["r"])
        e["sched"] += r["sched"] * r["n"]
        e["dist"] = metres((r["alat"], r["alon"]), (r["blat"], r["blon"])) \
            if None not in (r["alat"], r["blat"]) else None
        for k, (l, n) in r["hr"].items():
            e["hr"][int(k)][0] += l * n
            e["hr"][int(k)][1] += n
    wend = collections.defaultdict(lambda: [0.0, 0])
    for r in (W or []):
        wend[(r["an"], r["bn"])][0] += r["total"]
        wend[(r["an"], r["bn"])][1] += r["n"]

    top = sorted(road.items(), key=lambda kv: -kv[1]["t"])[:24]
    worst = []
    for (a, b), e in top:
        s = wend.get((a, b))
        worst.append({
            "a": a, "b": b, "routes": sorted(e["r"], key=lambda x: (len(x), x)),
            "min": round(e["t"] / 60, 1), "n": e["n"],
            "pass": round(e["t"] / e["n"], 1), "sched": round(e["sched"] / e["n"]),
            "dist": round(e["dist"]) if e.get("dist") else None,
            "sun": round(s[0] / s[1], 1) if s and s[1] >= 10 else None,
            "hr": {k: round(v[0] / v[1], 1) for k, v in sorted(e["hr"].items()) if v[1] >= 5},
        })

    # ---- reproducibility grid
    grid = None
    r_pc = r_pw = None
    if C:
        kp = {key(r): r for r in P}
        kc = {key(r): r for r in C}
        sh = [k for k in kp if k in kc]
        x = [kp[k]["lost"] for k in sh]
        y = [kc[k]["lost"] for k in sh]
        r_pc = round(corr(x, y), 3) if corr(x, y) is not None else None
        LO, HI, N = -150, 150, 30
        cells = [[0] * N for _ in range(N)]
        outside = 0
        for a, b in zip(x, y):
            i = int((a - LO) / (HI - LO) * N)
            j = int((b - LO) / (HI - LO) * N)
            if 0 <= i < N and 0 <= j < N:
                cells[j][i] += 1
            else:
                outside += 1
        grid = {"lo": LO, "hi": HI, "n": N, "cells": cells, "outside": outside,
                "max": max(max(r) for r in cells), "pairs": len(sh)}
    if W:
        kp = {key(r): r for r in P}
        kw = {key(r): r for r in W}
        sh = [k for k in kp if k in kw]
        v = corr([kp[k]["lost"] for k in sh], [kw[k]["lost"] for k in sh])
        r_pw = round(v, 3) if v is not None else None

    # ---- concentration
    loss = sorted((r["total"] for r in P if r["total"] > 0), reverse=True)
    tot = sum(loss) or 1
    conc, run = [], 0
    for i, v in enumerate(loss, 1):
        run += v
        if i in (5, 10, 25, 50, 75, 100, 150, 200, 300, 400, 600, 800, 1000, len(loss)):
            conc.append([i, round(100 * run / tot, 1)])

    totals = {d: {"net": round(sum(r["total"] for r in load(d)) / 3600, 1),
                  "lost": round(sum(r["total"] for r in load(d) if r["total"] > 0) / 3600, 1),
                  "back": round(sum(r["total"] for r in load(d) if r["total"] < 0) / 3600, 1),
                  "seg": len(load(d)), "hours": cov[d][1], "snapshots": cov[d][0],
                  "label": pretty(d), "short": short(d),
                  "weekend": not weekday(d), "complete": complete(d)}
              for d in have}

    w0 = worst[0]
    hit = sum(1 for w in worst[:6] if w["a"] in CORRIDOR or w["b"] in CORRIDOR)
    corridor = None
    if hit >= 3:
        names = []
        for w in worst[:6]:
            if w["a"] in CORRIDOR or w["b"] in CORRIDOR:
                names.append(f"{w['a']} to {w['bn'] if 'bn' in w else w['b']}")
        corridor = (f"{hit} of the six worst pieces of road are on the Neris crossings "
                    f"and the Šnipiškės approach, within about 900 m of "
                    f"Žaliasis tiltas.")

    labels = {
        "primary": primary, "compare": compare, "weekend": weekend,
        "primaryLabel": pretty(primary), "compareLabel": pretty(compare) if compare else None,
        "weekendLabel": pretty(weekend) if weekend else None,
        "primaryShort": short(primary), "compareShort": short(compare) if compare else None,
        "weekendShort": short(weekend) if weekend else None,
        "dateline": (f"{pretty(primary)} unless stated. "
                     f"{cov[primary][0]:,} snapshots over {cov[primary][1]} hours, "
                     f"{sum(r['n'] for r in P):,} complete segment traversals across "
                     f"{len(P):,} stop-to-stop segments."),
        "heroNet": totals[primary]["net"],
        "heroWorst": mmss(w0["pass"]),
        "heroWorstWhat": (f"lost per vehicle on the worst {w0['dist']} m, "
                          f"scheduled for {mmss(w0['sched'])}" if w0["dist"]
                          else f"lost per vehicle on the worst stretch, scheduled for {mmss(w0['sched'])}"),
        "heroR": r_pc,
        "corridor": corridor,
        "worstSentence": (
            f"{w0['a']} to {w0['b']} costs a vehicle {mmss(w0['pass'])} on "
            f"{pretty(primary).split(' ')[0]}"
            + (f" and {w0['sun']:.0f} seconds on {pretty(weekend).split(' ')[0]}"
               if w0["sun"] is not None and weekend else "")
            + (f", on the same {w0['dist']} m, against the same timetable." if w0["dist"] else ".")),
        "built": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    out = {"L": labels, "lines": lines, "hours": hours, "worst": worst, "grid": grid,
           "r_mt": r_pc, "r_ms": r_pw, "conc": conc, "totals": totals, "days": have}

    dp = os.path.join(HERE, "segdata.json")
    json.dump(out, open(dp, "w"), ensure_ascii=False, separators=(",", ":"))

    tpl = open(os.path.join(HERE, "report_template.html"), encoding="utf-8").read()
    html = tpl.replace("__DATA__", json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    rp = os.path.join(HERE, "segments-report.html")
    open(rp, "w", encoding="utf-8").write(html)

    print(f"{len(lines)} segments mapped, {len(worst)} roads, "
          f"grid {grid['pairs'] if grid else 0} pairs, r={r_pc}")
    print(f"-> segdata.json {os.path.getsize(dp)//1024} KB, "
          f"segments-report.html {os.path.getsize(rp)//1024} KB")


if __name__ == "__main__":
    main()
