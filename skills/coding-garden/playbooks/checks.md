<!-- coding:guidance -->
# Checks — what can find each kind of finding without a reading

A finding a command produced can be reproduced by its owner; a finding a
reading produced can only be agreed with. So each category is checked on the
highest rung the host has, and the report says which rung that was.

1. **Structure.** The language cannot express the mistake: a package-private
   directory, an `exports` map, crate visibility, a type that has no invalid
   state. Nothing to run, and nothing to report but a hole in it
2. **A declared rule a tool enforces.** The host wrote what is allowed in a
   config file, and a command fails on a violation
3. **A reading.** What is left. `inspected` at best

The tools below are kinds, named by example. Only what the host already has is
run; a missing one is reported, never installed.

## Architecture

| Rung | What checks it | What it cannot see |
|---|---|---|
| Structure | Package-private directories (Go `internal/`), a package `exports` map, crate-private modules | Rules between modules the language treats as equals |
| Declared rule | dependency-cruiser, eslint-plugin-boundaries, Nx module boundaries (JS/TS); import-linter layers and forbidden contracts (Python); ArchUnit, Konsist (JVM); depguard, go-arch-lint (Go) | A rule nobody declared. No contract is a finding, not a licence to guess one |
| Cycles | dependency-cruiser, madge; the compiler, where cycles do not build | Cycles through runtime lookup: reflection, a registry keyed by string |

## What has grown

| Kind | What checks it | What it cannot see |
|---|---|---|
| Dead code, unused exports and dependencies | knip (JS/TS); vulture, deptry (Python); deadcode, staticcheck (Go); cargo-machete, the compiler's dead-code warnings (Rust) | Code reached by reflection, a plugin loader, or a string |
| Duplication | jscpd, PMD CPD | Two shapes that do one job with different text |
| Complexity over a budget | ESLint `complexity`, `max-lines`, `max-params`; xenon (Python); gocognit (Go); lizard (many languages) | Whether the budget is right. A host with none has no finding here, only a missing check |
| Comments that bind nobody | ruff `ERA` (commented-out code) and `TD`/`FIX` (TODO notes); ESLint `no-warning-comments`; an ast-grep or semgrep rule for the host's own phrasings ("workaround", "temporary", "just in case") | Whether the note is still true |
| More code than the problem needed | Symptoms only: an interface with one implementation, an abstraction with one caller, a parameter always passed the same value. An ast-grep rule lists candidates | The judgement itself. Candidates go to the human as Questions |

## Drift between code and docs

| Kind | What checks it | What it cannot see |
|---|---|---|
| A doc generated from code | Regenerate in a throwaway copy, then `git diff --exit-code` on the result: an API schema, a CLI's help text, an API report (api-extractor, cargo-public-api) | Anything written by hand |
| Code inside docs | doctest (Python), rustdoc tests, Go `Example` functions | Prose around the example |
| Paths, links and commands | Path existence; lychee for links; each read-only command in the agent rules run as written | Whether the command still does what the sentence says |
| Docstrings against signatures | pydoclint; eslint-plugin-jsdoc `check-param-names` | Whether the description is still true |
| Meaning | Nothing mechanical. A reading, as a Question for the human | |

## Checks that have gone quiet

| Kind | What checks it |
|---|---|
| A check that covers less than it claims | Its run reports how many files it read; compare with the files in scope |
| Suppressions | A count in scope now and a month of history back. Growth is the finding |
| Thresholds | A threshold at the tool's maximum, or raised in the history without a reason in the message |
| Skipped tests | The runner's skip count, each skip with its stated reason |

## Dependencies

The package manager's report of outdated packages or an installed equivalent
(`npm outdated`, `pip list --outdated`, `cargo outdated`, `go list -m -u all`),
and the host's advisory audit if it has one. Both ask a registry, so the
go-ahead comes first. An outdated package is recorded; an advisory is recorded
with its severity, and the human says whether it blocks.
