<!-- coding:contract -->
# PREDICTION — what was expected, written before it was known

Binding on the skills `registry/harness.yaml` names in `signature.required_of`,
the ones that change what code does. The completion contract grades a claim
*after* the fact; this one fixes it *before*. Both are needed: an ungraded claim
is a wish, and an unregistered expectation is unfalsifiable.

## The failure this prevents

An agent that runs a change and then reads the result writes the explanation
afterwards, and the explanation always fits. Every observed output has a story
that accommodates it, so a story produced after the output is not evidence that
the mechanism was understood — it is evidence that language is flexible.

**The prediction is the only part of a run that cannot be revised in hindsight.**
Registering it is what makes `executed` mean "the model of this code was right"
rather than "something ran and was narrated".

## The form

One line, written before the edit or the command:

```
predict: <what will be run> -> <what observable result changes>
```

The right-hand side names something a second person could read off the same
screen: a named test moving from red to green, an exit code, a count, a value
at a path, a log line that appears or stops appearing. **"It will work" is not
a prediction** — it names no observation, so no result can contradict it.

| Well formed | Not |
|---|---|
| `pytest -k retry` -> `test_retry_backoff` fails at the assert on line 40 | "the retry test will show the bug" |
| `make build` -> exits 0, and the bundle drops below 400 kB | "the build gets smaller" |
| reverting the suspect commit -> the flake stops in 100 consecutive runs | "this is probably the flaky commit" |

A prediction that cannot be written without knowing the answer is a sign the
run is not ready: the thing to do next is read, not edit.

## The three outcomes

Report exactly one after the run, in the same words every time.

| Outcome | Means | What follows |
|---|---|---|
| `hit` | The observation matched what was registered | The claim rests on `executed` evidence *and* on a model that predicted it |
| `miss` | It ran, and the observation differed | Say what happened instead, in one line. The change is not defended; the model is corrected |
| `void` | The prediction turned out unobservable — the command could not run, or it named something the run cannot see | Re-register one that can be observed, or record why none can |

**A `miss` costs nothing. An unrecorded `miss` costs the run** — it is the
moment a wrong model of the code becomes invisible, and every later step
inherits it.

## The stop rule

Two consecutive misses in the same area mean the model of that area is wrong,
not that the last edit was unlucky. Stop editing and go back to reading. A
third attempt made without new information is the same attempt.

Predicting a `miss` on purpose is not a `miss`: designing an observation that
would *disprove* a hypothesis, and seeing it disprove it, is the hypothesis
being tested working exactly as intended. Register which one it is.

## What a run without a prediction may claim

An `executed` grade earned with nothing registered beforehand still supports
**"this ran and produced that output"**. It never supports **"it works because
X"**, and never supports a cause. A causal claim with no prediction behind it
is `asserted` wearing the output of a command.

## Boundary cases

- **A prediction written after reading the output** is not a prediction. If the
  run has already happened, register one for the *next* observation instead
- **A prediction the run makes true by construction** — asserting on a value the
  edit just wrote — is `void`, not `hit`. It observes the edit, not its effect
- **Mid-run correction is allowed and is recorded**: superseding a prediction is
  written down with what prompted it. A silently replaced prediction is a `miss`
  that was renamed
- **A `T0` run predicts too.** Dropping the paperwork never drops the evidence,
  and one line is not paperwork
