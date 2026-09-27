---
name: testing
description: "Write tests for existing code and bring it to at least 80% coverage: unit, integration and UI tests, edge cases and error paths, regression tests for fixed bugs, and measured coverage gap analysis. Detects the test framework from the build files and follows the project's conventions — Kotlin/KMP (kotlin.test, coroutines-test, Turbine, MockK, Kover), Compose Multiplatform, Flutter/Dart, Swift (Swift Testing, XCTest), Rust (cargo test, proptest), C++ (GoogleTest, Catch2), and secondarily Jest/Vitest/node:test, pytest/unittest, Go and JUnit. Use when someone says 'write tests for this', 'add unit tests', 'test this function', 'what is not covered', 'improve test coverage', 'write a regression test for this bug', or the Hungarian 'írj teszteket', 'teszteld le ezt', 'mi nincs letesztelve', 'növeld a lefedettséget'. Not for auditing a whole project (code-analyzer), nor for root-causing a crash or failing test (error-debugging)."
summary: "write unit, integration and UI tests for existing code to at least 80% coverage — framework detection from the build files, case selection for boundaries and error paths, correct source-set placement, and measured coverage gap analysis across Kotlin/KMP, Compose, Flutter/Dart, Swift, Rust and C++"
category: testing
risk: low
tags:
  - testing
  - unit-tests
  - integration-tests
  - coverage
  - mocks
  - kotlin
  - flutter
  - swift
  - rust
  - cpp
allowed-tools: Bash, Read, Grep, Glob, Edit, Write, Skill
argument-hint: "[file, function, class, or module to test]"
---

# testing

## Purpose

Turn existing code into tests that would actually catch it breaking. The input is a function,
class, module, or bug report; the output is test files in the project's own framework, in the
right source set, that run and pass, cover at least 80% of the code under test — plus a short,
measured statement of what is still untested.

The value is in case selection, not in typing. A test that only walks the happy path documents
the code; it does not defend it. Most real defects live at the boundaries and in the error paths,
so that is where the cases go — and that is also why well-chosen cases reach the coverage floor
without any padding.

## When to use

- "Write tests for `<file/function/class>`" — new or existing code
- A bug was just fixed and needs a regression test that fails without the fix
- A module has no tests and needs a suite scaffolded
- Coverage is low and the question is *what* to test next

Not this skill:

- **Whole-project audit that happens to mention missing tests** → `code-analyzer`
- **A test or app is failing and you need the root cause** → `error-debugging`
- **Setting up a test framework that does not exist in the project yet** → do that first (see the stack reference), then come back

## Route to a more specific skill first

Several stacks already have dedicated skills. When one applies, invoke it for the mechanics of
writing the test; this skill still owns the surrounding decisions — which cases, which source
set, and the coverage floor.

| Situation | Skill to invoke |
|---|---|
| Dart unit tests with `package:test` | `dart-add-unit-test` |
| Dart mocks via `mockito` + `build_runner` | `dart-generate-test-mocks` |
| Flutter widget tests | `flutter-add-widget-test` |
| Flutter `integration_test` flows | `flutter-add-integration-test` |
| Compose / CMP UI tests, semantics, screenshot tests | `compose-ui-testing-patterns` |

Swift, Rust, C++, and non-UI Kotlin/KMP have no dedicated skill — this one covers them directly.

## Prerequisites

**1. What stack is this, and what framework is already in use?** Detect from build files, not from
the file extension alone — a `.kt` file in a KMP `commonTest` source set is tested very differently
from one in an Android unit test.

| Build file / signal | Stack | Reference |
|---|---|---|
| `build.gradle.kts` with `kotlin("multiplatform")`, `commonTest` | Kotlin Multiplatform | [kotlin-kmp.md](references/kotlin-kmp.md) |
| `build.gradle(.kts)` with `com.android.application`, `androidTest/` | Kotlin/JVM, Android | [kotlin-kmp.md](references/kotlin-kmp.md) |
| `androidx.compose.*` or `compose-multiplatform` dependencies | Compose / CMP | `compose-ui-testing-patterns` skill |
| `pubspec.yaml` | Flutter / Dart | [flutter-dart.md](references/flutter-dart.md) |
| `Package.swift`, `*.xcodeproj`, `*.xcworkspace` | Swift (iOS/macOS) | [swift-apple.md](references/swift-apple.md) |
| `Cargo.toml` | Rust | [rust-cpp.md](references/rust-cpp.md) |
| `CMakeLists.txt`, `conanfile.txt`, `*.cpp` | C / C++ | [rust-cpp.md](references/rust-cpp.md) |
| `package.json`, `pyproject.toml`, `go.mod`, Maven `pom.xml` | JS/TS, Python, Go, Java | [other-languages.md](references/other-languages.md) |

Load exactly one stack reference — the one that matches. Loading several mixes idioms that do not
apply and wastes context.

**2. Does a test suite already exist?** Read two or three existing test files before writing
anything. The project's naming, assertion library, fixture style, and mocking approach are already
decided; matching them matters more than any convention in this skill. Note any coverage
threshold the project already enforces (Kover/JaCoCo rules, Jest `coverageThreshold`,
`fail_under` in `.coveragerc`/`pyproject.toml`) — if it is above 80%, it is the floor instead.

```bash
# find the existing suite and its conventions
find . -type d \( -name test -o -name tests -o -name '*Test*' -o -name commonTest \) -not -path '*/build/*' -not -path '*/node_modules/*' | head -20
```

If there is no suite at all, say so — the first test in a project often needs a framework
dependency and a runner configuration, which is a larger change than the user may expect. Prefer
a runner that needs no new dependency (`unittest`, `node:test`, `cargo test`, `go test`) when the
project has not picked one.

## Workflow

### Step 1: Read the code under test

Read the actual implementation, not just the signature. You are looking for the things a test can
assert on and the things that make it hard to test:

- **Contract** — inputs, outputs, thrown/returned errors, documented invariants
- **Branches** — every `if`, `when`/`switch`, early return, loop boundary, and `?:` fallback
- **Dependencies** — what has to be substituted (clock, network, filesystem, database, random)
- **State** — is the result a pure function of the inputs, or does it depend on prior calls?
- **Concurrency** — suspending functions, async/await, threads, actors, channels

Use symbol-aware tools (Serena, LSP) where available to read the enclosing symbol and its call
sites rather than whole files. Call sites show how the code is really used, which is where the
realistic cases come from.

If the code is untestable as written (hard-wired singleton, hidden clock, constructor doing I/O),
first look for a seam the language already gives you — patching the module-level name in Python,
`monkeypatch`, a default parameter, a protocol the type already conforms to. Only if there is none,
say so and name the smallest change that would fix it. Do not silently refactor production code to
make a test possible — propose it, and let the user decide.

### Step 2: Choose the cases

Derive cases from the contract and the branches, not from a template. For each unit under test,
work through these categories and keep the ones that are real for this code:

| Category | Ask |
|---|---|
| Happy path | The typical call with typical values — one per meaningful behavior, not per method |
| Boundaries | Zero, one, many; first, last; min, max; off-by-one on every index and length |
| Empty / absent | Empty string, empty collection, null/`None`/`nil`, absent optional, default argument |
| Invalid input | Malformed data, out-of-range values, wrong type where the language permits it |
| Error paths | Every thrown exception, `Err`, failed `Future`, and the recovery around it |
| State transitions | Called twice, called out of order, called after close/dispose |
| Concurrency | Cancellation, timeout, racing callers — only where the code is actually concurrent |

Two rules that decide most of the case list:

- **One behavior per test.** A test that asserts five things fails with one message and tells you
  nothing about the other four.
- **A case earns its place by being able to fail.** If no plausible implementation change makes the
  test go red, it is not testing anything — drop it.

For a bug-fix regression test, invert the order: write the test that reproduces the bug first,
confirm it fails against the unfixed code (for example by stashing the fix, or checking out the
file from the previous commit, and restoring it afterwards) — or explain why that is not possible —
then keep it.

Case-selection heuristics, naming, and fixture/mock/fake choice are in
[test-design.md](references/test-design.md) — load it when the cases are not obvious from the
contract.

### Step 3: Place the file correctly

Wrong placement is the most common way a generated test never runs. The stack reference gives the
exact rules; the shape is always the same:

- Mirror the source path in the test source root, and name the file after the unit under test
- Pick the source set by what the test needs: shared/pure logic goes in the common or plain unit
  test set; anything needing a device, a real framework, or a UI goes in the platform/instrumented
  set
- Match the existing suite's package/module declaration

### Step 4: Write the tests

Follow the conventions found in Prerequisite 2 and the idioms in the stack reference:

- **Arrange, act, assert** — visibly separated, in that order
- **Descriptive names** — the name states the condition and the expected result, so a failure is
  readable without opening the file
- **Assert the behavior, not the implementation** — asserting on internal calls freezes the design
  and breaks on every refactor
- **Substitute only what you must** — a real object beats a fake, a fake beats a mock; mocking
  types you own is usually a design smell
- **Deterministic by construction** — inject the clock, seed the random source, control the
  dispatcher/scheduler; never `sleep` to wait for async work
- **Fixtures over duplication** — but a little duplication in tests is cheaper than a fixture
  hierarchy nobody can follow

Write the tests the project's existing suite would recognize as its own.

### Step 5: Run them

A generated test that was never executed is a draft. Run the suite — narrowed to the new tests
first, then the full suite — and fix what fails.

The stack reference has the exact command. Keep the output small: filter to failures rather than
pasting the whole run.

Then verify the tests are worth having: break the implementation in a way that should fail a test
(flip a comparison, drop a branch — actually, then revert) and confirm the right test goes red.
Report honestly if a test passes against a deliberately broken implementation — that means it is
asserting nothing.

### Step 6: Measure coverage and close the gap

**The floor is 80% line coverage of the code under test — branch coverage too, where the tool
reports it. When more is cheap, take more.** See the next section for what counts and how to
measure. Run coverage, read the uncovered lines, and add cases for the ones that are real,
reachable behavior until the floor is met; keep going while the remaining gaps are ordinary
branches that one more meaningful case would take — on a small unit that usually lands at 90–100%.
Stop when the next test would be padding, or would need a disproportionate harness.

Then report:

```markdown
## Tests added
<file paths, and one line per behavior covered>

## Verification
<commands run, and the real result — pass/fail counts>

## Coverage
<tool used; line (and branch) % of the code under test, before → after; the floor that applied>

## Still untested
<each uncovered line or branch as `file:line` — with why: unreachable, needs a device, untestable as written (and the smallest change that would fix it)>
```

## Coverage target

The 80% floor exists because on code someone just wrote tests for, anything below it almost always
means an error path or a boundary was skipped — exactly where defects live. It is a floor, not the
point: a suite at 100% with weak assertions defends less than one at 85% that kills every mutation.

- **Scope is the code under test** — the files or units the user named, or that the new tests
  target. A request about one module does not make the whole project's coverage your job; mention
  the project-wide figure only if the tool prints it anyway.
- **A stricter project threshold wins.** If the build already enforces more than 80%, meet that.
- **Measure, do not guess.** Use the project's coverage tool if configured. If it is not, use one
  that needs no committed configuration — `node --test --experimental-test-coverage`,
  `flutter test --coverage`, `go test -cover`, `swift test --enable-code-coverage`,
  `python -m coverage` if installed, else the stdlib `python -m trace --summary --module unittest …`. Do not add
  a coverage plugin to the build or install tools globally unasked. If nothing can measure (e.g.
  `cargo llvm-cov` is not installed), say so and give a branch-by-branch estimate, labeled as an
  estimate — never present a guess as a measured number.
- **Every test that raises the number must still pass the "can this fail?" filter.** Assertion-free
  tests, getter tests, and tests that only execute a line without checking its effect do not count
  toward the floor — they are the way coverage gets gamed.
- **If the floor is not honestly reachable** — untestable-as-written code, defensive branches that
  cannot occur, platform-only paths — stop there. Report the achieved number, list each uncovered
  line with its reason, and propose the smallest production change that would unlock it. Do not
  pad, and do not change production code to hit the number.
- Exclude generated code (DTOs, `*.g.dart`, `BuildConfig`, serializers) from the denominator via the
  tool's exclude option rather than testing it.

## Operations

| Operation | User intent | Output |
|---|---|---|
| `unit` (default) | "write tests for this function/class" | Isolated tests with dependencies substituted, run and green, ≥80% coverage of the unit |
| `integration` | "test this end to end", "test the module together" | Tests across real collaborators — DB, HTTP, filesystem — with setup/teardown |
| `ui` | "test this screen/widget/view" | UI tests via the stack's UI harness; routes to the dedicated skill where one exists |
| `regression` | "write a test for the bug I just fixed" | One focused test that fails without the fix; then the touched file checked against the floor and topped up if it is below |
| `coverage` | "what is not tested", "raise coverage" | Coverage run, the result against the floor, and a ranked list of untested branches; tests written when the user asks for them or asks to raise coverage |

## Critical constraints

- **Never assert on invented behavior.** Read the implementation; if the intended behavior is
  genuinely ambiguous, ask rather than encoding a guess as an assertion. If the code looks wrong,
  do not enshrine the bug as expected behavior — report it.
- **Never write a test you have not run.** Report failures rather than hiding them.
- **Do not modify production code to make a test pass or to reach the coverage floor** — that
  inverts the point. Propose the change separately if the code is untestable.
- **Do not rewrite or "improve" the existing test suite** while adding tests to it.
- **Do not delete or weaken a failing test** you did not write. A red test is information.
- **No sleeps, no wall-clock dependence, no network in unit tests.** Flaky tests are worse than
  missing ones because they train people to ignore red.
- **Meet the floor with meaningful tests only.** Padding coverage with assertion-free or getter
  tests is worse than reporting an honest 70% with the reasons.
- **Never put real credentials, tokens, or production data in fixtures.** Test data is committed
  and public.
- **Do not commit.** Leave the new tests in the working tree for the user to review.

## References

- [test-design.md](references/test-design.md) — cross-cutting case selection, naming, fixtures vs fakes vs mocks, and how to read a coverage report
- [kotlin-kmp.md](references/kotlin-kmp.md) — `kotlin.test` and JUnit, source sets, `runTest`/`TestDispatcher`, Turbine, MockK, Kover
- [flutter-dart.md](references/flutter-dart.md) — routing to the dedicated Dart/Flutter skills, plus goldens and coverage
- [swift-apple.md](references/swift-apple.md) — Swift Testing, XCTest, XCUITest, async tests, `xccov`
- [rust-cpp.md](references/rust-cpp.md) — `cargo test`, doc-tests, `proptest`, `criterion`, `llvm-cov`; GoogleTest, Catch2, CTest
- [other-languages.md](references/other-languages.md) — Jest/Vitest/`node:test`, pytest/`unittest`, Go `testing`, plain JUnit
