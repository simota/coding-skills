<!-- coding:deferred -->
# Recovery — What Git Can Undo, and What Nothing Can

Purpose: Which destructive operations are reversible, by what command, and which destroy work no record holds.
Read when: before running anything that discards state — reset, restore, checkout, clean, stash, rebase, amend, force-push — or after one already ran.
Source: git — every row was produced against the git actually installed, so there is no version to pin.
Verified: 2026-08-21 — every row except the last two was produced by performing the operation in a fixture
repository and attempting the recovery; `git checkout <sha>` and `rm -rf` are stated without a run.
Re-run by `make figures` on every commit, against the git actually installed: a release that
changed one of these behaviours fails the build instead of quietly making the page wrong.

One line decides everything on this page:

> **Committed work is almost always recoverable. Uncommitted work usually is not.**

Git's safety net is the object store plus the reflog, and both only hold what
was written into them. A change that exists solely in the working tree has never
been written anywhere, so overwriting it leaves no trace to find — not a warning,
not a dangling object, nothing.

---

## The matrix

| Operation | What it discards | Recoverable? | How |
|---|---|---|---|
| `git reset --hard <sha>` | commits ahead of `<sha>` | **yes** | `git reflog`, then `git reset --hard <old-sha>` |
| `git rebase` gone wrong | the pre-rebase branch | **yes** | `git reflog`, or `git reset --hard ORIG_HEAD` |
| `git commit --amend` | the previous commit | **yes** | reflog holds the pre-amend commit |
| `git branch -D <name>` | the branch pointer | **yes** | reflog holds the tip; the commits were never removed |
| `git checkout <sha>` (detached work) | nothing, until GC | **yes** | `git reflog`, `git fsck --lost-found` |
| `git stash drop` / `stash clear` | the stash commit | **yes, until GC** | `git fsck --lost-found`, then `git show` each dangling commit |
| `git restore .` / `git checkout -- .` | **uncommitted** worktree edits | **no** | nothing recorded them |
| `git checkout -f` / `git switch --discard-changes` | uncommitted edits to **tracked** files | **no** | plain `checkout` refuses; `-f` removes the refusal. Untracked files survive — only `clean` takes those |
| `git clean -fd` | untracked files | **no** | git never had them |
| `rm -rf` on the worktree | everything uncommitted | **no** | — |

Measured, on a fixture:

```
reset --hard HEAD~1     -> reflog still lists the commit; reset back restores it
commit --amend          -> the pre-amend commit is still a valid object
branch -D doomed        -> "Deleted branch doomed (was e4e9b31)"; git branch restored e4e9b31
rebase gone wrong       -> ORIG_HEAD holds the pre-rebase tip; reset --hard ORIG_HEAD
stash drop              -> fsck --lost-found lists it as a dangling commit
edit f.txt; restore .   -> content gone; `git reflog | grep <content>` returns 0
clean -fd               -> the untracked file is destroyed, git has no record
```

**Two commands, two different halves.** `checkout -f` discards tracked edits and
leaves untracked files where they are; `clean -fd` removes untracked files and
does not touch tracked edits. Only running both destroys everything, which is why
"I ran checkout -f, my new file must be gone" is usually wrong — look before
concluding.

## `git add` is the cheapest insurance there is

Staging writes a blob into the object store. From that moment the *content* is
recoverable even if index and worktree are both wiped, because the blob outlives
the reference to it:

```
$ git add f.txt                      # content now in the object store
$ git restore --source=HEAD --staged --worktree .    # worktree and index wiped
$ git fsck --lost-found
dangling blob fd6d6213...
$ git cat-file -p fd6d6213
PRECIOUS-STAGED-WORK                 # recovered
```

So the rule before any destructive operation is one of:

1. `git add -A` — content survives in the object store, findable via `fsck`
2. `git stash -u` — **`-u` is required**; plain `git stash` leaves untracked
   files in the worktree, where the next `clean -fd` takes them
3. `git commit` on a scratch branch — the strongest, and the reflog indexes it

A verified fixture run: with untracked `untracked.txt` present, `git stash`
stashed the tracked edit and **left `untracked.txt` in place**.

## Reading the reflog

```
git reflog                       # HEAD's movements
git reflog show <branch>         # one branch's movements
git fsck --lost-found            # objects no reference points at
```

Entries expire — reachable ones after 90 days, unreachable ones after 30 by
default — and `git gc --prune=now` expires them immediately. Recovery is a
question with a deadline, so it is attempted before anything else, not after
finishing the task that motivated the reset.

`ORIG_HEAD` is set by `merge`, `rebase`, `reset`, and `pull`, and it holds only
the *previous* one. A second operation overwrites it; the reflog does not.

## Anything that leaves the machine

`git push --force` overwrites a remote branch. Whether it is recoverable depends
on a server-side reflog nobody in this session can see, and on whoever else had
the branch checked out.

- Use `--force-with-lease` (better, `--force-with-lease --force-if-includes`).
  Plain `--force` overwrites a colleague's push it never saw.
- **Ask before any force-push, tag move, or history rewrite of a pushed
  branch.** Being asked to finish the work is not permission to reshape what
  other people have already pulled.
- A secret that was pushed is rotated, not removed. Rewriting history does not
  recall the copies, the forks, the CI logs, or the caches.
