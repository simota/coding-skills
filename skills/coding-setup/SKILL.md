---
name: coding-setup
description: "Making a repo agent-ready, so an agent proves each change: AGENTS.md, a feature map, a verify script, CI gates, CODEOWNERS, a PR template (pull request template), branch protection, required checks."
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---
<!-- coding:contract -->

## Owns

The ground a host project gives an agent before any task: what it may touch,
where a feature's code and tests are, the one command that says a change is
good, and the gates that stop a wrong one. Five layers — design an agent can
follow, mechanical checks, written rules, self-verification, human review by
risk. Three moves: **audit** each layer by running it, **lay** what is missing,
**prove** the gate by breaking the tree. Ownership of adjacent work is defined
in `registry/capabilities.yaml`.

## Before starting

- **Audit first** — every layer for a setup, only the layer touched for one
  file. The host already has commands, rules and owners, and setup writes only
  what is missing: a second lint config is worse than the gap it filled
- **Three files come before the rest** — `AGENTS.md`, `docs/feature-map.md`,
  `scripts/verify.sh`. Everything laid later calls or cites one of them
- **The prediction here is the gate going red**: before each planted break, name
  the check that will fail on it. A gate only ever seen green has proved nothing
- A handoff received is checked first (`_coding/HANDOFF.md` — seven receiver
  checks); every `T1`/`T2` run returns one, a `T0` one line. Owner unclear? `_coding/ROUTING.md`
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
<!-- deliver:predict -->
- **Register the prediction before the run** — ideally before the edit: what
  will be run, and what observable result changes — a named test, an exit code, a
  value at a path. After it, report `hit`, `miss`, or `void` (it turned out
  unobservable). **A `miss` costs nothing; an unrecorded `miss` costs the run.**
  Two consecutive misses in one area mean the model of it is wrong: stop editing
  and read. `executed` with nothing registered supports "it ran", never "it
  works because X" (`_coding/PREDICTION.md`)
<!-- /deliver:predict -->

## Decide first

- **Here the tie usually goes to §2 mechanism over intent** — a rule a command
  could enforce becomes that command, and the sentence is deleted

| Situation | How to proceed |
|---|---|
| Asked to make a repository agent-ready, or what it lacks | [audit](playbooks/audit.md) — each layer graded by something that was run. The gap table is the report; nothing is written |
| A layer is missing a piece | [lay](playbooks/lay.md) — the order, what each file holds, and the proof that the gate stops a wrong change |
| About to write one of the files | [templates](reference/templates.md) — a starting shape for each. Every line is replaced by what this host does, or deleted |
| The file already exists | Merge into it and keep its rules; never replace it. Where it and the code disagree, that is a question for the human |
| The verify script is red on the untouched tree | Stop laying on top of it. The failing check is the audit's first finding, and repairing the product is not this run's work |
| The host has no command for a check — no types, no linter, no tests | The verify script runs what exists and prints what it does not cover. Adopting a tool adds a dependency: the human's call |
| A rule no command can check | It stays in `AGENTS.md`, under the heading that says it is discipline. Never dressed as enforced |
| A setting on the forge — branch protection, required checks, a merge queue | Ask first, every time, with the exact setting written out. It changes who can merge, and it is not in the tree to be reviewed |
| CODEOWNERS needs names | Propose them from history; the human confirms each one. A guessed owner is a gate that asks the wrong person |
| The design itself blocks an agent — a cycle, no boundaries, one module doing everything | Name it with its path and stop: `OUT-OF-SCOPE`. `registry/capabilities.yaml` says whose |
| Asked for the outer loop — alerts into issues, unattended pull requests, a wider automation range | The phase table in [audit](playbooks/audit.md): each phase is entered on a measure of the one before, never on a date |
| A claim about the gate would be expensive to get wrong | [refute](refute.py) — ask first: it sends the claim and the file it cites to the other engines. Run this skill's `refute.py` with `--running <engine>` (claude, codex or agy) and the path to a JSON file listing `{id, claim, evidence?, where?}`; a non-zero exit means at least one claim went unchecked, or the input or `--running` was refused (stderr says which) — read each verdict. `STANDS` is n engines finding nothing, never proof |
<!-- deliver:values -->
- Ties break by `_coding/VALUES.md`, read top to bottom: honesty over speed ·
  mechanism over intent · subtraction over addition · the existing shape over
  the better shape · what lasts over what helps today · the human decides what,
  the agent decides how. Against all of them: **a harness that is correct and
  avoided has failed** — when the ceremony costs more than the change, say so
  rather than performing it
<!-- /deliver:values -->

## Always / Never

- Always: make CI call `scripts/verify.sh`, never restate it. Two lists of
  checks drift, and an agent passes the one CI does not run
- Always: take every command, path and rule from the host — its manifest, its
  CI, its history. A template line that survives unedited is a claim nobody made
- Always: make a failing check say which check failed and where its output is.
  An agent repairs what it can read
- Always: put the gate's own files under an owner — the rules, the verify
  script, the workflows, CODEOWNERS. Unowned, an agent can loosen its own gate
- Always: keep `AGENTS.md` to what changes an agent's next action, and point at
  code where a description would be a second copy that goes stale
- Never: weaken a check to get the gate green — a skipped test, a disabled
  rule, a lowered threshold. A red gate on first run is a finding, reported
- Never: restructure product code or write its tests in a setup run
- Never: run a host command that changes state outside the checkout — a
  database, a service, an account — before reading it and getting a go-ahead
- Never: leave a planted break in the tree, or plant one over uncommitted work.
  Each is restored before the next, and the tree is shown clean at the end
- Never: write a secret into a rule, a script or a workflow, or tell an agent
  where one is kept

## Verify with

`scripts/verify.sh` exits zero on the untouched tree, and for each check it
wraps, one planted break made it exit non-zero naming that check (evidence:
`executed`), with the tree shown clean afterwards. Every path in the feature
map exists and every command in `AGENTS.md` was run as written.

- **A workflow no pull request has run, and a forge setting not read back, are
  `inspected`** — each says why, and is `UNVERIFIED` until one is
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

Every layer in the brief has its files, the gate has been seen both green and
red, nothing existing was overwritten, and the report names each gap left open
and each setting waiting on the human.
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
