<!-- coding:guidance -->
# Boundaries — code meeting what it does not control

A boundary is any point where data or control crosses into or out of code you
own: the network, another service, the filesystem, the clock, a database, a
subprocess, a user. Inside the boundary you may trust; across it you may not.

## Establish the contract before writing against it

- **Read the specification, not one response.** A sample shows what happened
  once; the contract says what is allowed. Optional fields, nullability, units,
  and enumerations are where the two differ
- **Call it once for real, early**, and record the actual shape. A mock written
  from imagination agrees with itself forever
- **Pin the units and the timezone in the name or the type.** `expires_at` in
  seconds versus milliseconds is a defect that passes every type check
- **Find out what it does under failure**, not just success: does it return an
  error code with HTTP 200? Does it truncate? Does it partially apply?

## Failure is a design decision, not an afterthought

For each boundary call, decide explicitly and write down the choice:

| Question | If you do not decide |
|---|---|
| Timeout — how long? | The default is often infinite, and one slow dependency stalls everything |
| Retry — how many, with what backoff? | Either no resilience, or a retry storm amplifying an outage |
| Is the operation idempotent? | Retries duplicate the effect. Decide before adding the retry |
| Partial failure — what state is left? | Half-applied changes with no record of which half |
| What does the caller see? | An internal exception leaks a stack trace to a user, or vanishes into a log |
| What gets logged, and without what? | Either nothing to debug with, or credentials in the log |

**Catch narrowly.** A bare `except`/`catch(e)` around a boundary call swallows
the programming errors alongside the network ones, and the programming error is
the one you needed to see.

## Validation belongs at the entrance

Validate once, where data arrives from outside, and convert it to a type the
rest of the code can trust. Re-validating downstream is noise that hides where
the real check lives — and if the downstream check ever disagrees with the
entrance check, you have two contracts.

What actually needs checking at the entrance: presence, type, range, encoding,
size, and anything that will become part of a query, a path, a command, or
markup. Size limits matter more than they look: an unbounded input is a
memory-exhaustion bug wearing a parsing bug's clothes.

## Concurrency and time

- **Nothing is atomic across a boundary.** Read-modify-write against a database
  or an API is a race unless something makes it atomic — `SELECT ... FOR UPDATE`,
  a conditional update (compare-and-set on a version column), `SERIALIZABLE`
  isolation, or a lock with an owner and a timeout. **A plain transaction is not
  one of them**: at `READ COMMITTED` — the default in PostgreSQL, Oracle, and
  SQL Server — two transactions happily read the same row and overwrite each
  other's update
- **The clock is a boundary.** Take time as an input rather than calling `now()`
  deep inside logic — untestable otherwise, and wrong across timezones anyway
- **Order is not guaranteed** for anything queued, retried, or delivered
  at-least-once. Design for duplicates and reordering, or state that you did not
- **Cached values are stale by definition.** Decide what stale means here and
  what invalidates it. A cache with no invalidation story is a bug with a delay

## Secrets and data crossing out

- Credentials come from the environment or a secret store, never from a literal,
  never from a comment, never from a test fixture that gets committed
- Log identifiers, not payloads. A payload log is a data breach on a slow timer
- Anything leaving the machine — a request, an upload, a publish — is a
  permission question first and a code question second

## Before calling a boundary done

- The real contract was read or the real call was made once
- Timeout, retry, and idempotency were each decided, and the decisions are visible in the code
- Failures are caught narrowly, and what the caller sees is deliberate
- Validation happens at the entrance and exactly once
- The failure path was actually exercised — unplugged, timed out, or fed a malformed response
