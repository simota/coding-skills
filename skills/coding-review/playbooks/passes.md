<!-- coding:guidance -->
# Passes — reading a diff one concern at a time

Reading for everything at once finds whatever is most visible, which is
formatting. Run separate passes; each is fast because it ignores everything the
others handle.

## Pass 0 — shape

Before any line-level reading:

- Is the change what was asked for? Does anything in it belong to a different task?
- Does it mix a refactor with a behaviour change? Say so now — everything below
  is compromised by the noise
- Is there a much smaller change that solves the same problem?
- Does it duplicate something the codebase already does?

Getting the shape wrong makes every line-level finding a waste of the author's
time. Stop here and say so if the answer is bad.

## Pass 1 — correctness

The pass that justifies the review. For each changed function, ask what input
makes it wrong:

- **Boundaries**: empty, zero, one, maximum, over maximum, negative, null versus absent
- **Off-by-one** at every index, slice, range, and loop bound
- **The branch not taken**: is the `else` right? Is a case missing? Is a new enum
  value handled everywhere it is switched on?
- **Early return**: does it skip cleanup, a commit, or a release that the normal
  path performs?
- **The error path**: it is the least-tested code in any change. Read it as
  carefully as the happy path
- **Types and units**: seconds versus milliseconds, cents versus dollars, string
  versus number, timezone-aware versus naive
- **Mutation**: is a caller's object modified? Is a default argument mutable? Is
  something being iterated while modified?
- **Idempotency**: what happens if this runs twice — retried, replayed, double-clicked?

## Pass 2 — boundaries and failure

Everything the code does not control:

- Every external call: timeout set? Retry safe? Partial failure handled?
- Every input from outside: validated at the entrance, once?
- Concurrency: read-modify-write without protection? Two requests hitting this
  simultaneously?
- Resources: file handles, connections, locks — released on the failure path too?
- Is an exception caught too broadly, swallowing the errors you needed to see?

## Pass 3 — security

Short, mechanical, non-negotiable:

- Any string reaching an interpreter — and the defence is sink-specific, not one
  rule: SQL wants **parameterised queries** (not escaping); a shell wants an
  **argv array**, never a built command line; a path wants **canonicalise then
  allowlist**; a URL wants a **host allowlist** (SSRF); markup wants
  **context-aware output encoding**
- AuthZ checked on the new path, not just authentication? Object-level, not just route-level?
- Secrets in the diff, in a fixture, in a log line, in an error message returned to a user?
- New dependency — what is it, who publishes it, what does it pull in?
- Does an error message reveal internals to someone who should not see them?

## Pass 4 — cost and clarity

- **Subtraction**: what could be deleted and still solve the problem? A flag with
  one caller, a parameter never varied, an abstraction with one implementation
- **Loops**: a query or a network call inside a loop over unbounded data
- **Consistency**: does it follow the codebase's existing idiom, or introduce a
  second one?
- **Naming**: would a reader who does not know this change guess right?
- **The comment that lies**: a stale comment above changed code is worse than none
- **The comment that says what**: cover it and read the code. Nothing lost means
  the comment is deletable; something lost means the code should have said it

## Pass 5 — the checks

- Do the tests actually exercise the change, or merely execute it?
- Is there a case for each new branch, especially the failure ones?
- Does each new assertion touch a value or path that exists only in this diff? A
  test that would pass verbatim against the base is not guarding the change. Say
  so — proving it by reverting is `coding-test`'s job, not a review's
- Was anything skipped, quarantined, or loosened in this diff?

## Order and stopping

Run 0, then 1, then 2 and 3, then 4 and 5. **Stop and report early** if pass 0
finds a shape problem or pass 1 finds a defect that will change the whole
approach — the rest of the review will be rewritten anyway.

## Before reporting

- Every pass ran over every changed file, or the report says which did not
- Each finding was re-checked against the source with the surrounding lines read
- Findings are ordered by consequence, and the report says plainly if there are none
