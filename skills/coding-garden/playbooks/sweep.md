<!-- coding:guidance -->
# Sweep — one pass over the tree before work starts

A pass reads the tree bottom-up, because a layer is only as good as the one
under it: a lint finding means nothing while the linter is silent, and a doc
that matches the code means little while the tests are red. Each step runs
what the host already has. Nothing here installs, edits or regenerates.

## The order

1. **The gate**, read before it runs, on the untouched tree. It fails in the
   area about to change: stop, for `coding-debug`. It is absent or cannot run:
   stop, for `coding-setup`. It fails only elsewhere: record that and go on
2. **The checks are alive.** For each check the gate wraps (format, lint,
   types, tests), confirm it ran over the paths in scope; proving one red by a
   planted break writes to the tree, so that is `coding-setup`'s. A check is
   silent when its config excludes the scope, its run reports zero files, or a
   rule is disabled wholesale. Count the suppressions in scope (`eslint-disable`,
   `# noqa`, `@ts-ignore`, `#[allow(`) now and a month of history back: more now is a finding
3. **The tests** in scope that the gate did not run. A skipped or disabled test
   is listed with its reason, or as giving none
4. **The docs.** Every path the agent rules and the feature map name exists.
   Every read-only command they give runs as written; one that changes state is
   listed, not run. Generated docs (an API schema, a CLI's help, an API report)
   are regenerated in a `cp -R` copy outside the checkout and diffed, on those
   paths only, against the committed ones; uncommitted edits, or a copy that
   cannot run the generator, leave it unchecked. Doc examples run where they can
5. **The architecture.** The host's declared boundary rules run, and cycles are
   counted. No declared rules is a finding for `coding-setup`, which declares the
   ones the code keeps, never a licence to infer them and judge against the guess
6. **What has grown.** Dead code, unused exports and dependencies, duplication,
   complexity above the host's threshold, and comments: code left commented out,
   a workaround or excuse left as a note, a TODO with no owner (a `#TODO(agent):`
   marker is an open residual, never clutter). [checks](checks.md) finds each
7. **Dependencies.** Outdated packages and published advisories, only on a
   go-ahead, because the registry learns the dependency list

## Two lists

| Blocks the start | Only recorded |
|---|---|
| The gate absent, or red in the area about to change; a check silent | Dead code, duplication, complexity, comments; suppressions grown, a threshold raised |
| A test red in the area about to change | A test red elsewhere, with its area; a test skipped |
| A command or path in the agent rules that fails: the next agent follows it | Drift in docs written for people |
| A boundary violation in the area about to change | Violations elsewhere, and cycles |
| An advisory the human says blocks | Outdated dependencies; edits not yet committed |

Anything on neither list is recorded. The human may move a row; the pass may not.

## Who takes each finding

| Finding | Goes to |
|---|---|
| The gate or a test is red | `coding-debug`; `coding-test` once the cause is the test itself |
| The gate absent; a check silent, broken or missing; a threshold raised; a category with no tool; a command or path in the agent rules or the feature map that fails | `coding-setup` |
| A test skipped, disabled, or asserting nothing | `coding-test` |
| A boundary violation, a cycle, dead code, duplication, complexity over threshold; suppressions grown, each cleared by fixing the code under it | `coding-refactor` if behaviour is unchanged, else `coding-implement` |
| No declared boundary rules | `coding-setup`, declaring the boundaries the code already keeps |
| A boundary itself in question | `coding-plan` |
| A doc that disagrees with the code, or a comment that binds nobody | The skill that next changes that code; documentation and comments travel with it |
| More code than the problem needed, or prose that may read out of date | The human, as a Question: judging the tree is nobody's standing work |
| An outdated dependency or an advisory | `coding-implement`, after the human agrees to the upgrade |
| Edits not yet committed | Whoever is making them; the human says whose they are |

## The second sighting

Before a finding is filed, search the history for the same kind already fixed:
`git log -S` or `-G` on its pattern, `git log --grep` on revert and fix
messages. A hit is a second sighting, and fixing it again clears only this
copy. A second finding closes it on the highest rung the host allows: a
structure that cannot express it (`coding-refactor` if behaviour is unchanged,
else `coding-implement`; `coding-plan` while the boundary is undecided), else a
check that fails on it or a written rule (`coding-setup`).

## The report

The first line says whether the start is clear or blocked, and by how many.
Then the blocking findings, one line each (owner, what, evidence); the recorded
ones counted by owner; each category left unchecked, with its reason. The fixes
come before the new work, blocking ones first, one commit each.
