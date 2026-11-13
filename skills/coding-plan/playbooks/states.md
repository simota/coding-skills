<!-- coding:guidance -->
# States — checking a state design before it is built

A flow that moves between states (a checkout, a connection, a lease, a job
queue) is rarely wrong in any one step. It is wrong in an order of steps
nobody walked. Reading the design finds the steps; only walking every order
finds the state they reach together.

So the design is written as a small model, every reachable state is checked
against the rules the reader agreed to, and each rule that breaks comes back
as the shortest path to it. The chart is how the reader checks the model; the
path is how the code is checked against it.

## When this is owed

- The design has two or more things that change independently: a request in
  flight and a user who can cancel, a retry and a timeout, two writers
- A rule must hold "always": never charged twice, never two holders of a lease,
  never a screen with no way out
- An existing flow has a bug report that reads as "only if you do X while Y"

One linear sequence with no branch is not a state design. Say the sequence.

## Write the model

- Variables: only what changes behaviour. A field that no step reads and no
  rule names is noise that multiplies states
- One named action per thing that happens. The next-step relation is the
  disjunction of the actions, never one anonymous step: an unnamed step is a
  path nobody can replay. Each action is one indivisible step in the code it
  describes; if the code can be interrupted halfway, it is two actions
- When modelling code that exists, anchor it. Each condition of an action
  carries the `file:line` that checks it. A condition with no line is the
  model's guess, and it says so
- Each rule is an invariant. A rule can be about a screen, a stored value, a
  message, a charge. If no variable can express it, add the variable. Never
  weaken a rule to make it hold: a rule rewritten until it passes is a bug
  with a new label
- End states get an explicit step that changes nothing. Otherwise a correct
  end reads as deadlock, and a real deadlock hides among them
- Bound it. Small constants (two users, three retries) or an explicit
  limit. A checker carries on past a broken state, so an unbounded model never
  finishes

## Check it

Exhaustive, never sampled. A sample that found nothing says nothing.

- Up to a few dozen states: enumerate them by hand in a table (state, each
  action's result, each rule). The table is the evidence
- Above that: a model checker. TLC where it is installed; otherwise a
  breadth-first walk in a scratch script, which also gives the shortest path
  for free. Never inside the repo
- Register first which rules you expect to break (`_coding/PREDICTION.md`).
  A model that breaks exactly what its author expected is checking the author
- For each rule: holds, breaks, or not checked. A run that hit its bound or
  stopped on an error has not checked the rules it did not reach. They are
  listed as not checked, never as holding
- A break is its shortest path from a start state, one action per step.
  The checker goes on past it, so states after a break are not bugs of their own

## Draw it

The chart is for the person who decides whether the behaviour is right. It is
in their words, and it is small enough to read.

- States say what the reader sees or cares about ("Paying", "Lease held,
  write pending"). No variable names
- Arrows say what happens, as the user sees it ("you press pay", "the
  charge times out"). No action or function names. A step possible only under a
  condition ends with it in brackets: `you press pay [while a charge is pending]`
- About 20 arrows at most. First coarsen: one label for values that act the
  same, drop a detail no rule depends on. Only then hide steps, and when hiding:
  every state stays reachable from a start, every state with a step out keeps
  one arrow, an arrow is hidden whole or not at all, and the plan says what
  was hidden
- Never merge two states that break different rules, nor a breaking state
  with one that does not. The reader can no longer see which rule breaks where
- Mark the breaking state, number the path. The form is in the review
  skill's diagram forms; here it goes in the plan

## Replay it

The model is a claim about the code, and a claim is graded by what was run.

- A path the model found is replayed against the real code, as a test or a
  live repro, one step per action. Until then the break is the model's:
  `executed` against the model, `asserted` against the code
- If the path does not reproduce, the model is wrong until shown otherwise.
  A missing guard in the model, an action that is not atomic, a bound that cut
  the real path. Find which before calling the code correct
- Writing the replay as a test is test work, and fixing what it exposes is
  debugging; the plan hands each path over as the first case

## In the plan

- The rules, each in the reader's sentence
- The chart, with each break marked
- One line per broken rule: the rule, the sentence, the numbered path
- What the model leaves out, and the command that re-runs the check

Adapted from the `statechart` skill in pstack (cursor/plugins): rules as
invariants, a chart in the reader's words, the shortest path to each break,
and the replay against code.
