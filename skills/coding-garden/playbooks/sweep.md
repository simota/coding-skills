<!-- coding:guidance -->
# Sweep — one pass over the tree before work starts

A pass reads the tree bottom-up, because a layer is only as good as the one
under it: a lint finding means nothing while the linter is silent, and a doc
that matches the code means little while the tests are red. Each step runs
what the host already has. Nothing here installs, edits or regenerates.

## The order

1. **The gate.** The host's verify command on the untouched tree. Red: stop,
   and the pass is one finding for `coding-debug`
2. **The checks are alive.** For each check the gate wraps (format, lint,
   types, tests), confirm that it ran over the paths in scope. Proving a check
   red by planting a break writes to the tree; that proof belongs to
   `coding-setup`. Here a check is silent when its config excludes the scope,
   when its run reports zero files, or when a rule is disabled wholesale. Count
   the suppressions in scope (`eslint-disable`, `# noqa`, `@ts-ignore`,
   `#[allow(`) and compare with the count a month of history back: a count
   that only grows is a finding
3. **The tests.** Run the suite in scope. A red test is `coding-debug`'s. A
   skipped or disabled test is listed with the reason it gives, or as giving
   none. A test that asserts nothing goes to `coding-test`
4. **The docs.** Every path the agent rules and the feature map name exists.
   Every read-only command they give runs as written; one that changes state is
   listed, not run. Generated docs (an API schema, a CLI's help, an API report)
   are regenerated in a throwaway copy and diffed against the committed ones.
   Doc examples run where the host has a runner for them
5. **The architecture.** The host's declared boundary rules run, and cycles are
   counted. No declared rules is a finding of its own for `coding-setup`, not a
   licence to infer the architecture and judge against the guess
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
| A check is silent, broken or missing; a category has no tool | `coding-setup` |
| A boundary violation or a cycle | `coding-refactor`; the boundary itself in question goes to `coding-plan` |
| Dead code, duplication, complexity over threshold, a comment that binds nobody | `coding-refactor` |
| More code than the problem needed, or prose that reads out of date | `coding-review`, as a Question |
| A doc that disagrees with the code | The skill that next changes that code; documentation travels with it |
| An outdated dependency | `coding-implement`, after the human agrees to the upgrade |
| A helper script in the toolbox that no longer runs | `coding-toolbox` |
| The same kind of finding fixed once before | `coding-setup`, to lay a check, together with the owner above |

## The second sighting

Before a finding is filed, search the history for the same kind already fixed:
`git log -S` or `-G` on its pattern, and `git log --grep` on revert and fix
messages. A hit makes it a second sighting. Fixing it again only clears this
copy, so it also goes to `coding-setup`, which closes it on the highest rung
the host allows: a structure that cannot express it, then a check that fails
on it, then a written rule.

## The report

The first line says whether the start is clear or blocked, and by how many. The
blocking findings follow, one line each: owner, what, evidence. Then the
recorded findings counted by owner, then each category left unchecked with its
reason. The fixes come before the new work, blocking ones first, one commit
each.
