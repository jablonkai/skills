# Rust and C++ documentation

Two toolchains with opposite defaults: rustdoc is built in, compiles the examples, and warns about
almost everything; Doxygen is external, configured by a large generated file, and warns only when
told to. The Rust half is the shorter read because the toolchain does more of the work.

## Contents

- [Rust: rustdoc](#rust-rustdoc)
  - [Comment syntax](#comment-syntax)
  - [Doc-tests](#doc-tests)
  - [Intra-doc links](#intra-doc-links)
  - [Crate-level docs and README reuse](#crate-level-docs-and-readme-reuse)
  - [Lints that find gaps](#lints-that-find-gaps)
  - [Building and docs.rs](#building-and-docsrs)
- [C++: Doxygen](#c-doxygen)
  - [Comment styles](#comment-styles)
  - [Common commands](#common-commands)
  - [Doxyfile settings that matter](#doxyfile-settings-that-matter)
  - [Running Doxygen](#running-doxygen)
  - [Breathe and Sphinx](#breathe-and-sphinx)

---

## Rust: rustdoc

### Comment syntax

`///` documents the item that follows; `//!` documents the enclosing item (a module or the crate).
Markdown throughout. The first line is the summary shown in every listing.

```rust
/// Uploads `file` to the configured bucket and returns its public URL.
///
/// The upload is retried up to three times with exponential backoff. Cancelling the future aborts
/// the in-flight request but does not delete an already-committed object.
///
/// # Errors
///
/// Returns [`Error::Io`] if the file cannot be read, and [`Error::Rejected`] if the bucket rejects
/// the object after all retries.
///
/// # Panics
///
/// Panics if the client was built without a bucket name.
///
/// # Examples
///
/// ```
/// # use storage::{Storage, Error};
/// # fn main() -> Result<(), Error> {
/// let storage = Storage::new("avatars")?;
/// let url = storage.upload("avatar.png")?;
/// assert!(url.starts_with("https://"));
/// # Ok(())
/// # }
/// ```
pub fn upload(&self, file: impl AsRef<Path>) -> Result<Url, Error>
```

The conventional section headings — `# Examples`, `# Errors`, `# Panics`, `# Safety` — are what
Rust developers scan for. `# Safety` is mandatory on `unsafe fn`: it states the invariants the caller
must uphold, and the `clippy::missing_safety_doc` lint enforces its presence.

### Doc-tests

Every fenced code block in a doc comment is compiled and run by `cargo test`. This makes rustdoc
examples the only documentation in the codebase that cannot silently rot, which is worth exploiting:
prefer a doc-test over prose whenever the example fits in a few lines.

```bash
cargo test --doc
```

Lines prefixed with `#` are compiled but hidden from the rendered output — use them for imports and
`main` boilerplate so the visible example stays about the API.

Fence attributes control what happens:

| Attribute | Behavior |
|---|---|
| (none) | Compiled and run |
| `no_run` | Compiled, not run — for network, filesystem, or long-running examples |
| `ignore` | Neither compiled nor run; a last resort, since it hides drift |
| `should_panic` | Must panic to pass |
| `compile_fail` | Must fail to compile — useful for documenting what the type system prevents |
| `text` | Not Rust; rendered as plain text |

Reach for `no_run` before `ignore`: it still catches signature changes.

### Intra-doc links

```rust
/// See [`Storage::upload`], [`crate::Config`], and [`Error::Io`] for the failure case.
```

A link target can also be written as a reference definition (`` [`Error::Io`]: crate::Error::Io ``)
when the same symbol is linked repeatedly, and the inline form `[text]` followed by
`(crate::module::Item)` in parentheses gives the link custom text.

Enable the lint so a rename that orphans a link fails the build rather than shipping:

```rust
#![deny(rustdoc::broken_intra_doc_links)]
```

### Crate-level docs and README reuse

`//!` at the top of `lib.rs` is the crate landing page. To keep it identical to the README without
maintaining two copies:

```rust
#![doc = include_str!("../README.md")]
```

The README's code blocks then run as doc-tests, which catches the classic failure of a README
example that stopped compiling three releases ago. Mark non-Rust blocks in the README with a
language tag so rustdoc skips them.

### Lints that find gaps

```rust
#![warn(missing_docs)]                       // every public item
#![warn(clippy::missing_errors_doc)]         // every fn returning Result needs # Errors
#![warn(clippy::missing_panics_doc)]         // every fn that can panic needs # Panics
#![warn(clippy::missing_safety_doc)]         // every unsafe fn needs # Safety
```

```bash
cargo doc --no-deps 2>&1 | grep -E '^(warning|error)' | head -40
```

### Building and docs.rs

```bash
cargo doc --no-deps --open        # this crate only, opened in a browser
cargo doc --workspace --no-deps
```

`--no-deps` matters: without it the build documents the entire dependency tree, which is slow and
produces output nobody reads.

For crates published to docs.rs, feature-gated APIs need annotations or they render as if they do
not exist:

```toml
[package.metadata.docs.rs]
all-features = true
rustdoc-args = ["--cfg", "docsrs"]
```

```rust
#![cfg_attr(docsrs, feature(doc_cfg))]

#[cfg(feature = "async")]
#[cfg_attr(docsrs, doc(cfg(feature = "async")))]
pub mod r#async;
```

Never read `target/doc/` back — it is build output.

---

## C++: Doxygen

### Comment styles

Doxygen accepts several; pick the one the project already uses and do not mix them. `/** */` with
`@`-prefixed commands is the most common:

```cpp
/**
 * @brief Uploads a file to the configured bucket.
 *
 * The upload is retried up to three times with exponential backoff. Blocks until the object is
 * durably stored.
 *
 * @param[in]  path        Path to a readable local file.
 * @param[in]  contentType MIME type stored with the object; empty means detect from the extension.
 * @param[out] url         Receives the public HTTPS URL on success.
 * @return `true` on success, `false` if the bucket rejected the object.
 * @throws std::system_error if @p path cannot be read.
 * @note Not thread-safe; one Storage instance per thread.
 * @see StorageConfig
 */
bool upload(const std::filesystem::path& path,
            std::string_view contentType,
            std::string& url);
```

`///` and `//!` work as one-line equivalents; `///<` documents the preceding member on the same line,
which is the readable choice for enum values and struct fields.

C++ makes ownership and lifetime invisible in the signature more often than other languages, so
document who owns a returned pointer, how long a returned reference stays valid, and whether a
callback may be invoked after the object is destroyed. Those are the questions the header cannot
answer.

### Common commands

| Command | Use |
|---|---|
| `@brief` | One-line summary (required when `AUTOBRIEF` is off) |
| `@param[in]`, `@param[out]`, `@param[in,out]` | Parameter with direction |
| `@tparam` | Template parameter |
| `@return`, `@retval` | Return value; `@retval` per specific value |
| `@throws` | Exception and its condition |
| `@pre`, `@post`, `@invariant` | Contract |
| `@note`, `@warning`, `@attention` | Callout boxes |
| `@code` / `@endcode`, `@snippet file id` | Examples; `@snippet` pulls from a real compiled file |
| `@deprecated` | Deprecation notice |
| `@file`, `@defgroup`, `@ingroup` | File-level docs and grouping |

Prefer `@snippet` over `@code` for anything non-trivial: it references a real file that the build
compiles, so it behaves like a Rust doc-test instead of a comment that drifts.

### Doxyfile settings that matter

`doxygen -g Doxyfile` generates a fully commented default. The settings that change the result most:

```
PROJECT_NAME           = Storage
INPUT                  = include src
RECURSIVE              = YES
EXTRACT_ALL            = NO      # YES documents undocumented symbols too — hides the gaps
EXTRACT_PRIVATE        = NO
WARN_IF_UNDOCUMENTED   = YES     # the missing-docs report
WARN_IF_DOC_ERROR      = YES
WARN_AS_ERROR          = NO      # FAIL_ON_WARNINGS once the backlog is clear
WARN_LOGFILE           = doxygen-warnings.log
GENERATE_HTML          = YES
GENERATE_LATEX         = NO      # on by default and rarely wanted
GENERATE_XML           = NO      # YES only when feeding Breathe/Sphinx
EXAMPLE_PATH           = examples
USE_MDFILE_AS_MAINPAGE = README.md
```

`EXTRACT_ALL = YES` is the setting to question first in an existing project: it makes the site look
complete while suppressing exactly the warnings this skill needs.

### Running Doxygen

```bash
doxygen Doxyfile 2>&1 | tail -5
grep -c 'warning' doxygen-warnings.log
grep 'is not documented' doxygen-warnings.log | head -40
```

The warning log is the deliverable of an audit run — it lists every undocumented public symbol and
every `@param` that no longer matches the signature, which is the most common form of C++ doc drift.

### Breathe and Sphinx

To render Doxygen output inside a Sphinx site (common when a C++ core has Python bindings):

```
GENERATE_XML = YES
XML_OUTPUT   = xml
```

```python
# conf.py
extensions = ["breathe"]
breathe_projects = {"storage": "../build/doxygen/xml"}
breathe_default_project = "storage"
```

```rst
.. doxygenclass:: storage::Storage
   :members:
```

Exhale generates the full API tree automatically on top of Breathe; add it only if the user wants a
complete browsable reference, since it produces a large generated tree that must be gitignored.
