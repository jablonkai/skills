# Rust and C / C++

## Rust — where tests live

| Location | Sees | Use for |
|---|---|---|
| `#[cfg(test)] mod tests` in the source file | Private items of that module | Unit tests — the default in Rust |
| `tests/*.rs` | Only the crate's public API | Integration tests, one binary per file |
| `///` doc comments | Public API, compiled and run | Examples that must stay correct |
| `benches/*.rs` | Public API | Criterion benchmarks |

Unit tests living beside the code is idiomatic Rust, not a compromise — `#[cfg(test)]` means they
are not compiled into the release binary. Do not move them to `tests/` "for tidiness"; that
changes what they can see.

```rust
pub fn parse(input: &str) -> Result<Config, ParseError> { … }

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_minimal_config() {
        let cfg = parse("name = \"x\"").expect("valid input");
        assert_eq!(cfg.name, "x");
    }

    #[test]
    fn rejects_trailing_comma() {
        assert!(matches!(parse("a = 1,"), Err(ParseError::Syntax { .. })));
    }

    #[test]
    #[should_panic(expected = "index out of bounds")]
    fn panics_on_bad_index() { … }
}
```

- Assert on the `Err` **variant**, not on its `Display` string — messages are not a contract.
- `expect("why this should hold")` in tests instead of `unwrap()`: the message becomes the failure
  report.
- `#[should_panic]` must always carry `expected = "…"`, otherwise it passes on the wrong panic.
- `assert_eq!` prints both values; `assert!(a == b)` does not. Prefer the former.

## Rust — async, fixtures, properties

```rust
#[tokio::test]
async fn retries_until_success() { … }

#[tokio::test(start_paused = true)]        // virtual time — no real sleeping
async fn times_out_after_30s() {
    tokio::time::advance(Duration::from_secs(31)).await;
}
```

- `#[tokio::test(flavor = "multi_thread")]` only when the test needs real parallelism.
- `async-std` uses `#[async_std::test]`; `smol`/`futures` use `futures::executor::block_on`.
- **rstest** for fixtures and parameterized cases:
  `#[rstest] #[case(0, "Free")] #[case(1, "$1")] fn formats(#[case] input: u32, #[case] want: &str)`.
- **proptest** / **quickcheck** for invariants that should hold for all inputs:

```rust
proptest! {
    #[test]
    fn roundtrips(cfg in any::<Config>()) {
        prop_assert_eq!(parse(&render(&cfg)).unwrap(), cfg);
    }
}
```

Property tests are worth their cost on parsers, serializers, and anything with an inverse. They
shrink failing inputs automatically — the shrunk case is the bug report.

- **insta** for snapshot assertions (`assert_snapshot!`); review `.snap` diffs with
  `cargo insta review`, never accept blindly.
- **criterion** in `benches/` for performance (`cargo bench`) — a benchmark is not a test; do not
  assert on timings in the test suite.

## Rust — running and coverage

```bash
cargo test                            # unit + integration + doc-tests
cargo test --lib parse::              # filter by path substring
cargo test -- --nocapture             # see println! output
cargo test --doc                      # doc-tests only
cargo nextest run                     # faster runner, better output, if installed

cargo llvm-cov --html                 # target/llvm-cov/html/index.html
cargo llvm-cov --summary-only
```

`cargo test` output is compact already; still filter to `FAILED`/`failures:` on a large suite.

## C++ — GoogleTest

```cpp
#include <gtest/gtest.h>
#include "price_formatter.h"

TEST(PriceFormatter, FormatsZeroAsFree) {
    EXPECT_EQ(Format(0), "Free");
}

TEST(PriceFormatter, RejectsNegative) {
    EXPECT_THROW(Format(-1), std::invalid_argument);
}

class CartTest : public ::testing::Test {
 protected:
    void SetUp() override { cart_ = std::make_unique<Cart>(); }
    std::unique_ptr<Cart> cart_;
};

TEST_F(CartTest, StartsEmpty) { EXPECT_TRUE(cart_->Empty()); }
```

- `EXPECT_*` continues after failure; `ASSERT_*` returns from the test — use `ASSERT` when
  continuing would crash (null pointer, empty container).
- `EXPECT_EQ` on floating point is a bug; use `EXPECT_NEAR(a, b, eps)` or `EXPECT_DOUBLE_EQ`.
- `TEST_P` + `INSTANTIATE_TEST_SUITE_P` for parameterized cases.
- **GoogleMock** for interaction tests: `MOCK_METHOD(void, Save, (const User&), (override));`,
  then `EXPECT_CALL(repo, Save(_)).Times(1);`. Mock against an abstract interface — mocking a
  concrete class means editing it.
- Death tests (`EXPECT_DEATH`) for assertions/aborts; they are slow, use sparingly.

## C++ — Catch2

```cpp
#include <catch2/catch_test_macros.hpp>

TEST_CASE("format handles boundaries", "[price]") {
    REQUIRE(Format(0) == "Free");

    SECTION("negative input throws") {
        REQUIRE_THROWS_AS(Format(-1), std::invalid_argument);
    }
}
```

`REQUIRE` aborts the section, `CHECK` continues. `SECTION` re-runs the enclosing body per section,
which gives fixture behavior with no fixture class.

## C++ — CMake wiring and running

```cmake
enable_testing()
find_package(GTest REQUIRED)
add_executable(price_tests price_formatter_test.cpp)
target_link_libraries(price_tests PRIVATE price_lib GTest::gtest_main)
include(GoogleTest)
gtest_discover_tests(price_tests)      # registers each TEST with CTest
```

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build -j
ctest --test-dir build --output-on-failure
ctest --test-dir build -R PriceFormatter          # filter by name
./build/price_tests --gtest_filter='PriceFormatter.*'
```

## C++ — sanitizers and coverage

Sanitizers catch what assertions cannot; run the suite under them in CI at least:

```bash
cmake -S . -B build-asan -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer"
ctest --test-dir build-asan --output-on-failure
```

Coverage:

```bash
cmake -S . -B build-cov -DCMAKE_CXX_FLAGS="--coverage -O0 -g"
cmake --build build-cov -j && ctest --test-dir build-cov
gcovr -r . --html-details -o coverage.html        # or: llvm-cov with -fprofile-instr-generate
```

Exclude third-party and generated sources from the report; report uncovered branches as
`file.cpp:line`.
