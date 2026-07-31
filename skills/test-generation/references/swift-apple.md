# Swift — iOS and macOS

## Which framework

| Framework | Use when |
|---|---|
| **Swift Testing** (`import Testing`) | New tests on Xcode 16+/Swift 6. Macro-based, async-native, parallel by default |
| **XCTest** (`import XCTest`) | The existing suite uses it, or you need performance tests, or UI tests |
| **XCUITest** (`XCUIApplication`) | Driving the real app through its UI — the only option for UI flows |

The two unit frameworks coexist in one target; a project migrating incrementally is normal. Do not
convert an existing XCTest suite to Swift Testing while adding tests to it.

## Placement

- **SwiftPM** — `Tests/<Module>Tests/<Type>Tests.swift`, declared as a `.testTarget` in
  `Package.swift` with `.target(name: "<Module>")` as a dependency.
- **Xcode project** — a unit test target (`<App>Tests`) and, separately, a UI test target
  (`<App>UITests`). New files must be added to the test target's membership or they silently never
  compile into the suite.
- Test the module under test via `@testable import <Module>` — that exposes `internal` symbols.
  `private` stays private; if a test needs it, the design is telling you something.

## Swift Testing

```swift
import Testing
@testable import Cart

@Test func formatsZeroAsFree() {
    #expect(format(0) == "Free")
}

@Test("rejects negative amounts")
func rejectsNegative() throws {
    #expect(throws: PriceError.negative) { try format(-1) }
}

@Test(arguments: [0, 1, 99, Int.max])
func neverReturnsEmpty(amount: Int) {
    #expect(!format(amount).isEmpty)
}
```

- `#expect` continues on failure; `#require` stops the test (use it to unwrap:
  `let user = try #require(result.user)`).
- `@Suite` groups tests; a `struct` suite is re-instantiated per test, giving free isolation —
  prefer it over class-with-shared-state.
- `async` tests need no ceremony: `@Test func loads() async throws { … }`.
- `@Test(.disabled("reason"))`, `.tags(...)`, `.timeLimit(...)` for control.
- Tests run **in parallel** by default. Shared global state across tests is a defect; use
  `.serialized` on a suite only when parallelism is genuinely impossible.

## XCTest

```swift
final class PriceFormatterTests: XCTestCase {
    private var sut: PriceFormatter!

    override func setUpWithError() throws { sut = PriceFormatter() }
    override func tearDownWithError() throws { sut = nil }

    func testFormatsZeroAsFree() {
        XCTAssertEqual(sut.format(0), "Free")
    }

    func testRejectsNegative() {
        XCTAssertThrowsError(try sut.format(-1)) { error in
            XCTAssertEqual(error as? PriceError, .negative)
        }
    }
}
```

- Method names must start with `test` or they do not run.
- `XCTUnwrap` instead of force-unwrapping — a failed unwrap should fail the test, not crash the run.
- Set `sut` to `nil` in `tearDown`: XCTest keeps test-case instances alive for the whole run, so
  strong references leak across tests.
- `XCTAssertNoThrow`, `XCTAssertIdentical`, `XCTAssertEqual(_:_:accuracy:)` for floating point.

## Async and concurrency

```swift
// Swift Testing — just await
@Test func loadsUser() async throws {
    let user = try await sut.load(id: 1)
    #expect(user.name == "Ada")
}

// XCTest — async test methods are supported directly
func testLoadsUser() async throws { … }

// Callback-based APIs, XCTest only
func testCallback() {
    let expectation = expectation(description: "completes")
    sut.load { _ in expectation.fulfill() }
    wait(for: [expectation], timeout: 1.0)
}
```

- `@MainActor` on the test (or suite) when asserting on main-actor-isolated state; a mismatch
  produces confusing hangs rather than clear failures.
- Never `sleep` or `Thread.sleep` to wait for async work. Await it, or use a continuation.
- Inject clocks (`ContinuousClock`/`SuspendingClock` or your own protocol) rather than measuring
  wall time.

## Test doubles

Swift has no runtime mocking library worth using — hand-write doubles against a protocol:

```swift
final class SpyUserRepository: UserRepository {
    private(set) var saved: [User] = []
    var stubbedUsers: [User] = []
    func all() async throws -> [User] { stubbedUsers }
    func save(_ user: User) async throws { saved.append(user) }
}
```

If a dependency is a concrete type with no protocol, extracting one is usually the smallest
testability fix — propose it rather than working around it.

For network, `URLProtocol` subclassing intercepts `URLSession` without touching the network:
register a stub `URLProtocol` on a `URLSessionConfiguration.ephemeral` and inject that session.

## XCUITest

```swift
let app = XCUIApplication()
app.launchArguments += ["-uitesting"]        // let the app stub its backend
app.launch()
app.buttons["Add to cart"].tap()
XCTAssertTrue(app.staticTexts["1 item"].waitForExistence(timeout: 2))
```

- Query by accessibility identifier (`accessibilityIdentifier`), never by displayed label — labels
  are localized and change.
- `waitForExistence(timeout:)` instead of asserting immediately; the UI is asynchronous.
- UI tests are slow and flaky by nature. Cover behavior at the unit level and reserve XCUITest for
  a handful of critical flows.

## Running

```bash
swift test                                     # SwiftPM
swift test --filter PriceFormatterTests

xcodebuild test -scheme MyApp \
  -destination 'platform=iOS Simulator,name=iPhone 16' -quiet

# one test only (Swift Testing and XCTest alike)
xcodebuild test -scheme MyApp \
  -destination 'platform=iOS Simulator,name=iPhone 16' \
  -only-testing:MyAppTests/PriceFormatterTests/testFormatsZeroAsFree -quiet
```

`xcodebuild` output is enormous — always `-quiet`, and pipe through `grep -E 'error:|failed|passed'`
or `xcbeautify` if available. Never paste a full build log.

## Coverage

```bash
xcodebuild test -scheme MyApp -enableCodeCoverage YES \
  -destination 'platform=iOS Simulator,name=iPhone 16' \
  -resultBundlePath /tmp/result.xcresult -quiet

xcrun xccov view --report --only-targets /tmp/result.xcresult
xcrun xccov view --report --files-for-target MyApp /tmp/result.xcresult
```

SwiftPM: `swift test --enable-code-coverage`, then
`xcrun llvm-cov report .build/debug/<Module>PackageTests.xctest/Contents/MacOS/<...> -instr-profile .build/debug/codecov/default.profdata`.

Exclude generated code and UI boilerplate from judgement rather than testing it; report uncovered
branches as `File.swift:line`.
