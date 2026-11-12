<!-- coding:guidance -->
# Lay — writing what is missing, and proving the gate

Each file here is either a gate or a pointer to one. The order below is the
order of dependency: every later file calls or cites an earlier one, and the
run can stop after any step with what exists so far still working.

## The order

1. **`scripts/verify.sh`** — the one command, made executable, and `.verify/`
   added to the host's ignore file with it. Everything else refers to it
2. **`AGENTS.md`** — what an agent may do, must do and must ask about
3. **`docs/feature-map.md`** — where each feature's code and tests are
4. **The CI workflow** — runs the verify script on every pull request
5. **The pull request template and CODEOWNERS** — what a person is shown, and
   which person
6. **Self-verification** — a setup script, a smoke test, failure artefacts
7. **Forge settings** — written out for the human, applied only on a go-ahead

Steps 1 to 3 are the base. A host with only those is already better ground than
one with all seven half done.

## What each file holds

| File | Holds | Wrong when |
|---|---|---|
| `scripts/verify.sh` | Every check the host has, each run through the host's own command, in one invocation that a person, an agent and CI all use. It names each failing check and where its output is, and exits non-zero if any failed | It hides a failure behind a fallback, needs a secret, behaves differently in CI, or is slow enough that nobody runs it — then the default is the quick set and a flag runs all of it |
| `AGENTS.md` | Five short sections — architecture, coding, verification, safety, pull requests — each rule taken from what this host does. Rules a command enforces are named by that command; the rest sit under a heading that says they are discipline | It restates the linter, describes the structure where it could point at it, carries a rule the code breaks, or is long enough to be skimmed |
| `docs/feature-map.md` | One row per feature, named as issues name it: the entry paths, the tests, and the narrowest command that runs only those tests | A path in it is missing, or it lists every file — that is a copy of the tree, and the tree is already there |
| The CI workflow | On every pull request: install as the manifest says, run the verify script, keep the failure artefacts. The least permissions that allow that | It lists the checks itself. The second list is the one that drifts |
| The pull request template | Purpose, what changed, the verification that was run and its result, what was not verified, known risks, the risk class | It is a column of boxes to tick. A box records that it was ticked |
| CODEOWNERS | An owner for every path whose change needs a person: schema and migrations, dependency manifests and lockfiles, authentication, infrastructure — and the gate's own files | It has one catch-all line, or names someone the human did not confirm |
| The setup and smoke scripts | From a clean checkout to a running product, then one request or command that shows it is alive, with logs at a path the rules name | A step needs knowledge that is not in the repository |

An existing agent instruction file under another name is kept. `AGENTS.md` then
holds the rules and the other file points at it, or the reverse — one copy,
whichever the host already treats as the source.

## The safety rules every host gets

These go into `AGENTS.md` whatever else the audit found, each matched to the
gate that holds it. A rule in this table without its gate is discipline, and
the report says so.

| Rule | Held by |
|---|---|
| Production is never changed directly | The agent's credentials not reaching it. No file in the tree can hold this one |
| No secret or credential is printed, committed or copied into a rule | A secret scan in the verify script, where the host has one |
| A schema change needs a person | CODEOWNERS on the migration paths |
| A new dependency needs a person | CODEOWNERS on the manifests and lockfiles |
| A test is not deleted or skipped to pass | Review. A count of tests in the pull request's evidence makes a drop visible |
| A type error or lint warning is fixed, never silenced | The linter's own rule against suppressions, where it has one |
| A pull request with a failing required check is not merged | Branch protection |

## Risk classes

The template asks for one, and CODEOWNERS is what makes the answer checkable:
the class is decided by the paths touched, never by the author's opinion of the
change.

| Class | Touches | Needs |
|---|---|---|
| low | Documentation, tests, or internal structure with the gate green | The checks. A person, until phase 4's measures say otherwise |
| medium | Product behaviour inside one feature | The checks and one reviewer |
| high | Schema, dependencies, authentication, money, infrastructure, or the gate's own files | The checks and the owner of that path, always |

## Proving the gate

A verify script seen only passing may be checking nothing. Each check it wraps
is shown to fail once.

1. **Record the tree's status first** — it holds what this run laid, still
   uncommitted. A break goes only into a tracked file with no change of its
   own: never into a file this run wrote, never over someone's edits
2. **Predict green, then run the script on the untouched tree, and again with
   `--full`** — a check never seen green cannot be shown red. Red here is a
   finding about the host: report it and stop, without repairing the product
   and without loosening the check
3. **For each check, plant the smallest break it should catch** — a formatting
   slip, an unused name, a wrong type, a flipped assertion, a syntax error for
   the build. One break, in one file
4. **Predict, then run** — with `--full` for a check in the full set: the
   script exits non-zero and names that check. A
   green run is a `miss` — the check is not wired, or the file sits outside what
   it reads. Fix the script, never the prediction
5. **Restore the file from version control before the next break**, and show
   the status equal to the one recorded once all are done
6. **The workflow is proved only by a pull request that ran it.** Until one
   has, it is `inspected` and `UNVERIFIED`; the same holds for a forge setting
   that was written out and not applied

## Forge settings

Written out in full for the human, never applied on the strength of the
original request — it asked for a setup, and this changes who can merge.

- The default branch requires the workflow's check and a review from the owners
- Nobody bypasses it, including administrators and bots, unless the human names
  the exception
- A merge queue once pull requests arrive faster than CI finishes: without one,
  two changes that each passed can break the branch together

On a go-ahead, apply exactly what was confirmed, then read the setting back.

## What it leaves behind

The files, each merged where one existed. In the report: the green run, one red
run per check, the clean tree, every rule that is discipline with no gate, and
every setting and owner name still waiting on the human. The handoff's
`evidence` keys each file to the command that was run against it.
