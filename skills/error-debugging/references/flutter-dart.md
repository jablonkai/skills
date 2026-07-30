# Flutter / Dart

## Reading a Flutter error

Framework errors arrive in a boxed report, and the useful part is rarely the first line:

```
══╡ EXCEPTION CAUGHT BY RENDERING LIBRARY ╞══════════════════════════
The following assertion was thrown during performLayout():
BoxConstraints forces an infinite width.
...
The relevant error-causing widget was:
  Row  Row:file:///app/lib/ui/header.dart:31:14        <- start here
```

- **"The relevant error-causing widget was"** points at your code; the frames above it are
  framework internals.
- The library banner (`RENDERING LIBRARY`, `WIDGETS LIBRARY`, `GESTURE`, `SCHEDULER`) tells you
  which phase failed — layout, build, gesture dispatch, or frame scheduling.
- `<asynchronous suspension>` marks an `await` boundary: frames below it are the caller chain
  *before* the await, and the synchronous context is lost. Turn on
  `Error.stackTraceCallback` / run in debug mode for better async chains, or wrap the failing call
  so the error is thrown with a preserved `StackTrace` argument.

## Layout and rendering errors

| Message | Cause |
|---|---|
| `A RenderFlex overflowed by N pixels` | Fixed-size children in a `Row`/`Column` exceed the available extent. Wrap in `Expanded`/`Flexible`, make it scrollable, or constrain the child. |
| `BoxConstraints forces an infinite width/height` | An unbounded parent (`Row` cross axis, scrollable, `IntrinsicWidth`) around a child that wants infinity. Give the child a bounded box. |
| `Vertical viewport was given unbounded height` | `ListView`/`Column`-in-`Column` nesting. Use `Expanded`, `shrinkWrap: true`, or `SliverList`. |
| `RenderBox was not laid out` | A layout exception was thrown earlier in the same frame and swallowed — look above this error, it is a symptom. |
| `Incorrect use of ParentDataWidget` | `Expanded`/`Positioned` used outside its matching parent (`Flex`/`Stack`). |
| `Cannot hit test a render box that has never been laid out` | Widget rendered with zero size or offstage during a gesture. |

## State and lifecycle errors

| Message | Cause |
|---|---|
| `setState() called during build` | State mutated inside `build()` or in a synchronously-called child build. Move to `initState`, a callback, or `WidgetsBinding.instance.addPostFrameCallback`. |
| `setState() called after dispose()` | Async result arriving after the widget was removed. Guard with `if (!mounted) return;` after every `await`. |
| `Looking up a deactivated widget's ancestor is unsafe` | `context` used across an async gap or after removal — capture the dependency (Navigator, Theme, ScaffoldMessenger) *before* the `await`. |
| `A GlobalKey was used multiple times` | The same key in two live subtrees, usually a rebuilt list without stable keys. |
| `dependOnInheritedWidgetOfExactType called before initState completed` | Inherited lookup in `initState`; move it to `didChangeDependencies`. |

## Async and isolate errors

- **Unawaited futures** swallow errors — an `async` call with no `await` and no `.catchError` loses
  its exception into the zone. Enable the `unawaited_futures` lint.
- **Zone-level errors**: an error thrown outside the Flutter framework surfaces through
  `PlatformDispatcher.instance.onError` / `runZonedGuarded`, not `FlutterError.onError`. If a crash
  appears in production but not in the error reporter, the wrong hook is installed.
- **Isolates** do not share error handlers; add `Isolate.addErrorListener` or use `Isolate.run`.
- `LateInitializationError: Field '_x' has not been initialized` — `late` field read before
  assignment, typically a `late final` set in an async `initState`.
- `Null check operator used on a null value` — a `!` on a nullable; find the producer, not the `!`.

## Platform channels and plugins

- `MissingPluginException(No implementation found for method X on channel Y)` — plugin not
  registered for that platform, or a hot restart after adding the plugin. Full stop/rebuild, and
  verify the platform-side registration.
- `PlatformException(error, message, details)` — the failure happened in native code; the `details`
  field usually carries the native trace. Diagnose it with the Android or Apple reference, not this one.
- Channel type mismatches (sending a `Map<String, dynamic>` with a non-codec-supported value)
  throw on encode; check the `StandardMessageCodec` supported types.

## Release-build traces

Obfuscated release traces show numeric frames only. Symbolicate with `flutter symbolize`
(see [symbolication.md](symbolication.md)) before analyzing.

## Useful commands

```bash
flutter analyze                      # static errors first — many crashes are visible here
flutter run --debug                  # debug mode gives assertions + full async chains
flutter test test/foo_test.dart      # targeted regression test
flutter logs                         # device logs from a running app
dart run custom_lint                 # if the project uses it
```

For layout-specific debugging, `debugPaintSizeEnabled = true`, the Flutter Inspector widget tree,
and `debugDumpRenderTree()` narrow an overflow faster than reading the trace.
