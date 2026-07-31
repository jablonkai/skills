---
name: test-generation
description: "Write tests for existing code: unit tests, integration tests, UI tests, edge cases and error paths, plus coverage analysis to find what is still untested. Detects the project's test framework from its build files and follows that project's conventions — Kotlin/KMP (kotlin.test, coroutines-test, Turbine, MockK, Kover), Compose Multiplatform, Flutter/Dart, Swift (Swift Testing, XCTest, XCUITest), Rust (cargo test, proptest, criterion), C++ (GoogleTest, Catch2), and secondarily Jest/Vitest, pytest, Go and JUnit. Use when someone says 'write tests for this', 'add unit tests', 'test this function', 'add an integration test', 'scaffold a test suite', 'what is not covered', 'improve test coverage', 'write a regression test for this bug', or the Hungarian 'írj teszteket', 'teszteld le ezt a függvényt', 'mi nincs letesztelve'. Not for auditing a whole project for bugs and missing tests in general (that is code-analyzer), nor for diagnosing a crash or a failing test's root cause (that is error-debugging)."
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

# test-generation

## Purpose

Turn existing code into tests that would actually catch it breaking. The input is a function,
class, module, or bug report; the output is test files in the project's own framework, in the
right source set, that run and pass — plus a short statement of what is still untested.

The value is in case selection, not in typing. A test that only walks the happy path documents
the code; it does not defend it. Most real defects live at the boundaries and in the error paths,
so that is where the cases go.

## When to use

- "Write tests for `<file/function/class>`" — new or existing code
- A bug was just fixed and needs a regression test that fails without the fix
- A module has no tests and needs a suite scaffolded
- Coverage is low and the question is *what* to test next, not *how much*

Not this skill:

- **Whole-project audit that happens to mention missing tests** → `code-analyzer`
- **A test or app is failing and you need the root cause** → `error-debugging`
- **Setting up a test framework that does not exist in the project yet** → do that first (see the stack reference), then come back

## Route to a more specific skill first

Several stacks already have dedicated skills. When one applies, invoke it instead of
reimplementing its guidance here; use this skill for the surrounding decisions (which cases,
which source set, coverage) and only where no dedicated skill exists.

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
decided; matching them matters more than any convention in this skill.

```bash
# find the existing suite and its conventions
find . -type d \( -name test -o -name tests -o -name '*Test*' -o -name commonTest \) -not -path '*/build/*' -not -path '*/node_modules/*' | head -20
```

If there is no suite at all, say so — the first test in a project often needs a framework
dependency and a runner configuration, which is a larger change than the user may expect.

## Workflow

### Step 1: Read the code under test

Read the actual implementation, not just the signature. You are looking for the things a test can
assert on and the things that make it hard to test:

- **Contract** — inputs, outputs, thrown/returned errors, documented invariants
- **Branches** — every `if`, `when`/`switch`, early return, loop boundary, and `?:` fallback
- **Dependencies** — what has to be substituted (clock, network, filesystem, database, random)
- **State** — is the result a pure function of the inputs, or does it depend on prior calls?
- **Concurrency** — suspending functions, async/await, threads, actors, channels

Use symbol-aware tools (Serena) to read the enclosing symbol and its call sites rather than whole
files. Call sites show how the code is really used, which is where the realistic cases come from.

If the code is untestable as written (hard-wired singleton, hidden clock, constructor doing I/O),
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
confirm it fails against the unfixed code (or explain why that is not possible), then keep it.

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

Follow the conventions found in Step "Prerequisites 2" and the idioms in the stack reference:

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
first, then the full file — and fix what fails.

The stack reference has the exact command. Keep the output small: filter to failures rather than
pasting the whole run.

Then verify the tests are worth having: change the implementation in a way that should break a
test (mentally, or actually and revert) and confirm the right test would catch it. Report honestly
if a test passes against a deliberately broken implementation — that means it is asserting nothing.

### Step 6: Report coverage and the gaps

Run the project's coverage tool if it is configured (Kover, `flutter test --coverage`, `xccov`,
`cargo llvm-cov`, `gcov`/`llvm-cov`, or the JS/Python equivalents — see the stack reference). If it
is not configured, do not add it unasked; report the gaps by reading the branches instead.

Report the gaps, not the percentage:

```markdown
## Tests added
<file paths, and one line per behavior covered>

## Verification
<command run, and the real result>

## Still untested
<specific branches or paths, as `file:line` — with why, if there is a reason>
```

Coverage is a way of finding untested branches, not a target. Do not add tests whose only purpose
is to raise the number.

## Operations

| Operation | User intent | Output |
|---|---|---|
| `unit` (default) | "write tests for this function/class" | Isolated tests with dependencies substituted, run and green |
| `integration` | "test this end to end", "test the module together" | Tests across real collaborators — DB, HTTP, filesystem — with setup/teardown |
| `ui` | "test this screen/widget/view" | UI tests via the stack's UI harness; routes to the dedicated skill where one exists |
| `regression` | "write a test for the bug I just fixed" | One focused test that fails without the fix |
| `coverage` | "what is not tested" | Coverage run plus a ranked list of untested branches; tests only if asked |

## Critical constraints

- **Never assert on invented behavior.** Read the implementation; if the intended behavior is
  genuinely ambiguous, ask rather than encoding a guess as an assertion.
- **Never write a test you have not run.** Report failures rather than hiding them.
- **Do not modify production code to make a test pass** — that inverts the point. Propose the
  change separately if the code is untestable.
- **Do not rewrite or "improve" the existing test suite** while adding tests to it.
- **Do not delete or weaken a failing test** you did not write. A red test is information.
- **No sleeps, no wall-clock dependence, no network in unit tests.** Flaky tests are worse than
  missing ones because they train people to ignore red.
- **Do not chase a coverage number.** Assertion-free tests and getter tests inflate coverage and
  defend nothing.
- **Never put real credentials, tokens, or production data in fixtures.** Test data is committed
  and public.

## References

- [test-design.md](references/test-design.md) — cross-cutting case selection, naming, fixtures vs fakes vs mocks, and how to read a coverage report
- [kotlin-kmp.md](references/kotlin-kmp.md) — `kotlin.test` and JUnit, source sets, `runTest`/`TestDispatcher`, Turbine, MockK, Kover
- [flutter-dart.md](references/flutter-dart.md) — routing to the dedicated Dart/Flutter skills, plus goldens and coverage
- [swift-apple.md](references/swift-apple.md) — Swift Testing, XCTest, XCUITest, async tests, `xccov`
- [rust-cpp.md](references/rust-cpp.md) — `cargo test`, doc-tests, `proptest`, `criterion`, `llvm-cov`; GoogleTest, Catch2, CTest
- [other-languages.md](references/other-languages.md) — Jest/Vitest, pytest, Go `testing`, plain JUnit
