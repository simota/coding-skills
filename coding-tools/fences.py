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
import html
from html.parser import HTMLParser

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
    """{line index: title} for every top-level level-2 heading, ATX or setext,
    as it renders — closing hashes and surrounding spaces gone. A heading in a
    quote or a list item is part of an example, not a section of the page."""
    toks = _tokens("\n".join(lines))
    return {tok.map[0]: toks[i + 1].content.strip()
            for i, tok in enumerate(toks)
            if tok.type == "heading_open" and tok.tag == "h2" and tok.level == 0
            and tok.map}


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


class _Visible(HTMLParser):
    """The text an HTML block shows, by line offset. A `<` that opens no tag is
    text, as a browser shows it; comments, attributes and the contents of a
    script or style are not.

    A text run is read back from its source span and decoded one source line
    at a time, so a reference lands on the line it is written on (`&#10;`
    shows a break but occupies no line), and it is decoded by the browser's
    rules (`&amp` and `&#40` work without `;`, `&colon` does not), whatever
    this Python's parser makes of it."""

    SCRIPT = ("script", "style")

    def __init__(self, source: str) -> None:
        super().__init__(convert_charrefs=True)
        self.src = source
        self.starts = [0]
        for line in source.split("\n"):
            self.starts.append(self.starts[-1] + len(line) + 1)
        self.text_from: int | None = None
        self.hidden = False  # inside a script or style, which shows nothing
        self.out: dict[int, str] = {}

    def _offset(self) -> int:
        line, col = self.getpos()
        return self.starts[line - 1] + col

    def _flush(self, end: int) -> None:
        if self.text_from is None:
            return
        first = self.src.count("\n", 0, self.text_from)
        for i, raw in enumerate(self.src[self.text_from:end].split("\n")):
            shown = html.unescape(raw).replace("\n", " ").replace("\r", " ")
            if shown:  # a lone space between two tags still separates words
                self.out[first + i] = self.out.get(first + i, "") + shown
        self.text_from = None

    def handle_data(self, data: str) -> None:
        if self.text_from is None and not self.hidden:
            self.text_from = self._offset()

    def _boundary(self, *_args) -> None:
        self._flush(self._offset())

    def handle_starttag(self, tag: str, attrs) -> None:
        self._boundary()
        if tag in self.SCRIPT:
            self.hidden = True

    def handle_endtag(self, tag: str) -> None:
        self._boundary()
        if tag in self.SCRIPT:
            self.hidden = False

    handle_startendtag = handle_comment = handle_decl = handle_pi = unknown_decl = _boundary

    def close(self) -> None:
        super().close()
        self._flush(len(self.src))


def live_text(text: str) -> dict[int, str]:
    """{line index: the text that renders there outside code}. Code spans,
    code blocks, HTML tags and comments are absent; a span crossing lines is
    absent on every line it covers. Text inside an HTML block renders too, so
    it is kept, line by line, with the tags and comments taken out."""
    out: dict[int, str] = {}
    for line, child in _inline(text):
        if child.type == "text":
            out[line] = out.get(line, "") + child.content
    for tok in _tokens(text):
        if tok.type == "html_block" and tok.map:
            parser = _Visible(tok.content)
            parser.feed(tok.content)
            parser.close()
            for offset, shown in parser.out.items():
                i = tok.map[0] + offset
                out[i] = out.get(i, "") + shown
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
