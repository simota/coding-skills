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


# A line that starts a new block ends the paragraph a span would have to sit in:
# a blank line, an ATX heading, a list item, a block quote, a fence, an HTML block.
_BLOCK_START = re.compile(r"[ \t]*$|[ ]{0,3}(?:#{1,6}(?:[ \t]|$)|[-+*][ \t]|\d{1,9}[.)][ \t]|>|`{3,}|~{3,}|<)")


def mask_code_spans(text: str) -> str:
    """The text with every inline code span — and every fenced block — blanked
    out, newlines kept, so a line number still points at the same line.

    As CommonMark reads spans: a run of n backticks opens one, and only a run of
    exactly n closes it, possibly on a later line of the same paragraph but never
    past the start of another block. A backslash escapes one backtick, not the
    run: the rest of the run can still open a span. A run with no close is
    literal text, and what follows it is not hidden.
    """
    lines = text.split("\n")
    mask = fence_mask(lines)
    out = [" " * len(l) if fenced else l for l, fenced in zip(lines, mask)]
    # Paragraphs: maximal runs of unfenced lines, cut before any block start.
    paragraphs, cur = [], []
    for i, line in enumerate(lines):
        if mask[i] or (cur and _BLOCK_START.match(line)):
            if cur:
                paragraphs.append(cur)
            cur = []
        if mask[i] or not line.strip():
            continue
        if h_any(line):                       # a heading is a block of one line
            paragraphs.append([i])
            continue
        cur.append(i)
    if cur:
        paragraphs.append(cur)
    for para in paragraphs:
        for start, end in _spans("\n".join(lines[i] for i in para)):
            pos = 0
            for i in para:                    # map the span back onto its lines
                a, b = max(start - pos, 0), min(end - pos, len(lines[i]))
                if a < b:
                    out[i] = out[i][:a] + " " * (b - a) + out[i][b:]
                pos += len(lines[i]) + 1
    return "\n".join(out)


def _spans(text: str) -> list[tuple[int, int]]:
    """(start, end) of each code span in one paragraph."""
    found, i = [], 0
    while True:
        m = re.compile(r"`+").search(text, i)
        if m is None:
            return found
        start, run = m.start(), m.group()
        backslashes = 0
        while start - backslashes > 0 and text[start - backslashes - 1] == "\\":
            backslashes += 1
        if backslashes % 2:                   # the first backtick is escaped
            start, run = start + 1, run[1:]
            if not run:
                i = m.end()
                continue
        close = re.compile(rf"(?<!`){run}(?!`)").search(text, m.end())
        if close is None:
            i = m.end()
            continue
        found.append((start, close.end()))
        i = close.end()


_ATX = re.compile(r"^ {0,3}#{1,6}(?:[ \t]|$)")


def h_any(line: str) -> bool:
    """Whether the line is an ATX heading of any level."""
    return _ATX.match(line) is not None


_H2 = re.compile(r"^ {0,3}##[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$")


def h2_title(line: str) -> str | None:
    """The title of a `## ` heading as CommonMark reads it — up to three spaces
    of indent, closing hashes and trailing spaces dropped — or None."""
    m = _H2.match(line)
    return m.group(1) if m else None
