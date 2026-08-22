---
name: coding-ship
description: "Getting finished code out: commit granularity and messages, history shape, branch and merge order, splitting an oversized pull request, changelog, and release notes."
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---
<!-- coding:contract -->

## Owns

The shape of the change as other people receive it — how it is divided into
commits, what those commits say, the order things merge in, and what the PR,
changelog, or release notes tell a reader. It moves code between commits and
branches; it does not fix code to make a commit tidy.

## Before starting

- **Confirm the work is actually done.** Tests green, sweep balanced, no
  `UNVERIFIED` residual. Shipping is not the place to discover an unrun file
- **Read the repository's existing convention** — `git log --oneline -30`, the
  most recent merged PRs, `CONTRIBUTING`, and any commit template. Follow it,
  including where you would have chosen differently
- **Read the whole diff yourself**, hunk by hunk, before writing anything about
  it. Almost every stray debug line and unintended file is caught here
- Every `T1`/`T2` run returns a handoff (`_coding/HANDOFF.md` — seven receiver
  checks); a `T0` returns one line and none. Owner unclear? `_coding/ROUTING.md`
<!-- deliver:sizing -->
- **Size it before anything else**, first match wins. `T0` — one skill owns it,
  reversible, under three files, acceptance in one sentence: act and report in
  one line, **no brief, no handoff**. `T1` — a `T0` condition fails: settle the
  brief first. `T2` — two or more skills own parts of it: route it. `T0` drops
  the paperwork, never the evidence. Mis-sized mid-run means re-sizing and saying so
- **A dialogue comes first** when the deliverable's shape is not uniquely
  determined, acceptance does not fit in one sentence, the request carries a
  word with no achievement condition ("improve", "clean up"), or the work is
  expensive to undo. Reading to find out is not executing. `excludes` may not be
  empty and execution waits on an empty `open_questions` (`_coding/SIZING.md`)
<!-- /deliver:sizing -->
<!-- deliver:predict -->
- **Register the prediction before the run.** Before the edit: what will be
  run, and what observable result changes — a named test, an exit code, a value
  at a path. After it, report `hit`, `miss`, or `void` (it turned out
  unobservable). **A `miss` costs nothing; an unrecorded `miss` costs the run.**
  Two consecutive misses in one area mean the model of it is wrong: stop editing
  and read. `executed` with nothing registered supports "it ran", never "it
  works because X" (`_coding/PREDICTION.md`)
<!-- /deliver:predict -->

## Decide first

- **Here the tie usually goes to §4 the existing shape over the better shape** —
  the repo's convention wins over the one you would have picked

| Situation | How to proceed |
|---|---|
| Deciding how to divide the work | [commits](playbooks/commits.md) — one reason to change per commit |
| The change is large or mixed | [commits](playbooks/commits.md) § splitting. A refactor and a behaviour change never share a commit |
| Writing the PR or the release notes | [pr](playbooks/pr.md) |
| A commit does not build or test green on its own | It is not a commit. Reorder or squash until each one stands alone |
| The diff contains something you did not intend | Remove it before anything else. Do not explain it in the description |
| Tempted to rewrite pushed history, or to run any command that discards state | [recovery](reference/recovery.md) — ask first, and `git add -A` before it. Committed work is almost always recoverable; uncommitted work is not |
| A generated file is in the diff | Separate commit, and say why it changed |
| A lockfile is in the diff | **Same commit as the manifest change that caused it.** Split apart, neither commit installs cleanly, and "every commit builds" is already broken |
| The branch conflicts with the base | Rebase or merge per the repo's convention, then **re-run the tests**. A clean merge is not a passing build |
| A claim here would be expensive to get wrong | [refute](refute.py) — put it to the engines that did not make it, asked to break it rather than to agree. Unrefuted is n engines finding nothing, never proof |
<!-- deliver:values -->
- Ties break by `_coding/VALUES.md`, read top to bottom: honesty over speed ·
  mechanism over intent · subtraction over addition · the existing shape over
  the better shape · what lasts over what helps today · the human decides what,
  the agent decides how. Against all of them: **a harness that is correct and
  avoided has failed** — when the ceremony costs more than the change, say so
  rather than performing it
<!-- /deliver:values -->

## Always / Never

- Always: get permission before anything that leaves the machine — push,
  force-push, opening or merging a PR, tagging, publishing, deploying. Being
  asked to "finish the work" is not permission to push it
- Always: state in the message **why**, not what. The diff already says what
- Always: verify each commit stands alone — builds, passes, and makes sense read
  by itself in six months
- Always: check the diff for secrets, credentials, tokens, `.env` files, internal
  hostnames, and personal data before any push. **A secret pushed is a secret
  rotated**, not a secret removed
- Never: `--no-verify`, or disable a hook, or skip CI to get something landed.
  The hook is the mechanism; bypassing it is deciding it does not apply
- Never: fix code here. A defect found while shipping goes back to
  `coding-debug` or `coding-implement`, and shipping waits
- Never: write a message describing intent the diff does not contain
- Never: include session URLs, agent metadata, or tool attribution in commit
  messages, PR bodies, or docs

## Verify with

The history is proved by running against it: each commit checked out builds and
passes (evidence: `executed`), and the diff was read hunk by hunk (evidence:
`inspected`, with the reason where nothing could be run).

- **`DONE` here**: history shaped, each commit green, description written, nothing pushed without permission
- Any `#TODO(agent):` introduced by this change and not mentioned in the PR is a
  residual that just went invisible — the sweep catches it, the PR body names it
- **State what a reviewer needs to know that the diff does not show** — the
  migration ordering, the flag that must be set, the deploy that must go first
<!-- deliver:report -->
- **Grade every claim**: `executed` (it was run) supports completion;
  `inspected` (read back) only where nothing could be run and the entry says
  why; `asserted` never does. **The unit is the file written to** — each carries
  a grade or sits in the residuals as `UNVERIFIED`, and a file in neither is how
  an unverified change leaves
- **`status`**: `DONE` (every criterion met, every file evidenced, zero
  `UNVERIFIED`) / `PARTIAL` / `BLOCKED` (say what was tried)
- **Every residual is `BLOCKED` / `OUT-OF-SCOPE` / `DEFERRED` / `UNVERIFIED`**
  and appears in the handoff's `open`; a run holding `Edit` or `Write` also
  leaves a `#TODO(agent):` marker carrying that class. The report closes and is
  gone; the marker stays
- **Never omit the sweep** — markers in this run's diff against `open`, files
  written against files evidenced: `swept, 0 markers; 7 changed / 7 evidenced`.
  While either pair disagrees the status is not `DONE` (`_coding/CONTRACT.md`)
<!-- /deliver:report -->

## Done when

Every commit stands alone and is green, the messages say why, the description
tells a reviewer what they cannot see in the diff, nothing left the machine
without permission, and the residuals are visible to whoever picks this up next.
