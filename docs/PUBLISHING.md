# The publishing rule

**Every new finding, correction or advance gets written to `docs/` and pushed to
GitHub in the same session it is produced. Not at the end of the week, not when
somebody remembers.**

## Why this exists

Until 20 September 2026 the analysis lived in one place: a conversation. Nine
finding documents existed, and GitHub held none of them. The repository carried
the data and the code, and the only prose in it was a state-of-play document that
had not been touched since 19 August. Everything learned in the following month,
including the result that overturned the project's oldest headline, had exactly
one copy.

The same audit found that `departure.py`, the script behind the early-departure
measure, was not in the publish list either, so a published figure could not have
been reproduced from the repository.

Data and code were being protected. Conclusions were not.

## The rule

1. A finding is not finished when it is written. It is finished when it is pushed.
2. Corrections count as findings. When a published number changes, the document
   that carried the old number gets a correction banner and goes up with it.
3. Anything that produced a published number belongs in `code/`, which means the
   file list in `publish.sh`.
4. `STATE-OF-PLAY.md` is the front door and carries the current numbers. When a
   headline result changes, it changes there too.

## How

On the box:

```
cd ~/vilnius
# write or edit docs/<something>-YYYY-MM-DD.md
./publish.sh
```

`publish.sh` copies `docs/` into the published tree and pushes. It is also the
last step of the nightly timer, so anything left in `docs/` goes up that night
regardless. Running it by hand just makes it immediate.

Verify from somewhere else, not from the box:

```
git clone --depth 1 https://github.com/kristupasbukota-cpu/vilnius-fleet
ls vilnius-fleet/docs
```

## Naming

`<subject>-YYYY-MM-DD.md`, dated by when the work was done, not when it was
tidied. Documents are never rewritten in place to hide a mistake: they get a
banner saying what changed and a pointer to the document that supersedes them.
The record of having been wrong is part of the record.
