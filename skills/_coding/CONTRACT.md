<!-- coding:contract -->
# CONTRACT — what counts as done

Binding on every `coding-*` skill. A skill that reports completion without
satisfying this has reported a wish.

## Evidence grades

Every claim about a change carries one of three grades. `executed` supports
completion; `inspected` does only where nothing can be run; `asserted` never does.

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
| `DONE` | Every acceptance criterion met, every file evidenced, zero `UNVERIFIED` or `BLOCKED` residuals |
| `PARTIAL` | Everything else that produced work — a single `UNVERIFIED` or `BLOCKED` residual lands here |
| `BLOCKED` | Could not proceed. Say what was tried and what stopped it |

Reporting `DONE` on a run with an unevidenced file is the failure this
document exists to prevent. Falling short is reported as falling short.

## Residuals

Anything left behind is classified, and every residual is recorded in the
handoff's `open` list with its class and the `file:line` a marker belongs at —
one entry per residual, never one per file (a `T0`, with no handoff, names them in its line).

**Who writes the marker into the tree depends on the tool grant.** A skill
holding `Edit` or `Write` places the `#TODO(agent): <CLASS> <action>` marker itself,
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

## Comments — the code says what, a comment says why

A comment that restates the line under it is a defect in the code, not a
sentence missing from it. **The test is mechanical: cover the comment and read
the code.** Nothing lost — delete the comment. Something lost — put it in the
code, renaming or extracting until the comment has become the name, and delete
it anyway.

What survives that test is what code cannot carry: why this way and not the
obvious way, the outside constraint that forces it, the ordering that looks
arbitrary and is not, the citation with its identifier. **Deleting those is the
opposite failure and costs more** — a `why` that lived in one head is
unrecoverable, where a `what` is re-read off the code. A `#TODO(agent):`
marker, a licence or provenance header, and the identifier a test quotes for
its oracle are never trimmed by this rule.

**Nothing checks this automatically.** It is a reading pass over the files this
run wrote, made before the sweep is reported, and it binds those alone —
stripping comments elsewhere is a change nobody asked for.

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
