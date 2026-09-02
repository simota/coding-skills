<!-- coding:guidance -->
# Search — finding code when you do not know its name

The failure mode is guessing names until something hits. It feels like
progress, costs a lot, and terminates only by luck. Work from something you
can actually observe instead.

## The ladder — cheapest anchor first

| You have | Anchor on |
|---|---|
| An error message or log line | The literal string. Strip the interpolated parts and grep the constant fragment |
| A URL, route, or CLI flag | The routing table or argument parser. Every request enters somewhere nameable |
| A UI label the user sees | The string, then its translation key, then whatever renders that key |
| A database column or table | The migration that created it, then the model, then its readers |
| A dependency's behaviour | The import site, then the call, then the installed source — `node_modules/`, `site-packages/`, `vendor/`. The lockfile pins the version; it holds no code |
| A time — "it broke Tuesday" | `git log --since` on the touched paths. Narrow by time before narrowing by name |
| Nothing but a feature name | The tests. Test names describe behaviour in the team's own vocabulary |

**The team's vocabulary is not yours.** What a user calls "archiving" may be
`soft_delete`, `retire`, or `status = 3` in the code. Two failed name guesses
means switching to an observable anchor, not a third guess.

## Working outward from an anchor

1. **Anchor** — one confirmed `file:line` that is definitely part of the path
2. **Up** — who calls this? `grep` the symbol, then read each hit to confirm it
   is a real call and not a same-named unrelated thing
3. **Down** — what does it call that matters? Follow only the branches the
   question needs. Depth without a question is a tour
4. **Sideways** — is there a second implementation? Search for a sibling with a
   similar shape. A forked copy is the single most common reason a fix does not take

Stop when the answer artifact named at the start exists. Not before, and
emphatically not after.

## What hides from grep

Any of these means a name search will under-report, and the report must say so:

- Dynamic dispatch — reflection, `getattr`, string-keyed registries, DI containers
- Names assembled at runtime — `f"handle_{event}"`, template-generated methods
- Config-driven wiring — YAML/JSON naming a class or handler by string
- Code generation — the symbol exists only after a build step
- Re-exports and barrel files — the definition is three hops from the import
- Framework conventions — a file in the right directory is called by nobody visible

For each of these that applies, either find the registry and enumerate it, or
report the search as `PARTIAL` and name the hole.

## Before reporting

- Every claim has a `file:line`
- Every "called from" was read, not just matched
- The dynamic-dispatch list above was checked, and any hits declared
- The directories you never searched are named
