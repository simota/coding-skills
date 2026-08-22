<!-- coding:guidance -->
# Severity — deciding what is worth saying

A review's value is destroyed by two failures: missing what matters, and
burying it. The second is more common. Every low-value finding spends the
author's attention and lowers the credibility of the next real one.

## The test a finding must pass

**Name the concrete failure**: the input, the state, or the sequence that makes
this produce a wrong result. If you cannot, it is not a defect finding.

- Can name it, and it is in this diff → **report it**
- Can name it, but it is pre-existing → **`OUT-OF-SCOPE`**, mention once, do not
  make it the author's problem
- Cannot name it, but the risk is real and specific → report as a **question**,
  with the case that worries you
- Cannot name it and the concern is general → **drop it**

## Ordering

| Rank | Kind | Test |
|---|---|---|
| 1 | Silent wrong results | Produces bad data or a wrong answer with no error. Nobody finds out for weeks |
| 2 | Security and data loss | Injection, missing authorisation, leaked secret, deletion without a path back |
| 3 | Crash or outage on a reachable path | Real inputs get there |
| 4 | Wrong behaviour on an edge case | Correct on the main path, wrong at a boundary |
| 5 | Missing check | Correct today, and nothing would catch it becoming wrong |
| 6 | Real maintenance cost | A second idiom, an abstraction that will bend, duplication that will diverge |
| 7 | Clarity | A name or structure that will mislead the next reader |

Everything below 7 — formatting the linter does not enforce, an alternative
spelling, a preference — does not go in the report.

## Things that are not findings

- **"I would have done it differently."** Different is not worse
- **A style the codebase does not enforce.** If it should be enforced, that is a
  linter change, and it is its own piece of work
- **A hypothetical future requirement.** "This won't scale" needs a number and a
  timeline, or it is not a finding
- **Repeating what the linter or type checker already said.** It already said it
- **A general principle with no instance.** "This should have better error
  handling" names nothing to fix

## Uncertainty, stated honestly

Say which of these applies, in the finding itself:

- **Confirmed** — traced it, or ran it, and it fails
- **Likely** — the code path reads wrong and the input that breaks it is named,
  but it was not run
- **Question** — you do not know the intent, and the answer decides whether it is a bug

Do not upgrade a question into a defect to make the review look sharper. A
review that cries wolf twice is skipped the third time, and the third one is the
one that mattered.

## Calibration by what the change is

| Change | What matters most |
|---|---|
| Handles money, permissions, or personal data | Passes 1–3, exhaustively. Say so explicitly when clean |
| A migration or anything touching persisted data | Reversibility and what happens to rows already written |
| A hot path | The loop, the query, and the allocation. Not the naming |
| A prototype behind a flag | Shape and reversibility. Not polish |
| A one-line fix | One-line review. A three-heading report on a three-line diff is noise |

## Before sending

- Every finding names a concrete failure or is explicitly a question
- The most severe is first, and the report says plainly when nothing was found
- Nothing pre-existing is presented as introduced by this change
- Nothing was edited — the review reports, it does not fix
