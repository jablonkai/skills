# Swift documentation with DocC

DocC is Apple's documentation compiler: it reads `///` markup from the source, merges it with a
`.docc` catalog of articles and tutorials, and produces a navigable archive. Unlike most doc
toolchains it treats curation as a first-class concern — an uncurated DocC site is an alphabetical
symbol dump, so the Topics sections are where the value is.

## Contents

- [Symbol documentation](#symbol-documentation)
- [Markup callouts](#markup-callouts)
- [Links](#links)
- [Documentation catalogs](#documentation-catalogs)
- [Curation with Topics](#curation-with-topics)
- [Articles and tutorials](#articles-and-tutorials)
- [Building](#building)
- [Static hosting](#static-hosting)
- [Availability and platform notes](#availability-and-platform-notes)

## Symbol documentation

```swift
/// Uploads a file to the configured bucket and returns its public URL.
///
/// The upload is retried up to three times with exponential backoff. The call suspends until the
/// object is durably stored; cancelling the task aborts the in-flight request but does not delete
/// an already-committed object.
///
/// ```swift
/// let url = try await storage.upload(fileURL, contentType: "image/png")
/// ```
///
/// - Parameters:
///   - fileURL: A file URL that must exist and be readable.
///   - contentType: MIME type stored with the object. Defaults to detection from the extension.
/// - Returns: The public HTTPS URL of the stored object.
/// - Throws: ``StorageError/rejected(_:)`` if the bucket rejects the object after all retries.
public func upload(_ fileURL: URL, contentType: String? = nil) async throws -> URL
```

The first paragraph is the abstract used in every listing; keep it to one sentence. A blank `///`
line separates the abstract from the discussion.

For a single parameter, `- Parameter fileURL: ...` is idiomatic; use the `- Parameters:` list once
there are two or more.

## Markup callouts

| Callout | Renders as |
|---|---|
| `- Note:` | Grey informational box |
| `- Important:` | Emphasised box for things that break if ignored |
| `- Warning:` | Red box — data loss, crashes, security |
| `- Tip:` | Suggestion box |
| `- Precondition:` / `- Postcondition:` / `- Invariant:` | Contract boxes |
| `- Complexity:` | Algorithmic complexity, e.g. `O(n log n)` |
| `- SeeAlso:` | Related-symbol link |

Concurrency and actor isolation belong in these boxes rather than in prose — a `- Warning:` that a
method must be called from the main actor is read; the same sentence buried in paragraph three is
not.

## Links

- ``` ``SymbolName`` ``` — link to a symbol; ``` ``Storage/upload(_:contentType:)`` ``` for a member,
  using the full selector so overloads resolve
- `<doc:ArticleName>` — link to an article in the catalog
- `<doc:tutorials/TutorialName>` — link to a tutorial
- Standard Markdown `[text](https://…)` for external links

DocC emits a warning for every unresolvable symbol link. Those warnings are the drift report: treat
them as findings, not noise.

## Documentation catalogs

A `.docc` directory alongside the source adds everything that has no symbol to hang off:

```
Sources/Storage/
├── Storage.swift
└── Storage.docc/
    ├── Storage.md              # landing page, same name as the module
    ├── GettingStarted.md       # article
    ├── Resources/
    │   └── overview.png
    └── Tutorials/
        └── UploadingFiles.tutorial
```

`Storage.md` is the module landing page and uses an extension-file header:

```markdown
# ``Storage``

Bucket-backed object storage for Apple platforms.

@Metadata {
    @DisplayName("Storage Kit")
}

## Overview

Create a ``Storage`` with a bucket name, then call ``Storage/upload(_:contentType:)``.

## Topics

### Essentials

- <doc:GettingStarted>
- ``Storage``
- ``StorageConfiguration``

### Uploading

- ``Storage/upload(_:contentType:)``
- ``Storage/uploadStream(_:)``

### Errors

- ``StorageError``
```

## Curation with Topics

Without `## Topics`, DocC lists every symbol alphabetically under generic headings — technically
complete and nearly useless. Group symbols by what a reader is trying to do, ordered by how early
they need it. Any public symbol you leave out of a Topics section still appears, so curation is
about ordering and emphasis, not exclusion.

The same mechanism works on a type: add a `Storage.md` extension file with a `## Topics` section to
curate that type's members.

## Articles and tutorials

- **Articles** are plain Markdown files in the catalog — conceptual explanations, getting-started
  guides, migration notes. Linked with `<doc:Name>`.
- **Tutorials** use `.tutorial` files with a directive syntax (`@Tutorial`, `@Section`, `@Steps`,
  `@Code`, `@Image`) and produce Apple's step-by-step format with live code diffs. They are
  substantially more work than articles; only build one when the user asks for the guided format,
  because each `@Code` step references a real file that must be kept in sync.

## Building

Swift Package Manager, via the Swift-DocC plugin in `Package.swift`:

```swift
dependencies: [
    .package(url: "https://github.com/apple/swift-docc-plugin", from: "1.0.0")
]
```

```bash
swift package generate-documentation --target Storage
swift package --disable-sandbox preview-documentation --target Storage
```

Xcode projects: **Product → Build Documentation**, or from the command line —

```bash
xcodebuild docbuild -scheme Storage -destination 'generic/platform=iOS' \
  -derivedDataPath build 2>&1 | grep -iE 'warning:|error:'
```

Both produce a `.doccarchive`. Filter the output; `xcodebuild` is extremely verbose and the archive
itself is build output that should never be read back.

## Static hosting

To serve the archive from a subpath such as GitHub Pages:

```bash
swift package --allow-writing-to-directory ./docs \
  generate-documentation --target Storage \
  --disable-indexing \
  --transform-for-static-hosting \
  --hosting-base-path my-repo \
  --output-path ./docs
```

`--hosting-base-path` must match the repository name for a project Pages site, or be omitted for a
user/organisation site — a mismatch produces a page that loads and then 404s on every asset.

## Availability and platform notes

Do not hand-write "iOS 16+" into an abstract. DocC renders availability from `@available`
attributes, and the annotation stays true when the deployment target moves while the prose does not.
Use the discussion for behavior that *differs* by platform, which the attributes cannot express.
