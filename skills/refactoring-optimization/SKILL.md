---
name: refactoring-optimization
description: "Improve the structure of working code without changing what it does: extract duplication, break up complex functions, remove dead code, replace magic numbers, fix misleading names, and modernize to the language's idioms — each step verified against the tests. Detects the stack from its build files and leans on the project's own linter (detekt/ktlint, dart analyze, SwiftLint, cargo clippy, clang-tidy). Use when someone says 'refactor this', 'clean this up', 'this function is too long', 'there's a lot of copy-paste here', 'remove the dead code', 'simplify this', 'make this more idiomatic', 'reduce the complexity', or the Hungarian 'refaktoráld ezt', 'tisztítsd meg ezt a kódot', 'túl bonyolult ez a függvény', 'sok itt a duplikáció'. This is the apply counterpart to code-analyzer's detect: that skill finds what is wrong across a project, this one changes it. Not for fixing a bug or crash (that is error-debugging), nor for writing the tests a refactoring needs (that is test-generation)."
summary: "behavior-preserving refactoring — duplication extraction, complexity reduction, dead-code removal, naming and idiom cleanups, driven by each stack's own linter and verified step by step against the tests"
category: code-quality
risk: low
tags:
  - refactoring
  - code-quality
  - complexity
  - dead-code
  - linting
  - kotlin
  - flutter
  - swift
  - rust
  - cpp
allowed-tools: Bash, Read, Grep, Glob, Edit, Write, Skill
argument-hint: "[file, function, class, or module to refactor]"
---

# refactoring-optimization

## Purpose

Change the shape of working code without changing what it does. The input is code that is hard to
read, hard to change, or repeated in four places; the output is the same behavior in a better
structure, with the tests still green after every step and a diff a reviewer can actually follow.

The discipline is the whole point. Anyone can rewrite a function so it reads better; the hard part
is proving it still does the same thing. So the ordering here is always the same — establish a
safety net, make one small reversible change, verify, repeat — and the value of the skill is in
refusing to skip that, not in knowing clever refactorings.

This is the *apply* half of a pair. `code-analyzer` surveys a project and reports what is wrong;
this skill takes one of those findings and actually changes the code.

## When to use

- A function has grown past what anyone can hold in their head and needs decomposing
- The same logic exists in three or four places and they have started to drift apart
- Code is unreachable or unreferenced and nobody dares delete it
- Names, magic numbers, or boolean flag parameters make call sites unreadable
- The code predates a language feature that would express it far more directly
- A refactoring is the prerequisite for a feature — untangle first, then add

Not this skill:

- **Finding out what is wrong across a whole project** → `code-analyzer`, then come back here
- **Fixing a bug, crash, or failing test** → `error-debugging` (that changes behavior, by design)
- **Writing the tests this refactoring needs as a safety net** → `test-generation`, first
- **Tidying code you just wrote in this session** → the built-in `simplify` skill is lighter weight
- **Making code faster** → measure first; see [performance](#a-note-on-optimization) below

## Route to a more specific skill first

Several stacks have dedicated skills for exactly the restructuring being asked for. When one
applies, invoke it rather than reimplementing its guidance; use this skill for the surrounding
discipline — safety net, ordering, verification, rollback.

| Situation | Skill to invoke |
|---|---|
| Compose state in the wrong place, stateful screen mixed with UI | `compose-state-hoisting`, `compose-state-holder-ui-split` |
| Compose component with boolean flags instead of content slots | `compose-slot-api-pattern` |
| Compose modifier chains, layout wrappers, hardcoded roots | `compose-modifier-and-layout-style` |
| Compose recomposing too often | `compose-recomposition-performance`, `compose-stability-diagnostics` |
| Kotlin coroutine scope and cancellation structure | `kotlin-coroutines-structured-concurrency` |
| Kotlin primitive obsession in domain types | `kotlin-types-value-class` |
| Dart mechanical lint fixes (`dart fix --apply`) | `dart-run-static-analysis` |
| Dart if/else chains that want to be pattern matches | `dart-use-pattern-matching` |
| Flutter widget tree restructuring, overflow, nesting | `flutter-fix-layout-issues` |
| Flutter layering and state management cleanup | `flutter-apply-architecture-best-practices` |

Swift, Rust, C++, and plain Kotlin/JVM have no dedicated skill — this one covers them directly.

## Prerequisites

**1. Is there a safety net?** Refactoring without one is rewriting and hoping. Before the first
edit, three things need to be true:

- **The tests pass now.** A green baseline is what makes "the tests went red" mean something. If
  they are already red, stop — fix or quarantine that first, or the signal is worthless.
- **The working tree is clean and committed.** Rollback is `git checkout` only if there is
  something to roll back to. Refactoring on top of uncommitted work destroys it.
- **The code under change is covered.** Not the whole project — the specific behavior being
  restructured. If it is not, say so and offer to write characterization tests first
  (`test-generation`) rather than proceeding blind.

When no tests exist and the user wants to proceed anyway, that is their call — but make the risk
explicit, keep the steps smaller than usual, and lean harder on the compiler and the linter.

**2. What stack is this?** Detect from build files, not file extensions — the linter, the idioms,
and the reference-checking tools are declared there.

| Build file / signal | Stack | Reference |
|---|---|---|
| `build.gradle.kts` with `kotlin("multiplatform")`, `commonMain` | Kotlin Multiplatform / CMP | [kotlin-kmp.md](references/kotlin-kmp.md) |
| `build.gradle(.kts)` with `com.android.application` | Kotlin/JVM, Android | [kotlin-kmp.md](references/kotlin-kmp.md) |
| `pubspec.yaml` | Flutter / Dart | [flutter-dart.md](references/flutter-dart.md) |
| `Package.swift`, `*.xcodeproj`, `*.xcworkspace` | Swift (iOS/macOS) | [swift-apple.md](references/swift-apple.md) |
| `Cargo.toml` | Rust | [rust-cpp.md](references/rust-cpp.md) |
| `CMakeLists.txt`, `conanfile.txt`, `*.cpp` | C / C++ | [rust-cpp.md](references/rust-cpp.md) |
| `package.json`, `pyproject.toml`, `go.mod`, `pom.xml` | JS/TS, Python, Go, Java | [other-languages.md](references/other-languages.md) |

Load exactly one stack reference. Mixing idioms from languages that are not in play produces
suggestions that read as wrong to everyone who works in the codebase.

**3. Who else is in this file?** A large refactoring on a file with open pull requests against it
turns into a merge conflict that costs more than the cleanup saved. Check before starting:

```bash
git log --since='2 weeks ago' --oneline -- <path>   # recent churn
git branch -a --contains HEAD >/dev/null 2>&1        # and any open branches touching it
```

If the file is hot, prefer several small landed refactorings over one large one.

## Workflow

### Step 1: Find the smells with tools, not by reading

Every stack ships a linter that already knows its own smells, and it will be more thorough and
less opinionated than a manual read. Run it first and let it set the agenda — the stack reference
has the exact command and the rules worth enabling.

Then look for the things linters are bad at, which is mostly duplication with variation and
structure that is wrong rather than ugly:

| Smell | What to look for | Usual refactoring |
|---|---|---|
| Duplication | The same 5+ lines in 3+ places, or near-copies that drifted | Extract function/class, or parameterize the difference |
| Long function | More than one reason to change; needs comments to be followable | Extract the named steps |
| Deep nesting | 3+ levels of `if`/`for`; the happy path is at the bottom | Guard clauses, early return, invert conditions |
| Long parameter list | 5+ parameters, or several booleans in a row | Introduce a parameter object; split the function per flag |
| Magic values | Unexplained literals, repeated string keys | Named constant, enum, or sealed type |
| Misleading name | The name says less or other than what the code does | Rename — reference-aware, never by find/replace |
| Dead code | Unreferenced symbols, unreachable branches, stale flags | Delete, once references are actually proven absent |
| Primitive obsession | `String` id, `Int` money, `Long` timestamp everywhere | Value/wrapper type |
| Feature envy | A function that mostly touches another type's data | Move it to that type |

Smell-to-refactoring detail, and the mechanics of each refactoring, live in
[refactoring-catalog.md](references/refactoring-catalog.md) — load it when the right move is not
obvious from the smell.

### Step 2: Order the work safe → complex

Refactorings differ enormously in risk, and the order changes how much of the work survives review.
Do the mechanical ones first: they are individually verifiable, they shrink the code, and they often
make the structural problems visible enough that the harder decisions become obvious.

1. **Automated and reversible** — formatter, `dart fix --apply`, `cargo clippy --fix`, IDE-grade
   renames. Machine-checked, and worth landing on their own so they do not drown the real diff.
2. **Local and contained** — extract a function, introduce a constant, add guard clauses. One
   file, no callers affected.
3. **Structural within a module** — extract a class, move a method, introduce a parameter object.
   Callers change, but all of them are in the repo and the compiler finds them.
4. **Cross-cutting** — changing a public API, hoisting platform code into `commonMain`, replacing
   an abstraction. Needs a caller inventory before the first edit, and is usually worth splitting
   across several changes.

Present this plan before editing anything past level 1. A refactoring plan the user rejects after
the fact is wasted work; one they redirect early is cheap.

### Step 3: Apply one refactoring at a time

The unit of work is one refactoring, not one file and not one session. Between them the code
compiles and the tests pass — that invariant is what makes a mistake cost minutes instead of a day.

- **Preserve behavior exactly**, including the behavior nobody meant: error messages, ordering,
  null/empty handling, overflow, logging that something else parses. If you believe a behavior is a
  bug, that is a separate change — report it, do not quietly correct it under cover of a refactor.
- **Change structure or behavior, never both in one step.** Mixed diffs are unreviewable, and when
  something breaks there is no way to tell which half did it.
- **Use reference-aware tools** for renames and moves (Serena's `rename_symbol`, `safe_delete_symbol`,
  `find_referencing_symbols`; the IDE's refactorings). Text search misses dynamic references and hits
  unrelated matches in comments and strings.
- **Do not reformat what you did not change.** A whitespace-only change to 400 unrelated lines hides
  the twelve that matter.
- **Leave the code more consistent than you found it.** A "better" pattern used once, differing from
  the surrounding twenty call sites, makes the codebase harder to read, not easier.

### Step 4: Verify after every step

Run the tests after each refactoring, not once at the end. The stack reference has the command;
keep the output filtered to failures.

Beyond green tests, three checks catch what tests miss:

- **The compiler/linter is quiet** — new warnings after a refactor usually mean something was left
  half-moved.
- **The diff is only what you intended.** Read `git diff` before moving on. Unintended edits are
  common and cheap to catch here, expensive to catch in review.
- **The public API is unchanged**, or the change was deliberate and every caller is updated. For a
  published library, callers outside the repo cannot be found by the compiler — check the stack
  reference for the binary-compatibility tooling.

If a test goes red, revert that step rather than debugging forward. The step was small by
construction, so re-doing it correctly is cheaper than repairing it — and a refactoring that needs
debugging was not a refactoring.

### Step 5: Report what changed and what you left alone

```markdown
## Refactorings applied
<one line per refactoring: what moved/merged/was deleted, and why it is better>

## Verification
<command run, and the real result — after which step>

## Behavior preserved
<how you know: tests, compiler, caller inventory>

## Left alone
<smells found but not addressed — as `file:line` — with the reason>

## Found while refactoring
<bugs or surprises discovered, reported not fixed>
```

The last two sections are where the value accumulates. A refactoring that also silently fixed a bug
is a change nobody can review, and a smell you deliberately left is information the next person
needs.

## A note on optimization

"Optimize" means two different things and they need different discipline. Structural cleanup —
everything above — is safe and reversible. Performance work is not: it trades readability for speed
and is often wrong about where the time goes.

So when the request is about speed, measure first. Profile, find the actual hot path, change that
one thing, and measure again. An optimization without a before-and-after number is a readability
regression with no proven benefit — and the stack references list each language's profiler for
exactly this reason. Algorithmic complexity in a hot loop is worth fixing on sight; everything else
waits for data.

## Operations

| Operation | User intent | Output |
|---|---|---|
| `refactor` (default) | "clean this up", "refactor this function" | Behavior-preserving edits, verified step by step |
| `plan` | "what should we refactor first" | Ranked, ordered plan with risk per step; no edits |
| `duplicates` | "there is a lot of copy-paste here" | Duplication located, shared abstraction extracted where it earns its place |
| `simplify` | "this function is too complex" | Decomposition into named steps, nesting flattened |
| `deadcode` | "remove the unused code" | Reference-verified deletions, with the dynamic-reference caveats stated |
| `rename` | "these names are confusing" | Reference-aware renames across declarations and call sites |
| `modernize` | "make this idiomatic" | Linter-driven idiom cleanups for the stack's current language version |

## Critical constraints

- **Never change behavior during a refactoring.** This is the one rule the whole practice rests on:
  if behavior may change, it is a rewrite, and it needs to be reviewed and tested as one.
- **Never refactor on a red or unknown baseline.** Without a green starting point there is no way to
  attribute a failure, and the refactoring gets blamed for a bug it merely revealed.
- **Never delete code you cannot prove is unreferenced.** Reflection, dependency injection,
  serialization, platform entry points, and build-flavor-specific code are invisible to a text
  search — the stack reference lists what each one hides.
- **Do not refactor and add a feature in the same change.** Reviewers cannot separate them, and
  neither can `git bisect`.
- **Do not touch generated code.** Fix the generator or the template; regenerated output overwrites
  edits and the diff misleads everyone.
- **Do not extract an abstraction from two occurrences.** Duplication is cheaper than the wrong
  abstraction — the third occurrence is what reveals which parts actually vary.
- **Do not optimize without a measurement.** See above; unmeasured performance work usually costs
  clarity and buys nothing.
- **Do not chase a metric.** Cyclomatic complexity and line counts point at code worth *looking* at;
  they are not the goal, and code can be split into eight functions that are collectively worse.
- **Do not restructure a public API without a caller inventory** covering consumers outside the
  repo. Inside the repo the compiler is the inventory; outside it, nothing is.
- **Stop and ask when the "right" structure is a judgment call** — layering, module boundaries, and
  abstraction choices encode intent this skill cannot recover from the code alone.

## References

- [refactoring-catalog.md](references/refactoring-catalog.md) — smell-to-refactoring map, the mechanics of each refactoring, characterization tests, and rollback
- [kotlin-kmp.md](references/kotlin-kmp.md) — Kotlin and Android idioms, detekt/ktlint, KMP `commonMain` hoisting and `expect`/`actual` trimming, Compose routing, binary compatibility
- [flutter-dart.md](references/flutter-dart.md) — `dart analyze`/`dart fix`, widget extraction vs helper methods, `const` constructors, disposal, nesting
- [swift-apple.md](references/swift-apple.md) — SwiftLint, protocol extraction, `guard` early returns, SwiftUI view decomposition, `@MainActor` and concurrency hygiene
- [rust-cpp.md](references/rust-cpp.md) — `cargo clippy` and `--fix`, iterator chains, `?` over nested matches, trimming `clone()`/`unwrap()`; RAII, smart pointers, `const`-correctness, clang-tidy
- [other-languages.md](references/other-languages.md) — JS/TS, Python, Go and Java tooling and idioms, for when a project needs them
