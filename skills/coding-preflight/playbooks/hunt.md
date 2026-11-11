<!-- coding:guidance -->
# Hunt — attacking the drawn plan

A drawing nobody attacks is an illustration. Each view answers one question
better than any other, so each gets its own attack, and the flaws no single
view can show are found where two views meet.

## Before the first attack

- **The rules are on the sheet**, in the reader's sentences. Never weaken a rule
  to make the plan pass — a rule rewritten until it holds is a flaw with a new label
- **Write down which views you expect to break** — after reading the plan and
  the code, before the first attack. A hunt that finds exactly what its author
  expected was checking the author; an expected flaw that is not there is
  worth a line in the report

## The premise

Before any detail:

- Does the plan, built exactly as drawn, reach the stated goal?
- What could be removed from it and still reach the goal?
- Which one assumption, if false, invalidates it — and was it checked?

**Stop and report if the premise fails.** Every flaw below it will be redrawn.

## One attack per view

- **Usage** — write the call as the laziest caller would. What must they know
  that the signature does not say: an order of calls, a flag that must match
  another, a rule from inside the module? Can it be called wrong and still run?
- **Structure** — follow each arrow backwards. A cycle. New code reaching inside
  an existing module. Two owners of one fact. A box whose only caller is a
  future one
- **Data flow** — for each value: validated once, at the entrance? The same unit
  and type at both ends of every arrow? One writer? A stored copy of a derived
  value — what keeps it in step?
- **Sequence** — cut every arrow: the process dies right after it, what is left?
  Run each step twice — a retry, a double click. Swap two steps nothing orders.
  Run two of the same actor at once
- **States** — every state has a way out, and every rule holds in every state
  that can be reached, including by an order nobody walked
- **Failure** — every empty cell and every `?` is a finding. "Noticed by:
  nobody" ranks first. A way back that can itself fail, and leaves worse
- **Data lifetime** — old code reading new rows, new code reading old ones,
  rollback after new rows exist, and the rows written before the change
- **Trust boundary** — at every crossing: who is checked, where, against what.
  A check drawn only where something is shown. Input trusted for where it
  came from
- **Operations** — for each row of the failure grid, the signal a person would
  see and who sees it. A rollback that is not the rollout reversed. A switch
  that leaves a write half done
- **Load** — a quantity with no number, or a number with no source. A call
  inside a loop over something unbounded. A limit somebody else owns
- **Build order** — after each step, something runs and shows it worked. A step
  checkable only after a later one. A step that cannot be reverted alone. No
  thin end-to-end path until the last step
- **Proof** — run each named check, in your head, on the broken path this sheet
  drew. A check that stays green there guards nothing
- **Network** — each link: who opens it, from which zone, on what. An arrow the
  sequence needs and the network forbids. A new way in. A secret crossing a zone
- **Screen design** — every state the person can be in has something to look
  at: empty, waiting, failed, half done. An action that cannot be undone
  looks like one
- **Screen spec** — each part: what it rejects, and what a press does while the
  last one is still waiting. A rule that only the screen enforces
- **Screen flow** — a screen with no way out, or no way in. Back, reload and a
  second tab at every step. Where the person lands after an error
- **Tables** — each rule about stored data: which constraint holds it. A column
  with no writer or no reader. A status with no value for "unknown"
- **ER** — each line: how many on each end, and what becomes of the many when
  the one goes. Two rows that must agree, with no line between them

## The seams

Each of these is one name looked up in two views. A missing counterpart is a
finding, and it is drawn as two columns.

- Every box in the structure appears in the sequence, or it does nothing
- Every arrow in the sequence has a row in the failure grid
- Every value stored in the data flow has a lane in the data lifetime
- Every step in the build order builds a box in the structure, and every `[new]`
  box is built by a step
- Every failure in the grid has a signal in operations
- Every arrow in the sequence is a link the network view allows
- Every rule has a check in the proof view that can run before release
- Every state has a screen that shows it, reachable in the screen flow
- Every part in the screen spec has a column or a source, every column a writer
- Every table is in the ER diagram, and every stored value is a column
- Every rule names something at least one view can show. A rule no view can
  show is unchecked, and the report says so

## What counts as a flaw

**Ranks 1–3 name the rule and the shortest path that breaks it** — the input,
the state, or the order of steps, one numbered mark per step. Without a path
it is a question, with the case that worries you, or it is dropped. Ranks 4–6
break no rule yet: they point at the mark — the `?`, the step, the box.

| Rank | Kind | Test |
|---|---|---|
| 1 | A rule can be broken | A reachable order of steps ends in a state the rules forbid, and nothing reports it |
| 2 | No way back | Once the row is written or the message sent, no drawn step undoes it |
| 3 | A failure nobody owns | A step fails and no view shows who notices or what recovers |
| 4 | A gap | A `?` two implementers would fill differently |
| 5 | An unverifiable step | Nothing that can be run shows the step worked |
| 6 | More than the goal needs | A part that can be removed with every rule still holding |

Not flaws: a different design that is not broken, a future requirement with no
number, a principle with no instance on the sheet.

## How sure

Each flaw says which, and its drawing never claims more:

- **Confirmed** — a probe was run and showed it (`executed`), or every step of
  the path was opened in the plan and the code (`inspected` — say which)
- **Likely** — the path is named and reads as broken; nothing was run
- **Question** — the answer depends on an intent the plan does not state. It
  takes the rank of its bad answer, and at rank 1–3 it blocks until answered

A flaw about what existing code does is proved by the smallest probe that shows
it — a script or a test in a scratch directory outside the repo — and reported
as the command, what it printed, and what the rule requires. Nothing is left in
the tree.

## Stopping

- **After the plan changes, redraw the views the change touches, then re-run
  every seam.** A fix in one view is how a flaw moves to the next
- **Zero is one full pass over every view and seam that adds no flaw of rank
  1–3.** Ranks 4–6 are reported, and the human decides which the plan carries
- **The same flaw back twice goes to the human.** It points at the rules or the
  premise, not at the plan's wording

## In the report

- Per flaw: rank, how sure, the rule in the reader's sentence with the numbered
  path on its drawing (ranks 1–3) or the mark it points at (ranks 4–6), and the
  smallest change to the plan that removes it — stated, never applied
- The views drawn, the views not owed, the rules no view could show
- The expected flaws that were not found

Adapted from pstack (cursor/plugins): `statechart`'s rules and shortest paths,
`architect`'s caller-first sketch, and `interrogate`'s rule that only a finding
proven by a run survives.
