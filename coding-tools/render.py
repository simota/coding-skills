#!/usr/bin/env python3
"""Write the delivered blocks back into every SKILL.md.

A contract kept only in the shared directory is not read on most launches, so the operative
part is carried verbatim in each skill. That only stays true if changing one
line does not cost eight hand edits — this is that cost, paid once.

Idempotent: run it, commit the diff.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
H = yaml.safe_load((ROOT / "coding-registry" / "harness.yaml").read_text(encoding="utf-8"))
PREFIX = H["prefix"]
SKILLS_ROOT = ROOT / H["skills_dir"] if H.get("skills_dir") else ROOT


def delivered_to(spec: dict, skill: str) -> bool:
    """A block with `only: signature` goes to the skills that owe the mechanism."""
    if spec.get("only") == "signature":
        return skill in H["signature"]["required_of"]
    return True


class Malformed(ValueError):
    """A marker pair that cannot be rewritten without guessing where it ends."""


def in_fence(lines: list[str], i: int) -> bool:
    """Whether line i sits inside a ``` fence, where a heading is only text."""
    return sum(1 for l in lines[:i] if l.startswith("```")) % 2 == 1


def heading_line(lines: list[str], section: str) -> int | None:
    """The index of `## <section>` as a whole line outside any fence."""
    for i, line in enumerate(lines):
        if line == f"## {section}" and not in_fence(lines, i):
            return i
    return None


def render(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    original = text
    for key, spec in H["delivered"].items():
        open_m, close_m = f"<!-- deliver:{key} -->", f"<!-- /deliver:{key} -->"
        # One marker without the other, a duplicate, or the pair reversed: any
        # rewrite would either insert a second block or swallow the text between.
        n_open, n_close = text.count(open_m), text.count(close_m)
        if (n_open, n_close) not in ((0, 0), (1, 1)) or (
                n_open and text.index(open_m) > text.index(close_m)):
            raise Malformed(f"{path.parent.name}/{path.name}: the {key} markers are "
                            f"unpaired ({n_open} open, {n_close} close); fix by hand")
        if not delivered_to(spec, path.parent.name):
            if open_m in text and close_m in text:
                head, rest = text.split(open_m, 1)
                _, tail = rest.split(close_m, 1)
                text = head.rstrip("\n") + tail
            continue
        block = (ROOT / "coding-registry" / "delivered" / f"{key}.md").read_text(
            encoding="utf-8").rstrip("\n")
        payload = f"{open_m}\n{block}\n{close_m}"
        if open_m in text and close_m in text:
            head, rest = text.split(open_m, 1)
            _, tail = rest.split(close_m, 1)
            text = head + payload + tail
        else:
            lines = text.split("\n")
            start = heading_line(lines, spec["section"])
            if start is None:
                print(f"  {path.name}: no section {spec['section']!r}", file=sys.stderr)
                continue
            # append at the end of that section, before the next heading
            end = next((i for i in range(start + 1, len(lines))
                        if lines[i].startswith("## ") and not in_fence(lines, i)), len(lines))
            while end > start + 1 and not lines[end - 1].strip():
                end -= 1
            lines[end:end] = payload.split("\n")
            text = "\n".join(lines)
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> int:
    try:
        changed = [d.name for d in sorted(SKILLS_ROOT.glob(f"{PREFIX}*"))
                   if (d / "SKILL.md").exists() and render(d / "SKILL.md")]
    except Malformed as e:
        print(f"  {e}", file=sys.stderr)
        return 1
    print(f"rendered: {len(changed)} changed" + (f" ({', '.join(changed)})" if changed else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
