#!/usr/bin/env python3
"""Hold the slop classes to the direction their checks must point.

coding-implement runs each class's **Check:** before a handoff and coding-setup
gates a class through its `tools`, so a check that points the wrong way passes
the defect it names. Nothing here runs a prover: what is tested is the wording
an agent and a gate act on.

Run: make test
"""
from __future__ import annotations

import pathlib
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLASSES = yaml.safe_load((ROOT / "coding-registry" / "slop.yaml").read_text(encoding="utf-8"))["classes"]


def _class(title: str) -> dict:
    return next(c for c in CLASSES if c["title"] == title)


class ProofThatProvesNothing(unittest.TestCase):
    def setUp(self):
        c = _class("A proof that proves nothing")
        self.body = " ".join(c["body"].split())
        self.check = self.body.split("**Check:**", 1)[1]
        self.axioms_tool = next(t for t in c["tools"] if "#print axioms" in t)

    def test_a_narrowed_precondition_is_the_defect_and_a_relaxed_one_is_not(self):
        """Relaxing `requires` strengthens the spec; narrowing it is the escape."""
        self.assertNotRegex(self.body, r"weaken\w*\s+`requires`")
        self.assertRegex(self.check, r"`requires`[^.;]*narrow")
        self.assertRegex(self.check, r"`ensures`[^.;]*weaken")

    def test_the_precondition_must_admit_every_required_input_not_just_one(self):
        """One admitted input survives `requires x == 0`; the requirement's inputs do not."""
        self.assertNotIn("one input the precondition admits", self.check)
        self.assertIn("every input the requirement covers", self.check)

    def test_the_axioms_lean_itself_supplies_do_not_fire_the_gate(self):
        """`simp`, classical reasoning and quotients print these for a sound proof."""
        for builtin in ("propext", "Classical.choice", "Quot.sound"):
            self.assertIn(builtin, self.axioms_tool)

    def test_the_tool_and_the_check_judge_a_new_axiom_alike(self):
        """The check fires on an escape hatch the diff adds, so the tool must too:
        an axiom the diff declares is one the repo declared, and passes a tool that
        exempts the repo's own."""
        self.assertRegex(self.check, r"escape hatch[^.;]*(adds|in the diff)")
        self.assertNotIn("the repo never declared", self.axioms_tool)
        self.assertRegex(self.axioms_tool, r"base commit")


if __name__ == "__main__":
    unittest.main()
