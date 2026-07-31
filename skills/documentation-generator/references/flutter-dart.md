# Dart and Flutter documentation

`///` doc comments in the source, `dart doc` to render them, pub.dev to publish. The toolchain is
opinionated and the analyzer enforces most of it, so the work is mostly writing comments that pass
the lints already available.

## Contents

- [Doc comment syntax](#doc-comment-syntax)
- [Links and references](#links-and-references)
- [Templates and macros](#templates-and-macros)
- [Generating](#generating)
- [Lints for missing and broken docs](#lints-for-missing-and-broken-docs)
- [Package metadata and pub.dev](#package-metadata-and-pubdev)
- [Flutter widget documentation](#flutter-widget-documentation)

## Doc comment syntax

Use `///`, not `/** */` — the Dart style guide is explicit about it and `dart format` assumes it.
The first sentence is the summary used in listings and search results, so it must be a single
self-contained sentence ending in a period.

```dart
/// Uploads [file] to the configured bucket and returns its public URL.
///
/// The upload is retried up to three times with exponential backoff. Completes once the object is
/// durably stored; cancelling the returned future aborts the in-flight request but does not delete
/// an already-committed object.
///
/// Throws [FileSystemException] if [file] cannot be read, and [StorageException] if the bucket
/// rejects the object after all retries.
///
/// ```dart
/// final url = await storage.upload(File('avatar.png'));
/// ```
Future<String> upload(File file, {String? contentType}) async { ... }
```

Dart's conventions differ from most other stacks in two ways worth respecting:

- **No `@param`/`@return` tags.** Document parameters by naming them in the prose with `[brackets]`.
  Tag-per-parameter blocks are not idiomatic Dart and read as ported Javadoc.
- **Start with a noun phrase for getters and properties, a verb phrase for functions.** "The number
  of bytes written." for a getter; "Writes [data] to the socket." for a method.

## Links and references

`[Identifier]` links to anything in scope: classes, methods, parameters, top-level functions.
`[Foo.bar]` and `[package:foo/foo.dart]`-qualified forms work for symbols that are not imported.
Unresolved references are a warning under the `comment_references` lint — enable it, because a
broken reference is nearly always a renamed symbol whose docs were left behind.

## Templates and macros

Reuse a block of documentation across declarations without copying it:

```dart
/// {@template storage.retry_policy}
/// Retried three times with exponential backoff, starting at 200ms.
/// {@endtemplate}
Future<String> upload(File file) async { ... }

/// Deletes the object at [key].
///
/// {@macro storage.retry_policy}
Future<void> delete(String key) async { ... }
```

Other dartdoc directives:

| Directive | Use |
|---|---|
| `{@template name}` / `{@endtemplate}` | Define a reusable block |
| `{@macro name}` | Insert a defined block |
| `{@category Name}` | Group the declaration in the sidebar |
| `{@image url}` | Embed an image |
| `{@tool snippet}` | Flutter's framework-only snippet tooling |
| `{@nodoc}` | Exclude the declaration from output |

## Generating

```bash
dart doc .                       # writes to doc/api
dart doc . --output build/docs
dart doc . --validate-links      # fails on broken references
```

`dart doc` replaced the standalone `dartdoc` command; a project still calling `dartdoc` directly is
on an old SDK, and switching it is a toolchain change rather than a documentation change.

For Flutter packages the same command works from the package root — Flutter's own SDK docs are built
with extra tooling that packages do not need.

Read the warnings: unresolved references and undocumented public members are printed, and they are
the drift signal. Filter rather than pasting the run:

```bash
dart doc . --validate-links 2>&1 | grep -iE 'warning|error|unresolved' | head -40
```

## Lints for missing and broken docs

In `analysis_options.yaml`:

```yaml
linter:
  rules:
    - public_member_api_docs      # every public member needs a doc comment
    - comment_references          # [references] must resolve
    - slash_for_doc_comments      # /// not /** */
    - lines_longer_than_80_chars  # optional, but common in doc-heavy packages
```

`public_member_api_docs` on an undocumented package produces hundreds of findings at once. When
introducing it, say how many and offer to work through them by file rather than committing a wall of
`// ignore` comments.

```bash
dart analyze 2>&1 | grep public_member_api_docs | wc -l
```

## Package metadata and pub.dev

pub.dev builds a package's landing page from files that must exist and be current:

| File / field | Renders as |
|---|---|
| `pubspec.yaml` `description` | The one-line package summary and search snippet — 60–180 chars |
| `pubspec.yaml` `homepage`, `repository`, `issue_tracker`, `documentation` | Sidebar links |
| `README.md` | The main tab — what it is, install, minimal working example |
| `CHANGELOG.md` | The changelog tab; version headings must match published versions |
| `example/` or `example/lib/main.dart` | The example tab, verbatim |
| `LICENSE` | The license tab, and part of the pub points score |

`dart pub publish --dry-run` reports what is missing before publishing. The example directory is
worth more than any amount of prose: it is the only part of the docs that is compiled.

## Flutter widget documentation

A widget's doc comment answers what it renders and how it is composed, since callers read it while
choosing between widgets:

```dart
/// A card that displays a runner's split times for a single race.
///
/// Splits are laid out vertically and scroll independently of the surrounding page. The card sizes
/// itself to its content, so it must not be placed directly inside an unbounded [Column] without a
/// height constraint.
///
/// See also:
///
///  * [SplitTile], the row rendered for each split.
///  * [RaceSummaryCard], which shows the aggregate result instead.
class SplitsCard extends StatelessWidget { ... }
```

The "See also" bullet list is the framework's own convention and reads naturally to Flutter
developers — use it for sibling widgets and the types a caller reaches for next. Document layout
constraints explicitly (bounded vs unbounded, intrinsic sizing): those are the failure modes callers
hit, and the signature cannot express them.
