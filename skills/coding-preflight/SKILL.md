---
name: coding-preflight
description: "Preflight of an implementation plan before it is built: visualise every view as a diagram — dependencies, data flow, sequence, failure paths — and hunt each design flaw to zero. Use on a written plan."
allowed-tools: Read, Grep, Glob, Bash, Write
---
<!-- coding:contract -->

## Owns

Making **all of a written plan visible** and attacking what the drawings show —
every view the plan implies, drawn from its own words and from the code it lands
in, then each view and each seam between two views hunted for the design flaw
it exposes, before a line is built. It produces the drawn plan and its flaws in
order of consequence. It does not decide the shape, revise the plan, or implement.

## Before starting

- **There is a written plan, or there is nothing to draw.** One that lives only
  in a conversation is written down first and confirmed; none at all is
  `coding-plan`'s. A drawing of a remembered plan is a drawing of a guess
- **Agree the rules before the first drawing** — what must always hold, in the
  reader's sentences: never charged twice, no row lost on rollback. A flaw is a
  rule broken; a hunt with no rules finds only taste
- **Open the code the plan lands in.** A box that claims to exist carries the
  `file:line` that was read; a box to be built is marked new
- **A sheet is never `T0`.** The one `T0` here is a plan of a single step,
  answered in a line: there is nothing to draw
- A handoff received is checked first (`_coding/HANDOFF.md` — seven receiver
  checks); every `T1`/`T2` run returns one. Owner unclear? `_coding/ROUTING.md`
<!-- deliver:sizing -->
- **Size it before the first write**, first match wins. `T0` — one skill owns it,
  reversible, under three files, acceptance in one sentence: act and report in
  one line, **no brief, no handoff**. `T1` — a `T0` condition fails: settle the
  brief first. `T2` — two or more skills own parts of it, or it spans phases:
  route it. `T0` drops the paperwork, never the evidence. Mis-sized: re-size and say so
- **A dialogue comes first** when the deliverable's shape is not uniquely
  determined, acceptance does not fit in one sentence, the request carries a
  word with no achievement condition ("improve", "clean up"), or the work is
  expensive to undo. Reading to find out is not executing. `excludes` may not be
  empty and execution waits on an empty `open_questions` (`_coding/SIZING.md`)
- **A term with two meanings, or a concept with two names, is a question, never
  a silent choice** — one question with its default, the answer into the brief's
  `terms` (at `T1`+ also the host project's `.agents/glossary.md`, if this run can
  write it, else `open`), and only those names from then on (`_coding/SIZING.md`)
<!-- /deliver:sizing -->

## Decide first

- **Here the tie usually goes to §2 mechanism over intent** — a plan that means
  to handle a failure and draws no path for it has not handled it

| Situation | How to proceed |
|---|---|
| Starting a preflight of any size | [views](playbooks/views.md) — which views this plan owes and the form of each. Every owed view is drawn before any is attacked |
| The views are drawn | [hunt](playbooks/hunt.md) — the premise, one attack per view, then the seams no single view shows |
| Writing up what was drawn | [sheet](playbooks/sheet.md) — one self-contained page a person can open: every view as a drawing, flaws flagged on the drawings and ranked in a register. Counts are counted from the finished page, never carried over from memory |
| The plan does not say what a view needs | Mark it `?` on the drawing and report the gap. Never fill it with what you would build — two implementers would fill it differently, and that is the flaw |
| Two views disagree about the same thing | The finding is at the seam. Show both sides; do not pick one |
| Two or more things change independently and a rule must hold in every order | Draw the chart from the plan. A plan carrying no exhaustive check of those orders has a flaw by that fact; the check itself is state design, `coding-plan`'s |
| A flaw rests on how existing code behaves | Run it — the smallest probe, in a scratch directory outside the repo. Not run, it is `Likely` at best |
| The fix is obvious | State the smallest change to the plan that removes the flaw, and stop. The judge is never the author |
| A flaw would be expensive to get wrong | [refute](refute.py) — ask first: it sends the claim, its `where` and its `evidence` to the other engines, so quote the plan lines the flaw rests on in `evidence`. Run this skill's `refute.py` with `--running <engine>` (claude, codex or agy) and the path to a JSON file listing `{id, claim, evidence?, where?}`; a non-zero exit means at least one claim went unchecked, or the input or `--running` was refused (stderr says which) — read each verdict. `STANDS` is n engines finding nothing, never proof |
| Nothing breaks | Say so plainly, with what was drawn and attacked. No flaws is a valid result; a padded list is not |
<!-- deliver:values -->
- Ties break by `_coding/VALUES.md`, read top to bottom: honesty over speed ·
  mechanism over intent · subtraction over addition · the existing shape over
  the better shape · what lasts over what helps today · the human decides what,
  the agent decides how. Against all of them: **a harness that is correct and
  avoided has failed** — when the ceremony costs more than the change, say so
  rather than performing it
<!-- /deliver:values -->

## Always / Never

- Always: draw every owed view before attacking any — the flaw is usually in
  the view nobody thought was needed
- Always: derive every mark from a plan line or a `file:line` that was opened
- Always: give each flaw of rank 1–3 the rule it breaks and the shortest path to
  the break, numbered on the drawing; a lower rank points at the mark it is about
- Always: label drawings in the reader's words, identifiers in the legend
- Never: edit the plan, or write code. This skill draws and reports
- Never: report a different design that is not broken. Taste is not a flaw
- Never: transmit the plan or its flaws off the machine without the human's
  go-ahead for this run — `refute` included

## Verify with

Every mark on a drawing is anchored — to the plan's own line, or to a
`file:line` that was opened (evidence: `inspected`) — and a flaw that rests on
what existing code does is proved by a probe that was run (evidence:
`executed`) or says it was not.

- This skill holds `Write` but not `Edit`: the sheet is a new file in the plan's
  own directory, named after it (a plan in no file: ask, default
  `docs/plans/<slug>.preflight.html`); a residual inside an existing file goes
  in the handoff's `open`
- **`DONE` here**: every owed view drawn, every view and seam attacked. A view
  left undrawn or unattacked is `PARTIAL`, and is listed as `DEFERRED`
- **State the coverage**: the views drawn, the views not owed and why, the
  rules checked, and what a plan cannot show — load, production data, the
  deployed client
- **The sheet is a snapshot of one plan, never kept current.** A revised plan is
  redrawn; a built one takes its sheet down with it (`_coding/CONTRACT.md`)
<!-- deliver:report -->
- **Grade every claim**: `executed` (it was run) supports completion;
  `inspected` (read back) only where nothing could be run and the entry says
  why; `asserted` never does. **The unit is the file written to** — each carries
  a grade or sits in the residuals as `UNVERIFIED`, and a file in neither is how
  an unverified change leaves
- **`status`**: `DONE` (every criterion met, every file evidenced, zero
  `UNVERIFIED`, `BLOCKED` or `DEFERRED` residuals) / `PARTIAL` / `BLOCKED` (say what was tried)
- **Every residual is `BLOCKED` / `OUT-OF-SCOPE` / `DEFERRED` / `UNVERIFIED`**
  and appears in the handoff's `open` (a `T0`: in its line); a run that may write
  that file also leaves a `#TODO(agent):` marker carrying that class. The report
  closes and is gone; the marker stays
- **Never omit the sweep** — markers in this run's diff against `open`, files
  written against files evidenced: `swept, 0 markers; 7 changed / 7 evidenced`.
  While either pair disagrees the status is not `DONE` (`_coding/CONTRACT.md`)
<!-- /deliver:report -->

## Done when

Every owed view is drawn from the plan and the code, every view and every seam
has been attacked, each flaw names the rule it breaks and the shortest path to
the break, the flaws are ordered by consequence, and the report says plainly
what the plan left undrawable.
<!-- deliver:surface -->
- **Say what the moment needs.** Start: what will be done and what is excluded.
  Mid-run: a line when the reader must act — a divergence from what was agreed,
  a path found blocked, work that would grow the scope — or when the run changes
  course; tool calls are already visible and are not replayed. A question names
  the decision it unblocks and the default taken if nobody answers
- **End with the answer in one line** — status and what changed; then the sweep
  line, then one line per residual a human must decide, then what is next. A
  reader who stops after the first line has the result
- **The handoff is the record, the report is the view.** The brief, the per-file
  grades and the `open` list travel in the handoff and are shown when asked
- **Sized to the tier**, the deliverable linked, never pasted: `T0` is one line
  with the sweep folded in, `T1` adds evidence and residuals, `T2` what is next.
  Trimming cuts what the reader already has — request, files, path (`_coding/REPORT.md`)
- **Not bigger than it is.** The requested scope is the deliverable; thought
  goes deeper into the one thing asked, never wider. **A real problem is the
  exception** — something that would break, is unsafe, or rests on a false
  premise is explained in full (`_coding/REPORT.md`)
<!-- /deliver:surface -->
