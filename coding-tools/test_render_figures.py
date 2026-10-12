#!/usr/bin/env python3
"""Regression checks for safe rendering and honest git figure results."""
from __future__ import annotations

import contextlib
import io
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.dont_write_bytecode = True
import figures_check
import render


class SafeRender(unittest.TestCase):
    SECTIONS = "".join(f"## {s}\n\nHand-written {s}.\n\n" for s in
                       ("Owns", "Before starting", "Decide first", "Always / Never",
                        "Verify with", "Done when"))

    def skill(self, root: pathlib.Path, name: str, body: str) -> pathlib.Path:
        path = root / name / "SKILL.md"
        path.parent.mkdir()
        path.write_text(body, encoding="utf-8")
        return path

    def test_missing_required_section_is_an_error_without_edits(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.skill(pathlib.Path(tmp), "coding-test", "## Owns\n\nKeep me.\n")
            before = path.read_bytes()
            with self.assertRaises(render.Malformed):
                render.render(path)
            self.assertEqual(path.read_bytes(), before)

    def test_marker_cannot_consume_a_hand_written_section(self):
        body = self.SECTIONS.replace("Hand-written Before starting.",
                                     "<!-- deliver:sizing -->\nold block")
        body = body.replace("Hand-written Decide first.",
                            "Hand-written Decide first.\n<!-- /deliver:sizing -->")
        with tempfile.TemporaryDirectory() as tmp:
            path = self.skill(pathlib.Path(tmp), "coding-test", body)
            before = path.read_bytes()
            with self.assertRaises(render.Malformed):
                render.render(path)
            self.assertEqual(path.read_bytes(), before)

    def test_nested_delivery_blocks_are_rejected_without_edits(self):
        body = self.SECTIONS.replace("Hand-written Before starting.",
                                    "<!-- deliver:sizing -->\n"
                                    "<!-- deliver:predict -->\nold\n"
                                    "<!-- /deliver:predict -->\n"
                                    "<!-- /deliver:sizing -->")
        with tempfile.TemporaryDirectory() as tmp:
            path = self.skill(pathlib.Path(tmp), "coding-test", body)
            before = path.read_bytes()
            with self.assertRaises(render.Malformed):
                render.render(path)
            self.assertEqual(path.read_bytes(), before)

    def test_duplicate_destination_sections_are_ambiguous(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = self.SECTIONS + "## Before starting\n\nAnother destination.\n"
            path = self.skill(pathlib.Path(tmp), "coding-test", body)
            before = path.read_bytes()
            with self.assertRaises(render.Malformed):
                render.render(path)
            self.assertEqual(path.read_bytes(), before)

    def test_main_preflights_all_skills_before_writing_any(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            first = self.skill(root, "coding-debug", self.SECTIONS)
            last = self.skill(root, "coding-test", self.SECTIONS + "<!-- deliver:surface -->\n")
            before = {p: p.read_bytes() for p in (first, last)}
            with mock.patch.object(render, "SKILLS_ROOT", root), \
                    contextlib.redirect_stderr(io.StringIO()), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(render.main([]), 1)
            for path, contents in before.items():
                self.assertEqual(path.read_bytes(), contents)

    def test_unreadable_file_is_a_render_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(render.Malformed):
                render.render(pathlib.Path(tmp) / "missing.md")

    def test_check_reports_stale_blocks_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            path = self.skill(root, "coding-test", self.SECTIONS)
            before = path.read_bytes()
            with mock.patch.object(render, "SKILLS_ROOT", root), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(render.main(["--check"]), 1)
                self.assertEqual(path.read_bytes(), before)
                self.assertEqual(render.main([]), 0)
                self.assertEqual(render.main(["--check"]), 0)


class FigureFailures(unittest.TestCase):
    def test_missing_git_cannot_report_success(self):
        with mock.patch.object(figures_check.shutil, "which", return_value=None), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertNotEqual(figures_check.main(), 0)
        self.assertIn("git", output.getvalue())

    def test_stash_recipe_cannot_omit_index_restoration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            for name in ("stash-staged", "stash-unstaged", "stash-test-staged"):
                (root / name).mkdir()
            page = root / "oracles.md"
            page.write_text(figures_check.ORACLES.read_text(encoding="utf-8")
                            .replace("git stash pop --index", "git stash pop"),
                            encoding="utf-8")
            failures = []
            with mock.patch.object(figures_check, "ORACLES", page), \
                    mock.patch.object(figures_check, "failures", failures):
                figures_check.check_stash_fix(root)
            self.assertTrue(any("no longer mentions `git stash pop --index`" in f
                                for f in failures), failures)


if __name__ == "__main__":
    unittest.main()
