<!-- coding:guidance -->
# Safety net — refactoring code nothing covers

Refactoring without a check is editing at random and hoping. The way in is to
first pin down what the code *currently* does — including the parts that are
wrong — and only then change its shape.

## Characterisation tests

Not tests of intended behaviour. Tests of **actual** behaviour, whatever it is.

1. Find the seam — the narrowest point where you can call in and observe out
2. Call it with a realistic input and see what comes back
3. Assert exactly that, including the parts that look wrong
4. Repeat until the branches you are about to touch are covered

**Assert the ugly output.** If the function returns `"None"` as a string when
given a null, the test asserts `"None"`. The goal is a tripwire that fires when
your refactor changes anything, not a statement about what it should do. A
`#TODO(agent): DEFERRED characterisation: pins current behaviour, possibly wrong;
resume when the intended behaviour is specified` next to it, with the matching
entry in `open`, tells the next reader what these are.

## When there is no seam

Legacy code often cannot be called in isolation. In rough order of preference:

| Situation | Approach |
|---|---|
| Constructor does I/O | Test at a higher level — the HTTP handler, the CLI, the job entry point. Coarse is fine; coverage is the point |
| Global or singleton state | Reset it in setup, and assert on it as the output |
| Deep dependency you cannot inject | Extract just the pure part first — that extraction is small and reviewable by eye |
| Nothing is callable at all | Golden-master: run the whole thing over recorded real inputs and diff the output before and after |

**Golden-master is the widest net available.** Capture output for many inputs,
store it, refactor, re-run, diff. It is coarse and slow and it catches most
things — but only where output is deterministic. Non-deterministic fields (ids,
timestamps, ordering) must be normalised out first, or every run diffs and the
net reports nothing.

## Approval by diff, when tests are impossible

Some code cannot be run at all in the available environment. Then the check is
the diff itself, and it only counts if the transformation is uniform:

- Apply exactly one kind of change
- Read every hunk, not a sample
- State in the handoff that evidence is `inspected` and **why nothing could be run**
- Keep the change smaller than you otherwise would — this is the weakest evidence
  there is, and its cost scales with the size of the diff

## Deciding whether the net is enough

Before starting the refactor, ask what would happen if the code silently broke.
The answer sets the bar:

| Consequence | Bar before refactoring |
|---|---|
| Money, data loss, or security | Real tests over the branches being touched. No exceptions |
| A visible feature breaks | Characterisation over the main paths, plus the edge case that motivated the refactor |
| An internal tool misbehaves | A golden-master run, or a smoke test |
| Nothing anybody would notice | Consider deleting the code instead |

That last row is serious. Code nobody would miss and nothing covers is a
deletion candidate before it is a refactoring candidate.

## Before starting the refactor itself

- The net exists and was seen to be green
- The net was seen to **fail** at least once — break something deliberately and
  confirm it trips. A net that cannot fail is not a net
- The branches about to change are covered, not just the file
- Where evidence is `inspected` only, the reason is written down
