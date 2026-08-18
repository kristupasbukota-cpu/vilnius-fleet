#!/usr/bin/env python3
"""Undo the over-copy from the Mac.

I rsynced the Mac's snapshots to fill the box's 10:37 to 11:26 hole, but the
include pattern took the whole 10:00 and 11:00 hours, so the minutes either side of
the hole now hold twelve snapshots where the collector writes six. Left alone that
would double-weight those minutes in the arc and in the headway tally.

rsync -a preserves mtime but not ctime, so a copied file has a ctime of a few
minutes ago while a file the collector wrote has a ctime matching its name. That is
the discriminator.
"""
import os, sys, glob, time
D = "/home/opc/vilnius/snapshots"
GAP0, GAP1 = "20260818T103705Z", "20260818T112611Z"   # the real hole, inclusive-ish
CUT = time.time() - 20 * 60                            # copied within the last 20 min
apply = "--apply" in sys.argv

kill = []
for p in glob.glob(os.path.join(D, "20260818T1*.csv.gz")):
    b = os.path.basename(p).split(".")[0]
    if GAP0 < b < GAP1:
        continue                      # inside the hole: this is the copy we wanted
    if os.stat(p).st_ctime > CUT:
        kill.append(p)

print(f"{len(kill)} files copied outside the gap")
for p in sorted(kill)[:3]:
    print("  ", os.path.basename(p))
if apply:
    for p in kill:
        os.unlink(p)
    print("deleted")
else:
    print("dry run, pass --apply")
