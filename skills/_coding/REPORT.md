<!-- coding:contract -->
# REPORT — what a person reads

Binding on every `coding-*` skill. The other contracts decide what must be true;
this one decides what reaches the reader: **a report that gets skimmed is a
report that did not happen**, and everything the other contracts bought is lost at
the last step.

## Record and view are different objects

| Object | Holds | Read by |
|---|---|---|
| The handoff (`_coding/HANDOFF.md`) | Every field of the brief, every file's grade, the whole `open` list | The next skill, and the person when they ask |
| The report | The answer, the line of evidence under it, what is unresolved | The person, now |

The report is a **view over** the handoff, never a second copy of it in prose.
Rendering the object field by field is how a five-word result arrives as a
paragraph, and it is the failure this file was added to stop.

## The moments a run speaks

Four, and no others. Each owes something different, and **what is right at one moment is
noise at the next.**

| Moment | What it owes | Form |
|---|---|---|
| **Start** | What will be done and what is excluded, with the tier if it is not obvious | stated once, before work begins |
| **A question** | The one decision that is blocked, and the default taken if nobody answers | one question, with its default |
| **Mid-run** | A line when the reader must act — a divergence from what was agreed, a path found blocked, work that would grow the scope, a second prediction miss in one area — and when the run changes course | a line per event; tool calls are not replayed |
| **End** | The report below | the order below, sized by the proportion rule |

**A tool call is already visible; what it changed is not.** "reading the
tests" tells the reader nothing they can act on; "the handler is not where the
bug is, moving to the parser" does. Say the second kind when it changes what
the reader would do next, and nothing otherwise.

**A question is not a status update.** Ask when guessing wrong would be
expensive to undo, ask one thing, and say what happens if the answer never
comes.

## At the end — this order, every time

1. **The answer, one line.** The status and what changed. A reader who stops
   after this line has the result
2. **The evidence, one line.** The sweep (`_coding/CONTRACT.md`), which already
   carries the counts: `swept, 0 markers; 7 changed / 7 evidenced`
3. **What is unresolved** — one line per residual that needs a human decision.
   `BLOCKED` and `UNVERIFIED` always. `DEFERRED` and `OUT-OF-SCOPE` are in the
   handoff and named here only if the reader would act on them today
4. **What is next** — one line, or nothing if the answer is nothing

A `T1` run with nothing unresolved reports lines 1 and 2; a `T2` adds line 4. A
`T0` folds it all into line 1: status, sweep, residuals, and before/after and `hit`/`miss` where owed.

## Proportion

The report is sized by the tier (`_coding/SIZING.md`): a `T0` is that one
folded line; a `T1` adds the evidence line and what is unresolved; a `T2` adds
what is next and where the deliverable is. **Trimming cuts content the reader
already has, never the answer** — and structure (a table, a list, a heading)
is used when it lets the reader find a thing faster, not to make the same
content look shorter.

## The deliverable is not the report

A plan, a diff, a review, a test suite is an artifact with a location. The
report says where it is and what it says in one line; it does not reproduce it.
Pasting the artifact into the report is how a short report becomes a long one.

## Not bigger than it is

The requested scope is the deliverable. Neighbouring concerns, future
possibilities and general principles are not folded into the answer, and a
small ask does not come back as a survey. **Being thoughtful and diverging
are not the same thing** — thought goes deeper into the one thing asked,
never wider. Option lists are given when they were asked for, or when the
choice is the reader's to make.

**A real problem is the exception.** If the request would break something,
is unsafe, or rests on a false premise, say what is wrong, why, and the
options, at whatever length that takes. **Cut noise, never risk.**

## What the report leaves out

Whatever the reader already has: the request, the diff's own file list, output
already quoted, and the path taken to the answer. Confidence and hedging appear
where they would change a decision.

## Asked for more

Bounding the default is not withholding. Every field lives in the handoff, and
"why", "which files", "what else did you find" are answered from it at whatever
length the question deserves. **The long form is available on request; it is
just not the default.**
