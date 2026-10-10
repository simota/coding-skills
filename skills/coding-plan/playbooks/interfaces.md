<!-- coding:guidance -->
# Interfaces — designing what others will call

An interface is a promise you cannot cheaply withdraw. Everything else in a
codebase can be rewritten by one person; an interface is rewritten by everyone
who calls it.

## Decide these, in this order

1. **Who calls it, and how many are there?** One caller means no abstraction is
   needed. The seam gets added when the second arrives, and it will be a better
   seam for having two real cases instead of one imagined
2. **What must the caller already know?** Every required parameter, every
   ordering rule ("call `open` before `read`"), every state assumption. Knowledge
   the caller needs but the signature does not express is where misuse comes from
3. **What can go wrong, and how does the caller learn?** Return value, exception,
   result type — pick one per category and be consistent. Silent failure is a
   choice, and almost never the right one
4. **What is the smallest surface that serves the real callers?** Every extra
   method is a promise. Start narrow; widening later is compatible, narrowing is not

## Shapes worth choosing deliberately

| Question | Default | Take the other when |
|---|---|---|
| Parameters or an options object | Parameters up to ~3 | More than three, or several are optional, or booleans read ambiguously at the call site |
| Boolean flag or two functions | Two functions | The flag is genuinely data flowing through, not a mode switch |
| Return `null` or raise | Raise | Absence is a normal, expected outcome the caller must handle every time — return an absence type |
| Sync or async | Match the surrounding code | Never within one call chain. Blocking I/O in an async codebase goes behind its existing offload (executor, thread pool) — mixing colours is a permanent tax |
| Accept a concrete type or an interface | Concrete | A second implementation exists today. A test that cannot construct the real one is fixed at construction, not by adding an interface |
| Mutate or return new | Return new | The object is large and hot, and the profile says so |

## Naming as part of the contract

- **The name states what it does, not how.** `sortedByPriority` survives the
  algorithm changing; `quickSortItems` does not
- **`get` should not do work.** A `get` that hits the network, writes, or blocks
  is a lie that surfaces as a performance bug in someone else's code
- **Match the codebase's word for the concept**, even if it is the worse word.
  Two words for one thing costs more than one imperfect word
- **Units and nullability belong in the name or the type**: `timeout_ms`,
  `maybeUser`, `Optional[Account]`. A field named `timeout` is a bug waiting for
  a second reader

## Compatibility, if anything already calls it

- **Removing and renaming break callers; adding usually does not, but not
  always.** A new response field breaks a strict deserialiser (Jackson's default,
  `additionalProperties: false`); a new enum value breaks an exhaustive match; a
  new interface method breaks implementers; a new struct field breaks positional
  literals; a parameter inserted mid-list breaks positional calls
- **Widening a parameter type** accepts everything it did before. **Widening a
  return type does not**: a caller written against `Dog` breaks when you start
  returning `Animal`. Narrowing the return is the safe direction — for callers;
  for implementers and overriders, both directions reverse. Both are source
  compatibility only: **on the JVM and .NET any signature change breaks compiled
  callers** (`NoSuchMethodError`) until they rebuild, so a published library
  adds an overload instead
- **Adding a required field to a request** breaks old callers; adding an optional
  one with a default does not
- **Removing a field from a response** breaks readers you cannot see. Deprecate,
  observe, then remove
- **Changing the meaning of an existing field** is the worst case — it breaks
  silently, produces wrong data instead of an error, and no type checker catches it
- Where a change cannot be compatible: add the new path, migrate callers, remove
  the old one. Three steps, three commits, never one

## Before calling the interface designed

- Write the **call site** first, as the caller would write it. If it reads badly
  there, the design is wrong regardless of how it looks from the inside
- Every error path has a named representation
- Nothing in the surface exists for a caller that does not exist yet
- A reader of the signature alone can use it correctly
