# Refactoring Kotlin, Android, KMP and Compose

Tooling, idioms, and the multiplatform-specific refactorings. Compose has its own dedicated skills —
route to them rather than duplicating their guidance here.

## Contents

- [Tooling](#tooling)
- [Kotlin idioms worth refactoring toward](#kotlin-idioms-worth-refactoring-toward)
- [Idioms worth refactoring away from](#idioms-worth-refactoring-away-from)
- [Kotlin Multiplatform](#kotlin-multiplatform)
- [Compose and Compose Multiplatform](#compose-and-compose-multiplatform)
- [Android specifics](#android-specifics)
- [Dead code in Kotlin](#dead-code-in-kotlin)
- [Verification](#verification)

## Tooling

Run the linters first — they set the agenda, and their findings are pre-justified by a rule name the
team already agreed to.

```bash
./gradlew detekt                    # complexity, long methods, long parameter lists, dead code
./gradlew ktlintCheck               # formatting and naming; ktlintFormat applies fixes
./gradlew lint                      # Android Lint — API misuse, resource and performance issues
./gradlew compileKotlin --console=plain 2>&1 | grep -E 'warning|error'
```

Useful detekt rules for this work, if not already on: `LongMethod`, `LongParameterList`,
`CyclomaticComplexMethod`, `NestedBlockDepth`, `MagicNumber`, `UnusedPrivateMember`,
`UnusedImports`, `TooManyFunctions`. Prefer raising an existing threshold conversation over
suppressing findings — a suppression is a decision that outlives the person who made it.

Add `-Werror` locally (not permanently) to surface deprecations that mark exactly the code worth
modernizing:

```bash
./gradlew compileKotlin -Pkotlin.compiler.execution.strategy=in-process --console=plain
```

## Kotlin idioms worth refactoring toward

These are the changes that make Kotlin read like Kotlin. Each is behavior-preserving; verify anyway.

| Instead of | Prefer | Why |
|---|---|---|
| `if (x != null) { x.f() }` | `x?.f()`, `x?.let { }` | Removes a nesting level and the shadowed name |
| Nested `if` chains | Guard clauses with `return`/`?: return` | Puts the happy path at the top level |
| `when` on a type tag with an `else` | Sealed class/interface, exhaustive `when` without `else` | The compiler now finds every site when a case is added |
| A `Util` object of static helpers | Extension functions on the receiver type | Discoverable at the call site, no import of a bag |
| `data class` used only as an id carrier | `@JvmInline value class` | Type safety with no allocation — see `kotlin-types-value-class` |
| Manual builder chains and `apply`-less setup | `apply`/`also` for configuration | Keeps the subject implicit and the block cohesive |
| Boolean parameters at call sites | Two named functions, or a sealed/enum parameter | `f(true, false)` is unreadable and unsearchable |
| `List<Pair<A, B>>` and nested generics | A named type | Names are the cheapest documentation |
| Manual loops building a list | `map`/`filter`/`fold`, `buildList` | Fewer mutable intermediates; intent is visible |
| Callback interfaces | `suspend` functions or `Flow` | Removes inversion of control and manual cancellation |
| `GlobalScope`, ad-hoc `CoroutineScope()` | Structured concurrency — see `kotlin-coroutines-structured-concurrency` | Cancellation and lifetime become correct by construction |
| `runBlocking` inside library/production code | `suspend` all the way up | `runBlocking` reintroduces the blocking it was meant to remove |

Two cautions. Chained sequence operations are elegant but allocate an intermediate collection per
step — on a hot path, `asSequence()` or a plain loop is the honest choice. And scope functions
nested more than one deep (`let` inside `apply` inside `run`) are harder to read than the code they
replaced; that is not a Kotlin idiom, it is a puzzle.

## Idioms worth refactoring away from

- **`!!`** — every one is an assertion with no message. Replace with `?: error("...")` carrying the
  reason, a guard clause, or a redesign that makes the nullability impossible.
- **Platform types crossing into Kotlin** — annotate or wrap at the Java boundary rather than
  letting `String!` propagate.
- **`lateinit` used for what is really nullable state** — it converts a null check into a crash.
- **`Any` and unchecked casts** — usually a missing sealed hierarchy or generic parameter.
- **Companion-object singletons holding mutable state** — invisible coupling and a test hazard;
  inject instead.

## Kotlin Multiplatform

The refactoring that pays for itself repeatedly in KMP is **hoisting duplicated platform code into
`commonMain`**.

Procedure, keeping every target compiling:

1. Diff the `androidMain` and `iosMain` implementations. Identify the part that is genuinely
   identical — usually most of the logic, with a thin platform-specific edge (filesystem paths,
   clock, crypto provider, HTTP engine).
2. Move the shared part into `commonMain` as an ordinary function or class.
3. Leave only the true platform edge behind the `expect`/`actual` boundary, and make that edge as
   small as possible — ideally one function, not a whole class.
4. Compile **every** target, not just the one you are working in: `./gradlew build` or the
   per-target compile tasks. A common-source change that breaks only `iosMain` is invisible until
   the iOS target compiles.

The inverse refactoring matters too: **trim `expect`/`actual` pairs that no longer need to exist**.
An `expect` declaration that has identical `actual` bodies on every target is pure ceremony — delete
it and put the body in `commonMain`. Likewise, prefer an interface with platform implementations
injected at the composition root over `expect`/`actual` when the abstraction is about behavior
rather than about platform APIs: it is testable, and it does not force every consumer through the
multiplatform mechanism.

Source-set placement rules of thumb:

| Code | Belongs in |
|---|---|
| Pure logic, models, use cases, serialization | `commonMain` |
| Anything with a `java.*`, `android.*`, `platform.*` or `NS*` reference | the platform source set |
| Shared between two platforms but not all | an intermediate source set, not duplicated |

## Compose and Compose Multiplatform

Do not reimplement the Compose guidance here — the dedicated skills are more precise and are kept
current:

| Refactoring | Skill |
|---|---|
| State in the wrong place; local `remember` vs hoisted vs ViewModel | `compose-state-hoisting` |
| A screen composable that both collects state and renders layout | `compose-state-holder-ui-split` |
| Boolean/`enum` flags controlling which children render | `compose-slot-api-pattern` |
| Modifier chain order, layout wrappers, hardcoded root layouts | `compose-modifier-and-layout-style` |
| Recomposing too often; unstable parameters | `compose-recomposition-performance`, `compose-stability-diagnostics` |
| Frame-rate state read in composition | `compose-state-deferred-reads` |
| `LaunchedEffect`/`DisposableEffect` misuse | `compose-side-effects` |

The refactoring that is *not* covered there and belongs here: extracting a large composable into
smaller ones. The rule is the same as for any function — extract along the axis of change, give the
extracted composable a name describing what it shows, and keep it stateless (parameters in, events
out) so it stays previewable and testable. Extracting into a private composable is nearly always
better than extracting into a helper that returns a `@Composable` lambda, which defeats the
compiler's skipping analysis.

## Android specifics

- **God Activity/Fragment** — extract the non-UI logic into a ViewModel or plain state holder first;
  that single move usually resolves the complexity findings without touching the UI.
- **`findViewById` chains and manual view state** — if the file is being restructured anyway, this
  is the moment to consider Compose, but that is a rewrite, not a refactoring — flag it as such.
- **Long-lived context references** — a refactoring that moves code into a longer-lived object can
  silently create a leak. Check what holds a `Context` after any move.
- **Resource and manifest references** — Android Lint catches unused resources
  (`./gradlew lintDebug`), but layout/ids referenced only from XML or data binding are easy to
  delete wrongly.

## Dead code in Kotlin

Beyond the generic invisible-reference list, Kotlin and Android add these:

- Anything annotated `@Keep`, or matched by a ProGuard/R8 `-keep` rule — kept precisely because
  something reflects on it
- `@Serializable` properties and constructors, read by name at runtime
- Hilt/Koin/Dagger-provided types with no direct constructor call
- `@Composable` previews, `@Test` functions, and `@JvmStatic`/`@JvmName` entry points used from Java
- Manifest-declared components, and anything referenced only from a non-default build flavor or
  another target's source set

Use `find_referencing_symbols` for the symbolic check, then grep for the name as a string.

## Verification

```bash
./gradlew test --console=plain                  # JVM/common unit tests
./gradlew allTests --console=plain              # every KMP target
./gradlew connectedDebugAndroidTest             # instrumented, when the change touches Android UI
./gradlew build --console=plain                 # compiles all targets and source sets
```

Filter the output rather than pasting it; Gradle logs are the fastest way to lose a context window.

For a published library, add binary-compatibility checking before any public-API restructuring —
`binary-compatibility-validator` (`./gradlew apiCheck`) turns "did I break downstream consumers"
from a guess into a build failure, and `apiDump` records a deliberate change.
