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
            heading = f"## {spec['section']}\n"
            if heading not in text:
                print(f"  {path.name}: no section {spec['section']!r}", file=sys.stderr)
                continue
            head, rest = text.split(heading, 1)
            # append at the end of that section, before the next heading
            nxt = rest.find("\n## ")
            body, tail = (rest[:nxt], rest[nxt:]) if nxt != -1 else (rest, "")
            text = head + heading + body.rstrip("\n") + "\n" + payload + "\n" + tail
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
