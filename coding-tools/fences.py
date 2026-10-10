"""What a markdown page renders as, read by a CommonMark parser.

Shared by validate.py, render.py and figures_check.py. Each of them once decided
"inside a code fence", "a heading", "inside a code span" and "a link" with its
own regular expressions, and every round of review found another construct the
expressions misread: a fence containing a fence-like line, a span crossing a
line, a heading or list item or quote marker between two backticks, a setext
heading, a thematic break, a lazy quote continuation, an inline HTML tag. Each
misreading either hid a real `#TODO(agent):` marker or broken link from the
rules, or failed a valid page.

So nothing here parses markdown by hand: markdown-it-py does, in CommonMark mode
with GitHub's tables, and these functions only read its tokens. A block token
carries the source lines it spans (`map`), which is how a finding keeps its
line number.
"""
from __future__ import annotations

import functools

from markdown_it import MarkdownIt

_MD = MarkdownIt("commonmark", {"html": True}).enable(["table", "strikethrough"])
# Links are reported as written, not percent-encoded: `a b.md` is the path a
# reader would look for, and `a%20b.md` is not on disk.
_MD.normalizeLink = lambda url: url
_MD.validateLink = lambda url: True


@functools.lru_cache(maxsize=256)
def _tokens(text: str) -> tuple:
    return tuple(_MD.parse(text))


def fence_mask(lines: list[str]) -> list[bool]:
    """True for every line of a code block — fenced or indented — delimiters
    included. A heading or a marker there is an example, not a delimiter."""
    mask = [False] * len(lines)
    for tok in _tokens("\n".join(lines)):
        if tok.type in ("fence", "code_block") and tok.map:
            for i in range(tok.map[0], min(tok.map[1], len(lines))):
                mask[i] = True
    return mask


def blocks(lines: list[str]) -> list[list[str]]:
    """The content lines of each fenced block, in order."""
    return [tok.content.removesuffix("\n").split("\n")
            for tok in _tokens("\n".join(lines)) if tok.type == "fence"]


def h2_lines(lines: list[str]) -> dict[int, str]:
    """{line index: title} for every level-2 heading, ATX or setext, as it
    renders — closing hashes and surrounding spaces gone."""
    toks = _tokens("\n".join(lines))
    return {tok.map[0]: toks[i + 1].content.strip()
            for i, tok in enumerate(toks)
            if tok.type == "heading_open" and tok.tag == "h2" and tok.map}


def marker_lines(lines: list[str], marker: str) -> list[int]:
    """Indices of lines that are exactly `marker`, outside any code block. A
    marker quoted in prose or shown in an example is text, not a delimiter."""
    return [i for i, (line, code) in enumerate(zip(lines, fence_mask(lines)))
            if line.strip() == marker and not code]


def _inline(text: str):
    """(line index, child token) for every inline child, in order.

    A break advances the line, and a text fragment is anchored to the first
    source line at or after the current one that contains it: a code span
    crossing a line folds its newline into a space, so counting breaks alone
    would number everything after it one line short."""
    src = text.split("\n")
    for tok in _tokens(text):
        if tok.type != "inline" or not tok.map:
            continue
        line, end = tok.map
        for child in tok.children or []:
            if child.type == "text" and child.content.strip():
                line = next((j for j in range(line, end) if child.content in src[j]), line)
            yield line, child
            if child.type in ("softbreak", "hardbreak"):
                line += 1


def live_text(text: str) -> dict[int, str]:
    """{line index: the text that renders there outside code}. Code spans,
    code blocks and HTML are absent; a span crossing lines is absent on every
    line it covers."""
    out: dict[int, str] = {}
    for line, child in _inline(text):
        if child.type == "text":
            out[line] = out.get(line, "") + child.content
    return out


def links(text: str) -> list[str]:
    """Every link and image target the page renders, reference-style included.
    A link written inside code is not one."""
    found = []
    for _, child in _inline(text):
        if child.type == "link_open":
            found.append(child.attrs.get("href", ""))
        elif child.type == "image":
            found.append(child.attrs.get("src", ""))
    return found
