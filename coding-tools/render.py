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

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.dont_write_bytecode = True                     # no __pycache__ in the tools dir
from fences import h2_lines, marker_lines          # noqa: E402

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


def heading_line(lines: list[str], section: str) -> int | None:
    """The index of `## <section>` as a whole line outside any fence."""
    return next((i for i, title in sorted(h2_lines(lines).items()) if title == section),
                None)


def render(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise Malformed(f"{path.parent.name}/{path.name}: not UTF-8 ({e.reason} at byte "
                        f"{e.start}); fix by hand") from None
    original = text
    for key, spec in H["delivered"].items():
        open_m, close_m = f"<!-- deliver:{key} -->", f"<!-- /deliver:{key} -->"
        # One marker without the other, a duplicate, or the pair reversed: any
        # rewrite would either insert a second block or swallow the text between.
        # Only a whole line outside a fence is a marker; one quoted in prose is not.
        lines = text.split("\n")
        opens, closes = marker_lines(lines, open_m), marker_lines(lines, close_m)
        if (len(opens), len(closes)) not in ((0, 0), (1, 1)) or (
                opens and opens[0] > closes[0]):
            raise Malformed(f"{path.parent.name}/{path.name}: the {key} markers are "
                            f"unpaired ({len(opens)} open, {len(closes)} close); fix by hand")
        if not delivered_to(spec, path.parent.name):
            if opens:
                i = opens[0]
                del lines[i:closes[0] + 1]
                while i > 0 and not lines[i - 1].strip():
                    i -= 1
                    del lines[i]
                text = "\n".join(lines)
            continue
        block = (ROOT / "coding-registry" / "delivered" / f"{key}.md").read_text(
            encoding="utf-8").rstrip("\n")
        payload = f"{open_m}\n{block}\n{close_m}"
        if opens:
            lines[opens[0]:closes[0] + 1] = payload.split("\n")
            text = "\n".join(lines)
        else:
            start = heading_line(lines, spec["section"])
            if start is None:
                print(f"  {path.name}: no section {spec['section']!r}", file=sys.stderr)
                continue
            # append at the end of that section, before the next heading
            end = next((i for i in sorted(h2_lines(lines)) if i > start), len(lines))
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
