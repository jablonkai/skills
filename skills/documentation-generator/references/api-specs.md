# OpenAPI and REST API documentation

When an OpenAPI spec exists, it is the source of truth and the human-readable docs are a rendering
of it. The work is therefore mostly about the spec: a reference site generated from a thin spec is
a thin site, and no amount of theming fixes it.

## Contents

- [Find and identify the spec](#find-and-identify-the-spec)
- [Lint before rendering](#lint-before-rendering)
- [Enriching the spec](#enriching-the-spec)
- [Rendering a reference site](#rendering-a-reference-site)
- [Rendering Markdown](#rendering-markdown)
- [Spec-first vs code-first](#spec-first-vs-code-first)
- [When there is no spec](#when-there-is-no-spec)

## Find and identify the spec

```bash
find . -maxdepth 4 \( -name 'openapi*.y*ml' -o -name 'openapi*.json' \
  -o -name 'swagger*.y*ml' -o -name 'swagger*.json' -o -name 'api.y*ml' \) \
  -not -path '*/node_modules/*' -not -path '*/build/*'
```

Check the version line first — it changes what the tooling accepts:

| Root field | Version | Notes |
|---|---|---|
| `swagger: "2.0"` | Swagger 2.0 | Legacy; many renderers still accept it, some require conversion |
| `openapi: 3.0.x` | OpenAPI 3.0 | The most widely supported |
| `openapi: 3.1.x` | OpenAPI 3.1 | JSON Schema 2020-12 aligned; older tools reject it |

Do not upgrade the spec version to satisfy a renderer without saying so — it changes the contract
artifact that clients and code generators consume.

## Lint before rendering

A spec that renders is not a spec that is correct. Lint first and report what you find, because
every finding is a place where the published docs would mislead someone:

```bash
npx @redocly/cli lint openapi.yaml
npx @stoplight/spectral-cli lint openapi.yaml
```

The findings worth surfacing to the user:

- **Operations without `summary`/`description`** — the endpoint list renders as bare paths
- **Missing `operationId`** — breaks generated client method names and deep links
- **Schemas without `description`, `example`, or `format`** — the model tables render as type names
- **Undocumented error responses** — only `200` defined, so callers cannot see what failures exist
- **No `security` on operations that require auth** — the docs imply a public endpoint
- **`$ref`s that do not resolve** — silently empty sections in most renderers

## Enriching the spec

Where the spec is thin, the fix belongs in the spec, not in a separate document that will disagree
with it. The fields that carry the most weight per character:

```yaml
paths:
  /objects/{key}:
    put:
      operationId: putObject
      summary: Store an object
      description: |
        Stores the request body at `key`, replacing any existing object. Writes are
        read-your-writes consistent; a subsequent GET on the same key returns this body.
      parameters:
        - name: key
          in: path
          required: true
          description: Object key, up to 1024 UTF-8 bytes. May contain `/` to emulate folders.
          schema:
            type: string
            maxLength: 1024
          example: avatars/user-42.png
      responses:
        "200":
          description: Object stored.
        "409":
          description: A write to the same key is already in flight. Retry with backoff.
        "413":
          description: Body exceeds the 5 GiB per-object limit.
```

Priorities, in order:

1. **`description` on every operation** — one or two sentences on what it does and any side effect
2. **Every error response the caller must handle**, with the condition and what to do about it
3. **`example`/`examples` on request and response bodies** — readers copy these; they are the most
   used part of any API reference
4. **`description` on every schema property** whose meaning is not the name — units, ranges,
   nullability, defaults
5. **`securitySchemes` plus per-operation `security`** — how to authenticate, once, at the top

Write examples that would actually work, with realistic values and no real credentials, tokens,
internal hostnames, or customer data. API docs are the most-copied text in a repo.

## Rendering a reference site

```bash
# Redocly — single self-contained HTML file, the usual default
npx @redocly/cli build-docs openapi.yaml --output docs/api.html

# Redocly preview with live reload
npx @redocly/cli preview-docs openapi.yaml
```

Other renderers, when the project already uses one: Swagger UI (interactive "try it" console),
Scalar, Stoplight Elements. Do not introduce a second renderer alongside an existing one — pick up
whatever is configured in `redocly.yaml`, `docusaurus.config.js`, or the docs site's build.

The `redoc-cli` package is deprecated in favour of `@redocly/cli`; a project still calling it works,
but a new setup should not use it.

## Rendering Markdown

For docs that live in the repository or a wiki rather than a generated site:

```bash
npx widdershins openapi.yaml -o docs/api.md --language_tabs 'shell:curl' 'javascript:JS'
npx @openapitools/openapi-generator-cli generate -i openapi.yaml -g markdown -o docs/api
```

Markdown output is reviewable in a pull request, which is its main advantage over a bundled HTML
file. Whichever you use, treat the output as generated: regenerate it rather than hand-editing, and
say so in a comment at the top of the file, or the next person will edit the Markdown and lose it.

## Spec-first vs code-first

Where the spec comes from determines where an edit belongs:

| Setup | Spec origin | Edit here |
|---|---|---|
| Spec-first | Hand-written `openapi.yaml`, code generated or validated against it | The spec |
| Code-first (Kotlin/Spring) | springdoc-openapi from annotations | `@Operation`, `@Schema` annotations |
| Code-first (Ktor) | Ktor OpenAPI plugin / route metadata | The route definitions |
| Code-first (FastAPI) | Generated from type hints and docstrings | Docstrings, `Field(description=...)`, `response_model` |
| Code-first (NestJS) | `@nestjs/swagger` decorators | `@ApiOperation`, `@ApiProperty` decorators |
| Code-first (Go) | swaggo comments | The `// @Summary` comment block above the handler |

Editing a generated spec file directly is the most common mistake here: the next build overwrites
it. Check whether the spec is gitignored or has a "do not edit" header before touching it.

## When there is no spec

Do not reverse-engineer one from route handlers and present it as documentation — an inferred spec
is a guess about status codes, auth, and error shapes, and readers will treat it as authoritative.

The honest options, in order of preference:

1. **Write the spec from the handlers with the user reviewing it**, then generate docs from it. This
   produces a durable artifact rather than a one-off document.
2. **Adopt the code-first tooling for the framework** so the spec is generated and stays current.
3. **Document only what is verifiable** — the routes, methods, and parameter names that are literally
   in the code — and mark status codes and error shapes as unverified rather than inventing them.
