<!-- coding:deferred -->
# History — Asking Git the Right Question

Purpose: The commands that answer "why is it like this", and the ones that look right and answer something else.
Read when: the question is about the past — when a value changed, who introduced a line, where deleted code went, why a decision was made.
Verified: 2026-08-21 — every fenced output below was produced by running the command in a fixture
repository; the table rows name flags that were confirmed to run, not outputs that were captured.
Re-run by `make figures` on every commit, against the git actually installed: a release that
changed one of these behaviours fails the build instead of quietly making the page wrong.

Git holds two different kinds of answer and one command shape for both, so the
usual failure here is not a wrong repository. It is a right-looking command that
searched the wrong axis and returned a confident, incomplete list.

---

## `-S` and `-G` are not the same search

`-S<string>` is the **pickaxe**: it matches commits where the *number of
occurrences* of the string changed. `-G<regex>` matches commits whose diff
contains *any line* matching the pattern.

A commit that changes `b=2` to `b=3` adds one line containing `b` and removes
one line containing `b`. The occurrence count is unchanged, so **`-S` does not
see it**:

```
$ git log --oneline -Sb        # commits where the count of "b" changed
4ea7bd7 c3                     # added a line
36258b7 c1                     # created the file
                               # <- c2, which changed b's value, is missing

$ git log --oneline -Gb        # commits whose diff touches a line matching "b"
4ea7bd7 c3
5c894bd c2                     # <- found
36258b7 c1
```

Choose by the question:

| Question | Use |
|---|---|
| When was this symbol introduced or removed | `-S<symbol>` — it is asking about existence |
| When did this value / call / config change | `-G<regex>` — it is asking about edits |
| When did this exact line last change | `-L<start>,<end>:<file>` — it follows the range |

`-S` with `--pickaxe-regex` takes a pattern but keeps counting semantics; it
still misses an equal-count edit. Add `--all` when the change may live on a
branch that was never merged into the current one.

## `..` and `...` invert between `log` and `diff`

This is the single most costly confusion in this area, because both spellings
return plausible output.

| Command | Means | Use it for |
|---|---|---|
| `git log A..B` | commits reachable from B but not A | **the branch's own commits** |
| `git log A...B` | symmetric difference — commits on *either* side | comparing two divergent lines |
| `git diff A..B` | endpoint against endpoint | almost never during review |
| `git diff A...B` | merge-base of A and B, against B | **the branch's own changes** |

Measured on a fixture where `main` moved after `feat` branched:

```
$ git diff --stat main..feat
 1 file changed, 2 insertions(+), 3 deletions(-)   # includes undoing main's work

$ git diff --stat main...feat
 1 file changed, 1 insertion(+)                    # feat's actual contribution
```

So reviewing a branch means **`git diff main...feat` with three dots and
`git log main..feat` with two**. Same intent, different spelling. Getting either
one wrong changes what is reported, not whether the command succeeds.

#TODO(agent): DEFERRED the dot table is stated in both this set's reference pages, because a
skill cannot read another skill's directory once installed. Nothing checks the two copies still
agree — re-read the other page when editing this one.

## Blame, and the three flags that stop it lying

Plain `git blame` attributes a line to the last commit that touched it — which
is frequently a reformat, a rename, or a whitespace sweep.

```
git blame -w -M -C -- <path>
```

- `-w` ignores whitespace-only changes
- `-M` sees lines moved within the file
- `-C` sees lines copied from another file in the same commit (repeat as `-C -C`
  to search the commit's other files, `-C -C -C` to search all of history)

When blame still lands on a bulk commit, walk past it: `git log -L` on the range
shows every revision of those lines in order, which is the question blame was
being asked to answer.

## Finding code that is no longer there

Deleted code is not gone; it is unreachable from the working tree.

| Goal | Command |
|---|---|
| Which commit deleted this file | `git log --diff-filter=D --name-only -- '**/<name>'` |
| Where did this function go | `git log --all -S'<name>' --oneline` then read the diff |
| Grep the whole history | `git rev-list --all \| xargs git grep -n '<pattern>' --` |
| See the file as it was | `git show <commit>^:<path>` — note the `^`; at the deleting commit the path no longer exists |
| A commit you cannot reach any more | `git reflog` first, `git fsck --lost-found` second |

`git log -- <path>` alone stops at a rename unless `--follow` is given, and
`--follow` accepts exactly one path. A search that returns "no history before
2023" is usually a rename, not a rewrite.

## What history cannot tell you

- **A commit message states intent, not effect.** The claim in it was never
  checked by anything. Read the diff.
- **Squash-merge repositories have one commit per PR**, so blame points at the
  merge and `-S` lands on a batch. The PR discussion holds what the history does
  not; say so rather than presenting the squash as the origin.
- **A bug introduced dormant and exposed later** shows up at the exposing
  commit. History names the change, never the mechanism.

Every claim taken from history is `inspected`, never `executed`, and a claim
about *why* is `asserted` unless the reason is written down somewhere. Report it
at the grade it earned.
