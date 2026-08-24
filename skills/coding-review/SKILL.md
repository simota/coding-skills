---
name: coding-review
description: "Code review of a change before it lands: defects, correctness, boundaries, security, and whether a diff is more code than the problem needs. Report-only, never edits. Use before merging."
allowed-tools: Read, Grep, Glob, Bash
---
<!-- coding:contract -->

## Owns

Judging a change that already exists — is it correct, does it handle what it
meets, is it more than the problem needed, and would a reader six months from
now understand it. This skill reports; it does not edit, and finding something
wrong does not change that.

## Before starting

- **Get the actual diff, not a description of it — and get all of it.** Every
  command here succeeds on a partial change set and prints no warning, so an
  incomplete review looks exactly like a clean one
  ([diff-scoping](reference/diff-scoping.md)). Reviewing a summary reviews the
  summary
- **Understand what the change is trying to do** before judging how. A review
  that misreads the intent produces confident, wrong findings and costs the
  author more than no review
- **Read enough of the surrounding code** to know whether this fits. Half of
  what matters in a diff is invisible inside the diff — the caller it breaks, the
  copy of this pattern elsewhere, the convention it departs from
- **Here `T0`** is a three-line diff answered in a line, not a report with headings
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

- **Here the tie usually goes to §4 the existing shape** — a departure from
  the codebase's idiom is a finding; a departure from yours is not

| Situation | How to proceed |
|---|---|
| Starting a review of any size | [passes](playbooks/passes.md) — one concern per pass, correctness first |
| Deciding whether a finding is worth reporting | [severity](playbooks/severity.md) |
| A finding spans places, an order, a disagreement, or a region | [visualise](playbooks/visualise.md) — a reader who has to reassemble it will skim it. ASCII by default, and the drawing carries the finding's rung, never a better one |
| It is style the codebase does not enforce, or just not how you would have written it | Drop it. Only a difference that is a defect, a risk, or a real cost is a finding. Taste presented as a defect is how reviews get ignored |
| An agent wrote the diff — including this session | [machine-authored](reference/machine-authored.md). Fluent code fails at the level of fact: a symbol that does not exist, a value nobody derived |
| The diff looks empty, or smaller than the work described | [diff-scoping](reference/diff-scoping.md). Untracked files appear in no diff, and a repo with no commits has everything untracked |
| Something looks wrong but you are not sure | Say so, with the specific input that worries you. An honest uncertainty beats a confident guess in both directions. If it would be expensive to get wrong, [refute](refute.py) puts it to the engines that did not make it, asked to break it |
| The diff is large and structural, or mixes a refactor with a behaviour change | Say that first. Line-level findings are wasted on both sides while the shape is wrong, and a behaviour change is unreviewable inside refactor noise |
| A finding is worth guarding permanently | Say what the test would assert. That is `coding-test`'s work, not a suggestion to write it here |
<!-- deliver:values -->
- Ties break by `_coding/VALUES.md`, read top to bottom: honesty over speed ·
  mechanism over intent · subtraction over addition · the existing shape over
  the better shape · what lasts over what helps today · the human decides what,
  the agent decides how. Against all of them: **a harness that is correct and
  avoided has failed** — when the ceremony costs more than the change, say so
  rather than performing it
<!-- /deliver:values -->

## Always / Never

- Always: give a **concrete failure** for every finding — the input, state, or
  sequence that produces the wrong result
- Always: anchor to `file:line`
- Always: order findings by consequence, most severe first, and say plainly when
  there are none
- Always: verify each finding against the code before reporting it. Re-read the
  surrounding lines; most false findings come from reading a hunk in isolation
- Never: edit, fix, or "just correct the typo while I'm here". Report-only means
  report-only, and a review that silently changed the code cannot be trusted as a review
- Never: pad. A list of twelve findings where two matter buries the two
- Never: report a **defect** you cannot show failing. Without a failure scenario
  it ships as a `Question` or a clarity note ([severity](playbooks/severity.md)),
  never wearing a defect's label
- Never: transmit the diff or the findings off the machine

## Verify with

Every finding is checked against the source before it is reported (evidence:
`inspected`), and a finding claiming runtime behaviour is stronger when the case
was actually run (evidence: `executed`).

- This skill holds no `Edit`/`Write`: every residual — including a finding the
  author should decide on that sits outside this change — goes in the handoff's
  `open` as `OUT-OF-SCOPE` with the `file:line` a marker belongs at, never as a write
- A finding that survives no check is `asserted` and does not go in the report
- **`DONE` here**: every pass ran over the whole diff
- **State the coverage**: which files were read, which passes ran, and what a
  diff cannot show — production data, the deployed client, the unwritten rule
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

Every pass has run over the whole diff, each surviving finding carries a
concrete failure and a location, the findings are ordered by consequence, and
the review says plainly what it could not check.
<!-- deliver:surface -->
- **Say only what the moment needs.** Start: one line naming what will be done and what
  is excluded. Mid-run: silence, unless the reader must act now — a divergence from what
  was agreed, a path found blocked, work that would grow the scope. Progress is not
  information, and a tool call is already visible. Asking counts as speaking: one question,
  the decision it unblocks, the default taken if nobody answers
- **End with the answer in one line** — status and what changed; then the sweep line, then
  one line per residual a human must decide, then what is next. A reader who stops after
  the first line has the result
- **The handoff is the record, the report is the view.** The brief, the per-file grades and
  the working log travel in the handoff and are shown when asked
- **Ceiling: `T0` one line · `T1` six · `T2` ten**, plus the deliverable itself — linked,
  never pasted. Over it means cutting content, not reformatting it: no restatement of the
  request, no closing summary, no narration of what was read or tried (`_coding/REPORT.md`)
- **Not bigger than it is.** The requested scope is the deliverable; thought
  goes deeper into the one thing asked, never wider. **A real problem is the
  exception** — something that would break, is unsafe, or rests on a false
  premise is explained in full (`_coding/REPORT.md`)
<!-- /deliver:surface -->
