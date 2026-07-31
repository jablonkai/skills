# skills

Personal skill catalog: one directory per reusable, task-oriented skill. See
[README.md](README.md) for the full overview.

## Reference

Skills in this repo follow the open **Agent Skills** format — see
[agentskills.io](https://agentskills.io/) for the authoritative
[specification](https://agentskills.io/specification) of `SKILL.md`, its frontmatter
fields, and the progressive disclosure model. The conventions below are this repo's
house rules on top of that format; when the two disagree, the spec wins.

## AI agent guidance

- `skills/<name>/` is the main workspace surface; changes to skills belong there.
- Every skill directory must contain exactly one `SKILL.md` with YAML frontmatter `name:`, `description:`, `summary:` and `category:`.
- The `name:` value must match the directory name. The `description:` value must explain what the skill does and when to use it.
- Validate every change with `bash .github/scripts/validate.sh`.
- The **Available Skills** sections of `README.md` and `AGENTS.md` are generated — never
  hand-edit them. Change `summary:`/`category:` in the skill instead and run
  `.github/scripts/generate-catalog.sh`.
- Prefer updating existing skills and documentation over adding new repository conventions.

## Layout

| Path | Purpose |
|------|---------|
| `skills/<name>/SKILL.md` | Skill entry point — one directory per skill |
| `skills/<name>/references/` | Optional reference docs the skill loads on demand |
| `skills/<name>/scripts/` | Optional helper scripts shipped with the skill |
| `skills/<name>/assets/` | Optional templates, fonts, images used by the skill |
| `.github/scripts/validate.sh` | Local validation (run before committing) |
| `.github/scripts/generate-catalog.sh` | Renders the Available Skills sections from frontmatter |
| `.github/scripts/catalog-lib.sh` | Helpers shared by the two scripts above |

## Available Skills

<!-- Generated from the `summary:` and `category:` frontmatter of each skill.
     Edit skills/<name>/SKILL.md, then run .github/scripts/generate-catalog.sh -->
<!-- BEGIN GENERATED SKILLS -->
- `affinity`: remote-control Affinity (the unified Affinity by Canva app) with JavaScript via its local automation endpoint — document edits, batch operations, and reusable library scripts, with no MCP client configuration
- `blender`: remote-control a running Blender by Python via a local bridge — bmesh/modifier modeling, shader and geometry nodes, animation, rigging, physics, Grease Pencil and the VSE, EEVEE/Cycles stills and video, glTF/FBX/USD/OBJ/STL export
- `cavalry`: remote-control Cavalry (Scene Group's 2D motion-design app) via a scriptable bridge — build scenes procedurally, animate with keyframes and per-letter text effects, then render PNG frames or alpha overlay videos
- `code-analyzer`: holistic read-only project audit for bugs, security vulnerabilities, code quality issues, performance risks, missing tests, documentation gaps, and prioritized improvement ideas
- `duv`: search and retrieve data from the DUV Ultramarathon Statistics website (statistik.d-u-v.org), including runner profiles, events, and rankings
- `emu-branding`: brand guidelines and visual identity for EMU (Egyesület a Magyar Ultrafutásért), including logo, color palette, and typography
- `error-debugging`: analyze a stack trace, crash report, panic or error log down to its root cause, then propose a fix and a way to verify it — Kotlin/Android, KMP/Compose, Flutter/Dart, Swift, Rust and C++, including deobfuscation and symbolication of release traces
- `freecad`: remote-control a running FreeCAD (parametric CAD) by Python via a local bridge — primitives and booleans, constrained Sketcher profiles, PartDesign features, metrics and viewport screenshots, STEP/IGES/STL/OBJ export
- `github-commit-pr`: end-to-end workflow for committing changes, pushing a branch, and opening or updating a GitHub pull request
- `github-do-issue`: fetch a GitHub issue, implement it in the current repository, and stop before commit or PR creation
- `github-fix-action-error`: diagnose the latest failing GitHub Actions run on the current branch, apply a targeted fix locally, and — after user approval — commit and push; refuses to run on main/master/develop
- `github-issues`: standardized issue creation, labeling, triage, commenting, and issue management through the GitHub CLI
- `markitdown`: convert PDF, Office, HTML, data, e-book, image, audio, and ZIP files (or YouTube URLs) to clean Markdown using Microsoft's markitdown tool, via CLI or Python API
- `rebelle`: remote-control Rebelle and Rebelle Motion IO with JSON events — live WebSocket painting in Rebelle Pro, batch-rendered painted animation frames, and visual verification through canvas exports
- `test-generation`: write unit, integration and UI tests for existing code — framework detection from the build files, case selection for boundaries and error paths, correct source-set placement, and coverage gap analysis across Kotlin/KMP, Compose, Flutter/Dart, Swift, Rust and C++
<!-- END GENERATED SKILLS -->

## Conventions

### Skill directories (`skills/`)
- Directory name: **kebab-case** (e.g. `github-commit-pr`)
- Every skill dir must contain exactly one `SKILL.md`
- The frontmatter `name:` **must** equal the directory name
- Required YAML frontmatter fields: `name`, `description`, `summary`, `category`
- Optional fields: `risk`, `tags`, `allowed-tools`, `argument-hint`, `license`
- No other top-level frontmatter keys — the validator rejects unknown fields so that
  tooling-generated blocks (e.g. the `metadata:` block written by `gh skill install`)
  don't drift into the catalog

### Frontmatter fields

| Field | Required | Value |
|-------|----------|-------|
| `name` | yes | kebab-case, equal to the directory name |
| `description` | yes | what the skill does **and** when to use it (see below) |
| `summary` | yes | single line, lowercase start, no trailing period — the catalog entry (see below) |
| `category` | yes | single token grouping the skill (e.g. `testing`, `git`, `3d`), mapped to a README theme (see below) |
| `risk` | no | one of `low`, `medium`, `high` — see the scale below |
| `tags` | no | YAML list of lowercase keywords |
| `allowed-tools` | no | comma-separated tool names the skill needs |
| `argument-hint` | no | usage string shown for `/`-invocation |
| `license` | no | SPDX identifier, if the skill ships under its own terms |

### Risk scale

`risk` describes the blast radius of the skill running as intended — not how likely it
is to go wrong:

| Value | Meaning |
|-------|---------|
| `low` | Reads, analyzes, or makes changes that are cheap to review and undo — local file edits, generated docs, issue comments. |
| `medium` | Drives an external application or mutates shared state: pushes commits, opens or merges pull requests, edits documents in a running app. |
| `high` | Destructive or irreversible: deletes data, force-pushes, publishes, or spends money. |

There is no separate `safe` level — read-only skills are `low`.

### Writing a description
The `description` is the only thing an agent sees when deciding whether to load the
skill, so it carries the whole triggering burden:

- state what the skill does **and** when to use it
- list concrete trigger phrases — the agent matches a description against its
  understanding of the task, not against the user's literal wording, so a handful of
  representative phrasings beats an exhaustive list of variants in the one field that
  is always in context
- say explicitly when *not* to use it if a neighbouring skill overlaps

Use an existing skill (e.g. [code-analyzer](skills/code-analyzer/SKILL.md)) as
a template.

### The generated catalog (`summary` and `category`)

`description` is written for an agent deciding whether to load the skill; `summary` is
written for a human scanning the catalog. The **Available Skills** sections of
[README.md](README.md) and this file are rendered from `summary` and `category`, so each
skill is described in exactly one place and CI catches any drift:

```bash
.github/scripts/generate-catalog.sh            # rewrite both sections
.github/scripts/generate-catalog.sh --check    # fail on drift, write nothing
```

- `summary` is one line, lowercase start, no trailing period — it is spliced into
  ``- `name`: <summary>``. Keep it single-line: the generator reads it as plain text,
  not as folded YAML. Quote it, and avoid quote characters inside.
- `category` is the fine-grained grouping. README rolls categories up into themes via
  `CATALOG_SECTIONS` in the generator; a category no theme covers is a hard error, so a
  new grouping means adding it there deliberately rather than a skill quietly vanishing
  from README.

Everything between the `<!-- BEGIN GENERATED SKILLS -->` and
`<!-- END GENERATED SKILLS -->` markers is overwritten — edit the frontmatter, not the
docs.

### Progressive disclosure
Keep `SKILL.md` short and load detail on demand. Anything long — API references, format
specs, lookup tables — belongs in `references/` and should be pulled in only when the
task needs it. Ship deterministic work as `scripts/` rather than prose instructions.

## Validation

Always run before committing:

```bash
bash .github/scripts/validate.sh
```

Checks: frontmatter completeness, the allowed frontmatter field set and `risk`
vocabulary, `name:`↔directory match, skill directory structure, kebab-case names,
README/AGENTS catalog sync (by regenerating both sections and failing on any
difference), and broken relative Markdown links.

## Adding a new skill

Use Anthropic's **skill-creator** skill to author the skill body — it walks through
scaffolding, description writing, and evaluation:
<https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md>
(available as the `skill-creator` skill in Claude Code). Then apply this repo's
conventions on top:

1. Create `skills/<kebab-name>/SKILL.md` with valid frontmatter, including `summary` and `category`
2. Run `.github/scripts/generate-catalog.sh` to render the **Available Skills** entry into
   [README.md](README.md) and this file
3. Run `bash .github/scripts/validate.sh`
