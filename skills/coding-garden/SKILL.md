---
name: coding-garden
description: "Garden pass before work starts: tree health, doc drift, silent checks, red tests, over-implementation, unnecessary comments, outdated dependencies. Report-only, each finding routed to its owner."
allowed-tools: Read, Grep, Glob, Bash
---
<!-- coding:contract -->

## Owns

The state of the tree as it stands, read before new work goes on top of it:
whether the checks still run and still cover what they claim to, whether the
docs still say what the code does, whether the architecture still keeps its
declared rules, and what has grown that nothing needs: dead code, duplicates,
comments that bind nobody, dependencies left behind. It reports and routes.
Every finding names the skill that takes it, and finding something wrong never
authorises fixing it here. Ownership of adjacent work is defined in
`registry/capabilities.yaml`.

## Before starting

- **Read the host's gate, then run it first**: its result decides the pass. A
  step writing in the checkout runs in a copy, one changing state outside it (a
  database, a service) only on a go-ahead; a step left unrun is reported unchecked
- **Record the tree that was read**: the commit, and whether the status was
  clean. A finding about uncommitted edits is a finding about someone's work in
  progress, and it is reported as that
- **Scope by the work about to start**, not by the whole repository. Scope sets
  where the pass runs, never its tier: a pass that routes findings is `T1`, and
  `T0` is only the gate run, asked for alone and answered in one line
- **Nothing leaves the machine without a go-ahead.** Asking a package registry
  what is current sends the dependency list. Ask before the pass; without a
  yes, dependencies go in the brief's `excludes` and the report names them
- A handoff received is checked first (`_coding/HANDOFF.md`, seven receiver
  checks); every `T1`/`T2` run returns one, a `T0` one line. Owner unclear? `_coding/ROUTING.md`
<!-- deliver:sizing -->
- Size it before the first write, first match wins. `T0`: one skill owns it,
  reversible, under three files, acceptance in one sentence. Act and report in
  one line; it needs no brief and no handoff. `T1`: a `T0` condition fails, so
  settle the brief first. `T2`: two or more skills own parts of it, or it spans
  phases, so route it. `T0` drops the paperwork, never the evidence. Mis-sized: re-size and say so
- A dialogue comes first when the deliverable's shape is not uniquely
  determined, acceptance does not fit in one sentence, the request carries a
  word with no achievement condition ("improve", "clean up"), or the work is
  expensive to undo. Reading to find out is not executing. `excludes` may not be
  empty and execution waits on an empty `open_questions` (`_coding/SIZING.md`)
- A term with two meanings, or a concept with two names, is a question, never
  a silent choice: one question with its default, the answer into the brief's
  `terms` (at `T1`+ also the host project's `.agents/glossary.md`, if this run can
  write it, else `open`), and only those names from then on (`_coding/SIZING.md`)
<!-- /deliver:sizing -->

## Decide first

- Here the tie usually goes to §2 mechanism over intent: a finding a command
  produced outranks one a reading produced, and a category with no command is
  reported as unchecked, never filled in by impression

| Situation | How to proceed |
|---|---|
| Starting a pass | [sweep](playbooks/sweep.md): the order, what blocks the start and what is only recorded, and which skill takes each finding |
| Deciding what can check a category mechanically | [checks](playbooks/checks.md): structure first, then a declared rule a tool enforces, then a reading, which proves least |
| The gate is red on the untouched tree | Read which check failed. It fails in the area about to change: stop the pass, and that is the report's first line, routed to `coding-debug`. It is absent or cannot run (no script, a tool not installed): stop, routed to `coding-setup`. It fails only elsewhere: record that with its area and run the remaining steps |
| A check exists and passes on anything | A silent gate is worse than a missing one. It blocks the start like a red one and goes to `coding-setup` |
| The host has no tool for a category | Report it unchecked, with the kind of tool that would check it. Adopting one adds a dependency, so it goes to `coding-setup` and the human decides |
| The same kind of finding was fixed before | Search the history for the earlier fix. A second occurrence is also sent to be closed for good: [sweep](playbooks/sweep.md) § The second sighting says by whom |
| A finding rests on judgement: an abstraction nothing needs, prose that reads out of date | `inspected` at best. It goes in as a Question for the human, who decides whether it is work, or it is dropped |
| A claim here would be expensive to get wrong | [refute](refute.py). Ask first: it sends the claim and the code it cites to the other engines. Run this skill's `refute.py` with `--running <engine>` (claude, codex or agy) and the path to a JSON file listing `{id, claim, evidence?, where?}`; a non-zero exit means at least one claim went unchecked, or the input or `--running` was refused (stderr says which). Read each verdict. `STANDS` is n engines finding nothing, never proof |
<!-- deliver:values -->
- Ties break by `_coding/VALUES.md`, read top to bottom: honesty over speed ·
  mechanism over intent · subtraction over addition · the existing shape over
  the better shape · what lasts over what helps today · the human decides what,
  the agent decides how. Against all of them, a harness that is correct and
  avoided has failed: when the ceremony costs more than the change, say so
  rather than performing it
<!-- /deliver:values -->

## Always / Never

- Always: one finding, one owner. The routing table in
  [sweep](playbooks/sweep.md) names it; a finding with two owners is two findings
- Always: give each finding the command that produced it and the output or
  `file:line` it rests on, so its owner starts from evidence, not a description
- Always: keep what blocks the start apart from what is only recorded. An
  outdated dependency is a line on a list; blocking on it is a start that never comes
- Always: order the fixes before the new work, one commit each and never
  inside its diff. A cleanup inside a feature is unreviewable
- Never: edit, install, upgrade, format, or regenerate in the tree. A generator
  run to detect drift writes files: run it in a copy of the checkout made
  outside it, installed dependencies included, or report the category unchecked
- Never: pass a tool's raw output on as findings. Each line is read,
  deduplicated, and graded; a thousand warnings of one kind are one finding
  about the threshold
- Never: run a host command that changes state outside the checkout (a
  database, a service, an account) without a go-ahead for this pass

## Verify with

A finding is proved by its owner being able to reproduce it: each carries the
command that produced it (evidence: `executed`) or the `file:line` it was read
at (`inspected`, with why nothing could be run).

- Findings travel in `done` with list, owner, rank and evidence, never as
  `BLOCKED`; `open` holds residuals at the `file:line` a marker belongs, `written: false`
- **`DONE` here**: the gate's state is known, every category in scope was run or
  is a finding saying why it could not be, and every finding has one owner. A
  pass stopped at the gate is `PARTIAL`, each step not run `DEFERRED` until it is green
- Writing nothing, the sweep reads `0 changed / 0 evidenced`, and the status of
  the tree read back after the pass matches the one recorded before it
<!-- deliver:report -->
- Grade every claim: `executed` (it was run) supports completion;
  `inspected` (read back) only where nothing could be run and the entry says
  why; `asserted` never does. The unit is the file written to: each carries
  a grade or sits in the residuals as `UNVERIFIED`, and a file in neither is how
  an unverified change leaves
- `status`: `DONE` (every criterion met, every file evidenced, zero
  `UNVERIFIED`, `BLOCKED` or `DEFERRED` residuals) / `PARTIAL` / `BLOCKED` (say what was tried)
- Every residual is `BLOCKED` / `OUT-OF-SCOPE` / `DEFERRED` / `UNVERIFIED`
  and appears in the handoff's `open` (a `T0`: in its line); a run that may write
  that file also leaves a `#TODO(agent):` marker carrying that class. The report
  closes and is gone; the marker stays
- Never omit the sweep: markers in this run's diff against `open`, files
  written against files evidenced (`swept, 0 markers; 7 changed / 7 evidenced`).
  While either pair disagrees the status is not `DONE` (`_coding/CONTRACT.md`)
<!-- /deliver:report -->

## Done when

The gate's state on the untouched tree is known, each category in scope has
been run or reported unchecked with its reason, and every finding sits on one
of two lists, blocks the start or recorded, with the skill that takes it.
<!-- deliver:surface -->
- Say what the moment needs. Start: what will be done and what is excluded.
  Mid-run: a line when the reader must act (a divergence from what was agreed,
  a path found blocked, work that would grow the scope) or when the run changes
  course; tool calls are already visible and are not replayed. A question names
  the decision it unblocks and the default taken if nobody answers
- End with the answer in one line: status and what changed; then the sweep
  line, then one line per residual a human must decide, then what is next. A
  reader who stops after the first line has the result
- The handoff is the record, the report is the view. The brief, the per-file
  grades and the `open` list travel in the handoff and are shown when asked
- Sized to the tier, the deliverable linked, never pasted: `T0` is one line
  with the sweep folded in, `T1` adds evidence and residuals, `T2` what is next.
  Trimming cuts what the reader already has: request, files, path (`_coding/REPORT.md`)
- Not bigger than it is. The requested scope is the deliverable; thought
  goes deeper into the one thing asked, never wider. A real problem is the
  exception: something that would break, is unsafe, or rests on a false
  premise is explained in full (`_coding/REPORT.md`)
<!-- /deliver:surface -->
