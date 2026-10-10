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
        engine.conforms(None, {"anyOf": [False, {"type": "null"}]})   # boolean subschemas
        with self.assertRaises(engine.EngineError):
            engine.conforms(1, {"anyOf": [False]})
        for value, schema in (({"x": 1}, {"type": "object", "properties": {"x": False}}),
                              ([1], {"type": "array", "items": False})):
            with self.assertRaises(engine.EngineError, msg=schema):
                engine.conforms(value, schema)
        engine.conforms([], {"type": "array", "items": False})      # nothing to reject

    def test_a_boolean_is_not_a_number_in_const_or_enum(self):
        for value, schema in ((True, {"const": 1}), (True, {"enum": [1]}),
                              ([False], {"const": [0]})):
            with self.assertRaises(engine.EngineError, msg=schema):
                engine.conforms(value, schema)
        engine.conforms(1, {"enum": [1, 2]})

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


class Markdown(unittest.TestCase):
    """Every construct a review found misread, now read by the parser.

    A marker is `#TODO(agent):`; "live" means it renders outside code, which is
    what V22 checks. A link is live the same way, for V8 and V19."""

    M = "#TODO(agent): fix"

    def live(self, text: str) -> bool:
        return any(self.M in s for s in fences.live_text(text).values())

    def test_markers_that_render_as_text_are_live(self):
        cases = {
            "plain": "prose " + self.M,
            "after a span": "a `x` " + self.M,
            "after an escaped backtick": "literal \\` then " + self.M,
            "after a lone backtick": "a lone ` then " + self.M,
            "across a whitespace-only blank line": "a ` lone\n   \nnext " + self.M + " `x`",
            "after a tilde fence": "~~~\necho `date\n~~~\nprose " + self.M + " `x`",
            "after an ATX heading": "## head `\n" + self.M + " `",
            "after a setext heading": "head `\n---\n" + self.M + " `",
            "after a thematic break": "a `\n\n***\n" + self.M + " `",
            "in a list item after a span opener": "a ` lone\n- item " + self.M + " `x`",
            "in a nested quote": "> `example\n> > " + self.M + "`",
            "inside an HTML block": "<div>\n" + self.M + "\n</div>",
            "between bare angle brackets in an HTML block": "<div>\nx < " + self.M + " > y\n</div>",
        }
        for name, text in cases.items():
            self.assertTrue(self.live(text), msg=name)

    def test_markers_inside_code_are_mentions(self):
        cases = {
            "single span": "`" + self.M + "`",
            "double span": "``" + self.M + "``",
            "span across lines": "a `" + self.M + "\nUNVERIFIED` b",
            "span across quoted lines": "> `example\n> " + self.M + "`",
            "span across a lazy quote continuation": "> `example\n" + self.M + "`",
            "span across an inline HTML tag": "a `start\n<span>" + self.M + "</span>`",
            "escaped first backtick": "\\``" + self.M + "`",
            "backtick fence": "```\n" + self.M + "\n```",
            "tilde fence": "~~~\n" + self.M + "\n~~~",
            "fence holding a fence-like line": "```text\n```example\n" + self.M + "\n```",
            "indented code": "para\n\n    " + self.M,
            "in an HTML comment": "<!--\n" + self.M + "\n-->",
            "in an HTML attribute": "<div title=\"" + self.M + "\">\nx\n</div>",
        }
        for name, text in cases.items():
            self.assertFalse(self.live(text), msg=name)

    def test_line_numbers_survive_breaks_and_spans(self):
        text = "one\ntwo `x\ny` three\n" + self.M
        self.assertIn(self.M, fences.live_text(text)[3])

    def test_line_numbers_survive_decoded_references(self):
        shown = fences.live_text("<div>&#10;" + self.M + "\nUNVERIFIED &amp; &NewLine;x\n</div>")
        self.assertIn(self.M, shown[0])
        self.assertNotIn(self.M, shown.get(1, ""))
        self.assertIn("&", shown[1])

    def test_links_are_read_as_rendered(self):
        self.assertEqual(fences.links("[a](x.md) and [b][r]\n\n[r]: y.md"), ["x.md", "y.md"])
        self.assertEqual(fences.links("`[a](x.md)`\n\n```\n[b](y.md)\n```"), [])
        self.assertEqual(fences.links("[t](x.md \"Title\")"), ["x.md"])
        self.assertEqual(fences.links("head `\n---\n[bad](missing) `"), ["missing"])

    def test_headings(self):
        lines = ["## Done when ##", "   ## Verify with  ", "    ## code", "### Three",
                 "Setext", "------", "```", "## fenced", "```"]
        self.assertEqual(fences.h2_lines(lines), {0: "Done when", 1: "Verify with", 4: "Setext"})
        self.assertEqual(fences.h2_lines(["> ## Verify with", "", "- ## Done when", "",
                                          "## Real"]), {4: "Real"})

    def test_fences(self):
        lines = ["~~~~", "```", "~~~", "~~~~", "## After", "``` a`b", "x"]
        self.assertEqual(fences.fence_mask(lines),
                         [True, True, True, True, False, False, False])
        self.assertEqual(fences.blocks(["a", "```", "x", "```", "```py", "y"]), [["x"], ["y"]])

    def test_sections_after_a_nested_lookalike_are_found(self):
        import validate
        text = "## Owns\n```text\n```example\n```\n## Done when\nyes\n"
        self.assertEqual(validate.sections(text).get("Done when"), "yes")


class Validator(unittest.TestCase):
    """False positives: content these rules must leave alone."""

    def test_a_pipe_in_a_shell_example_is_not_an_enumeration(self):
        import validate
        line = "List the environment with `ENV | sort` first."
        m = validate.ENUM_RE.search(line)
        self.assertTrue(m is None or not validate._is_enumeration(
            [w.strip() for w in m.group(1).split("|")]))


class Round4(unittest.TestCase):
    """Each of these passed silently, or crashed, before the fix it names."""

    def test_frontmatter_ignores_an_indented_rule_and_a_bom(self):
        import validate
        text = '---\ndescription: >-\n  one\n  ---\n  two\n---\nbody\n'
        self.assertEqual(validate.frontmatter(text, "t-indented")["description"], "one --- two")

    def test_schema_keywords_are_checked_or_refused(self):
        for value, schema in (({}, {"allOf": [{"required": ["x"]}]}),
                              ("a", {"not": {"type": "string"}}),
                              ({"x": 1, "y": 2}, {"type": "object", "properties": {"x": {}},
                                                  "additionalProperties": False}),
                              (-1, {"minimum": 0}),
                              ({"a": 1}, {"properties": {"a": {"$ref": "#/x"}}})):
            with self.assertRaises(engine.EngineError, msg=schema):
                engine.conforms(value, schema)
        engine.conforms({"x": 1}, {"title": "t", "properties": {"x": {"description": "d"}}})

    def test_an_unchecked_keyword_is_never_absorbed_by_a_combinator(self):
        for schema in ({"not": {"minimum": 0}},
                       {"anyOf": [{"minimum": 0}, {"type": "integer"}]},
                       {"oneOf": [{"maximum": 0}]}):
            with self.assertRaises(engine.Unchecked, msg=schema):
                engine.conforms(1, schema)

    def test_make_hooks_replaces_a_dangling_hook_link_only_when_forced(self):
        root = pathlib.Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as tmp:
            env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
            env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
            subprocess.run(["git", "init", "-q", tmp], check=True, env=env)
            (pathlib.Path(tmp) / "coding-tools" / "githooks").mkdir(parents=True)
            for f in ("Makefile", "coding-tools/githooks/pre-commit"):
                (pathlib.Path(tmp) / f).write_bytes((root / f).read_bytes())
            hook = pathlib.Path(tmp) / ".git" / "hooks" / "pre-commit"
            hook.parent.mkdir(exist_ok=True)
            hook.symlink_to("/nonexistent/hook")
            plain = subprocess.run(["make", "-s", "hooks"], cwd=tmp, env=env,
                                   capture_output=True, text=True)
            self.assertIn("refusing", plain.stdout)
            forced = subprocess.run(["make", "-s", "hooks", "FORCE=1"], cwd=tmp, env=env,
                                    capture_output=True, text=True)
            self.assertEqual(forced.returncode, 0, forced.stdout + forced.stderr)
            self.assertFalse(hook.is_symlink())

    def test_make_hooks_accepts_a_hooks_directory_inside_the_worktree(self):
        root = pathlib.Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as tmp:
            env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
            env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
            subprocess.run(["git", "init", "-q", tmp], check=True, env=env)
            subprocess.run(["git", "-C", tmp, "config", "core.hooksPath", ".githooks"],
                           check=True, env=env)
            (pathlib.Path(tmp) / "coding-tools" / "githooks").mkdir(parents=True)
            for f in ("Makefile", "coding-tools/githooks/pre-commit"):
                (pathlib.Path(tmp) / f).write_bytes((root / f).read_bytes())
            r = subprocess.run(["make", "-s", "hooks"], cwd=tmp, env=env,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue((pathlib.Path(tmp) / ".githooks" / "pre-commit").exists())

    def test_make_hooks_never_deletes_its_own_source(self):
        root = pathlib.Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as tmp:
            env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
            env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
            subprocess.run(["git", "init", "-q", tmp], check=True, env=env)
            subprocess.run(["git", "-C", tmp, "config", "core.hooksPath",
                            "coding-tools/githooks"], check=True, env=env)
            (pathlib.Path(tmp) / "coding-tools" / "githooks").mkdir(parents=True)
            for f in ("Makefile", "coding-tools/githooks/pre-commit"):
                (pathlib.Path(tmp) / f).write_bytes((root / f).read_bytes())
            r = subprocess.run(["make", "-s", "hooks"], cwd=tmp, env=env,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue((pathlib.Path(tmp) / "coding-tools/githooks/pre-commit").exists())

    def test_make_hooks_recreates_a_missing_hooks_directory(self):
        root = pathlib.Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as tmp:
            env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
            env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
            subprocess.run(["git", "init", "-q", tmp], check=True, env=env)
            (pathlib.Path(tmp) / "coding-tools" / "githooks").mkdir(parents=True)
            for f in ("Makefile", "coding-tools/githooks/pre-commit"):
                (pathlib.Path(tmp) / f).write_bytes((root / f).read_bytes())
            subprocess.run(["rm", "-rf", f"{tmp}/.git/hooks"], check=True)
            r = subprocess.run(["make", "-s", "hooks"], cwd=tmp, env=env,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue((pathlib.Path(tmp) / ".git" / "hooks" / "pre-commit").exists())

    def test_strict_leaves_literals_and_refuses_open_maps(self):
        got = engine.strict({"type": "object",
                             "properties": {"k": {"const": {"type": "object"}}}})
        self.assertEqual(got["properties"]["k"]["const"], {"type": "object"})
        with self.assertRaises(engine.EngineError):
            engine.strict({"type": "object", "additionalProperties": True})

    def test_spawn_failures_are_engine_errors(self):
        with self.assertRaises(engine.EngineError):
            engine._spawn("x", [sys.executable, "-c", "pass", "x" * 200_000])
        r = engine._spawn("x", [sys.executable, "-c",
                                "import sys; sys.stdout.buffer.write(b'\\xff{}')"])
        self.assertIn("{}", r.stdout)
        self.assertEqual(engine._as_argument("--- task"), "\n--- task")

    def test_a_page_that_lost_its_claims_fails(self):
        before = len(figures_check.failures)
        figures_check.states(pathlib.Path("/nonexistent/recovery.md"), "reset --hard")
        self.assertGreater(len(figures_check.failures), before)
        del figures_check.failures[before:]

    def test_render_finds_heading_forms_and_refuses_bad_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp) / "coding-test"
            d.mkdir()
            p = d / "SKILL.md"
            body = "".join(f"## {s} ##\n\nx\n\n" for s in
                           ("Owns", "Before starting", "Decide first", "Always / Never",
                            "Verify with", "Done when"))
            p.write_text(body, encoding="utf-8")
            render.render(p)
            self.assertIn("<!-- deliver:", p.read_text(encoding="utf-8"))
            p.write_bytes(b"## Owns\n\xff\n")
            with self.assertRaises(render.Malformed):
                render.render(p)

    def test_make_refute_requires_the_running_engine(self):
        r = subprocess.run(["make", "-s", "-C", str(pathlib.Path(__file__).resolve().parent.parent),
                            "refute", "CLAIMS=x.json"], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("RUNNING", r.stdout + r.stderr)


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
