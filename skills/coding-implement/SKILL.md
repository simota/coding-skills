---
name: coding-implement
description: "Writing working code: a feature, an endpoint, a screen, business logic, a CLI, an integration, a dependency upgrade, or performance work. Use when the shape is settled and code must exist."
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---
<!-- coding:contract -->

## Owns

Turning a settled shape into code that runs — new behaviour, changed behaviour,
and the wiring between them, with checks that prove the change. Ownership of
adjacent work is defined in `registry/capabilities.yaml`.

## Before starting

- **Find where this is already done.** One precedent in the codebase outranks
  any general best practice. Follow its shape, including choices you would have
  made differently. **The exception is a precedent that is unsafe or wrong** —
  an injection, a missing authorisation check, a swallowed error, a race. Copy
  the shape, fix the flaw in the copy, and report that the original carries it
  (`_coding/VALUES.md` §4)
- **For a defect, does the cause fit in one sentence?** If not, stop: this is
  `coding-debug`'s work, and implementing against a guessed cause produces a
  second bug on top of the first
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

- **Here the tie usually goes to §4 the existing shape over the better shape**,
  with its carve-out — a precedent that is unsafe or wrong is not copied

| Situation | How to proceed |
|---|---|
| A similar implementation exists | Read it fully, then match its shape. Do not introduce a second idiom |
| No precedent anywhere | Get the thinnest end-to-end path running first, then widen |
| The change spans more than about three files | Split it into steps that each leave the tree green |
| The code meets something you do not control — network, filesystem, another service, user input | [boundaries](playbooks/boundaries.md) |
| Tempted to add a dependency | Check the standard library and current dependencies first. Weigh install, upgrade, audit, and supply chain against the lines saved |
| Nothing runs end to end yet, or progress feels fast and unverifiable | [traps](playbooks/traps.md) |
| The change would also tidy something nearby | Do not. Behaviour change and cleanup in one diff is unreviewable — mark it and hand it to `coding-refactor` |
| A test fails and the quickest fix is to change the test | Establish which is wrong first. Changing the test to match the code deletes the only evidence you had |
| A claim here would be expensive to get wrong | [refute](refute.py) — put it to the engines that did not make it, asked to break it rather than to agree. Unrefuted is n engines finding nothing, never proof |
| About to run it for the first time | **Predict the observable** — the status code, the value written, the line logged. Where the prediction cannot be written, the spec has a hole, and it is cheaper to find it here |
<!-- deliver:values -->
- Ties break by `_coding/VALUES.md`, read top to bottom: honesty over speed ·
  mechanism over intent · subtraction over addition · the existing shape over
  the better shape · what lasts over what helps today · the human decides what,
  the agent decides how. Against all of them: **a harness that is correct and
  avoided has failed** — when the ceremony costs more than the change, say so
  rather than performing it
<!-- /deliver:values -->

## Always / Never

- Always: get permission first for anything irreversible, anything that leaves
  the machine (push, deploy, send, publish), anything touching secrets or
  credentials, and any change spanning ten or more files. **The only exception
  is one substitution applied identically everywhere** — reversible, in scope,
  or checkable by a script you wrote are not exceptions
- Always: match the surrounding naming, error handling, and level of abstraction
- Always: build the means of checking the change alongside the change. A change
  with no way to run it gets split into one that can be run
- Always: handle the failure routes you decided to handle, and leave the ones
  you decided not to as a deliberate, stated choice
- Never: guard against states that cannot occur. Trust internal callers and
  framework guarantees; validation belongs where data actually arrives from
  outside — a user, a network, another system
- Never: swallow an exception, silence a warning, widen a type to `any`, or pass
  `--no-verify` to make a failure disappear. The failure is the information
- Never: leave commented-out code, a stray debug print, or a `TODO` without the
  `#TODO(agent):` class marker
- Never: write a comment that says what the line under it already says. Cover it
  and read the code: nothing lost, delete it; something lost, rename or extract
  until the code says it. A comment carries the why, never the what

## Verify with

Confirm by running it — the test, the build, the request, the program (evidence:
`executed`). Reading the diff back is `inspected` and supports completion only
where nothing can be run, with the reason stated.

- **Achievement requires every axis the brief agreed.** Judged on one oracle,
  there is always an axis that can be declared satisfied
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

Every acceptance criterion is met, the change has been observed working rather
than reasoned about, and the sweep balances.
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
