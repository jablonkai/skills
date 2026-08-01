# Refactoring Flutter and Dart

Tooling, Dart idioms, and the widget-tree refactorings that make up most Flutter cleanup work.
Several restructurings have dedicated skills — route to them.

## Contents

- [Tooling](#tooling)
- [Route to a dedicated skill](#route-to-a-dedicated-skill)
- [Dart idioms worth refactoring toward](#dart-idioms-worth-refactoring-toward)
- [Widget tree refactoring](#widget-tree-refactoring)
- [Lifecycle and disposal](#lifecycle-and-disposal)
- [Dead code in Dart](#dead-code-in-dart)
- [Verification](#verification)

## Tooling

Dart's analyzer does more of this work than any other stack's, and `dart fix` applies a large share
of it mechanically — which makes it the ideal level-1 step: fully automated, individually
reversible, and worth landing on its own so it does not drown the real diff.

```bash
dart analyze                       # or: flutter analyze
dart fix --dry-run                 # what would change, grouped by lint
dart fix --apply                   # apply them
dart format .                      # formatting only
```

Lints worth enabling in `analysis_options.yaml` for refactoring work, if the project does not
already use a strict ruleset (`package:lints/recommended.yaml`, `package:flutter_lints`, or
`package:very_good_analysis`):

```yaml
linter:
  rules:
    - prefer_const_constructors
    - prefer_const_literals_to_create_immutables
    - avoid_unnecessary_containers
    - sized_box_for_whitespace
    - use_super_parameters
    - unnecessary_lambdas
    - cascade_invocations
    - always_declare_return_types
```

Turning on a strict ruleset mid-project produces hundreds of findings at once. Land the
`dart fix --apply` sweep as its own commit before starting any structural work.

## Route to a dedicated skill

| Situation | Skill |
|---|---|
| Mechanical lint cleanup with `dart analyze` / `dart fix` | `dart-run-static-analysis` |
| `if`/`else` and type-check chains that want pattern matching | `dart-use-pattern-matching` |
| Widget tree overflow, nesting, layout restructuring | `flutter-fix-layout-issues` |
| Layering, state management, repository/service structure | `flutter-apply-architecture-best-practices` |
| Making a layout adapt to screen size while restructuring it | `flutter-build-responsive-layout` |
| Hand-written JSON parsing that should be generated | `flutter-implement-json-serialization` |
| Hardcoded user-facing strings encountered during cleanup | `flutter-setup-localization` |

## Dart idioms worth refactoring toward

| Instead of | Prefer | Why |
|---|---|---|
| `if (x != null) x.f()` | `x?.f()` | One less nesting level |
| Long `if`/`else if` on types or shapes | Switch expressions and patterns (Dart 3) | Exhaustiveness checking; see `dart-use-pattern-matching` |
| `dynamic` and casts | Sealed classes, generics, records | The analyzer can only help with types it can see |
| Returning `Map<String, dynamic>` from domain code | A named class or record | Keys in strings are unsearchable and untypo-checkable |
| `Key? key` forwarded through constructors | `super.key` (`use_super_parameters`) | Removes boilerplate from every widget |
| Constructor without `const` | `const` constructor where fields are final | Enables const call sites, which skip rebuilds |
| Manual `Future.then` chains | `async`/`await` | Error handling becomes ordinary `try`/`catch` |
| Anonymous callbacks reimplemented per call site | Tear-offs (`onTap: _handleTap`) | `unnecessary_lambdas` |
| Repeated `Container` with one property set | The specific widget (`Padding`, `SizedBox`, `ColoredBox`) | `avoid_unnecessary_containers`; less to read, cheaper to build |

## Widget tree refactoring

The single most consequential choice here: **extract into a widget class, not into a method that
returns a widget.**

A `Widget _buildHeader()` method looks like an extraction but is not — its result is rebuilt every
time the enclosing widget rebuilds, it cannot be `const`, it cannot have its own state, and it does
not appear as a boundary in the widget inspector. A `class _Header extends StatelessWidget` gets
its own element in the tree, participates in rebuild scoping, and can be `const`. When a build
method is too long, extracting widget classes is the refactoring; helper methods just move the
lines.

Procedure:

1. Identify a subtree that has a name — a header, a row of actions, an empty state.
2. Create a private `StatelessWidget` (or `StatefulWidget` if it owns controllers) in the same file.
3. Pass what it needs as final constructor fields; pass callbacks out rather than a parent reference.
4. Mark the constructor `const` if every field is final and const-constructible, then use it as
   `const _Header(...)` at the call site.
5. Rebuild and compare the widget inspector — the tree gained a named node and lost nothing else.

Other widget-tree cleanups worth doing while in there:

- **Flatten deep nesting** by extracting the inner subtrees, not by cleverer layout widgets. Six
  levels of nesting inside one build method is a naming problem, not a layout problem.
- **Push `const` as far up as it will go.** A `const` subtree is skipped entirely on rebuild; this is
  the cheapest performance work in Flutter and the analyzer finds every opportunity.
- **Move expensive work out of `build`.** `build` can run many times per frame; anything creating
  controllers, parsing, or sorting belongs in `initState`, a memoized field, or a state holder.
- **Replace `Container` with what it is actually doing.** A `Container(padding: ...)` is a `Padding`.

## Lifecycle and disposal

Refactoring that moves stateful code between widgets is the most common way disposal gets lost —
and a missing `dispose` is a leak that no test catches.

After any move involving a `StatefulWidget`, verify each of these is created in `initState` (or the
field initializer) and released in `dispose`:

`AnimationController`, `TextEditingController`, `ScrollController`, `PageController`, `FocusNode`,
`StreamSubscription`, `Timer`, `Ticker`, platform channel listeners.

Also re-check `didUpdateWidget` — a widget that was previously never rebuilt with new configuration
may now be, once it has been extracted and given a parent that rebuilds.

## Dead code in Dart

Beyond the generic invisible-reference list:

- Generated files (`*.g.dart`, `*.freezed.dart`, `*.mocks.dart`) — never edit these; change the
  source annotation and re-run `build_runner`
- Symbols referenced only from generated code, which may not be present until `build_runner` has run
- Anything reached through `MethodChannel` names, route name strings, or `Navigator` string routes
- Assets and localization keys declared in `pubspec.yaml` or ARB files
- Entry points on the platform side (Android/iOS host code calling into Dart)

`dart analyze` reports unused local variables, fields, and imports; it does not report an unused
public API, since any package consumer might use it.

## Verification

```bash
dart analyze                                    # must be clean before and after
flutter test                                    # unit and widget tests
flutter test integration_test                   # end-to-end, when the change touches flows
flutter build apk --debug                       # or ios/web — catches what analysis does not
```

Golden tests are unusually valuable for widget refactoring: they assert the rendered output is
byte-identical, which is precisely the "behavior preserved" claim being made. If the project has
goldens, run them; if it does not and the refactoring is large, adding a golden for the affected
screen before starting is a cheap safety net (see `flutter-add-widget-test`).
