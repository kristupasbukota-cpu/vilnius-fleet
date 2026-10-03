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
import collections, csv, glob, gzip, json, math, os, re, statistics as st, sys
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
from zoneinfo import ZoneInfo
# Vilnius local time. It follows summer time: UTC+3 until 25 October 2026, then
# UTC+2. Until 1 October 2026 this file used a fixed timedelta(hours=3), which
# would have filed every hop one hour late from the end of summer time.
VILNIUS = ZoneInfo("Europe/Vilnius")
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
    return d.replace(tzinfo=timezone.utc).astimezone(VILNIUS)


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


def local_path(day):
    return os.path.join(HERE, f"segments-{day}.json")


def published_path(day):
    return os.path.join(HERE, "pub", "segments", f"segments-{day}.json.gz")


def published_days():
    out = []
    for p in glob.glob(os.path.join(HERE, "pub", "segments", "segments-*.json.gz")):
        m = re.fullmatch(r"segments-(\d{4}-\d{2}-\d{2})\.json\.gz", os.path.basename(p))
        if m:
            out.append(m.group(1))
    return out


def load(day):
    """A day's segments: the working file if it is still on disk, which is the
    freshest, otherwise the compressed copy export.py published."""
    p = local_path(day)
    if os.path.exists(p):
        return json.load(open(p))
    g = published_path(day)
    if os.path.exists(g):
        return json.load(gzip.open(g, "rt", encoding="utf-8"))
    return None


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


def daily_totals(have, day_sums):
    """Net, lost and regained vehicle-hours for every day ever exported.

    Only the last few days' segments files stay on disk; export.py compresses each
    finished day into pub/segments and removes the working copy. So the history is
    read from there, each day once, and remembered in daily_totals.json. Days whose
    working file is still on disk are recomputed every night, since they may still
    be growing. The nightly cost is one day's file however long the archive gets."""
    path = os.path.join(HERE, "daily_totals.json")
    try:
        cache = json.load(open(path))
    except Exception:
        cache = {}
    for d in have:
        net, lost, back, seg = day_sums[d]
        cache[d] = {"net": round(net / 3600, 1), "lost": round(lost / 3600, 1),
                    "back": round(back / 3600, 1), "seg": seg}
    pub = os.path.join(HERE, "pub", "segments")
    for p in sorted(glob.glob(os.path.join(pub, "segments-*.json.gz"))):
        m = re.fullmatch(r"segments-(\d{4}-\d{2}-\d{2})\.json\.gz", os.path.basename(p))
        if not m:
            continue            # segments-all.json.gz and anything else undated
        d = m.group(1)
        if d in cache:
            continue
        try:
            rows = json.load(gzip.open(p, "rt", encoding="utf-8"))
        except Exception:
            continue
        cache[d] = {"net": round(sum(r["total"] for r in rows) / 3600, 1),
                    "lost": round(sum(r["total"] for r in rows if r["total"] > 0) / 3600, 1),
                    "back": round(sum(r["total"] for r in rows if r["total"] < 0) / 3600, 1),
                    "seg": len(rows)}
        del rows
    tmp = path + ".tmp"
    json.dump(cache, open(tmp, "w"), separators=(",", ":"), sort_keys=True)
    os.replace(tmp, path)
    return cache


def daily_rain():
    """local day -> [mm, wet hours] between 06:00 and 22:00, from pub/weather.

    LHMT, station Vilniaus AMS. The row stamped T covers the hour ending at T, so it
    describes the local hour that starts at T - 1 h. Checked against Vilnius airport
    in docs/weather-audit-2026-10-01.md. A wet hour is 0.1 mm or more."""
    out = {}
    for p in glob.glob(os.path.join(HERE, "pub", "weather", "weather-*.csv")):
        with open(p, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    t = datetime.strptime(row["observationTimeUtc"], "%Y-%m-%d %H:%M:%S")
                    mm = float(row["precipitation"])
                except (KeyError, ValueError, TypeError):
                    continue
                loc = (t.replace(tzinfo=timezone.utc) - timedelta(hours=1)).astimezone(VILNIUS)
                if 6 <= loc.hour < 22:
                    e = out.setdefault(loc.date().isoformat(), [0.0, 0])
                    e[0] += mm
                    e[1] += mm >= 0.1
    return out


def main():
    cov = coverage()
    # Days with a working file on disk: only yesterday and today in normal running,
    # since export.py removes each finished day. Until 30 September the comparison
    # days were chosen from these alone, so once pruning began the "is it real" and
    # weekend panels compared every new day against three stale files from 15 to 17
    # August. Every published day is now a candidate. Existence is checked without
    # parsing anything.
    have = sorted(d for d in cov if os.path.exists(local_path(d)))
    avail = sorted(set(have) | {d for d in published_days() if d in cov})
    if not avail:
        raise SystemExit("no segments on disk or published")

    # A day still in progress is never complete, however many hours it already has.
    # Without this, a run late in the evening (outside the nightly chain, which runs
    # just after midnight) took today as the primary day, loaded its working file from
    # 00:20, which holds three hours, and crashed on an empty worst-roads list.
    today = datetime.now(timezone.utc).astimezone(VILNIUS).date().isoformat()

    def complete(d):
        return d < today and cov.get(d, (0, 0))[1] >= MIN_HOURS

    def weekday(d):
        return datetime.fromisoformat(d).weekday() < 5

    if "--primary" in sys.argv:
        primary = sys.argv[sys.argv.index("--primary") + 1]
    else:
        wd = [d for d in avail if weekday(d) and complete(d)]
        if not wd:
            raise SystemExit(f"no complete working day yet (need {MIN_HOURS} hours). "
                             f"coverage: { {d: cov[d][1] for d in avail} }")
        primary = wd[-1]

    # The nearest complete days before the primary one, never after it and never a
    # part-day: a weekend compared against a few hours of Sunday morning would say
    # nothing about the commute.
    others = [d for d in avail if d < primary and complete(d)]
    compare = next((d for d in reversed(others) if weekday(d)), None)
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

    # ---- one pass over every day on disk. Until 29 September this read each day's
    # segments file four times a night (once here, three times for the totals) and
    # the count grew with the archive. Each file is now read once and dropped, so
    # memory stays at one day's worth however long the archive gets.
    hours, day_sums = {}, {}
    for d in have:
        rows = P if d == primary else load(d)
        hours[d] = hourly(rows)
        day_sums[d] = (sum(r["total"] for r in rows),
                       sum(r["total"] for r in rows if r["total"] > 0),
                       sum(r["total"] for r in rows if r["total"] < 0),
                       len(rows))
        del rows
    # the three days the page draws, whether or not their working files survive
    for d, rows in ((primary, P), (compare, C), (weekend, W)):
        if d and rows is not None and d not in hours:
            hours[d] = hourly(rows)

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

    history = daily_totals(have, day_sums)
    rain = daily_rain()
    totals = {d: {"net": h["net"], "lost": h["lost"], "back": h["back"], "seg": h["seg"],
                  "hours": cov.get(d, (0, 0))[1], "snapshots": cov.get(d, (0, 0))[0],
                  "label": pretty(d), "short": short(d),
                  "weekend": not weekday(d), "complete": complete(d),
                  "rain": round(rain.get(d, [0, 0])[0], 1) if d in rain else None,
                  "wet": rain.get(d, [0, 0])[1] if d in rain else None}
              for d, h in sorted(history.items())}

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
           "r_mt": r_pc, "r_ms": r_pw, "conc": conc, "totals": totals, "days": avail}

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
