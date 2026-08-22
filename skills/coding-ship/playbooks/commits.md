<!-- coding:guidance -->
# Commits — dividing the work

A commit is the unit at which a change can be understood, reverted, and
bisected. Those three uses decide the division; tidiness does not.

## One reason to change

A commit contains everything that changes for a single reason, and nothing that
changes for another. Practical consequences:

- A rename and a logic change are two commits. Together, the logic change is
  invisible in a wall of renamed lines
- A dependency bump and the code adapting to it are two commits, unless the code
  does not compile without both
- Reformatting is always its own commit, and ideally its own PR
- A fix and its regression test belong together — the test is the fix's evidence,
  and separating them breaks the revert

## Every commit stands alone

Check by actually doing it: check out each commit, build, run the tests.

- **It builds.** A commit that does not is a bisect that lands on it and tells you nothing
- **It passes.** Same reason
- **It is revertible on its own.** If reverting commit 3 requires also reverting
  2, they were one commit
- **It makes sense from the message alone**, to someone who was not there

"I'll fix it in the next commit" produces a history that cannot be bisected,
which is the one thing history is uniquely good for.

## Messages

The subject says what changed, in the repo's convention. The body says **why**,
because the diff already says what.

```
<subject: imperative, ~50 chars, repo's convention>

<why this change exists — the problem, not the solution. Wrap at 72>
<what was considered and rejected, when it is non-obvious>
<what a reader needs to know that the diff cannot show>

<issue or ticket reference, in the repo's format>
```

Worth writing in the body:

- The reason the obvious approach was not taken
- A constraint that forced an odd-looking choice
- A consequence not visible in the diff — an ordering requirement, a flag, a
  manual step
- The behaviour before, when the diff only shows after

Not worth writing: a restatement of the diff, a list of files, an apology, or
anything about the tools used.

## Splitting an oversized change

When it is already one large working tree:

1. **By layer** — schema, then data access, then logic, then interface. Each
   layer's commit should still leave the tree green
2. **By file group**, when the layers are genuinely independent
3. **By behaviour** — the mechanism first, then each case that uses it
4. **Refactor out first** — extract every behaviour-preserving move into its own
   earlier commit, then the remaining diff is the real change and it is small

Mechanically, and without an interactive prompt — `git add -p` cannot be driven
by an agent or a script:

- **Split by path** where the groups are whole files: `git add <paths>`, commit,
  repeat. This covers most cases
- **Split within a file** by writing the diff out and editing it:
  `git diff > /tmp/w.patch`, delete the hunks that belong to later commits, then
  `git apply --cached /tmp/w.patch`
- **Set the rest aside** with `git stash push --keep-index` — `--keep-index` is
  what leaves the staged change in place. A bare `git stash` takes the index too

Run the tests at each step.

**If it cannot be split, say why.** A genuinely atomic change is rare but real —
and a reviewer told "this is atomic because X" reviews it better than one left
to wonder.

## Order of merge

- Anything others are blocked on goes first
- **An additive migration** — a new column, table, or index — merges and deploys
  **before** the code that reads it. **A destructive one is the reverse**:
  deploying a `DROP` ahead of the code that stopped using the column takes the
  running version down. Anything destructive follows the expand/contract order
  `coding-plan` sequences, never a single ordering rule
- Removals go last, after everything that referenced the old thing has landed
  and been running long enough to trust
- A change that is risky to revert goes on its own, not bundled with an
  unrelated safe change

## Before pushing anything

- Each commit was checked out, built, and passed
- The diff was read hunk by hunk — no debug prints, no commented code, no stray files
- No secrets, tokens, `.env`, internal hostnames, or personal data
- Messages say why, in the repo's convention
- **Permission to push was given.** Finishing the work is not permission to publish it
