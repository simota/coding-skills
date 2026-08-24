<!-- coding:contract -->
# HANDOFF — passing work between coding skills

Every `T1` and `T2` run returns one, whether the next reader is another skill, a
person, or a later session. It is the single place the facts live, and it is the
**record, not the report**: what a person reads is a bounded view over it
(`_coding/REPORT.md`), never this object rendered field by field.

**`T0` is the exception** (`_coding/SIZING.md`): a one-skill, reversible,
under-three-files change with one-sentence acceptance returns its one-line
report and no handoff. It still names what was run and what was observed — `T0`
drops the paperwork, never the evidence.

## The object

```yaml
brief:                        # every field of the brief in _coding/SIZING.md
  goal: "<one sentence describing the state once achieved>"
  delivers: "<a single artifact>"
  axes: [...]                 # what counts as achieved — every one must hold
  excludes: [...]             # what will not be done. May not be empty
  baseline: "<the observed starting state>"
  max_attempts: <n>
  open_questions: []          # must be empty; a non-empty one never travels
status: DONE                  # DONE | PARTIAL | BLOCKED  (_coding/CONTRACT.md)
done: "<what this stage achieved, 1-3 lines>"
evidence:
  "<path>": { level: executed, how: "<the specific command and what it showed>" }
open:
  - { what: "...", class: OUT-OF-SCOPE, marker: "<path>:<line>", written: true }
swept: "2 markers / 2 in open; 7 changed / 7 evidenced"
next: "<the skill that should receive this, or none>"
```

- **`brief` travels whole and is not modifiable** — every field of
  `_coding/SIZING.md`'s brief, not a subset. The receiver may not rewrite any of
  them. Rewriting the brief downstream is the main route by which scope creeps,
  and it is invisible in the diff
- **The keys of `evidence` are the artifacts.** A file written and not keyed is
  a coverage hole arriving at a boundary
- **`open` carries a class and the class decides what happens.** `BLOCKED` and
  `UNVERIFIED` stop the chain and go back to the human; `DEFERRED` and
  `OUT-OF-SCOPE` travel as record, so the receiver learns what was already
  decided against rather than rediscovering it
- **`written` says whether the `#TODO(agent):` marker is in the tree yet.**
  A report-only skill sets it `false` and names where the marker belongs; the
  first receiver holding `Edit` or `Write` places it and flips the flag
  (`_coding/CONTRACT.md` § Residuals)
- Pass the change in state, not the working log. Reasoning does not travel

## What the receiver checks before starting

1. Is a whole `brief` attached, with every field present? A pointer to one is
   not one, and a subset is a brief that lost a constraint in transit
2. Does `open` hold a `BLOCKED` or `UNVERIFIED`? Hand back to the human
3. Does every key of `evidence` exist on disk, and is every level above `asserted`?
4. Do `swept` and `evidence` agree, and does every marker counted appear in
   `open`? A coverage claim that does not add up is no coverage
5. Is any `open` entry `written: false`? If you hold `Edit` or `Write`, placing
   those markers is part of your run
6. Is any `inspected` level missing its reason? That is `asserted` renamed
7. Does the work about to start fall under the brief's `excludes`?

## Send-backs

A send-back **names the check that failed and the field it failed on**.
Without that, the same handoff returns unchanged and the round trip bought
nothing.

**After two round-trips on the same handoff, hand back to the human.** Being
rejected twice points at the brief or at how the work was divided, not at the
implementation.
