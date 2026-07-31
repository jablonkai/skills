# TypeScript, Python and Go documentation

Secondary stacks — reach for this file only when the project is actually in one of them. Each
section covers the comment syntax, the generator, and the switch that reports missing docs.

## Contents

- [TypeScript and JavaScript](#typescript-and-javascript)
- [Python](#python)
- [Go](#go)

---

## TypeScript and JavaScript

### TSDoc comments

```ts
/**
 * Uploads a file to the configured bucket and returns its public URL.
 *
 * The upload is retried up to three times with exponential backoff. Resolves once the object is
 * durably stored; aborting the signal cancels the in-flight request but does not delete an
 * already-committed object.
 *
 * @param file - The file to upload.
 * @param options - Upload options; `contentType` defaults to detection from the file name.
 * @returns The public HTTPS URL of the stored object.
 * @throws {StorageError} If the bucket rejects the object after all retries.
 *
 * @example
 * ```ts
 * const url = await storage.upload(file, { contentType: "image/png" });
 * ```
 */
export async function upload(file: File, options?: UploadOptions): Promise<string>
```

In TypeScript, do not restate types in the comment — `@param {string} file` is JSDoc-for-JavaScript
and duplicates what the signature already declares, so it becomes wrong at the first refactor. The
hyphen after the parameter name is TSDoc's separator and is what TypeDoc expects.

Useful tags: `@remarks`, `@example`, `@defaultValue`, `@deprecated`, `@see`, `@internal` (excluded
from output), `{@link Symbol}` for inline references.

### Generating

```bash
npx typedoc --out docs/api src/index.ts
npx typedoc --validation.invalidLink --validation.notDocumented
```

`--validation.notDocumented` is the missing-docs report; `--validation.invalidLink` catches
`{@link}` references orphaned by a rename. Configure once in `typedoc.json` rather than passing
flags at every call site.

For a Markdown-output site, `typedoc-plugin-markdown` writes files a docs framework (Docusaurus,
VitePress) can consume directly.

### Enforcing docs in lint

```json
// eslint config
{
  "plugins": ["jsdoc"],
  "rules": {
    "jsdoc/require-jsdoc": ["warn", { "publicOnly": true }],
    "jsdoc/require-param-description": "warn",
    "jsdoc/require-returns-description": "warn",
    "jsdoc/check-tag-names": ["warn", { "typed": true }]
  }
}
```

`typed: true` tells the plugin the project is TypeScript, so it stops asking for type annotations in
comments.

### Package metadata

`package.json` drives what npm renders: `description`, `homepage`, `repository`, `keywords`, plus
`README.md` as the package page. The `exports` map is worth documenting in the README when it is
non-trivial — subpath imports are a common source of confusion that no generated reference explains.

---

## Python

### Docstrings

Pick the style the project already uses; mixing styles breaks the parser configured in the docs
build. Google style is the most readable in source:

```python
def upload(file: Path, content_type: str | None = None) -> str:
    """Upload ``file`` to the configured bucket and return its public URL.

    The upload is retried up to three times with exponential backoff. Blocks until the object is
    durably stored.

    Args:
        file: Path to a readable local file.
        content_type: MIME type stored with the object. Defaults to detection from the suffix.

    Returns:
        The public HTTPS URL of the stored object.

    Raises:
        OSError: If ``file`` cannot be read.
        StorageError: If the bucket rejects the object after all retries.

    Example:
        >>> storage = Storage("avatars")
        >>> storage.upload(Path("avatar.png"))
        'https://cdn.example.com/avatars/avatar.png'
    """
```

NumPy style (underlined section headers) is standard in scientific codebases; reStructuredText style
(`:param x:`) is the Sphinx default. With type hints present, omit types from the docstring — Sphinx
and MkDocs both read the annotations.

Doctests in `Example:` blocks are executable:

```bash
python -m pytest --doctest-modules src/
```

Like rustdoc doc-tests, this is the only part of the docs that cannot silently rot — prefer a
doctest over a prose example wherever the example is short and deterministic.

### Generating

```bash
# Sphinx — the established option, autodoc pulls docstrings from imported modules
sphinx-build -b html docs docs/_build/html -W   # -W turns warnings into errors

# MkDocs + mkdocstrings — less configuration, Markdown-native
mkdocs build --strict
mkdocs serve
```

`mkdocstrings` renders a symbol with a directive in a Markdown page:

```markdown
::: storage.Storage
    options:
      show_source: false
      members_order: source
```

### Finding gaps

```bash
ruff check --select D .           # pydocstyle rules, D100-D107 are the missing-docstring set
interrogate -v src/               # docstring coverage percentage per file
```

Set the convention in `pyproject.toml` so the rules match the docstring style in use:

```toml
[tool.ruff.lint.pydocstyle]
convention = "google"
```

---

## Go

### Doc comments

Go's convention is deliberately minimal: a plain comment directly above the declaration, starting
with the identifier's name. There are no tags.

```go
// Upload stores file in the configured bucket and returns its public URL.
//
// The upload is retried up to three times with exponential backoff. Upload blocks until the object
// is durably stored; cancelling ctx aborts the in-flight request but does not delete an
// already-committed object.
//
// Upload returns [ErrRejected] if the bucket rejects the object after all retries.
func (s *Storage) Upload(ctx context.Context, file string) (string, error)
```

Starting with the name is not stylistic — `go doc` and every Go tool assume it, and the sentence is
extracted verbatim into package listings.

Package documentation goes in a `doc.go` file:

```go
// Package storage provides bucket-backed object storage.
//
// # Getting started
//
// Create a [Storage] with [New], then call [Storage.Upload].
package storage
```

Go 1.19+ doc comments support headings (`# Heading`), lists, doc links (`[Storage.Upload]`,
`[pkg/path.Symbol]`), and `//go:` directives. `gofmt` reformats doc comments to the canonical form,
so run it after editing.

### Examples

Example functions in `_test.go` files are compiled, run, and rendered as documentation:

```go
func ExampleStorage_Upload() {
    s, _ := storage.New("avatars")
    url, _ := s.Upload(context.Background(), "avatar.png")
    fmt.Println(url)
    // Output: https://cdn.example.com/avatars/avatar.png
}
```

The `// Output:` comment makes it an assertion — `go test` fails when the output changes. This is
the Go equivalent of a doc-test and the best example format the language has.

### Generating and checking

```bash
go doc ./...                          # terminal output
go run golang.org/x/pkgsite/cmd/pkgsite@latest    # local pkg.go.dev
go vet ./...                          # catches malformed example functions
```

`revive` with the `exported` rule reports exported identifiers without a comment, and comments that
do not start with the identifier name.
