<!-- coding:guidance -->
# Audit — what each layer has, found by running it

A repository is ready for an agent when three things hold: the agent can find
out what the code is, it can check its own change, and a wrong change is stopped
without a person noticing it first. The audit asks those of five layers and
answers each with something that was run. It lays nothing: no tracked file changes.

## The layers

Read bottom-up: a layer is only as good as the one under it. Review by risk
means little when the checks under it pass on broken code.

| Layer | Holds | Present when | A gap is closed by |
|---|---|---|---|
| 1. Design an agent can follow | Separated responsibilities, module boundaries, types, one dependency direction, the reasons for past decisions | One feature can be traced from its name to its code and its tests in a few reads, and imports across a boundary run one way | Not this skill. Named with the path, for the human to route |
| 2. Mechanical checks | Format, lint, types, unit tests, build, security scan, rules for the module boundaries the code already keeps | Each has a command that exits non-zero on a planted break, and CI runs the same command on every pull request | The verify script and the workflow that calls it |
| 3. Rules for agents | `AGENTS.md`, the feature map, procedures for recurring tasks | Every command in the rules runs as written and every path exists. No rule contradicts what the code does | `AGENTS.md` and `docs/feature-map.md` |
| 4. Self-verification | A local run, a smoke test, end-to-end tests, logs, traces, screenshots | An agent can start the product with no human, and a failed run leaves its output at a path the rules name | The setup and smoke scripts, and failure artefacts kept by CI |
| 5. Human review by risk | CODEOWNERS, the pull request template, risk classes, a protected branch, merge conditions | The default branch cannot be merged to with a red check, and the paths whose change needs a person have one | CODEOWNERS and the template, with the forge settings the human applies |

## The grades

One grade per row of the gap table, and each carries what was run to reach it.

| Grade | Means |
|---|---|
| present | It was run and behaved as the layer needs |
| partial | It exists and something is missing. Say what: a check not in CI, a rule with a dead path |
| absent | Nothing does this job |
| unreached | It could not be checked from here: a forge setting this account cannot read, a service that is not running. The prerequisite is named, and the row is `UNVERIFIED` |

A file's existence is never `present`. A workflow nothing triggers, a test
command that runs zero tests, and a CODEOWNERS file naming someone who has left
all exist.

## The pass

**Read a command before running it.** One that changes state outside the
checkout (a database, a queue, a service, an account) is listed to the human
with what it changes, and run only on a go-ahead. Left unrun, its row is
`unreached`.

1. Read what agents are already told: every agent instruction file, the
   contributing guide, the manifest's scripts, the CI workflows, the hooks.
   Rules found in two places that disagree are a finding before anything is run
2. Run each check the way CI runs it, from a clean checkout state. Record
   the command and its exit code, and roughly how long it took. A check too slow to
   run before every pull request is `partial`, whatever it catches
3. Trace one feature. Pick one a recent issue names, and go from that name
   to the entry point, then the logic, then the tests. Count the reads. That count is
   what the feature map is for, and the path taken is its first row
4. Start the product as a new contributor would, using only what the
   repository says. Every step that needed knowledge from outside it is a gap
   in layer 4
5. Read the forge settings if this account can: what the default branch
   requires, who must approve, what is allowed to bypass. Reading is safe;
   changing is never part of an audit
6. Look for the gate's own exits: a way to skip hooks, a check marked
   optional, a path pattern that excludes generated code and also catches real
   code, a bot allowed to merge its own change
7. Write the gap table, bottom layer first

## The gap table

| Column | Holds |
|---|---|
| Layer | The number above |
| What was run | The command or the read, so the row can be repeated |
| What was seen | The observable: an exit code, a count, a missing path |
| Grade | One of the four |
| Closed by | The file or setting that would close it, or the skill a layer 1 gap belongs to |
| Decided by | The agent, or the human. Every dependency, owner name and forge setting is the human's |

## The phases

Setup is laid in an order, and each phase is entered on a measure of the one
before it, never on a date. This skill lays the first two. The last two are
mostly outside the tree; the audit says whether their entry condition holds.

| Phase | State reached | Entered when | This skill |
|---|---|---|---|
| 1. A trusted base | A person and an agent verify with the same command; CI runs it; the default branch requires it | — | Lays layers 2, 3 and 5, and proves the gate |
| 2. A self-contained agent | A small fix reaches a pull request carrying its own evidence, with no person in the loop until review | The gate has been seen green and red, and CI has run it on a real pull request | Lays layer 4 and the feature map's remaining rows |
| 3. The outer loop | An error report or a message becomes an issue, and an agent investigates, fixes, verifies and opens the pull request | Agent pull requests from phase 2 are merging without rework at a rate the human accepts | Names what it needs: duplicate detection, a cap on runs per issue, the conditions that require approval. Wiring outside services is the human's call |
| 4. Reliability, then range | Automation widens from the lowest risk class upwards | The measures below have been collected long enough to compare | Names the measures; never widens the range itself |

**The measures for phase 4**: the share of agent pull requests merged without
rework, review time per pull request, the CI failure rate, defects that reached
production, and the rollback rate. The count of pull requests opened is not one
of them. What matters is how many merged safely and then ran without incident.

## What it leaves behind

The gap table in the report, the phase the host is in and why, and for each
gap who decides. No tracked file is written by an audit; the handoff's
`evidence` keys each row to the command that produced it.
