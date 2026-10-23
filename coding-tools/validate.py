#!/usr/bin/env python3
"""Static checks over the coding-* skill set.

Every threshold and every piece of vocabulary comes from coding-registry/harness.yaml.
Nothing is hard-coded here: a number written twice is a number that drifts.

A rule earns its place only if CI can decide it. Anything needing judgement
belongs in a review, not in this file.
"""
from __future__ import annotations

import os.path
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.dont_write_bytecode = True                     # no __pycache__ in the tools dir
from fences import code_spans, h2_lines, leading_code, links, live_text, marker_lines  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FAILURES: list[str] = []


def fail(rule: str, msg: str) -> None:
    FAILURES.append(f"{rule}: {msg}")


# --- corpus ------------------------------------------------------------------

class UniqueKeyLoader(yaml.SafeLoader):
    """A repeated key must not silently replace an earlier permission or limit."""

    def construct_mapping(self, node, deep=False):
        seen = set()
        for key_node, _ in node.value:
            if key_node.tag == "tag:yaml.org,2002:merge":
                continue  # An explicit key may override a YAML merge.
            key = self.construct_object(key_node, deep=deep)
            try:
                if key in seen:
                    raise yaml.constructor.ConstructorError(
                        "while constructing a mapping", node.start_mark,
                        f"found duplicate key {key!r}", key_node.start_mark)
                seen.add(key)
            except TypeError:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping", node.start_mark,
                    "found an unhashable key", key_node.start_mark) from None
        return super().construct_mapping(node, deep=deep)


class RegistryLoadError(ValueError):
    """A registry input could not be read or parsed; the corpus cannot run."""


def load(name: str):
    label = f"coding-registry/{name}"
    try:
        with (ROOT / label).open(encoding="utf-8") as fh:
            return yaml.load(fh, Loader=UniqueKeyLoader)
    except yaml.YAMLError as error:
        mark = getattr(error, "problem_mark", None)
        if mark is not None:
            label += f":{mark.line + 1}:{mark.column + 1}"
        problem = getattr(error, "problem", None) or str(error).splitlines()[0]
        raise RegistryLoadError(f"{label}: invalid YAML: {problem}") from error
    except UnicodeError as error:
        raise RegistryLoadError(f"{label}: not valid UTF-8: {error}") from error
    except OSError as error:
        raise RegistryLoadError(f"{label}: cannot read registry: {error.strerror or error}") from error


# The shape the rules read. Valid YAML of another shape crashed a rule with a
# traceback, or passed it silently: a scalar where a list belongs is iterated
# letter by letter. The gate judges only that, and what no rule judges (a
# positive limit, a non-empty chain); whether a list may be empty or a key
# absent is the rule's to say, in its own words, so lists here may be empty
# and only keys read unconditionally are required.
# `[x]` is a list of x; `{"*": x}` a mapping whose every value is x, and whose
# other named keys are also required; a tuple is any one of its shapes; a plain
# string other than TEXT/COUNT is that literal; a key ending in `?` may be
# absent. Keys not named here are not read.
COUNT = "a positive integer"
TEXT = "a non-empty string"
NONEMPTY = "non-empty"
STRINGS = [str]
# Read by a rule by name, on every run: absent, the rule crashed instead of the
# gate naming the key, and an absent class `tools` read as "grants no Bash".
LIMITS = ("skill_md_lines", "description_chars", "playbook_lines", "playbooks_per_skill",
          "shared_file_lines", "shared_lines_total", "skills_max", "routes_max",
          "route_stages_max", "repo_md_lines_total")
SHAPES = {
    "harness.yaml": {
        "set": TEXT, "prefix": TEXT, "shared_dir": TEXT, "skills_dir": str,
        "platform_dirs": STRINGS, "limits": {"*": COUNT, **dict.fromkeys(LIMITS, COUNT)},
        "permission_classes": {"*": {"tools": str, "writes?": bool}},
        "forbidden_description_terms": STRINGS, "engines?": dict, "refutation?": dict,
        "linked_tools?": {"*": ("all", STRINGS)},
        "finding_visuals?": {"playbook?": str, "contract?": str, "why?": str,
                             "required_of?": STRINGS, "forms?": STRINGS,
                             "triggers?": STRINGS, "floor?": STRINGS},
        "vocabulary": {"*": STRINGS, "patterns": STRINGS, "evidence_levels": STRINGS,
                       "residual_classes": STRINGS},
        "document_labels": STRINGS,
        "label_by_path": {"*": str}, "reference_headers": STRINGS,
        # A version is text: YAML reads `2.40` as the number 2.4.
        "source_authorities?": {"*": (str, None)}, "source_none_marker?": str,
        "verified_markers?": STRINGS, "external_paths?": STRINGS, "rot_patterns": STRINGS,
        # V35 reads every key. An empty own_word is in every body, so the rule
        # could not fail; an empty contract names the shared directory itself.
        "signature": {"name": TEXT, "contract": TEXT, "vocabulary": TEXT,
                      "required_of": STRINGS, "own_word": TEXT},
        "delivered": {"*": {"section": str, "only?": str}},
    },
    "capabilities.yaml": {"*": {"class?": str, "does?": STRINGS, "signals?": STRINGS,
                                "not?": [{"what?": str, "go?": str}]}},
    # Nothing else judges an empty chain: V7 and V13 would iterate nothing.
    "routes.yaml": {"*": {"pattern?": str, "chain": (NONEMPTY, STRINGS)}},
}


def misshapen(value, shape, where: str) -> list[str]:
    """Every place `value` departs from `shape`, by its path in the file."""
    at = where or "the file"
    if shape is TEXT:
        return [] if isinstance(value, str) and value.strip() else [f"{at} must be {TEXT}"]
    if shape is None:
        return [] if value is None else [f"{at} must be null"]
    if shape is COUNT:
        return [] if type(value) is int and value > 0 else [f"{at} must be {COUNT}"]
    if isinstance(shape, str):
        return [] if value == shape else [f"{at} must be {shape!r}"]
    if isinstance(shape, tuple) and shape[0] is NONEMPTY:
        if isinstance(value, list) and not value:
            return [f"{at} must not be empty"]
        return misshapen(value, shape[1], where)
    if isinstance(shape, tuple):
        tried = [misshapen(value, option, where) for option in shape]
        if all(tried):
            return [f"{at} must be one of: " + "; or ".join(
                p[0].removeprefix(at + " must be ") for p in tried)]
        return []
    if isinstance(shape, type):
        ok = isinstance(value, shape) and not (shape is int and isinstance(value, bool))
        return [] if ok else [f"{at} must be a {shape.__name__}"]
    if isinstance(shape, list):
        if not isinstance(value, list):
            return [f"{at} must be a list"]
        return [p for i, item in enumerate(value) for p in misshapen(item, shape[0], f"{where}[{i}]")]
    if not isinstance(value, dict):
        return [f"{at} must be a mapping"]
    problems = []
    if "*" in shape:
        for key, item in value.items():
            if not isinstance(key, str):
                problems.append(f"{at}: key {key!r} must be a string")
            problems += misshapen(item, shape.get(key, shape["*"]),
                                  f"{where}.{key}" if where else str(key))
        for key in shape:
            if key != "*" and key not in value:
                problems.append(f"{where}.{key} is missing" if where else f"{key} is missing")
        return problems
    for key, sub in shape.items():
        name = key.rstrip("?")
        path = f"{where}.{name}" if where else name
        if name in value:
            problems += misshapen(value[name], sub, path)
        elif not key.endswith("?"):
            problems.append(f"{path} is missing")
    return problems


# V0 is the input gate. Keep valid imports available to the other tools, but
# stop before deriving any corpus state from a registry that did not load, or
# that loaded in a shape the rules do not read.
try:
    H = load("harness.yaml")
    CAP = load("capabilities.yaml")
    ROUTES = load("routes.yaml")
    FIX = load("fixtures.yaml")
except RegistryLoadError as error:
    print(f"V0: {error}", file=sys.stderr)
    raise SystemExit(1) from None
_SHAPE_PROBLEMS = [f"coding-registry/{name}: {p}" for name, data in (("harness.yaml", H), ("capabilities.yaml", CAP),
                                        ("routes.yaml", ROUTES))
                   for p in misshapen(data, SHAPES[name], "")]
if not _SHAPE_PROBLEMS:
    _named = H["signature"].get("vocabulary")
    if _named is not None and _named not in H["vocabulary"]:
        _SHAPE_PROBLEMS.append(f"coding-registry/harness.yaml: signature.vocabulary must "
                               f"name a vocabulary list, not {_named!r}")
if _SHAPE_PROBLEMS:
    for problem in _SHAPE_PROBLEMS:
        print(f"V0: {problem}", file=sys.stderr)
    raise SystemExit(1)

LIM = H["limits"]
VOCAB = H["vocabulary"]
PREFIX = H["prefix"]
SET = H["set"]
SHARED = H["shared_dir"]
CONTRACT_FILE = f"{SHARED}/CONTRACT.md"
ROUTING_FILE = f"{SHARED}/ROUTING.md"
SIGNATURE = H["signature"]
PLATFORM_DIRS = set(H["platform_dirs"])

SKILLS_ROOT = ROOT / H["skills_dir"] if H.get("skills_dir") else ROOT
SKILL_DIRS = sorted(p for p in SKILLS_ROOT.glob(f"{PREFIX}*") if (p / "SKILL.md").exists())
SKILLS = [p.name for p in SKILL_DIRS]
# A backticked token is a path if it contains a slash or names a file. Matching
# only on the slash misses the bare sibling reference (`SIZING.md`), which is
# the form that breaks: it resolves against the skill directory, not against
# the directory the file writing it lives in.
PATH_TOKEN_RE = re.compile(r"[^\s]*(?:/[^\s]*|\.(?:md|yaml|py))")
# A marker in code (`#TODO(agent):`) is a mention of the convention, not a
# marker; V22 reads only what renders outside code (`fences.live_text`).
MARKER_RE = re.compile(r"#" + r"TODO\(agent\):")


def read(p: Path) -> str:
    """A page that cannot be read — a looping or dangling link — is a failure
    to report, not a traceback that hides every other rule's result."""
    try:
        target = p.resolve(strict=True)
        if not target.is_relative_to(ROOT.resolve()):
            fail("V27", f"{p.relative_to(ROOT)} points outside the repo ({target})")
            return ""
        return target.read_text(encoding="utf-8").removeprefix("\ufeff")   # a BOM is not content
    except (OSError, RuntimeError, UnicodeDecodeError) as e:
        fail("V27", f"{p.relative_to(ROOT)} cannot be read: {getattr(e, 'strerror', None) or e}")
        return ""


_FRONTMATTER: dict[str, dict] = {}


def frontmatter(text: str, label: str) -> dict:
    """Parsed as YAML, which is how a CLI reads it. A line-by-line reading saw
    only the first line of a continued description, so length and wording rules
    checked a fragment of what the listing actually carries.

    Parsed once per page, so a broken header is reported once and by name
    rather than by every rule that reads it."""
    if label in _FRONTMATTER:
        return _FRONTMATTER[label]
    out: dict = {}
    # Only unindented `---` lines delimit it; one inside a block scalar does not.
    m = re.match(r"---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", text, re.S)
    if m:
        try:
            got = yaml.load(m.group(1), Loader=UniqueKeyLoader)
        except yaml.YAMLError as e:
            fail("V1", f"{label} frontmatter is not valid YAML: " + str(e).splitlines()[0])
            got = {}
        if not isinstance(got, dict):
            fail("V1", f"{label} frontmatter is not a mapping of keys to values")
            got = {}
        for key, value in got.items():
            if key in ("name", "description", "allowed-tools") and not isinstance(value, str):
                fail("V1", f"{label} frontmatter {key} must be a string")
                value = ""
            out[str(key)] = "" if value is None else value if isinstance(value, str) else str(value)
    else:
        fail("V1", f"{label} has no complete YAML frontmatter at the start of the page")
    _FRONTMATTER[label] = out
    return out


def walk(d: Path):
    """Every entry under d, not descending through a link — `_coding` and
    `registry` are judged as links, not re-walked as directories."""
    try:
        if not d.resolve(strict=True).is_relative_to(ROOT.resolve()):
            fail("V27", f"{d.relative_to(ROOT)} points outside the repo")
            return
        entries = sorted(d.iterdir())
    except (OSError, RuntimeError) as e:
        fail("V27", f"{d.relative_to(ROOT)} cannot be walked: {getattr(e, 'strerror', None) or e}")
        return
    for entry in entries:
        yield entry
        if entry.is_dir() and not entry.is_symlink():
            yield from walk(entry)


def _commonmark_lines(text: str) -> list[str]:
    """Lines as CommonMark counts them: split at \\n, \\r\\n and a bare \\r, but
    not at \\f, \\x85 or \\u2028, where splitlines() also splits."""
    return re.sub(r"\r\n?", "\n", text).removesuffix("\n").split("\n")


def sections(text: str) -> dict[str, str]:
    """Level-2 headings as rendered — one inside code is text, not a section."""
    out, cur, buf = {}, None, []
    lines = _commonmark_lines(text)
    heads = h2_lines(lines)
    for i, line in enumerate(lines):
        title = heads.get(i)
        if title is not None:
            if cur:
                out[cur] = "\n".join(buf)
            cur, buf = title, []
        elif cur:
            buf.append(line)
    if cur:
        out[cur] = "\n".join(buf)
    return out


def section_links(text: str, title: str) -> list[str]:
    """Parse the whole page so a link may use a definition in another section."""
    lines = _commonmark_lines(text)   # numbered as links() numbers them
    heads = list(h2_lines(lines).items())
    targets = []
    for index, (start, name) in enumerate(heads):
        if name == title:
            end = heads[index + 1][0] if index + 1 < len(heads) else len(lines)
            targets.extend(links(text, line_range=(start + 1, end)))
    return targets


def local_link_path(href: str) -> str | None:
    target = urlsplit(href)
    if target.scheme.lower() == "file":
        raise ValueError("file: links are not repository-relative")
    if target.scheme or target.netloc:
        return None
    return unquote(target.path)


def link_paths(base: Path, targets: list[str]) -> set[Path]:
    found = set()
    for href in targets:
        try:
            path = local_link_path(href)
        except ValueError:
            continue  # V8 reports malformed URLs.
        if path:
            found.add(Path(os.path.normpath(base / path)))
    return found


def inline_paths(text: str) -> list[str]:
    return [value for value in code_spans(text) if PATH_TOKEN_RE.fullmatch(value)]


FIXED_SECTIONS = ["Owns", "Before starting", "Decide first",
                  "Always / Never", "Verify with", "Done when"]


# --- rules -------------------------------------------------------------------

def v1_sizes():
    for d in SKILL_DIRS:
        t = read(d / "SKILL.md")
        n = len(t.splitlines())
        if n > LIM["skill_md_lines"]:
            fail("V1", f"{d.name}/SKILL.md is {n} lines (max {LIM['skill_md_lines']})")
        metadata = frontmatter(t, d.name)
        for field in ("name", "description", "allowed-tools"):
            if not metadata.get(field, "").strip():
                fail("V1", f"{d.name} frontmatter is missing a non-empty {field}")
        if metadata.get("name") and metadata["name"] != d.name:
            fail("V1", f"{d.name} frontmatter name is {metadata['name']!r}, not its directory name")
        desc = metadata.get("description", "")
        if len(desc) > LIM["description_chars"]:
            fail("V1", f"{d.name} description is {len(desc)} chars "
                       f"(max {LIM['description_chars']}; the listing truncates)")


def v2_description_terms():
    others = set(SKILLS)
    for d in SKILL_DIRS:
        desc = frontmatter(read(d / "SKILL.md"), d.name).get("description", "")
        for term in H["forbidden_description_terms"]:
            if term.lower() in desc.lower():
                fail("V2", f"{d.name} description contains {term!r}; "
                           "boundaries belong in capabilities.yaml `not:`")
        for name in others - {d.name}:
            if name in desc:
                fail("V2", f"{d.name} description names {name}")


def v3_roster():
    # Every key, prefixed or not: a misspelt one is still read by V9 and V10.
    declared = set(CAP)
    if declared != set(SKILLS):
        fail("V3", f"capabilities.yaml vs disk: only in yaml={sorted(declared - set(SKILLS))} "
                   f"only on disk={sorted(set(SKILLS) - declared)}")


def v4_playbook_orphans():
    for d in SKILL_DIRS:
        pb_dir = d / "playbooks"
        if not pb_dir.exists():
            continue
        linked = link_paths(d, section_links(read(d / "SKILL.md"), "Decide first"))
        for pb in sorted(pb_dir.glob("*.md")):
            if pb not in linked:
                fail("V4", f"{d.name}/playbooks/{pb.name} is not linked from Decide first")
    _flat("V4", "playbooks")


def _flat(rule: str, kind: str) -> None:
    """Pages of a kind sit directly in its directory. The budget, label, link
    and orphan rules read one level, so a page one directory down was checked
    by none of them."""
    for d in SKILL_DIRS:
        for sub in sorted(p for p in (d / kind).glob("*") if p.is_dir()):
            fail(rule, f"{d.name}/{kind}/{sub.name}/ is a directory; {kind} pages sit directly "
                       f"in {kind}/, where the rules read them")


def v5_playbook_budget():
    for d in SKILL_DIRS:
        pbs = sorted((d / "playbooks").glob("*.md")) if (d / "playbooks").exists() else []
        if len(pbs) > LIM["playbooks_per_skill"]:
            fail("V5", f"{d.name} has {len(pbs)} playbooks (max {LIM['playbooks_per_skill']})")
        for pb in pbs:
            n = len(read(pb).splitlines())
            if n > LIM["playbook_lines"]:
                fail("V5", f"{pb.relative_to(ROOT)} is {n} lines (max {LIM['playbook_lines']})")


def v6_budgets():
    # The budgets, labels and path rules read the shared directory one level
    # down, as _flat says of playbooks/; a page in a subdirectory escaped them all.
    for sub in sorted(p for p in (SKILLS_ROOT / SHARED).glob("*") if p.is_dir()):
        fail("V6", f"{SHARED}/{sub.name}/ is a directory; shared pages sit directly "
                   f"in {SHARED}/, where the rules read them")
    total = 0
    for f in sorted((SKILLS_ROOT / SHARED).glob("*.md")):
        n = len(read(f).splitlines())
        total += n
        if n > LIM["shared_file_lines"]:
            fail("V6", f"{SHARED}/{f.name} is {n} lines (max {LIM['shared_file_lines']})")
    if total > LIM["shared_lines_total"]:
        fail("V6", f"{SHARED} totals {total} lines (max {LIM['shared_lines_total']})")
    repo = sum(len(read(f).splitlines()) for f in ROOT.rglob("*.md")
               if ".git" not in f.parts)
    if repo > LIM["repo_md_lines_total"]:
        fail("V6", f"repo markdown totals {repo} lines (max {LIM['repo_md_lines_total']})")


def v7_routes_real():
    for name, r in ROUTES.items():
        for s in r.get("chain", []):
            if s not in SKILLS:
                fail("V7", f"route {name} chains {s}, which does not exist")


def v8_links():
    for f in ROOT.rglob("*.md"):
        if ".git" in f.parts:
            continue
        # A link shown in code is an example, not a link.
        for target in links(read(f)):
            try:
                local = local_link_path(target)
                if not local:
                    continue
                path = f.parent / local
                if Path(local).is_absolute() or not path.resolve().is_relative_to(ROOT.resolve()):
                    fail("V8", f"{f.relative_to(ROOT)} links to {target}, outside the repo")
                elif not path.exists():
                    fail("V8", f"{f.relative_to(ROOT)} links to missing {target}")
            except (OSError, RuntimeError, ValueError) as e:
                fail("V8", f"{f.relative_to(ROOT)} cannot resolve link {target!r}: {e}")


def _norm(s: str) -> str:
    return unicodedata.normalize("NFKC", s).lower()


def v9_signals():
    seen: dict[str, str] = {}
    for name, c in CAP.items():
        sigs = c.get("signals", [])
        if not sigs:
            fail("V9", f"{name} declares no signals")
        for s in sigs:
            k = _norm(s)
            if k in seen:
                fail("V9", f"signal {s!r} claimed by both {seen[k]} and {name}")
            seen[k] = name


def _says(text: str, phrase: str) -> bool:
    """A signal is matched as words, a plural included. As a substring, `diff`
    matched "different" and `where` matched "somewhere", and the fixtures
    passed on noise; as an exact word, `regression test` missed "tests"."""
    return re.search(rf"(?<!\w){re.escape(phrase)}s?(?!\w)", text) is not None


def v10_fixtures():
    pairs = [(_norm(s), name) for name, c in CAP.items() for s in c.get("signals", [])]
    if not isinstance(FIX, list) or not FIX:
        fail("V10", "fixtures.yaml must be a non-empty list of ask/expect mappings")
        return
    for index, entry in enumerate(FIX, 1):
        if not isinstance(entry, dict) or any(
                not isinstance(entry.get(key), str) or not entry[key].strip()
                for key in ("ask", "expect")):
            fail("V10", f"fixture {index} must name non-empty ask and expect strings")
            continue
        ask, expect = _norm(entry["ask"]), entry["expect"]
        hits = [(len(sig), owner) for sig, owner in pairs if _says(ask, sig)]
        if not hits:
            fail("V10", f"no signal matches {entry['ask']!r} (expected {expect})")
            continue
        best = max(h[0] for h in hits)
        winners = {owner for ln, owner in hits if ln == best}
        if winners != {expect}:
            fail("V10", f"{entry['ask']!r} -> {sorted(winners)}, expected {expect}")


def v11_count():
    if len(SKILLS) > LIM["skills_max"]:
        fail("V11", f"{len(SKILLS)} skills (max {LIM['skills_max']}); "
                    "past the cap an addition must retire one")


def v12_prefix():
    for d in SKILLS_ROOT.iterdir():
        if d.is_dir() and (d / "SKILL.md").exists() and not d.name.startswith(PREFIX):
            fail("V12", f"{d.name} does not start with {PREFIX!r}")


def v13_route_budget():
    if len(ROUTES) > LIM["routes_max"]:
        fail("V13", f"{len(ROUTES)} routes (max {LIM['routes_max']})")
    # A budget declared and never read is a number that only looks enforced.
    for name, r in ROUTES.items():
        n = len(r.get("chain", []))
        if n > LIM["route_stages_max"]:
            fail("V13", f"route {name} chains {n} stages (max {LIM['route_stages_max']})")


def v14_patterns():
    for name, r in ROUTES.items():
        p = r.get("pattern")
        if p not in VOCAB["patterns"]:
            fail("V14", f"route {name} uses pattern {p!r}, not in the vocabulary")
        if p == "loop":
            for key in ("oracle", "checker"):
                if not isinstance(r.get(key), str) or not r[key].strip():
                    fail("V14", f"loop route {name} needs a non-empty {key}")
            cycles = r.get("max_cycles")
            if type(cycles) is not int or cycles <= 0:
                fail("V14", f"loop route {name} max_cycles must be a positive integer")
        if p == "report-only" and (not isinstance(r.get("stops_at"), str) or not r["stops_at"].strip()):
            fail("V14", f"report-only route {name} needs a non-empty stops_at")


def v15_permission_class():
    classes = H["permission_classes"]
    for d in SKILL_DIRS:
        declared = CAP.get(d.name, {}).get("class")
        if declared not in classes:
            fail("V15", f"{d.name} declares unknown class {declared!r}")
            continue
        want = classes[declared]["tools"]
        got = frontmatter(read(d / "SKILL.md"), d.name).get("allowed-tools", "")
        if got != want:
            fail("V15", f"{d.name} allowed-tools is {got!r}, class {declared} requires {want!r}")


def v16_sections():
    for d in SKILL_DIRS:
        have = sections(read(d / "SKILL.md"))
        for s in FIXED_SECTIONS:
            if s not in have:
                fail("V16", f"{d.name}/SKILL.md is missing section {s!r}")


def v17_delivery():
    for key, spec in H["delivered"].items():
        want = read(ROOT / "coding-registry" / "delivered" / f"{key}.md").rstrip("\n")
        open_m, close_m = f"<!-- deliver:{key} -->", f"<!-- /deliver:{key} -->"
        owners = set(SIGNATURE["required_of"]) if spec.get("only") == "signature" else set(SKILLS)
        for d in SKILL_DIRS:
            text = read(d / "SKILL.md")
            lines = text.splitlines()
            present = marker_lines(lines, open_m) or marker_lines(lines, close_m)
            if d.name not in owners:
                if present:
                    fail("V17", f"{d.name}/SKILL.md carries the {key} block, which is "
                                f"delivered only to {sorted(owners)} (run: make render)")
                continue
            span = delivered_block(text, key)
            if span is None:
                fail("V17", f"{d.name}/SKILL.md is missing the {key} delivery block, "
                            "or its markers are unpaired")
                continue
            got = "\n".join(lines[span[0] + 1:span[1]]).strip("\n")
            if got != want:
                fail("V17", f"{d.name}/SKILL.md {key} block differs from "
                            f"coding-registry/delivered/{key}.md (run: make render)")
            # Placement is where the marker line sits, not whether the section
            # quotes the marker: a sentence naming it there is not the block.
            heads = sorted(h2_lines(lines).items())
            starts = [i for i, title in heads if title == spec["section"]]
            if not any(start < span[0] < min((i for i, _ in heads if i > start),
                                             default=len(lines))
                       for start in starts):
                fail("V17", f"{d.name}/SKILL.md {key} block is not under {spec['section']!r}")


def v18_signals_in_description():
    for d in SKILL_DIRS:
        desc = _norm(frontmatter(read(d / "SKILL.md"), d.name).get("description", ""))
        for s in CAP.get(d.name, {}).get("signals", []):
            # Whole words, as V10 routes: `refactor` inside "Refactoring" is
            # not the word a request carries.
            if not _says(desc, _norm(s)):
                fail("V18", f"{d.name} signal {s!r} is not literal in its description; "
                            "the listing carries nothing else")


def v19_paths_resolve():
    """Every path a skill can be told to read must resolve from its own directory.

    A skill is handed its own directory as the base, and paths are normalised
    lexically, so `..` never travels back through the install symlink. That
    applies to the shared contracts too — they are read *by* a skill, so a
    sibling-relative path in them points at nothing once installed.
    """
    if not SKILL_DIRS:
        return  # V3 reports the missing roster.
    probe = SKILL_DIRS[0]
    shared = sorted((SKILLS_ROOT / SHARED).glob("*.md"))
    for d in SKILL_DIRS:
        # reference/ is read by the skill exactly as a playbook is, only later.
        readable = [d / "SKILL.md"] + sorted(d.glob("playbooks/*.md")) \
            + sorted(d.glob("reference/*.md"))
        for f in readable:
            _check_paths(f, d, f"{d.name}/{f.relative_to(d)}", f.relative_to(d).parent)
    for f in shared:                      # checked once, against one skill dir
        _check_paths(f, probe, f"{SHARED}/{f.name}", Path(SHARED))


# A backticked path is a reference to this set only if it names a file or sits
# under one of the set's own roots. `node_modules/` in a search playbook is an
# example of the reader's project, not a pointer into this repo.
def _is_own_reference(p: str) -> bool:
    if any(p == x or (x.endswith("/") and p.startswith(x))
           for x in H.get("external_paths", [])):
        return False
    if p.endswith((".md", ".yaml", ".py")):
        return True
    return p.startswith((f"{SHARED}/", "registry/", "playbooks/", "reference/"))


def _check_paths(f: Path, base: Path, label: str, where: Path) -> None:
    """Backticked paths are read from the skill directory; markdown links from
    the file that holds them (`where`, relative to the skill directory). Either
    way the path is normalised lexically, so a link whose `..` climbs out of
    the skill directory points at nothing once installed."""
    for href in links(read(f)):
        try:
            target = local_link_path(href)
        except ValueError:
            continue  # V8 reports malformed URLs.
        if not target or Path(target).is_absolute():
            continue
        norm = os.path.normpath(str(where / target))
        if norm == ".." or norm.startswith("../"):
            fail("V19", f"{label} links to {target!r}, which climbs out of the skill "
                        "directory; paths are normalised lexically")
        elif not (base / norm).exists():
            fail("V19", f"{label} links to {target!r}, which does not resolve from a "
                        "skill directory")
    for p in inline_paths(read(f)):
        if p.startswith(("~", "/")) or re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", p) or not _is_own_reference(p):
            continue
        if ".." in p:
            fail("V19", f"{label} references {p!r}; paths are normalised lexically, "
                        "so `..` does not traverse the install symlink")
        elif not (base / p).exists():
            fail("V19", f"{label} references {p!r}, which does not resolve from a "
                        "skill directory")


# A definition, as against a mention: a table row or a heading that opens with
# the word. `patterns` and `checkers` are route vocabulary and live in
# routes.yaml, so no page is asked to define them.
DEFINITION_FORMS = (("row", "{w}"), ("row", "[{w}]"), ("heading", "{w}"))
ROUTE_VOCAB = {"patterns", "checkers"}


def v20_contract_vocabulary():
    """Every declared word is defined on a shared page, not merely named there.

    The earlier form asked whether the word appeared anywhere in CONTRACT.md,
    and a word used in a sentence passed as defined — so a definition that was
    replaced by a mere mention did not trip it. A definition is a row or a
    heading, and every vocabulary key is held to it, not three. Both are read
    as rendered: the same characters inside a sentence, a later cell, a code
    block or a comment are a mention of the form, not the form.
    """
    defined = set()
    for p in (SKILLS_ROOT / SHARED).glob("*.md"):
        defined |= leading_code(read(p))
    for key, words in VOCAB.items():
        if key in ROUTE_VOCAB:
            continue
        for word in words:
            forms = {(kind, code.format(w=word)) for kind, code in DEFINITION_FORMS}
            if not forms & defined:
                fail("V20", f"no page under {SHARED}/ defines {word!r} ({key}) — "
                            "a table row or a heading, not a mention")


def delivered_block(text: str, key: str) -> tuple[int, int] | None:
    """Line indices of a delivered block's two markers — whole lines outside any
    fence, exactly one of each, in order — or None."""
    lines = text.splitlines()
    opens = marker_lines(lines, f"<!-- deliver:{key} -->")
    closes = marker_lines(lines, f"<!-- /deliver:{key} -->")
    if len(opens) == len(closes) == 1 and opens[0] < closes[0]:
        return opens[0], closes[0]
    return None


def strip_delivered(text: str) -> str:
    for key in H["delivered"]:
        span = delivered_block(text, key)
        if span:
            lines = text.splitlines()
            text = "\n".join(lines[:span[0]] + lines[span[1] + 1:])
    return text


def shows(text: str, word: str, *, whole_word: bool = False) -> bool:
    """Whether a reader sees `word` — in rendered prose or in code — rather than
    only in a comment, an attribute or a script. With `whole_word`, `executed`
    is not found inside `unexecuted`."""
    pattern = (rf"(?<![\w-]){re.escape(word)}(?![\w-])" if whole_word
               else re.escape(word))
    return any(re.search(pattern, fragment)
               for fragment in (*live_text(text).values(),
                                *code_spans(text, include_html=True)))


def v21_verify_names_a_grade():
    for d in SKILL_DIRS:
        body = strip_delivered(sections(read(d / "SKILL.md")).get("Verify with", ""))
        if not any(shows(body, g, whole_word=True) for g in VOCAB["evidence_levels"]):
            fail("V21", f"{d.name} Verify with names no evidence grade of its own; "
                        "the delivered block does not count")


def v22_markers_classified():
    for f in ROOT.rglob("*.md"):
        if ".git" in f.parts or f.parts[-2:-1] == ("delivered",):
            continue
        for i in unclassified_markers(read(f)):
            fail("V22", f"{f.relative_to(ROOT)}:{i + 1} marker carries no residual class")


def unclassified_markers(text: str) -> list[int]:
    """Lines whose rendered marker has no residual class. The class may sit in
    code on the line (`UNVERIFIED`) or be spelled with references in HTML, so
    rendered prose and code are checked separately. Hidden comments and
    attributes cannot supply a class that no reader sees."""
    classes = [re.compile(rf"(?<![\w-]){re.escape(word)}(?![\w-])")
               for word in VOCAB["residual_classes"]]
    missing = []
    for line, rendered in sorted(live_text(text).items()):
        if not MARKER_RE.search(rendered):
            continue
        visible = [rendered, *code_spans(text, line_range=(line, line + 1), include_html=True)]
        if not any(pattern.search(fragment) for pattern in classes for fragment in visible):
            missing.append(line)
    return missing


def v23_labels():
    import fnmatch
    for pat, label in H["label_by_path"].items():
        if label not in H["document_labels"]:
            fail("V23", f"label_by_path[{pat!r}] is {label!r}, not one of "
                        f"{H['document_labels']}")
    for f in sorted(ROOT.rglob("*.md")):
        if ".git" in f.parts:
            continue
        rel = str(f.relative_to(ROOT))
        want = None
        for pat, label in H["label_by_path"].items():
            if fnmatch.fnmatch(rel, pat):
                want = label
                break
        if want is None:
            continue
        lines = read(f).splitlines()
        if lines and lines[0].rstrip() == "---":         # skip frontmatter
            end = next((i for i, l in enumerate(lines[1:], 1) if l.rstrip() == "---"), 0)
            lines = lines[end + 1:]
        first = next((l for l in lines if l.strip()), "")
        if first.strip() != f"<!-- {SET}:{want} -->":
            fail("V23", f"{rel} label is {first.strip()!r}, expected {SET}:{want}")


OWN_DIRS = {Path(__file__).resolve().parent.name, "coding-registry"}


def v24_rendered_tables():
    routing = read(SKILLS_ROOT / ROUTING_FILE)
    readme = read(ROOT / "README.md")
    # Listed is a row whose first cell is the name: a skill dropped from the
    # table and still mentioned in prose is not listed. README links its rows.
    routing_rows = leading_code(routing)
    readme_rows = leading_code(readme, linked=True)
    for name in SKILLS:
        if ("row", name) not in routing_rows:
            fail("V24", f"{ROUTING_FILE} does not list {name}")
        if ("row", name) not in readme_rows:
            fail("V24", f"README.md does not list {name}")
    for doc, text in ((SKILLS_ROOT / ROUTING_FILE, routing), (ROOT / "README.md", readme)):
        for found in set(re.findall(rf"`({PREFIX}[a-z][a-z-]*)`", text)):
            # The set's own tools and registry carry the prefix as V28 requires
            # and are no skill. Only they: a retired skill's directory left on
            # disk is still a name that does not exist.
            if found not in SKILLS and found not in OWN_DIRS:
                fail("V24", f"{doc.relative_to(ROOT)} names {found}, which does not exist")


def v25_playbook_rot():
    pats = [re.compile(p) for p in H["rot_patterns"]]
    for d in SKILL_DIRS:
        for pb in sorted((d / "playbooks").glob("*.md")) if (d / "playbooks").exists() else []:
            for i, line in enumerate(read(pb).splitlines(), 1):
                for p in pats:
                    if p.search(line):
                        fail("V25", f"{pb.relative_to(ROOT)}:{i} pins a version or date; "
                                    "content that goes stale belongs outside the budget")


def v26_boundaries_real():
    for name, c in CAP.items():
        for entry in c.get("not", []):
            go = entry.get("go", "")
            if go.startswith(PREFIX) and go not in SKILLS:
                fail("V26", f"{name} `not:` sends work to {go}, which does not exist")


def v27_symlinks_stay_inside():
    """What a skill reaches must live in this repo, and must actually be there."""
    # Every link at any depth, in each skill and in the shared directory.
    for d in SKILL_DIRS + [SKILLS_ROOT / SHARED]:
        for entry in walk(d):
            if not entry.is_symlink():
                continue
            label = entry.relative_to(SKILLS_ROOT)
            try:
                target = (entry.parent / entry.readlink()).resolve()
            except (OSError, RuntimeError):
                fail("V27", f"{label} is a symlink loop")
                continue
            if not target.exists():
                fail("V27", f"{label} is a broken symlink")
            elif ROOT.resolve() not in target.parents and target != ROOT.resolve():
                fail("V27", f"{label} points outside the repo ({target})")


def v28_namespace_agrees():
    """One declaration, and every namespaced name derived from it.

    A skills directory is flat and shared with every other set on the machine,
    so the names that travel there carry the set and the names that do not
    travel stay inside a skill directory.
    """
    if PREFIX != f"{SET}-":
        fail("V28", f"prefix is {PREFIX!r}; set {SET!r} requires {SET + '-'!r}")
    if SHARED != f"_{SET}":
        fail("V28", f"shared_dir is {SHARED!r}; set {SET!r} requires {'_' + SET!r}")
    if not (SKILLS_ROOT / SHARED).is_dir():
        fail("V28", f"{SHARED}/ does not exist")
    # Every directory this set owns carries the set name. The alternative rule —
    # "prefix only what gets installed" — needs a judgement about what travels,
    # and a sibling set's install line (`cp -R coding-* _common <skills dir>`)
    # is what that judgement looks like when it is wrong.
    for d in sorted(list(ROOT.iterdir()) + list(SKILLS_ROOT.iterdir() if SKILLS_ROOT != ROOT else [])):
        if not d.is_dir() or d.name in PLATFORM_DIRS:
            continue
        if not (d.name.startswith(PREFIX) or d.name == SHARED):
            fail("V28", f"{d.name}/ carries no set name; a directory this set owns "
                        f"is {PREFIX}* or {SHARED}, so that copying it into a shared "
                        "skills directory cannot collide")


def v29_reference_headers():
    """reference/ carries no line budget, so it carries headers instead.

    A file with no stated purpose and no date of last check is indistinguishable
    from one that is still true, which is how a deferred layer rots quietly.
    """
    want = H["reference_headers"]
    for d in SKILL_DIRS:
        for f in sorted((d / "reference").glob("*.md")) if (d / "reference").exists() else []:
            # A header opens its line: V31 and V37 read it there and leave a
            # missing one to this rule, so `**Verified:**` is missing to all three.
            head = read(f).splitlines()[:12]
            for header in want:
                if not any(l.startswith(header) for l in head):
                    fail("V29", f"{f.relative_to(ROOT)} has no {header!r} in its first "
                                "12 lines; the deferred layer states what it claims "
                                "and when anyone last checked")


def v30_reference_orphans():
    """A reference nothing points at is never read and never noticed as stale."""
    _flat("V30", "reference")
    for d in SKILL_DIRS:
        ref_dir = d / "reference"
        if not ref_dir.exists():
            continue
        linked = link_paths(d, section_links(read(d / "SKILL.md"), "Decide first"))
        for pb in sorted((d / "playbooks").glob("*.md")) if (d / "playbooks").exists() else []:
            text = read(pb)
            linked |= link_paths(pb.parent, links(text))
            linked |= {Path(os.path.normpath(d / p)) for p in inline_paths(text)}
        for f in sorted(ref_dir.glob("*.md")):
            if f not in linked:
                fail("V30", f"{f.relative_to(ROOT)} is reachable from nothing — "
                            "not the Decide first table, not a playbook")


def v31_verified_names_a_check():
    """A `Verified:` date cannot fail, so the line has to say what can.

    Either it names what re-checks the page, or it says that nothing does. Both
    are acceptable; what is not is a bare date, which reads exactly like a
    checked page and is indistinguishable from one that has rotted.
    """
    markers = H.get("verified_markers")
    if not markers:
        fail("V31", "harness.yaml declares no verified_markers; this rule is checking nothing")
        return
    for d in SKILL_DIRS:
        for f in sorted((d / "reference").glob("*.md")) if (d / "reference").exists() else []:
            lines = read(f).splitlines()
            start = next((i for i, l in enumerate(lines) if l.startswith("Verified:")), None)
            if start is None:
                continue                      # V29 already reports the missing header
            # To the next header, as V37 reads `Source:`: a `Source:` line that
            # follows directly is not what re-checks this page's date.
            block = [lines[start]]
            for l in lines[start + 1:]:
                if not l.strip() or any(l.startswith(h) for h in H["reference_headers"]):
                    break
                block.append(l)
            text = " ".join(block)
            if not any(m in text for m in markers):
                fail("V31", f"{f.relative_to(ROOT)} states a `Verified:` date and nothing "
                            "else; name what re-checks it, or say `no automated check`")

def v32_checker_engine():
    """A loop route's checker is resolved against the engine that is running.

    `checker: external` checked nothing. Naming an engine instead was no better:
    all three CLIs read this SKILL.md, so a checker pinned to `codex` is the
    maker marking its own work on any run that is codex. What can be checked
    here is that the set names more than one engine — otherwise no run has an
    independent one to reach for — and that the route defers the choice.
    """
    eng = H.get("engines") or {}
    runs_on = eng.get("runs_on") if isinstance(eng, dict) else None
    if not isinstance(runs_on, list) or any(not isinstance(name, str) or not name.strip() for name in runs_on):
        fail("V32", "engines.runs_on must be a list of non-empty engine names")
        runs_on = []
    if len(set(runs_on)) != len(runs_on):
        fail("V32", "engines.runs_on repeats an engine; duplicate entries are not independent checkers")
    if len(set(runs_on)) < 2:
        fail("V32", f"engines.runs_on is {runs_on}; with fewer than two engines no "
                    "run can be checked by one that did not produce the work")
    allowed = VOCAB.get("checkers") or []
    if not allowed:
        fail("V32", "harness.yaml declares no checker vocabulary; "
                    "this rule is checking nothing")
        return
    for name, r in ROUTES.items():
        if r.get("pattern") != "loop":
            continue
        c = r.get("checker")
        if c in runs_on:
            fail("V32", f"loop route {name} pins its checker to {c!r}; on a run that "
                        f"is {c!r} that is the maker marking its own work")
        elif c not in allowed:
            fail("V32", f"loop route {name} checks with {c!r}, not in {allowed}")


def v33_refutation_lens():
    """The set says what a refuting engine should attack, and what breaks a claim.

    `refute.py` is identical in every set; the lens is what makes it adversarial
    rather than a second opinion, and it is the one part that cannot be shared.
    A set holding the tool and no framing would ask two engines to review — which
    is the thing an adversarial pass exists to not be.
    """
    r = H.get("refutation") or {}
    for key in ("lens", "refuted_when"):
        if not isinstance(r.get(key), str) or not r[key].strip():
            fail("V33", f"harness.yaml declares no refutation {key} as text; "
                        f"{SET}-tools/refute.py has nothing domain-specific to ask with")


def v34_tools_reachable():
    """Every declared tool is reachable from a skill exactly where it is runnable.

    Linked into a skill whose class withholds `Bash`, a tool is decoration that
    reads like a capability. Missing from one that holds `Bash`, the skill has to
    shell out to a path outside its own directory, which does not resolve. Tying
    the link to the grant makes the absence checked rather than accidental — a set
    where no skill can run one says so out loud.

    The list is `linked_tools` in harness.yaml, so adding a tool costs one line
    and is checked the same way as the ones already there. The tools directory is
    never linked whole: a skill holding `Bash` and all of it could edit the
    harness it is part of, `render.py` included.
    """
    declared_tools = H.get("linked_tools") or {}
    if not declared_tools:
        fail("V34", "harness.yaml declares no linked_tools; this rule is "
                    "checking nothing")
        return
    for tool, who in declared_tools.items():
        source = ROOT / f"{SET}-tools" / tool
        if not source.exists():
            fail("V34", f"linked_tools names {tool}, which is not in {SET}-tools/")
            continue
        wanted = set(SKILLS) if who == "all" else set(who)
        unknown = wanted - set(SKILLS)
        if unknown:
            fail("V34", f"linked_tools[{tool}] names {sorted(unknown)}, "
                        "which are not skills")
        for d in SKILL_DIRS:
            cls = CAP.get(d.name, {}).get("class")
            has_shell = "Bash" in H["permission_classes"].get(cls, {}).get("tools", "")
            link = d / tool
            should = d.name in wanted and has_shell
            if should and not link.is_symlink():
                fail("V34", f"{d.name} may run {SET}-tools/{tool} but cannot reach "
                            f"it; link it as {tool}")
            if not should and link.is_symlink():
                why = ("its class grants no Bash" if d.name in wanted
                       else f"linked_tools[{tool}] does not name it")
                fail("V34", f"{d.name} links {tool} and {why}")
            if link.is_symlink():
                try:
                    target = link.resolve(strict=True)
                    if target != source.resolve():
                        fail("V34", f"{d.name}/{tool} points at {target}, not the set's own")
                except (OSError, RuntimeError):
                    continue  # V27 reports a broken or looping link.
    tools_dir = (ROOT / f"{SET}-tools").resolve()
    for d in SKILL_DIRS:
        for entry in walk(d):
            label = entry.relative_to(SKILLS_ROOT)
            # Judged by where it points, not by its name, and at any depth:
            # `tools -> coding-tools`, `render -> render.py`, or a link to the
            # repo root reaches the harness as surely as a `.py` does.
            try:
                target = entry.resolve(strict=True) if entry.is_symlink() else None
            except (OSError, RuntimeError):
                continue                      # V27 reports a broken or looping link
            if target is not None and (target == tools_dir or target in tools_dir.parents):
                fail("V34", f"{label} reaches the whole {SET}-tools/; "
                            "tools are linked one by one")
            elif target is not None and tools_dir in target.parents:
                declared_here = entry.parent == d and entry.name in declared_tools
                if not declared_here or target.name != entry.name:
                    fail("V34", f"{label} links {SET}-tools/{target.name}, which "
                                "linked_tools does not declare there under that name")
            elif entry.parent == d and entry.suffix == ".py" and entry.name not in declared_tools:
                fail("V34", f"{label} is a tool link nothing "
                            "declares; add it to linked_tools or remove it")


def v35_signature():
    """The mechanism this set has and its siblings do not, checked the same way.

    Each set declares one signature mechanism in `signature:` — the contract
    that carries it, the vocabulary it introduces, and the skills that owe it.
    The rule is identical in every set; only the declaration differs, which is
    what keeps six copies of this file from becoming six dialects.

    The delivered block states the rule inside every skill. A skill that owes
    the mechanism also names its own half of it, because a rule stated
    everywhere and owned nowhere is a ritual.
    """
    contract = f"{SHARED}/{SIGNATURE['contract']}"
    path = SKILLS_ROOT / contract
    if not path.exists():
        fail("V35", f"signature names {contract}, which does not exist")
        return
    text = read(path)
    for word in VOCAB[SIGNATURE["vocabulary"]]:
        if f"`{word}`" not in text:
            fail("V35", f"{contract} never defines {word!r}, which "
                        f"{SIGNATURE['vocabulary']} declares")
    for name in SIGNATURE["required_of"]:
        if name not in SKILLS:
            fail("V35", f"signature.required_of names {name!r}, which is not a skill")
            continue
        body = strip_delivered(read(SKILLS_ROOT / name / "SKILL.md"))
        if not shows(body, SIGNATURE["own_word"]):
            fail("V35", f"{name} owes the {SIGNATURE['name']} mechanism and never names "
                        f"it in its own words; the delivered block does not count")


def v36_finding_visuals():
    """A finding a reader has to reassemble gets a picture, and the picture is
    held to the same standard as the words.

    `finding_visuals` in harness.yaml names the triggers, the forms and the
    floor; this checks the review skill actually defines each of them, and that
    its `Decide first` table reaches the playbook — a rule stated in a file
    nothing links to is read on no launches at all.

    A set with no review skill declares `required_of: []` and says why. The
    absence is then a decision on the record rather than something a later
    reader has to notice.
    """
    fv = H.get("finding_visuals")
    if not fv:
        fail("V36", "harness.yaml declares no finding_visuals; this rule is "
                    "checking nothing")
        return
    required = fv.get("required_of")
    if required is None:
        fail("V36", "finding_visuals declares no required_of")
        return
    if not required:
        if not (fv.get("why") or "").strip():
            fail("V36", "finding_visuals.required_of is empty and says nothing "
                        "about why no skill in this set owes a diagram")
        return
    if not (fv.get("playbook") and fv.get("contract")):
        fail("V36", "finding_visuals names no playbook or contract; "
                    f"{required} owe files the rule cannot find")
        return
    words = list(fv.get("triggers") or []) + list(fv.get("floor") or [])
    if not words or not fv.get("forms"):
        fail("V36", "finding_visuals declares no triggers, floor or forms; "
                    "the rule would check that a file exists and nothing else")
        return
    for name in required:
        if name not in SKILLS:
            fail("V36", f"finding_visuals.required_of names {name!r}, "
                        "which is not a skill")
            continue
        pb = SKILLS_ROOT / name / "playbooks" / fv["playbook"]
        ref = SKILLS_ROOT / name / "reference" / fv["contract"]
        for f in (pb, ref):
            if not f.exists():
                fail("V36", f"{name} owes {f.relative_to(SKILLS_ROOT)}, "
                            "which does not exist")
        if not (pb.exists() and ref.exists()):
            continue
        text = read(pb) + read(ref)
        for word in words:
            if f"`{word}`" not in text:
                fail("V36", f"{name} never defines {word!r}, which "
                            "finding_visuals declares")
        for form in fv["forms"]:
            if _norm(form) not in _norm(text):
                fail("V36", f"{name} never names the {form!r} form")
        linked = link_paths(SKILLS_ROOT / name,
                            section_links(read(SKILLS_ROOT / name / "SKILL.md"), "Decide first"))
        if pb not in linked:
            fail("V36", f"{name}/SKILL.md does not reach {fv['playbook']} from "
                        "Decide first; a rule nothing links to is read on no launches")


def v37_source_pins_the_rot():
    """`Verified:` is when someone looked. `Source:` is what they looked at.

    V31 makes the line name what re-checks it, and across the family 94 of 114
    reference pages answer `no automated check`. That one admission covers two
    populations: pages bound to something outside themselves, and the templates
    and catalogues that depend on nothing and cannot go stale. Only the first
    can rot, and nothing in the header said which page was which.

    So the header names it and the check is an equality — every authority the
    registry declares and the body leans on is named in `Source:`, and nothing
    is named there the body does not use. Where the registry pins a version,
    that version has to appear in the page too: a page edited to a newer one
    then fails instead of quietly disagreeing with its own header.

    Nothing here reads a date or leaves the machine. Freshness is time- and
    environment-dependent and does not belong in CI; agreement between a header
    and its own body is neither.

    Matching is on word boundaries, not substrings. Plain `in` reported that a
    page on test oracles depended on git, having found it inside "legitimate".
    """
    def names(text: str, name: str) -> bool:
        return re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", text) is not None

    def pinned(text: str, pin: str) -> bool:
        """A version ends where no digit, letter or `.<more>` continues it:
        `git 2.4` is none of `git 2.45`, `git 2.4.1`, `git 2.4.*` or
        `git 2.4+local`, and ends a sentence. A bare `2.4+` names the pin as a
        floor, and is the pin."""
        return re.search(rf"(?<![\w-]){re.escape(pin)}(?![\w-]|\.[\w*]|\+\w)", text) is not None

    declared = H.get("source_authorities")
    none_marker = H.get("source_none_marker")
    if declared is None or not none_marker:
        fail("V37", "harness.yaml declares no source_authorities/source_none_marker; "
                    "this rule is checking nothing. A set whose reference layer "
                    "depends on nothing outside itself declares the map empty — "
                    "silence and emptiness have to look different")
        return
    for d in SKILL_DIRS:
        for f in sorted((d / "reference").glob("*.md")) if (d / "reference").exists() else []:
            lines = read(f).splitlines()
            start = next((i for i, l in enumerate(lines) if l.startswith("Source:")), None)
            if start is None:
                continue                      # V29 already reports the missing header
            # The block ends at the next header, not at the next blank line.
            # `Source:` and `Verified:` sit on adjacent lines, and a run-to-blank
            # reading swallowed the evidence line into the header — where it named
            # the very tool the mutation had just removed, and the rule stayed
            # quiet about a page that no longer declared what it runs on.
            end = start
            while (end + 1 < len(lines) and lines[end + 1].strip()
                   and not any(lines[end + 1].startswith(h) for h in H["reference_headers"])):
                end += 1
            head = " ".join(lines[start:end + 1])
            body = "\n".join(lines[:start] + lines[end + 1:])
            named = [a for a in declared if names(head, a)]
            if not named and not names(head, none_marker):
                fail("V37", f"{f.relative_to(ROOT)} names no source and does not say "
                            f"{none_marker!r}; a page that depends on nothing says so, "
                            "because silence reads the same from a page that rots")
            for name, version in declared.items():
                if names(body, name) and not names(head, name):
                    fail("V37", f"{f.relative_to(ROOT)} leans on {name} and its `Source:` "
                                "does not name it; the header is where the rot is declared")
                if names(head, name) and not names(body, name):
                    fail("V37", f"{f.relative_to(ROOT)} names {name} in `Source:` and never "
                                "uses it; a source the page does not depend on pins nothing")
                if version and names(head, name):
                    pin = f"{name} {version}"
                    if not pinned(head, pin):
                        fail("V37", f"{f.relative_to(ROOT)} names {name} in `Source:` without "
                                    f"the pinned version; the registry pins {version}, and a "
                                    "source without one cannot be compared with anything later")
                    elif not pinned(body, pin):
                        fail("V37", f"{f.relative_to(ROOT)} pins {pin} and the page never says "
                                    f"{pin}; one of the two moved without the other")


# `KEY: A | B | C` in a schema, or a bare `A | B | C` on a line of its own —
# upper-case words joined by pipes. Underscored and parenthesised forms are not
# matched, so this is a floor.
# A value may follow a colon or a `#` (a schema comment), or open a line (after
# indentation, a quote or a list bullet); it may end the line or be followed by
# punctuation, but not by another word. One opened by a backtick is not read:
# in code, `ENV | sort` is a pipe. A value may carry digits (`T0`). Lower-case
# values are matched too, then reported as undeclared: one lower-case value used
# to hide the whole line from the rule.
_ENUM_T = r"[A-Za-z][A-Za-z0-9-]*(?: [A-Za-z][A-Za-z0-9-]*)*"
ENUM_RE = re.compile(rf"(?:^[\s>*+-]*|[:#]\s*)({_ENUM_T}(?:\s*\|\s*{_ENUM_T})+)"
                     r"(?=\s*(?:[^\w\s|]|$))")


def _is_enumeration(words: list[str]) -> bool:
    """At least one all-caps value; otherwise `a | b` in prose would count."""
    return any(re.fullmatch(r"[A-Z][A-Z0-9-]*(?: [A-Z][A-Z0-9-]*)*", w) for w in words)


def v38_enumerations_declared():
    """A value set a page switches on is declared vocabulary, or nothing checks it.

    `SEVERITY: CRITICAL | HIGH | MEDIUM | LOW | NIT` in a handoff schema is a
    vocabulary — the receiver branches on it — and a set that writes it only
    on the page has no rule reaching it, so `low` in a playbook fails nowhere.
    Declared words are what V20 and V22 reach; the rest is what drifts.
    """
    declared = {w for words in VOCAB.values() for w in words}
    for f in sorted(SKILLS_ROOT.rglob("*.md")):
        if ".git" in f.parts:
            continue
        for i, line in enumerate(read(f).splitlines(), 1):
            # Every set on the line: a second one after the first is read too.
            for m in ENUM_RE.finditer(line):
                words = [w.strip() for w in m.group(1).split("|")]
                if not _is_enumeration(words):
                    continue
                missing = [w for w in words if w not in declared]
                if missing:
                    fail("V38", f"{f.relative_to(ROOT)}:{i} switches on {', '.join(missing)}, "
                                "which harness.yaml vocabulary does not declare")


RULES = [v1_sizes, v2_description_terms, v3_roster, v4_playbook_orphans,
         v5_playbook_budget, v6_budgets, v7_routes_real, v8_links, v9_signals,
         v10_fixtures, v11_count, v12_prefix, v13_route_budget, v14_patterns,
         v15_permission_class, v16_sections, v17_delivery,
         v18_signals_in_description, v19_paths_resolve, v20_contract_vocabulary,
         v21_verify_names_a_grade, v22_markers_classified, v23_labels,
         v24_rendered_tables, v25_playbook_rot, v26_boundaries_real,
         v27_symlinks_stay_inside, v28_namespace_agrees,
         v29_reference_headers, v30_reference_orphans, v31_verified_names_a_check,
         v32_checker_engine,
         v33_refutation_lens,
         v34_tools_reachable,
         v35_signature,
         v36_finding_visuals,
         v37_source_pins_the_rot,
         v38_enumerations_declared]


def _earlier_hook(installed: Path) -> bool:
    """A copy of a version of this repo's hook that history has since changed —
    on any branch: one installed from a newer branch is still this repo's."""
    import subprocess
    if installed.is_symlink() or not installed.is_file():
        return False
    try:
        blob = subprocess.run(["git", "hash-object", str(installed)], cwd=ROOT,
                              capture_output=True, text=True).stdout.strip()
        log = subprocess.run(["git", "log", "--all", "--root", "--format=", "--raw", "--no-abbrev", "--",
                              "coding-tools/githooks/pre-commit"],
                             cwd=ROOT, capture_output=True, text=True).stdout
    except OSError:
        return False
    return bool(blob) and blob in {line.split()[3] for line in log.splitlines()
                                   if len(line.split()) > 3}


CRASHED = "the rule could not run"   # test_validate.py: a crash is not a rule firing


def main() -> int:
    for rule in RULES:
        try:
            rule()
        except Exception as e:   # one rule's crash must not hide the others' findings
            import traceback
            frames = traceback.extract_tb(e.__traceback__)
            here = Path(__file__).resolve()
            frame = next((f for f in reversed(frames) if Path(f.filename).resolve() == here),
                         frames[-1])   # the rule's own line, not the library it called
            fail(rule.__name__.split("_")[0].upper(),
                 f"{CRASHED}: {type(e).__name__}: {e} "
                 f"({Path(frame.filename).name}:{frame.lineno})")
    import subprocess
    try:
        got = subprocess.run(["git", "rev-parse", "--git-path", "hooks/pre-commit"],
                             cwd=ROOT, capture_output=True, text=True)
    except OSError:                       # no git: the rules need none
        got = None
    if got is None or got.returncode != 0:
        hooks = ""                        # not a repository: the hook's own checkout
    else:
        installed = ROOT / got.stdout.strip()
        ours = (ROOT / "coding-tools" / "githooks" / "pre-commit").read_bytes()
        state = ("off — run: make hooks" if not installed.exists() else "on"
                 if installed.read_bytes() == ours else "stale — run: make hooks"
                 if _earlier_hook(installed) else "foreign — not this repo's pre-commit")
        hooks = f" · hooks {state}"
    print(f"{len(RULES)} rules · {len(SKILLS)} skills{hooks}")
    if FAILURES:
        for f in sorted(FAILURES):
            print(f"  {f}")
        print(f"\n{len(FAILURES)} failure(s)")
        return 1
    print("green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
