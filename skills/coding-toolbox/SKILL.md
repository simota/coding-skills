---
name: coding-toolbox
description: "Sharing the scripts agents write between runs: find a helper script before writing one, keep a throwaway script in the project toolbox so the next agent can reuse it, and prune stale tools."
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---
<!-- coding:contract -->

## Owns

The scripts a run writes to get its work done (a reproduction, a launcher, a
seeder, a probe, a log reader), kept where the next agent finds them: the host
project's `.agents/toolbox/`, one executable per tool, each with a header saying
when to reach for it and what a good run shows. Three moves: find before
writing, keep what was costly to derive, tend what is kept. Ownership of
adjacent work is defined in `registry/capabilities.yaml`.

## Before starting

- Read `.agents/toolbox/INDEX.md` first, whatever the move. A tool that
  nearly fits is fixed in place and proved again, never forked: two tools for
  one job is the state this skill exists to prevent
- No toolbox yet is a normal start. The first keep creates it and adds one
  line to the host's `AGENTS.md` or `CLAUDE.md`: read the index before writing
  a script. Without that line no agent outside this skill ever finds it
- The header's `Proves:` line is the prediction, written before the tool
  runs from its new place and graded after
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
<!-- deliver:predict -->
- Register the prediction before the run, ideally before the edit: what will
  be run, and what observable result changes (a named test, an exit code, a
  value at a path). After it, report `hit`, `miss`, or `void` (it turned out
  unobservable). A `miss` costs nothing; an unrecorded `miss` costs the run.
  Two consecutive misses in one area mean the model of it is wrong: stop editing
  and read. `executed` with nothing registered supports "it ran", never "it
  works because X" (`_coding/PREDICTION.md`)
<!-- /deliver:predict -->

## Decide first

- Here the tie usually goes to §3 subtraction over addition: every agent
  that looks reads the whole index, so each tool kept is paid for by all of them

| Situation | How to proceed |
|---|---|
| About to write a script for this run | Read the index. A fit is run as its `Run:` line says; a near fit is fixed in place and proved again |
| A script from this run would have to be derived again | [keep](playbooks/keep.md): the gate, the header, the proof from where it will live |
| Asked whether the tools still work, or the index has grown long | [tend](playbooks/tend.md): every tool run once, then fixed, merged or deleted |
| Anything under `.agents/toolbox/` changed | [toolbox](toolbox.py): run this skill's `toolbox.py index`, then `toolbox.py check`, each followed by the toolbox path when it is not `.agents/toolbox`. A non-zero exit names each tool and what it failed on (stderr). A clean check is the headers and the index agreeing; it runs no tool and proves none |
| A one-liner, or useful only to this change | Do not keep it. Name it in the report and let it go |
| The script exercises the product's own behaviour as a check | It is a test and lives in the suite. `registry/capabilities.yaml` says whose |
| A tool changes state outside a scratch directory | Its `Side effects:` starts with `mutates` and says what. It is run only with the human's go-ahead, at keep and at every tend |
| The toolbox is at its cap | Merge or delete before adding. The cap is `toolbox.py`'s, and raising it is the human's call |
| A claim about a tool would be expensive to get wrong | [refute](refute.py). Ask first: it sends the claim and the script it cites to the other engines. Run this skill's `refute.py` with `--running <engine>` (claude, codex or agy) and the path to a JSON file listing `{id, claim, evidence?, where?}`; a non-zero exit means at least one claim went unchecked, or the input or `--running` was refused (stderr says which). Read each verdict. `STANDS` is n engines finding nothing, never proof |
<!-- deliver:values -->
- Ties break by `_coding/VALUES.md`, read top to bottom: honesty over speed ·
  mechanism over intent · subtraction over addition · the existing shape over
  the better shape · what lasts over what helps today · the human decides what,
  the agent decides how. Against all of them, a harness that is correct and
  avoided has failed: when the ceremony costs more than the change, say so
  rather than performing it
<!-- /deliver:values -->

## Always / Never

- Always: run a tool from where it will live before recording it. A script that
  worked in a scratch directory says nothing about the copy
- Always: turn what was pinned into an argument: a path, a port, a commit, an
  account. A convention travels; a pinned value does not
- Always: write the header for an agent that has never seen the app and is
  mid-task. A tool the reader has to reverse-engineer is not a tool
- Always: get the human's go-ahead before the first write to the host's
  `AGENTS.md` or `CLAUDE.md`. It changes what every later agent is told
- Never: edit product code in a toolbox run. A tool failing because the app
  moved is drift, fixed here; one failing because the app is broken is reported
- Never: put a secret, a token or a person's data in a tool. It reads them from
  the environment, and the header names the variable
- Never: edit `.agents/toolbox/INDEX.md` by hand. It is generated from the headers

## Verify with

Every tool kept or changed was run from `.agents/toolbox/tools/` and showed what
its `Proves:` line says (evidence: `executed`), and `toolbox.py check` exits
zero. A tool that could not be run (it `mutates` and no go-ahead was given, or
its prerequisite is absent) is `inspected`, says why, and is `UNVERIFIED`.

- A tend ends one of three ways, and says which: nothing worth changing;
  corrections, each proved by a run; or stopped, with what stopped it
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

The index matches the tools, every tool touched has been observed doing what its
header says from where it lives, nothing kept fails the gate, and the report
names each script this run wrote and did not keep.
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
