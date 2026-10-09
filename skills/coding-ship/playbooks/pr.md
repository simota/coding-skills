<!-- coding:guidance -->
# PR and release notes — writing for the reader

Both answer the same question for different readers: what do I need to know
that I cannot see for myself? A PR body that restates the diff has told a
reviewer nothing they did not already have.

## The PR body

```
## What
<one or two sentences: the change, in the reader's terms>

## Why
<the problem. Link the issue, but do not make the link the explanation>

## How
<only the non-obvious decisions, and only where a reviewer would otherwise
 have to reconstruct them>

## Risk
<what could break, what is irreversible, what happens on rollback>

## Verification
<what was run and what it showed. Named, not "tested locally">

## Notes for the reviewer
<migration order, required flag, follow-on PR, the file to read first>
```

Drop any section with nothing to say. An empty heading is worse than a missing
one — it teaches the reader the headings are decorative.

## What belongs in it that the diff cannot show

- **The order of operations** — this must deploy before that; this needs the
  migration applied first
- **The manual step** — a flag to set, a cache to clear, a job to run once
- **What was deliberately not done**, and why. This prevents the review finding
  it as a gap
- **The rollback story** — can this be reverted after it has run? Anything that
  writes data usually cannot, and the reviewer needs to know before approving
- **Where to start reading.** For anything past a few files, naming the first
  file changes the quality of the review you get

## Verification, stated honestly

"Tested locally" is not verification. Name what was run and what it showed:

```
- `pytest tests/billing` — 214 passed, includes 3 new cases for the proration boundary
- Ran the migration against a copy of staging: 1.2M rows, 40s, no lock contention
- Not covered: the legacy import path (no fixtures exist) — #TODO(agent): DEFERRED resume when legacy fixtures exist
```

**The uncovered line is the important one.** A PR that lists only successes
reads as complete, and the gap is discovered in production instead of in review.

## Release notes and changelogs

Different reader, different rules. A user does not care that a function was
extracted.

- **Group by what changed for the user**: added, changed, fixed, removed
- **Write the effect, not the mechanism.** "Exports no longer time out on
  accounts with more than 50k rows", not "increased worker timeout"
- **Breaking changes first**, with the exact migration step required. Anything a
  reader must act on goes above anything they may merely enjoy
- **Omit internal changes entirely** unless they change behaviour, performance,
  or a security posture the reader can observe
- Follow the repo's existing format exactly — its parser or its release tooling
  may depend on it

## Before opening

- The body says something the diff does not
- The risk and rollback are stated, especially for anything touching data
- Verification names commands and results, including what was not covered
- Every `#TODO(agent):` this change introduced is mentioned
- No session URLs, agent metadata, or tool attribution anywhere in it
- **Permission to open it was given.** A PR is a publish
