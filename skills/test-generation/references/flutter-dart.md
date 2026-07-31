# Flutter and Dart

## Use the dedicated skills

Four skills already cover most of this stack. Invoke the matching one instead of writing the test
from scratch here; this file only covers what they leave out and the decisions around them.

| Task | Skill |
|---|---|
| Unit tests with `package:test` — functions, classes, pure Dart | `dart-add-unit-test` |
| Mocks via `mockito` + `build_runner` (`@GenerateMocks`, `.mocks.dart`) | `dart-generate-test-mocks` |
| Widget tests — `testWidgets`, `WidgetTester`, finders, pumping | `flutter-add-widget-test` |
| End-to-end flows on a device with `integration_test` | `flutter-add-integration-test` |

## Choosing the test type

| The code is… | Test type | Directory |
|---|---|---|
| Pure Dart — model, parser, use case, extension | Unit | `test/` |
| A widget's build output, layout, or interaction | Widget | `test/` |
| A provider/bloc/notifier's state transitions | Unit (drive it directly, no widget) | `test/` |
| A whole user flow across screens, or plugin/platform behavior | Integration | `integration_test/` |

Mirror the `lib/` path and suffix with `_test.dart`: `lib/src/cart/cart_repository.dart` →
`test/src/cart/cart_repository_test.dart`. Files not ending in `_test.dart` are not picked up by
the runner; shared helpers go in `test/helpers/` and are imported.

State-management logic is unit-testable without a widget — test the notifier/bloc directly and
reserve widget tests for what the widget actually renders.

## Determinism

- **Async** — `await tester.pumpAndSettle()` for animations that end; a bare `pump()` advances one
  frame. `pumpAndSettle` on an infinite animation (a spinner) times out — pump a fixed duration
  instead.
- **Time** — `fakeAsync` from `package:fake_async`, or `FakeAsync` via
  `flutter_test`'s `tester.binding.delayed`. Never `Future.delayed` with a real duration.
- **HTTP** — `MockClient` from `package:http/testing.dart`, or a fake implementing your own client
  interface. Never hit the network.
- **Plugins** — `TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
  .setMockMethodCallHandler(channel, handler)` to answer platform channels in widget tests.
- `SharedPreferences.setMockInitialValues({})` before anything reads preferences.

## Mocks

`mockito` needs codegen — that is what `dart-generate-test-mocks` handles. `mocktail` needs none
and is often the simpler choice in newer projects:

```dart
class MockCartRepository extends Mock implements CartRepository {}

when(() => repo.items()).thenAnswer((_) async => [item]);
verify(() => repo.save(any())).called(1);
```

Use whichever the project already uses; do not add a second mocking library.

## Golden (screenshot) tests

Not covered by the widget-test skill:

```dart
await expectLater(
  find.byType(PriceTag),
  matchesGoldenFile('goldens/price_tag.png'),
);
```

```bash
flutter test --update-goldens        # regenerate — review the diff, never blanket-accept
```

Goldens are font- and platform-sensitive. Pin the test font (`loadAppFonts` from
`golden_toolkit`, or bundle the font in the test) or the same test produces different bytes on CI
than locally.

## Running

```bash
flutter test                                   # all tests under test/
flutter test test/src/cart/cart_repository_test.dart
flutter test --name 'rejects negative quantity'
flutter test --reporter compact
dart test                                      # pure Dart package, no Flutter dependency

flutter test integration_test/app_test.dart -d <device-id>   # integration, needs a device
```

Keep the output small — `--reporter compact`, or pipe through `tail`. Analysis must be clean too:
`flutter analyze` (or the `dart-run-static-analysis` skill) before declaring the work done.

## Coverage

```bash
flutter test --coverage                        # writes coverage/lcov.info
genhtml coverage/lcov.info -o coverage/html    # needs lcov installed
```

For pure Dart packages use the `dart-collect-coverage` skill. Filter generated files
(`*.g.dart`, `*.freezed.dart`, `*.mocks.dart`) out of the report rather than testing them:

```bash
lcov --remove coverage/lcov.info '*.g.dart' '*.freezed.dart' '*.mocks.dart' -o coverage/lcov.info
```
