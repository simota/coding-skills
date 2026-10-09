#!/usr/bin/env python3
"""Re-run the git behaviour the reference layer states, and compare.

The reference pages claim things about git that are true of the git they were
written against: that `-S` misses an equal-count edit, that three-dot diff means
merge-base, that `restore .` leaves no trace and `git add` does. A `Verified:`
date cannot notice when a new git changes one of those, and neither can a reader.

    make figures

Every check builds a throwaway repository, runs the command, and compares the
result to what the page prints. Where the page prints an output, that output is
parsed from the page rather than restated here, so editing the page to say
something false fails too.
"""
from __future__ import annotations

import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
HISTORY = SKILLS / "coding-explore/reference/history.md"
SCOPING = SKILLS / "coding-review/reference/diff-scoping.md"
RECOVERY = SKILLS / "coding-ship/reference/recovery.md"
failures: list[str] = []

# The user's own git configuration is not part of the claim. A global hooks
# path, a commit template or a signing requirement would change what these
# commands do — or make a setup commit fail quietly — on one machine only.
GIT_ENV = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C"}


def fail(page: pathlib.Path, msg: str) -> None:
    failures.append(f"  {page.name}: {msg}")


class Repo:
    def __init__(self, d: pathlib.Path):
        self.d = d
        self.must("init", "-q")
        self.must("config", "user.email", "check@example.invalid")
        self.must("config", "user.name", "check")
        self.must("config", "commit.gpgsign", "false")

    def git(self, *args: str) -> str:
        r = subprocess.run(("git", *args), cwd=self.d, capture_output=True, text=True,
                           env=GIT_ENV)
        return (r.stdout + r.stderr).strip()

    def must(self, *args: str) -> None:
        """A setup step. If it fails, every comparison after it is against nothing."""
        r = subprocess.run(("git", *args), cwd=self.d, capture_output=True, text=True,
                           env=GIT_ENV)
        if r.returncode != 0:
            raise RuntimeError(f"setup `git {' '.join(args)}` failed in {self.d.name}: "
                               f"{(r.stderr or r.stdout).strip()}")

    def write(self, name: str, body: str) -> None:
        (self.d / name).write_text(body)

    def commit(self, msg: str) -> None:
        self.must("add", "-A")
        self.must("commit", "-qm", msg)


def fenced(page: pathlib.Path, contains: str) -> list[str]:
    """The lines of the first fenced block containing a marker string."""
    blocks, cur, inside = [], [], False
    for line in page.read_text().splitlines():
        if line.startswith("```"):
            if inside:
                blocks.append(cur)
                cur = []
            inside = not inside
            continue
        if inside:
            cur.append(line)
    for b in blocks:
        if any(contains in l for l in b):
            return b
    fail(page, f"no fenced block containing {contains!r} — "
               "the checker has stopped checking anything")
    return []


def subjects(out: str) -> list[str]:
    return [l.split(maxsplit=1)[1] for l in out.splitlines() if " " in l]


def printed_subjects(block: list[str], command: str) -> list[str]:
    """The `<sha> <subject>` lines the page prints under one `$ git …` command.

    The listing ends at the next prompt, and a trailing `# …` note is the page's
    commentary, not output. Reading the whole block instead once took one
    command's expectation from the other's listing, and passed by coincidence.
    """
    out, inside = [], False
    for line in block:
        if line.startswith("$ "):
            inside = command in line
            continue
        bare = line.split("#", 1)[0].strip()
        if inside and re.fullmatch(r"[0-9a-f]{7} c\d", bare):
            out.append(bare.split()[-1])
    return out


def check_pickaxe(tmp: pathlib.Path) -> int:
    """history.md: -S counts occurrences, -G matches lines, so an equal-count
    edit is invisible to -S."""
    r = Repo(tmp / "pickaxe")
    r.write("f.txt", "a=1\nb=2\n"); r.commit("c1")
    r.write("f.txt", "a=1\nb=3\n"); r.commit("c2")
    r.write("f.txt", "a=1\nb=3\nb=4\n"); r.commit("c3")
    got_s, got_g = subjects(r.git("log", "--oneline", "-Sb")), subjects(r.git("log", "--oneline", "-Gb"))
    want_s = printed_subjects(fenced(HISTORY, "-Sb"), "log --oneline -Sb")
    want_g = printed_subjects(fenced(HISTORY, "-Gb"), "log --oneline -Gb")
    n = 0
    if not want_s:
        # The listing is what the comparison is against. Skipping when it stops
        # parsing means an edit to the printed output drops the check and the
        # green line just counts one behaviour fewer.
        fail(HISTORY, "the `-Sb` block no longer prints a `<sha> <subject>` listing "
                      "to compare against — the checker has stopped checking anything")
    else:
        n += 1
        if got_s != want_s:
            fail(HISTORY, f"`log -Sb` found {got_s}, the page prints {want_s}")
    if not want_g:
        fail(HISTORY, "the `-Gb` block no longer prints a `<sha> <subject>` listing "
                      "to compare against — the checker has stopped checking anything")
    else:
        n += 1
        if got_g != want_g:
            fail(HISTORY, f"`log -Gb` found {got_g}, the page prints {want_g}")
    if "c2" in got_s:
        fail(HISTORY, "`-S` found the equal-count edit c2; the page's whole point is that it does not")
    if "c2" not in got_g:
        fail(HISTORY, "`-G` missed the equal-count edit c2, which the page says it catches")
    n += 2
    return n


def stat_counts(text: str) -> tuple[int, int] | None:
    """(insertions, deletions) from a `--stat` summary, or None if it prints none."""
    ins = re.search(r"(\d+) insertions?\(\+\)", text)
    dels = re.search(r"(\d+) deletions?\(-\)", text)
    if not (ins or dels):
        return None
    return (int(ins.group(1)) if ins else 0, int(dels.group(1)) if dels else 0)


def check_dots(tmp: pathlib.Path) -> int:
    """history.md and diff-scoping.md: two-dot diff compares tips, three-dot
    compares merge-base to the branch."""
    r = Repo(tmp / "dots")
    r.write("f.txt", "a=1\nb=2\n"); r.commit("c1")
    r.write("f.txt", "a=1\nb=3\nb=4\n"); r.commit("c3")
    base = r.git("rev-parse", "--abbrev-ref", "HEAD")
    r.must("checkout", "-q", "-b", "feat", "HEAD~1")
    r.write("f.txt", "a=1\nb=2\nnew\n"); r.commit("feat1")
    r.must("checkout", "-q", base)
    r.write("f.txt", "a=1\nb=3\nb=4\nmainonly\n"); r.commit("main-extra")
    two = r.git("diff", "--stat", f"{base}..feat")
    three = r.git("diff", "--stat", f"{base}...feat")
    n = 0
    # Both pages print the figures: history.md on the line after the command,
    # diff-scoping.md after an arrow on the same line. Either way the counts are
    # read off the page, so editing either page to a wrong figure fails.
    for page in (HISTORY, SCOPING):
        for marker, out, label in (("diff --stat main..feat", two, "two-dot"),
                                   ("diff --stat main...feat", three, "three-dot")):
            block = fenced(page, marker)
            stated = next((l for l in block if marker in l), None)
            if stated is None:
                fail(page, f"the block for {marker!r} no longer contains the command — "
                           "the checker has stopped checking anything")
                continue
            idx = block.index(stated)
            printed = stated.split(marker, 1)[1].split("#", 1)[0]
            if stat_counts(printed) is None and idx + 1 < len(block):
                printed = block[idx + 1].split("#", 1)[0]
            want = stat_counts(printed)
            if want is None:
                fail(page, f"the {label} block no longer prints a --stat count — "
                           "the checker has stopped checking anything")
                continue
            n += 1
            if stat_counts(out) != want:
                fail(page, f"{label} diff gave {out.splitlines()[-1].strip()!r}, "
                           f"the page prints {printed.strip()!r}")
    if stat_counts(three) != (1, 0):
        fail(HISTORY, "three-dot diff no longer isolates the branch's own change")
    if three == two:
        fail(HISTORY, "two-dot and three-dot diff agree; the page's central claim is that they differ")
    n += 2
    return n


def check_scoping(tmp: pathlib.Path) -> int:
    """diff-scoping.md: git diff / --staged / HEAD each show a different subset,
    and none of them shows an untracked file."""
    r = Repo(tmp / "scope")
    r.write("f.txt", "base\n"); r.commit("c1")
    r.write("f.txt", "base\nwork-tree-edit\n")
    r.write("s.txt", "staged\n"); r.must("add", "s.txt")
    r.write("u.txt", "never-added\n")
    got = {
        "git diff": r.git("diff", "--name-only").split(),
        "git diff --staged": r.git("diff", "--staged", "--name-only").split(),
        "git diff HEAD": r.git("diff", "HEAD", "--name-only").split(),
    }
    want = {"git diff": ["f.txt"], "git diff --staged": ["s.txt"],
            "git diff HEAD": ["f.txt", "s.txt"]}
    n = 0
    for cmd, expect in want.items():
        n += 1
        if sorted(got[cmd]) != sorted(expect):
            fail(SCOPING, f"`{cmd}` showed {got[cmd]}, the page says {expect}")
    if "u.txt" in sum(got.values(), []):
        fail(SCOPING, "an untracked file appeared in a diff; the page says none of them show it")
    porcelain = r.git("status", "--porcelain")
    if "?? u.txt" not in porcelain:
        fail(SCOPING, f"`status --porcelain` did not list the untracked file: {porcelain!r}")
    n += 2
    empty = Repo(tmp / "empty")
    empty.write("a.txt", "x\n")
    if "fatal" not in empty.git("rev-parse", "HEAD").lower():
        fail(SCOPING, "`rev-parse HEAD` resolved in a repository with no commits; "
                      "the page says it does not")
    n += 1
    return n


def check_recovery(tmp: pathlib.Path) -> int:
    """recovery.md: committed work is recoverable, uncommitted work is not, and
    `git add` alone puts content where fsck can still reach it."""
    n = 0
    r = Repo(tmp / "reset")
    r.write("f.txt", "v1\n"); r.commit("c1")
    r.write("f.txt", "valuable\n"); r.commit("c2")
    sha = r.git("rev-parse", "--short", "HEAD")
    r.must("reset", "-q", "--hard", "HEAD~1")
    if sha not in r.git("reflog", "--format=%h"):
        fail(RECOVERY, "reset --hard left no reflog entry; the page says it is recoverable")
    n += 1

    r2 = Repo(tmp / "restore")
    r2.write("f.txt", "committed\n"); r2.commit("c1")
    r2.write("f.txt", "committed\nUNSAVED\n")
    r2.git("restore", ".")
    if "UNSAVED" in (r2.d / "f.txt").read_text() or "UNSAVED" in r2.git("reflog"):
        fail(RECOVERY, "`restore .` left the uncommitted edit somewhere; "
                       "the page says nothing recorded it")
    n += 1

    r3 = Repo(tmp / "staged")
    r3.write("f.txt", "committed\n"); r3.commit("c1")
    r3.write("f.txt", "PRECIOUS-STAGED-WORK\n"); r3.must("add", "f.txt")
    r3.git("restore", "--source=HEAD", "--staged", "--worktree", ".")
    blobs = [l.split()[2] for l in r3.git("fsck", "--lost-found").splitlines()
             if "dangling blob" in l]
    if not any("PRECIOUS-STAGED-WORK" in r3.git("cat-file", "-p", b) for b in blobs):
        fail(RECOVERY, "a staged blob was not reachable via fsck; "
                       "the page's cheapest-insurance claim rests on it")
    n += 1

    r4 = Repo(tmp / "untracked")
    r4.write("f.txt", "committed\n"); r4.commit("c1")
    r4.write("f.txt", "committed\ntracked-edit\n")
    r4.write("untracked.txt", "brand-new\n")
    r4.must("stash", "-q")
    if not (r4.d / "untracked.txt").exists():
        fail(RECOVERY, "`git stash` took the untracked file; the page says `-u` is required")
    n += 1

    r5 = Repo(tmp / "force")
    r5.write("f.txt", "committed\n"); r5.commit("c1")
    r5.write("f.txt", "committed\nedit\n")
    r5.write("newfile.txt", "untracked\n")
    r5.git("checkout", "-f")
    if "edit" in (r5.d / "f.txt").read_text():
        fail(RECOVERY, "`checkout -f` kept the tracked edit; the page says it discards it")
    if not (r5.d / "newfile.txt").exists():
        fail(RECOVERY, "`checkout -f` removed an untracked file; the page says only `clean` does")
    n += 2

    r6 = Repo(tmp / "gc")
    r6.write("f.txt", "v1\n"); r6.commit("c1")
    r6.write("f.txt", "v2\n"); r6.commit("c2")
    gone = r6.git("rev-parse", "--short", "HEAD")
    r6.must("reset", "-q", "--hard", "HEAD~1")
    r6.must("gc", "-q", "--prune=now")
    if gone not in r6.git("reflog", "--format=%h"):
        fail(RECOVERY, "`gc --prune=now` expired a reflog entry; the page says only "
                       "`reflog expire` does")
    n += 1

    r7 = Repo(tmp / "switch")
    r7.write("f.txt", "committed\n"); r7.commit("c1")
    base = r7.git("rev-parse", "--abbrev-ref", "HEAD")
    r7.must("checkout", "-q", "-b", "other")
    r7.write("n.txt", "tracked-on-other\n"); r7.commit("add n")
    r7.must("checkout", "-q", base)
    r7.write("n.txt", "MINE-UNTRACKED\n")
    if "would be overwritten" not in r7.git("checkout", "other"):
        fail(RECOVERY, "plain `checkout <branch>` did not refuse to overwrite an untracked "
                       "file; the page says it refuses")
    r7.git("checkout", "-q", "-f", "other")
    if "MINE-UNTRACKED" in (r7.d / "n.txt").read_text():
        fail(RECOVERY, "`checkout -f <branch>` kept an untracked file the branch tracks; "
                       "the page says it overwrites it")
    n += 2

    r8 = Repo(tmp / "branchd")
    r8.write("f.txt", "v1\n"); r8.commit("c1")
    r8.must("branch", "doomed")
    r8.git("branch", "-D", "doomed")
    if (r8.d / ".git" / "logs" / "refs" / "heads" / "doomed").exists():
        fail(RECOVERY, "`branch -D` left the branch's own reflog; the page says it goes too")
    n += 1
    return n


def main() -> int:
    if not shutil.which("git"):
        print("figures skipped - git is not on PATH")
        return 0
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="coding-figures-"))
    try:
        for d in ("pickaxe", "dots", "scope", "empty", "reset", "restore",
                  "staged", "untracked", "force", "gc", "switch", "branchd"):
            (tmp / d).mkdir()
        checks = (check_pickaxe(tmp) + check_dots(tmp)
                  + check_scoping(tmp) + check_recovery(tmp))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if failures:
        print(f"{len(failures)} claim(s) the current git does not support:")
        print("\n".join(failures))
        return 1
    ver = subprocess.run(["git", "--version"], capture_output=True, text=True).stdout.strip()
    print(f"figures green - {checks} documented git behaviours re-run against {ver}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
