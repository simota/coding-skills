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
from bisect import bisect_right
from html.parser import HTMLParser

from markdown_it import MarkdownIt
from markdown_it.common.html_blocks import block_names
from markdown_it.parser_inline import ParserInline
from markdown_it.rules_inline import StateInline, backtick


class _LocatedState(StateInline):
    """Keep the parser's source line when it emits an inline token.

    Rendered text cannot locate itself reliably in the source: entities and
    escapes change its spelling, and code spans and link targets fold newlines.
    Token creation happens before that information is lost. Inline content has
    the same source lines as its enclosing block, without quote/list prefixes.
    """

    def __init__(self, *args) -> None:
        super().__init__(*args)
        self._starts = [0] + [i + 1 for i, c in enumerate(self.src) if c == "\n"]

    def pushPending(self):
        token = super().pushPending()
        line = bisect_right(self._starts, self.pos) - 1
        token.map = [line - token.content.count("\n"), line + 1]
        return token

    def push(self, *args):
        token = super().push(*args)
        line = bisect_right(self._starts, self.pos) - 1
        token.map = [line, line + 1]
        return token


class _LocatedInline(ParserInline):
    def parse(self, src, md, env, tokens):
        state = _LocatedState(src, md, env, tokens)
        self.tokenize(state)
        for rule in self.ruler2.getRules(""):
            rule(state)
        return state.tokens


def _located_backtick(state, silent):
    start, count = state.pos, len(state.tokens)
    matched = backtick(state, silent)
    if matched and not silent and len(state.tokens) > count:
        token = state.tokens[-1]
        if token.type == "code_inline":
            width = len(token.markup)
            # The parser already found the closing delimiter. Preserve those
            # exact source fragments before CommonMark folds their newlines.
            token.meta["source_lines"] = state.src[start + width:state.pos - width].split("\n")
    return matched


_MD = MarkdownIt("commonmark")
_MD.inline = _LocatedInline()
_MD.configure("commonmark", {"html": True}).enable(["table", "strikethrough"])
_MD.inline.ruler.at("backticks", _located_backtick)
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
    """(source line index, child token) for every inline child, in order."""
    for tok in _tokens(text):
        if tok.type != "inline" or not tok.map:
            continue
        for child in tok.children or []:
            yield tok.map[0] + (child.map[0] if child.map else 0), child


class _Visible(HTMLParser):
    """The text an HTML block shows, by line offset. A `<` that opens no tag is
    text, as a browser shows it; comments, attributes and the contents of a
    script or style are not.

    A text run is read back from its source span and decoded one source line
    at a time, so a reference lands on the line it is written on (`&#10;`
    shows a break but occupies no line), and it is decoded by the browser's
    rules (`&amp` and `&#40` work without `;`, `&colon` does not), whatever
    this Python's parser makes of it."""

    HIDDEN = ("script", "style", "code", "pre")
    BREAKS = {*block_names, "br", "img", "code", "pre"}

    def __init__(self, source: str, code=None) -> None:
        super().__init__(convert_charrefs=True)
        self.src = source
        self.starts = [0]
        for line in source.split("\n"):
            self.starts.append(self.starts[-1] + len(line) + 1)
        self.text_from: int | None = None
        self.hidden: list[str] = []  # script/style text and code are not live prose
        self.out: dict[int, str] = {}
        self.html_code: dict[int, str] = {}
        self.links: list[tuple[int, str]] = []
        self._code = code or {}
        self.code: list[tuple[int, str, list[str]]] = []

    def _offset(self) -> int:
        line, col = self.getpos()
        return self.starts[line - 1] + col

    def _flush(self, end: int) -> None:
        if self.text_from is None:
            return
        first = self.src.count("\n", 0, self.text_from)
        output = self.html_code if self.hidden else self.out
        for i, raw in enumerate(self.src[self.text_from:end].split("\n")):
            shown = html.unescape(raw).replace("\n", " ").replace("\r", " ")
            if shown:  # a lone space between two tags still separates words
                output[first + i] = output.get(first + i, "") + shown
        self.text_from = None

    def handle_data(self, data: str) -> None:
        if self.text_from is None and not any(t in ("script", "style") for t in self.hidden):
            self.text_from = self._offset()

    def _boundary(self, *_args) -> None:
        self._flush(self._offset())

    def _separate(self, tag: str) -> None:
        if tag in self.BREAKS:
            line = self.getpos()[0] - 1
            output = self.html_code if self.hidden else self.out
            output[line] = output.get(line, "") + " "

    def handle_starttag(self, tag: str, attrs) -> None:
        self._boundary()
        self._separate(tag)
        if not self.hidden and tag in ("a", "img"):
            attribute = "href" if tag == "a" else "src"
            target = next((value for key, value in attrs if key == attribute), None)
            if target is not None:
                self.links.append((self.getpos()[0] - 1, target))
        if tag in self.HIDDEN:
            self.hidden.append(tag)

    def handle_endtag(self, tag: str) -> None:
        self._boundary()
        self._separate(tag)
        if tag in self.hidden:
            i = len(self.hidden) - 1 - self.hidden[::-1].index(tag)
            del self.hidden[i:]

    def handle_comment(self, _data) -> None:
        self._boundary()
        # Generated placeholders retain the real token without rendering its
        # contents. HTMLParser does not expose comments inside script/style,
        # so hidden code cannot lend a path or residual class to visible prose.
        code = self._code.get(self._offset())
        if code is not None and not any(t in ("script", "style") for t in self.hidden):
            self.code.append(code)

    handle_startendtag = handle_starttag
    handle_decl = handle_pi = unknown_decl = _boundary

    def close(self) -> None:
        super().close()
        self._flush(len(self.src))


def _escape(text: str) -> str:
    # A decoded character reference can contain a newline without occupying a
    # source line. Keep it encoded until _Visible assigns its source location.
    return html.escape(text).replace("\n", "&#10;").replace("\r", "&#13;")


@functools.lru_cache(maxsize=256)
def _visible(text: str) -> _Visible:
    """Project parsed tokens into HTML while preserving their source lines.

    Raw HTML and Markdown then share one visibility pass, including an inline
    script/code element, raw links, and block boundaries. Code is replaced by a
    separator so removing an example cannot join two fragments into a marker.
    """
    parts: list[str] = []
    code = {}
    line = size = 0

    def emit(fragment: str, start: int | None = None) -> int:
        nonlocal line, size
        if start is not None and start > line:
            parts.append("\n" * (start - line))
            size += start - line
            line = start
        offset = size
        parts.append(fragment)
        size += len(fragment)
        line += fragment.count("\n")
        return offset

    for tok in _tokens(text):
        start = tok.map[0] if tok.map else None
        if tok.type == "html_block" and tok.map:
            emit(tok.content, start)
        elif tok.type in ("fence", "code_block"):
            emit(" ", start)
        elif tok.type == "inline" and tok.map:
            for child in tok.children or []:
                at = tok.map[0] + (child.map[0] if child.map else 0)
                if child.type == "text":
                    emit(_escape(child.content), at)
                elif child.type == "html_inline":
                    emit(child.content, at)
                elif child.type == "code_inline":
                    offset = emit("<!-- --> ", at)
                    code[offset] = (at, child.content, child.meta["source_lines"])
                elif child.type in ("softbreak", "hardbreak"):
                    emit(" ", at)
                elif child.type == "link_open":
                    emit(f'<a href="{_escape(child.attrs.get("href", ""))}">', at)
                elif child.type == "link_close":
                    emit("</a>", at)
                elif child.type == "image":
                    emit(f'<img src="{_escape(child.attrs.get("src", ""))}">', at)
        elif tok.nesting:
            emit(f"<{'/' if tok.nesting < 0 else ''}{tok.tag}>", start)
        elif tok.type == "hr":
            emit("<hr>", start)
    source = "".join(parts)
    parser = _Visible(source, code)
    parser.feed(source)
    parser.close()
    return parser


def live_text(text: str) -> dict[int, str]:
    """{source line index: visible prose}, excluding code, tags and comments."""
    return dict(_visible(text).out)


def links(text: str, *, line_range: tuple[int, int] | None = None) -> list[str]:
    """Every link and image target the page renders, reference-style included.
    A link written inside code is not one. An optional zero-based, half-open
    source range filters uses, while definitions are resolved from the page."""
    return [target for line, target in _visible(text).links
            if line_range is None or line_range[0] <= line < line_range[1]]


def code_spans(text: str, *, line_range: tuple[int, int] | None = None,
               include_html: bool = False) -> list[str]:
    """Inline code contents, excluding fenced/indented examples. With a source
    range, return only fragments written on those lines: a multiline span must
    not lend a residual class to a marker on a different source line. Residual
    checks may include visible HTML code/pre text; path checks leave examples
    in HTML pre blocks out. Script/style contents are never visible code."""
    visible = _visible(text)
    found = []
    for line, content, source_lines in visible.code:
        if line_range is None:
            found.append(content)
        else:
            for offset, fragment in enumerate(source_lines):
                if line_range[0] <= line + offset < line_range[1]:
                    found.append(fragment)
    if include_html:
        found.extend(shown for line, shown in visible.html_code.items()
                     if line_range is None or line_range[0] <= line < line_range[1])
    return found
