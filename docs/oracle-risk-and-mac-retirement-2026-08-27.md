# The Mac is retired, and what actually threatens the box

27 August 2026.

> **Resolved 29 August.** Exposure A is closed. The console shows the Always Free
> badge on both `vilnius-collector` and its 100 GB boot volume, and a Resource
> Explorer search for "always free" in eu-milan-1 returns exactly those two
> resources and nothing else. The 16 September credit expiry and the October
> reclamation date do not touch either of them. Exposures B and C stand: idle
> reclamation applies *because* the instance is Always Free, and the account
> inactivity rule is unchanged. Two further things the console surfaced: the boot
> volume has never been backed up, and cross-region replication is off.

## 1. Mac collector: stopped

It ran as a plain foreground process started on 15 August, `caffeinate -i python3
collect.py 10`, with no launchd job and no cron entry, so stopping it was a
matter of killing two PIDs. Nothing will restart it, including after a reboot.

**Before stopping it I checked what would be lost.** Comparing filenames is
misleading here: the two collectors poll the same feed at different instants, so
39,740 of the Mac's 60,801 files have no identically named twin on the box while
covering exactly the same seconds. Comparing *coverage* instead, by minute:

| | minutes covered |
|---|---|
| Mac | 11,092 |
| box | 17,085 |
| **only on the Mac** | **19** |

Those 19 minutes were 18 August 08:45 to 09:03, the window before the box came
up. 98 files, now rsynced across and verified: zero minutes remain that the Mac
holds and the box does not.

The Mac keeps its archive. 60,815 files, 929 MB, untouched, frozen at
`20260827T134013Z`. That is now a complete offline copy of everything through
today, which matters for section 3.

---

## 2. The Oracle problem, which is not the outage

The Ashburn outage was noise. The account itself has two real exposures, and
they are different problems with different deadlines.

### Exposure A: is the instance actually Always Free?

The account `viesastransportas` was created **17 August 2026** and the instance
`vilnius-collector` was created the same evening, 21:26 UTC. That places it
inside the 30-day free credit promotion.

- Free credits expire around **16 September 2026**.
- A **30-day grace period** follows, during which existing paid resources keep
  running but no new ones can be created.
- Around **16 October 2026**, anything that is not Always Free is reclaimed
  unless the account is upgraded to paid.

Anything Always Free is explicitly exempt and is kept for the life of the
account.

The instance looks Always Free eligible on every dimension visible from inside
it: `VM.Standard.E2.1.Micro`, 1 GB of memory, and a 100 GB boot volume, against
an Always Free allowance of up to 2 micro instances and 200 GB of block storage.
But eligible and actually flagged are different things, and the flag is not
visible from inside the VM. It is only visible in the console.

**The check, which takes a minute.** Console, Compute, Instances, open
`vilnius-collector`. An Always Free instance carries an **"Always Free-eligible"**
label. If it is there, exposure A is closed and nothing happens in September. If
it is not, the instance is running on trial credits and will be reclaimed in
October unless the account is upgraded.

### Exposure B: idle reclamation

This one applies specifically *because* the instance is Always Free, and it is
the one I would actually worry about.

Oracle reclaims Always Free compute instances that stay idle for 7 consecutive
days, where idle means all of:

- CPU utilisation, 95th percentile, below 20%
- network utilisation below 20%
- memory utilisation below 20%, which applies to Ampere A1 shapes only, so not
  to this one

Measured on the box over the 9 days since it last booted:

| metric | measured | threshold |
|---|---|---|
| system CPU busy since boot | **0.45%** | 20% |
| collector process CPU | 18 min 29 s over 8.8 days, **0.15%** | |
| network | 4.62 GB in, 1.01 GB out over 9.1 days, about **6 KB/s**, roughly 0.01% of the shape's 480 Mbps | 20% |

It is not close. This workload polls a 60 KB text file six times a minute and
gzips it. It is about as idle as a running machine can be while still doing
something useful. By the stated criteria this instance qualifies for reclamation
on any 7-day window you care to pick.

Whether Oracle actually acts on it is another matter. The criteria are published
but the enforcement is not, and plenty of people run tiny always-free instances
for years untouched. I would treat it as a live risk rather than a certainty.

### Exposure C, minor: account inactivity

Separately, Oracle's Free Tier FAQ says accounts left idle for 30 days or more
may be deemed abandoned and become eligible for suspension. That is an
account-level rule about your usage, not the instance's. Logging into the console
once a month is free insurance.

---

## 3. What I would do

**The clean fix for both A and B is to upgrade to Pay As You Go.** Always Free
resources stay free on a paid account, so the running cost stays zero, the
September and October dates stop mattering, and idle reclamation is a free-tier
policy. The cost of the upgrade is the risk of accidentally provisioning
something billable, which a budget alert set to a euro or two makes visible
immediately.

The alternative people use for exposure B is to run a synthetic CPU load to stay
above the threshold. It works, but it exists to defeat a policy whose whole point
is not wasting idle capacity, and on a 1/8 OCPU burstable shape sustained load
will eventually cost you the burst credits the nightly jobs rely on. I would not.

**Regardless of which you choose, the archive needs somewhere else to live.**
This is the part that is actually urgent, and it is now more exposed than it was
this morning, because the Mac has stopped mirroring. What the GitHub repo holds
is 5.8 MB of derived tables, two days of traversals, the block table, the report
and every GTFS version. What it does not hold is the raw snapshot archive: 98,043
files on the box, of which the Mac's frozen copy covers everything up to today
and nothing after.

So the exposure is specific: **if the box disappears, every snapshot written from
28 August onward is gone**, and the derived tables stop at 19 August. A weekly
job that regenerates the derived tables for the days since the last run and
pushes them to the repo would close most of it for a few megabytes a week, since
those tables, not the raw feed, are the scientific product. The raw archive at
roughly 2.3 GB a month needs a different home if you want it kept.

---

## Checklist

1. Console, Compute, Instances, `vilnius-collector`: confirm the **Always
   Free-eligible** label. Before 16 September.
2. Decide on Pay As You Go. It closes both exposures and costs nothing while you
   stay inside the free allowances.
3. Set a budget alert at a low threshold if you do upgrade.
4. Extend the weekly publish to cover derived tables for recent days, so the
   repo stops being a snapshot of 19 August.
5. Log into the console monthly.
