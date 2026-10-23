#!/usr/bin/env python3
"""Exercise valid Markdown and invalid inputs at the validator's boundaries."""
from __future__ import annotations

import copy
import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.dont_write_bytecode = True
import validate  # noqa: E402


class RegistryLoading(unittest.TestCase):
    def setUp(self):
        import test_validate
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "repo"
        test_validate.copy_repository(test_validate.ROOT, self.root)

    def registry(self, name: str) -> Path:
        return self.root / "coding-registry" / name

    def run_validator(self, *, importing: bool = False) -> subprocess.CompletedProcess[str]:
        arguments = ["-c", "import validate"] if importing else ["validate.py"]
        return subprocess.run([sys.executable, *arguments], cwd=self.root / "coding-tools",
                              capture_output=True, text=True)

    def assert_load_failure(self, name: str, detail: str = "") -> None:
        for importing in (False, True):
            with self.subTest(name=name, importing=importing):
                result = self.run_validator(importing=importing)
                output = result.stdout + result.stderr
                self.assertEqual(result.returncode, 1, output)
                self.assertNotIn("Traceback", output)
                self.assertRegex(result.stderr, rf"^V0: coding-registry/{name}(?::| )")
                self.assertIn(detail, result.stderr)
                self.assertNotIn("green", result.stdout)

    def test_duplicate_keys_in_every_registry_have_controlled_diagnostics(self):
        additions = {
            "harness.yaml": "set: coding\n",
            "capabilities.yaml": "coding-test: {}\n",
            "routes.yaml": "bug-fix: {}\n",
            "fixtures.yaml": "- ask: first\n  ask: second\n  expect: coding-test\n",
        }
        for name, extra in additions.items():
            path = self.registry(name)
            original = path.read_bytes()
            try:
                path.write_bytes(original + b"\n" + extra.encode("utf-8"))
                self.assert_load_failure(name, "duplicate key")
            finally:
                path.write_bytes(original)

    def test_valid_yaml_of_the_wrong_shape_stops_at_the_gate(self):
        # Each crashed a rule with a traceback, or let it pass on a value it
        # read letter by letter or not at all.
        mutations = {
            "capabilities.yaml": [("coding-explore:\n", "coding-explore: null\nunused:\n"),
                                  ("class: read-only", "class: [read-only]"),
                                  ("signals: [where,", "signals: [123, where,")],
            "routes.yaml": [("chain: [coding-debug, coding-ship]", "chain: []"),
                            ("chain: [coding-debug, coding-ship]", "chain: coding-debug")],
            "harness.yaml": [("forms: [ascii, mermaid]", "forms: ascii"),
                             ("checkers: [other-engine]", "checkers: other-engine"),
                             ('verified_markers:\n', 'verified_markers: "no automated check"\nunused:\n'),
                             ("skills_dir: skills", "skills_dir: 3"),
                             ("refute.py: all", "refute.py: coding-review"),
                             ("  vocabulary: prediction_outcomes", "  vocabulary: nosuch"),
                             # YAML reads 2.40 as 2.4: a pin is text or nothing.
                             ("  git: null", "  git: 2.40")],
        }
        for name, edits in mutations.items():
            path = self.registry(name)
            original = path.read_text(encoding="utf-8")
            for old, new in edits:
                self.assertIn(old, original)
                try:
                    path.write_text(original.replace(old, new, 1), encoding="utf-8")
                    self.assert_load_failure(name, "must ")
                finally:
                    path.write_text(original, encoding="utf-8")
        for name in ("harness.yaml", "capabilities.yaml", "routes.yaml"):
            path = self.registry(name)
            original = path.read_bytes()
            try:
                path.write_text("[]\n", encoding="utf-8")
                self.assert_load_failure(name, "must be a mapping")
            finally:
                path.write_bytes(original)

    def test_a_key_a_rule_reads_by_name_is_required_at_the_gate(self):
        # Each crashed its rule rather than naming the key; the class without
        # `tools` also made V34 report a grant of no Bash. An empty own_word let
        # V35 pass every skill.
        harness = self.registry("harness.yaml")
        original = harness.read_text(encoding="utf-8")
        edits = [("  skill_md_lines: 156\n", "", "limits.skill_md_lines is missing"),
                 ("  route_stages_max: 6 ", "  unused_max: 6 ", "limits.route_stages_max is missing"),
                 ("  residual_classes: [", "  unused_classes: [", "vocabulary.residual_classes is missing"),
                 ('    tools: "Read, Grep, Glob, Bash"\n', "", "permission_classes.read-only.tools is missing"),
                 ("  own_word: redict", '  own_word: ""', "signature.own_word must be a non-empty string"),
                 ("  contract: PREDICTION.md\n", "", "signature.contract is missing")]
        for old, new, detail in edits:
            self.assertIn(old, original)
            try:
                harness.write_text(original.replace(old, new, 1), encoding="utf-8")
                self.assert_load_failure("harness.yaml", detail)
                self.assertNotIn(validate.CRASHED, self.run_validator().stdout)
            finally:
                harness.write_text(original, encoding="utf-8")

    def test_the_gate_leaves_presence_and_emptiness_to_the_rules(self):
        # Forms the rules document as valid, or judge in their own words.
        harness = self.registry("harness.yaml")
        original = harness.read_text(encoding="utf-8")
        edits = [("checkers: [other-engine]", "checkers: []", "V32"),
                 ("verified_markers:\n", "verified_markers: []\nunused:\n", "V31"),
                 ("forms: [ascii, mermaid]", "forms: []", "V36")]
        for old, new, rule in edits:
            self.assertIn(old, original)
            try:
                harness.write_text(original.replace(old, new, 1), encoding="utf-8")
                result = self.run_validator()
                self.assertNotIn("V0:", result.stderr, (old, result.stderr))
                self.assertIn(f"{rule}:", result.stdout + result.stderr, old)
            finally:
                harness.write_text(original, encoding="utf-8")
        listed = original.replace("refute.py: all", "refute.py: [coding-review]", 1)
        try:
            harness.write_text(listed, encoding="utf-8")
            self.assertNotIn("V0:", self.run_validator().stderr)
        finally:
            harness.write_text(original, encoding="utf-8")

    def test_a_crash_is_located_in_the_rule_not_the_library_it_called(self):
        harness = self.registry("harness.yaml")
        original = harness.read_text(encoding="utf-8")
        try:
            harness.write_text(original.replace("rot_patterns:\n", "rot_patterns:\n  - '('\n", 1),
                               encoding="utf-8")
            result = self.run_validator()
            out = result.stdout + result.stderr
            self.assertEqual(result.returncode, 1, out)
            self.assertNotIn("Traceback", out)
            self.assertRegex(out, rf"V25: {validate.CRASHED}: .*\(validate\.py:\d+\)")
        finally:
            harness.write_text(original, encoding="utf-8")

    def test_a_rule_that_crashes_is_reported_and_the_others_still_run(self):
        def broken():
            raise KeyError("playbook_lines")
        ran = []
        rules = [broken, lambda: ran.append(True)]
        with mock.patch.object(validate, "RULES", rules), \
                mock.patch.object(validate, "FAILURES", []) as failures, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(validate.main(), 1)
        self.assertEqual(ran, [True])
        self.assertTrue(any(f.startswith("BROKEN:") and "KeyError" in f for f in failures), failures)

    def test_invalid_registry_syntax_has_a_controlled_diagnostic(self):
        self.registry("routes.yaml").write_text("routes: [\n", encoding="utf-8")
        self.assert_load_failure("routes.yaml", "YAML")

    def test_a_missing_registry_has_a_controlled_diagnostic(self):
        self.registry("capabilities.yaml").unlink()
        self.assert_load_failure("capabilities.yaml")

    def test_a_registry_that_cannot_be_opened_has_a_controlled_diagnostic(self):
        path = self.registry("fixtures.yaml")
        path.unlink()
        path.mkdir()
        self.assert_load_failure("fixtures.yaml")

    def test_non_utf8_registry_bytes_have_a_controlled_diagnostic(self):
        self.registry("harness.yaml").write_bytes(b"set: coding\nbroken: \xff\n")
        self.assert_load_failure("harness.yaml", "UTF-8")

    def test_yaml_reader_errors_have_a_controlled_diagnostic(self):
        self.registry("fixtures.yaml").write_bytes(b"- ask: \x00\n  expect: coding-test\n")
        self.assert_load_failure("fixtures.yaml", "YAML")

    def test_valid_yaml_merges_and_imported_registry_values_are_preserved(self):
        harness = self.registry("harness.yaml")
        with harness.open("a", encoding="utf-8") as stream:
            stream.write("""
fixture_defaults: &fixture_defaults
  inherited: kept
  override: old
fixture_second: &fixture_second
  second: kept
fixture_merged:
  <<: [*fixture_defaults, *fixture_second]
  override: new
""")
        script = """import validate
assert validate.H['fixture_merged'] == {'inherited': 'kept', 'override': 'new', 'second': 'kept'}
assert validate.CAP['coding-test']['class'] == 'full'
assert validate.ROUTES['review-to-zero']['max_cycles'] == 4
assert isinstance(validate.FIX, list) and validate.FIX
"""
        imported = subprocess.run([sys.executable, "-c", script], cwd=self.root / "coding-tools",
                                  capture_output=True, text=True)
        self.assertEqual(imported.returncode, 0, imported.stdout + imported.stderr)
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("green", result.stdout)


class ValidatorBoundaries(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "repo"
        self.skill = self.root / "skills/coding-test"
        self.skill.mkdir(parents=True)
        self.shared = self.root / "skills/_coding"
        self.shared.mkdir()
        self.harness = copy.deepcopy(validate.H)
        patches = {
            "ROOT": self.root,
            "SKILLS_ROOT": self.root / "skills",
            "SKILL_DIRS": [self.skill],
            "SKILLS": [self.skill.name],
            "H": self.harness,
            "VOCAB": self.harness["vocabulary"],
            "FAILURES": [],
            "_FRONTMATTER": {},
        }
        for name, value in patches.items():
            patch = mock.patch.object(validate, name, value)
            patch.start()
            self.addCleanup(patch.stop)

    def write(self, relative: str, text: str = "") -> Path:
        path = self.skill / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def decide(self, text: str, tail: str = "") -> None:
        self.write("SKILL.md", f"## Decide first\n\n{text}\n\n## Done when\n\n{tail}\n")

    def assert_fails(self, rule, rule_id: str) -> None:
        rule()
        self.assertTrue(any(f.startswith(rule_id + ":") for f in validate.FAILURES),
                        validate.FAILURES)

    def assert_passes(self, rule) -> None:
        rule()
        self.assertEqual(validate.FAILURES, [])

    def test_playbook_reference_definition_can_live_after_the_section(self):
        self.write("playbooks/flaky.md")
        self.decide("[flaky][guide]", '[guide]: playbooks/flaky.md#diagnosis "Guide"')
        self.assert_passes(validate.v4_playbook_orphans)

    def test_playbook_link_with_fragment_and_title_is_reachable(self):
        self.write("playbooks/flaky.md")
        self.decide('[flaky](playbooks/flaky.md#diagnosis "Guide")')
        self.assert_passes(validate.v4_playbook_orphans)

    def test_a_fenced_example_does_not_make_a_playbook_reachable(self):
        self.write("playbooks/flaky.md")
        self.decide("```md\n[flaky](playbooks/flaky.md)\n```")
        self.assert_fails(validate.v4_playbook_orphans, "V4")

    def test_a_same_named_reference_does_not_make_a_playbook_reachable(self):
        self.write("playbooks/flaky.md")
        self.write("reference/flaky.md")
        self.decide("[flaky](reference/flaky.md)")
        self.assert_fails(validate.v4_playbook_orphans, "V4")

    def test_a_reference_definition_can_live_after_the_section(self):
        self.write("reference/oracles.md")
        self.decide("[oracles][guide]", "[guide]: reference/oracles.md#values")
        self.assert_passes(validate.v30_reference_orphans)

    def test_a_same_named_playbook_does_not_make_a_reference_reachable(self):
        self.write("reference/oracles.md")
        self.write("playbooks/oracles.md")
        self.decide("[oracles](playbooks/oracles.md)")
        self.assert_fails(validate.v30_reference_orphans, "V30")

    def test_a_fenced_example_does_not_make_a_reference_reachable(self):
        self.write("reference/oracles.md")
        self.write("playbooks/cases.md", "```md\nRead `reference/oracles.md`.\n```")
        self.decide("[cases](playbooks/cases.md)")
        self.assert_fails(validate.v30_reference_orphans, "V30")

    def test_playbook_links_and_inline_paths_resolve_from_their_own_bases(self):
        self.write("reference/oracles.md")
        for text in ("Read [oracles](../reference/oracles.md#values).",
                     "Read ``reference/oracles.md``."):
            with self.subTest(text=text):
                self.write("playbooks/cases.md", text)
                self.decide("[cases](playbooks/cases.md)")
                self.assert_passes(validate.v30_reference_orphans)

    def test_percent_encoded_local_links_resolve(self):
        self.write("reference/test oracle.md")
        self.decide("[oracles](reference/test%20oracle.md?view=1#values)")
        self.assert_passes(validate.v8_links)
        self.assert_passes(validate.v19_paths_resolve)

    def test_http_is_a_scheme_not_a_filename_prefix(self):
        self.decide("[missing](http-guide.md)")
        self.assert_fails(validate.v8_links, "V8")

    def test_absolute_percent_encoded_link_cannot_leave_the_repository(self):
        self.decide("[outside](%2Fetc%2Fhostname)")
        self.assert_fails(validate.v8_links, "V8")

    def test_fenced_path_examples_are_not_instructions_to_read_a_file(self):
        self.decide("```md\nRead `reference/missing.md`.\n```")
        self.assert_passes(validate.v19_paths_resolve)

    def test_inline_paths_with_an_http_prefix_are_still_checked(self):
        self.decide("Read `http-guide.md`.")
        self.assert_fails(validate.v19_paths_resolve, "V19")

    def test_external_filenames_are_exact_exemptions(self):
        self.decide("Read `AGENTS.md-missing.md`.")
        self.assert_fails(validate.v19_paths_resolve, "V19")

    def test_a_link_to_a_symlink_loop_reports_a_failure(self):
        self.write("loop.txt").unlink()
        (self.skill / "loop.txt").symlink_to("loop.txt")
        self.decide("[loop](loop.txt)")
        self.assert_fails(validate.v8_links, "V8")

    def test_a_linked_tool_loop_does_not_abort_the_remaining_rules(self):
        source = self.root / "coding-tools/refute.py"
        source.parent.mkdir()
        source.write_text("", encoding="utf-8")
        (self.skill / "refute.py").symlink_to("refute.py")
        self.assert_fails(validate.v27_symlinks_stay_inside, "V27")
        validate.v34_tools_reachable()

    def test_a_missing_shared_directory_is_reported_without_a_traceback(self):
        self.shared.rmdir()
        self.assert_fails(validate.v27_symlinks_stay_inside, "V27")

    def test_an_empty_skill_roster_does_not_abort_path_checks(self):
        with mock.patch.object(validate, "SKILL_DIRS", []):
            validate.v19_paths_resolve()

    def test_markdown_symlinks_do_not_read_outside_the_repository(self):
        outside = self.root.parent / "outside.md"
        outside.write_text("outside content", encoding="utf-8")
        path = self.skill / "outside.md"
        path.symlink_to(outside)
        self.assertEqual(validate.read(path), "")
        self.assertTrue(any(f.startswith("V27:") for f in validate.FAILURES))

    def test_frontmatter_name_must_match_the_directory(self):
        for name_line in ("", "name: coding-other\n"):
            with self.subTest(name_line=name_line):
                validate.FAILURES.clear()
                validate._FRONTMATTER.clear()
                self.write("SKILL.md", f"---\n{name_line}description: Some work\n"
                           "allowed-tools: Read, Grep, Glob, Bash, Write, Edit\n---\n")
                self.assert_fails(validate.v1_sizes, "V1")

    def test_frontmatter_does_not_coerce_non_string_descriptions(self):
        text = "---\nname: coding-test\ndescription: [one, two]\n---\n"
        validate.frontmatter(text, self.skill.name)
        self.assertTrue(any(f.startswith("V1:") for f in validate.FAILURES))

    def test_duplicate_frontmatter_keys_are_rejected(self):
        text = "---\nname: coding-wrong\nname: coding-test\ndescription: some work\n---\n"
        validate.frontmatter(text, self.skill.name)
        self.assertTrue(any(f.startswith("V1:") for f in validate.FAILURES))

    def test_fixture_mapping_and_empty_list_are_not_silently_skipped(self):
        for fixtures in ({"ask": "where", "expect": "coding-explore"}, []):
            with self.subTest(fixtures=fixtures), mock.patch.object(validate, "FIX", fixtures):
                validate.FAILURES.clear()
                self.assert_fails(validate.v10_fixtures, "V10")

    def test_bad_fixture_entries_are_reported_and_later_entries_checked(self):
        fixtures = [None, {"ask": 1}, {"ask": "somewhere", "expect": "coding-explore"}]
        with mock.patch.object(validate, "FIX", fixtures):
            self.assert_fails(validate.v10_fixtures, "V10")
            self.assertTrue(any("somewhere" in f for f in validate.FAILURES), validate.FAILURES)

    def test_loop_stop_is_a_positive_integer_and_oracle_is_not_empty(self):
        valid = {"pattern": "loop", "chain": ["coding-review", "coding-implement"],
                 "oracle": "no findings", "checker": "other-engine", "max_cycles": 4}
        for change in ({"max_cycles": None}, {"max_cycles": 0}, {"max_cycles": -1},
                       {"max_cycles": True}, {"max_cycles": "four"}, {"oracle": " "}):
            with self.subTest(change=change), mock.patch.object(validate, "ROUTES", {"loop": valid | change}):
                validate.FAILURES.clear()
                self.assert_fails(validate.v14_patterns, "V14")

    def test_report_only_route_cannot_have_an_empty_stop(self):
        with mock.patch.object(validate, "ROUTES", {"report": {"pattern": "report-only", "stops_at": None}}):
            self.assert_fails(validate.v14_patterns, "V14")

    def test_two_engine_entries_must_name_two_distinct_engines(self):
        for engines in (["claude", "claude"], "claude,codex", ["claude", " "], ["claude", 1]):
            with self.subTest(engines=engines):
                validate.FAILURES.clear()
                self.harness["engines"]["runs_on"] = engines
                self.assert_fails(validate.v32_checker_engine, "V32")

    def test_residual_classes_must_be_visible_whole_words_on_the_marker_line(self):
        for text in ("#TODO(agent): fix <!-- UNVERIFIED -->",
                     "#TODO(agent): UNVERIFIEDNESS fix",
                     "#TODO(agent): fix `start\nUNVERIFIED`",
                     "#TODO(agent): fix <script>`UNVERIFIED`</script>",
                     "#TODO(agent): fix <style>`UNVERIFIED`</style>",
                     '#TODO(agent): fix <span title="UNVERIFIED">later</span>'):
            with self.subTest(text=text):
                self.assertEqual(validate.unclassified_markers(text), [0])

    def test_visible_residual_classes_can_be_plain_or_code(self):
        for text in ("#TODO(agent): UNVERIFIED fix", "#TODO(agent): fix ``UNVERIFIED``",
                     "#TODO(agent): fix <code>UNVERIFIED</code>",
                     "<pre>#TODO(agent): fix UNVERIFIED</pre>",
                     "<div>#TODO(agent): UNVER&#73;FIED fix</div>"):
            with self.subTest(text=text):
                self.assertEqual(validate.unclassified_markers(text), [])

    def test_a_definition_is_a_row_or_heading_that_opens_with_the_word(self):
        self.harness["vocabulary"].clear()
        self.harness["vocabulary"]["statuses"] = ["DONE"]
        for text in ("Ends as the | `DONE` | row says.\n", "```\n## `DONE`\n```\n",
                     "| status | `DONE` |\n|---|---|\n",
                     "<!--\n| `DONE` | all met |\n-->\n",
                     "| removed | why |\n|---|---|\n| `DONE` was dropped | merged |\n",
                     "| status | meaning |\n|---|---|\n| `OK` | fine |\n`DONE` is never emitted.\n"):
            with self.subTest(text=text):
                validate.FAILURES.clear()
                (self.shared / "CONTRACT.md").write_text(text, encoding="utf-8")
                self.assert_fails(validate.v20_contract_vocabulary, "V20")
        # Read as rendered: indentation, a quote or a list does not unmake one.
        for text in ("| `DONE` | all met |\n|---|---|\n", "## `DONE`\n\nAll met.\n",
                     "### `DONE`\n\nAll met.\n", "  | `DONE` | all met |\n|---|---|\n",
                     "> | `[DONE]` | all met |\n> |---|---|\n", "- ## `DONE`\n",
                     "| `DONE` <!-- note --> | all met |\n|---|---|\n",
                     "## <!-- note --> `DONE`\n"):
            with self.subTest(text=text):
                validate.FAILURES.clear()
                (self.shared / "CONTRACT.md").write_text(text, encoding="utf-8")
                self.assert_passes(validate.v20_contract_vocabulary)

    def test_a_verified_date_is_not_vouched_for_by_the_next_header(self):
        self.write("reference/r.md", "Verified: 2026-08-21\nSource: git — quoted from its help.\n")
        self.assert_fails(validate.v31_verified_names_a_check, "V31")

    def test_a_pinned_version_is_not_a_prefix_of_another(self):
        self.harness["source_authorities"] = {"git": "2.4"}
        for other in ("2.45", "2.4.1", "2.4.*", "2.4+local"):
            with self.subTest(other=other):
                validate.FAILURES.clear()
                self.write("reference/r.md", f"Source: git {other}\n\nVerified: no automated "
                                             f"check\n\nTested with git {other}.\n")
                self.assert_fails(validate.v37_source_pins_the_rot, "V37")
        validate.FAILURES.clear()
        self.write("reference/r.md", "Source: git 2.4\n\nVerified: no automated check\n\n"
                                     "Tested with git 2.4, and works on git 2.4+.\n")
        self.assert_passes(validate.v37_source_pins_the_rot)

    def test_a_refutation_that_is_not_text_is_reported_not_crashed_on(self):
        self.harness["refutation"] = {"lens": ["the citation"], "refuted_when": "it is wrong"}
        self.assert_fails(validate.v33_refutation_lens, "V33")

    def finding_visuals(self) -> dict:
        self.write("playbooks/visualise.md", "`hops` and `labelled`, drawn in ASCII or Mermaid.\n")
        self.write("reference/diagram-forms.md")
        self.decide("[visualise](playbooks/visualise.md)")
        fv = {"playbook": "visualise.md", "contract": "diagram-forms.md",
              "required_of": [self.skill.name], "forms": ["ascii", "mermaid"],
              "triggers": ["hops"], "floor": ["labelled"]}
        self.harness["finding_visuals"] = fv
        return fv

    def test_a_form_is_named_whatever_its_case(self):
        self.finding_visuals()["forms"] = ["ASCII", "Mermaid"]
        self.assert_passes(validate.v36_finding_visuals)

    def test_finding_visuals_without_its_files_is_reported_not_crashed_on(self):
        for key in ("playbook", "contract"):
            with self.subTest(key=key):
                validate.FAILURES.clear()
                del self.finding_visuals()[key]
                self.assert_fails(validate.v36_finding_visuals, "V36")


    def test_every_capability_key_is_a_skill_whatever_its_prefix(self):
        for key in ("codng-test", "coding-ghost"):
            with self.subTest(key=key), mock.patch.object(
                    validate, "CAP", {"coding-test": {}, key: {"class": "full"}}):
                validate.FAILURES.clear()
                self.assert_fails(validate.v3_roster, "V3")
        with mock.patch.object(validate, "CAP", {"coding-test": {}}):
            validate.FAILURES.clear()
            self.assert_passes(validate.v3_roster)

    def test_a_delivered_block_is_placed_where_its_marker_sits(self):
        self.harness["delivered"] = {"sizing": {"section": "Before starting"}}
        (self.root / "coding-registry/delivered").mkdir(parents=True)
        (self.root / "coding-registry/delivered/sizing.md").write_text("Size it.\n",
                                                                       encoding="utf-8")
        block = "<!-- deliver:sizing -->\nSize it.\n<!-- /deliver:sizing -->"
        misplaced = ("## Before starting\n\nThe block (`<!-- deliver:sizing -->`) is "
                     f"delivered.\n\n## Done when\n\n{block}\n")
        self.write("SKILL.md", misplaced)
        self.assert_fails(validate.v17_delivery, "V17")
        validate.FAILURES.clear()
        self.write("SKILL.md", f"## Before starting\n\n{block}\n\n## Done when\n\nDone.\n")
        self.assert_passes(validate.v17_delivery)

    def test_a_grade_in_verify_with_is_one_a_reader_sees_as_a_word(self):
        for text in ("Read back. <!-- executed -->", "Never unexecuted.",
                     '<span title="executed">Read back.</span>'):
            with self.subTest(text=text):
                validate.FAILURES.clear()
                self.write("SKILL.md", f"## Verify with\n\n{text}\n")
                self.assert_fails(validate.v21_verify_names_a_grade, "V21")
        for text in ("Run it (evidence: `executed`).", "It was executed.",
                     "<code>inspected</code>, with the reason."):
            with self.subTest(text=text):
                validate.FAILURES.clear()
                self.write("SKILL.md", f"## Verify with\n\n{text}\n")
                self.assert_passes(validate.v21_verify_names_a_grade)

    def test_the_signature_word_is_one_a_reader_sees(self):
        signature = {"name": "prediction", "contract": "PREDICTION.md",
                     "vocabulary": "prediction_outcomes", "required_of": [self.skill.name],
                     "own_word": "redict"}
        words = " ".join(f"`{w}`" for w in self.harness["vocabulary"]["prediction_outcomes"])
        (self.shared / "PREDICTION.md").write_text(words + "\n", encoding="utf-8")
        with mock.patch.object(validate, "SIGNATURE", signature):
            self.write("SKILL.md", "Write the observable first <!-- predict -->.\n")
            self.assert_fails(validate.v35_signature, "V35")
            validate.FAILURES.clear()
            self.write("SKILL.md", "**Predict the observable** first.\n")
            self.assert_passes(validate.v35_signature)

    def test_a_source_says_none_as_a_word(self):
        self.harness["source_authorities"] = {}
        self.write("reference/r.md", "Source: the docs, which nonetheless move.\n\n"
                                     "Verified: no automated check\n")
        self.assert_fails(validate.v37_source_pins_the_rot, "V37")
        validate.FAILURES.clear()
        self.write("reference/r.md", "Source: none — the shapes are this set's own.\n\n"
                                     "Verified: no automated check\n")
        self.assert_passes(validate.v37_source_pins_the_rot)

    def test_an_enumeration_is_read_wherever_a_line_lists_it(self):
        self.harness["vocabulary"] = {"statuses": ["DONE", "PARTIAL"]}
        for line in ("status: DONE  # DONE | PARTIAL | FAILED, see the contract",
                     "status: DONE  # DONE | PARTIAL | FAILED.",
                     "  DONE | PARTIAL | FAILED", "- DONE | PARTIAL | FAILED",
                     "> DONE | PARTIAL | FAILED"):
            with self.subTest(line=line):
                validate.FAILURES.clear()
                (self.shared / "HANDOFF.md").write_text(line + "\n", encoding="utf-8")
                self.assert_fails(validate.v38_enumerations_declared, "V38")
        for line in ("status: DONE  # DONE | PARTIAL, see the contract",
                     "Pick DONE | PARTIAL or neither and stop"):
            with self.subTest(line=line):
                validate.FAILURES.clear()
                (self.shared / "HANDOFF.md").write_text(line + "\n", encoding="utf-8")
                self.assert_passes(validate.v38_enumerations_declared)


class MutationHarness(unittest.TestCase):
    def run_fixture(self, script: str, *, nested_tmp: bool = False) -> int:
        import test_validate
        temporary_directory = tempfile.TemporaryDirectory
        with temporary_directory() as tmp:
            root = Path(tmp) / "source"
            (root / "coding-tools").mkdir(parents=True)
            (root / "coding-tools/validate.py").write_text("pass\n", encoding="utf-8")

            def mutate(repository):
                (repository / "coding-tools/validate.py").write_text(script, encoding="utf-8")

            location = mock.patch.object(test_validate.tempfile, "TemporaryDirectory",
                                         lambda: temporary_directory(dir=root)) if nested_tmp \
                else contextlib.nullcontext()
            with mock.patch.object(test_validate, "ROOT", root), \
                    mock.patch.object(test_validate, "CASES", {"V1": mutate}), \
                    mock.patch.object(test_validate.validate, "RULES", [validate.v1_sizes]), \
                    location, contextlib.redirect_stdout(io.StringIO()):
                return test_validate.main()

    def test_copy_does_not_recurse_into_its_own_temporary_directory(self):
        self.assertEqual(self.run_fixture("print('  V1: injected violation')\nraise SystemExit(1)\n",
                                         nested_tmp=True), 0)

    def test_a_rule_message_followed_by_a_crash_is_not_a_passing_test(self):
        self.assertEqual(self.run_fixture("print('  V1: injected violation')\nraise RuntimeError('crash')\n"), 1)

    def test_a_rule_message_with_a_success_exit_is_not_a_passing_test(self):
        self.assertEqual(self.run_fixture("print('  V1: injected violation')\n"), 1)


if __name__ == "__main__":
    unittest.main()
