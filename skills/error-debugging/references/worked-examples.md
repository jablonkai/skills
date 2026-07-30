# Worked examples

Sample traces with the analysis the skill should produce. These are illustrative reconstructions,
not captures from a specific project — use them to calibrate depth and output shape, not as a
pattern-match table.

Each example follows the report format from `SKILL.md` Step 6.

---

## 1. Android / Kotlin coroutines — result delivered after teardown

**Trace**

```
FATAL EXCEPTION: main
Process: com.example.app, PID: 9182
java.lang.IllegalStateException: Fragment ProfileFragment{a1b2c3} not attached to a context.
    at androidx.fragment.app.Fragment.requireContext(Fragment.java:965)
    at com.example.app.ui.ProfileFragment.showError(ProfileFragment.kt:114)
    at com.example.app.ui.ProfileFragment$onViewCreated$1$1.emit(ProfileFragment.kt:62)
    at kotlinx.coroutines.flow.FlowKt__CollectKt$collect$3.emit(Collect.kt:30)
    ...
```

**What failed** — `IllegalStateException` at `ProfileFragment.kt:114`, on the main thread.

**Why** — `onViewCreated` collects the view model's error `Flow` in `lifecycleScope.launch { … }`.
That scope survives view destruction (it is tied to the *fragment*, not the *view*), so an error
emitted after the user navigated away reaches `showError`, which calls `requireContext()` on a
detached fragment.

**Evidence** — `ProfileFragment.kt:62` is the collector inside `lifecycleScope.launch`; the frame
above it is `kotlinx.coroutines.flow` machinery, confirming the emission path rather than a direct
UI call. There is no `repeatOnLifecycle` in the frames.

**Fix** — collect lifecycle-aware so collection stops at `STOPPED`:

```kotlin
viewLifecycleOwner.lifecycleScope.launch {
    viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.errors.collect(::showError)
    }
}
```

**Verify** — reproduce by triggering the request and navigating back immediately; add a test that
emits after `moveToState(DESTROYED)` on a `FragmentScenario`.

**Also worth checking** — every other `lifecycleScope.launch` in the fragment package; this is a
per-collector mistake, not a per-screen one.

---

## 2. Compose — infinite recomposition

**Symptom** — the screen freezes, no exception; the frame is dropped repeatedly and
`ProfileScreen` shows an enormous recomposition count in Layout Inspector.

**Why** — state is written during composition:

```kotlin
@Composable
fun ProfileScreen(vm: ProfileViewModel) {
    val items by vm.items.collectAsState()
    vm.selected = items.firstOrNull()   // <- write during composition
    …
}
```

Each write invalidates the composable that just read `items`, which recomposes, which writes
again. There is no trace because nothing throws — this is a liveness bug, not a crash.

**Evidence** — the assignment sits directly in the composable body with no effect wrapper; the
recomposition count grows monotonically while the screen is idle.

**Fix** — move the write to where the event happens, or derive it instead:

```kotlin
val selected by remember(items) { derivedStateOf { items.firstOrNull() } }
```

**Verify** — Layout Inspector recomposition counts stop climbing when idle; a Compose UI test with
`mainClock.autoAdvance = false` no longer times out.

---

## 3. KMP on iOS — unannotated Kotlin exception terminates the process

**Trace**

```
Uncaught Kotlin exception: kotlin.IllegalStateException: Session expired
    at 0   Shared   0x104f2b1c8  kfun:com.example.data.SessionRepo#requireToken(){}kotlin.String + 216
    at 1   Shared   0x104f30a44  kfun:com.example.data.SyncUseCase#$invoke$lambda + 88
    at 2   MyApp    0x1020a1b30  closure #1 in ProfileViewModel.refresh()
```

**What failed** — a Kotlin exception crossing into Swift, aborting the process rather than
surfacing as an error.

**Why** — Kotlin exceptions only bridge to Swift as `NSError` when the exposed function is
annotated `@Throws`. `SyncUseCase.invoke` is not, so the runtime treats the escape as unrecoverable
and calls `terminateWithUnhandledException`. The Swift `do/catch` around it never runs — which is
why the code "looks like" it handles the failure.

**Evidence** — frame 2 is Swift, frames 0–1 are `kfun:` symbols; the report says
`Uncaught Kotlin exception` rather than a Swift trap, so the boundary is the mechanism.

**Fix** — annotate the boundary function and handle it Swift-side, or (preferably) do not throw
across the boundary at all — return a sealed `Result` type from shared code:

```kotlin
@Throws(CancellationException::class, AppException::class)
suspend fun invoke(): SyncResult
```

**Verify** — an iOS test that forces an expired session now catches the error instead of crashing.

**Also worth checking** — every other suspend function exposed to iOS; the same omission is
usually repo-wide.

---

## 4. Flutter — `setState` after `dispose`

**Trace**

```
══╡ EXCEPTION CAUGHT BY WIDGETS LIBRARY ╞═══════════════════════════
The following assertion was thrown while dispatching notifications for TextEditingController:
setState() called after dispose(): _SearchPageState#4f2a1(lifecycle state: defunct, not mounted)

When the exception was thrown, this was the stack:
#0      State.setState (package:flutter/src/widgets/framework.dart:1157:9)
#1      _SearchPageState._onResults (package:app/ui/search_page.dart:73:5)
<asynchronous suspension>
```

**What failed** — `setState` at `search_page.dart:73` on a disposed `State`.

**Why** — `_onResults` is a continuation after `await api.search(query)`. The user left the page
while the request was in flight; when it completed, the callback resumed against a defunct state
object. The `<asynchronous suspension>` marker is the tell: the call originates from a resumed
future, not from a live event handler.

**Evidence** — the lifecycle state is reported as `defunct, not mounted`; frame #1 sits directly
below the suspension boundary.

**Fix** — guard after every await, and cancel work in `dispose`:

```dart
final results = await api.search(query);
if (!mounted) return;
setState(() => _results = results);
```

**Verify** — `flutter test` widget test that pumps the request, disposes the widget, then completes
the future; it should not throw.

---

## 5. Swift — main-actor violation surfacing as `EXC_BAD_ACCESS`

**Trace**

```
Exception Type:  EXC_BAD_ACCESS (SIGSEGV)
Exception Subtype: KERN_INVALID_ADDRESS at 0x0000000000000018
Triggered by Thread:  6

Thread 6 Crashed:
0   UIKitCore   0x1a2b3c4d5  -[UITableView _updateWithItems:...]
1   MyApp       0x1045a2b1c  ProfileViewModel.applyUpdates()  (ProfileViewModel.swift:96)
2   libdispatch 0x1b0c1a2f0  _dispatch_worker_thread
```

**What failed** — a UIKit table-view update executed on a dispatch worker thread (Thread 6), not
the main thread.

**Why** — `applyUpdates()` is called from a `URLSession` completion handler, which runs on a
background queue. UIKit is main-thread-only; the internal state it touches is not synchronized, so
the update walks a partially-updated structure and dereferences garbage. The crash address
(`0x18`) is a small offset — a nil-ish base pointer, consistent with reading a torn structure
rather than a genuine null in the app's own code.

**Evidence** — the crashing thread is not Thread 0, and its top frame is UIKit. The app frame
below it is the entry point from our code.

**Fix** — hop to the main actor at the boundary:

```swift
@MainActor func applyUpdates() { … }
// or, at the call site:
await MainActor.run { viewModel.applyUpdates() }
```

**Verify** — run with the Main Thread Checker enabled (scheme diagnostics); it now reports nothing
on this path. Thread Sanitizer confirms the race is gone.

---

## 6. Rust — the `Err` payload is the diagnosis

**Trace**

```
thread 'tokio-runtime-worker' panicked at src/importer.rs:142:38:
called `Result::unwrap()` on an `Err` value: Os { code: 2, kind: NotFound,
  message: "No such file or directory" }
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
```

**What failed** — `unwrap()` at `importer.rs:142`.

**Why** — the proximate cause is the unwrap; the root cause is in the payload: the file the
importer opens does not exist. Line 142 joins a configured directory with a filename that came
from user input without normalization, so a config value with a trailing separator produces a
path that never resolves. The `unwrap` merely converts a recoverable error into a panic — and the
error lost its context, so the message does not even say *which* path.

**Evidence** — `kind: NotFound` from an OS error, on the runtime worker; no path in the message
means the `?`/`unwrap` chain crossed a boundary without `.context(…)`.

**Fix** — propagate with context instead of unwrapping:

```rust
let file = File::open(&path)
    .with_context(|| format!("opening import source {}", path.display()))?;
```

then handle the missing-file case at the caller (skip and warn, or fail the job explicitly).

**Verify** — `cargo test` with a fixture pointing at a missing path asserts an `Err` with the path
in the message, not a panic.

---

## 7. C++ — ASan use-after-free

**Trace**

```
==4711==ERROR: AddressSanitizer: heap-use-after-free on address 0x60300000eff0
READ of size 8 at 0x60300000eff0 thread T0
    #0 0x4f1a2b in Renderer::drawFrame() renderer.cpp:212
    #1 0x4f2c10 in App::tick() app.cpp:64

0x60300000eff0 is located 0 bytes inside of 32-byte region
freed by thread T0 here:
    #0 0x4c9d1a in operator delete(void*)
    #1 0x4f0e33 in Scene::reset() scene.cpp:31

previously allocated by thread T0 here:
    #1 0x4ef221 in Scene::load() scene.cpp:18
```

**What failed** — `Renderer::drawFrame` reads a `Scene`-owned object 32 bytes wide that
`Scene::reset()` already deleted.

**Why** — the renderer caches a raw pointer obtained during `Scene::load()`. `Scene::reset()`
frees the underlying storage but leaves the renderer's cached pointer dangling; the next
`App::tick()` dereferences it. The free site (`scene.cpp:31`), not the read site, is where the
ownership contract breaks.

**Evidence** — ASan reports all three events for the same address: allocation at `scene.cpp:18`,
free at `scene.cpp:31`, read at `renderer.cpp:212`. That triple is the whole proof.

**Fix** — make the ownership explicit rather than patching the read: hold a
`std::shared_ptr`/`std::weak_ptr` in the renderer, or have `Scene::reset()` notify the renderer to
drop its cache. A null check at `renderer.cpp:212` would *not* fix this — the pointer is not null,
it is dangling.

**Verify** — rerun the ASan build over the reset→tick sequence; the report disappears. Add a
regression test that resets the scene between frames.
