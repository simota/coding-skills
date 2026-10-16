#!/usr/bin/env python3
"""Exercise installation and staged-tree checks in disposable repositories.

All host paths, hooks, Git configuration and temporary snapshots belong to the
fixture. These checks must never install a skill in the developer's home.
"""
from __future__ import annotations

import os
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "coding-tools/githooks/pre-commit"


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="coding-install-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        self.scratch = self.base / "scratch"
        self.scratch.mkdir()
        self.env = {key: value for key, value in os.environ.items()
                    if not key.startswith("GIT_")}
        self.env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
                        XDG_CONFIG_HOME=os.devnull, TMPDIR=str(self.scratch))
        for key in ("MAKEFLAGS", "MAKEOVERRIDES", "MFLAGS"):
            self.env.pop(key, None)
        self.git("init", "-q")

    def git(self, *args, env=None):
        result = subprocess.run(["git", *args], cwd=self.repo,
                                env=self.env if env is None else env,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout.strip()

    def commit(self):
        self.git("-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "-c", "core.hooksPath=" + os.devnull,
                 "commit", "-qm", "fixture")


class InstallCommands(Fixture):
    def setUp(self):
        super().setUp()
        shutil.copy2(ROOT / "Makefile", self.repo / "Makefile")
        (self.repo / "coding-tools/githooks").mkdir(parents=True)
        shutil.copy2(HOOK, self.repo / "coding-tools/githooks/pre-commit")
        self.skill = self.repo / "skills/coding-example"
        self.skill.mkdir(parents=True)
        (self.skill / "SKILL.md").write_text("fixture\n", encoding="utf-8")
        self.host = self.base / "host"
        self.host.mkdir()
        self.skills = self.host / "skills"

    def make(self, target, *args, env=None):
        return subprocess.run(
            ["make", "-s", "--no-print-directory", target,
             "CLAUDE_DIR=" + str(self.skills),
             "CODEX_DIR=" + str(self.base / "absent-codex/skills"),
             "AGY_DIR=" + str(self.base / "absent-agy/skills"), *args],
            cwd=self.repo, env=self.env if env is None else env,
            capture_output=True, text=True)

    def fail_command(self, command):
        directory = self.base / "bin"
        directory.mkdir(exist_ok=True)
        executable = directory / command
        executable.write_text("#!/bin/sh\nexit 23\n", encoding="utf-8")
        executable.chmod(0o755)
        return {**self.env, "PATH": str(directory) + os.pathsep + self.env["PATH"]}

    def test_link_reports_a_directory_creation_failure(self):
        self.skills.write_text("a file already occupies this path\n", encoding="utf-8")
        result = self.make("link")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("  link coding-example", result.stdout)
        self.assertTrue(self.skills.is_file())

    def test_link_reports_a_symlink_creation_failure(self):
        result = self.make("link", env=self.fail_command("ln"))
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("  link coding-example", result.stdout)
        self.assertFalse((self.skills / "coding-example").exists())

    def test_unlink_reports_a_removal_failure(self):
        self.skills.mkdir()
        target = self.skills / "coding-example"
        target.symlink_to(self.skill, target_is_directory=True)
        result = self.make("unlink", env=self.fail_command("rm"))
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("  unlink coding-example", result.stdout)
        self.assertTrue(target.is_symlink())

    def test_repository_and_host_paths_are_data_not_shell_code(self):
        new_repo = self.base / 'repo `touch repo_marker` "quoted"'
        self.repo.rename(new_repo)
        self.repo = new_repo
        self.skill = self.repo / "skills/coding-example"
        self.host = self.base / 'host `touch host_marker` "quoted"'
        self.host.mkdir()
        self.skills = self.host / "skills"
        for target in ("link", "status", "unlink"):
            with self.subTest(target=target):
                result = self.make(target)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertFalse((self.repo / "repo_marker").exists())
                self.assertFalse((self.repo / "host_marker").exists())
                if target == "link":
                    self.assertEqual((self.skills / "coding-example").resolve(), self.skill)
                if target == "unlink":
                    self.assertFalse((self.skills / "coding-example").is_symlink())

    def test_a_host_path_is_not_expanded_as_a_make_expression(self):
        self.host = self.base / "host $(shell touch make_marker)"
        self.host.mkdir()
        self.skills = self.host / "skills"
        result = self.make("link")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.repo / "make_marker").exists())
        self.assertEqual((self.skills / "coding-example").resolve(), self.skill)

    def test_refute_preserves_a_claims_path_without_evaluating_it(self):
        (self.repo / "coding-tools/refute.py").write_text(
            "import json, sys\nprint(json.dumps(sys.argv[1:]))\n", encoding="utf-8")
        claims = 'claims $(shell touch claims_marker) `touch shell_marker` "quoted".json'
        result = self.make("refute", "CLAIMS=" + claims, "RUNNING=codex")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout), ["--running", "codex", claims])
        self.assertFalse((self.repo / "claims_marker").exists())
        self.assertFalse((self.repo / "shell_marker").exists())

    def test_link_and_unlink_preserve_foreign_paths_even_when_forced(self):
        self.skills.mkdir()
        target = self.skills / "coding-example"
        foreign = self.base / "foreign-skill"
        foreign.mkdir()
        (foreign / "keep").write_text("keep\n", encoding="utf-8")
        target.symlink_to(foreign, target_is_directory=True)
        for command in ("link", "unlink"):
            result = self.make(command, "FORCE=1")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(target.resolve(), foreign)
            self.assertEqual((foreign / "keep").read_text(), "keep\n")
        target.unlink()
        target.mkdir()
        for command in ("link", "unlink"):
            result = self.make(command, "FORCE=1")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(target.is_dir())
            self.assertFalse(target.is_symlink())

    def test_dangling_links_require_force_to_replace_or_remove(self):
        self.skills.mkdir()
        target = self.skills / "coding-example"
        missing = self.base / "missing"
        target.symlink_to(missing)
        for command in ("link", "unlink"):
            result = self.make(command)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(target.readlink(), missing)
        result = self.make("link", "FORCE=1")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(target.resolve(), self.skill)
        target.unlink()
        target.symlink_to(missing)
        result = self.make("unlink", "FORCE=1")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(target.is_symlink())

    def test_hooks_reject_a_shared_directory_reached_through_a_symlink(self):
        shared = self.base / "shared-hooks"
        shared.mkdir()
        (self.repo / "hook-alias").symlink_to(shared, target_is_directory=True)
        self.git("config", "core.hooksPath", "hook-alias")
        result = self.make("hooks")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((shared / "pre-commit").exists())
        result = self.make("hooks", "FORCE=1")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((shared / "pre-commit").read_bytes(), HOOK.read_bytes())

    def test_hooks_upgrade_an_earlier_copy_but_not_a_foreign_hook(self):
        source = self.repo / "coding-tools/githooks/pre-commit"
        self.git("add", ".")
        self.commit()
        result = self.make("hooks")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        installed = Path(self.git("rev-parse", "--path-format=absolute", "--git-path",
                                  "hooks/pre-commit"))
        source.write_text(source.read_text(encoding="utf-8") + "# changed upstream\n",
                          encoding="utf-8")
        self.git("add", ".")
        self.commit()
        result = self.make("hooks")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(installed.read_bytes(), source.read_bytes())
        installed.write_text("#!/bin/sh\necho someone else's\n", encoding="utf-8")
        result = self.make("hooks")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("someone else's", installed.read_text(encoding="utf-8"))

    def test_hooks_activate_the_source_when_hooks_path_already_points_to_it(self):
        source = self.repo / "coding-tools/githooks/pre-commit"
        source.chmod(0o644)
        self.git("config", "core.hooksPath", "coding-tools/githooks")
        result = self.make("hooks")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(os.access(source, os.X_OK))
        self.assertEqual(source.read_bytes(), HOOK.read_bytes())

    def test_shared_hooks_are_not_activated_without_force(self):
        source = self.repo / "coding-tools/githooks/pre-commit"
        source.chmod(0o644)
        shared = self.base / "shared-hooks"
        shared.mkdir()
        (shared / "pre-commit").symlink_to(source)
        self.git("config", "core.hooksPath", str(shared))
        result = self.make("hooks")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(os.access(source, os.X_OK))
        result = self.make("hooks", "FORCE=1")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(os.access(source, os.X_OK))


class PreCommit(Fixture):
    VALIDATOR = '''import pathlib
root = pathlib.Path(__file__).resolve().parent.parent
assert (root / "tracked.txt").read_text() == "good\\n"
'''

    def setUp(self):
        super().setUp()
        (self.repo / "coding-tools").mkdir()
        (self.repo / "coding-tools/validate.py").write_text(self.VALIDATOR, encoding="utf-8")
        (self.repo / "coding-tools/figures_check.py").write_text("pass\n", encoding="utf-8")
        (self.repo / "tracked.txt").write_text("good\n", encoding="utf-8")
        self.git("add", ".")

    def run_hook(self, env=None):
        return subprocess.run(["sh", str(HOOK)], cwd=self.repo,
                              env=self.env if env is None else env,
                              capture_output=True, text=True)

    def test_staged_bad_content_cannot_be_hidden_by_an_unstaged_fix(self):
        (self.repo / "tracked.txt").write_text("bad\n", encoding="utf-8")
        self.git("add", "tracked.txt")
        (self.repo / "tracked.txt").write_text("good\n", encoding="utf-8")
        result = self.run_hook()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git("show", ":tracked.txt"), "bad")
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_unstaged_bad_content_does_not_contaminate_the_snapshot(self):
        (self.repo / "tracked.txt").write_text("bad\n", encoding="utf-8")
        result = self.run_hook()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.repo / "tracked.txt").read_text(), "bad\n")
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_checkout_filters_cannot_repair_a_bad_staged_file(self):
        (self.repo / "tracked.txt").write_text("bad\n", encoding="utf-8")
        (self.repo / ".gitattributes").write_text("tracked.txt filter=repair\n", encoding="utf-8")
        self.git("add", ".")
        self.git("config", "filter.repair.smudge", "printf 'good\\n'")
        result = self.run_hook()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git("show", ":tracked.txt"), "bad")

    def test_replacement_objects_cannot_repair_a_bad_staged_file(self):
        good = self.git("rev-parse", ":tracked.txt")
        (self.repo / "tracked.txt").write_text("bad\n", encoding="utf-8")
        self.git("add", "tracked.txt")
        bad = self.git("rev-parse", ":tracked.txt")
        self.git("replace", bad, good)
        result = self.run_hook()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git("--no-replace-objects", "show", ":tracked.txt"), "bad")

    def test_snapshot_preserves_raw_blobs_symlinks_and_executable_modes(self):
        (self.repo / "alias").symlink_to("tracked.txt")
        unusual = "binary\tname\n.bin"
        contents = b"\x00\xff\r\nraw\x00bytes\n"
        (self.repo / unusual).write_bytes(contents)
        executable = self.repo / "run"
        executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        executable.chmod(0o755)
        validator = self.repo / "coding-tools/validate.py"
        validator.write_text(self.VALIDATOR + f'''import os
assert (root / "alias").is_symlink()
assert os.readlink(root / "alias") == "tracked.txt"
assert (root / {unusual!r}).read_bytes() == {contents!r}
assert os.access(root / "run", os.X_OK)
''', encoding="utf-8")
        self.git("add", ".")
        result = self.run_hook()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_snapshot_creates_an_empty_directory_for_a_submodule(self):
        self.commit()
        commit = self.git("rev-parse", "HEAD")
        self.git("update-index", "--add", "--cacheinfo", "160000," + commit + ",module")
        validator = self.repo / "coding-tools/validate.py"
        validator.write_text(self.VALIDATOR + '''assert (root / "module").is_dir()
assert list((root / "module").iterdir()) == []
''', encoding="utf-8")
        self.git("add", "coding-tools/validate.py")
        result = self.run_hook()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unstaged_python_modules_cannot_shadow_the_snapshot_helper(self):
        (self.repo / "pathlib.py").write_text(
            'raise RuntimeError("an unstaged module was imported")\n', encoding="utf-8")
        result = self.run_hook()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_sparse_checkout_still_checks_the_complete_commit(self):
        self.git("update-index", "--skip-worktree", "tracked.txt")
        (self.repo / "tracked.txt").unlink()
        before = self.git("ls-files", "-v", "--stage")
        result = self.run_hook()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git("ls-files", "-v", "--stage"), before)
        self.assertFalse((self.repo / "tracked.txt").exists())

    def test_intent_to_add_is_not_in_the_commit(self):
        validator = self.repo / "coding-tools/validate.py"
        validator.write_text(self.VALIDATOR.replace(
            'assert (root', 'assert not (root / "intent.txt").exists()\nassert (root'),
            encoding="utf-8")
        self.git("add", "coding-tools/validate.py")
        (self.repo / "intent.txt").write_text("not staged\n", encoding="utf-8")
        self.git("add", "-N", "intent.txt")
        before = self.git("ls-files", "-v", "--stage")
        result = self.run_hook()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git("ls-files", "-v", "--stage"), before)
        self.assertEqual((self.repo / "intent.txt").read_text(), "not staged\n")

    def test_a_temporary_directory_inside_the_repo_cannot_rediscover_its_git_dir(self):
        validator = self.repo / "coding-tools/validate.py"
        validator.write_text('''import pathlib
import subprocess
root = pathlib.Path(__file__).resolve().parent.parent
result = subprocess.run(["git", "rev-parse", "--git-dir"], cwd=root, capture_output=True)
assert result.returncode != 0, "the snapshot discovered the original repository"
''', encoding="utf-8")
        self.git("add", "coding-tools/validate.py")
        scratch = self.repo / "scratch"
        scratch.mkdir()
        result = self.run_hook({**self.env, "TMPDIR": str(scratch)})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(list(scratch.iterdir()), [])
        # A ':' splits the ceiling list, so the hook refuses rather than run unfenced.
        colon = self.repo / "scratch:with-colon"
        colon.mkdir()
        result = self.run_hook({**self.env, "TMPDIR": str(colon)})
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("contains ':'", result.stderr)
        self.assertEqual(list(colon.iterdir()), [])

    def test_an_alternate_index_is_honoured_and_repository_environment_is_cleared(self):
        validator = self.repo / "coding-tools/validate.py"
        validator.write_text(self.VALIDATOR + '''import os
assert "GIT_DIR" not in os.environ
assert "GIT_INDEX_FILE" not in os.environ
assert "GIT_OBJECT_DIRECTORY" not in os.environ
''', encoding="utf-8")
        self.git("add", "coding-tools/validate.py")
        alternate = self.base / "alternate-index"
        shutil.copy2(self.repo / ".git/index", alternate)
        (self.repo / "tracked.txt").write_text("bad\n", encoding="utf-8")
        self.git("add", "tracked.txt")
        env = {**self.env, "GIT_DIR": str(self.repo / ".git"),
               "GIT_INDEX_FILE": str(alternate),
               "GIT_OBJECT_DIRECTORY": str(self.repo / ".git/objects")}
        result = self.run_hook(env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git("show", ":tracked.txt"), "bad")
        self.assertEqual(self.git("show", ":tracked.txt", env=env), "good")

    def test_removing_the_validator_does_not_disable_the_gate(self):
        self.commit()
        self.git("rm", "coding-tools/validate.py")
        result = self.run_hook()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("removes coding-tools/validate.py", result.stderr)

    def test_an_unrelated_repository_has_nothing_to_check(self):
        self.git("rm", "--cached", "coding-tools/validate.py")
        result = self.run_hook()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(list(self.scratch.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
