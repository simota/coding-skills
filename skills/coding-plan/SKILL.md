---
name: coding-plan
description: "Deciding the shape before code exists: interfaces and signatures, the data model, error and state design, build order, and the trade-off between options. Use when the approach is not obvious."
allowed-tools: Read, Grep, Glob, Bash, Write
---
<!-- coding:contract -->

## Owns

Choosing **what shape** the code takes before any is written — the interfaces
and their contracts, how state and data are modelled, which failures are
represented and which are not, what gets built in what order, and which of
several viable approaches to take and why. It produces a decision with its
reasoning, and at most a written plan. It does not implement.

## Before starting

- **A plan is only worth writing when the shape is not uniquely determined.**
  If one obvious approach exists and the acceptance fits in a sentence, this
  skill is overhead — hand straight to `coding-implement`
- **Read the neighbours first.** How this codebase already models similar things
  outranks how it should be modelled. Planning without reading produces a design
  the codebase rejects
- **Name the constraints that are actually fixed** — existing data, a deployed
  client, a deadline, a dependency that cannot change. A plan that ignores one
  of these is fiction
- **A plan is `T1` at minimum**, because by definition the shape was not obvious
- **The dialogue is mandatory here**, whatever the size of the change
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

- **Here the tie usually goes to §3 subtraction over addition** — the option
  that removes something beats the one that adds a flag to guard it

| Situation | How to proceed |
|---|---|
| The codebase already solves something similar | Follow that shape. A second idiom costs every future reader, forever |
| Two or more approaches are viable | [options](playbooks/options.md) — name them, price them, recommend one |
| The design centres on an interface others will call | [interfaces](playbooks/interfaces.md) |
| It touches persisted data or a public format | Plan the migration and the rollback **before** the feature. Data outlives code |
| The work is large or has an unclear middle | [sequencing](playbooks/sequencing.md) — get a thin end-to-end path first |
| A requirement is ambiguous | Ask. One question now is cheaper than a plan built on a guess |
| You are tempted to design for a future caller | There is one caller. Design for it; add the seam when the second arrives |
| The plan is growing past a page | It is two pieces of work. Split it and say where the seam is |
| A claim here would be expensive to get wrong | [refute](refute.py) — put it to the engines that did not make it, asked to break it rather than to agree. Unrefuted is n engines finding nothing, never proof |
<!-- deliver:values -->
- Ties break by `_coding/VALUES.md`, read top to bottom: honesty over speed ·
  mechanism over intent · subtraction over addition · the existing shape over
  the better shape · what lasts over what helps today · the human decides what,
  the agent decides how. Against all of them: **a harness that is correct and
  avoided has failed** — when the ceremony costs more than the change, say so
  rather than performing it
<!-- /deliver:values -->

## Always / Never

- Always: state what the plan **excludes** as explicitly as what it includes
- Always: give each option a cost in the terms that matter here — files touched,
  reversibility, who has to know about it, what it forecloses
- Always: name the one assumption that, if wrong, invalidates the plan, and say
  how to check it cheaply before building
- Always: make a recommendation. A survey of options with no recommendation
  hands the work back rather than doing it
- Never: write implementation code. A signature or a schema sketch is the plan;
  a working function is `coding-implement`'s
- Never: plan around a fact that could have been looked up. Read the file
- Never: introduce an abstraction whose only justification is a hypothetical
  second use

## Verify with

A plan is checked against the code it will live in, not against itself: every
claim about existing behaviour is anchored to `file:line` (evidence:
`inspected`), and any load-bearing assumption is proved by running something
(evidence: `executed`) or is declared unproved.

- This skill holds `Write` but not `Edit`, so a residual inside an existing file
  goes in the handoff's `open` and in the plan document — never as an in-place edit
- **`DONE` here**: decision made, grounds stated, exclusions named
- **The plan names its own falsification.** "This is wrong if X" is what makes
  a plan checkable rather than persuasive
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

One approach is chosen, its cost and what it forecloses are stated, the
rejected options and the reason are recorded, the exclusions are explicit, and
the first buildable step is small enough to start immediately.
