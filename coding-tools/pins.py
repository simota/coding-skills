#!/usr/bin/env python3
"""Fail when the installed packages are not the ones requirements.txt pins.

CI installs the pins; a local run uses whatever the interpreter has. A gate
green on other versions is green on a tree CI never ran, and nothing said so.

Run: make deps (part of make check)
"""
from __future__ import annotations

import re
import sys
from importlib import metadata
from pathlib import Path
from typing import Callable

REQUIREMENTS = Path(__file__).resolve().parent / "requirements.txt"
# The one form read. Extras, markers, ranges and options (`-r`, `--hash`) are
# refused by name: read as a name, `pyyaml[x]` would be reported missing.
PIN = re.compile(r"([A-Za-z0-9][A-Za-z0-9._-]*)==([A-Za-z0-9.+!_-]+)")


def mismatches(text: str, installed: Callable[[str], str] = metadata.version) -> list[str]:
    """One line per requirement the interpreter does not satisfy exactly."""
    found = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        pin = PIN.fullmatch(line.replace(" ", ""))
        if not pin:
            found.append(f"{line} is not a plain name==version pin, so no version can be checked")
            continue
        name, version = pin.groups()
        try:
            have = installed(name)
        except metadata.PackageNotFoundError:
            have = "missing"
        if have != version:
            found.append(f"{name} {have}, pinned {version}")
    return found


def main() -> int:
    found = mismatches(REQUIREMENTS.read_text(encoding="utf-8-sig"))   # pip accepts a BOM
    for line in found:
        print(f"pins: {line}")
    if found:
        print("pins: run python3 -m pip install -r coding-tools/requirements.txt")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
