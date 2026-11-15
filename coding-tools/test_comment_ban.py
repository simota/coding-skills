#!/usr/bin/env python3
"""The comment ban, held to what it promises to keep.

Each case here came from a review finding that was reproduced before it was
fixed: a ban that deletes what the contract keeps, and a gate that fails on it.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"


def read(*parts: str) -> str:
    return SKILLS.joinpath(*parts).read_text(encoding="utf-8")


def line_starting(page: str, opening: str) -> str:
    return next(line for line in page.splitlines() if line.startswith(opening))


def bullet(page: str, opening: str) -> str:
    return re.search(rf"^{re.escape(opening)}.*?(?=^- |^\n|\Z)", page, re.S | re.M).group(0)


KEPT = {
    "a cited outside constraint": r"outside\s+constraint",
    "a directive a tool reads": r"directive\s+a\s+tool\s+reads",
    "a #TODO(agent): marker": r"`#TODO\(agent\):`\s+marker",
    "a licence or provenance header": r"licence\s+or\s+provenance\s+header",
    "a test's oracle identifier": r"oracle\s+identifier",
}

LAY_ROW = line_starting(read("coding-setup", "playbooks", "lay.md"), "| Code carries no comment")
HOST_RULE, HOST_GATE = (cell.strip() for cell in LAY_ROW.strip("|").split(" | "))

SAMPLES = {
    "marker.py": "x = 1  #TODO(agent): OUT-OF-SCOPE the workaround under this\n"
                 "#TODO(agent): DEFERRED finish the last case\n",
    "kept.py": "#!/usr/bin/env python3\n# type: ignore\nimport os  # noqa: F401\n"
               "# upstream issue #123: the API returns seconds\nz = 3\n",
    "plain.py": "# Explain the calculation\nx = 1\n",
    "commented_out.py": "# x = compute(1)\ny = 2\n",
    "fixme.py": "# FIXME: workaround until upstream ships\ny = 2\n",
    "hack.py": "# HACK: just in case\ny = 2\n",
    "bare_todo.py": "# TODO: later\ny = 2\n",
}


def gate_exit(sample: str) -> int:
    codes = re.findall(r"`([A-Z]+\d*)`", re.search(r"ruff ((?:`[A-Z]+\d*`(?:, )?)+)", HOST_GATE).group(1))
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / sample
        path.write_text(SAMPLES[sample], encoding="utf-8")
        return subprocess.run([sys.executable, "-m", "ruff", "check", "--no-cache", "--isolated",
                               "--select", ",".join(codes), str(path)],
                              capture_output=True).returncode


class KeptKinds(unittest.TestCase):
    def assert_names_every_kept_kind(self, text: str, where: str) -> None:
        for kind, pattern in KEPT.items():
            with self.subTest(where=where, kind=kind):
                self.assertRegex(text, pattern)

    def test_contract_never_trims_every_kept_kind(self):
        never_trimmed = re.search(r"Never trimmed:.*?\.", read("_coding", "CONTRACT.md"), re.S).group(0)
        self.assert_names_every_kept_kind(never_trimmed, "CONTRACT.md")

    def test_refactor_leaves_a_cited_outside_constraint(self):
        rule = bullet(read("coding-refactor", "SKILL.md"), "- Always: leave no comment")
        self.assertRegex(rule, KEPT["a cited outside constraint"])
        self.assertIn("`_coding/CONTRACT.md`", rule)

    def test_host_rules_cannot_cite_the_contract_so_they_name_every_kept_kind(self):
        templates = read("coding-setup", "reference", "templates.md")
        self.assert_names_every_kept_kind(line_starting(templates, "- No comment in code"), "templates.md")
        self.assert_names_every_kept_kind(HOST_RULE, "lay.md")


class Gate(unittest.TestCase):
    def test_gate_passes_what_the_rule_keeps(self):
        for sample in ("marker.py", "kept.py"):
            with self.subTest(sample=sample):
                self.assertEqual(gate_exit(sample), 0)

    def test_gate_fails_on_a_planted_excuse(self):
        for sample in ("commented_out.py", "fixme.py", "hack.py", "bare_todo.py"):
            with self.subTest(sample=sample):
                self.assertNotEqual(gate_exit(sample), 0)

    def test_what_the_gate_cannot_see_is_named_discipline(self):
        self.assertEqual(gate_exit("plain.py"), 0)
        self.assertIn("discipline", HOST_GATE)

    def test_gate_red_on_the_untouched_tree_is_not_wired(self):
        self.assertRegex(HOST_GATE, r"[Rr]ed on the untouched tree, they are not wired")
        self.assertIn("`coding-refactor`", HOST_GATE)


if __name__ == "__main__":
    unittest.main()
