---
name: error-debugging
description: "Analyze a stack trace, crash report, panic, or error log; find the failing frame and the root cause; then propose a fix and a way to verify it. Covers Kotlin/JVM/Android (coroutines, ANRs, R8-obfuscated traces), KMP/Compose Multiplatform, Flutter/Dart (FlutterError, RenderFlex overflow), Swift on iOS/macOS (.ips reports, EXC_BAD_ACCESS), Rust panics, C++ segfaults and sanitizer output, plus Python, JS/TS, Go and Java. Use when someone pastes a stack trace, crash log or panic — even with no question attached — or says 'why does this crash', 'what does this error mean', 'debug this exception', 'root-cause this trace', 'symbolicate this crash', 'deobfuscate this trace', or the Hungarian 'miért crashel', 'mit jelent ez a hiba', 'elemezd ezt a stack trace-t', 'nézd meg ezt a crash logot'. Not for auditing a whole project for latent bugs (that is code-analyzer), nor for a red CI run whose log has not been fetched yet (that is github-fix-action-error)."
category: debugging
risk: low
tags:
  - debugging
  - stacktrace
  - crash
  - root-cause
  - symbolication
  - kotlin
  - flutter
  - swift
  - rust
allowed-tools: Bash, Read, Grep, Glob, Edit, Write
argument-hint: "[stack trace, crash log, or path to a log/crash file]"
---

# error-debugging

## Purpose

Turn an error message into an explanation and a fix. The input is whatever the user has — a
stack trace, a crash report, a panic, a log excerpt, sometimes just a screenshot description.
The output is: which line actually failed, why it failed, what to change, and how to confirm
the change worked.

Most of the value is in the middle step. The frame that throws is rarely the frame that is
wrong — a `NullPointerException` in a rendering routine usually means something upstream
handed it a null it never should have had. Report the cause, not the symptom.

## When to use

- The user pastes a stack trace, crash report, panic, ANR, or error log — with or without a question
- The user asks what an error means, why an app crashes, or where a failure comes from
- A release-build trace needs deobfuscation or symbolication before it can be read
- A test failure, build failure, or runtime log needs root-causing

Not this skill:

- **Whole-project bug hunt with no specific failure** → `code-analyzer`
- **A failing GitHub Actions run you have not fetched yet** → `github-fix-action-error` (that skill fetches the run; come back here if its log needs deep trace analysis)

## Prerequisites

Before analyzing, establish two things.

**1. What platform produced this?** Detect from the shape of the trace, not from the user's
description — descriptions are often wrong or absent:

| Signal in the trace | Platform | Reference |
|---|---|---|
| `at com.foo.Bar.baz(Bar.kt:42)`, `Caused by:`, `FATAL EXCEPTION` | Kotlin / Java / Android | [kotlin-android-kmp.md](references/kotlin-android-kmp.md) |
| `kfun:`, `Uncaught Kotlin exception`, `kotlin.Throwable`, `ObjCException` | Kotlin/Native (KMP on iOS) | [kotlin-android-kmp.md](references/kotlin-android-kmp.md) |
| `androidx.compose.*`, `Snapshot`, "recomposition", `Composer` frames | Compose / CMP | [kotlin-android-kmp.md](references/kotlin-android-kmp.md) |
| `FlutterError`, `RenderFlex`, `package:flutter/src/...`, `<asynchronous suspension>` | Flutter / Dart | [flutter-dart.md](references/flutter-dart.md) |
| `Exception Type: EXC_BAD_ACCESS`, `Thread 0 Crashed:`, `.ips`, `libswiftCore.dylib` | Swift / Apple | [swift-apple.md](references/swift-apple.md) |
| `thread 'main' panicked at`, `note: run with RUST_BACKTRACE=1`, `core::panicking` | Rust | [rust-cpp.md](references/rust-cpp.md) |
| `SIGSEGV`, `AddressSanitizer:`, `#0 0x...`, `ndk-stack`, core dump | C / C++ / NDK | [rust-cpp.md](references/rust-cpp.md) |
| `Traceback (most recent call last)`, `at Object.<anonymous>`, `goroutine 1 [running]` | Python / JS / Go | [other-languages.md](references/other-languages.md) |

Load exactly one platform reference — the one that matches. Loading all of them wastes context
and mixes idioms that do not apply.

**2. Is the trace readable, or does it need symbolication first?**

Hex addresses, single-letter class names (`a.b.c`), `<optimized out>`, or missing line numbers
mean the trace is obfuscated or unsymbolicated. Analyzing it as-is produces confident nonsense.
Symbolicate first — see [symbolication.md](references/symbolication.md) for R8 mapping files,
dSYMs, `flutter symbolize`, `ndk-stack`, and `addr2line`.

If the required artifact (mapping file, dSYM, debug build) is missing, say so plainly, extract
whatever signal survives (exception type, thread state, top-level module), and tell the user what
to retrieve before a real diagnosis is possible.

## Workflow

### Step 1: Capture the full error

Get the complete trace, not the first three lines. Specifically make sure you have:

- The **exception type and message** verbatim
- The **full frame list**, including every `Caused by:` / `suppressed` / nested chain
- The **thread** it happened on (main/UI thread failures have different causes than background ones)
- **Context**: debug or release build, which device/OS, reproducible or intermittent, when it started

If the user pasted a truncated trace, ask for the rest — a middle section usually holds the
frame that matters. If the error lives in a file, read it rather than asking the user to paste:

```bash
# Keep log reading cheap — grep for the failure region instead of loading whole files
grep -n -A 40 -iE 'exception|fatal|panic|error|traceback' <logfile> | head -120
```

For Android, pull the trace directly:

```bash
adb logcat -d -b crash | tail -100
```

### Step 2: Symbolicate or deobfuscate if needed

Only when Step "Prerequisites 2" flagged it. Follow [symbolication.md](references/symbolication.md).
Do not skip ahead with an unreadable trace — every conclusion drawn from obfuscated frames is a
guess dressed up as an answer.

### Step 3: Locate the failing frame

Read the trace from the bottom up, then answer:

- **Where did it throw?** The topmost frame in the user's own code — not the framework frame
  above it. Framework frames tell you the mechanism; your frames tell you the mistake.
- **What is the deepest `Caused by:`?** In chained exceptions the last cause is usually the
  real one; the outer wrappers are transport.
- **Which frames belong to the project?** Filter to the app's package/module prefix. Everything
  else is context.

Then open the actual source at that line. Never diagnose from the trace alone when the code is
available:

```bash
# read the failing site plus the surrounding context
grep -n "<symbol>" -r <src-dir>
```

Use symbol-aware tools (Serena) to read the enclosing function and its callers instead of
reading whole files.

### Step 4: Trace back to the root cause

Work backwards from the failing line to the origin of the bad state. For each candidate cause,
you must be able to name the concrete value or condition that produced the failure.

Cross-cutting causes to consider, whatever the platform:

- **Null / absent value** — an optional unwrapped, a nullable dereferenced, a map lookup assumed present
- **Lifecycle / use-after-destroy** — the object was valid when captured, not when used
- **Concurrency** — a race, a torn read, an unsynchronized mutation, a deadlock, work on the wrong thread
- **Contract violation** — an API called out of order, in the wrong state, or off the required thread/actor
- **Resource exhaustion** — OOM, file descriptors, unbounded caches or collections
- **Boundary mismatch** — serialization, FFI, platform channels, JNI: data shaped differently on each side

Platform-specific pattern catalogs (swallowed `CancellationException`, `setState` during build,
main-actor violations, `RefCell` double borrow, use-after-free, …) live in the platform reference
loaded in Prerequisites.

Distinguish these two, and say which one you have:

- **Proximate cause** — the operation that threw (`list[3]` on a 2-element list)
- **Root cause** — why the state was wrong (the API returned fewer items than the caller assumed, and nothing validated it)

A fix applied at the proximate cause alone is usually a bug displacement, not a bug fix. Note
that explicitly when you propose one as a stopgap.

### Step 5: Verify the hypothesis before fixing

State the hypothesis as a falsifiable claim, then test it. Cheapest test first:

- Re-read the code path with the hypothesis in mind — does every frame in the trace fit?
- Check recent history for the same area: `git log -p -L <start>,<end>:<file> | head -80`, or `git log --oneline -- <file>`
- Add a temporary assertion/log at the suspected origin and reproduce
- Write a failing test that reproduces the crash — the best outcome, because it survives the fix as a regression guard

If the trace does **not** fully fit the hypothesis, the hypothesis is wrong. Say so and keep going
rather than shipping a plausible story.

### Step 6: Propose the fix

Deliver the analysis in this shape — short, ordered, skimmable:

```markdown
## What failed
<exception type + the failing line, as `path/to/File.kt:42`>

## Why
<root cause in 2–4 sentences: the bad state, where it came from, why it reached this line>

## Evidence
<the specific frames / code / history that support this, with file:line references>

## Fix
<the concrete change; a code sketch only when prose is not enough>

## Verify
<the command, test, or reproduction step that proves it — e.g. `./gradlew :app:testDebugUnitTest --tests '*FooTest*'`>

## Also worth checking
<other call sites with the same flaw, or the guard that would have caught this earlier — omit if none>
```

Apply the fix when the user asks for it. If they only asked what the error means, stop after
the analysis — do not start editing code.

### Step 7: Close the loop

After a fix is applied, run the project's own verification (test, build, analyzer) and report the
real result — including when it still fails. A fix that was not run is a proposal, not a fix.

If the same class of bug is likely elsewhere, mention it in one line. Do not expand into a
refactor of the surrounding module.

## Operations

The skill supports three modes; pick from what the user asked for:

| Operation | User intent | Output |
|---|---|---|
| `explain-error` | "what does this mean" | Steps 1–4, plain-language explanation, no code changes |
| `analyze` (default) | "why does this crash", bare trace paste | Steps 1–6, full report with proposed fix |
| `suggest-fixes` | "fix this" | Steps 1–7, applies the change and verifies it |

## Critical constraints

- **Never invent frames, line numbers, or file paths.** If the trace is truncated or obfuscated, say what is missing instead of filling the gap.
- **Symbolicate before analyzing** any release/obfuscated trace. An unsymbolicated diagnosis is a guess.
- **Read the actual source** at the failing line whenever the code is available. Trace-only analysis is for when the code is not.
- **Separate certainty levels.** Mark each conclusion as confirmed (you can point at the line), likely (fits the evidence, unverified), or speculative (needs more data). Do not present the third as the first.
- **One root cause per report.** If the trace shows several independent failures, treat them as separate analyses rather than blending them.
- **Do not paste raw logs back at the user.** Quote the handful of lines that carry the diagnosis.
- **Do not silently widen scope.** Fix the crash that was asked about; list adjacent issues, do not refactor them.
- **Never send crash logs, `.ips` files, or mapping files to an external service.** They routinely carry device identifiers, user paths, and internal symbol names.

## References

- [symbolication.md](references/symbolication.md) — deobfuscation and symbolication per platform; do this before analysis on release builds
- [kotlin-android-kmp.md](references/kotlin-android-kmp.md) — Kotlin/JVM, Android, coroutines, ANRs, Kotlin/Native, Compose & CMP
- [flutter-dart.md](references/flutter-dart.md) — FlutterError, render/layout errors, async gaps, platform channels
- [swift-apple.md](references/swift-apple.md) — `.ips` crash reports, exception types, Swift Concurrency, Objective-C exceptions
- [rust-cpp.md](references/rust-cpp.md) — Rust panics and error chains; C++ segfaults, core dumps, sanitizers, NDK
- [other-languages.md](references/other-languages.md) — Python, JavaScript/TypeScript, Go, Java-only traces
- [worked-examples.md](references/worked-examples.md) — sample traces with full analyses, one per platform
