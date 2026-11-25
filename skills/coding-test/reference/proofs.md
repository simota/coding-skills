<!-- coding:deferred -->
# Proofs — When a Check Must Hold for Every Input

Purpose: When a proof or a model check is worth its cost, and the rules that keep one from certifying nothing.

Read when: a rule must hold for every input rather than a sample, the repo already carries a prover or a model checker, or a proof is being written or repaired.

Source: none — the rules are this set's own; each tool named is an example of a class, and its syntax is the repo's pinned version's.

Verified: 2026-11-25 — catalogue of when to prove and how a proof passes vacuously; the escape hatches agree with the `A proof that proves nothing` class in coding-review — no automated check.

A proof is an oracle over every input its specification admits, and only those.
The checker confirms that the proof meets the specification; nothing confirms
that the specification meets the requirement. That half is where it fails.

## When it earns its cost

| Situation | Check |
|---|---|
| A rule must hold for every input, and one missed input is costly: money, authorisation, a parser of untrusted bytes, an invariant other code trusts | A proof of the code (Lean, Dafny, Verus, Kani, Coq) |
| The risk is in a design's interleavings: a protocol, a lock order, a retry with a timeout | A model check of the design (TLA+, Alloy) before the code. It shows the model; the code is still a test's job |
| Neither, or the repo cannot re-run the checker on every change | A property ([oracles](oracles.md) § 3). A proof nobody re-runs is a document |

Use the checker the repo already carries. A new prover is a dependency change,
reported as one, and it joins the repo's own check or it rots unrun.

## Built to fail

| Rule | Because |
|---|---|
| Write the specification first and apart from the proof; beside each theorem, `requires` and `ensures`, quote the requirement clause it encodes | The specification is the only part the checker cannot judge, so it is the part a reader audits |
| See it reject: a mutated implementation must fail the proof, and a deliberately false `ensures` must not check | A specification that accepts a wrong output is satisfied by every output |
| Show one input that meets each `requires`, and that the requirement's whole domain does | A contradictory precondition proves anything; a narrowed one drops the inputs that failed |
| No escape hatch in what is delivered: `sorry`, `admit`, `Admitted`, `axiom`, `assume`, `#[verifier::external_body]`. In Lean, `#print axioms` on each theorem lists nothing beyond `propext`, `Classical.choice` and `Quot.sound` | Each closes the goal without showing it, and the checker still passes |
| Never weaken the specification to get the proof through, unless the requirement excludes the case; name the clause | Weakening the specification is weakening the assertion |
| A bounded check states its bound: unwinding depth, model size, steps | Past the bound nothing was shown, and an unstated bound reads as none |
| Pin the checker's version, and run it in the repo's own check | A proof the next version rejects, or that no check runs, guards nothing |

## Evidence

The checker's run is `executed` for "the proof meets the specification". "The
specification meets the requirement" is `inspected` at best, and the report says
so, with the clauses quoted. Code outside what was proved, a model's
implementation or a hand port of extracted code, is `UNVERIFIED` until a test reaches it.
