# Refactoring JavaScript/TypeScript, Python, Go and Java

Secondary stacks — reach for this reference only when a project actually uses one. The workflow and
the discipline in `SKILL.md` are unchanged; what differs is the tooling and the idioms.

## Contents

- [JavaScript / TypeScript](#javascript--typescript)
- [Python](#python)
- [Go](#go)
- [Java](#java)

---

## JavaScript / TypeScript

### Tooling

```bash
npx tsc --noEmit                       # the type checker is the refactoring safety net
npx eslint . --fix                     # auto-fixable rules
npx eslint . --ext .ts,.tsx            # the rest
npx prettier --write .
npx knip                               # unused files, exports and dependencies
npx depcheck                           # unused dependencies
npx jscpd src/                         # copy-paste detection
```

The single most valuable preparation for refactoring a TypeScript project is tightening the
compiler, because it converts whole categories of smell into errors:

```jsonc
// tsconfig.json
"strict": true,
"noUncheckedIndexedAccess": true,
"noUnusedLocals": true,
"noUnusedParameters": true,
"exactOptionalPropertyTypes": true
```

Turn these on one at a time. Each produces its own wave of findings, and a single commit mixing all
of them is unreviewable.

### Idioms worth refactoring toward

| Instead of | Prefer | Why |
|---|---|---|
| `any` and type assertions | Real types, generics, `unknown` + narrowing | `any` disables the safety net this refactoring depends on |
| String unions duplicated across files | A shared union type or `const` object with `as const` | One place to change |
| Nested `if` on possibly-missing values | Optional chaining, nullish coalescing, early return | Flattens |
| `.then()` chains | `async`/`await` | Ordinary `try`/`catch`, readable ordering |
| Boolean/options-bag parameters mutated inside | Explicit parameters or a readonly options type | Mutation of arguments is invisible to callers |
| Deeply nested callbacks | `async`/`await`, or extracted named functions | Same fix as any deep nesting |
| Barrel files re-exporting everything | Direct imports | Barrels defeat tree-shaking and create import cycles |
| Classes used purely as namespaces of statics | Plain exported functions | Modules already are the namespace |
| `let` reassigned through a long function | `const` + extracted computation | Narrows what a reader must track |

For React specifically: extract a component when the JSX subtree has a name, extract a hook when the
*logic* is reused (not the markup), and remember that a component extracted out of a `.map()` needs
its `key` moved with it. Do not memoize (`useMemo`/`useCallback`/`memo`) as part of a cleanup —
that is performance work, and it needs a measurement.

### Dead code

`knip` is the best tool here, but it cannot see: dynamic `import()` with a computed specifier,
string-keyed property access, framework file-based routing conventions (Next.js `app/`, `pages/`),
config-referenced entry points, or anything consumed by a published package's users. Check
`package.json` `exports`/`bin`/`main` before deleting a module.

### Verification

```bash
npx tsc --noEmit && npm test && npx eslint .
npm run build
```

---

## Python

### Tooling

```bash
ruff check . --fix                     # replaces flake8/isort/pyupgrade and much of pylint
ruff format .
mypy .                                 # or: pyright
vulture .                              # dead code candidates
radon cc -s -a .                       # cyclomatic complexity, ranked
```

Ruff rule sets that map onto this skill: `C90` (mccabe complexity), `SIM` (simplifications), `RET`
(return/early-exit), `ARG` (unused arguments), `PLR` (refactor suggestions), `UP` (pyupgrade —
modern syntax), `B` (bugbear).

Python's lack of a compiler makes types the only static safety net available. If the project has no
annotations on the code being refactored, adding them to the affected functions first is usually
worth the detour — otherwise every rename is a runtime discovery.

### Idioms worth refactoring toward

| Instead of | Prefer | Why |
|---|---|---|
| `if x is not None:` wrapping the body | Early `return`/`raise` guard | Flattens |
| Long `if`/`elif` on a value or type | `match` (3.10+), or a dispatch dict | Reads as a table |
| Loop appending to a list | Comprehension, or a generator for large data | Intent visible; generators avoid materializing |
| `dict` passed around as a record | `dataclass`, `NamedTuple`, or Pydantic model | Attribute typos become errors; fields get names |
| Mutable default arguments (`def f(x=[])`) | `None` + create inside | This is a bug, not a style issue — report it as one |
| Manual `open`/`close`, locks, temp files | `with` / context managers | Cleanup on every exit path |
| `*args, **kwargs` pass-through in domain code | Explicit parameters | Signature stops being a mystery |
| Module-level mutable state | Explicit dependency passed in | Import order stops mattering; testable |
| String literals as keys/flags everywhere | `Enum`, `StrEnum`, or module constants | Searchable, typo-checked |

### Dead code

`vulture` produces candidates, not conclusions. Python hides references in: `getattr`/`setattr`,
`__getattr__`, entry points declared in `pyproject.toml`, plugin registries, Django/Flask decorators
and settings strings, `importlib` dynamic imports, pytest fixture discovery by name, `__all__`, and
anything a serializer reads by field name. Confirm each candidate with a project-wide grep for the
name as a string.

### Verification

```bash
ruff check . && mypy . && python -m pytest
```

---

## Go

### Tooling

```bash
gofmt -l .          # and gofumpt for the stricter variant
go vet ./...
staticcheck ./...   # the substantive linter; includes simplification suggestions
golangci-lint run   # aggregates the above plus gocyclo, dupl, unused
gopls rename        # reference-aware rename
```

`staticcheck`'s `S1*` (simplifications) and `golangci-lint`'s `unused`, `gocyclo` and `dupl` cover
most of what this skill looks for.

### Idioms worth refactoring toward

| Instead of | Prefer | Why |
|---|---|---|
| `if err == nil { ... }` wrapping the body | `if err != nil { return ... }` early | Go's canonical shape: errors out, happy path unindented |
| `errors.New(fmt.Sprintf(...))` | `fmt.Errorf("...: %w", err) ` | Wrapping preserves the chain for `errors.Is`/`As` |
| Repeated struct literals across call sites | A constructor function with defaults | One place to add a field |
| Large interfaces defined next to the implementation | Small interfaces defined at the consumer | "Accept interfaces, return structs" |
| `interface{}` / `any` parameters | Generics (1.18+) or a concrete type | Type safety without reflection |
| Long functions with named step comments | Extracted functions named after the steps | Same rule as everywhere |
| Package-level mutable state | Struct fields with an explicit constructor | Testable; no init-order coupling |

Go's convention weight is unusually high — matching what the surrounding package already does
matters more here than any improvement suggested above.

### Dead code

`golangci-lint`'s `unused` finds most of it. It cannot see: methods satisfying an interface used
via reflection, `init()` side effects, symbols used by another module (anything exported from a
library package), build-tag-guarded files (`//go:build`), `go:generate` outputs, and anything
reached through `reflect` or struct tags. Build with every relevant tag set before deleting.

### Verification

```bash
go build ./... && go vet ./... && go test ./...
go test -race ./...     # after anything touching concurrency
```

---

## Java

### Tooling

```bash
./gradlew build                       # or: mvn verify
./gradlew spotlessApply               # formatting
./gradlew pmdMain checkstyleMain      # complexity, duplication, naming
./gradlew spotbugsMain                # bug patterns, some dead code
```

The IDE is the better tool for Java refactoring than any CLI: IntelliJ's and Eclipse's refactorings
are reference-aware across reflection-adjacent frameworks in a way grep is not. Where a symbolic
tool is available (Serena's `rename_symbol`, `find_referencing_symbols`), prefer it over text edits.

### Idioms worth refactoring toward

| Instead of | Prefer | Why |
|---|---|---|
| `null` returns | `Optional<T>` on the return type | The absent case appears in the signature |
| Long `if`/`else if` on type | `sealed interface` + pattern matching `switch` (17/21+) | Exhaustiveness checking |
| Data-carrying classes with getters/equals/hashCode | `record` | Removes boilerplate that can drift |
| Manual loops accumulating | Streams — where the pipeline is short | Intent visible; do not chain past readability |
| Try/finally resource cleanup | try-with-resources | Cleanup on every exit path |
| Constructor with 6+ parameters | Builder, or extracted parameter objects | Call sites stop depending on argument order |
| Static utility classes reached everywhere | Injected collaborators | Coupling becomes visible and testable |
| Checked exceptions wrapped and rethrown at every layer | One boundary that translates them | Removes ceremony from the middle |

### Dead code

Java's invisible references are mostly framework-driven: Spring/CDI/Guice-injected beans with no
direct constructor call, JPA entities and their no-arg constructors, Jackson-bound properties,
`Class.forName` and `ServiceLoader`, JNI (`native` methods and the C side calling back), JSP/JSF/
template-referenced beans, and anything named in XML config or annotations. SpotBugs and PMD flag
candidates; confirm each with a reference search plus a grep for the fully-qualified name as a
string.

### Verification

```bash
./gradlew build test          # or: mvn verify
```

For a published library, run `japicmp` or `revapi` before changing any public signature — Java's
binary compatibility rules are subtle (adding a method to an interface, changing a return type,
reordering enum constants), and source compatibility does not imply binary compatibility.
