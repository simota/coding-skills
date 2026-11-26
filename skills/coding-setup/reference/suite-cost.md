<!-- coding:deferred -->
# Suite cost — what a test buys, and what it costs to run

Purpose: Make the suite's cost measurable, keep the default verify run inside a budget, and retire a test only on evidence that it catches nothing another test does not.

Read when: the default run is over its budget, one check dominates `.verify/timings`, or a test is proposed for deletion as redundant.

Source: git, for what a test caught before (`git log --follow`) — each runner and tool named is an example of a class, and its flags are the host's pinned version's.

Verified: 2026-11-26 — the budget lines of the verify script are re-run by the set's test_setup_templates suite: nothing written inside the budget, a line and `.verify/over-budget` past it, the exit code the same either way. The rungs and the order of moves have no automated check.

A test costs every run it is part of, and buys only the defects it would catch
that no other test would. Once agents verify after every change, a suite too
slow to run is a suite that is not run. The remedy is to run less per change
and to keep fewer tests that buy nothing, never to weaken one.

## Measuring

| What | From |
|---|---|
| Each check's time | `.verify/timings`, written by every run |
| Each test's time | The runner's durations from a `--full` run, written under `.verify/`: `pytest --durations=0`, `jest --json --outputFile`, `go test -json`, a JUnit report's `time` |
| The default run against its budget | `.verify/over-budget`, written only when a default run took longer than `VERIFY_BUDGET` seconds |
| What each test alone catches | Mutants killed per test (mutmut, Stryker, PIT, cargo-mutants), else coverage recorded per test (coverage.py `--cov-context=test`) |
| What a test caught before | `git log --follow` on the test file: a test added with a fix, and that fix's message |

The budget never fails the gate. A gate red on time is turned green by deleting
tests, the one move this page restricts. Over budget is a finding for the next
garden pass, and the budget is the human's number.

## Moves, cheapest loss first

1. **Run it less often.** A test that reaches nothing in the change leaves the
   default run: the related command, or a slow tier only `--full` runs. CI still runs it
2. **Make it cheaper.** A real sleep, a real network call, a fixture rebuilt per
   test, a whole app started for one function: `coding-test`, asserting what it asserted
3. **Run it in parallel.** The runner's own workers or shards (`jest --maxWorkers`,
   `go test -p`). A plugin that adds them is a new dependency: the human's
4. **Retire it.** Only a test that buys nothing alone, on the evidence below,
   each one agreed by a person. `coding-test` removes it

## When a test buys nothing

| Rung | Evidence | It supports |
|---|---|---|
| Mutation | Zero mutants it alone kills, on a run that mutated what it calls | A retirement the human can agree to |
| Coverage | No line or branch that only it reaches | A Question: reaching a line is not asserting on it |
| Reading | The same input and the same assertion as another test, both `file:line` | A Question |
| History | It never failed | Nothing. A guard that never failed may be why |

- A regression test pinned to a fixed bug, a test of a path that must never
  break, and the only test at its level for a path are retired on mutation evidence or not at all
- The pull request names each test retired, its evidence and the time saved, and
  its count of tests drops by exactly that number
- A red or flaky test is never retired as redundant: red is `coding-debug`'s, flaky `coding-test`'s
