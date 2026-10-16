#!/usr/bin/env python3
"""Run a checker on an engine that did not produce the work.

`routes.yaml` defers every loop route's `checker` to run time, because all three
CLIs read the same SKILL.md and any of them may be the one running. This resolves
it: given the engine that is running, it picks one that is not.

    make engines                     every declared engine answers, or says why
    python3 coding-tools/engine.py --running claude --prompt-file p.txt --schema s.json

**The running engine is stated, never sniffed.** codex launched from inside
Claude Code inherits `CLAUDECODE` and `CLAUDE_CODE_*`, so a nested run reads as
its parent and any env heuristic silently mis-identifies it — which would hand
back a verdict from the very engine that was supposed to be excluded. `--running`
is required, and absent it this stops.

**A checker that did not run is not a checker that passed.** Every failure path
here raises. Nothing returns a default verdict, nothing degrades to "assume
fine": an engine missing from PATH, an engine that starts and produces no
parseable object, a response that does not match the schema — each is an error
with the engine's own words attached, because the alternative is a green run
that verified nothing.

Engine quirks, re-checked by `make engines` rather than dated:

* `codex exec` rejects a schema without `additionalProperties: false`, at every
  level. Schemas are normalised here so callers write ordinary JSON Schema.
* `agy --print` returns an envelope; the validated object is `structured_output`.
* `claude -p --json-schema` validates the object and returns it in the envelope's
  `structured_output`; `result` carries the same object as a string.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import subprocess
import sys
import tempfile

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
H = yaml.safe_load((ROOT / "coding-registry" / "harness.yaml").read_text(encoding="utf-8"))
ENGINES = H.get("engines") or {}
TIMEOUT = 600


class EngineError(RuntimeError):
    """The engine did not answer. Never a verdict."""


class Unchecked(EngineError):
    """The schema asks for a check this runner cannot make. Unlike a mismatch,
    it is never absorbed by `not`, `anyOf` or `oneOf`: a check that could not
    run is not a check that failed, and treating it as one inverts the answer."""


def _types(schema: dict) -> list:
    t = schema.get("type")
    return t if isinstance(t, list) else [t]


# Keywords whose values are schemas, by shape. Everything else is a literal —
# a `const`, an `enum`, a `default` — and is copied, never rewritten.
_SUBSCHEMA = {"items", "not", "additionalProperties", "if", "then", "else", "contains"}
_SUBSCHEMA_LIST = {"anyOf", "oneOf", "allOf", "prefixItems"}
_SUBSCHEMA_MAP = {"properties", "$defs", "definitions", "patternProperties"}


def strict(schema):
    """Every object closed, which is what codex requires and agy tolerates.

    Recurses through the keywords that hold schemas and nothing else, so a
    literal that happens to look like a schema is left as written. A map — an
    object whose `additionalProperties` is a schema or `true` — cannot be closed
    without changing what it accepts, so it stops rather than being narrowed.
    """
    if not isinstance(schema, dict):
        return schema
    out = {}
    for k, v in schema.items():
        if k in _SUBSCHEMA:
            out[k] = strict(v)
        elif k in _SUBSCHEMA_LIST and isinstance(v, list):
            out[k] = [strict(s) for s in v]
        elif k in _SUBSCHEMA_MAP and isinstance(v, dict):
            out[k] = {name: strict(s) for name, s in v.items()}
        else:
            out[k] = v
    if "object" in _types(out):
        extra = schema.get("additionalProperties", False)
        if extra is not False:
            raise EngineError("an object open to further keys (additionalProperties "
                              f"{extra!r}) cannot be closed; codex rejects it open")
        out["additionalProperties"] = False
        out.setdefault("properties", {})
    return out


_CHECKED = {"type", "properties", "required", "items", "additionalProperties",
            "anyOf", "oneOf", "allOf", "not", "enum", "const"}
_ANNOTATIONS = {"title", "description", "default", "examples", "$schema", "$id",
                "$comment", "$defs", "definitions", "deprecated", "readOnly", "writeOnly"}

_JSON_TYPES = {"string": str, "boolean": bool, "object": dict, "array": list,
               "null": type(None)}


def _same(a, b) -> bool:
    """JSON equality: Python's `True == 1` would let a boolean pass for a number."""
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_same(a[k], b[k]) for k in a)
    return a == b


def _finite_number(raw: str) -> float:
    value = float(raw)
    if not math.isfinite(value):
        raise EngineError(f"non-finite JSON number {raw!r} is not an answer")
    return value


def _integer(raw: str) -> int:
    try:
        return int(raw)
    except ValueError:    # Python refuses to convert more than 4300 digits
        raise EngineError(f"a {len(raw)}-digit integer is too long to read as an answer") from None


def _loads(text: str):
    """json.loads with the answer rules: finite numbers, readable integers, and
    a nesting too deep to read reported as such rather than as a traceback."""
    try:
        return json.loads(text, parse_float=_finite_number, parse_constant=_finite_number,
                          parse_int=_integer)
    except RecursionError:
        raise EngineError("the output nests too deeply to read") from None


def _check_finite(obj) -> None:
    """Non-JSON numbers are invalid even under an unconstrained subschema."""
    if isinstance(obj, float) and not math.isfinite(obj):
        raise EngineError(f"non-finite JSON number {obj!r} is not an answer")
    if isinstance(obj, dict):
        for value in obj.values():
            _check_finite(value)
    elif isinstance(obj, list):
        for value in obj:
            _check_finite(value)


def _check_schema(schema, where: str = "schema") -> None:
    """Reject malformed or unsupported checks before any answer is evaluated.

    A malformed subschema is not a failed match: absorbing it under `not` or
    `anyOf` could approve an answer without applying the requested check. Walk
    even inactive branches here, before starting a paid checker process.
    """
    if isinstance(schema, bool):
        return
    if not isinstance(schema, dict):
        raise Unchecked(f"{where} must be an object or boolean schema")
    unchecked = set(schema) - _CHECKED - _ANNOTATIONS
    if unchecked:
        raise Unchecked(f"the schema at {where} uses {sorted(unchecked)}, which this "
                        "runner does not check; simplify the schema")
    if "type" in schema:
        types = _types(schema)
        if (not types or any(not isinstance(t, str) or
                             t not in {*_JSON_TYPES, "number", "integer"} for t in types)
                or len(set(types)) != len(types)):
            raise Unchecked(f"{where}.type must name distinct JSON types")
    if "enum" in schema and not isinstance(schema["enum"], list):
        raise Unchecked(f"{where}.enum must be an array")
    if "required" in schema:
        names = schema["required"]
        if (not isinstance(names, list) or any(not isinstance(k, str) for k in names)
                or len(set(names)) != len(names)):
            raise Unchecked(f"{where}.required must be an array of distinct strings")
    for key in ("properties", "$defs", "definitions"):
        if key in schema:
            if not isinstance(schema[key], dict):
                raise Unchecked(f"{where}.{key} must be an object of schemas")
            for name, sub in schema[key].items():
                _check_schema(sub, f"{where}.{key}.{name}")
    for key in ("items", "additionalProperties", "not"):
        if key in schema:
            _check_schema(schema[key], f"{where}.{key}")
    for key in ("allOf", "anyOf", "oneOf"):
        if key in schema:
            options = schema[key]
            if not isinstance(options, list) or not options:
                raise Unchecked(f"{where}.{key} must be a non-empty array of schemas")
            for i, sub in enumerate(options):
                _check_schema(sub, f"{where}.{key}[{i}]")


def conforms(obj, schema: dict, where: str = "answer") -> None:
    """Required keys and primitive types, checked here rather than trusted.

    An engine's validation is the engine's claim, and the claim is what this
    runner exists not to take on faith: `"refuted": "false"` is a string, and
    read as truthy it reverses the verdict.
    """
    _check_schema(schema)
    _check_finite(obj)
    _conforms(obj, schema, where)


def _conforms(obj, schema, where: str) -> None:
    if schema is True:                    # JSON Schema: `true` accepts anything
        return
    if schema is False:
        raise EngineError(f"{where} is checked against a schema that accepts nothing")
    for option in schema.get("allOf") or []:
        _conforms(obj, option, where)
    if "not" in schema:
        try:
            _conforms(obj, schema["not"], where)
        except Unchecked:
            raise
        except EngineError:
            pass
        else:
            raise EngineError(f"{where} matches a schema it must not match")
    for key in ("anyOf", "oneOf"):
        options = schema.get(key)
        if isinstance(options, list) and options:
            fits = 0
            for option in options:
                try:
                    _conforms(obj, option, where)
                    fits += 1
                except Unchecked:
                    raise
                except EngineError:
                    pass
            if fits == 0 or (key == "oneOf" and fits > 1):
                raise EngineError(f"{where} matches {fits} of the schema's {key} options")
    if "const" in schema and not _same(obj, schema["const"]):
        raise EngineError(f"{where} is {obj!r}, the schema fixes it at {schema['const']!r}")
    if isinstance(schema.get("enum"), list) and not any(_same(obj, v) for v in schema["enum"]):
        raise EngineError(f"{where} is {obj!r}, not one of {schema['enum']}")
    types = [t for t in _types(schema) if t]
    if types:
        ok = False
        for t in types:
            if t in ("number", "integer") and not isinstance(obj, bool):
                # An int is checked as an int: float() of a 400-digit one overflows.
                ok |= isinstance(obj, int) or (isinstance(obj, float) and (
                    t == "number" or obj.is_integer()))
            elif t in _JSON_TYPES:
                ok |= isinstance(obj, _JSON_TYPES[t])
        if not ok:
            raise EngineError(f"{where} is {type(obj).__name__}, the schema wants {types}")
    if isinstance(obj, dict):
        for key in schema.get("required") or []:
            if key not in obj:
                raise EngineError(f"{where} has no {key!r}, which the schema requires")
        for key, sub in (schema.get("properties") or {}).items():
            if key in obj and isinstance(sub, (dict, bool)):   # `false` is a schema too
                _conforms(obj[key], sub, f"{where}.{key}")
        extra = schema.get("additionalProperties", True)
        for key in set(obj) - set(schema.get("properties") or {}):
            _conforms(obj[key], extra, f"{where}.{key}")
    if isinstance(obj, list) and isinstance(schema.get("items"), (dict, bool)):
        for i, item in enumerate(obj):
            _conforms(item, schema["items"], f"{where}[{i}]")


def run(engine: str, prompt: str, schema: dict) -> dict:
    """Ask `engine` for one object matching `schema`. Raises rather than guessing."""
    try:
        _check_schema(schema)
    except RecursionError:
        raise Unchecked("the schema nests too deeply to check") from None
    try:
        got = _ask(engine, prompt, schema)
    except (OSError, UnicodeError) as e:
        raise EngineError(f"{engine} could not complete its run: {e}") from None
    try:
        _check_finite(got)
        _conforms(got, schema, f"{engine}'s answer")
    except RecursionError:
        raise EngineError(f"{engine}'s answer nests too deeply to check") from None
    return got


def _ask(engine: str, prompt: str, schema: dict) -> dict:
    known = ENGINES.get("runs_on") or []
    if engine not in known:
        raise EngineError(f"{engine} is not one of {known}")

    with tempfile.TemporaryDirectory(prefix="coding-engine-") as tmp:
        d = pathlib.Path(tmp)
        s = d / "schema.json"
        s.write_text(json.dumps(strict(schema)), encoding="utf-8")
        if engine == "codex":
            out = d / "answer.json"
            argv = ["codex", "exec", "--output-schema", str(s), "-o", str(out),
                    "--sandbox", "read-only", "--skip-git-repo-check", _as_argument(prompt)]
            r = _spawn(engine, argv)
            try:
                body = out.read_text(encoding="utf-8")
            except FileNotFoundError:
                body = ""
            except (OSError, UnicodeError) as e:
                raise EngineError(f"codex's answer could not be read: {e}.\n{_tail(r)}") from None
            if not body.strip():
                raise EngineError(f"codex wrote no answer.\n{_tail(r)}")
            return _parse(engine, body)
        if engine == "claude":
            argv = ["claude", "-p", _as_argument(prompt), "--output-format", "json",
                    "--json-schema", json.dumps(schema)]
            r = _spawn(engine, argv)
            envelope = _parse(engine, r.stdout)
            if "structured_output" not in envelope:
                raise EngineError(f"claude returned no structured_output "
                                  f"(subtype {envelope.get('subtype')!r}).\n{_tail(r)}")
            return envelope["structured_output"]
        if engine == "agy":
            argv = ["agy", f"--print={prompt}", "--output-format", "json",
                    "--json-schema", str(s)]
            r = _spawn(engine, argv)
            envelope = _parse(engine, r.stdout)
            if "structured_output" not in envelope:
                raise EngineError(f"agy returned no structured_output "
                                  f"(status {envelope.get('status')!r}).\n{_tail(r)}")
            return envelope["structured_output"]
    raise EngineError(f"no invocation is known for {engine}")


def _spawn(engine: str, argv: list[str]) -> subprocess.CompletedProcess:
    """Every way the engine can fail to start or answer is an EngineError — a
    caller asking several engines keeps the verdicts the others gave."""
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=TIMEOUT,
                                encoding="utf-8", errors="replace")
    except FileNotFoundError:
        raise EngineError(f"{engine} is not on PATH") from None
    except subprocess.TimeoutExpired:
        raise EngineError(f"{engine} did not answer within {TIMEOUT}s") from None
    except (OSError, ValueError) as e:     # E2BIG, or a NUL in a prompt argument
        raise EngineError(f"{engine} could not be started: {e}") from None
    if result.returncode:
        raise EngineError(f"{engine} exited with status {result.returncode}.\n{_tail(result)}")
    return result


def _as_argument(prompt: str) -> str:
    """A prompt opening with `-` (YAML frontmatter, a rule) is read as an option."""
    return "\n" + prompt if prompt.startswith("-") else prompt


def _parse(engine: str, body: str) -> dict:
    stripped = body.strip()
    refused = None
    try:
        got = _loads(stripped)
    except ValueError:
        pass
    except EngineError as e:
        refused = EngineError(f"{engine}: {e}")   # unless a line holds the answer
    else:
        if isinstance(got, dict):
            return got
        raise EngineError(f"{engine} returned {type(got).__name__}, not an object")
    # A log line after the answer is skipped, whatever it holds: `NaN` alone
    # on a line is not the answer, and must not stop the search for it.
    for line in reversed(stripped.splitlines()):
        try:
            got = _loads(line)
        except (ValueError, EngineError):
            continue
        if isinstance(got, dict):
            return got
    if refused:
        raise refused
    raise EngineError(f"{engine} printed nothing that parses as an object:\n{body[:400]}")


def _tail(r: subprocess.CompletedProcess) -> str:
    return "\n".join((r.stderr or r.stdout or "").strip().splitlines()[-6:])


def other_than(running: str) -> str:
    """An engine that is not the one running. Raises rather than falling back."""
    known = ENGINES.get("runs_on") or []
    if running not in known:
        raise EngineError(f"the running engine {running!r} is not one of {known}; "
                          "state it correctly rather than letting this guess")
    for candidate in known:
        if candidate != running:
            return candidate
    raise EngineError(f"{known} leaves nothing to check {running} with")


SELFTEST = {"type": "object", "properties": {"ok": {"type": "boolean"}},
            "required": ["ok"]}


def selftest() -> int:
    """Ask each declared engine for one object. Reachability, not correctness."""
    bad = 0
    for engine in ENGINES.get("runs_on") or []:
        try:
            got = run(engine, "Reply with ok=true and nothing else.", SELFTEST)
        except EngineError as e:
            print(f"  {engine}: UNAVAILABLE — {e}")
            bad += 1
            continue
        print(f"  {engine}: answered {got}")
    known = ENGINES.get("runs_on") or []
    print(f"engines reachable: {len(known) - bad}/{len(known)} of {known}   "
          f"any of them may be the one running")
    # Unreachable is reported, never fatal: a machine without one of these still
    # runs every other check, and a hook that fails on a missing CLI gets removed.
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("engine", nargs="?", help="the checker; omit to resolve from --running")
    ap.add_argument("--running", help="the engine running this harness — required, never guessed")
    ap.add_argument("--prompt-file")
    ap.add_argument("--schema")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest or not (a.engine or a.running or a.prompt_file or a.schema):
        return selftest()
    if not a.running:
        # Naming the checker is not enough: without the running engine there is
        # nothing to compare it with, and the maker could be marking its own work.
        print("need --running: the engine running this is stated, never guessed",
              file=sys.stderr)
        return 2
    if not (a.prompt_file and a.schema):
        print("need --prompt-file and --schema", file=sys.stderr)
        return 2
    try:
        default_checker = other_than(a.running)  # validate even with an explicit checker
        engine = a.engine or default_checker
        if engine == a.running:
            raise EngineError(f"{engine} is the engine running this; "
                              "a verdict from it is not a check")
        got = run(engine,
                  pathlib.Path(a.prompt_file).read_text(encoding="utf-8"),
                  json.loads(pathlib.Path(a.schema).read_text(encoding="utf-8")))
    except (OSError, ValueError, RecursionError) as e:
        print(f"could not read the prompt or schema: {e}", file=sys.stderr)
        return 2
    except Unchecked as e:
        # The caller's schema, not the engine: no engine was asked.
        print(f"schema: {e}", file=sys.stderr)
        return 2
    except EngineError as e:
        print(f"{a.engine or 'checker'}: {e}", file=sys.stderr)
        return 1
    print(json.dumps(got, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
