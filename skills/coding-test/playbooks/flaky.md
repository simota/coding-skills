<!-- coding:guidance -->
# Flaky — tests that lie

A test that passes sometimes has already failed at its job: it no longer
distinguishes working code from broken code. Worse, it trains everyone to rerun
red builds, which is how a real failure ships.

**Never make a flake pass by retrying it, sleeping longer, or skipping it.**
Each of those converts a known unreliable signal into an unknown one. Quarantine
is not passing: it is allowed only as an `UNVERIFIED` residual that holds the run
at `PARTIAL` (§ Repairing a red suite).

## Find the difference between runs

Something differs between the pass and the fail. Work the list:

| Suspect | Symptom | How to confirm |
|---|---|---|
| Test order | Passes alone, fails in the suite (or vice versa) | Run the file alone; run the suite with a fixed seed and then a different one |
| Shared state | Fails only after certain other tests ran in the same process; passes alone in a fresh one | Look for module-level state, class attributes, caches, singletons, an unclean DB |
| Time | Fails near midnight, month end, or at a specific hour | Freeze the clock and re-run at the boundary |
| Timezone or locale | Fails in CI, passes locally | Re-run under a 45-minute, DST-observing zone and a non-ASCII locale — `TZ=Pacific/Chatham LC_ALL=tr_TR.UTF-8`, after `locale -a` confirms the locale is installed: a missing one falls back to C — loudly where the code calls `setlocale`, silently everywhere else. Note `TZ=` with no value means UTC, which is what CI already runs |
| Concurrency | Fails under load or on a machine with more cores | Run repeatedly with parallelism forced |
| Real I/O | Fails when the network is slow or absent | Cut the network and see |
| Unordered collections | Fails on some runs with the same data | Look for a set, a Go map, a JSON object round-trip, or a query without `ORDER BY`. Python dicts have kept insertion order since 3.7 — they are not the culprit |
| Randomness | Fails roughly one run in N | Seed it and find the failing seed |
| Resource limits | Fails only in CI | Ports, file handles, memory, disk, or a leftover container |

Reproduce it before fixing: a repeat flag (pytest-repeat's `--count=100`), a
loop, a shuffled order (pytest-random-order's `--random-order`), or CI re-runs. **A flake fixed without being reproduced is a flake with a delay on it.**

## Fixing by cause

| Cause | Fix |
|---|---|
| Waiting on a fixed sleep | Wait for the condition, with a timeout. Never a bare sleep |
| Unordered result compared to an ordered expectation | Sort explicitly, or compare as sets — say which you mean |
| Leaked state | Tear down in a fixture that runs even on failure. Prefer a fresh instance per test over cleanup |
| Real clock | Inject the time. Take `now` as a parameter |
| Real network | Stub it at the boundary, and check the stub against reality once |
| Shared fixture mutated by one test | Make it per-test, or make it immutable |
| Race in the code, not the test | **This is a real bug.** The test found it. Hand it to `coding-debug` — do not stabilise the test |

That last row is the one worth pausing on. A flaky test is sometimes the only
evidence of a genuine race, and "fixing the test" destroys it.

## Repairing a red suite honestly

1. Run it and **classify each failure** before touching anything: real defect,
   wrong test, environmental, or flaky
2. Fix by class, not by file. Silencing failures one at a time hides the pattern
3. For each failure, establish whether the code or the test is wrong. The test
   was written by someone who believed something — find out what before overruling them
4. Anything genuinely unfixable now is **quarantined with a `#TODO(agent):
   UNVERIFIED` marker naming what is no longer covered**, and it counts as
   `PARTIAL`. A skipped test is not a passing test

## Before calling a flake fixed

- The flake was reproduced deliberately, not just observed
- The cause is stated as a mechanism, not "timing"
- The fix removes the nondeterminism rather than tolerating it
- It ran many times (100+, or the suite's convention) without failing
- No sleep was lengthened, no retry added, nothing skipped
