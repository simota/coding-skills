<!-- coding:guidance -->
# Cases — deciding what to test

Coverage tells you which lines ran. It says nothing about which behaviours are
guarded. Derive cases from what the code promises and where it meets the world.

## Where cases come from

| Source | The case |
|---|---|
| Each stated behaviour | The plain path — does it do the thing it claims? |
| Each boundary in the input domain | Zero, one, many; empty, min, max, over max; first and last element |
| Each branch in the code | What condition selects it, and what makes it not selected |
| Each failure route you chose to handle | It is handled the way you decided |
| Each bug ever fixed here | The regression case — high value, because it pins a failure that already happened once |
| Each assumption about the outside | Malformed response, timeout, partial result, duplicate delivery |
| Each type that can be null or absent | Absent, and present-but-empty. These behave differently |
| Each invariant | Something that must always hold — a total that balances, an ID that stays unique |

## Rank them by silence, not by likelihood

Write first what would break **without anyone noticing**. A crash announces
itself; a wrong number in a report does not.

1. Wrong data written or returned, silently
2. Money, permissions, or personal data
3. Anything whose failure is only visible later — a batch job, an export, an
   analytics event
4. Loud failures, which the next user reports for free

## Boundaries that actually catch things

- **Off-by-one**: the last element, the empty collection, exactly at the limit
- **Empty versus absent**: `""` versus `null` versus a missing key
- **Zero and negative**: quantities, offsets, durations
- **Unicode**: multi-byte, combining characters, right-to-left, emoji in a field
  sized in bytes
- **Time**: month ends, DST transitions, leap day, expiry exactly now, timezone
  where the date differs from UTC's
- **Repetition**: calling twice — is it idempotent? Is the second call a duplicate?
- **Order**: the same operations in a different sequence
- **Size**: an input large enough to hit a limit somewhere

## Writing one that means something

- **Arrange, act, assert** — and one act per test. Two acts means the failure
  message will not say which one failed
- **Name the case, not the function.** `rejects_expired_token` over `test_auth_3`.
  The name is what a failure report shows at 3am
- **Assert the value, not the shape.** `== 3` beats `is not None`, and both beat
  "did not raise"
- **Fixtures make the case obvious.** Whatever is not relevant to this case
  belongs in a default; whatever is relevant is visible in the test body
- **One reason to fail.** A test asserting six unrelated things fails once and
  tells you the least useful of the six

## What not to write

- Tests of the framework, the ORM, or the standard library
- Tests of a getter that returns a field
- Tests that restate the implementation line by line — they fail on every
  refactor and catch no defects. This is the main cost of a bad suite
- A second test that differs only in an irrelevant value. Use a parameterised
  case, or drop it

## Levels

Choose the cheapest level where the behaviour is actually observable:

- **Unit** for logic with branches — fast, precise, most cases live here
- **Integration** for anything crossing a boundary you own: the query really
  runs, the migration really applies, the serialisation really round-trips
- **End-to-end** for a handful of paths that must never break. They are slow and
  flaky in proportion to their length, so keep the handful small and the
  assertions coarse

**A mock at the wrong level tests nothing.** Mocking the database and asserting
"save was called" checks the test's own wiring; the interesting failures are in
the query and the schema.

## Before calling the cases chosen

- The silent-failure case is written first
- Every fixed bug in this area has a regression case
- Each case was seen to fail for its stated reason
- The behaviours deliberately left uncovered are named in the report
