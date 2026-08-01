# Refactoring Swift (iOS / macOS)

Tooling, Swift idioms, SwiftUI view decomposition, and the concurrency hygiene that Swift 6 makes
unavoidable.

## Contents

- [Tooling](#tooling)
- [Swift idioms worth refactoring toward](#swift-idioms-worth-refactoring-toward)
- [Guard clauses and early return](#guard-clauses-and-early-return)
- [Protocol extraction](#protocol-extraction)
- [SwiftUI view decomposition](#swiftui-view-decomposition)
- [Concurrency hygiene](#concurrency-hygiene)
- [Dead code in Swift](#dead-code-in-swift)
- [Verification](#verification)

## Tooling

```bash
swiftlint                          # style, complexity, force-unwrap, file/type length
swiftlint --fix                    # applies the auto-correctable subset
swift-format lint -r Sources/      # or the project's formatter
swift build 2>&1 | grep -E 'warning|error'
xcodebuild -quiet -scheme <S> build 2>&1 | grep -E 'warning:|error:'
```

SwiftLint rules that map directly onto the smells in this skill: `cyclomatic_complexity`,
`function_body_length`, `type_body_length`, `function_parameter_count`, `nesting`,
`force_unwrapping`, `force_try`, `large_tuple`, `unused_declaration` (requires the analyze mode
below), `redundant_optional_initialization`.

`swiftlint analyze` finds unused declarations, but needs a compiler log:

```bash
xcodebuild -scheme <S> -destination '<D>' clean build \
  OTHER_SWIFT_FLAGS="-D DEBUG" > /tmp/xcodebuild.log
swiftlint analyze --compiler-log-path /tmp/xcodebuild.log
```

Also turn on the compiler's own upcoming-feature and strict-concurrency warnings while refactoring —
they mark exactly the code that will need to change anyway:

```swift
// Package.swift
swiftSettings: [.enableUpcomingFeature("StrictConcurrency")]
```

## Swift idioms worth refactoring toward

| Instead of | Prefer | Why |
|---|---|---|
| `if let x = x { ... }` wrapping the body | `guard let x else { return }` | Happy path at the top level, no shadowed pyramid |
| `!` force unwrap and `try!` | `guard`, `??`, `throws` | Each `!` is an unlabeled crash site |
| Long `if`/`else if` on an enum or type | `switch` without `default` | Exhaustiveness — the compiler finds every site when a case is added |
| Class with no inheritance and no identity | `struct` | Value semantics remove a whole class of aliasing bugs |
| Stringly-typed keys and identifiers | Enum, or a `RawRepresentable` wrapper | Typos become compile errors |
| Manual loops accumulating a result | `map`/`filter`/`reduce`/`compactMap` | Intent visible, no mutable intermediate |
| Nested closures with `[weak self] guard let self` repeated | `async`/`await` | Removes the retain-cycle ceremony entirely |
| Completion-handler APIs | `async` functions, `AsyncSequence` | Errors flow through `throws` instead of a result enum |
| A large type in one file | `extension`s grouped by responsibility, or an extracted type | Extensions are free and make the axis of change visible |
| Boolean parameters | Enum parameter or two named functions | `configure(true, false)` is unreadable at the call site |
| Singletons reached directly | Injected dependency, protocol-typed | Testability, and the coupling becomes visible |

Note that `NSObject` subclasses, Objective-C interop, `@objc` members, and anything KVO observes
cannot become a `struct` — check before converting.

## Guard clauses and early return

Swift's `guard` exists for this refactoring, which makes it the highest-yield mechanical cleanup in
the language. Take the outermost condition wrapping the whole body, invert it into a `guard` with an
early `return`/`throw`, and dedent. Repeat until the happy path is unindented.

Two Swift-specific cautions: `guard` requires the else branch to exit scope, so a condition whose
failure path has real work is a `switch` or an `if`, not a `guard`; and in `deinit` or code with
manual cleanup, an early return can skip work that a `defer` should be holding instead.

## Protocol extraction

The usual reasons to extract a protocol from a concrete type: to make a dependency substitutable in
tests, or to allow a second implementation. Both are real, but the refactoring is over-applied —
a protocol with exactly one conformer and no test double is speculative generality, and inlining it
away is itself a valid refactoring.

When it does earn its place:

1. Declare the protocol with only the members the *caller* uses — not everything the type exposes.
   A protocol mirroring the whole type is a rename, not an abstraction.
2. Conform the existing type: `extension ExistingType: NewProtocol {}`. No members move. Compile.
3. Change the consumer's stored property/parameter type to the protocol. Compile.
4. Only now write the second conformer or the test double.

Prefer protocol witnesses over class inheritance for sharing behavior, and prefer generic
constraints (`some Protocol`) over existential `any Protocol` where the concrete type is known —
existentials box and cost dynamic dispatch on a hot path.

## SwiftUI view decomposition

A long `body` is the SwiftUI equivalent of a long function, and the same fix applies — but the
mechanism matters:

- **Extract a `View` struct**, not a computed `var` or a function returning `some View`, when the
  subtree is a real component. A separate struct gets its own identity in the view graph, its own
  dependency tracking, and can be previewed and tested in isolation.
- **A computed `var someSection: some View` is fine** for a small piece used once inside the same
  view — it keeps the code readable without inventing a type. The distinction is reuse and identity:
  if it has state, is used more than once, or would benefit from a `#Preview`, make it a struct.
- **Pass the minimum.** A subview taking the whole view model re-renders on every unrelated change;
  one taking the two values it displays does not.
- **Keep extracted views stateless** where possible — values in, closures out. That is what makes
  them previewable, and it puts the state ownership question where it belongs.
- **Move `@State` down, not up.** State that only one subview reads belongs in that subview; hoisting
  it to the parent widens the invalidation scope.
- **`ViewBuilder` parameters instead of boolean flags** — a view configured by `showsHeader: Bool`
  wants a `header: () -> Header` slot.

Watch for identity changes while restructuring: adding or removing a container, or changing where a
`ForEach` id comes from, can reset `@State` and restart animations. That is a behavior change, and
it is the one this refactoring most often causes accidentally.

## Concurrency hygiene

Under Swift 6 strict concurrency, restructuring code frequently moves it across an isolation
boundary — which is a behavior change even when the code looks identical.

- **`@MainActor` belongs on the type or member that genuinely touches UI**, not sprinkled to silence
  diagnostics. A blanket `@MainActor` on a model type serializes work that had no reason to be on
  the main thread.
- **When extracting from a `@MainActor` context**, decide deliberately whether the extracted function
  is main-actor-isolated or `nonisolated`. Defaulting to inherited isolation silently keeps work on
  the main thread; marking it `nonisolated` silently moves it off. Both can be wrong.
- **`Task { }` inherits actor context; `Task.detached` does not.** Swapping one for the other during
  a cleanup changes which thread the body runs on and whether cancellation propagates.
- **Prefer `async let` and `TaskGroup`** over manually orchestrated `Task`s with shared mutable
  state — structured concurrency makes cancellation and lifetime correct by construction.
- **`Sendable` conformance is a claim, not a formality.** Adding `@unchecked Sendable` to make a
  refactoring compile trades a compile error for a data race.

## Dead code in Swift

Beyond the generic invisible-reference list, Apple platforms hide references in:

- `@objc` members reached by selector, target/action, KVO, and `NSSelectorFromString`
- Storyboard, XIB, and `@IBAction`/`@IBOutlet` connections — text references in XML, invisible to
  the compiler
- `Info.plist` principal classes, `NSExtension` entry points, app/scene delegates
- `#selector` and `#keyPath` string forms
- `Codable` properties, decoded by name
- App extensions, widgets, intents, and other targets that compile separately — a symbol unused in
  the app target may be the widget's entry point
- `@_cdecl`, `@_silgen_name`, and anything exported to C/Objective-C

`swiftlint analyze --compiler-log-path` is the tool, but treat its findings as candidates, not
conclusions — it cannot see the XML or the plists.

## Verification

```bash
swift build && swift test                            # SwiftPM
xcodebuild -quiet -scheme <S> -destination '<D>' test # Xcode project or workspace
xcodebuild -quiet -scheme <S> -destination '<D>' build -configuration Release
```

Build every target, not just the app: extensions, widgets, and test targets compile separately and
are where a moved symbol most often goes missing. Build Release as well as Debug — `#if DEBUG` code
hides compile errors from a Debug-only build.

For a published Swift package, restructuring public API breaks source compatibility for consumers
the compiler cannot see. Check the package's declared API surface and semantic version before
changing anything `public`, and prefer `@available(*, deprecated)` with a migration path over
removal.
