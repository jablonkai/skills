# Kotlin, KMP and Compose Multiplatform documentation

KDoc comments in the source, Dokka to render them. Dokka understands Kotlin's source-set model, so a
multiplatform project gets one site with per-platform annotations rather than one site per target —
that is the main reason to use it over anything generic.

## Contents

- [KDoc syntax](#kdoc-syntax)
- [Tags](#tags)
- [Links and references](#links-and-references)
- [Samples that compile](#samples-that-compile)
- [Dokka setup](#dokka-setup)
- [Multiplatform source sets](#multiplatform-source-sets)
- [Documenting expect/actual](#documenting-expectactual)
- [Finding undocumented symbols](#finding-undocumented-symbols)
- [Modules and packages](#modules-and-packages)

## KDoc syntax

`/** ... */` before the declaration. The first paragraph up to the first blank line is the summary
shown in listings, so it must stand alone — a summary that continues into the next paragraph reads
as a truncated fragment everywhere it is indexed.

```kotlin
/**
 * Uploads [file] to the configured bucket and returns its public URL.
 *
 * The upload is retried up to three times with exponential backoff. The call suspends until the
 * object is durably stored; cancelling the coroutine aborts the in-flight request but does not
 * delete an already-committed object.
 *
 * @param file the local file to upload; must exist and be readable
 * @param contentType MIME type stored with the object, defaults to detection from the extension
 * @return the public HTTPS URL of the stored object
 * @throws IOException if the file cannot be read
 * @throws StorageException if the bucket rejects the object after all retries
 * @sample com.example.storage.samples.uploadAvatar
 */
suspend fun upload(file: File, contentType: String? = null): String
```

Markdown works in KDoc bodies: lists, fenced code blocks, emphasis, tables.

## Tags

| Tag | Use |
|---|---|
| `@param name` | One per parameter that needs more than its name says |
| `@return` | Omit when the summary already states what comes back |
| `@throws` / `@exception` | One per exception a caller must handle, with its condition |
| `@receiver` | The receiver of an extension function |
| `@property name` | A constructor `val`/`var` — documented on the class, not the parameter |
| `@constructor` | The primary constructor, when it needs its own explanation |
| `@sample` | Fully-qualified name of a function whose body is inlined as an example |
| `@see` | Related declaration |
| `@since` | Version that introduced the declaration |
| `@suppress` | Exclude the declaration from generated output |

Kotlin has no `@deprecated` tag — use the `@Deprecated` annotation, which Dokka renders with its
message and replacement.

## Links and references

`[Foo]` links to a declaration in scope; `[com.example.Foo.bar]` links by qualified name;
`[custom text][Foo]` sets the link text. Dokka warns on unresolved links, which is the cheapest
drift detector available: a broken link almost always means a symbol was renamed.

## Samples that compile

`@sample` inlines the body of a real function, so the example is compiled by the build and breaks CI
when the API changes. Put samples in their own source set so they never ship in the artifact:

```kotlin
// build.gradle.kts
dokka {
    dokkaSourceSets.configureEach {
        samples.from("src/samples/kotlin")
    }
}
```

```kotlin
// src/samples/kotlin/com/example/storage/samples/UploadSamples.kt
package com.example.storage.samples

fun uploadAvatar() {
    val storage = Storage(bucket = "avatars")
    val url = runBlocking { storage.upload(File("avatar.png")) }
    println(url)
}
```

Prefer `@sample` over a fenced code block in the comment whenever the example touches the API being
documented — a fenced block is never compiled and will drift.

## Dokka setup

Dokka 2.x uses the `org.jetbrains.dokka` plugin with a `dokka { }` extension:

```kotlin
plugins {
    id("org.jetbrains.dokka") version "2.0.0"
}

dokka {
    moduleName.set("storage-core")
    dokkaSourceSets.configureEach {
        includes.from("Module.md")
        documentedVisibilities.set(setOf(VisibilityModifier.Public))
        sourceLink {
            localDirectory.set(file("src"))
            remoteUrl("https://github.com/example/repo/tree/main/storage-core/src")
            remoteLineSuffix.set("#L")
        }
        externalDocumentationLinks.register("coroutines") {
            url("https://kotlinlang.org/api/kotlinx.coroutines/")
        }
    }
}
```

Common tasks — check `./gradlew tasks --group documentation` for what the resolved version exposes:

| Task | Output |
|---|---|
| `dokkaGenerate` | All configured publications (Dokka 2.x) |
| `dokkaGeneratePublicationHtml` | HTML site under `build/dokka/html` |
| `dokkaGeneratePublicationJavadoc` | Javadoc-style HTML, for Maven Central's javadoc jar |

For a multi-module build, apply the plugin to the root project and add each module with the
`dokka(project(":module"))` dependency so the modules cross-link into one site.

Older builds may still be on Dokka 1.x (`dokkaHtml`, `dokkaHtmlMultiModule`, `dokkaGfm`). Do not
migrate the project's Dokka version as a side effect of a documentation request — that is a build
change with its own review.

## Multiplatform source sets

Dokka reads the Kotlin source-set graph, so `commonMain` documentation appears once and each
platform's additions are tagged with their target. Two consequences worth knowing:

- Document in the **most common** source set that can hold the declaration. A comment on
  `commonMain` covers every platform; the same comment copied into `androidMain` and `iosMain` is
  two copies to keep in sync.
- Platform-only APIs are automatically labelled in the output. Do not hand-write "Android only" into
  the summary — Dokka already renders the platform chip, and the prose version goes stale when a
  target is added.

Suppress a source set that should not appear at all (test fixtures, generated bindings):

```kotlin
dokka {
    dokkaSourceSets.named("jvmTest") { suppress.set(true) }
}
```

## Documenting expect/actual

Document the `expect` declaration — that is the API callers of common code see, and it is where the
contract belongs. An `actual` gets its own comment only when it adds platform behavior a caller must
account for:

```kotlin
// commonMain
/**
 * Returns the platform's persistent cache directory, creating it if absent.
 *
 * @throws IOException if the directory cannot be created
 */
expect fun cacheDirectory(): Path

// iosMain
/**
 * Resolves to `NSCachesDirectory`, which iOS may purge under storage pressure — callers must
 * tolerate the directory being empty between launches.
 */
actual fun cacheDirectory(): Path
```

## Finding undocumented symbols

Kotlin has no built-in `missing_docs` warning. Two practical options:

```bash
# Dokka reports unresolved links and, with reportUndocumented, missing docs
./gradlew dokkaGenerate 2>&1 | grep -iE 'warn|undocumented|unresolved'
```

```kotlin
dokka {
    dokkaSourceSets.configureEach {
        reportUndocumented.set(true)
        failOnWarning.set(false)   // true only once the backlog is cleared
    }
}
```

Projects using detekt can enable the `UndocumentedPublicClass`, `UndocumentedPublicFunction` and
`UndocumentedPublicProperty` rules, which surface the same gaps inline in the IDE. Enable them only
when the user asks — turning on a lint rule across an undocumented codebase floods the build.

## Modules and packages

`Module.md` supplies overview prose that has no declaration to attach to:

```markdown
# Module storage-core

Bucket-backed object storage shared across platforms.

# Package com.example.storage

Entry points: [Storage] for uploads, [StorageConfig] for credentials and endpoints.
```

Wire it up with `includes.from("Module.md")` as shown above. This is the right home for the
"where do I start" paragraph — it is the first thing on the generated landing page.
