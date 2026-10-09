<!-- coding:guidance -->
# Traps — writing code that only looks finished

Implementation fails in ways that resemble progress: the file grows, the demo
runs, and what was actually asked for drifts out of reach.

## While building

| Trap | What it looks like | Instead |
|---|---|---|
| Happy path only | Every route that succeeds is written; every route that fails is not | Name what can fail at each boundary, then decide which are worth handling — decide, do not forget |
| Two sources of truth | The same state lives in two places, kept in step by hand | One owner. Everything else derives from it |
| Depth before width | One layer is finished properly before the path exists end to end | Get the thinnest end-to-end path running first; otherwise nothing is demonstrable until the last day, and every interface between layers is a guess |
| Configurability for one caller | An option appears so the single caller can choose | Inline it. Add the option when the second caller exists |
| Fighting the framework | The framework's shape is worked around rather than used | Use the framework's extension point. A workaround becomes permanent and every upgrade breaks it |
| A dependency for a function | A package arrives for something small | Weigh install, upgrade, audit, and supply chain against the lines saved |
| Cleverness where it is hardest | The densest code sits where the domain is most complex | That is exactly where it will be read under pressure. Put the cleverness elsewhere, or nowhere |
| Defensive noise | Null checks and try/except around calls that cannot fail | Trust internal callers. Validate where data enters from outside, once |
| The premature interface | An abstraction with one implementation, "for testing" | If the real thing cannot be constructed in a test, fix that. One implementation needs no interface |

## At the boundaries

Most defects live where code meets something it does not control.

| Trap | What it looks like | Instead |
|---|---|---|
| The mock that never matched | A stub stands in for an external system and is never compared against it | Check the real shape once, early. A stub agrees with whatever it was written to agree with |
| Contract by assumption | Field names, nullability, and units inferred from one sample response | Read the contract. A sample shows what happened, not what is allowed |
| Retry without idempotency | A failed call repeated on an operation that cannot be repeated | Decide repeatability before adding the retry, not after the duplicate charge |
| Partial failure as atomic | A multi-step external operation treated as all-or-nothing | State what happens when step three of five fails, and write that |
| Ambient assumptions | Local clock, timezone, locale, encoding, and filesystem treated as universal | They differ in production, and the difference surfaces as corrupted data, not as an error |
| Trusting the boundary | Input from outside handled like input from inside | Validate where it enters, once, and trust it afterwards |

## Finishing

| Trap | What it looks like | Instead |
|---|---|---|
| Demonstrated once, by hand | It worked when it was tried | Leave behind something that can be run again |
| Green on the wrong thing | The check passes without exercising the change | Make it fail first, then make it pass. An assertion that never failed proves nothing |
| The unfinished edge | The last case is left as a comment and the work is reported complete | Finish it. An in-scope gap left behind is a `DEFERRED` residual — marker, `open` entry, resume condition — and the status is `PARTIAL`. Never a comment and `DONE` |
| Scope discovered late | Work outside the brief is absorbed because it was found while building | It was not agreed. Mark it and hand the decision back |
| The tidy-up rider | A rename or reformat rides along in the diff | Behaviour change plus cleanup is unreviewable. Separate commits, or separate work |

## The order that works

1. Make the thinnest end-to-end path run, with most of it stubbed
2. Replace one stub at a time, keeping the path runnable throughout
3. Handle the failures worth handling — named, not caught broadly
4. Confirm by running it, not by reading it

The point of this order is that interfaces are proved by use before anything is
built on them.

## Before calling it done

- The path was run, and what running it produced is stated
- Failure routes were chosen deliberately; the unhandled ones were decided, not overlooked
- Nothing works only because it has not been exercised yet
- The diff contains the change and nothing else
