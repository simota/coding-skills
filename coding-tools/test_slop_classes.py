#!/usr/bin/env python3
"""Hold the slop classes to the direction their checks must point.

coding-implement runs each class's **Check:** before a handoff and coding-setup
gates a class through its `tools`, so a check that points the wrong way passes
the defect it names. Nothing here runs a prover: what is tested is the wording
an agent and a gate act on, and each reading is shown rejecting the wording
that points the other way.

Run: make test
"""
from __future__ import annotations

import pathlib
import re
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLASSES = yaml.safe_load((ROOT / "coding-registry" / "slop.yaml").read_text(encoding="utf-8"))["classes"]


def _class(title: str) -> dict:
    return next(c for c in CLASSES if c["title"] == title)


def exempts_lean_builtins(tool: str) -> bool:
    return re.search(r"other than propext, Classical\.choice and Quot\.sound", tool) is not None


def judges_sorry_against_the_base(tool: str) -> bool:
    return "sorryAx included" in tool and re.search(r"sorryAx,? or\b", tool) is None


def gives_a_new_theorem_a_baseline(tool: str) -> bool:
    return "the base commit's own declarations" in tool


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
        self.assertTrue(exempts_lean_builtins(self.axioms_tool))
        self.assertFalse(exempts_lean_builtins(
            "Lean #print axioms: sorryAx, or propext, Classical.choice and Quot.sound"))

    def test_a_sorry_already_at_the_base_does_not_fire_the_gate(self):
        """The check fires on an escape hatch the diff adds, not one it touches."""
        self.assertTrue(judges_sorry_against_the_base(self.axioms_tool))
        self.assertFalse(judges_sorry_against_the_base(
            "Lean #print axioms: sorryAx, or an axiom absent at the base commit"))

    def test_a_new_theorem_is_judged_against_the_axioms_the_base_declared(self):
        """A theorem the diff adds or renames has no output at the base; using an
        axiom the repo already declared adds no escape hatch."""
        self.assertTrue(gives_a_new_theorem_a_baseline(self.axioms_tool))
        self.assertFalse(gives_a_new_theorem_a_baseline(
            "Lean #print axioms: an axiom absent from its output at the base commit"))

    def test_the_tool_and_the_check_judge_a_new_axiom_alike(self):
        """The check fires on an escape hatch the diff adds, so the tool must too:
        an axiom the diff declares is one the repo declared, and passes a tool that
        exempts the repo's own."""
        self.assertRegex(self.check, r"escape hatch[^.;]*(adds|in the diff)")
        self.assertNotIn("the repo never declared", self.axioms_tool)
        self.assertRegex(self.axioms_tool, r"base commit")


if __name__ == "__main__":
    unittest.main()
