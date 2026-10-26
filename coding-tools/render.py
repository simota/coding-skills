#!/usr/bin/env python3
"""Write the delivered blocks back into every SKILL.md.

A contract kept only in the shared directory is not read on most launches, so the operative
part is carried verbatim in each skill. That only stays true if changing one
line does not cost eight hand edits — this is that cost, paid once.

Idempotent: run it, commit the diff.
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
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
    """A page that cannot be rewritten without guessing what to replace."""


def heading_line(lines: list[str], section: str) -> int | None:
    """The index of `## <section>` as a whole line outside any fence."""
    return next((i for i, title in sorted(h2_lines(lines).items()) if title == section),
                None)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise Malformed(f"{path.parent.name}/{path.name}: not UTF-8 ({e.reason} at byte "
                        f"{e.start}); fix by hand") from None
    except OSError as e:
        raise Malformed(f"{path}: cannot read ({e.strerror or e})") from None


def check_structure(path: Path, text: str) -> None:
    """Reject ambiguous ranges before a replacement can swallow hand-written text."""
    lines = text.split("\n")
    headings = h2_lines(lines)
    spans = []
    for key, spec in H["delivered"].items():
        opens = marker_lines(lines, f"<!-- deliver:{key} -->")
        closes = marker_lines(lines, f"<!-- /deliver:{key} -->")
        if (len(opens), len(closes)) not in ((0, 0), (1, 1)) or (
                opens and opens[0] > closes[0]):
            raise Malformed(f"{path.parent.name}/{path.name}: the {key} markers are "
                            f"unpaired ({len(opens)} open, {len(closes)} close); fix by hand")
        if opens:
            start, end = opens[0], closes[0]
            spans.append((start, end, key))
            if any(start < i <= end for i in headings):
                raise Malformed(f"{path.parent.name}/{path.name}: the {key} block crosses "
                                "a section heading; fix by hand")
        if delivered_to(spec, path.parent.name):
            matches = [i for i, title in headings.items() if title == spec["section"]]
            if len(matches) != 1:
                raise Malformed(f"{path.parent.name}/{path.name}: expected one section "
                                f"{spec['section']!r}, found {len(matches)}; fix by hand")
            section_start = matches[0]
            section_end = min((i for i in headings if i > section_start), default=len(lines))
            if opens and not section_start < opens[0] < closes[0] < section_end:
                raise Malformed(f"{path.parent.name}/{path.name}: the {key} block is not "
                                f"under {spec['section']!r}; fix by hand")
    spans.sort()
    for left, right in zip(spans, spans[1:]):
        if left[1] >= right[0]:
            raise Malformed(f"{path.parent.name}/{path.name}: the {left[2]} and {right[2]} "
                            "blocks overlap; fix by hand")


def prepared(path: Path) -> tuple[str, bool]:
    text = read_text(path)
    check_structure(path, text)
    original = text
    for key, spec in H["delivered"].items():
        open_m, close_m = f"<!-- deliver:{key} -->", f"<!-- /deliver:{key} -->"
        lines = text.split("\n")
        opens, closes = marker_lines(lines, open_m), marker_lines(lines, close_m)
        if not delivered_to(spec, path.parent.name):
            if opens:
                i = opens[0]
                del lines[i:closes[0] + 1]
                while i > 0 and not lines[i - 1].strip():
                    i -= 1
                    del lines[i]
                if 0 < i < len(lines) and lines[i].strip():
                    # Text written after the block stays its own paragraph.
                    lines.insert(i, "")
                text = "\n".join(lines)
            continue
        block = read_text(ROOT / "coding-registry" / "delivered" / f"{key}.md").rstrip("\n")
        payload = f"{open_m}\n{block}\n{close_m}"
        if opens:
            lines[opens[0]:closes[0] + 1] = payload.split("\n")
            text = "\n".join(lines)
        else:
            start = heading_line(lines, spec["section"])
            if start is None:
                raise Malformed(f"{path.parent.name}/{path.name}: no section "
                                f"{spec['section']!r}; fix by hand")
            # append at the end of that section, before the next heading
            end = next((i for i in sorted(h2_lines(lines)) if i > start), len(lines))
            while end > start + 1 and not lines[end - 1].strip():
                end -= 1
            lines[end:end] = payload.split("\n")
            text = "\n".join(lines)
    check_structure(path, text)
    return text, text != original


def staged(path: Path, text: str) -> Path:
    """The new text, complete on disk beside `path` and not yet in its place."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, path.stat().st_mode & 0o7777)
    except BaseException:
        os.unlink(tmp)
        raise
    return Path(tmp)


def write_all(updates: list[tuple[Path, str]]) -> None:
    """Every file or none, as far as a filesystem allows. Writing in place
    truncates as it goes: a full disk left earlier skills rewritten, one cut off
    mid-sentence, and the rest stale. Each new text is written in full first;
    only then does a rename, which replaces a file whole, put each in place."""
    # A link is written through, as writing in place did, not replaced by a file.
    updates = [(path.resolve(), text) for path, text in updates]
    done: list[Path] = []
    try:
        for path, text in updates:
            done.append(staged(path, text))
    except BaseException:
        for tmp in done:
            tmp.unlink(missing_ok=True)
        raise
    try:
        for tmp, (path, _) in zip(done, updates):
            os.replace(tmp, path)
    finally:
        for tmp in done:
            tmp.unlink(missing_ok=True)


def render(path: Path) -> bool:
    text, changed = prepared(path)
    if changed:
        write_all([(path, text)])
    return changed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="fail on stale blocks without writing")
    args = ap.parse_args(argv)
    try:
        updates = []
        for d in sorted(SKILLS_ROOT.glob(f"{PREFIX}*")):
            path = d / "SKILL.md"
            if path.exists():
                text, changed = prepared(path)
                if changed:
                    updates.append((path, text))
        if args.check:
            if updates:
                print("stale delivered blocks: " + ", ".join(path.parent.name for path, _ in updates)
                      + "; run: make render")
                return 1
            print("delivered blocks current")
            return 0
        # A malformed later skill, or a write that fails, must not leave
        # earlier skills half-rendered.
        write_all(updates)
    except (Malformed, OSError) as e:
        print(f"  {e}", file=sys.stderr)
        return 1
    changed = [path.parent.name for path, _ in updates]
    print(f"rendered: {len(changed)} changed" + (f" ({', '.join(changed)})" if changed else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
