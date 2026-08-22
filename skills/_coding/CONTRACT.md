<!-- coding:contract -->
# CONTRACT — what counts as done

Binding on every `coding-*` skill. A skill that reports completion without
satisfying this has reported a wish.

## Evidence grades

Every claim about a change carries one of three grades. Only the first
supports completion.

| Grade | Means | Supports `DONE`? |
|---|---|---|
| `executed` | The thing was run and its output observed — test, build, script, request, the program itself | Yes |
| `inspected` | The change was read back, diffed, or type-checked but never run | Only where nothing can be run, and the entry says why |
| `asserted` | The claim stands alone | Never |

**`inspected` without a stated reason is `asserted` wearing a better name.**
"It's a small change", "it obviously works", and "the types line up" are not
reasons — they are the absence of one.

## The unit of evidence is the file written to

Code, config, and prose alike. Each file touched either carries a grade or
appears in the residuals as `UNVERIFIED`. **A file in neither is how an
unverified change leaves.**

## Status

| Status | Condition |
|---|---|
| `DONE` | Every acceptance criterion met, every file evidenced, zero `UNVERIFIED` |
| `PARTIAL` | Everything else that produced work — a single `UNVERIFIED` lands here |
| `BLOCKED` | Could not proceed. Say what was tried and what stopped it |

Reporting `DONE` on a run with an unevidenced file is the failure this
document exists to prevent. Falling short is reported as falling short.

## Residuals

Anything left behind is classified, and every residual is recorded in the
handoff's `open` list with its class and the `file:line` a marker belongs at —
one entry per residual, never one per file.

**Who writes the marker into the tree depends on the tool grant.** A skill
holding `Edit` or `Write` places the `#TODO(agent): <action>` marker itself,
where a reader would next look, and names it in `open`. A report-only skill
(`coding-explore`, `coding-review`, and any run whose grant lacks the tool for
the file in question) records the entry in `open` alone and leaves the writing
to whoever receives the handoff. **A report-only skill never edits the tree to
satisfy this rule** — doing so would break the guarantee that makes its output
trustworthy.

| Class | Means |
|---|---|
| `BLOCKED` | Wanted, attempted, prevented |
| `OUT-OF-SCOPE` | Found during the work, outside what was agreed. Marked, not fixed |
| `DEFERRED` | In scope, deliberately postponed, with the condition to resume named |
| `UNVERIFIED` | Changed but never run |

The report closes and is gone. The marker stays. **A problem found outside the
scope is marked, not fixed** — absorbing it is how a two-file change becomes a
twenty-file one nobody agreed to.

## The completion sweep — never omitted

Before reporting, run both halves and state both results:

1. **Markers introduced by this run** — scan the working-tree diff, not the
   whole tree, so markers left by earlier runs are not counted again. Every
   marker in the diff must appear in `open` with a matching class
2. **Coverage** — diff the files actually written against the files carrying
   evidence

Report it in one line: `swept, 2 markers / 2 in open; 7 changed / 7 evidenced`.
**While either pair fails to match, the status is not `DONE`** — a marker in
the diff with no `open` entry is a residual that just went invisible, and a
file written with no evidence is an unverified change leaving.

A run that left no residual reports `swept, 0 markers; 7 changed / 7 evidenced`.

## Boundary cases

- **A test that was written but not run** is `inspected`, not `executed`.
  Writing a test proves nothing until it fails for the right reason and then passes
- **A build passing** evidences compilation, not behaviour. It is `executed`
  evidence for "it compiles" and no evidence at all for "it works"
- **Reverting is not completing.** A change backed out to make a check pass is
  a `BLOCKED` residual, not a green run
- **Someone else's failing test** encountered mid-run is `OUT-OF-SCOPE` unless
  the change caused it. Establish which by checking the baseline, not by assuming
- **A skipped or quarantined test** is `UNVERIFIED` for whatever it covered.
  Silencing a check never upgrades a grade
