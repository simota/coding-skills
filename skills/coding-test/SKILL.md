---
name: coding-test
description: "Building the checks that catch defects: test cases, coverage of untested behaviour, regression tests, flaky repair, and what to assert. Use for standalone test work or an unreliable suite."
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---
<!-- coding:contract -->

## Owns

The mechanism that catches a defect — choosing which cases are worth writing,
writing them so they fail for the right reason, repairing tests that lie
(flaky, tautological, or asserting the wrong thing), and getting a red suite
green honestly.

## Before starting

- **Name what would break and go unnoticed.** That is the test worth writing.
  Coverage percentage is not a goal; it measures lines executed, not behaviour checked
- **Read the existing tests first.** Their structure, fixtures, and naming are
  the house style, and a second style makes the suite harder to work in than an
  imperfect consistent one
- **Run the suite before writing anything.** A pre-existing failure discovered
  after your change looks like your change
- A handoff received is checked first (`_coding/HANDOFF.md` — seven receiver
  checks); every `T1`/`T2` run returns one, a `T0` one line. Owner unclear? `_coding/ROUTING.md`
<!-- deliver:sizing -->
- **Size it before the first write**, first match wins. `T0` — one skill owns it,
  reversible, under three files, acceptance in one sentence: act and report in
  one line, **no brief, no handoff**. `T1` — a `T0` condition fails: settle the
  brief first. `T2` — two or more skills own parts of it, or it spans phases:
  route it. `T0` drops the paperwork, never the evidence. Mis-sized mid-run: re-size, say so
- **A dialogue comes first** when the deliverable's shape is not uniquely
  determined, acceptance does not fit in one sentence, the request carries a
  word with no achievement condition ("improve", "clean up"), or the work is
  expensive to undo. Reading to find out is not executing. `excludes` may not be
  empty and execution waits on an empty `open_questions` (`_coding/SIZING.md`)
- **A term with two meanings, or a concept with two names, is a question, never
  a silent choice** — one question with its default, the answer into the brief's
  `terms` (at `T1`+ also the host project's `.agents/glossary.md`, if this run can
  write it; else via `open`), and those names only from then on (`_coding/SIZING.md` § Terms)
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

- **Here the tie usually goes to §2 mechanism over intent** — a rule that cannot
  fail is not a check

| Situation | How to proceed |
|---|---|
| Choosing which cases to write | [cases](playbooks/cases.md) — derive from behaviour and boundaries, not from lines |
| A test passes sometimes | [flaky](playbooks/flaky.md). Never fix it with a retry or a longer sleep |
| Deciding what the expected value should be | [oracles](reference/oracles.md) — ask where it came from. A value copied from the output asserts that the code equals itself |
| Writing a regression test for a fixed bug | Write it so it fails on the pre-fix code. Verify by removing only the fix, recoverably ([oracles](reference/oracles.md) § The regression-test rule), running it, and restoring |
| The code is hard to test | That is information about the code, not about testing. Usually a missing seam — hand it to `coding-refactor` rather than building elaborate mocks |
| A test needs six mocks to run | The unit is wrong. Test a level up, where fewer things need faking |
| The suite is slow | Find the few slow tests before optimising the many fast ones. Slow suites stop being run, and an unrun suite catches nothing |
| A test fails after a change | Establish whether the test or the code is wrong **before** editing either |
| Asked to raise coverage to a number | Say what the number will and will not buy, then cover the behaviour that would break silently |
| A claim here would be expensive to get wrong | [refute](refute.py) — ask first: it sends the claim and the code it cites to the other engines. Run this skill's `refute.py` with `--running claude\|codex\|agy` and a JSON list of `{id, claim, evidence?, where?}`; they are asked to break it, not agree, and a non-zero exit means nothing was checked. `STANDS` is n engines finding nothing, never proof |
| About to run a new test | **Predict the failure first** — which assert, what message. A test that passes on its first run predicted nothing, and may be asserting nothing. For behaviour that already works, get the red by breaking the code under test on purpose, then restore it |
<!-- deliver:values -->
- Ties break by `_coding/VALUES.md`, read top to bottom: honesty over speed ·
  mechanism over intent · subtraction over addition · the existing shape over
  the better shape · what lasts over what helps today · the human decides what,
  the agent decides how. Against all of them: **a harness that is correct and
  avoided has failed** — when the ceremony costs more than the change, say so
  rather than performing it
<!-- /deliver:values -->

## Always / Never

- Always: see a new test **fail first**, for the reason it claims, before making
  it pass. An assertion never observed failing proves nothing
- Always: assert on behaviour the caller depends on — the returned value, the
  persisted state, the message sent. Not on how the code got there
- Always: name the test after the case it pins: what, under what condition,
  expecting what
- Always: keep tests independent — no shared mutable state, no ordering
  dependency, no leakage between runs
- Never: make a test pass by weakening it. Loosening an assertion, adding a
  retry, extending a timeout, marking it skipped, or asserting only that it did
  not raise — each of these deletes the evidence and leaves the suite reporting green
- Never: mock the thing under test, or assert that a mock was called as the only
  assertion. That tests the wiring of the test
- Never: put **branching** logic in a test. A conditional means the test asserts
  different things on different runs and no longer names one case. Parameterised
  cases and property-based generators are not this — they run the same assertion
  over many inputs, which keeps one case per assertion
- Never: commit a test that depends on the wall clock, the network, the
  filesystem outside a temp dir, or a specific machine
- Never: comment a test with what its assertion already says. The name carries
  the case; the one comment a test owes is the identifier of its oracle

## Verify with

A test is proved by watching it fail and then pass (evidence: `executed`).
Both halves are required — a test that was never seen red is `inspected` at
best, and the entry says why it could not be made to fail.

- **`DONE` here**: cases written, each seen red then green, whole suite green (or each
  remaining failure shown by the baseline to pre-date the change, `OUT-OF-SCOPE`), sweep balances
- A skipped or quarantined test is `UNVERIFIED` for whatever it covered, and
  leaves a marker naming what is no longer guarded
- **Report what is still uncovered.** A test report without its gaps reads as
  proof of correctness, which no suite has ever been
<!-- deliver:report -->
- **Grade every claim**: `executed` (it was run) supports completion;
  `inspected` (read back) only where nothing could be run and the entry says
  why; `asserted` never does. **The unit is the file written to** — each carries
  a grade or sits in the residuals as `UNVERIFIED`, and a file in neither is how
  an unverified change leaves
- **`status`**: `DONE` (every criterion met, every file evidenced, zero
  `UNVERIFIED` or `BLOCKED` residuals) / `PARTIAL` / `BLOCKED` (say what was tried)
- **Every residual is `BLOCKED` / `OUT-OF-SCOPE` / `DEFERRED` / `UNVERIFIED`**
  and appears in the handoff's `open`; a run whose grant can write that file
  also leaves a `#TODO(agent):` marker carrying that class. The report closes and is
  gone; the marker stays
- **Never omit the sweep** — markers in this run's diff against `open`, files
  written against files evidenced: `swept, 0 markers; 7 changed / 7 evidenced`.
  While either pair disagrees the status is not `DONE` (`_coding/CONTRACT.md`)
<!-- /deliver:report -->

## Done when

Each new case was observed failing for its stated reason and then passing, the
full suite is green or each remaining failure is shown to pre-date the change,
no assertion was weakened to get there, and the behaviours still unguarded are named.
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
  the `open` list travel in the handoff and are shown when asked
- **Sized to the tier**, the deliverable linked, never pasted: `T0` is the answer
  line with the sweep folded in, `T1` adds evidence and residuals, `T2` what is next. Trimming cuts
  what the reader already has — request, file list, path taken (`_coding/REPORT.md`)
- **Not bigger than it is.** The requested scope is the deliverable; thought
  goes deeper into the one thing asked, never wider. **A real problem is the
  exception** — something that would break, is unsafe, or rests on a false
  premise is explained in full (`_coding/REPORT.md`)
<!-- /deliver:surface -->
