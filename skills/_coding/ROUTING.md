<!-- coding:guidance -->
# ROUTING — which coding skill owns this

A request with an obvious owner calls that skill directly. This is the fallback
and the ordering guide, not a gate.

**Boundaries are defined in `registry/capabilities.yaml`, not here and not in
any skill's description.** Each entry carries what a skill does, what it does
not (`not:`, with where that work goes instead), and the words that select it.
Writing an exclusion into a description makes every skill added rewrite its
neighbours; keeping it in one file makes an addition cost O(1). The table below
is a reading of that file, not a second copy of it.

## Ownership

| Skill | Owns | Writes code? |
|---|---|---|
| `coding-explore` | Where things are, how they work, what a change would touch | No |
| `coding-plan` | The shape before code exists: interfaces, data model, sequencing | No |
| `coding-implement` | Producing working code — features, endpoints, screens, logic | Yes |
| `coding-debug` | Why something is broken, reproduced and root-caused, then fixed | Yes |
| `coding-refactor` | Changing structure while behaviour stays identical | Yes |
| `coding-test` | Test cases, coverage of behaviour, flaky repair, failing suites | Yes |
| `coding-review` | Finding defects in a change before it lands | No |
| `coding-ship` | Commit granularity, history shape, PR, changelog, release | Yes (git only) |

**Who may write a test.** `registry/capabilities.yaml` assigns checks of the
current change to its writing skill, including retained regression cases and
characterisation nets. Keeping a check does not create a second owner.
`coding-test` owns standalone test work, broader coverage, and suite repair.
Read-only skills may run checks, but their findings do not authorise edits.

**Not owned by this set.** Documentation and comments belong to whichever skill
changes the code they describe. Anything else outside these eight is said
plainly rather than absorbed by the nearest skill.

## Disambiguation

Where two skills are both plausible, `not:` in the registry says where the work
goes. These rows say *how to tell which case you are in* — judgement the
registry cannot hold.

| Both plausible | Decided by |
|---|---|
| explore vs debug | Is something **broken**? Broken → debug. Merely unknown → explore |
| plan vs implement | **Does the shape fit in one sentence?** If yes, implement. If not, plan first |
| implement vs refactor | Does observable behaviour change? Changes → implement. Identical → refactor |
| refactor vs implement (mixed) | **Split it.** A behaviour change hidden inside a rename is unreviewable. Refactor first, commit, then change behaviour |
| debug vs test | **A red suite is debug's until the cause is known, test's after.** Diagnosing why it fails is debug; repairing tests that lie, are flaky, or assert the wrong thing is test |
| review vs test | review reads for defects; test builds the check that catches them. A finding worth guarding becomes a test |
| implement vs ship | Ship starts once the code is correct. Ship never fixes code to make a commit tidy |

## Chains

The chains in `registry/routes.yaml` are templates, not mandatory lifecycles.
Use only stages needed for the agreed deliverable; a skill's own reading and
checks are not extra stages. Stop when that scope is evidenced. Shipping is
included only when requested, with its permission boundary unchanged.

A chain of names expresses linear work only. Where a stage repeats until a
condition holds — `review-to-zero` is the one that does — the entry must carry
the stopping condition, the judge, and a hard cycle limit. **The judge is never
the skill that made the change.** Without those three, "until it is good" has no
stopping rule and the loop ends when someone gets tired.

## Rules for running a chain

- **Settle the brief before the first stage.** Every stage receives it whole and
  it does not change mid-run (`_coding/SIZING.md`)
- **A stage's output is a handoff** (`_coding/HANDOFF.md`), and the next stage runs the
  seven receiver checks before starting
- **Never run a writing skill on work classified as report-only.** "Review this"
  does not authorise edits, and neither does finding something obviously wrong
- **A chain wanting a seventh stage is mis-scoped.** Split the request instead
- Stages run in order. Two skills editing the same files concurrently produces a
  merge, not a result
