<!-- coding:deferred -->
# Machine-Authored Code — What to Check That a Human Diff Would Not Need

Purpose: The defect classes that concentrate in generated code, each with the check that decides it.
Read when: reviewing a diff an agent wrote — including one this session wrote.
Source: git — only the example of `git <subcommand> -h` under check 1 depends on it; the checks themselves use whatever tools the repo has.
Verified: 2026-08-21 — catalogue of defect classes and their checks; the checks are runnable, the frequency claims are deliberately absent — no automated check.

Generated code fails differently from hand-written code. It is fluent, locally
consistent, and matches the surrounding style, so the usual review signals —
awkward naming, obvious copy-paste, a comment that trails off — are absent. What
remains wrong is wrong at the level of *fact*: a symbol that does not exist, a
value nobody derived, a guard for a state that cannot occur.

**Reviewing one's own output is the weakest case.** The same process that
produced the mistake produces the confidence that it is fine. That is what this
list is for: it replaces judgement with a check that can be run.

---

## 1. Symbols that do not exist

A method, flag, config key, or environment variable that reads exactly like the
real API and is not in it. Fluency is not evidence of existence.

**Check:** resolve every non-local symbol in the diff to a definition — grep the
dependency, open the type, or run the call. Not "it looks like the right name".
An import that resolves does not vouch for the attribute after the dot.

**The check is only as good as what it resolves against.** Abbreviated help
output, a summary page, and a README list a subset and say nothing about the
rest, so absence there is not evidence of absence. A run of this check against
`git <subcommand> -h` reported nine flags missing that all exist and all run.
Resolve against the definition, the type, or the executed call — never against a
list that was never meant to be complete.

## 2. The API of a different version

The shape is real but belongs to another major version — a renamed parameter, a
return type that changed, a helper that moved.

**Check:** read the installed version from the lockfile or manifest, then check
the call against *that* version's surface, not against general knowledge of the
library.

## 3. Error handling that removes the error

A broad `try`/`except`, a `catch` that logs and returns a default, a `?? []` on
the failure path. It is a plausible-looking shape that converts a loud failure
into a silent wrong answer.

**Check:** for each handler, name the specific failure it is for and what the
caller does with the fallback. If the answer is "carry on with a default", the
handler is the defect.

## 4. Guards for impossible states

Null checks on values the type system already guarantees, validation of internal
callers, defensive branches with no reachable input. It reads as care and it is
volume: every branch is a thing later readers must consider and tests must cover.

**Check:** name an input that reaches the branch. No input, no branch.

## 5. Tests written from observed output

The expected value was produced by running the code. The test then asserts that
the code does what the code does — it passes forever, including while the
behaviour is wrong.

**Check:** ask where each expected value came from. A snapshot with no provenance
and a regression test never seen to fail on the pre-fix code are the same defect.

## 6. A second implementation of something that exists

Written rather than found, because searching was skipped. The result is two
helpers that drift apart, and the newer one has no callers but this diff.

**Check:** grep for the concept — not the new function's name, which is by
construction unique — before accepting any new utility.

## 7. The precedent's flaw, copied forward

Following the surrounding shape is correct, and it reproduces whatever the
surrounding shape got wrong: the same missing authorisation check, the same
unparameterised query, the same swallowed error, now in one more place.

**Check:** when a diff mirrors an existing pattern, review the pattern once. A
finding there is a finding in every copy, and it outranks anything line-level.

## 8. Scope that grew without being asked

Files touched that no acceptance criterion named — a reformat, a rename, an
"improvement while I was here", a dependency bump.

**Check:** map every changed file to a stated criterion. Anything unmapped is
either out of scope or an undeclared decision; both get reported.

## 9. Comments and messages that assert intent the code lacks

A docstring describing a parameter the function ignores; a commit message
claiming a behaviour the diff does not contain; a `# handle the retry case`
above code with no retry.

**Check:** read each comment against the lines under it, as a claim to be
falsified. Prose is not verified by anything else in the pipeline.

## 10. Completion claimed without execution

The report says a check passed, and no command produced that output. This is the
one defect whose evidence is outside the diff.

**Check:** for each claim of a passing test, build, or run, find the command and
its output. Absent that, the grade is `asserted`, and the change is `UNVERIFIED`
regardless of how the report reads.

---

## Order

Run 1 and 2 first. They are cheap, they are decidable, and each of them
invalidates the rest of the review when it fires — code that calls a symbol that
does not exist has no line-level findings worth writing. Run 5 early too: it is
just as cheap, though it invalidates only the tests.
