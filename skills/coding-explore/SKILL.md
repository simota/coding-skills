---
name: coding-explore
description: "Reading a codebase without changing it: where something lives, how a path works, what a change touches, blast radius, structure, and what the history says. Use before touching unfamiliar code."
allowed-tools: Read, Grep, Glob, Bash
---
<!-- coding:contract -->

## Owns

Answering **where**, **how**, and **what breaks** about code that already
exists — locating a feature, tracing a value from entry to storage, mapping the
blast radius of a proposed change, and reading history for why something is the
way it is. This skill produces understanding, never a diff.

## Before starting

- **Write the question down as one sentence before searching.** "How does X
  work" is not a question; "which code decides whether X is retried" is. An
  unbounded exploration returns a tour, and a tour answers nothing
- **Decide what would end the search.** A file path, a function name, a call
  chain, a commit — name the artifact that will constitute the answer
- **Here `T0`** is one obvious lookup answered in a line; several areas means
  ordering the passes
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

## Decide first

- **Here the tie usually goes to §1 honesty over speed** — a claim you did not
  confirm is a guess, and it is reported as one

| Situation | How to proceed |
|---|---|
| You know a name, symbol, or string | Grep for it first. The cheapest search that could work runs first |
| You know only the behaviour | [search](playbooks/search.md) — work inward from the entry point the user can see |
| The question is "what breaks if I change this" | [blast-radius](playbooks/blast-radius.md) |
| The question is "why is it like this" | [history](reference/history.md) — `-S` and `-G` search different axes, and `..`/`...` invert between `log` and `diff` |
| Three searches returned nothing | The vocabulary is wrong. Find the entry point and read outward instead of guessing more names |
| The answer looks obvious after one file | Confirm with a second, independent signal before reporting it |
| Framework or generated code dominates the result | Exclude it by path and search again. Vendored code answers questions about the vendor |
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

- Always: report **file:line**, never a paraphrase of where something is
- Always: distinguish what was read from what was inferred. "Called from three
  places" is a fact; "probably only used by the admin path" is a guess and is
  labelled one
- Always: state coverage honestly — which directories were searched, which were
  not, and what a dynamic call or reflection could be hiding
- Never: edit, format, or "fix while I'm here". This skill is read-only, and
  finding something wrong does not authorise changing it — mark it and hand it back
- Never: transmit code or findings off the machine. Read-only is not permission
  to publish
- Never: report a call graph derived from names alone. A name match is a
  candidate; a read confirmation is a fact

## Verify with

An answer is proved by the reader being able to check it: every claim carries a
`file:line` a reader can open (evidence: `inspected`), and a claim about
runtime behaviour is `executed` — the test, the script, or the program was run.

- This skill holds no `Edit`/`Write`, so residuals go in the handoff's `open`
  with the `file:line` a marker belongs at — never as a write
- **`DONE` here**: the question answered, every claim anchored to a path
- **Say what you did not cover.** An exploration reported without its boundary
  reads as exhaustive, and the next person builds on a gap they cannot see
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

The one-sentence question has an answer anchored to specific lines, the
confidence in it is stated, and the parts of the codebase that were not looked
at are named.
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
