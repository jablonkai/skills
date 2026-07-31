# Refactoring Rust and C/C++

Two languages with opposite defaults — Rust's compiler and linter do most of the work and the risk
is over-abstraction; C++ has weaker guarantees and the risk is that a "safe" refactoring changes
lifetimes, aliasing, or ABI.

## Contents

- [Rust: tooling](#rust-tooling)
- [Rust: idioms worth refactoring toward](#rust-idioms-worth-refactoring-toward)
- [Rust: trimming clone and unwrap](#rust-trimming-clone-and-unwrap)
- [Rust: dead code](#rust-dead-code)
- [Rust: verification](#rust-verification)
- [C++: tooling](#c-tooling)
- [C++: RAII and ownership](#c-raii-and-ownership)
- [C++: idioms worth refactoring toward](#c-idioms-worth-refactoring-toward)
- [C++: dead code](#c-dead-code)
- [C++: verification](#c-verification)

---

## Rust: tooling

Clippy is unusually good at exactly this skill's job — most of its lints *are* refactorings, with
the rationale attached.

```bash
cargo clippy --all-targets --all-features -- -D warnings
cargo clippy --fix --allow-dirty           # applies the machine-applicable subset
cargo fmt
cargo +nightly udeps                       # unused dependencies
```

Worth enabling temporarily while refactoring, then removing:

```rust
#![warn(clippy::pedantic, clippy::nursery)]
#![warn(unused_crate_dependencies, unreachable_pub)]
```

`clippy::pedantic` produces a lot of noise; treat it as a list of candidates rather than a to-do
list, and never blanket-`allow` a lint at crate level to make it quiet — that hides the next real
instance.

`cargo clippy --fix` is the ideal level-1 step: machine-applicable, individually justified by a lint
name, and worth landing as its own commit.

## Rust: idioms worth refactoring toward

| Instead of | Prefer | Why |
|---|---|---|
| `match x { Ok(v) => v, Err(e) => return Err(e.into()) }` | `x?` | The entire point of `?`; removes a nesting level per call |
| Nested `match` on `Option` | `if let`, `let ... else`, or combinators (`map`, `and_then`, `ok_or`) | Flattens; `let else` gives a guard clause |
| `for` loop pushing into a `Vec` | `iter().map(...).collect()` | No mutable intermediate; often faster |
| `.iter().filter(...).count() > 0` | `.any(...)` | Short-circuits |
| `unwrap()` in library code | `?` with a real error type, or `expect("why")` | An `unwrap` is a panic with no explanation |
| `String`/`Vec<T>` parameters | `&str`/`&[T]` | Callers stop allocating to call you |
| `Box<dyn Trait>` in a hot path | Generic parameter with a trait bound | Static dispatch, no allocation |
| Stringly-typed state | Enum, or a newtype | The compiler starts checking it |
| Repeated `pub struct` field access across modules | Constructor + accessors, or a newtype with invariants | Invariants become enforceable |
| A `mod.rs` growing past readability | Split into submodules by responsibility | The module tree is the module structure |
| Manual `Display`/`Error` impls | `thiserror` for libraries, `anyhow` for binaries | Less boilerplate, better messages |

Two cautions specific to Rust. Iterator chains longer than three or four steps read worse than the
loop they replaced — extract a named function instead of extending the chain. And introducing a
lifetime parameter to avoid a `clone()` is only a win when the clone was actually on a hot path;
otherwise it propagates lifetime annotations through every caller for no measured benefit.

## Rust: trimming clone and unwrap

These two are the most-requested Rust cleanups, and both can change behavior if done carelessly.

**`clone()`** — before removing one, establish why it exists:

- *Borrow checker appeasement* — usually removable by restructuring: narrow the borrow's scope,
  split the struct so two fields can be borrowed independently, or take `&mut` later.
- *Genuine ownership transfer* — not removable, and the clone is correct.
- *`Arc`/`Rc` clone* — cheap by design; removing it is not an optimization.

Measure before treating clone removal as performance work. A `clone` of a small `String` once per
request is not what makes a service slow, and the lifetime annotations that replace it are permanent
readability cost.

**`unwrap()`/`expect()`** — the refactoring is to propagate rather than panic:

1. Change the function's return type to `Result<T, E>`.
2. Replace `unwrap()` with `?`.
3. The compiler now walks you up the call chain; convert each caller in turn.
4. At the top (`main`, a request handler, a test), decide where the error is actually handled.

Panics that are genuinely unreachable are fine — but write `expect("invariant: ...")` stating the
invariant, so the next reader knows whether it still holds.

## Rust: dead code

`cargo clippy` and `#[warn(dead_code)]` catch most of it, but they see only the current feature and
target combination. Before deleting:

- Compile with `--all-features` **and** with `--no-default-features` — code used only under a
  feature flag looks dead otherwise
- Check other targets: `--all-targets` includes benches, examples, and tests
- `pub` items in a library crate are never dead from the compiler's perspective —
  `#![warn(unreachable_pub)]` finds ones that are `pub` but not reachable from the crate root
- Rule out `#[no_mangle]`, `extern "C"`, `#[used]`, proc-macro-generated references, `build.rs`
  outputs, and anything named in a `serde` rename or a `#[derive]`

## Rust: verification

```bash
cargo check --all-targets --all-features
cargo test --all-features
cargo test --no-default-features
cargo clippy --all-targets -- -D warnings
cargo doc --no-deps                       # doc-tests and intra-doc links
```

For a published crate, add `cargo semver-checks` before changing anything `pub` — it turns
downstream breakage into a check instead of a guess. Behavior-preservation for `unsafe` code needs
more than tests: run the affected paths under `cargo miri test` where Miri supports them.

---

## C++: tooling

```bash
clang-tidy -p build/ <file.cpp>                       # needs compile_commands.json
run-clang-tidy -p build/ -fix                         # applies fixes across the project
clang-format -i <files>
cppcheck --enable=all --inconclusive <dir>
cmake -B build -DCMAKE_EXPORT_COMPILE_COMMANDS=ON     # generates compile_commands.json
```

clang-tidy check groups that map onto this skill: `modernize-*` (idiom upgrades, most with
fix-its), `readability-*` (complexity, naming, nesting), `bugprone-*`, `performance-*`,
`cppcoreguidelines-*`.

Compile with warnings on while refactoring — they find half of what a review would:

```bash
-Wall -Wextra -Wpedantic -Wshadow -Wconversion -Wold-style-cast
```

`run-clang-tidy -fix` with `modernize-*` alone is a large, mechanical, individually-justified
change. Land it separately from any structural work.

## C++: RAII and ownership

The highest-value C++ refactoring is replacing manual lifetime management with RAII, because it
converts a class of runtime bugs into a compile-time impossibility.

| Instead of | Prefer |
|---|---|
| `new`/`delete` pairs | `std::unique_ptr`, `std::make_unique` |
| Shared raw pointers with unclear ownership | `std::shared_ptr` — but only where ownership genuinely is shared |
| Raw pointer parameters that do not own | `T&`, `T*` documented as non-owning, or `std::span` |
| `malloc`/`free`, C arrays | `std::vector`, `std::array` |
| Manual `lock()`/`unlock()` | `std::scoped_lock`, `std::unique_lock` |
| `fopen`/`fclose`, manual handles | A small RAII wrapper, or `std::fstream` |
| Manual cleanup at every return | RAII, or a scope guard |

Two things to check on every ownership change: the type's rule-of-five (introducing a `unique_ptr`
member makes the class move-only, which breaks copies the compiler previously generated), and
whether any raw pointer escaping the type outlives its owner.

Do this refactoring behind the tests and one type at a time. A wholesale `new` → `make_unique`
sweep across a codebase with unclear ownership is how double-frees get introduced.

## C++: idioms worth refactoring toward

| Instead of | Prefer | Why |
|---|---|---|
| Raw loops over containers | Range-based `for`, then `<algorithm>` / `<ranges>` | States intent; the algorithm name is the comment |
| Index loops copying into a new container | `std::transform`, `std::copy_if`, ranges views | Fewer off-by-one opportunities |
| `T` by value in parameters | `const T&` for large types, `T&&`/by-value for sinks | Removes a copy per call |
| Missing `const` on members and parameters | `const`-correctness throughout | The compiler starts checking what you meant |
| Output parameters (`void f(T& out)`) | Return by value, structured bindings, `std::optional` | NRVO makes this free; the signature says what it does |
| Sentinel return values (`-1`, `nullptr`) | `std::optional`, `std::expected` (C++23) | The absent case stops being a convention |
| `#define` constants and macros | `constexpr`, `inline constexpr`, templates | Type-checked, scoped, debuggable |
| Deep `if` nesting | Guard clauses with early return | Same as elsewhere — mind cleanup, or use RAII |
| Typedef'd primitives for domain values | Strong types / tagged wrappers | Prevents argument-order mistakes |
| Preprocessor conditionals selecting behavior | `if constexpr`, templates, policy types | Visible to tooling and the type checker |

`const`-correctness is worth calling out: it is mechanical, it spreads (adding `const` to one method
forces it on the ones it calls), and it is best done bottom-up in a single dedicated pass.

## C++: dead code

Harder to prove than anywhere else, because the preprocessor hides references from every tool:

- `#ifdef`-guarded code for platforms and build configurations you are not compiling
- Symbols referenced only from another translation unit, a library consumer, or a plugin loaded at
  runtime (`dlopen`)
- `extern "C"` exports, symbols named in a version script or `.def` file
- Template code that is only instantiated in a configuration you are not building
- Virtual overrides — removing a "unused" override silently changes dispatch
- Anything reflected on by a serialization or binding framework

Build every configuration and platform before deleting, and prefer marking a symbol deprecated for a
release over removing it from a shared library — removal is an ABI break.

## C++: verification

```bash
cmake --build build -j                                  # every target
ctest --test-dir build --output-on-failure
clang-tidy -p build/ <changed files>
```

For anything touching memory or threading, the sanitizers are the real verification — tests alone do
not prove a refactoring preserved behavior in C++:

```bash
cmake -B build-asan -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -g"
cmake -B build-tsan -DCMAKE_CXX_FLAGS="-fsanitize=thread -g"
```

Run the suite under ASan/UBSan after ownership changes and under TSan after anything touching
concurrency. For a shared library, check ABI compatibility (`abi-compliance-checker`, or the
project's own tooling) before changing any exported type's layout — adding a member to a public
struct is an ABI break even though it compiles.
