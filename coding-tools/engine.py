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


def _types(schema: dict) -> list:
    t = schema.get("type")
    return t if isinstance(t, list) else [t]


def strict(schema: dict) -> dict:
    """Every object closed, which is what codex requires and agy tolerates.

    Recurses through nested schemas, lists of them (`anyOf`, `prefixItems`) and
    nullable objects. A map — `additionalProperties` given as a schema — cannot
    be closed without changing what it accepts, so it stops rather than being
    silently narrowed to `{}`.
    """
    if isinstance(schema, list):
        return [strict(s) for s in schema]
    if not isinstance(schema, dict):
        return schema
    out = {k: strict(v) if isinstance(v, (dict, list)) else v for k, v in schema.items()}
    if "object" in _types(out):
        extra = schema.get("additionalProperties")
        if isinstance(extra, dict):
            raise EngineError("a schema with additionalProperties as a schema (a map) "
                              "cannot be closed; codex rejects it open")
        out["additionalProperties"] = False
        out["properties"] = {k: strict(v) for k, v in (out.get("properties") or {}).items()}
    return out


_JSON_TYPES = {"string": str, "boolean": bool, "object": dict, "array": list,
               "null": type(None)}


def conforms(obj, schema: dict, where: str = "answer") -> None:
    """Required keys and primitive types, checked here rather than trusted.

    An engine's validation is the engine's claim, and the claim is what this
    runner exists not to take on faith: `"refuted": "false"` is a string, and
    read as truthy it reverses the verdict.
    """
    for key in ("anyOf", "oneOf"):
        options = schema.get(key)
        if isinstance(options, list) and options:
            fits = 0
            for option in options:
                try:
                    conforms(obj, option, where)
                    fits += 1
                except EngineError:
                    pass
            if fits == 0 or (key == "oneOf" and fits > 1):
                raise EngineError(f"{where} matches {fits} of the schema's {key} options")
    if "const" in schema and obj != schema["const"]:
        raise EngineError(f"{where} is {obj!r}, the schema fixes it at {schema['const']!r}")
    if isinstance(schema.get("enum"), list) and obj not in schema["enum"]:
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
            if key in obj and isinstance(sub, dict):
                conforms(obj[key], sub, f"{where}.{key}")
    if isinstance(obj, list) and isinstance(schema.get("items"), dict):
        for i, item in enumerate(obj):
            conforms(item, schema["items"], f"{where}[{i}]")


def run(engine: str, prompt: str, schema: dict) -> dict:
    """Ask `engine` for one object matching `schema`. Raises rather than guessing."""
    got = _ask(engine, prompt, schema)
    conforms(got, schema, f"{engine}'s answer")
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
                    "--sandbox", "read-only", "--skip-git-repo-check", prompt]
            r = _spawn(engine, argv)
            body = out.read_text(encoding="utf-8") if out.exists() else ""
            if not body.strip():
                raise EngineError(f"codex wrote no answer.\n{_tail(r)}")
            return _parse(engine, body)
        if engine == "claude":
            argv = ["claude", "-p", prompt, "--output-format", "json",
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
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=TIMEOUT)
    except FileNotFoundError:
        raise EngineError(f"{engine} is not on PATH") from None
    except subprocess.TimeoutExpired:
        raise EngineError(f"{engine} did not answer within {TIMEOUT}s") from None


def _parse(engine: str, body: str) -> dict:
    stripped = body.strip()
    try:
        got = json.loads(stripped)
        if isinstance(got, dict):
            return got
    except ValueError:
        pass
    for line in reversed(stripped.splitlines()):
        try:
            got = json.loads(line)
        except ValueError:
            continue
        if isinstance(got, dict):
            return got
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
        engine = a.engine or other_than(a.running)
        if engine == a.running:
            raise EngineError(f"{engine} is the engine running this; "
                              "a verdict from it is not a check")
        got = run(engine,
                  pathlib.Path(a.prompt_file).read_text(encoding="utf-8"),
                  json.loads(pathlib.Path(a.schema).read_text(encoding="utf-8")))
    except (OSError, ValueError) as e:
        print(f"could not read the prompt or schema: {e}", file=sys.stderr)
        return 2
    except EngineError as e:
        print(f"{a.engine or 'checker'}: {e}", file=sys.stderr)
        return 1
    print(json.dumps(got, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
