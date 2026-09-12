---
name: coding-debug
description: "Diagnosing something already broken: reproduce the bug, isolate and prove the root cause, then fix it minimally. Use for a regression, a failing suite, or any why is this broken question."
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---
<!-- coding:contract -->

## Owns

Getting from a symptom to a proved cause, and then to the smallest fix that
removes it. The regression test that keeps it gone belongs to `coding-test`,
though this skill writes the failing case that proves the diagnosis.

## Before starting

- **Reproduce it before reading anything.** A bug you cannot trigger cannot be
  proved fixed, and every hypothesis about it is unfalsifiable
  ([reproduce](playbooks/reproduce.md))
- **Write down the symptom precisely**: what was expected, what happened, and
  the exact input, environment, and version. "It's broken" is a report, not a symptom
- **Establish the baseline.** Does it fail on a clean checkout? On the last
  release? A failure that predates the change under suspicion is a different bug
- **Here `T0`** is a one-line cause with a one-line fix; a bisect, or anything
  spanning modules, is not
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

- **Here the tie usually goes to §2 mechanism over intent** — a cause you cannot
  demonstrate at will is a correlation

| Situation | How to proceed |
|---|---|
| It cannot be reproduced yet | [reproduce](playbooks/reproduce.md). Everything else is premature |
| It worked before and does not now | [bisect](playbooks/bisect.md) — find the commit, then read it |
| It reproduces sometimes | Do not chase it by rerunning. Find what differs between runs — order, time, concurrency, leftover state |
| You have a hypothesis | Design the observation that would **disprove** it, and run that. A confirmation-only test confirms anything |
| Two changes were made to test one hypothesis | Revert one. Two variables means the next result is uninterpretable |
| The stack trace points at library code | The cause is almost always in the argument you passed. Read the call site before the library |
| The fix is not obvious after the cause is proved | Hand the shape decision to `coding-plan` rather than improvising in a hot file |
| The same failure has been chased twice with no progress | Stop and state what is known, what was ruled out, and what would settle it |
| A claim here would be expensive to get wrong | [refute](refute.py) — put it to the engines that did not make it, asked to break it rather than to agree. Unrefuted is n engines finding nothing, never proof |
| The fix is written and about to be run | **Predict what the reproduction does now** — which assert, what output — before running it. A fix confirmed by a run nobody predicted is a fix nobody can explain |
<!-- deliver:values -->
- Ties break by `_coding/VALUES.md`, read top to bottom: honesty over speed ·
  mechanism over intent · subtraction over addition · the existing shape over
  the better shape · what lasts over what helps today · the human decides what,
  the agent decides how. Against all of them: **a harness that is correct and
  avoided has failed** — when the ceremony costs more than the change, say so
  rather than performing it
<!-- /deliver:values -->

## Always / Never

- Always: prove the cause before fixing — the mechanism from input to wrong
  output, stated in one sentence, and demonstrated
- Always: change one thing at a time, and observe after each change
- Always: after the fix, confirm the original reproduction now passes **and**
  that it failed before the fix. A fix never seen to change a failing result is
  a guess with better formatting
- Always: check whether the same cause exists elsewhere in the codebase — the
  copied pattern is the reason a fix does not take
- Never: fix a symptom you cannot explain. A change that makes the failure
  disappear without a mechanism has moved it, not removed it
- Never: change a test to match broken behaviour, delete a failing assertion, or
  add a retry to make a flake pass. That deletes the evidence
- Never: leave debug instrumentation, added logging, or a loosened timeout in
  the diff
- Never: leave a comment narrating the fix. What changed is the commit message's
  job; the code keeps only the why that outlived the bug
- Never: expand the fix into nearby improvements. The diff must be small enough
  to be obviously about this bug

## Verify with

The reproduction is the oracle: it failed before, it passes after, and both were
observed in the same session (evidence: `executed`). Anything else about the
cause is a hypothesis.

- **`DONE` here**: cause proved, fix verified, sweep balances
- **State the blast radius of the cause**: everywhere else this pattern occurs,
  and whether data already written is affected. A bug that corrupted data is not
  fixed when the code is fixed
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

The mechanism is stated in one sentence, the reproduction that failed now
passes, the same cause elsewhere has been searched for, and any damage already
done is named.
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
