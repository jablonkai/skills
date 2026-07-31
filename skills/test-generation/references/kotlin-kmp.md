# Kotlin, KMP, and Android

## Pick the source set first

Placement decides which targets run the test and which APIs are available. Getting this wrong is
the usual reason a generated test never executes.

| Source set | Runs on | Put here |
|---|---|---|
| `commonTest` | Every configured target | Shared business logic, pure functions, serialization, use cases, repositories over interfaces |
| `jvmTest` / `androidUnitTest` | JVM, no device | Code needing JVM-only APIs or JUnit-specific machinery |
| `androidInstrumentedTest` (`androidTest/`) | Device or emulator | Real framework: `Context`, Room, `WorkManager`, Compose UI |
| `iosTest` / `nativeTest` | Simulator/device via Kotlin/Native | `expect`/`actual` iOS implementations, platform interop |

Rule: if it can run in `commonTest`, it belongs in `commonTest`. Only push a test down to a
platform set when it genuinely needs that platform.

Mirror the main source path and name the file after the unit: `commonMain/kotlin/foo/Bar.kt` →
`commonTest/kotlin/foo/BarTest.kt`.

## Framework

Multiplatform code uses `kotlin.test` — it maps onto JUnit on JVM and the native test runner
elsewhere:

```kotlin
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class PriceFormatterTest {
    @Test
    fun formats_zero_as_free() {
        assertEquals("Free", format(0))
    }

    @Test
    fun rejects_negative_amounts() {
        assertFailsWith<IllegalArgumentException> { format(-1) }
    }
}
```

JVM-only modules may use JUnit 5 (`@Test` from `org.junit.jupiter.api`, `@ParameterizedTest`,
`@Nested`, `assertThrows`) — match whatever the existing suite uses. Do not mix `kotlin.test` and
JUnit assertions in one file.

Assertion libraries in use in Kotlin projects: `kotlin.test` (default), AssertK, Truth, Kotest
assertions. Follow the project; do not introduce a new one.

Backtick-quoted test names read best but are **not** allowed on Android instrumented tests or
Kotlin/Native — use snake_case there. Prefer snake_case in `commonTest` for that reason.

## Coroutines

`kotlinx-coroutines-test` gives virtual time; anything else makes the suite slow or flaky.

```kotlin
@Test
fun retries_three_times_before_failing() = runTest {
    val client = FailingClient(failures = 3)
    val result = SyncUseCase(client).run()          // delays are skipped, not slept
    assertEquals(3, client.attempts)
    assertTrue(result.isSuccess)
}
```

- `runTest` skips `delay` automatically — never `Thread.sleep`, never a real timeout.
- Inject the dispatcher; do not hard-code `Dispatchers.IO` in code under test. In tests pass
  `StandardTestDispatcher()` (queues, advance manually) or `UnconfinedTestDispatcher()` (runs
  eagerly — handy for simple ViewModel state assertions).
- `advanceUntilIdle()`, `advanceTimeBy(n)`, `runCurrent()` control the queue explicitly.
- Test cancellation deliberately: cancel the job and assert cleanup ran. Never assert on
  `CancellationException` being swallowed.
- `backgroundScope` for collectors that should be cancelled when the test ends.

## Flow and StateFlow

Use Turbine for anything with more than one emission:

```kotlin
@Test
fun emits_loading_then_content() = runTest {
    viewModel.state.test {
        assertEquals(Loading, awaitItem())
        assertEquals(Content(items), awaitItem())
        cancelAndIgnoreRemainingEvents()
    }
}
```

- `awaitItem()`, `awaitError()`, `awaitComplete()`, `expectNoEvents()`.
- A `StateFlow` replays its current value — the first `awaitItem()` is the initial state, not the
  first change. Missing this causes off-by-one assertions.
- For a one-shot terminal value, `flow.first()` inside `runTest` is simpler than Turbine.

## Test doubles

Prefer a hand-written fake implementing the interface — it works in `commonTest`, where JVM mocking
libraries do not.

```kotlin
class FakeUserRepository(private var users: List<User> = emptyList()) : UserRepository {
    var saveCount = 0; private set
    override suspend fun all() = users
    override suspend fun save(user: User) { saveCount++; users = users + user }
}
```

When a mock is genuinely needed:

- **MockK** — the Kotlin default; `mockk<T>()`, `every { } returns`, `coEvery { }` for suspending
  functions, `verify { }` / `coVerify { }`. `relaxed = true` when only some calls matter.
- **Mockito(-Kotlin)** — JVM only; fine if the project already uses it.
- Neither works in `commonTest` or on Native. Shared-code tests get fakes.

## Android specifics

- **Robolectric** (`androidUnitTest`) runs framework code on the JVM — much faster than an
  emulator, and the right home for tests touching `Context`, resources, or `SharedPreferences`.
- **Instrumented** (`androidTest`) for Room migrations, `WorkManager`, permissions, and real
  device behavior. `androidx.test.ext.junit.runners.AndroidJUnit4`,
  `InstrumentationRegistry.getInstrumentation().targetContext`.
- **Architecture components**: `InstantTaskExecutorRule` for `LiveData`, `androidx.room.testing`
  for migrations, `WorkManagerTestInitHelper` for workers.
- Do not test Android framework classes themselves — test your code's use of them.

## Compose and Compose Multiplatform

UI tests, semantics assertions, and screenshot testing are covered by the
**`compose-ui-testing-patterns`** skill — invoke it rather than duplicating its guidance. The
short version: `runComposeUiTest` (multiplatform) or `createComposeRule()` /
`createAndroidComposeRule<Activity>()` (Android), assert via semantics
(`onNodeWithText`, `onNodeWithTag`, `assertIsDisplayed`), and prefer testing the state holder
directly over driving the UI where the logic lives outside composition.

Screenshot/snapshot: Paparazzi (JVM, no device) or Roborazzi (Robolectric-based). Both commit
golden images — regenerate deliberately, and review the diff rather than blanket-accepting.

## Running

```bash
./gradlew test                                   # all JVM/common unit tests
./gradlew :shared:jvmTest --tests '*PriceFormatter*'
./gradlew :shared:iosSimulatorArm64Test          # KMP iOS target
./gradlew :app:testDebugUnitTest                 # Android unit tests
./gradlew :app:connectedDebugAndroidTest         # instrumented, needs a device
```

Run quiet and filter — a full Gradle log is enormous:

```bash
./gradlew test --console=plain 2>&1 | grep -E 'FAILED|tests? completed|^> Task .*test' | head -40
```

HTML report with the actual failure detail: `<module>/build/reports/tests/<task>/index.html`.

## Coverage

**Kover** is the Kotlin-native choice and works for KMP:

```bash
./gradlew koverHtmlReport      # build/reports/kover/html/index.html
./gradlew koverVerify          # if verification rules are configured
```

JaCoCo remains common on Android/JVM-only projects. Report uncovered *branches* with file:line;
exclude generated code (`*_Impl`, `*$$serializer`, `BuildConfig`, DI modules) in the report config
rather than writing tests for it.
