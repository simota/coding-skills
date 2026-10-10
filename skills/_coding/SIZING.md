<!-- coding:contract -->
# SIZING — how much ceremony the request is worth

Ceremony **above** what a request needs is what gets a harness worked around.
Ceremony **below** it is how unverified work leaves. Both come from the same
move — choosing the tier for comfort — so the tier is read on first match, not
judged, and nobody raises or lowers their own.

## The three tiers

Read top to bottom, take the first match.

| Tier | All of these hold | What it costs |
|---|---|---|
| `T0` | One skill obviously owns it · reversible · fewer than three files · acceptance fits in one sentence | Act, report in one line. **No brief, no handoff** |
| `T1` | One skill owns it, but a `T0` condition fails | Settle the brief, then run. Handoff on return |
| `T2` | Two or more skills own parts of it, or the work spans phases | Route it: settle the brief once, run the chain, one report covers every stage |

`T0` drops the paperwork. It never drops the evidence grades or the line about
handing back when blocked — a one-line report still says what was run.

**Finding mid-run that the tier was wrong means re-sizing and saying so**, not
finishing at the tier you started from. A `T0` that has reached its third file
is a `T1` that was mis-sized.

## When a dialogue is required first

Before executing, one of these makes the dialogue mandatory:

- The shape of the deliverable is not uniquely determined by the request
- The acceptance criteria do not fit in one sentence
- The request carries a word with no achievement condition — "improve",
  "optimise", "clean up", "make it robust", "modernise"
- Doing it wrong would be expensive to undo — a migration, a public interface,
  deleted data, anything that leaves the machine
- A term in the request, the code or the design carries two meanings, or one
  concept goes by two names, and the host's glossary does not settle it

**Reading to find out is not executing.** Never ask what can be looked up: the
file, the test, the git history, and the type signature answer more questions
than the person can. And never open a dialogue over trivial reversible work.

## The brief the dialogue produces

Conclusions recorded as data, not as an understanding. Execution reads only
this.

```yaml
goal: "<one sentence describing the state once achieved>"
delivers: "<a single artifact>"   # split the work if this goes plural
axes: [...]                       # what counts as achieved
excludes: [...]                   # what will not be done. May not be empty
baseline: "<the observed starting state the result is measured against>"
max_attempts: <n>                 # after this many, hand back rather than retry
open_questions: []                # execution does not begin until empty
terms: {}                         # the names this run uses, spelled as the glossary spells them
```

`baseline` and `max_attempts` exist so the closing section below is checkable.
A baseline recorded as an observation ("suite green at 214 passed", "p95 =
340ms") can be compared at the end; one recorded as an impression cannot.

- **Execution does not begin while `open_questions` is non-empty.** Deferring
  an unknown to "I'll decide while implementing" is the shared entrance to both
  rework and scope creep
- **`excludes` may not be empty.** Writing down what will not be done fixes the
  boundary before any work starts, and it is the only thing a downstream skill
  can check itself against
- **Achievement requires every axis.** Judged on a single oracle, there is
  always one axis that can be declared satisfied while the request goes unmet

## Terms — one name per concept, one concept per name

The host's glossary is `.agents/glossary.md` when it exists. Read it before the
brief is settled and write with its names only — code, plan, report alike. A
term the work has to coin goes into `terms`, and at `T1` or above it is
proposed in the dialogue rather than invented on the way.

**An ambiguous or inconsistent term is never resolved by a silent choice.**
Two meanings for one word, or two names for one concept, is a question
(`_coding/REPORT.md`): one question, with the default named — the spelling the
code already uses most. The answer lands in `terms` and — at `T1` or above,
where this run may write it — is appended to the glossary as `term · means · not
to be called`, else it travels in `open`: the next run inherits the decision, not
the ambiguity. A `T1` may create the glossary for its first settled term; a `T0`
never does — it records what it found as an `OUT-OF-SCOPE` residual.

## Constraints do not loosen mid-run

Scope, `axes`, `baseline`, and `max_attempts` are fixed at the start — each is
a field of the brief above, so "did it hold?" is answerable rather than
remembered. About to break one — stop and hand back. A constraint quietly
relaxed to reach a green result is the most expensive kind of false report.

For a `T0` run, which has no brief, the same rule applies to the one fact that
stands in for it: the state observed before the change. Report it alongside the
state after.
