#!/usr/bin/env python3
"""Keep a project's shared toolbox honest: every tool says what it is for, and
the index says exactly what the tools say.

    python3 toolbox.py index [.agents/toolbox]
    python3 toolbox.py check [.agents/toolbox]

A toolbox is `<dir>/tools/`, one executable file per tool, and `<dir>/INDEX.md`.
Each tool carries six header lines in a comment near its top:

    # Purpose: seed a local database with two tenants
    # Use when: a check needs data that crosses a tenant boundary
    # Run: .agents/toolbox/tools/seed-tenants --db "$DATABASE_URL"
    # Proves: prints `seeded 2 tenants` and exits 0
    # Side effects: mutates — inserts rows into the database named by --db
    # Verified: 2026-01-31 by running the Run line against an empty database

**The index is generated, never written.** It is what an agent reads before
writing a script of its own, so a row that disagrees with its tool sends the
reader to the wrong one. `index` writes it from the headers and refuses while
any header is incomplete; `check` fails when the file on disk differs.

**`check` reads; it never runs a tool.** It can say a header is whole, a file
is executable and nothing obviously pinned or secret is in it. Whether the tool
still does what `Proves:` says is found by running it, which is the skill's
work and not this file's. A clean check is not a working toolbox.

Exit status: 0 nothing found, 1 at least one finding, 2 the invocation was
refused.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import sys

FIELDS = ("Purpose", "Use when", "Run", "Proves", "Side effects", "Verified")
EFFECTS = ("read-only", "scratch", "mutates")
HEAD_LINES = 40          # a header further down than this is not at the top
MAX_TOOLS = 20           # every agent that looks reads the whole index
DEFAULT_DIR = ".agents/toolbox"

FIELD_RE = re.compile(rf"^\W*({'|'.join(FIELDS)}):\s*(.+?)\s*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\b")

# What makes a tool work on one machine, in one session, for one person.
PINNED = (
    (re.compile(r"(?<![\w.$}])/(?:Users|home)/[\w.-]+"), "an absolute home path"),
    (re.compile(r"\b[0-9a-f]{40}\b"), "a full commit hash"),
)
# High-precision shapes only. Finding none is not evidence there is none.
SECRETS = (
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "a private key"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "an AWS access key id"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"), "a GitHub token"),
)

PREAMBLE = """# Toolbox

Scripts earlier runs kept because they were costly to derive. Read this before
writing one. Generated from each tool's header by `toolbox.py index` — edit the
tool, never this file.

| Tool | Purpose | Use when | Run | Side effects |
|---|---|---|---|---|
"""


def tool_files(box: pathlib.Path) -> list[pathlib.Path]:
    tools = box / "tools"
    if not tools.is_dir():
        return []
    return sorted(p for p in tools.iterdir() if not p.name.startswith("."))


def header(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for line in text.splitlines()[:HEAD_LINES]:
        m = FIELD_RE.match(line)
        if m and m.group(1) not in found:
            found[m.group(1)] = m.group(2)
    return found


def read(path: pathlib.Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def header_findings(box: pathlib.Path) -> list[str]:
    """What stops a tool from having an index row at all."""
    out = []
    for path in tool_files(box):
        name = f"tools/{path.name}"
        if path.is_dir():
            out.append(f"{name}/ is a directory; a tool is one file with its header in it")
            continue
        text = read(path)
        if text is None:
            out.append(f"{name} is not readable as text, so it carries no header")
            continue
        missing = [f for f in FIELDS if f not in header(text)]
        if missing:
            out.append(f"{name} header is missing {', '.join(missing)} "
                       f"(within its first {HEAD_LINES} lines)")
    return out


def render(box: pathlib.Path) -> str:
    def cell(value: str) -> str:
        return value.replace("|", "\\|")

    rows = []
    for path in tool_files(box):
        h = header(read(path) or "")
        rows.append(f"| `tools/{cell(path.name)}` | {cell(h['Purpose'])} | {cell(h['Use when'])} "
                    f"| `{cell(h['Run'])}` | {cell(h['Side effects'])} |\n")
    return PREAMBLE + "".join(rows)


def check(box: pathlib.Path, max_tools: int) -> list[str]:
    out = header_findings(box)
    files = [p for p in tool_files(box) if p.is_file()]
    for path in files:
        name = f"tools/{path.name}"
        text = read(path)
        if text is None:
            continue
        if not os.access(path, os.X_OK):
            out.append(f"{name} is not executable; its Run line cannot be followed as written")
        h = header(text)
        effect = h.get("Side effects")
        if effect is not None and not effect.startswith(EFFECTS):
            out.append(f"{name} Side effects starts with {effect.split()[0]!r}, "
                       f"not one of {', '.join(EFFECTS)}")
        verified = h.get("Verified")
        if verified is not None and not DATE_RE.match(verified):
            out.append(f"{name} Verified does not start with a YYYY-MM-DD date")
        for number, line in enumerate(text.splitlines(), 1):
            for pattern, what in PINNED + SECRETS:
                if pattern.search(line):
                    out.append(f"{name}:{number} holds {what}; make it an argument "
                               "or read it from the environment")
    if len(files) > max_tools:
        out.append(f"{len(files)} tools (max {max_tools}); merge or delete before adding")
    index = box / "INDEX.md"
    if not header_findings(box) and (files or index.exists()):
        if read(index) != render(box):
            out.append("INDEX.md does not match the tools' headers (run: toolbox.py index)")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("command", choices=("index", "check"))
    parser.add_argument("dir", nargs="?", default=DEFAULT_DIR)
    parser.add_argument("--max", type=int, default=MAX_TOOLS, dest="max_tools",
                        help=f"most tools a toolbox may hold (default {MAX_TOOLS})")
    args = parser.parse_intermixed_args(argv)
    box = pathlib.Path(args.dir)

    if args.command == "index":
        findings = header_findings(box)
        if not findings:
            if not (box / "tools").is_dir():
                print(f"{box}/tools does not exist; there is nothing to index", file=sys.stderr)
                return 2
            (box / "INDEX.md").write_text(render(box), encoding="utf-8")
            print(f"{box}/INDEX.md: {len(tool_files(box))} tools")
            return 0
    else:
        findings = check(box, args.max_tools)
        if not findings:
            print(f"{box}: {len(tool_files(box))} tools, nothing found "
                  "(headers and index only; no tool was run)")
            return 0
    for finding in findings:
        print(finding, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
