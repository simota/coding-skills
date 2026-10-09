<!-- coding:deferred -->
# Diff Scoping — Reviewing All of the Change

Purpose: Getting the complete change set before judging it, and the commands that silently return a subset.
Read when: starting any review, or when a review found nothing and that seems surprising.
Source: git — the commands below are re-run against the git actually installed, so there is no version to pin.
Verified: 2026-08-21 — the command outputs below were produced by running them in a fixture repository.
Re-run by `make figures` on every commit, against the git actually installed: a release that
changed one of these behaviours fails the build instead of quietly making the page wrong.

A review is bounded by what was read. Every command in this area succeeds on a
partial change set and prints no warning, so an incomplete review looks exactly
like a clean one. Establish the scope first, then judge.

---

## What each command actually shows

On a tree with one modified tracked file, one staged new file, and one file that
was never added:

```
$ git diff              -> f.txt              # unstaged changes only
$ git diff --staged     -> s.txt              # staged changes only
$ git diff HEAD         -> f.txt s.txt        # both — still no untracked file
$ git status --porcelain
 M f.txt
A  s.txt
?? u.txt                                      # the only place u.txt appears
```

So `git diff HEAD` plus `git status --porcelain` is the minimum for a working
tree, and the untracked entries have to be read with `Read`, not with `diff`.

**A repository with no commits has everything untracked.** `git diff HEAD` fails
outright (`HEAD` does not resolve), and a review that reports "no changes" there
has reviewed nothing. Check `git rev-parse HEAD` before trusting an empty diff.

## Branch review: the dot count changes per command

| Intent | Command |
|---|---|
| The branch's own changes | `git diff <base>...HEAD` — **three** dots |
| The branch's own commits | `git log <base>..HEAD` — **two** dots |
| Files it touched | `git diff --name-status <base>...HEAD` |

Three-dot `diff` means *merge-base against HEAD*. Two-dot `diff` compares the
two tips, so everything the base branch gained since the fork appears as the
branch deleting it. On a fixture where `main` advanced after the fork:

```
$ git diff --stat main..feat    -> 2 insertions(+), 3 deletions(-)   # wrong
$ git diff --stat main...feat   -> 1 insertion(+)                    # the change
```

For `log` the inversion runs the other way: `log A...B` is the symmetric
difference and includes the base's commits too. Fix the base explicitly with
`git merge-base main HEAD` when the branch has been merged into repeatedly.

The dot table is stated in both coding-explore's history reference and coding-review's
diff-scoping reference, because a skill cannot read another skill's directory
once installed. `make figures` re-runs both pages' printed counts against git, so the figures
cannot drift apart; the prose around them is not checked — re-read the other page when editing this one.

## Scope decisions worth making deliberately

| Situation | What to do |
|---|---|
| The diff is dominated by a reformat | Re-read with `-w`, review the real change, and report the mixing as its own finding |
| Files were renamed | `-M` (usually on by default) shows a rename as a rename; `-C` also detects copies. Without them a move reads as a large delete plus a large add, and the review drowns |
| A lockfile or generated file is present | Confirm it matches its source of truth. Do not read it line by line |
| A submodule pointer moved | `git diff --submodule=log` names the commits. The diff otherwise shows only a hash, and a hash review is not a review |
| Binary or vendored paths | State that they were excluded and why. Silent exclusion is the failure this whole page is about |
| The PR is the unit | Read the PR diff, not the local branch. They differ whenever the base moved or a maintainer pushed |

## Before judging, establish two things

1. **The base.** Name it explicitly in the report — `main` at `<sha>`, or the PR
   number. A review whose base is implicit cannot be reproduced.
2. **The coverage.** Which files were read in full, which were skimmed, which
   were skipped. Half of what matters in a diff is outside it: the caller that
   breaks, the second copy of the pattern, the convention departed from.

Both belong in the report. A finding is `inspected` evidence; a finding
demonstrated by running the case is `executed` and worth far more. When neither
is possible, the finding is `asserted` and does not carry a defect's label.
