<!-- coding:guidance -->
# Reproduce — turning a report into a failing case

Until it fails on demand, there is nothing to reason about. Every hypothesis is
unfalsifiable, and every "fix" is indistinguishable from the bug moving.

## Get to a trigger

1. **Extract the exact input.** The literal request, file, argument, or click
   sequence — not a description of it. "A large upload" is not an input
2. **Match the environment that matters.** Version, config, feature flags, data
   state, timezone, locale, OS. List them; you will need to vary them
3. **Trigger it the shortest way available.** Prefer a test, then a script, then
   a CLI invocation, then the full application. Each step down that list costs
   minutes per attempt, and you will attempt many times
4. **Confirm it fails the same way twice.** A one-off failure has not been
   reproduced; it has been observed

## When it will not reproduce

Work through these in order — the list is roughly by frequency:

| Suspect | Check |
|---|---|
| Data state | Their row has something yours does not — a null, a legacy value, an unusual length, a different tenant |
| Version skew | They are on a different build, or a cached asset, or a stale container |
| Config or environment | An env var, a flag, a region, a locale, a timezone offset that only bites past a certain hour |
| Scale | It appears past N rows, N concurrent requests, or a payload size that crosses a limit |
| Order | It only fails after another action ran first, or when tests run in a different order |
| Concurrency | Two things touch the same state. It reproduces under load and never alone |
| Time | Month boundaries, DST, leap day, expiring tokens, clock skew |
| Their client | Browser, proxy, or SDK version differing from yours |

**Do not stop at "cannot reproduce" without saying which of these were
eliminated and how.** That list is the deliverable when the bug will not come out.

## Shrink it

Once it fails on demand, make it fail faster and smaller — you are about to run
it dozens of times.

- Remove input until it stops failing, then put back the last piece
- Replace slow parts with fixtures, one at a time, checking it still fails after each
- Move it from the application into a test
- Delete assertions and setup that are not required for the failure

**Every shrink step is checked.** A "simplified" reproduction that no longer
fails for the original reason will lead the whole investigation somewhere else.

## Turn it into evidence

The end state is a case that:

- Fails **now**, for the reported reason, with the reason visible in the output
- Runs in seconds
- Does not depend on the network, the wall clock, or leftover state
- Names the expected behaviour in its assertion, not just the current one

Keep it. Whether it becomes the regression test is `coding-test`'s call, but the
fix is not verifiable without it.

## Before moving on to diagnosis

- The failure is triggered on demand and twice in a row
- The failing output is quoted, not summarised
- The environment facts that mattered are written down
- The reproduction is small enough to run repeatedly without cost
