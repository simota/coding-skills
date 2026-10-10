<!-- coding:guidance -->
# Sequencing — what to build first

The order is not a formality. It decides how early you learn you were wrong,
and how much has been built on top of the wrong thing by then.

## The rule

**Make the thinnest end-to-end path run first, stubbed everywhere it can be.**
Then replace one stub at a time, keeping the path runnable throughout.

The value is not tidiness. It is that the interfaces get proved by real use
before anything is built on them, and that there is a working thing at every
point — including the point where the work is interrupted.

## Why the alternative fails

Building layer by layer — schema fully done, then the service fully done, then
the API — feels efficient and is not:

- Nothing is demonstrable until the last day, so nothing is falsifiable until then
- Every interface between layers is a guess until the layer above exists
- The last layer discovers that the first one modelled the wrong thing, and the
  correction is now expensive
- Interruption leaves three finished layers and zero working features

## Ordering the steps

1. **Riskiest assumption first**, once a path exists to test it against. The
   thing most likely to invalidate the plan gets checked while changing course
   is still cheap
2. **Whatever unblocks another person** next
3. **The irreversible parts as late as possible** — a migration, a deleted
   column, a published format. Late means better informed
4. **The rest by whatever keeps the tree working**

Riskiest-first and thin-path-first do conflict. Thin path wins: you cannot test
the risky assumption without something to run it in.

## What makes a good step

- **Runnable.** Every step leaves the tree building and the tests passing
- **Committable.** If it cannot be a sensible commit, it is not one step
- **One reason to be wrong.** A step that changes the schema *and* the parsing
  cannot be bisected when it breaks
- **Under a day.** Steps longer than that hide their own sub-steps, and their
  estimates are guesses

## Splitting when a step is too big

| Split along | Example |
|---|---|
| The happy path, then the failures | Working request first; timeouts, retries, and partial failure next |
| One case, then the rest | One file format, then the other four |
| Read, then write | Display the new field before anything writes it |
| Behind a flag, then on | Ship dark, enable separately — the enabling is its own reversible step |
| New path beside old, then switch, then delete | The only safe shape for anything with live data |

## Data and deployed clients

These never fit in one step, whatever the plan says:

1. Add the new shape alongside the old — nothing reads it yet
2. Write both, read old
3. Backfill in bounded batches, each its own short transaction, and only once
   step 2 runs on every instance — rows an old instance writes mid-rollout are
   otherwise missed. Then verify the backfill on real data
4. Read new, keep writing both
5. Stop writing old
6. Remove the old shape, once nothing in flight can still reference it

Skipping a step here is not a shortcut; it is an outage with a delay on it.
Each step is separately deployable and separately revertible, and that is the
entire point.

## Before calling the sequence planned

- Step 1 produces something that runs today
- Every step leaves the tree green
- The irreversible steps are identified and placed as late as they can go
- The step that would most likely reveal the plan is wrong is near the front
