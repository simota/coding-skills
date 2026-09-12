---
name: coding-refactor
description: "Changing structure while behaviour stays identical: extraction, renaming, duplication, dead code, module boundaries, and mechanical migration. Use when correct code is hard to work with."
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---
<!-- coding:contract -->

## Owns

Changing how code is organised without changing what it does — extracting,
inlining, renaming, deduplicating, deleting the unused, moving things to where
they belong, and applying one mechanical substitution across a codebase.
**Observable behaviour before and after must be identical**, including error
messages, ordering, and timing that anything depends on.

## Before starting

- **Name the specific difficulty this removes.** "Cleaner" is not a goal;
  "this function is edited on every feature and nobody can tell which branch
  applies" is. A refactor with no named difficulty is churn with a merge conflict
- **Find the safety net before touching anything.** Which tests cover this? Run
  them and confirm green *now*. If nothing covers it, that is the first piece of
  work, not an afterthought ([safety-net](playbooks/safety-net.md))
- **Confirm the code is correct.** Refactoring around a bug bakes it in and
  hides where it lives. A defect found first goes to `coding-debug`
- **Here `T0`** is a rename in one file; a module split is not, and a ten-file
  sweep needs permission
- Every `T1`/`T2` run returns a handoff (`_coding/HANDOFF.md` — seven receiver
  checks); a `T0` returns one line and none. Owner unclear? `_coding/ROUTING.md`
<!-- deliver:sizing -->
- **Size it before anything else**, first match wins. `T0` — one skill owns it,
  reversible, under three files, acceptance in one sentence: act and report in
  one line, **no brief, no handoff**. `T1` — a `T0` condition fails: settle the
  brief first. `T2` — two or more skills own parts of it: route it. `T0` drops
  the paperwork, never the evidence. Mis-sized mid-run means re-sizing and saying so
- **A dialogue comes first** when the deliverable's shape is not uniquely
  determined, acceptance does not fit in one sentence, the request carries a
  word with no achievement condition ("improve", "clean up"), or the work is
  expensive to undo. Reading to find out is not executing. `excludes` may not be
  empty and execution waits on an empty `open_questions` (`_coding/SIZING.md`)
- **A term with two meanings, or a concept with two names, is a question, never
  a silent choice** — one question with its default, the answer into the
  brief's `terms` and `.agents/glossary.md`, and the glossary's names only from
  then on (`_coding/SIZING.md` § Terms)
<!-- /deliver:sizing -->
<!-- deliver:predict -->
- **Register the prediction before the run.** Before the edit: what will be
  run, and what observable result changes — a named test, an exit code, a value
  at a path. After it, report `hit`, `miss`, or `void` (it turned out
  unobservable). **A `miss` costs nothing; an unrecorded `miss` costs the run.**
  Two consecutive misses in one area mean the model of it is wrong: stop editing
  and read. `executed` with nothing registered supports "it ran", never "it
  works because X" (`_coding/PREDICTION.md`)
<!-- /deliver:predict -->

## Decide first

- **Here the tie usually goes to §4 the existing shape over the better shape** —
  two idioms cost every future reader more than one mediocre idiom

| Situation | How to proceed |
|---|---|
| Choosing what move to make | [moves](playbooks/moves.md) — pick the smallest one that removes the named difficulty |
| Nothing covers the code | [safety-net](playbooks/safety-net.md). Characterise current behaviour first, then refactor |
| A behaviour change is also wanted | Refactor first, verify, commit. Then change behaviour separately. Never in one diff |
| The refactor keeps growing | Stop at the first green point and commit. A half-finished restructuring is worse than either end state |
| Duplication found in three places | Check whether they are the same thing or three things that currently look alike. Wrong abstraction costs more than duplication |
| Code appears unused | Prove it: grep, dynamic dispatch check, then history. Then delete it — do not comment it out |
| The tests break during the refactor | The behaviour changed. Revert to green and take a smaller step — do not adjust the test |
| Someone else is working in these files | Coordinate or defer. A large refactor across an active branch is a merge conflict with a delay on it |
| A claim here would be expensive to get wrong | [refute](refute.py) — put it to the engines that did not make it, asked to break it rather than to agree. Unrefuted is n engines finding nothing, never proof |
| About to run the safety net | **Predict that it stays green and that nothing else moves.** A refactor whose honest prediction includes a changed output is not a refactor |
<!-- deliver:values -->
- Ties break by `_coding/VALUES.md`, read top to bottom: honesty over speed ·
  mechanism over intent · subtraction over addition · the existing shape over
  the better shape · what lasts over what helps today · the human decides what,
  the agent decides how. Against all of them: **a harness that is correct and
  avoided has failed** — when the ceremony costs more than the change, say so
  rather than performing it
<!-- /deliver:values -->

## Always / Never

- Always: run the tests before starting, and confirm they are green. A refactor
  begun on a red tree cannot be told apart from the thing that was already broken
- Always: take one move at a time, running the tests after each
- Always: keep the tree green at every commit
- Always: turn a comment that says what the next block does into that block's
  name — extract, rename, delete the comment. It changes no behaviour, so it is
  this skill's work. A comment carrying a why is left alone
- Always: get permission before any change spanning ten or more files. **The only
  exception is one substitution applied identically everywhere**
- Never: change behaviour. Not the return value in an edge case, not an error
  message, not the log format, not the iteration order, not the exception type.
  If any of those must change, this is `coding-implement`'s work
- Never: edit tests to make a refactor pass. The test is the invariant
- Never: mix a rename with a logic change in one commit — it makes the logic
  change invisible in review
- Never: introduce an abstraction for a second caller that does not exist

## Verify with

Behaviour preservation is proved by the same tests passing before and after,
run in the same session (evidence: `executed`). Where a mechanical
transformation is uniform, a diff review is `inspected` evidence and the entry
says why nothing could be run.

- **`DONE` here**: green before, green after, behaviour identical, sweep balances
- **Report what shrank.** Lines removed, branches removed, call sites
  consolidated, dependencies dropped. A refactor that only moves code around and
  removes nothing should say so, and justify itself on the named difficulty alone
<!-- deliver:report -->
- **Grade every claim**: `executed` (it was run) supports completion;
  `inspected` (read back) only where nothing could be run and the entry says
  why; `asserted` never does. **The unit is the file written to** — each carries
  a grade or sits in the residuals as `UNVERIFIED`, and a file in neither is how
  an unverified change leaves
- **`status`**: `DONE` (every criterion met, every file evidenced, zero
  `UNVERIFIED`) / `PARTIAL` / `BLOCKED` (say what was tried)
- **Every residual is `BLOCKED` / `OUT-OF-SCOPE` / `DEFERRED` / `UNVERIFIED`**
  and appears in the handoff's `open`; a run holding `Edit` or `Write` also
  leaves a `#TODO(agent):` marker carrying that class. The report closes and is
  gone; the marker stays
- **Never omit the sweep** — markers in this run's diff against `open`, files
  written against files evidenced: `swept, 0 markers; 7 changed / 7 evidenced`.
  While either pair disagrees the status is not `DONE` (`_coding/CONTRACT.md`)
<!-- /deliver:report -->

## Done when

The named difficulty is gone, the same tests pass unchanged, the diff contains
no behaviour change, and every commit in the sequence is independently green.
<!-- deliver:surface -->
- **Say what the moment needs.** Start: what will be done and what is excluded.
  Mid-run: a line when the reader must act — a divergence from what was agreed,
  a path found blocked, work that would grow the scope — or when the run changes
  course; tool calls are already visible and are not replayed. A question names
  the decision it unblocks and the default taken if nobody answers
- **End with the answer in one line** — status and what changed; then the sweep line, then
  one line per residual a human must decide, then what is next. A reader who stops after
  the first line has the result
- **The handoff is the record, the report is the view.** The brief, the per-file grades and
  the working log travel in the handoff and are shown when asked
- **Sized to the tier**, the deliverable linked, never pasted: `T0` is the answer
  line, `T1` adds evidence and residuals, `T2` adds what is next. Trimming cuts
  what the reader already has — request, file list, path taken (`_coding/REPORT.md`)
- **Not bigger than it is.** The requested scope is the deliverable; thought
  goes deeper into the one thing asked, never wider. **A real problem is the
  exception** — something that would break, is unsafe, or rests on a false
  premise is explained in full (`_coding/REPORT.md`)
<!-- /deliver:surface -->
