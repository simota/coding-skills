#!/usr/bin/env python3
"""Prove each rule in validate.py fires.

A check only ever seen passing may be checking nothing. Every rule below gets a
deliberate violation injected into a throwaway copy of the repo, and the test
fails if the validator stays quiet.

Run: make test
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.dont_write_bytecode = True                     # no __pycache__ in the tools dir
import validate                                    # noqa: E402  — for RULES only


def run(root: Path) -> str:
    r = subprocess.run([sys.executable, str(root / "coding-tools" / "validate.py")],
                       capture_output=True, text=True)
    return r.stdout + r.stderr


S = "skills/"          # everything the CLI reads lives here


def sub(path: Path, old: str, new: str) -> None:
    t = path.read_text(encoding="utf-8")
    assert old in t, f"fixture text not found in {path.name}: {old[:60]!r}"
    path.write_text(t.replace(old, new, 1), encoding="utf-8")


# Each case mutates a copy, then expects that rule id in the output.
CASES: dict[str, callable] = {}


def case(rule):
    def deco(fn):
        CASES[rule] = fn
        return fn
    return deco


@case("V1")
def _(r): sub(r / f"{S}coding-test/SKILL.md", "## Owns", "## Owns\n" + "x\n" * 200)


@case("V2")
def _(r): sub(r / f"{S}coding-test/SKILL.md", "Building the checks",
              "Not for coding-debug. Building the checks")


@case("V3")
def _(r): (r / f"{S}coding-ghost").mkdir(); (r / f"{S}coding-ghost/SKILL.md").write_text("x")


@case("V4")
def _(r): (r / f"{S}coding-test/playbooks/orphan.md").write_text("<!-- coding:guidance -->\n")


@case("V5")
def _(r): (r / f"{S}coding-test/playbooks/flaky.md").write_text("y\n" * 400)


@case("V6")
def _(r): sub(r / f"{S}_coding/VALUES.md", "## 1. Honesty", "z\n" * 200 + "## 1. Honesty")


@case("V7")
def _(r): sub(r / "coding-registry/routes.yaml", "chain: [coding-explore, coding-test]",
              "chain: [coding-explore, coding-nonexistent]")


@case("V8")
def _(r): sub(r / "README.md", "](skills/_coding/ROUTING.md)", "](skills/_coding/GONE.md)")


@case("V9")
def _(r): sub(r / "coding-registry/capabilities.yaml", "signals: [where, how a path works",
              "signals: [interfaces, how a path works")


@case("V10")
def _(r): sub(r / "coding-registry/fixtures.yaml",
              '- ask: "where does the retry logic live"\n  expect: coding-explore',
              '- ask: "where does the retry logic live"\n  expect: coding-ship')


@case("V11")
def _(r):
    for i in range(4):
        d = r / f"{S}coding-extra{i}"
        d.mkdir()
        shutil.copy(r / f"{S}coding-test/SKILL.md", d / "SKILL.md")


@case("V12")
def _(r): (r / f"{S}rogue").mkdir(); (r / f"{S}rogue/SKILL.md").write_text("x")


@case("V13")
def _(r):
    t = (r / "coding-registry/routes.yaml").read_text(encoding="utf-8")
    t += "".join(f"\nfiller{i}:\n  pattern: linear\n  when: x\n  chain: [coding-test]\n"
                 for i in range(20))
    (r / "coding-registry/routes.yaml").write_text(t, encoding="utf-8")


@case("V14")
def _(r): sub(r / "coding-registry/routes.yaml", "  pattern: loop", "  pattern: spiral")


@case("V15")
def _(r): sub(r / f"{S}coding-review/SKILL.md", "allowed-tools: Read, Grep, Glob, Bash",
              "allowed-tools: Read, Grep, Glob, Bash, Edit, Write")


@case("V16")
def _(r): sub(r / f"{S}coding-test/SKILL.md", "## Done when", "## Finished when")


@case("V17")
def _(r): sub(r / f"{S}coding-test/SKILL.md", "- **Grade every claim**",
              "- **Grade some claims**")


@case("V18")
def _(r): sub(r / f"{S}coding-test/SKILL.md", "coverage", "reach")


@case("V19")
def _(r): sub(r / f"{S}coding-test/SKILL.md", "`_coding/SIZING.md`", "`../_coding/SIZING.md`")


@case("V20")
def _(r):
    f = r / f"{S}_coding/CONTRACT.md"
    f.write_text(f.read_text(encoding="utf-8").replace("asserted", "claimed"),
                 encoding="utf-8")


@case("V21")
def _(r): sub(r / f"{S}coding-test/SKILL.md",
              """A test is proved by watching it fail and then pass (evidence: `executed`).
Both halves are required — a test that was never seen red is `inspected` at
best, and the entry says why it could not be made to fail.""",
              "A test is proved by watching it fail and then pass.")


@case("V22")
def _(r): sub(r / f"{S}coding-test/SKILL.md", "## Done when",
              "## Done when\n\n#" + "TODO(agent): tidy this up later\n")


@case("V23")
def _(r): sub(r / f"{S}_coding/VALUES.md", "<!-- coding:contract -->", "<!-- coding:guidance -->")


@case("V24")
def _(r): sub(r / f"{S}_coding/ROUTING.md", "`coding-ship`", "`coding-deploy`")


@case("V25")
def _(r): sub(r / f"{S}coding-test/playbooks/flaky.md", "# ", "# pinned at v2.14.0 — ")


@case("V19-shared")
def _(r): sub(r / f"{S}_coding/ROUTING.md", "(`_coding/SIZING.md`)", "(`SIZING.md`)")


@case("V27")
def _(r):
    (r / f"{S}coding-test/_coding").unlink()
    (r / f"{S}coding-test/_coding").symlink_to("../_gone")


@case("V28")
def _(r): sub(r / "coding-registry/harness.yaml", "set: coding", "set: dev")


@case("V28-generic-dir")
def _(r): (r / "registry").mkdir()


@case("V26")
def _(r): sub(r / "coding-registry/capabilities.yaml", "      go: coding-debug",
              "      go: coding-diagnose")


@case("V29")
def _(r):
    d = r / f"{S}coding-test/reference"
    d.mkdir(exist_ok=True)   # the set now ships a reference layer
    (d / "headerless.md").write_text("<!-- coding:deferred -->\n# No headers\n")
    sub(r / f"{S}coding-test/SKILL.md", "| A test passes sometimes |",
        "| Something deferred | [headerless](reference/headerless.md) |\n| A test passes sometimes |")


@case("V30")
def _(r):
    d = r / f"{S}coding-test/reference"
    d.mkdir(exist_ok=True)   # the set now ships a reference layer
    (d / "orphan.md").write_text(
        "<!-- coding:deferred -->\n# Orphan\n\nPurpose: x\nRead when: y\nVerified: 2026-08-21\n")


@case("V31")
def _(r):
    for f in sorted((r / f"{S}").glob("*/reference/*.md")):
        t = f.read_text()
        i = t.index("Verified:")
        j = t.index("\n\n", i)
        f.write_text(t[:i] + "Verified: 2026-08-21" + t[j:])
        return


@case("V32")
def _(r):
    sub(r / "coding-registry/routes.yaml", "checker: ", "checker: claude  # ")


@case("V32-unknown")
def _(r):
    sub(r / "coding-registry/routes.yaml", "checker: ", "checker: nosuchengine  # ")



@case("V32-single")
def _(r):
    sub(r / "coding-registry/harness.yaml",
        "runs_on: [claude, codex, agy]", "runs_on: [claude]")



@case("V33")
def _(r):
    sub(r / "coding-registry/harness.yaml", "  lens: |", "  lens: ''\n  unused: |")



@case("V34")
def _(r):
    """Reachable and runnable must move together, whichever way they are split."""
    for d in sorted((r / "skills").glob("coding-*")):
        link = d / "refute.py"
        if link.is_symlink():
            link.unlink()                      # runnable, and now out of reach
            return
    # No set-wide link to remove: make a skill runnable instead, and leave it
    # unreachable. Widening a class trips V15 too, which the harness allows —
    # it only asks that V34 appear.
    sub(r / "coding-registry/harness.yaml",
        "tools: \"Read, Grep, Glob, Write", "tools: \"Read, Grep, Glob, Bash, Write")


@case("V34-decoration")
def _(r):
    """A link where the class grants no shell reads like a capability and is not one."""
    import yaml as _y
    caps = _y.safe_load((r / "coding-registry/capabilities.yaml").read_text())
    cls = _y.safe_load((r / "coding-registry/harness.yaml").read_text())["permission_classes"]
    for name, e in caps.items():
        if "Bash" not in cls[e["class"]]["tools"]:
            (r / "skills" / name / "refute.py").symlink_to("../../coding-tools/refute.py")
            return
    for d in sorted((r / "skills").glob("coding-*")):
        link = d / "refute.py"
        if link.is_symlink():
            link.unlink()
            link.symlink_to("../../coding-tools/render.py")   # the set's own, but the wrong tool
            return


@case("V35")
def _(r): sub(r / "coding-registry/harness.yaml", "required_of: [coding-debug",
              "required_of: [coding-explore, coding-debug")


def main() -> int:
    baseline = run(ROOT)
    if "green" not in baseline:
        print("the working tree is already failing; fix that first:\n" + baseline)
        return 1

    bad: list[str] = []
    for rule, mutate in CASES.items():
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "repo"
            shutil.copytree(ROOT, copy, symlinks=True,
                            ignore=shutil.ignore_patterns(".git", "__pycache__"))
            mutate(copy)
            out = run(copy)
            expect = rule.split("-")[0]
            if not re.search(rf"^\s*{expect}: ", out, re.M):
                bad.append(rule)
                print(f"  {rule} did not fire\n{out}")

    print(f"{len(CASES)} rules exercised, {len(bad)} silent")
    if bad:
        print("silent: " + ", ".join(bad))
        return 1

    # Counting the cases that exist says nothing about the rules that do. A rule
    # added without a case left this printing "every rule fires" about it.
    covered = {c.split("-")[0] for c in CASES}
    declared = {fn.__name__.split("_")[0].upper() for fn in validate.RULES}
    untested = sorted(declared - covered, key=lambda r: int(r[1:]))
    if untested:
        print("no deliberate violation is injected for: " + ", ".join(untested))
        return 1
    print(f"every rule fires ({len(declared)} rules, {len(CASES)} cases)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
