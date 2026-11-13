<!-- coding:contract -->
# CONTRACT — what counts as done

Binding on every `coding-*` skill. A skill that reports completion without
satisfying this has reported a wish.

## Evidence grades

Every claim about a change carries one of three grades. `executed` supports
completion; `inspected` does only where nothing can be run; `asserted` never does.

| Grade | Means | Supports `DONE`? |
|---|---|---|
| `executed` | The thing was run and its output observed: test, build, script, request, the program itself | Yes |
| `inspected` | The change was read back, diffed, or type-checked but never run | Only where nothing can be run, and the entry says why |
| `asserted` | The claim stands alone | Never |

**`inspected` without a stated reason is `asserted` wearing a better name.**
"It's a small change", "it obviously works", and "the types line up" are not
reasons. They are the absence of one.

## The unit of evidence is the file written to

Code, config, and prose alike. Each file touched either carries a grade or
appears in the residuals as `UNVERIFIED`. **A file in neither is how an
unverified change leaves.**

## Status

| Status | Condition |
|---|---|
| `DONE` | Every acceptance criterion met, every file evidenced by the checks that reach it, the full suite green or delegated to a required CI check that runs it on the pull request (named in the report, `regression: delegated to CI (<check>)`, and not a residual), and zero `UNVERIFIED`, `BLOCKED` or `DEFERRED` residuals |
| `PARTIAL` | Everything else that produced work. A single `UNVERIFIED`, `BLOCKED` or `DEFERRED` residual lands here |
| `BLOCKED` | Could not proceed. Say what was tried and what stopped it |

Reporting `DONE` on a run with an unevidenced file is the failure this
document exists to prevent. Falling short is reported as falling short.

## Residuals

Anything left behind is classified, and every residual is recorded in the
handoff's `open` list (a `T0`, with no handoff, names it in its one line) with
its class and the `file:line` a marker belongs at, one per residual, not per file.

Who writes the marker depends on what the run may write. A run that may
edit the file in question places the `#TODO(agent): <CLASS> <action>` marker
itself, where a reader would next look, and names it in `open`. A run that may
not (`coding-explore` and `coding-review` anywhere, `coding-plan` in a file it
did not create, `coding-ship` in the diff it ships) records the entry in `open`
alone and leaves the writing to whoever receives the handoff. **A report-only
skill never edits the tree to satisfy this rule**: doing so would break the
guarantee that makes its output trustworthy.

| Class | Means |
|---|---|
| `BLOCKED` | Wanted, attempted, prevented |
| `OUT-OF-SCOPE` | Found during the work, outside what was agreed. Marked, not fixed |
| `DEFERRED` | In scope, deliberately postponed, with the condition to resume named |
| `UNVERIFIED` | Changed but never run |

The report closes and is gone. The marker stays. A problem found outside the
scope is marked, not fixed: absorbing it is how a two-file change becomes a
twenty-file one nobody agreed to.

## The completion sweep — never omitted

Before reporting, run both halves and state both results:

1. Markers introduced by this run. Scan what changed since it began:
   `git diff <the commit it started on>` (across a rebase or merge onto a moved base: up to the move, then from the commit the move made, plus what resolving its conflicts wrote) and the untracked files, less what was
   dirty at the start. Never the whole tree: what the base brought is not this run's. Every marker there must be in `open`, class matching
2. Coverage: diff the files actually written against the files carrying
   evidence

Report it in one line: `swept, 2 markers / 2 in open; 7 changed / 7 evidenced`.
**While either pair fails to match, the status is not `DONE`.** A marker in
the diff with no `open` entry is a residual that just went invisible, and a
file written with no evidence is an unverified change leaving.

A run that left no residual reports `swept, 0 markers; 7 changed / 7 evidenced`.

## Comments and documents — the code is the only copy

An agent copies what sits around the file it opened, and believes a page about
the code before the code. One workaround left as a comment spreads; one page
restating behaviour is still read after the code moved. So prose about code is
deleted by default, and what it carried moves into structure: a what into a
name; a caution (must be sorted, never null) into a type that cannot hold the
bad value, a test that fails when it is ignored, or a lint rule. A workaround is
fixed or becomes a residual with its `#TODO(agent):` marker.

**A document is an index, never a second copy.** It points (path, symbol,
command) and holds only what no structure can: the outside constraint, cited by
its identifier (ticket, spec, upstream issue), and the why that would be
re-derived wrongly without it. Deleting those costs more, because a `why` in one
head is unrecoverable. A plan is scaffolding: what the code now says leaves it.
Never trimmed: a `#TODO(agent):` marker, a licence or provenance header, a test's
oracle identifier. Nothing checks this: a reading pass over the files this
run wrote, before the sweep, binding those alone; a nearby workaround is not copied.

## Boundary cases

- A test that was written but not run is `inspected`, not `executed`.
  Writing a test proves nothing until it fails for the right reason and then passes
- A build passing evidences compilation, not behaviour. It is `executed`
  evidence for "it compiles" and no evidence at all for "it works"
- Reverting is not completing. A change backed out to make a check pass is
  a `BLOCKED` residual, not a green run
- Someone else's failing test encountered mid-run is `OUT-OF-SCOPE` unless
  the change caused it. Establish which by checking the baseline, not by assuming
- A skipped or quarantined test is `UNVERIFIED` for whatever it covered.
  Silencing a check never upgrades a grade
