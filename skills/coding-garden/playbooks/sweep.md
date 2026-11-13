<!-- coding:guidance -->
# Sweep — one pass over the tree before work starts

A pass reads the tree bottom-up, because a layer is only as good as the one
under it: a lint finding means nothing while the linter is silent, and a doc
that matches the code means little while the tests are red. Each step runs
what the host already has. Nothing here installs, edits or regenerates.

## The order

1. **The gate**, read before it runs, on the untouched tree. It cannot run, or
   fails in the area about to change: stop, one finding for `coding-debug`. It
   fails only elsewhere: record that failure with its area and go on
2. **The checks are alive.** For each check the gate wraps (format, lint,
   types, tests), confirm that it ran over the paths in scope. Proving a check
   red by planting a break writes to the tree; that proof belongs to
   `coding-setup`. Here a check is silent when its config excludes the scope,
   when its run reports zero files, or when a rule is disabled wholesale. Count
   the suppressions in scope (`eslint-disable`, `# noqa`, `@ts-ignore`,
   `#[allow(`) and compare with the count a month of history back: a count
   that only grows is a finding
3. **The tests** in scope that the gate did not run. A red test is
   `coding-debug`'s. A skipped or disabled test is listed with its reason, or
   as giving none. A test that asserts nothing goes to `coding-test`
4. **The docs.** Every path the agent rules and the feature map name exists.
   Every read-only command they give runs as written; one that changes state is
   listed, not run. Generated docs (an API schema, a CLI's help, an API report)
   are regenerated in a copy of the checkout made outside it and diffed against
   the committed ones; where the copy cannot run the generator, the category is
   unchecked. Doc examples run where the host has a runner for them
5. **The architecture.** The host's declared boundary rules run, and cycles are
   counted. No declared rules is a finding for `coding-plan`, which decides
   boundaries, never a licence to infer them and judge against the guess
6. **What has grown.** Dead code, unused exports and dependencies,
   duplication, complexity above the host's own threshold, and comments: code
   left commented out, a workaround or excuse left as a note, a TODO with no
   owner. [checks](checks.md) says what can find each
7. **Dependencies.** Outdated packages and published advisories, only on a
   go-ahead, because the registry learns the dependency list

## Two lists

| Blocks the start | Only recorded |
|---|---|
| The gate red, or a check silent or broken | Dead code, duplication, complexity, comments |
| A test red in the area about to change | A test red elsewhere, named with its area |
| A command or path in the agent rules that fails: the next agent follows it | Drift in docs written for people |
| A boundary violation in the area about to change | Violations elsewhere, and cycles |
| An advisory the human says blocks | Outdated dependencies |

The human may move a row between lists. The pass may not, in either direction.

## Who takes each finding

| Finding | Goes to |
|---|---|
| The gate or a test is red | `coding-debug`, then `coding-test` once the cause is known |
| A check silent, broken or missing; a category with no tool; a command or path in the agent rules or the feature map that fails | `coding-setup` |
| A boundary violation, a cycle, dead code, duplication, complexity over threshold | `coding-refactor` |
| No declared boundaries, or a boundary itself in question | `coding-plan` |
| A doc that disagrees with the code, or a comment that binds nobody | The skill that next changes that code; documentation and comments travel with it |
| More code than the problem needed, or prose that may read out of date | The human, as a Question: judging the tree is nobody's standing work |
| An outdated dependency | `coding-implement`, after the human agrees to the upgrade |

## The second sighting

Before a finding is filed, search the history for the same kind already fixed:
`git log -S` or `-G` on its pattern, `git log --grep` on revert and fix
messages. A hit is a second sighting. Fixing it again clears only this copy,
so a second finding, with its own owner, closes it on the highest rung the
host allows: a structure that cannot express it (`coding-refactor`, or
`coding-plan` while the boundary is undecided), else a check that fails on it
or a written rule (`coding-setup`).

## The report

The first line says whether the start is clear or blocked, and by how many.
Then the blocking findings, one line each (owner, what, evidence); the recorded
ones counted by owner; each category left unchecked, with its reason. The fixes
come before the new work, blocking ones first, one commit each.
