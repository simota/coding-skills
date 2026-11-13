<!-- coding:deferred -->
# Templates — a starting shape for each file a setup lays

Purpose: One starting shape per file — the agent rules, the feature map, the verify script, the CI workflow, the pull request template and CODEOWNERS — so a setup run edits a shape, never invents one.

Read when: about to write one of those files into a host that has none, or checking an existing one for a missing part.

Source: none — these are this set's own shapes. The verify script finds the change with git (`diff --name-only`, `merge-base`, `ls-files --others`). The workflow names two hosted actions by major version as an example; the host's own pins replace them.

Verified: 2026-11-12 — the verify script is re-run by the set's test_setup_templates suite on every check: green, red on a planted break with the check named, and the tree restored; the default run is shown to run only the related check, to widen to every check on a widening or deleted path, to write the timings, and to leave a baseline only from a full run over a tree with nothing uncommitted. The same suite holds the workflow's triggers and its artefact settings. The agent rules, the feature map and CODEOWNERS have no automated check.

Every `<…>` is replaced by what the host does, and a line with nothing to
replace it is deleted. A shape copied whole is a set of claims nobody checked.

---

## The verify script

`scripts/verify.sh`, made executable. Each `run` line wraps one command the host already has.
Output goes to `.verify/`, which the same change adds to the host's ignore file.

```sh
#!/usr/bin/env bash
# One command for a person, an agent and CI. Default: the checks that reach what
# changed since the base; --full: every check, as CI runs it. Exit 1 names what failed.
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p .verify && : >.verify/timings

failed=()
run() {                       # run <name> <command> [args...]
  local name=$1 start=$SECONDS log=".verify/$1.log"; shift
  printf '== %s\n' "$name"
  if "$@" >"$log" 2>&1; then
    printf '   ok\n'
  else
    printf '   FAILED: see %s\n' "$log"
    tail -n 40 "$log"
    failed+=("$name")
  fi
  printf '%s\t%ss\n' "$name" "$((SECONDS - start))" >>.verify/timings
}

# A changed path matching this, or a deleted one, reaches code no related test names.
widens='^(scripts/verify\.sh|\.github/|<dependency manifests>|<lockfiles>|<build and test config>|<shared code>)'
full=0 changed=(); [ "${1:-}" = "--full" ] && full=1
[ "$full" = 0 ] && while IFS= read -r path; do
  if [ ! -e "$path" ] || [[ $path =~ $widens ]]; then echo "verify: $path widens the change"; full=1; break; fi
  changed+=("$path")
done < <({ git diff --name-only "${VERIFY_BASE:-$(git merge-base HEAD <default branch>)}" --; git ls-files --others --exclude-standard; } | sort -u)

# Every run, quickest first. Use the host's own commands:
# run format  <format check>
# run lint    <lint>
# run types   <type check>
if [ "$full" = 1 ]; then
  : # run unit        <unit tests>
  : # run build       <build>
  : # run integration <integration tests>
  : # run e2e         <end-to-end tests>
elif [ "${#changed[@]}" -gt 0 ]; then
  : # run related <the host's command for the tests that reach these files> "${changed[@]}"
fi

summary="verify: ok"; [ "${#failed[@]}" -gt 0 ] && summary="verify: FAILED: ${failed[*]}"
[ "$full" = 1 ] && [ -z "$(git status --porcelain)" ] && echo "$summary" >".verify/baseline-$(git rev-parse HEAD)"
echo "not covered: <what the host has no check for>"
echo "$summary"
[ "${#failed[@]}" -eq 0 ]
```

Every check runs even after one fails, so all failures are repaired in one pass.
`related` is the host's related-tests command: `jest --findRelatedTests`, `pytest --testmon`, the feature map's narrowest one.

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
- After every change: `./scripts/verify.sh` (the checks that reach it; slow ones
  in `.verify/timings`). Before a pull request: `./scripts/verify.sh --full`
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
  merge_group:
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
          include-hidden-files: true
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
<each command that was run, its result, and how many tests ran>

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
