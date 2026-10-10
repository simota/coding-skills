#!/usr/bin/env python3
"""Prove the tools around the validator fail where they say they fail.

`test_validate.py` covers the rules. This covers the code that has no rule over
it: the engine runner, the refuter's verdicts, the renderer's markers and the
figures checker's parsing. Nothing here launches an engine or leaves the
machine — what is tested is every path that must stop rather than guess.

Run: make test
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.dont_write_bytecode = True
import engine                                       # noqa: E402
import fences                                       # noqa: E402
import figures_check                                # noqa: E402
import refute                                       # noqa: E402
import render                                       # noqa: E402


class Engine(unittest.TestCase):
    def test_strict_closes_every_object(self):
        got = engine.strict({"type": "object", "properties": {
            "a": {"type": "object", "properties": {"b": {"type": "string"}}},
            "c": {"type": "array", "items": {"type": "object", "properties": {}}}}})
        self.assertIs(got["additionalProperties"], False)
        self.assertIs(got["properties"]["a"]["additionalProperties"], False)
        self.assertIs(got["properties"]["c"]["items"]["additionalProperties"], False)

    def test_other_than_never_returns_the_running_engine(self):
        for running in engine.ENGINES["runs_on"]:
            self.assertNotEqual(engine.other_than(running), running)

    def test_other_than_refuses_an_unknown_engine(self):
        with self.assertRaises(engine.EngineError):
            engine.other_than("nosuchengine")

    def test_run_refuses_an_unknown_engine(self):
        with self.assertRaises(engine.EngineError):
            engine.run("nosuchengine", "p", {"type": "object"})

    def test_strict_reaches_nullable_objects_and_schema_lists(self):
        got = engine.strict({"anyOf": [{"type": "object", "properties": {}}],
                             "properties": {"n": {"type": ["object", "null"]}},
                             "type": "object"})
        self.assertIs(got["anyOf"][0]["additionalProperties"], False)
        self.assertIs(got["properties"]["n"]["additionalProperties"], False)

    def test_strict_refuses_to_narrow_a_map(self):
        with self.assertRaises(engine.EngineError):
            engine.strict({"type": "object", "additionalProperties": {"type": "string"}})

    def test_an_answer_that_misses_the_schema_is_not_an_answer(self):
        for bad in ({"verdict": "looks fine"}, {"refuted": "false", "reason": "",
                                               "what_would_settle_it": ""}):
            with self.assertRaises(engine.EngineError, msg=bad):
                engine.conforms(bad, refute.SCHEMA)
        engine.conforms({"refuted": False, "reason": "r", "what_would_settle_it": "w"},
                        refute.SCHEMA)

    def test_conforms_checks_enum_const_and_alternatives(self):
        engine.conforms(10 ** 400, {"type": "integer"})          # no OverflowError
        with self.assertRaises(engine.EngineError):
            engine.conforms("maybe", {"type": "string", "enum": ["yes", "no"]})
        with self.assertRaises(engine.EngineError):
            engine.conforms({"a": {}}, {"anyOf": [
                {"type": "object", "required": ["b"]}, {"type": "null"}]})
        engine.conforms(None, {"anyOf": [{"type": "object"}, {"type": "null"}]})

    def test_parse_takes_the_last_object_line(self):
        self.assertEqual(engine._parse("x", 'log line\n{"ok": true}\n'), {"ok": True})

    def test_parse_refuses_output_with_no_object(self):
        with self.assertRaises(engine.EngineError):
            engine._parse("x", "[1, 2]\nnot json\n")

    def test_main_requires_running(self):
        argv = sys.argv
        try:
            sys.argv = ["engine.py", "codex", "--prompt-file", "p", "--schema", "s"]
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(engine.main(), 2)
            self.assertIn("--running", err.getvalue())
        finally:
            sys.argv = argv


class Refute(unittest.TestCase):
    def test_verdicts(self):
        yes, no = {"refuted": True}, {"refuted": False}
        self.assertEqual(refute.verdict({}), "UNCHECKED")
        self.assertEqual(refute.verdict({"a": yes, "b": yes}), "REFUTED")
        self.assertEqual(refute.verdict({"a": no, "b": no}), "STANDS")
        self.assertEqual(refute.verdict({"a": yes, "b": no}), "CONTESTED")

    def test_a_non_boolean_vote_is_refused(self):
        with self.assertRaises(ValueError):
            refute.verdict({"a": {"refuted": "false"}})

    def test_pool_excludes_the_running_engine(self):
        for running in engine.ENGINES["runs_on"]:
            self.assertNotIn(running, refute.refuters(running))

    def test_claims_without_a_claim_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            for body in ([], [{"id": "a"}], [{"claim": "  "}], "text", 3):
                p = pathlib.Path(tmp) / "c.json"
                p.write_text(json.dumps(body), encoding="utf-8")
                with self.assertRaises(ValueError, msg=body):
                    refute.load_claims(str(p))

    def test_a_single_claim_object_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "c.json"
            p.write_text(json.dumps({"id": "a", "claim": "x"}), encoding="utf-8")
            self.assertEqual(refute.load_claims(str(p)), [{"id": "a", "claim": "x"}])


class Render(unittest.TestCase):
    def skill(self, tmp: str, body: str) -> pathlib.Path:
        d = pathlib.Path(tmp) / "coding-test"         # owes every delivered block
        d.mkdir()
        p = d / "SKILL.md"
        p.write_text(body, encoding="utf-8")
        return p

    SECTIONS = "".join(f"## {s}\n\nown words\n\n" for s in
                       ("Owns", "Before starting", "Decide first", "Always / Never",
                        "Verify with", "Done when"))

    def test_render_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = self.skill(tmp, self.SECTIONS)
            self.assertTrue(render.render(p))
            once = p.read_text(encoding="utf-8")
            self.assertFalse(render.render(p))
            self.assertEqual(p.read_text(encoding="utf-8"), once)
            for key in render.H["delivered"]:
                self.assertEqual(once.count(f"<!-- deliver:{key} -->"), 1)

    def test_a_fenced_heading_is_not_the_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = "```\n## Verify with\n```\n\n" + self.SECTIONS
            p = self.skill(tmp, body)
            render.render(p)
            text = p.read_text(encoding="utf-8")
            fence_end = text.index("```\n", 4)
            self.assertNotIn("<!-- deliver:", text[:fence_end])

    def test_a_marker_quoted_in_prose_is_not_a_delimiter(self):
        key = next(iter(render.H["delivered"]))
        quoted = f"The block between `<!-- deliver:{key} -->` and its close is generated."
        with tempfile.TemporaryDirectory() as tmp:
            p = self.skill(tmp, self.SECTIONS.replace("own words", quoted, 1))
            render.render(p)
            self.assertFalse(render.render(p))
            self.assertIn(quoted, p.read_text(encoding="utf-8"))

    def test_an_unpaired_marker_stops_the_render(self):
        key = next(iter(render.H["delivered"]))
        for broken in (f"<!-- deliver:{key} -->\n",
                       f"<!-- /deliver:{key} -->\n<!-- deliver:{key} -->\n",
                       f"<!-- deliver:{key} -->\n<!-- /deliver:{key} -->\n" * 2):
            with tempfile.TemporaryDirectory() as tmp:
                p = self.skill(tmp, self.SECTIONS.replace("own words", broken, 1))
                with self.assertRaises(render.Malformed):
                    render.render(p)


class Fences(unittest.TestCase):
    def test_a_fence_lookalike_inside_a_fence_does_not_close_it(self):
        """The case that used to toggle three times and swallow the page."""
        lines = ["```text", "```example", "```", "## Done when", "x"]
        self.assertEqual(fences.kinds(lines), ["open", "body", "close", "text", "text"])

    def test_tildes_and_longer_fences(self):
        lines = ["~~~~", "```", "~~~", "~~~~", "## After"]
        self.assertEqual(fences.kinds(lines), ["open", "body", "body", "close", "text"])

    def test_an_info_string_with_a_backtick_is_not_a_fence(self):
        self.assertEqual(fences.kinds(["``` a`b", "## H"]), ["text", "text"])

    def test_blocks_and_an_unclosed_fence(self):
        self.assertEqual(fences.blocks(["a", "```", "x", "```", "```py", "y"]), [["x"], ["y"]])

    def test_sections_after_a_nested_lookalike_are_found(self):
        import validate
        text = "## Owns\n```text\n```example\n```\n## Done when\nyes\n"
        self.assertEqual(validate.sections(text).get("Done when"), "yes")


class Validator(unittest.TestCase):
    """False positives: content these rules must leave alone."""

    def test_a_marker_inside_a_code_span_is_a_mention(self):
        import validate
        line = "A Python marker reads `x = f()  #TODO(agent): ...` in the source."
        self.assertIsNone(validate.MARKER_RE.search(validate.outside_code_spans(line)))
        open_span = "**quarantined with a `#TODO(agent):"
        self.assertIsNone(validate.MARKER_RE.search(validate.outside_code_spans(open_span)))

    def test_a_pipe_in_a_shell_example_is_not_an_enumeration(self):
        import validate
        line = "List the environment with `ENV | sort` first."
        m = validate.ENUM_RE.search(line)
        self.assertTrue(m is None or not validate._is_enumeration(
            [w.strip() for w in m.group(1).split("|")]))


class Figures(unittest.TestCase):
    BLOCK = ["$ git log --oneline -Sb   # note",
             "aaaaaaa c3                # added",
             "bbbbbbb c1",
             "",
             "$ git log --oneline -Gb",
             "aaaaaaa c3",
             "ccccccc c2                # <- found",
             "bbbbbbb c1"]

    def test_each_command_reads_only_its_own_listing(self):
        self.assertEqual(figures_check.printed_subjects(self.BLOCK, "-Sb"), ["c3", "c1"])
        self.assertEqual(figures_check.printed_subjects(self.BLOCK, "-Gb"),
                         ["c3", "c2", "c1"])

    def test_an_inherited_git_dir_is_never_touched(self):
        """Run from a hook, git exports GIT_DIR; the fixtures must not use it."""
        with tempfile.TemporaryDirectory() as tmp:
            env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
            env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
            def git(*a):
                return subprocess.run(("git", *a), cwd=tmp, env=env, check=True,
                                      capture_output=True, text=True).stdout.strip()
            git("init", "-q")
            git("-c", "user.email=s@s", "-c", "user.name=s", "commit", "-q",
                "--allow-empty", "-m", "sentinel")
            head = git("rev-parse", "HEAD")
            leak = {**os.environ, "GIT_DIR": os.path.join(tmp, ".git"),
                    "GIT_INDEX_FILE": os.path.join(tmp, ".git", "index")}
            subprocess.run([sys.executable, str(pathlib.Path(figures_check.__file__))],
                           env=leak, capture_output=True, text=True)
            self.assertEqual(git("rev-parse", "HEAD"), head)
            self.assertEqual(git("status", "--porcelain"), "")

    def test_stat_counts(self):
        sc = figures_check.stat_counts
        self.assertEqual(sc(" 1 file changed, 2 insertions(+), 3 deletions(-)"), (2, 3))
        self.assertEqual(sc("-> 1 insertion(+)"), (1, 0))
        self.assertEqual(sc(" 1 file changed, 1 deletion(-)"), (0, 1))
        self.assertIsNone(sc("nothing here"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
