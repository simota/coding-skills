<!-- coding:deferred -->
# Oracles — Where the Expected Value Comes From

Purpose: The sources a test's expected value can legitimately have, what each one can falsify, and the shapes that assert nothing.
Read when: writing any assertion, reviewing a suite that passes while behaviour is wrong, or deciding whether a test is worth keeping.
Source: git — only the regression-test rule's recipe depends on it, and it is run against whatever is installed; the catalogue itself is this set's own.
Verified: 2026-10-09 — catalogue of oracle kinds and their failure modes; the examples are illustrative, the disqualifying question is the operative rule. Both halves of the git recipe are re-run by `make figures` on every commit — the stash with a newly created fix file, and the revert with staged and unstaged test edits; the catalogue has no automated check.

To test something you must already know the right answer. Where that answer came
from decides whether the test is evidence or decoration — and a decorative test
is worse than none, because it reports green.

---

## The disqualifying question

> **Where did this expected value come from?**

If the answer is *"I ran the code and copied the output"* or *"I read the
implementation and wrote down what it does"*, the test asserts that the code does
what the code does. It will pass forever, including for every future run in which
the behaviour is wrong. It is `asserted` evidence wearing an `executed` grade.

This is the dominant failure of machine-written tests and of tests written after
a fix, precisely because in both cases working code is sitting right there.

---

## 1. Specification

The value is quoted from an acceptance criterion, a ticket, an RFC, a published
API contract, or a standard.

```
// AC-114: "orders of 10,000 JPY or more ship free"
expect(shippingFee({ subtotal: 10_000 })).toBe(0)     // boundary is IN, per the wording
expect(shippingFee({ subtotal:  9_999 })).toBe(500)
```

Strongest and cheapest **when the spec is precise**. Quote it with its
identifier: that comment is what makes the assertion auditable a year later.

When the spec says "should be fast" or "handle errors gracefully", the spec is
the defect. Say so rather than inventing a threshold and reporting it verified.

## 2. Independent computation

The value is derived by a route that shares no code with the implementation — by
hand, from a table, by a slow obviously-correct version, or by a trusted library.

Fits anything with a closed form: money, dates, encodings, geometry, parsing.
The cost is real work per case, so use it on the boundaries and use a property
for the interior.

## 3. Property

No single expected value; an invariant that must hold for every input.

- round-trip: `decode(encode(x)) == x`
- idempotence: `f(f(x)) == f(x)`
- conservation: sums, counts, and balances before and after
- ordering: the result of `sort` is non-decreasing and a permutation of the input

A property finds the case nobody thought of, which is exactly the case that
reaches production. It cannot tell you the value is *right* — only consistent —
so pair it with one specification case.

## 4. Metamorphic relation

Two runs related by a known transformation, when no absolute answer exists.
Search results for a query and its synonym; a total that must not change when
the input order is shuffled; a render at two densities.

The standard oracle for anything whose correct output nobody can write down.

## 5. Golden / snapshot — only with provenance

A recorded output is a legitimate oracle **when someone verified the recording
once and said so**, and only for output whose shape matters more than its value.

```
// reviewed 2026-08-21 against the spec's example payload — do not re-record blind
```

Without that line it is the first shape below — an expected value copied from
the output — with a filename. A snapshot updated by
re-running the tool records the bug and turns it green.

---

## Shapes that assert nothing

| Shape | Why it is empty |
|---|---|
| Expected value copied from the output | Asserts the code equals itself |
| `assertDoesNotThrow` as the only assertion | A function returning the wrong answer quietly passes |
| Asserting a mock was called | Tests the test's own wiring |
| Mocking the unit under test | Nothing under test remains |
| A conditional around the assertion | Different runs assert different things; the test names no case |
| Comparing against a constant that also lives in the implementation | One edit changes both |

## The regression-test rule

A test for a fixed bug must be **seen failing on the pre-fix code**. Remove the
fix, run it, watch it fail for the stated reason, restore the fix, run it again.
Remove only the fix, and only recoverably: uncommitted, `git stash push -u -- <fix
paths>` and `git stash pop` — `-u` because a newly created fix file is otherwise
refused, and the test then runs with the fix still in place (never the test file,
never `restore`, which keeps no copy); committed, `git revert --no-commit <sha>` with the test edits committed
or left unstaged, then put it back with `git revert --abort` — `--abort` resets
the index, so a staged test edit is discarded with it.

Both observations are `executed` evidence and both belong in the report. A
regression test that was never observed red is a guess with a filename — it may
be pinning the bug rather than its absence, and nothing downstream can tell.
