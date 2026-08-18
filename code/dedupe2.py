#!/usr/bin/env python3
"""Remove the snapshots this box holds twice.

Two collectors have been watching the same feed on purpose, the laptop and this
box, and at one point the laptop's whole archive was rsynced here so the raw data
existed in two places. The consequence was not noticed at the time: for every minute
where both were running, this box now holds twelve snapshots of a minute that only
ever had six of anything to see. The two sets interleave, because the collectors
poll on different phases, so nothing looks wrong in a directory listing.

It matters unevenly:

  summarize.py   counts every row of every file, so a doubled minute contributes
                 twice to the headway tally that the bunching baseline is built from.
                 Small, but real, and silently there.
  segments.py    immune. It skips any row whose MatavimoLaikas it has already used,
                 so a second copy of the same GPS fix is discarded as silence.
  delaygrid      immune. It samples one snapshot per 60 seconds by construction.

rsync preserves mtime but cannot preserve ctime, so a file copied here has a ctime
long after its mtime while a file this box wrote itself has the two within seconds.
That is the whole discriminator.

The rule: in any minute that holds files from both origins, the copies go and the
originals stay. In a minute where this box has fewer than four of its own, the
copies are filling a real hole and are kept.

    python3 dedupe2.py            # report only
    python3 dedupe2.py --apply
"""
import os, sys, glob, collections

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snapshots")
KEEP_IF_FEWER_THAN = 4
apply_it = "--apply" in sys.argv

byminute = collections.defaultdict(lambda: {"own": [], "copy": []})
for p in glob.glob(os.path.join(D, "*.csv.gz")):
    st = os.stat(p)
    kind = "copy" if st.st_ctime - st.st_mtime > 60 else "own"
    byminute[os.path.basename(p)[:13]][kind].append(p)

kill, doubled = [], 0
for m, e in byminute.items():
    if e["copy"] and len(e["own"]) >= KEEP_IF_FEWER_THAN:
        doubled += 1
        kill.extend(e["copy"])

own = sum(len(e["own"]) for e in byminute.values())
cp = sum(len(e["copy"]) for e in byminute.values())
print(f"{len(byminute)} minutes covered, {own} written here, {cp} copied in")
print(f"{doubled} minutes hold both; {len(kill)} copies to drop "
      f"({100*len(kill)/max(own+cp,1):.1f}% of the archive)")
gapfill = sum(1 for e in byminute.values() if e["copy"] and len(e["own"]) < KEEP_IF_FEWER_THAN)
print(f"{gapfill} minutes are covered only by copies and are left alone")

if apply_it:
    for p in kill:
        os.unlink(p)
    print(f"deleted {len(kill)}")
else:
    print("dry run, pass --apply")
