# Kotlin / JVM / Android, KMP and Compose

## Reading a JVM trace

Frames are listed innermost-first; the causal chain reads bottom-up.

```
FATAL EXCEPTION: main
Process: com.example.app, PID: 12345
java.lang.IllegalStateException: Fragment not attached to a context
    at com.example.app.ui.ProfileFragment.render(ProfileFragment.kt:88)   <- our code, topmost
    at com.example.app.ui.ProfileViewModel$load$1.invokeSuspend(ProfileViewModel.kt:41)
    ...
Caused by: retrofit2.HttpException: HTTP 401                              <- the real origin
    at com.example.app.data.AuthInterceptor.intercept(AuthInterceptor.kt:23)
```

Rules:

- The **deepest `Caused by:`** is usually the root cause; outer exceptions are wrappers.
- The **topmost project frame** is where the mistake surfaced; framework frames above it explain
  the mechanism, not the fault.
- `Suppressed:` entries come from `try`-with-resources / `use {}` cleanup failures — a suppressed
  exception can mask the primary one.
- `FATAL EXCEPTION: main` means the UI thread died; the process is gone.

## Exception → likely cause

| Exception | Usual root cause |
|---|---|
| `NullPointerException` | Platform type from Java/JNI assumed non-null; `lateinit` read before init; `!!` on an absent value |
| `UninitializedPropertyAccessException` | `lateinit` read before assignment — often lifecycle ordering |
| `IllegalStateException: Fragment not attached` | Async result delivered after the fragment detached |
| `ConcurrentModificationException` | Collection mutated while iterating, often across threads |
| `ClassCastException` | Unchecked generic cast, or a heterogeneous JSON/Bundle payload |
| `OutOfMemoryError` | Bitmap decoding at full resolution, unbounded cache, leaked activity |
| `NetworkOnMainThreadException` | Blocking I/O on the UI thread |
| `ANR / Input dispatching timed out` | Main thread blocked >5 s — see ANRs below |
| `AndroidRuntimeException: Can't create handler inside thread that has not called Looper.prepare()` | UI construction off the main thread |
| `WindowLeaked` / `IllegalArgumentException: View not attached to window manager` | Dialog shown or dismissed against a destroyed activity |

## Coroutines

Coroutine traces are cut at suspension points — the frames above the `invokeSuspend` boundary
belong to the resumption, not the launch site.

- Enable `kotlinx-coroutines-debug` and `DebugProbes.install()` (or the
  `-Dkotlinx.coroutines.debug` JVM flag) in debug builds to get `Coroutine boundary` frames that
  stitch the launch site back in.
- `StackTraceRecovery` adds the creation site automatically for suspend functions when the debug
  agent is present.

Patterns worth checking:

- **Swallowed `CancellationException`** — a `catch (e: Exception)` inside a coroutine catches
  cancellation and turns a normal cancel into a "mystery" failure or a hung job. Rethrow it, or
  catch narrower types.
- **Wrong scope** — `GlobalScope`/`viewModelScope` chosen so the job outlives (or dies before)
  the thing it updates; results arriving after `onDestroy` produce detached-context crashes.
- **Uncaught failure in a child** — a plain `launch` child failure cancels the whole parent scope;
  `SupervisorJob` / `supervisorScope` isolates it. Failure inside `async` surfaces only at `await()`.
- **Blocking a dispatcher** — `runBlocking` or synchronous I/O on `Dispatchers.Main` (ANR) or on
  the small `Dispatchers.Default` pool (throughput collapse). Use `Dispatchers.IO`.
- **`Flow`/`StateFlow` misuse** — collecting without a lifecycle-aware collector
  (`repeatOnLifecycle` / `flowWithLifecycle`) keeps the collector alive past the view; `StateFlow`
  conflation means intermediate values are legitimately dropped (not a bug).

## ANRs

`anr` traces are not exceptions — they are thread dumps. Read them differently:

- Find the `"main"` thread block and look at its state: `RUNNABLE` (busy — CPU-bound work),
  `BLOCKED on <lock> held by tid=N` (lock contention — go find thread N), `WAITING`/`TIMED_WAITING`
  (waiting on I/O, a `Future`, or `runBlocking`).
- Sources: disk/network I/O on main, `SharedPreferences.commit()`, large JSON parse, synchronous
  `ContentProvider` / binder call, database migration, oversized `onDraw`.
- Pull with `adb bugreport`, or read `/data/anr/traces.txt` on debuggable builds; Play Console
  Vitals aggregates them for released builds.

## Kotlin Multiplatform / Kotlin/Native (iOS)

```
Uncaught Kotlin exception: kotlin.IllegalStateException: Not initialized
    at 0   MyFramework   0x... kfun:com.example.Repo#load(){} + 120
```

- `kfun:` frames are Kotlin/Native symbols. Line numbers require the framework built with debug
  info; release frameworks need the dSYM (see [symbolication.md](symbolication.md)).
- Kotlin exceptions crossing into Swift/ObjC become `NSError` only for `@Throws`-annotated
  functions; everything else **terminates the process** rather than propagating. An "unexplained"
  iOS crash from shared code is usually an unannotated Kotlin exception.
- `expect`/`actual` failures: a symbol resolves on one platform and not another, or the `actual`
  has different nullability/threading assumptions than the `expect` contract implies. Check both
  actuals, not just the one you are debugging.
- Memory model: on the modern (new) memory manager, freezing errors are gone; on legacy code
  paths `InvalidMutabilityException` / `IncorrectDereferenceException` mean cross-thread access to
  unfrozen state.
- iOS main-thread rules still apply — UI touched from a background Kotlin dispatcher crashes in
  UIKit, not in Kotlin, so the trace looks like a Swift bug.

## Compose / Compose Multiplatform

| Symptom | Cause |
|---|---|
| Infinite recomposition / frozen frame | State written during composition — a `mutableStateOf` assignment in the composable body instead of in an effect or event handler |
| `IllegalStateException: Reading a state that was created after the snapshot was taken` | State created inside composition and read across a snapshot boundary; hoist it or wrap with `remember` |
| `Snapshot` / `Composer` frames with no project frame nearby | The failing lambda is inlined — search for the composable named in the nearest `androidx.compose.runtime` frame's caller |
| Crash on recomposition only after config change | State not `remember`ed / not `rememberSaveable`, so it is rebuilt into an invalid combination |
| `IllegalArgumentException: Cannot round to nearest integer` / infinite constraints | Nested scrollable in an unbounded parent (a `LazyColumn` inside a `Column` with vertical scroll) |
| Effects firing repeatedly | `LaunchedEffect(key)` given an unstable key that changes every recomposition |

For deeper recomposition performance work, the `compose-recomposition-performance` and
`compose-side-effects` skills go further than this diagnosis-oriented list.

## Useful commands

```bash
adb logcat -d -b crash | tail -100            # last crash buffer
adb logcat -c                                 # clear before reproducing
adb shell dumpsys activity processes | head    # is the process even alive
./gradlew :app:testDebugUnitTest --tests '*FooTest*'   # targeted regression test
```
