<!-- coding:deferred -->
# Templates — a starting shape for each file a setup lays

Purpose: One starting shape per file — the agent rules, the feature map, the verify script, the CI workflow, the pull request template and CODEOWNERS — so a setup run edits a shape, never invents one.

Read when: about to write one of those files into a host that has none, or checking an existing one for a missing part.

Source: none — these are this set's own shapes. The workflow names two hosted actions by major version as an example; the host's own pins replace them.

Verified: 2026-11-12 — the verify script was run under bash 3.2 with one passing and one failing check, and it printed the failing check's name and log path and exited 1. The other shapes have no automated check.

Every `<…>` is replaced by what the host does, and a line with nothing to
replace it is deleted. A shape copied whole is a set of claims nobody checked.

---

## The verify script

`scripts/verify.sh`. Each `run` line wraps one command the host already has.
Output goes to `.verify/`; the same change adds it to the host's ignore file.

```sh
#!/usr/bin/env bash
# One command for a person, an agent and CI.
# Exit 0: every check below passed. Exit 1: the last line names those that did not.
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p .verify

failed=()
run() {                       # run <name> <command> [args...]
  local name=$1; shift
  local log=".verify/$name.log"
  printf '== %s\n' "$name"
  if "$@" >"$log" 2>&1; then
    printf '   ok\n'
  else
    printf '   FAILED: see %s\n' "$log"
    tail -n 40 "$log"
    failed+=("$name")
  fi
}

# One line per check, quickest first. Use the host's own commands:
# run format  <format check>
# run lint    <lint>
# run types   <type check>
# run unit    <unit tests>
# run build   <build>
[ "${1:-}" = "--full" ] && {
  : # run integration <integration tests>
  : # run e2e         <end-to-end tests>
}

echo "not covered: <what the host has no check for>"
if [ "${#failed[@]}" -gt 0 ]; then
  printf 'verify: FAILED: %s\n' "${failed[*]}"
  exit 1
fi
echo "verify: ok"
```

Every check runs even after one fails: an agent that sees all the failures at
once repairs them in one pass.

## The agent rules

`AGENTS.md`. Five sections, each rule in the host's own terms.

```markdown
# AGENTS.md

## Architecture
- <the dependency direction, as paths: what may import what>
- <where business logic lives, and where it must not>
- Change only what the task needs. Unrelated edits go in their own pull request

## Coding
- New behaviour comes with a test for it
- No existing test is deleted or skipped without a person agreeing
- A type error or lint warning is fixed, never silenced
- <the host's own conventions that a linter does not hold>

## Verification
- After every change: `./scripts/verify.sh`. Before a pull request: `./scripts/verify.sh --full`
- A change to <the UI paths> also runs <the end-to-end command>
- A failing check is investigated and repaired. Its log is under `.verify/`
- To find a feature's code and tests: `docs/feature-map.md`

## Safety
- Production is never changed directly
- No secret or credential is printed, committed or pasted into a file
- These need a person before the change is made: a schema change, a new
  dependency, anything under <the paths CODEOWNERS guards>

## Pull requests
- Fill every section of the template, with the verification output
- Say what was not verified and what could go wrong
- A pull request with a failing required check is not merged

## Discipline — nothing checks these
- <each rule above that no command or owner enforces, repeated here by name>
```

## The feature map

`docs/feature-map.md`. An index: paths and commands, no prose about how the
code works.

```markdown
# Feature map

Where each feature lives. A path that no longer exists is a bug in this file.

| Feature | Entry | Logic | Tests | Run only these |
|---|---|---|---|---|
| <the name issues use> | <route, command or screen file> | <module paths> | <test paths> | <the narrowest test command> |
```

## The CI workflow

`.github/workflows/ci.yml`, for a host on GitHub. It calls the verify script
and lists no check of its own.

```yaml
name: ci
on:
  pull_request:
  push:
    branches: [<default branch>]
permissions:
  contents: read
jobs:
  verify:
    runs-on: ubuntu-latest
    timeout-minutes: <a bound a real run stays under>
    steps:
      - uses: actions/checkout@v4
      - run: <the host's install command, or its setup script once one exists>
      - run: ./scripts/verify.sh --full
      - if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: verify-output
          path: |
            .verify/
            <where end-to-end traces and screenshots land>
```

## The pull request template

`.github/pull_request_template.md`.

```markdown
## Purpose
<the issue or the need, in one or two sentences>

## What changed
<the behaviour that is different, not the list of files>

## Verification
<each command that was run, and its result>

## Not verified
<what could not be run, and why>

## Risks
<what could go wrong, and how it would show>

## Risk class
<low, medium or high — decided by the paths touched>
```

## CODEOWNERS

`.github/CODEOWNERS`. The last matching line wins, so the general owner is
first and the guarded paths follow it.

```text
*                         <the team that reviews by default>

# A person, always
<migrations path>         <owner>
<dependency manifests>    <owner>
<lockfiles>               <owner>
<auth paths>              <owner>
<infrastructure paths>    <owner>

# The gate's own files
/AGENTS.md                <owner>
/scripts/verify.sh        <owner>
/.github/                 <owner>
```
