# Refactoring catalog

Cross-cutting reference: which refactoring answers which smell, how to perform each one safely, how
to build a safety net when tests are missing, and how to back out. Language-specific tooling and
idioms live in the stack references.

## Contents

- [Smell to refactoring](#smell-to-refactoring)
- [The mechanics, refactoring by refactoring](#the-mechanics-refactoring-by-refactoring)
- [Duplication: when to extract and when not to](#duplication-when-to-extract-and-when-not-to)
- [Dead code: proving something is unreferenced](#dead-code-proving-something-is-unreferenced)
- [Characterization tests: a safety net for untested code](#characterization-tests-a-safety-net-for-untested-code)
- [Rollback](#rollback)
- [Sequencing a large refactoring](#sequencing-a-large-refactoring)

## Smell to refactoring

The smell is the symptom; the refactoring is the treatment. Several treatments often fit — pick the
one that makes the *next* change easier, since that is the only reason to refactor at all.

| Smell | Refactoring | When it is the wrong answer |
|---|---|---|
| Repeated block, identical | Extract function | The blocks are coincidentally alike and will diverge |
| Repeated block, varies slightly | Parameterize, or extract with a lambda/strategy for the varying part | The variation is most of the block |
| Long function | Extract the named steps; each step gets a name that says *what*, not *how* | The function is a linear pipeline that reads fine top to bottom |
| Deep nesting | Guard clauses, invert the condition, early return | The branches are genuinely parallel cases — use a `when`/`switch` |
| Long parameter list | Introduce a parameter object | The parameters are unrelated — that is a sign the function does too much |
| Boolean flag parameter | Split into two named functions | The flag is a real runtime value, not a compile-time choice at every call site |
| Magic literal | Named constant, enum, or sealed hierarchy | The literal is used once, adjacent to its meaning (`take(1)`) |
| Misleading or vague name | Rename (reference-aware) | Never — this is the cheapest, highest-value refactoring there is |
| Comment explaining *what* the code does | Extract a function named after the comment, delete the comment | The comment explains *why*, which code cannot say |
| Primitive obsession | Value/wrapper type around the primitive | The type is genuinely a number or a string with no invariant |
| Feature envy (touches another type's data) | Move the function to that type | The other type is a DTO or belongs to another layer |
| Data clump (same 3 fields travel together) | Extract a type holding them | They are coincidentally co-located |
| Large class | Extract class along the axis of change, not the axis of nouns | The class is a cohesive facade over parts that must stay together |
| Switch on a type tag | Polymorphism or a sealed hierarchy | The switch lives in one place and the tag comes from outside (parsing) |
| Speculative generality (unused hooks, one-implementation interfaces) | Inline it away | The seam exists for testing, or a second implementation is imminent |
| Dead or unreachable code | Delete | See [dead code](#dead-code-proving-something-is-unreferenced) — proof first |

## The mechanics, refactoring by refactoring

Each of these is a sequence of steps that keeps the code compiling throughout. That property is what
makes them safe; performing them as a single edit forfeits it.

**Extract function**
1. Copy the block into a new function with a name that describes its result, not its steps.
2. Turn its free variables into parameters, and the values used afterwards into the return.
3. Replace the original block with a call. Compile.
4. Only now consider whether the parameter list is telling you the extraction was wrong — more than
   three or four parameters usually means the block was not a coherent unit.

**Inline function** (the inverse — for indirection that no longer earns its place)
1. Find every caller with a reference-aware search; if any are dynamic, stop.
2. Replace each call with the body. Compile after each.
3. Delete the function.

**Rename**
Use the reference-aware tool (Serena's `rename_symbol`, or the IDE). Never find/replace: it hits
comments, strings, and unrelated identifiers with the same name, and misses dynamic references. When
the tool reports success the rename is complete across declarations, references, and overrides —
no re-verification needed for the rename itself.

**Guard clause / early return**
1. Take the outermost condition wrapping the whole body.
2. Invert it, return/throw early, and dedent the body. Compile.
3. Repeat for the next level. Stop when the happy path is at the top level.

Watch for `else` branches with side effects and for languages where an early return skips cleanup
(C++ without RAII, `defer`/`finally` semantics) — those are the cases where this is not mechanical.

**Introduce parameter object**
1. Create the type with the fields, no behavior yet.
2. Add an overload taking the new type; make the old signature delegate to it. Compile — nothing
   broke, because nothing changed.
3. Migrate call sites in batches, compiling between them.
4. Delete the old signature once no callers remain.

The intermediate delegating overload is what makes this safe on a large call-site count, and it is
the same trick for any signature change.

**Extract class**
1. Create the empty class.
2. Move one field and its directly-related methods; leave a delegating member behind on the
   original. Compile.
3. Repeat field by field, compiling each time.
4. Remove the delegation once callers use the new type directly.

Split along the axis of change — the fields that get modified together belong together. Splitting
by noun ("everything named `user*`") produces classes that must always change in lockstep.

**Replace magic value with a constant**
Name it after its meaning, not its value: `RETRY_LIMIT`, not `THREE`. Put it where its meaning
lives — beside the code that owns the rule, not in a shared `Constants` bag, which becomes a
dependency magnet that every module ends up importing.

**Replace conditional with polymorphism**
Worth it when the same type-tag switch appears in several places, because then adding a case means
finding all of them. For a single switch in a single place, a sealed hierarchy with exhaustiveness
checking gives the same safety with far less machinery.

## Duplication: when to extract and when not to

Duplication is the most over-treated smell. The rule that holds up:

- **Two occurrences: wait.** Two similar blocks carry almost no maintenance cost, and you cannot yet
  tell which parts vary. An abstraction extracted from two samples is a guess.
- **Three occurrences: extract.** The third one shows the axis of variation, which is the thing the
  abstraction actually needs to parameterize.
- **Coincidental duplication: never extract.** Two blocks that look alike but answer to different
  requirements will diverge, and the shared function becomes a `if (isFoo)` thicket. Ask whether a
  future change to one should automatically apply to the other; if the answer is no, they are not
  duplicates.

A wrong abstraction is more expensive than the duplication it replaced, because every future caller
inherits it and the coupling is invisible at the call site. When in doubt, leave the duplication and
say why in the report.

## Dead code: proving something is unreferenced

Deleting dead code is the highest-value cleanup available and the easiest to get catastrophically
wrong, because "no references found" and "no references exist" are different statements.

Before deleting, rule out the invisible reference paths:

- **Reflection and dynamic dispatch** — class names in strings, `Class.forName`, `NSClassFromString`,
  Python `getattr`, JS bracket access
- **Dependency injection and service discovery** — annotation-driven wiring, DI modules, `ServiceLoader`
- **Serialization** — fields that look unused are read by name by the serializer; constructors that
  look unused are called by it
- **Platform entry points** — manifest-declared activities/services, `@objc` selectors, exported
  symbols, FFI/JNI boundaries, CLI subcommand registries, test discovery by naming convention
- **Build variants and platform source sets** — code referenced only from a flavor, `iosMain`, a
  feature flag, or a target you are not currently compiling
- **Published API** — anything a downstream consumer might call; inside a library, "unreferenced in
  this repo" means nothing

The practical procedure: run the stack's unused-symbol lint, then confirm each candidate with a
reference-aware search (`find_referencing_symbols`), then grep for the symbol *as a string* to catch
reflection and config. Compile every target and source set, not just the default one. When a
deletion cannot be proven safe, say so rather than deleting hopefully — and note that deletions are
much safer landed as their own commit, where a revert is surgical.

## Characterization tests: a safety net for untested code

When the code to refactor has no tests, the honest options are: write tests first, or accept the
risk explicitly. Characterization tests are the cheap version of the former — they do not assert
what the code *should* do, only what it *currently* does, which is exactly what a refactoring must
preserve.

1. Call the code with representative inputs, including the ugly edge cases you would not design for.
2. Assert whatever it actually returns — even if it looks wrong. Wrong-but-preserved is the goal;
   fixing it is a separate change.
3. Cover each branch you are about to touch. Coverage of the rest of the file is not needed.
4. Refactor against them.
5. Afterwards, decide which of these tests are worth keeping as real tests and which were scaffolding.

If a characterization test captures behavior that is clearly a bug, keep the test (it documents
reality) and report the bug separately. `test-generation` covers the mechanics of writing them in
each stack.

## Rollback

Small steps make rollback trivial, which is the entire reason for small steps.

- **A step went red:** revert that step and redo it. `git checkout -- <path>` if uncommitted, or
  `git reset --hard HEAD` if the step was the only uncommitted work. Do not debug forward — a
  refactoring that needs debugging has stopped being a refactoring.
- **A committed step went wrong:** `git revert <sha>`. This is why each refactoring is its own
  commit.
- **The whole direction was wrong:** revert the range and report what you learned. A refactoring
  abandoned after two hours with a clear explanation is a better outcome than one landed half-done.
- **Something broke after landing:** a small, single-purpose commit is `git bisect`-friendly and
  revertable in isolation. A 40-file mixed commit is neither, which is the real cost of batching.

Always confirm the working tree is clean and committed *before* starting — rollback needs a known
good point to return to.

## Sequencing a large refactoring

For anything that will not land in one change, the sequence that keeps the codebase working
throughout is expand → migrate → contract:

1. **Expand** — add the new structure alongside the old. Nothing calls it yet; nothing can break.
2. **Migrate** — move call sites over in batches, keeping both structures working. Each batch is a
   reviewable, revertable change.
3. **Contract** — delete the old structure once nothing references it.

Every intermediate state compiles and passes tests, so the work can be paused, reviewed, or
abandoned at any point without leaving the repo broken. That property matters more than speed on
anything touching a shared module.
