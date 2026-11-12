#!/usr/bin/env python3
"""The setup skill's shapes and its proof procedure, run as a host would run them.

A template is a claim about what works in someone else's repository. Each case
here came from a review finding that was reproduced before it was fixed.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "coding-setup"
TEMPLATES = (SKILL / "reference" / "templates.md").read_text(encoding="utf-8")
LAY = (SKILL / "playbooks" / "lay.md").read_text(encoding="utf-8")
SKILL_MD = (SKILL / "SKILL.md").read_text(encoding="utf-8")


def section(page: str, heading: str) -> str:
    """The text under one `## heading`, to the next heading of that level."""
    return re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", page, re.S | re.M).group(1)


def shape(heading: str) -> str:
    """The first fenced block after a heading of the templates page. Read from
    the heading on, since a shape may carry `## ` lines of its own."""
    rest = TEMPLATES[TEMPLATES.index(f"\n## {heading}\n"):]
    return re.search(r"^```\w*\n(.*?)^```", rest, re.S | re.M).group(1)


def step(page: str, heading: str, number: int) -> str:
    """One numbered step of a section, with its continuation lines."""
    return re.search(rf"^{number}\. (.*?)(?=^\d+\. |\Z)", section(page, heading),
                     re.S | re.M).group(1)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, text=True,
                          capture_output=True).stdout


class Workflow(unittest.TestCase):
    def setUp(self) -> None:
        self.doc = yaml.safe_load(shape("The CI workflow"))
        # YAML 1.1 reads a bare `on` as the boolean true.
        self.triggers = self.doc.get("on", self.doc.get(True))

    def test_runs_when_a_merge_queue_asks(self) -> None:
        """lay.md has the human turn on a merge queue; a required check that
        never reports there leaves every queued pull request waiting."""
        self.assertIn("merge queue", section(LAY, "Forge settings"))
        self.assertIn("merge_group", self.triggers)

    def test_keeps_the_hidden_log_directory(self) -> None:
        """upload-artifact leaves hidden files out unless told otherwise, and
        the verify script writes every log under a dot directory."""
        uploads = [s for job in self.doc["jobs"].values() for s in job["steps"]
                   if "upload-artifact" in s.get("uses", "")]
        self.assertTrue(uploads)
        for upload in uploads:
            if any(p.startswith(".") for p in upload["with"]["path"].split()):
                self.assertIs(upload["with"].get("include-hidden-files"), True)


class PullRequestTemplate(unittest.TestCase):
    def test_asks_for_the_count_the_safety_rule_leans_on(self) -> None:
        self.assertIn("count of tests", section(LAY, "The safety rules every host gets"))
        self.assertRegex(shape("The pull request template"), r"how many tests ran")


class Proof(unittest.TestCase):
    """The proof is run where it will be run: straight after lay, with the
    files lay wrote still uncommitted."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        git(self.repo, "init", "-q")
        (self.repo / "product.txt").write_text("ok\n")
        git(self.repo, "add", "product.txt")
        git(self.repo, "-c", "user.name=t", "-c", "user.email=t@example.invalid",
            "commit", "-qm", "base")
        script = shape("The verify script") \
            .replace("<default branch>", "HEAD") \
            .replace("<shared code>", "shared/") \
            .replace("  : # run unit        <unit tests>", "  run unit grep -q ok product.txt") \
            .replace("  : # run integration <integration tests>",
                     "  run integration grep -q ok product.txt") \
            .replace('  : # run related <the host\'s command for the tests that reach these files> "${changed[@]}"',
                     '  run related grep -q ok "${changed[@]}"')
        for check in ("unit", "integration", "related"):
            self.assertIn(f"run {check} grep", script)
        (self.repo / "scripts").mkdir()
        self.script = self.repo / "scripts" / "verify.sh"
        self.script.write_text(script)
        (self.repo / ".gitignore").write_text(".verify/\n")

    def verify(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["./scripts/verify.sh", *args], cwd=self.repo, text=True,
                              capture_output=True)

    def commit_all(self) -> None:
        git(self.repo, "add", "-A")
        git(self.repo, "-c", "user.name=t", "-c", "user.email=t@example.invalid",
            "commit", "-qm", "lay")

    def test_the_script_is_made_executable_before_anything_calls_it(self) -> None:
        """Written by a file tool it is not executable, and the workflow, the
        rules and the proof all call it by path."""
        self.assertFalse(os.access(self.script, os.X_OK))
        with self.assertRaises(PermissionError):
            self.verify()
        self.assertIn("executable", step(LAY, "The order", 1))

    def test_a_tree_holding_what_lay_wrote_is_not_refused(self) -> None:
        """Lay commits nothing, so a proof that needs a tree with no
        uncommitted work can never start, and a worktree has no script in it."""
        self.assertNotEqual(git(self.repo, "status", "--porcelain"), "")
        self.assertNotIn("no uncommitted work", step(LAY, "Proving the gate", 1))
        self.assertNotIn("over uncommitted work", SKILL_MD)
        self.assertNotIn("shown clean", SKILL_MD)
        # The report asks for what the proof leaves, and that is not a clean tree.
        self.assertNotIn("clean tree", section(LAY, "What it leaves behind"))

    def test_a_break_is_planted_and_undone_beside_uncommitted_files(self) -> None:
        self.script.chmod(0o755)
        before = git(self.repo, "status", "--porcelain")
        self.assertEqual(self.verify().returncode, 0)
        self.assertEqual(self.verify("--full").returncode, 0)
        (self.repo / "product.txt").write_text("planted\n")
        red = self.verify()
        self.assertEqual(red.returncode, 1)
        self.assertIn("verify: FAILED: unit", red.stdout)
        git(self.repo, "restore", "product.txt")
        self.assertEqual(git(self.repo, "status", "--porcelain"), before)
        self.assertEqual(self.verify("--full").returncode, 0)

    def test_the_full_set_is_seen_green_before_it_is_seen_red(self) -> None:
        """A check that was red all along reads exactly like one the planted
        break turned red, and the default run never runs it."""
        self.script.write_text(self.script.read_text().replace(
            "run integration grep -q ok product.txt", "run integration false"))
        self.script.chmod(0o755)
        self.commit_all()
        self.assertEqual(self.verify().returncode, 0)
        already_red = self.verify("--full")
        self.assertIn("verify: FAILED: integration", already_red.stdout)
        self.assertIn("--full", step(LAY, "Proving the gate", 2))
        self.assertIn("--full", section(SKILL_MD, "Verify with"))


    def test_the_default_run_holds_only_the_checks_that_reach_the_change(self) -> None:
        """A one-line change that runs every check is a change after which
        nobody runs the checks."""
        self.script.chmod(0o755)
        self.commit_all()
        (self.repo / "product.txt").write_text("ok, edited\n")
        green = self.verify()
        self.assertEqual(green.returncode, 0, green.stdout)
        self.assertIn("== related", green.stdout)
        self.assertNotIn("== unit", green.stdout)
        (self.repo / "product.txt").write_text("planted\n")
        red = self.verify()
        self.assertEqual(red.returncode, 1)
        self.assertIn("verify: FAILED: related", red.stdout)

    def test_an_untouched_tree_runs_no_related_check(self) -> None:
        self.script.chmod(0o755)
        self.commit_all()
        run = self.verify()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertNotIn("== related", run.stdout)

    def test_a_widening_or_deleted_path_runs_every_check(self) -> None:
        """What a shared module or a removed file reaches, no related-tests
        command can name."""
        self.script.chmod(0o755)
        (self.repo / "shared").mkdir()
        (self.repo / "shared" / "lib.txt").write_text("ok\n")
        (self.repo / "gone.txt").write_text("ok\n")
        self.commit_all()
        (self.repo / "shared" / "lib.txt").write_text("ok, edited\n")
        widened = self.verify()
        self.assertIn("shared/lib.txt widens the change", widened.stdout)
        self.assertIn("== integration", widened.stdout)
        git(self.repo, "restore", "shared/lib.txt")
        (self.repo / "gone.txt").unlink()
        deleted = self.verify()
        self.assertIn("gone.txt widens the change", deleted.stdout)
        self.assertIn("== unit", deleted.stdout)

    def test_each_check_run_has_its_time_written(self) -> None:
        self.script.chmod(0o755)
        self.verify("--full")
        timings = (self.repo / ".verify" / "timings").read_text()
        self.assertEqual([line.split("\t")[0] for line in timings.splitlines()],
                         ["unit", "integration"])

    def test_a_baseline_comes_only_from_a_full_run_over_a_committed_tree(self) -> None:
        """A baseline taken over uncommitted work is not the commit's, and a
        later run reading it would blame the commit for that work."""
        self.script.chmod(0o755)
        self.verify("--full")
        self.assertEqual(list((self.repo / ".verify").glob("baseline-*")), [])
        self.commit_all()
        self.verify()
        self.assertEqual(list((self.repo / ".verify").glob("baseline-*")), [])
        self.verify("--full")
        sha = git(self.repo, "rev-parse", "HEAD").strip()
        self.assertEqual((self.repo / ".verify" / f"baseline-{sha}").read_text(), "verify: ok\n")

if __name__ == "__main__":
    unittest.main()
