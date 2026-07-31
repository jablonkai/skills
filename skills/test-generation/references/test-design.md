# Test design — cases, names, doubles, coverage

Stack-independent decisions. Load this when the case list is not obvious from the contract, or
when choosing between a fake and a mock.

## Deriving cases from the code

Work outward in this order; stop when the next category adds nothing real.

1. **The contract** — one test per documented behavior. If the doc comment says "returns null when
   the key is absent", that sentence is a test.
2. **The branches** — every `if`, `when`/`switch` arm, early return, loop that can run zero times,
   and every `?:`/`??`/`unwrap_or` fallback. Each needs at least one case that takes it.
3. **The boundaries** — for every number, index, length, and date: zero, one, many, min, max,
   and one past each end. Off-by-one is the single most common defect a unit test catches.
4. **The absences** — empty string, empty collection, null/`nil`/`None`, missing optional,
   whitespace-only input, default parameters left unset.
5. **The failures** — every exception the code can throw, every `Err`/`Failure` it can return, and
   what the caller-visible behavior is when a dependency fails.
6. **The sequences** — called twice, called out of order, called after close/dispose/cancel. Only
   for stateful units.

### Equivalence classes, not enumerations

Inputs that travel the same path through the code are one case. Testing `add(2,3)`, `add(4,5)` and
`add(6,7)` is one test written three times. Testing `add(2,3)`, `add(0,0)`, `add(MAX,1)` is three
cases. Where the framework supports parameterized tests, use them for genuinely distinct values in
one class — not to pad the count.

### The "can this fail?" filter

Before keeping a case, name the implementation change that would make it go red. If you cannot,
delete it. Cases that never fail:

- Asserting a constructor assigns its parameters
- Asserting a getter returns the field
- Asserting a mock returns what you just told it to return (tests the mock, not the code)
- Asserting no exception is thrown when nothing could throw

## Naming

The name is read in a failure report, without the source. It must carry the condition and the
expectation. Match the project's existing style; if there is none, prefer one of:

```
returns empty list when the query matches nothing
throws IllegalArgumentException when retryCount is negative
test_parse_rejects_trailing_comma
```

Avoid `testFoo`, `test1`, `worksCorrectly` — they identify the method, not the behavior, and tell
you nothing when they fail at 2am.

## Structure

```
// Arrange — the state and inputs, visibly separated
// Act     — exactly one call to the unit under test
// Assert  — the observable result
```

- One act per test. Two calls to the unit under test usually means two tests, unless the point of
  the test *is* the sequence.
- Assert on values, not on interactions, whenever the value is observable. Interaction assertions
  ("was `save()` called") pin the implementation and break on every refactor; use them only when
  the interaction *is* the behavior (an event was published, a payment was charged).
- No logic in tests — no loops building expectations, no `if` deciding what to assert. A test with
  a bug is worse than no test.

## Test doubles — pick the weakest one that works

| Double | What it is | Use when |
|---|---|---|
| Real object | The actual collaborator | Cheap, deterministic, no I/O — always prefer this |
| Stub | Returns canned values | You need a specific input to the unit under test |
| Fake | Working lightweight implementation (in-memory repo) | The collaborator is used repeatedly across a suite |
| Spy | Records calls, real behavior otherwise | You must assert an interaction happened |
| Mock | Preprogrammed expectations, verifies them | Last resort — the interaction is the behavior |

Rules of thumb:

- **Do not mock types you own.** If your own class is hard to construct in a test, that is a design
  signal, not a mocking problem.
- **Do not mock what you do not own either** — wrap it. Mocking a third-party client encodes your
  assumptions about its behavior, and those assumptions are exactly what breaks on upgrade.
- **A fake shared across a suite pays for itself**; a mock configured in twelve tests does not.
- Mocking a value type, a data class, or a collection is always wrong — construct a real one.

## Determinism

Non-deterministic tests are removed from CI eventually, taking their coverage with them. Control:

- **Time** — inject a clock/`TimeSource`/`Instant` provider. Never assert on `now()`.
- **Randomness** — seed it, or inject the generator.
- **Concurrency** — use the framework's test scheduler (`runTest`, `FakeAsync`, `tokio::test`,
  `#expect` with async). Never `sleep` to wait for async work.
- **Order** — tests must pass in any order and in isolation. Shared mutable state between tests is
  a defect in the suite.
- **Environment** — no network, no real filesystem outside a temp dir, no dependence on locale,
  timezone, or ambient env vars unless the test sets them itself.

## Integration tests

The distinction that matters is not "how many classes" but **what is real**.

- Keep the boundary explicit: name what is real (the DB, the HTTP layer) and what is still
  substituted. A test that is unclear about this is hard to trust when it fails.
- Prefer ephemeral real dependencies (in-memory DB, temp dir, local test server, containers) over
  a shared environment. Shared state across runs makes failures unreproducible.
- Setup and teardown must be symmetric and must run even when the test fails — use the framework's
  fixture mechanism, not manual cleanup at the end of the body.
- Integration tests are slower and fewer. If a case can be covered at the unit level, cover it
  there and leave the integration test for the wiring.

## Reading a coverage report

Coverage finds untested code. It does not measure test quality — a suite with no assertions can
reach 100%.

- **Branch coverage over line coverage.** A one-line `if` with a missing else is 100% line-covered
  and untested.
- Read the report as a list of uncovered branches and judge each one: is it a real path, or is it
  defensive code that cannot occur? Say which.
- Exclude generated code, DTOs, and framework glue from the denominator rather than writing tests
  for them.
- A coverage *drop* on a PR is a useful signal. An absolute target is a metric to game.

Report gaps as `file:line` with the reason each is untested — that is actionable in a way that a
percentage is not.
