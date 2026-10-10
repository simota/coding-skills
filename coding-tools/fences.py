"""Which lines of a markdown page sit inside a fenced code block.

Shared by validate.py, render.py and figures_check.py, because each of them
once decided this by toggling on every line that starts with three backticks.
That is wrong in both directions: a fence can open with tildes or with more than
three backticks, and inside a fence a line such as ```` ```text ```` is content,
not a close — a closing fence repeats the opening character, at least as many
times, with nothing after it but spaces. One toggle too many and every heading
after it reads as code, so a valid skill fails its section checks.

This follows CommonMark for the cases this corpus can contain; it does not
model fences inside list items or block quotes.
"""
from __future__ import annotations

import re

_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


def kinds(lines: list[str]) -> list[str]:
    """Each line as "text", or as the "open", "body" or "close" of a fence."""
    out, opener = [], None
    for line in lines:
        if opener is None:
            m = _OPEN.match(line)
            # A backtick fence's info string may not itself contain a backtick.
            if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
                opener = m.group(1)
                out.append("open")
            else:
                out.append("text")
        elif re.match(rf"^ {{0,3}}{re.escape(opener[0])}{{{len(opener)},}}\s*$", line):
            opener = None
            out.append("close")
        else:
            out.append("body")
    return out


def fence_mask(lines: list[str]) -> list[bool]:
    """True for every line inside a fence, the delimiter lines included."""
    return [k != "text" for k in kinds(lines)]


def blocks(lines: list[str]) -> list[list[str]]:
    """The content lines of each fenced block, in order. An unclosed fence runs
    to the end of the page, as it renders."""
    out: list[list[str]] = []
    for line, kind in zip(lines, kinds(lines)):
        if kind == "open":
            out.append([])
        elif kind == "body":
            out[-1].append(line)
    return out


def marker_lines(lines: list[str], marker: str) -> list[int]:
    """Indices of lines that are exactly `marker`, outside any fence. A marker
    quoted in prose or shown in an example is text, not a delimiter."""
    return [i for i, (line, fenced) in enumerate(zip(lines, fence_mask(lines)))
            if line.strip() == marker and not fenced]


def mask_code_spans(text: str) -> str:
    """The text with every inline code span blanked out, newlines kept, so a
    line number still points at the same line.

    As CommonMark reads spans: a run of n backticks opens one only if it is not
    escaped, and only a run of exactly n closes it — possibly on a later line
    of the same paragraph, never past a blank line. A run with no such close is
    literal text, and what follows it is not hidden.
    """
    out = list(text)
    i = 0
    for m in re.finditer(r"`+", text):
        start = m.start()
        if start < i:
            continue
        backslashes = 0
        while start - backslashes > 0 and text[start - backslashes - 1] == "\\":
            backslashes += 1
        if backslashes % 2:                   # an escaped backtick is literal
            i = start + 1
            continue
        run = m.group()
        paragraph_end = text.find("\n\n", m.end())
        limit = len(text) if paragraph_end == -1 else paragraph_end
        close = re.compile(rf"(?<!`){run}(?!`)").search(text, m.end(), limit)
        if close is None:
            i = m.end()
            continue
        for k in range(start, close.end()):
            if out[k] != "\n":
                out[k] = " "
        i = close.end()
    return "".join(out)
