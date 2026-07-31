---
name: documentation-generator
description: "Generate and update documentation from what the code already knows: API reference from doc comments (KDoc/Dokka, dartdoc, DocC, rustdoc, Doxygen), REST docs from an OpenAPI spec, README scaffolding from package metadata, changelogs from conventional commits, and architecture diagrams from module structure. Also fills in missing doc comments and finds docs that drifted from the implementation. Use when someone says 'generate the docs', 'document this API', 'add KDoc/dartdoc/DocC/rustdoc comments', 'set up Dokka', 'write the README', 'generate a changelog', 'the docs are out of date', or the Hungarian 'generáld a dokumentációt', 'dokumentáld ezt az API-t', 'írd meg a README-t', 'frissítsd a changelogot'. Not for prose docs written from scratch with the user (that is doc-coauthoring), not for looking up someone else's library docs (that is find-docs)."
summary: "generate and refresh documentation from code — doc comments and API reference via Dokka, dartdoc, DocC, rustdoc and Doxygen, OpenAPI-driven REST docs, README scaffolding, conventional-commit changelogs, and architecture diagrams"
category: documentation
risk: low
tags:
  - documentation
  - api-docs
  - changelog
  - openapi
  - kotlin
  - flutter
  - swift
  - rust
  - cpp
allowed-tools: Bash, Read, Grep, Glob, Edit, Write, Skill
argument-hint: "[module, package, spec file, or doc type to generate]"
---

# documentation-generator

## Purpose

Produce documentation whose source of truth is the code, not a separate document that starts
accurate and rots. The input is a codebase, a module, or an API spec; the output is doc comments in
the source, a generated reference site, a README, a changelog, or a diagram — plus an honest list of
what is still undocumented.

Documentation that is written *beside* the code drifts within weeks. Documentation *derived* from
the code drifts only when someone changes a signature without changing its comment — which a
generator can detect and report. That detection is most of the value here; typing prose is the
cheap part.

## When to use

- A public API has no reference docs, or its docs are stale after a refactor
- Doc comments are missing on public symbols and the toolchain warns about it
- An OpenAPI spec exists and the human-readable REST docs do not
- A release needs a changelog and the commits follow a convention
- A new contributor needs a README or an architecture overview to orient themselves

Not this skill:

- **Writing a design doc, proposal, or spec with the user** → `doc-coauthoring`
- **Looking up documentation for a third-party library** → `find-docs`
- **A whole-project audit that happens to flag documentation gaps** → `code-analyzer`
- **Hand-drawing a specific diagram rather than deriving one** → `draw-io-diagram-generator`
- **Converting existing documents between formats** → `markitdown`

## Prerequisites

**1. What is being documented, and which toolchain already owns it?** Detect from build files, not
from file extensions — the doc toolchain is declared there, and a project that already has one has
already made most of the decisions.

| Build file / signal | Stack | Reference |
|---|---|---|
| `build.gradle.kts` with `kotlin("multiplatform")` or `org.jetbrains.dokka` | Kotlin / KMP / CMP | [kotlin-kmp.md](references/kotlin-kmp.md) |
| `pubspec.yaml` | Flutter / Dart | [flutter-dart.md](references/flutter-dart.md) |
| `Package.swift`, `*.xcodeproj`, `*.docc/` | Swift (iOS/macOS) | [swift-apple.md](references/swift-apple.md) |
| `Cargo.toml` | Rust | [rust-cpp.md](references/rust-cpp.md) |
| `CMakeLists.txt`, `Doxyfile`, `conanfile.txt` | C / C++ | [rust-cpp.md](references/rust-cpp.md) |
| `openapi.yaml`, `swagger.json`, `paths:` + `components:` | REST API spec | [api-specs.md](references/api-specs.md) |
| `package.json`, `pyproject.toml`, `go.mod` | JS/TS, Python, Go | [other-languages.md](references/other-languages.md) |
| README, CHANGELOG, diagrams, versioned sites | Any — cross-cutting | [project-docs.md](references/project-docs.md) |

Load one stack reference plus, when the task needs it, `project-docs.md`. Loading all of them mixes
idioms from toolchains that are not in play and buries the ones that are.

**2. What documentation already exists?** Read the current docs before generating anything —
a `docs/` directory, an existing README, three or four already-documented public symbols. Their
voice, depth, and structure are already decided; matching them matters more than any convention in
this skill. A generated page that reads nothing like its neighbours will be rewritten by hand.

```bash
# existing docs, doc config, and the conventions already in use
ls -d docs doc site .docc *.docc 2>/dev/null
find . -maxdepth 2 \( -name 'Doxyfile*' -o -name 'mkdocs.yml' -o -name 'dokka*' \
  -o -name '*.docc' -o -name 'cliff.toml' -o -name 'redocly.yaml' \) -not -path '*/build/*'
```

**3. Is the code stable enough to document?** Documenting an API that is about to change wastes the
work twice. If the target is mid-refactor, say so and offer to document the parts that are settled.

## Workflow

### Step 1: Decide what the reader needs

Documentation fails far more often from wrong altitude than from bad prose. Pick the type from who
is reading and what they are trying to do:

| Reader's question | Artifact | Derived from |
|---|---|---|
| "What does this function do?" | API reference | Doc comments on public symbols |
| "How do I call this endpoint?" | REST reference | OpenAPI spec |
| "How do I start using this?" | README / getting started | Package metadata + a real working example |
| "How does this fit together?" | Architecture overview | Module graph, layering, key types |
| "What changed?" | Changelog | Commit history |
| "How do I accomplish X?" | Guide / tutorial | Neither — this is written, not generated |

The last row matters: a guide cannot be derived from signatures, because the ordering and the
motivation live in the author's head. When the user asks for one, either gather that context from
them or hand off to `doc-coauthoring`.

### Step 2: Find what is undocumented

Let the toolchain answer this instead of reading files: every stack has a warning for missing docs
on public symbols. The stack reference gives the exact switch — `#![warn(missing_docs)]` in Rust,
`public_member_api_docs` in Dart, `WARN_IF_UNDOCUMENTED` in Doxygen, and so on.

Rank the gaps rather than filing them alphabetically:

1. **Public API surface first.** What callers cannot see, they do not need documented.
2. **Entry points before leaves.** The type someone constructs first earns a comment before its
   private helper does.
3. **Non-obvious behavior before obvious behavior.** Units, threading, nullability, ownership,
   error conditions, and side effects are what readers actually come for.

A comment restating the signature (`/** Returns the name. */` on `getName()`) is noise: it adds
maintenance cost and no information. Skip it, and say you skipped it and why.

### Step 3: Write the doc comments

Write in the source, in the stack's markup, with its tags — the stack reference has the syntax and
the idioms. Across all of them, the same things separate a useful comment from filler:

- **Lead with the contract, not the mechanism.** What it guarantees, not how it is implemented —
  implementations change, contracts are what callers depend on.
- **Document what the signature cannot say**: units, valid ranges, nullability, thread/isolate/actor
  affinity, ownership and lifetime, whether it blocks, whether it is idempotent.
- **Every error path a caller must handle** — thrown exceptions, `Err` variants, failed futures,
  non-zero returns — with the condition that produces it.
- **Compilable examples where the toolchain supports them** — rustdoc doc-tests, KDoc `@sample`,
  DocC snippets, Doxygen `@snippet`. These are the only examples that cannot silently go stale,
  because CI fails when they break.
- **Link, do not repeat.** Every toolchain has intra-doc links; a duplicated explanation is a second
  copy to keep true.

Write for the caller who has the signature in front of them and still has a question.

### Step 4: Generate and check the output

Run the generator and read its warnings — broken links, undocumented symbols, and unresolved
references are exactly the drift this skill exists to catch. The stack reference has the command.

Two checks worth doing every time:

- **Do the examples compile and run?** Run the doc-tests where the toolchain has them. An example
  that does not compile is worse than no example.
- **Do the links resolve?** Broken intra-doc links usually mean a symbol was renamed and its
  references were not — a drift signal, not a formatting nit.

Keep the output small: doc generators are verbose, so filter to warnings and errors rather than
pasting the whole run. Never read the generated site back into context — it is build output, and
the source comments are the thing under review.

### Step 5: Report what is documented and what is not

```markdown
## Documentation added
<files touched, and what each now documents>

## Generated
<command run, output location, and the real result — including warning count>

## Still undocumented
<specific public symbols or endpoints, as `file:line` — with why, where there is a reason>

## Drift found
<docs that contradict the implementation, if any>
```

The drift section is the one people act on. A comment that describes behavior the code no longer has
is worse than a missing comment, because it is believed. Report it even when fixing it is out of
scope.

## Operations

| Operation | User intent | Output |
|---|---|---|
| `comments` (default) | "document this class/module" | Doc comments written in the source, in the project's markup |
| `reference` | "generate the API docs", "set up Dokka/DocC/dartdoc" | Generator configured and run; reference site or Markdown produced |
| `api` | "document this REST API" | Human-readable REST docs from the OpenAPI spec, spec lint issues reported |
| `readme` | "write the README" | README scaffolded from package metadata plus a verified working example |
| `changelog` | "generate the changelog for this release" | Keep a Changelog-format entries derived from commits since the last tag |
| `architecture` | "explain how this fits together" | Overview doc with a Mermaid module/layer diagram derived from the build graph |
| `audit` | "the docs are out of date" | Ranked list of undocumented symbols and doc/implementation drift; fixes only if asked |

## Critical constraints

- **Never document behavior you have not read.** A plausible-sounding comment on code you skimmed is
  a confident lie that outlives the person who wrote it. Read the implementation, or ask.
- **Never invent API surface** — endpoints, parameters, error codes, or config keys that are not in
  the code or the spec. Readers trust docs more than they trust code, which makes fabrication here
  unusually expensive.
- **Do not modify implementation code while documenting it.** Renaming for clarity or "fixing" what
  a comment reveals is a separate change; propose it, do not slip it in.
- **Do not commit generated output** unless the project already does — check for `docs/api/`,
  `target/doc/`, or `doc/api/` in `.gitignore` first. Committed generated docs go stale in review.
- **Never put credentials, internal hostnames, customer data, or unreleased product names in
  examples.** Documentation is the most-published artifact a repo has; use the toolchain's own
  placeholder conventions.
- **Do not delete existing documentation to make room for generated docs.** Hand-written docs
  usually encode context no generator can recover — merge, or ask.
- **Do not fabricate a changelog entry for a commit you cannot interpret.** List it as-is under an
  "Other" heading and let the human classify it.

## References

- [kotlin-kmp.md](references/kotlin-kmp.md) — KDoc tags, Dokka setup and tasks, per-source-set docs for KMP, `@sample`, `expect`/`actual` documentation
- [flutter-dart.md](references/flutter-dart.md) — dartdoc comments, `dart doc`, macros and templates, pub.dev metadata, doc lints
- [swift-apple.md](references/swift-apple.md) — DocC markup, `.docc` catalogs, Topics, tutorials, `swift package generate-documentation`, static hosting
- [rust-cpp.md](references/rust-cpp.md) — rustdoc, doc-tests, intra-doc links, docs.rs metadata; Doxygen, Breathe/Sphinx
- [api-specs.md](references/api-specs.md) — OpenAPI/Swagger linting, generating reference sites and Markdown, documenting a spec that already exists
- [other-languages.md](references/other-languages.md) — TSDoc/TypeDoc, Python docstrings and Sphinx/MkDocs, Go doc comments
- [project-docs.md](references/project-docs.md) — README scaffolding, conventional-commit changelogs, architecture diagrams in Mermaid, versioned docs sites
