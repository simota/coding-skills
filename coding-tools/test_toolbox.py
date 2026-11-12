#!/usr/bin/env python3
"""The toolbox tool refuses what would mislead the next agent, and only that.

The index is read in place of the tools, so each test here is a way a row could
come to disagree with the file it describes, or a tool could be kept that only
works where it was written.
"""
from __future__ import annotations

import contextlib
import io
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.dont_write_bytecode = True
import toolbox                                      # noqa: E402

HEADER = {
    "Purpose": "seed two tenants",
    "Use when": "a check crosses a tenant boundary",
    "Run": '.agents/toolbox/tools/seed --db "$DATABASE_URL"',
    "Proves": "prints `seeded 2 tenants` and exits 0",
    "Side effects": "mutates — inserts rows into the database named by --db",
    "Verified": "2026-01-31 by running the Run line against an empty database",
}


def source(prefix: str = "# ", body: str = "echo seeded 2 tenants\n", **override: str | None) -> str:
    fields = {**HEADER, **override}
    lines = [f"{prefix}{k}: {v}" for k, v in fields.items() if v is not None]
    return "#!/bin/sh\n" + "\n".join(lines) + "\n" + body


class Box(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.box = pathlib.Path(tmp.name) / "toolbox"
        (self.box / "tools").mkdir(parents=True)

    def add(self, name: str = "seed", text: str | None = None, mode: int = 0o755) -> pathlib.Path:
        path = self.box / "tools" / name
        path.write_text(source() if text is None else text, encoding="utf-8")
        path.chmod(mode)
        return path

    def run_tool(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = toolbox.main([*argv, str(self.box)])
        return code, out.getvalue(), err.getvalue()

    def indexed(self) -> None:
        self.assertEqual(self.run_tool("index")[0], 0)

    def test_an_indexed_toolbox_checks_clean_and_says_no_tool_was_run(self):
        self.add()
        self.indexed()
        code, out, err = self.run_tool("check")
        self.assertEqual((code, err), (0, ""))
        self.assertIn("no tool was run", out)

    def test_the_index_row_is_the_header(self):
        self.add()
        self.indexed()
        row = (self.box / "INDEX.md").read_text(encoding="utf-8").splitlines()[-1]
        for field in ("Purpose", "Use when", "Run", "Side effects"):
            self.assertIn(HEADER[field], row)
        self.assertTrue(row.startswith("| `tools/seed` |"))

    def test_a_header_edited_after_indexing_makes_the_index_stale(self):
        self.add()
        self.indexed()
        self.add(text=source(**{"Use when": "never"}))
        code, _, err = self.run_tool("check")
        self.assertEqual(code, 1)
        self.assertIn("INDEX.md does not match", err)

    def test_a_tool_added_without_reindexing_makes_the_index_stale(self):
        self.add()
        self.indexed()
        self.add("probe")
        self.assertIn("INDEX.md does not match", self.run_tool("check")[2])

    def test_tools_with_no_index_at_all_is_a_finding(self):
        self.add()
        self.assertIn("INDEX.md does not match", self.run_tool("check")[2])

    def test_index_refuses_and_writes_nothing_while_a_header_is_incomplete(self):
        self.add(text=source(Proves=None))
        code, _, err = self.run_tool("index")
        self.assertEqual(code, 1)
        self.assertIn("tools/seed header is missing Proves", err)
        self.assertFalse((self.box / "INDEX.md").exists())

    def test_every_missing_field_is_named_once_and_the_index_is_not_blamed_for_it(self):
        self.add(text="#!/bin/sh\necho hi\n")
        code, _, err = self.run_tool("check")
        self.assertEqual(code, 1)
        self.assertIn("missing " + ", ".join(toolbox.FIELDS), err)
        self.assertNotIn("INDEX.md", err)

    def test_a_header_is_read_under_any_comment_prefix(self):
        for prefix in ("# ", "// ", "-- ", " * ", ""):
            with self.subTest(prefix=prefix):
                self.add(text=source(prefix=prefix))
                self.indexed()
                self.assertEqual(self.run_tool("check")[0], 0)

    def test_a_header_below_the_top_of_the_file_is_not_a_header(self):
        self.add(text="#!/bin/sh\n" + "\n" * toolbox.HEAD_LINES + source())
        self.assertIn("header is missing", self.run_tool("check")[2])

    def test_a_tool_that_cannot_be_executed_is_a_finding(self):
        self.add(mode=0o644)
        self.indexed()
        self.assertIn("tools/seed is not executable", self.run_tool("check")[2])

    def test_side_effects_starts_with_a_declared_word(self):
        self.add(text=source(**{"Side effects": "harmless"}))
        self.indexed()
        self.assertIn("Side effects starts with 'harmless'", self.run_tool("check")[2])

    def test_verified_starts_with_a_date(self):
        self.add(text=source(Verified="last week by running it"))
        self.indexed()
        self.assertIn("Verified does not start with", self.run_tool("check")[2])

    def test_a_pinned_home_path_or_commit_is_reported_at_its_line(self):
        pinned = {"home": "cd /" + "Users/someone/app\n", "commit": "git show " + "0a" * 20 + "\n"}
        for what, body in pinned.items():
            with self.subTest(what=what):
                self.add(text=source(body=body))
                self.indexed()
                code, _, err = self.run_tool("check")
                self.assertEqual(code, 1)
                self.assertIn(f"tools/seed:{len(HEADER) + 2} holds", err)

    def test_a_home_path_read_from_a_variable_is_not_pinned(self):
        self.add(text=source(body='cd "$ROOT/home/data" && ls "${HOME}/Users/x"\n'))
        self.indexed()
        self.assertEqual(self.run_tool("check")[0], 0)

    def test_a_secret_shape_is_reported(self):
        shapes = {"a private key": "-----BEGIN RSA " + "PRIVATE KEY-----",
                  "an AWS access key id": "AKIA" + "A" * 16,
                  "a GitHub token": "ghp_" + "a" * 36}
        for what, text in shapes.items():
            with self.subTest(what=what):
                self.add(text=source(body=f"KEY='{text}'\n"))
                self.indexed()
                self.assertIn(f"holds {what}", self.run_tool("check")[2])

    def test_past_the_cap_the_toolbox_is_told_to_merge_or_delete(self):
        for name in ("a", "b", "c"):
            self.add(name)
        self.indexed()
        code, _, err = self.run_tool("check", "--max", "2")
        self.assertEqual(code, 1)
        self.assertIn("3 tools (max 2)", err)
        self.assertEqual(self.run_tool("check", "--max", "3")[0], 0)

    def test_a_directory_among_the_tools_is_a_finding(self):
        (self.box / "tools" / "lib").mkdir()
        self.assertIn("tools/lib/ is a directory", self.run_tool("check")[2])

    def test_a_pipe_in_a_header_does_not_break_the_table(self):
        self.add(text=source(Run="tools/seed | tee out.log"))
        self.indexed()
        row = (self.box / "INDEX.md").read_text(encoding="utf-8").splitlines()[-1]
        self.assertEqual(row.replace("\\|", "").count("|"), 6)

    def test_dotfiles_are_not_tools(self):
        self.add()
        self.add(".DS_Store", text="\x00")
        self.indexed()
        self.assertEqual(self.run_tool("check")[0], 0)

    def test_no_toolbox_is_clean_to_check_and_refused_to_index(self):
        (self.box / "tools").rmdir()
        self.assertEqual(self.run_tool("check")[0], 0)
        code, _, err = self.run_tool("index")
        self.assertEqual(code, 2)
        self.assertIn("nothing to index", err)
        self.assertFalse((self.box / "INDEX.md").exists())

    def test_an_index_left_behind_by_deleted_tools_is_stale(self):
        self.add()
        self.indexed()
        (self.box / "tools" / "seed").unlink()
        self.assertIn("INDEX.md does not match", self.run_tool("check")[2])


if __name__ == "__main__":
    unittest.main()
