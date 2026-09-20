# How late is Vilnius? State of play

Written 18 August 2026, revised through 19 August, five days in.

---

## 1. What this is

A study of how punctual Vilnius public transport actually is, built entirely from the
city's own live GPS feed. No survey, no press release, no operator dashboard. Every
number comes from the same file the JUDU journey planner reads, polled every 10
seconds and kept.

The one question it answers so far: **is the city late, when, and where.**

---

## 2. What happened, in order

| When | What |
|---|---|
| Sat 15 Aug, 03:03 | First snapshot. 15 August is Žolinė, a public holiday, so this is a holiday timetable. |
| Sat 15 Aug | Feed refresh rate measured empirically at 5.5 s, so polling faster is pointless. Collector started at 30 s, later tightened to 10 s. |
| Sun 16 Aug | First visualization. Map replay, day chart, filters. |
| Sun 16 Aug | Bunching analysis and the delay map added. |
| Mon 17 Aug | An ordinary working day collected, by accident rather than plan: the collector had simply never stopped. |
| Mon 17 Aug, 21:26 | An always-on machine created in Oracle's Milan region. Collector moved there. |
| Mon 17 Aug, 22:12 | Both collectors running in parallel for the overlap check. |

Total collected: **16,117 snapshots, 227 MB, covering 67 hours** across a holiday, a
Sunday and a weekday.

---

## 3. What we are actually collecting

**Source:** `https://www.stops.lt/vilnius/gps_full.txt`, published by SĮ "Susisiekimo
paslaugos" (JUDU). Plain CSV, no API key, no rate limit published. It refreshes every
5.5 seconds, measured, and carries roughly 300 to 550 vehicles depending on the hour.

Each row is one vehicle at one moment, with 17 fields. **We use 9 of them. Eight are
being written to disk and never read.** That is the single biggest opportunity in the
project, and it is covered in section 7.

### Fields we use

| Field | Meaning | What it gives us |
|---|---|---|
| `Marsrutas` | route short name | route filter, per-route stats |
| `Transportas` | bus / trolleybus / ferry | mode filter |
| `MasinosNumeris` | vehicle id | tracking one vehicle between snapshots |
| `Platuma` / `Ilguma` | latitude / longitude, ×10⁶ | the map, the delay grid |
| `Greitis` | speed, km/h | "actually moving" vs parked-but-transmitting |
| `NuokrypisSekundemis` | seconds behind schedule, negative = early | **every lateness number in the project** |
| `KryptiesPavadinimas` | destination text | tooltips, the table |
| `IntervalasPries` | seconds to the vehicle ahead | the bunching analysis |

### Fields we collect and ignore

| Field | Example | Filled | What it would unlock |
|---|---|---|---|
| `ReisoIdGTFS` | `T10-03-6-260620-ba-1000` | 98% | **Joins to the official timetable.** 94% match `trips.txt` exactly. |
| `ReisoPradziaMinutemis` | `598` (09:58) | 98% | Which trip of the day a vehicle is on. |
| `MatavimoLaikas` | `36892` (10:14:52) | 100% | The true GPS fix time, rather than when we happened to poll. |
| `Azimutas` | `0` to `360` | 100% | Direction of travel, so a road can be split inbound vs outbound. |
| `IntervalasPaskui` | seconds to the vehicle behind | 88% | The other half of the bunching picture. |
| `KryptiesTipas` | `A>B`, `D>A` | 100% | Which end of the route it is running toward. |
| `MasinosTipas` | `KWNZ`, `KZ` | 98% | Vehicle attributes, 8 distinct codes. |
| `ReisoID` | `26779640958` | 98% | The operator's own trip identifier. |

Nothing here needs re-collecting. It is all already on disk, in every snapshot since
Saturday morning.

### Also on disk

The **static GTFS feed** (`gtfs.zip`): 115 routes, 1,538 stops, **21,825 trips**,
**437,389 stop times**, plus route shapes and official colours. Currently used only
for route long names and to draw the route network as a basemap. This is the other
unopened box.

---

## 4. What we have actually found

**The headline.** Vilnius runs late in the afternoon, not the morning, and that is a
property of the working week rather than of the time of day.

| day | morning 07-10 | afternoon 16-19 | difference |
|-----|-----|-----|-----|
| Sat 15 (holiday) | 2.12 min | 2.05 min | -0.08 |
| Sun 16 | 1.55 min | 2.08 min | +0.53 |
| Mon 17 | 2.30 min | **5.82 min** | **+3.52** |

Figures are the 90th percentile of lateness across the whole fleet, in minutes.

**The asymmetry.** Monday's morning peak runs 320 vehicles against Saturday's 181, and
arrives 0.18 min worse. Nearly double the fleet, the same punctuality. Monday's evening
peak runs essentially the same number of vehicles as its own morning and arrives 3.5 min
worse. Whatever fails at 17:00 is not volume.

**Bunching.** Only meaningful on frequent service, so the measure is restricted to
route-hours with a usual gap of 15 minutes or less. That leaves 17 routes. The express
`G` routes bunch at two to three times the rate of the trolleybus trunk routes on
comparable headways, which is backwards from what skipping stops should do.

**Where delay is created.** Every vehicle tracked minute to minute, deviation change
attributed to the midpoint of consecutive positions, binned onto a 250 m grid. 1,597
cells with enough traffic to trust. Worst well-sampled cell loses 73 seconds per vehicle
minute; the best claws back 64.

**Things I got wrong and corrected.** Route 51's 27% bunching was an artefact of a
4-vehicle route with a 40-minute headway. "No deviation reported" does not mean "heading
to a depot": 26% are ordinary passenger destinations. Deviations beyond ±60 minutes are
stale trip assignments, 0.19% of readings, now excluded and counted rather than silently
dropped. The day chart was drawing straight lines through 13 hours of missing data.

---

## 5. Where it runs now

```
Oracle Cloud, Milan            github.com/                anywhere
VM.Standard.E2.1.Micro    →    kristupasbukota-cpu/  →    rebuilds the
1/8 OCPU, 1 GB, 83 GB disk     vilnius-fleet              visualization
always free

collect.py under systemd, restarts on crash and on reboot (both proved)
summarize.py then publish.sh on a nightly timer at 00:20 UTC
```

The push is over an SSH deploy key generated on the box itself, so no token was ever
typed anywhere. Verified end to end by cloning the repository from a third machine
with neither the box nor the laptop involved.

The Mac still collects in parallel. That is deliberate and temporary: two independent
machines watching one feed is the cheapest correctness check available, and once they
agree over the overlap the Mac stops.

---

## 6. What is wrong with the current situation

Ordered by how soon it bites.

1. ~~The summariser will run out of memory in about eight days.~~ **Fixed.** Rewritten
   as a running tally with a checkpoint. 386 snapshots in 20 seconds, 68 MB peak, and
   the cost does not grow with the size of the archive.
2. ~~Rebuilding the visualization still needs the Mac awake.~~ **Fixed.** See section 8.
3. **One weekday.** Every claim about working days rests on a single Monday, with a
   4.5 hour hole in the middle of it.
4. **13 hours of the weekend is missing**, across 45 gaps, from wifi dropouts on the
   laptop. Now shaded on the chart rather than hidden, but still absent.
5. ~~The GTFS snapshot is going stale.~~ **Fixed, section 11.** It had in fact already
   gone stale by the time this was written.
6. **The delay map conflates two different things.** A terminus with built-in recovery
   time looks identical to a junction where traffic is kind. Both show as "time regained".
7. **Eight fields and the entire timetable are collected and unread.**

---

## 7. How to improve it

### Tier 1: keep what exists working

Not optional, and none of it needs you.

- ~~**Rewrite the summariser as a running tally.**~~ Done. Histogram buckets instead of lists, a
  checkpoint instead of a full rescan. Turns a job that dies in eight days into one that
  takes 30 seconds a night forever.
- ~~**Publish from the box.**~~ Done. A small repository the machine pushes summaries and sampled
  frames to each night, so the visualization can be rebuilt from anywhere with nothing of
  yours switched on.
- ~~**Re-download the GTFS feed weekly** and keep the old ones.~~ **Done, section 11.**
- ~~**Watchdog.**~~ **Done. See section 10.**

### Tier 2: open the fields we already have

This is where the real gain is. All of it works on data already on disk, retroactively,
back to Saturday.

- ~~**Join `ReisoIdGTFS` to `stop_times.txt`.**~~ **Done. See section 9.** 437,389 stop times waiting.
  This converts "this bus is 6 minutes late" into "this bus is 6 minutes late *between
  these two specific stops*", which is the difference between a heatmap and a diagnosis.
  It also separates real congestion from scheduled recovery time, fixing problem 6.
- **Use `block_id` from `trips.txt` to test the compounding hypothesis.** A block is one
  vehicle's whole day of work. If a bus on its sixth trip is reliably worse than the same
  bus on its first, that is the mechanism behind the evening collapse, and it argues for
  recovery time mid-shift rather than more vehicles. This is the most interesting open
  question in the project and the data is already sitting there.
- **Split the delay map by `Azimutas`.** Averaging both directions in a 250 m cell hides
  the asymmetry. Inbound at 08:00 and outbound at 17:00 are different roads in practice.
- **Use `MatavimoLaikas` instead of the filename.** Right now every rate is computed
  against when we polled, not when the GPS actually fixed. It also exposes stale
  positions, which we currently treat as fresh.
- **Use `IntervalasPaskui` alongside `IntervalasPries`.** Bunching is a property of a
  pair of buses; we are only looking forward.

### Tier 3: new questions worth asking

- **Buses running early.** Arguably the worse failure, since you cannot catch a bus that
  has already gone. We have the data and have never counted it.
- **Per-vehicle effects.** Is chronic lateness a property of a route, or of specific
  vehicles? `MasinosNumeris` and `MasinosTipas` are both already collected.
- **Weather.** Free historical data exists for Vilnius. Rain against lateness is one join
  away and would be a genuinely new variable rather than a reslice of the same one.
- **The long baseline.** Everything above is analysis. The one thing that cannot be
  rushed is time. A month gives day-of-week patterns, a season gives school terms and
  darkness, a year gives snow. The machine in Milan exists so that this costs nothing but
  patience.

---

## Recommendation

Tier 1 first, because in eight days it stops being optional. Then **the GTFS join**,
which is the single change that would most improve what this project can say. Everything
else is worth doing and nothing else changes the questions we can ask.

---

## 8. The 18 August outage, and what actually caused it

Between **10:36 and 11:24 UTC the box stopped executing userspace entirely** for 48
minutes. Not slow: stopped. SSH accepted the TCP connection and never sent its
banner, the collector wrote nothing, and journald logged one line in the middle of
the whole thing.

I assumed it was my fault, because I had just wired the nightly publish job in and
started it by hand. It was not. The journal from that boot says:

```
kernel: oom-kill: constraint=CONSTRAINT_NONE, global_oom,
        task_memcg=/system.slice/dnf-makecache.service, task=dnf, pid=7429
kernel: Out of memory: Killed process 7429 (dnf) anon-rss:722748kB
```

`dnf-makecache` is a stock Oracle Linux timer that refreshes package metadata. It
fired on its own schedule, with no memory limit of any kind, and grew to **722 MB on
a 946 MB machine**. Everything else went into reclaim and stayed there until the
global OOM killer finally got enough CPU to fire, at 11:24, which is the exact minute
the machine came back.

The nightly job I was blamed on had finished cleanly nine minutes earlier: 386
snapshots summarised, pushed to GitHub, **5.7 seconds of CPU and 68 MB peak**.

This also re-explains the two earlier freezes. Both were `dnf`, run by me. Once I
started wrapping my own `dnf` calls in `systemd-run` with a memory cap they were
cleanly OOM-killed inside their own cgroup and the machine stayed up. This third one
was not capped, because I never started it.

### What changed

| Change | Why |
|---|---|
| `dnf-makecache.timer` and `.service` masked | The proven cause. It has no business running unattended on a 946 MB box. |
| `/usr/local/bin/dnf` wrapper | Any `dnf` run by hand now execs inside `systemd-run --scope -p MemoryMax=200M -p MemorySwapMax=0`. It dies instead of the machine. |
| PCP disabled (`pmcd`, `pmlogger`, `pmie`, 6 timers) | 50 MB resident and four timers a day of performance metrics nobody reads. |
| `mlocate-updatedb.timer` disabled | It indexed 22,000 snapshot files every night to build a database nothing queries. |
| `ksplice-agent` capped at 200 MB | The only remaining unattended job that could grow. |
| Nightly job: `CPUQuota=25%`, `MemoryHigh=180M`, `MemoryMax=260M`, `MemorySwapMax=0`, idle IO, 15 min timeout | The previous values, 350 MB and 45%, were both *looser than the hardware*. A 45% quota on an eighth of a core never binds on anything. Measured, the job needs 5.7 s of CPU and 68 MB. |
| Collector drop-in: `Nice=-5`, `CPUWeight=1000`, `IOWeight=1000`, `MemoryLow=120M` | The one process on this box that must not miss a beat now outranks everything else, and the kernel reclaims from anything else first. |
| `publish.sh`: `du` walk removed, git told never to gc or repack, one thread, 16 MB window | The `du` stat-walked 22,000 files nightly to report a number `df` already gives. Git's defaults assume a laptop; an automatic repack here is exactly the shape of job that has taken this box down. |

Four timers remain: `logrotate`, `systemd-tmpfiles-clean`, `ksplice-agent` (capped)
and our own summariser.

### The publishing path is done

The box now pushes to `github.com/kristupasbukota-cpu/vilnius-fleet` at the end of
every nightly summarise. Verified by cloning the repository from a third machine
with no connection to either the box or the laptop:

```
1a89493 summaries 2026-08-18 11:40 UTC, 22170 snapshots collected
  README.md  STATE-OF-PLAY.md  status.json
  code/  gtfs/gtfs.zip
  summaries/{arc,baseline,delaygrid}.json  summaries/framelist.txt
```

`status.json` is regenerated on every push, so the health of the collector is
readable without an SSH session.

### The seam in the data

The box's own archive has snapshots for 10:37:05 to 11:26:11 only because they were
copied across from the Mac afterwards. Backfilling that hole took two goes: the first
rsync pattern was wider than the hole and left twelve snapshots a minute where the
collector writes six, which would have double-weighted those minutes in both the arc
and the headway tally. Corrected using `ctime`, which `rsync -a` does not preserve
and therefore distinguishes a copied file from a collected one. Every minute across
the seam now holds exactly six.

The Mac collector did not miss a single snapshot throughout. That is the second time
running two independent collectors has paid for itself.


---

## 9. Where the time actually goes

Done on 18 August. This is the section the whole project was building towards.

### The method, in one paragraph

Every live row carries `MatavimoLaikas`, when the GPS actually fixed, and
`NuokrypisSekundemis`, how many seconds late the vehicle was at that moment. Their
difference is the vehicle's position **on its own timetable**: a bus six minutes late
at 17:20 is standing where it was scheduled to be at 17:14. Look that up in the trip's
stop times and you know which pair of stops it is between, **without touching a single
coordinate**. Between two fixes, the gap between how much real time passed and how much
schedule time passed is the lateness gained, and it is shared across whichever
scheduled segments the vehicle crossed while gaining it, weighted by how much of each
one it covered.

Both GTFS clock fields and `MatavimoLaikas` are seconds past local midnight, so there
is no timezone arithmetic anywhere in `segments.py`.

### Does the arithmetic put buses where they really are

Checked against the geometry it never uses, on 76,407 sampled readings:

| check | result |
|---|---|
| nearest stop is the claimed segment's own start or end | **98.9%** |
| split between the two ends | 46.5% / 52.4% |
| median distance off the straight line joining them | **6 m** |
| p95 | 214 m, which is road curvature, not misplacement |

### Does a segment behave the same way twice

Pearson r on mean seconds lost per traversal, over segments seen on both days:

| pair | r | shared segments |
|---|---|---|
| **Mon 17 vs Tue 18** | **+0.854** | 1,934 |
| Sat 15 vs Sun 16 | +0.520 | 1,620 |
| Sun 16 vs Mon 17 | +0.514 | 1,644 |
| Sat 15 vs Tue 18 | +0.292 | 1,617 |

Two independent working days, collected by two independent machines, agree at 0.854.
Weekday against weekend is half that. **This is a property of the road, and of the
working week, not noise.**

### What it says

Monday 17 August created **204 vehicle-hours** of lateness and gave back 132, for a net
of **+72.7**. Tuesday had already reached +95.3 by mid-afternoon.

The worst pieces of road, collapsed across every route that uses them:

| stretch | routes | scheduled | Monday | Sunday |
|---|---|---|---|---|
| Kražių st. → Operos ir baleto teatras | 4, 10, 17, 43 | 139 s | **+131 s** | +5 s |
| Jono Kazlausko st. → Pramogų arena | 8 routes | 164 s | +61 s | +10 s |
| Lvivo st. → Rinktinės st. | 9, 12, 19 | 150 s | **+189 s** | +53 s |
| Čiurlionio st. → Tumo-Vaižganto st. | 6 routes | 183 s | +64 s | +24 s |
| Tumo-Vaižganto st. → Žaliasis tiltas | 3G | 292 s | **+167 s** | +29 s |
| Lvivo st. → Tuskulėnų rimties parkas | 4G | 254 s | **+177 s** | +54 s |

**Four of the six are within about 900 m of Žaliasis tiltas.** The evening collapse is
not a property of the network. It is the Neris crossings and the Šnipiškės approach.

The Sunday column is the argument. These are not slow roads. They are roads that fail
under commuter load: Kražių into the Opera costs a bus 2 min 11 s on a Monday and 5
seconds on a Sunday, on the same 409 m, against the same timetable.

It is a corridor plus a long tail: the ten worst segments carry 13.7% of all time lost,
the worst 100 carry 46.6%, and you need about 400 to reach three quarters.

### One expectation that did not survive

Problem 6 in section 6 assumed the delay map conflates congestion with **scheduled
recovery time at termini**. It does not, because there is barely any recovery time at
termini to conflate. Segments that give time back sit at median position **0.48**
through their trip at a median scheduled speed of **18.8 km/h**; segments that lose it
sit at 0.47 and 18.1 km/h. The padding in this timetable is spread evenly along the
route rather than parked at the end. That is a finding in its own right, and it means
the "time regained" cells on the old grid are mostly real recovery from real delay, not
an artefact of the schedule.

### Files

`segments.py` does the join, `validate_seg.py` does the geometric check, `runseg.sh`
runs one pass per day. Output is `segments-YYYY-MM-DD.json`, one record per
route-direction-stop-pair with scheduled duration, mean seconds lost, and an hourly
breakdown. The report is `segments-report.html`.


---

## 10. The watchdog

Done on 18 August. The design problem is not the checking, it is who does the telling.

### Why the alarm is not on the box

On 18 August this machine stopped executing userspace for 48 minutes. Anything
installed on it to report that would have frozen alongside everything else. A
watchdog that lives on the thing it watches cannot report the thing being dead.

So the box never sends alarms. It sends a **heartbeat**, every 15 minutes, to a
separate `status` branch on GitHub, using the deploy key that already exists.
A scheduled GitHub Action watches for that heartbeat to stop and opens an issue,
which GitHub emails to the repository owner. Silence is the signal, and silence is
the one thing a dead machine still produces reliably.

```
  the box                     GitHub                      inbox
  ───────                     ──────                      ─────
  watchdog.py                 status branch
  every 15 min   ──push──▶    one commit,      ──────▶     issue opened when the
  8 checks                    force-updated                heartbeat stops or the
  1 permitted action                                       box reports trouble
                              Actions, hourly at :17
```

No token, address or password is configured anywhere. The Action uses its own
built-in credentials and GitHub's existing notification settings.

### The thresholds are measured

A watchdog that cries at three in the morning gets muted, and a muted watchdog is
worse than none. So the quiet threshold came from the archive rather than from
taste. Across 23,043 snapshots:

| | gap between consecutive snapshots |
|---|---|
| median | **10.0 s** |
| p99 | 30.0 s |
| worst in any hour 00:00-05:00 | 42 s |
| gaps over 300 s | 42, all belonging to known outages |

There is no overnight quiet period: the feed keeps changing even when the fleet is
nearly parked. So **300 s of silence means something is wrong**, with a wide margin
and no seasonal false alarms.

### What it checks

Snapshot age. Whether the collector process is still logging, which is what
separates "the city's feed is refusing us", where the collector correctly backs off
and must be left alone, from "our process has hung", which we can fix. Row count,
because a feed returning an error page has a shape nothing else would notice.
Whether the nightly actually produced output. Whether the publish repository is
ahead of GitHub. Memory headroom, disk, and the age of the GTFS timetable.

### What it may do

One thing: if the collector has hung, restart it, at most once an hour. It will
never reboot the box, restart the summariser, delete anything or install anything.
Those are the actions that have hurt this machine, not helped it.

It runs under the tightest leash on the box: `CPUQuota=10%`, `MemoryMax=96M`,
`MemorySwapMax=0`, idle IO, `Nice=19`. A watchdog capable of taking the machine
down would be worse than none, and here that is not hypothetical.

### It was tested by breaking something

Not by inspection. The collector was stopped at 18:45:26 UTC and left down.

```
18:53:47  alarm  snaps=23079 age=498s  [collector_hung] [collector_down] [restarted]
18:53:57  collector writing again
18:54:56  ok     snaps=23086 age=6s
```

The alarm state reached GitHub with full detail and was read back from a third
machine with no connection to either the box or the laptop. The restart stamp was
written, so a second restart inside the hour would have been suppressed rather than
looped on. With the timer at 15 minutes, worst-case recovery from a hung collector
is about 20 minutes, unattended.

The Action's own logic was tested separately against mocked API responses, across
all seven paths: healthy, healthy-with-an-issue-open (it closes it), stale
heartbeat, box-reports-trouble, still-failing-inside-the-quiet-window, still-failing
-past-it, and no-heartbeat-branch-at-all.

The 8.5 minute hole the test left in the box's archive was backfilled from the
laptop, and `dedupe2.py` then removed exactly the 10 overlapping copies at the seam
on its own.

### Maintenance note

The watchdog will restart a collector that has been deliberately stopped, five
minutes later. Before doing maintenance on the collector, stop the timer first:

    sudo systemctl stop vilnius-watchdog.timer


---

## 11. The timetable refresh

Done on 19 August, and it justified itself on the first run.

### It was already stale

The very first check found that the city had **republished since 17 August**: 19,531
trips against the 19,292 we held, 384,425 stop times against 382,948, and one extra
stop. We had been drifting for two days with no way to notice.

### Watching the wrong thing

The obvious design checks the file's age. That is wrong twice over. If the city does
not republish for three weeks, an age check raises a false alarm every day of the
third week, which is how a watchdog gets muted. And a fresh file is no guarantee the
join works.

The number that actually matters is the **match rate**: what fraction of the vehicles
currently running resolve to a trip we know about. It is measured against a live
snapshot on every check and it is now in the heartbeat. Today it is **98.2%**, 390 of
397 vehicles, against 22,743 known trips across three versions. The watchdog warns
below 90% and alarms below 75%. It also warns if three days pass without a *check*,
which is the honest version of the staleness question.

### It has to earn the right to be installed

A truncated download or an error page replacing a good timetable would corrupt every
number downstream, so a candidate must pass before it is allowed anywhere near
`gtfs.zip`: at least 1 MB, opens as a zip, `testzip()` clean, contains all four files
we read, more than 5,000 trips, 100,000 stop times and 500 stops. Each of those
rejection paths was tested with a deliberately broken archive. Fail any and the
download is discarded and the current timetable is untouched.

### Stored only when it actually changed

Zip files embed build timestamps, so comparing bytes is useless. The fingerprint is a
hash of the archive directory, every member's name, size and CRC, sorted. Verified by
repacking the same content with completely different timestamps and confirming the
fingerprint did not move. Checking daily therefore costs 3 MB of traffic and no disk
until the city actually publishes something.

### Every version is kept, and now backed up

The city publishes only the present. Once a version is gone it cannot be obtained
again, and every retrospective claim about August depends on August's schedule. All
three versions are now in the repository alongside a manifest, about 3 MB each.

Rotation preserves the property the loaders depend on: a dash sorts before a dot, so
`gtfs-20260814.zip` and `gtfs-20260817.zip` load first and `gtfs.zip` is always read
last and wins.

```
gtfs-20260814.zip   21,825 trips   the copy this project started with
gtfs-20260817.zip   19,292 trips   what the box was holding
gtfs.zip            19,531 trips   current, installed 19 August
```

Re-running Tuesday's segment join with all three produced results **identical to the
run before**, r = 1.0000 across all 3,215 segments. That is the right answer and worth
stating: a newer timetable must not retroactively change a past day. The new trips are
for service that had not run yet.

### Where it runs

Its own `vilnius-gtfs.timer`, daily at 23:40 UTC, forty minutes before the nightly
analysis so a new timetable is in place before anything is measured against it.
Deliberately not part of the nightly chain, which is otherwise entirely local work
and should not be delayed by a slow server in Vilnius. Capped like everything else:
`CPUQuota=10%`, `MemoryMax=96M`, `MemorySwapMax=0`, 180 second timeout. A full check
takes one second.
