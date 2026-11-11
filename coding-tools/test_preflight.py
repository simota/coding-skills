#!/usr/bin/env python3
"""The preflight skill's worked example obeys the rules its playbooks state.

`sheet.html` is read on every run as the form to follow, so a rank, a count or
a claim that is wrong there is copied into every sheet written from it.
"""
from __future__ import annotations

import pathlib
import re
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.dont_write_bytecode = True
import refute                                       # noqa: E402

SKILL = pathlib.Path(__file__).resolve().parent.parent / "skills" / "coding-preflight"
SHEET = (SKILL / "sheet.html").read_text(encoding="utf-8")
HUNT = (SKILL / "playbooks" / "hunt.md").read_text(encoding="utf-8")


def cards() -> list[dict]:
    found = []
    for cid, body in re.findall(r'<article class="card[^"]*" id="(f\d+)">(.*?)</article>', SHEET, flags=re.S):
        found.append({"id": cid, "body": body,
                      "rank": int(re.search(r"RANK (\d)", body).group(1)),
                      "rules": re.findall(r'<span class="chip">(R\d+)</span>', body),
                      "seen": set(re.findall(r"V\d\d", re.sub(r"V\d\d–V\d\d", "", body.split("<dd>")[-1])))})
    return found


def views() -> dict[str, str]:
    return {v.upper(): body for v, body in
            re.findall(r'<section class="fig[^"]*" id="(v\d\d)">(.*?)</section>', SHEET, flags=re.S)}


class Sheet(unittest.TestCase):
    def test_a_rank_below_three_breaks_no_rule_and_a_rank_above_names_one(self):
        """hunt.md: ranks 4-6 break no rule yet, and a Question takes the rank
        of its bad answer. A card that names a rule and sits at rank 4 is a
        blocking flaw filed where nothing stops the build."""
        for c in cards():
            with self.subTest(card=c["id"]):
                self.assertEqual(bool(c["rules"]), c["rank"] <= 3,
                                 f'{c["id"]} is rank {c["rank"]} and names {c["rules"] or "no rule"}')

    def test_what_stops_the_build_is_every_card_of_rank_one_to_three(self):
        blocking = [c["id"] for c in cards() if c["rank"] <= 3]
        stops = re.search(r'<section class="stops">(.*?)</section>', SHEET, flags=re.S).group(1)
        self.assertEqual(re.findall(r'<li><a class="fl" href="#(f\d+)">', stops), blocking)
        shown = re.search(r'Blocking the build</span><span class="big">(\d+)', SHEET).group(1)
        self.assertEqual(int(shown), len(blocking))

    def test_the_register_is_ordered_most_severe_first(self):
        ranks = [c["rank"] for c in cards()]
        self.assertEqual(ranks, sorted(ranks))

    def test_the_bars_count_the_cards(self):
        by_rank: dict[str, int] = {}
        for c in cards():
            by_rank[str(c["rank"])] = by_rank.get(str(c["rank"]), 0) + 1
        bars = {r: int(n) for r, n in
                re.findall(r"<span>rank (\d)</span><i[^>]*></i><span>(\d+)</span>", SHEET)}
        self.assertEqual({r: n for r, n in bars.items() if n}, by_rank)

    def test_the_gap_count_is_the_marks_on_the_views(self):
        marks = len(re.findall(r'class="[^"]*\bq\b[^"]*"', SHEET.split("</style>")[1]))
        shown = re.search(r'Gaps marked \?</span><span class="big">(\d+)', SHEET).group(1)
        self.assertEqual(int(shown), marks)

    def test_a_card_is_seen_in_exactly_the_views_that_flag_it(self):
        for c in cards():
            with self.subTest(card=c["id"]):
                flagged = {v for v, body in views().items() if f'href="#{c["id"]}"' in body}
                self.assertEqual(c["seen"], flagged)

    def test_an_index_dot_is_the_worst_mark_on_its_view(self):
        rank = {c["id"]: c["rank"] for c in cards()}
        for v, body in views().items():
            with self.subTest(view=v):
                flags = [rank[f] for f in re.findall(r'href="#(f\d+)"', body)]
                broken = re.search(r'class="(?:b|[^"]* bad)"', body) is not None
                want = ("bad" if broken or any(r <= 3 for r in flags)
                        else "gap" if flags or re.search(r'class="[^"]*\bq\b', body) else "")
                chip = re.search(rf'<a(?: class="(\w+)")? href="#{v.lower()}">', SHEET)
                self.assertEqual(chip.group(1) or "", want)

    def test_a_thing_called_unread_has_no_reader_in_another_view(self):
        """F8 removes the refund reasons because nothing reads them. A view that
        fills a list from them is a reader, and the removal would break it."""
        unread = next(c for c in cards() if c["id"] == "f8")
        spec = views()["V15"]
        sources = [re.findall(r"<td[^>]*>(.*?)</td>", row, flags=re.S)[2]
                   for row in re.findall(r"<tr><td>.*?</tr>", spec, flags=re.S)]
        self.assertFalse([s for s in sources if "refund reasons" in s.lower()],
                         "the screen spec reads what F8 says nothing reads")
        # Dropping the table alone leaves the column that points at it.
        self.assertIn("column", unread["body"].split("Change</dt>")[1])


class Seams(unittest.TestCase):
    def test_a_seam_whose_view_is_not_owed_is_not_a_finding(self):
        """A job with states and no screen owes no screen view. The seam that
        looks each state up on a screen would then report a flaw that is the
        view's absence, which views.md allows."""
        seams = HUNT.split("## The seams")[1].split("\n## ")[0]
        self.assertIn("not owed", seams)


class Lens(unittest.TestCase):
    def test_the_refuter_is_told_a_claim_may_be_about_a_plan(self):
        """A preflight flaw cites a plan and code not yet built. A lens that
        knows only code refutes it for citing a line that does not exist."""
        with mock.patch.object(refute.engine, "run", return_value={}) as run:
            refute.ask("codex", {"id": "F1", "claim": "two presses pay twice",
                                 "where": "docs/plans/order-refunds.md:14"})
        prompt = run.call_args.args[1]
        self.assertRegex(prompt, r"\bplan\b")
        self.assertRegex(prompt.split("Treat the claim as refuted when:")[1].split("\n\n")[0], r"\bplan\b")


if __name__ == "__main__":
    unittest.main()
