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
- Every skill directory must contain exactly one `SKILL.md` with YAML frontmatter `name:` and `description:`.
- The `name:` value must match the directory name. The `description:` value must explain what the skill does and when to use it.
- Validate every change with `bash .github/scripts/validate.sh`.
- Keep `README.md` and `AGENTS.md` synced with the actual `skills/` directories.
- Prefer updating existing skills and documentation over adding new repository conventions.

## Layout

| Path | Purpose |
|------|---------|
| `skills/<name>/SKILL.md` | Skill entry point — one directory per skill |
| `skills/<name>/references/` | Optional reference docs the skill loads on demand |
| `skills/<name>/scripts/` | Optional helper scripts shipped with the skill |
| `skills/<name>/assets/` | Optional templates, fonts, images used by the skill |
| `.github/scripts/validate.sh` | Local validation (run before committing) |

## Available Skills

- `affinity`: remote-control Affinity (by Canva) with JavaScript via its local automation endpoint — document edits, batch operations, library scripts; no MCP client config
- `blender`: remote-control a running Blender (3D) by Python via a local bridge — bmesh/modifier modeling, shader + geometry nodes, animation & rigging, physics, Grease Pencil, VSE, EEVEE/Cycles stills and video, glTF/FBX/USD/OBJ/STL export
- `cavalry`: remote-control Cavalry (2D motion-design app) via a scriptable bridge: procedural scene building, keyframe animation, rendering
- `code-analyzer`: read-only whole-project audit for bugs, security, quality, performance, tests, docs, and prioritized improvement ideas
- `duv`: DUV Ultramarathon Statistics lookup workflow
- `emu-branding`: EMU visual identity and brand guidance
- `error-debugging`: stack trace, crash report and panic analysis — root cause, fix, and verification across Kotlin/Android, KMP/Compose, Flutter, Swift, Rust and C++
- `freecad`: remote-control a running FreeCAD (parametric CAD) by Python via a local bridge — primitives/booleans, Sketcher + PartDesign features, live metrics + viewport screenshots, STEP/STL/IGES/OBJ export
- `github-commit-pr`: commit, push, and pull request workflow
- `github-do-issue`: implement a GitHub issue locally before commit or PR creation
- `github-fix-action-error`: diagnose and fix the latest failing GitHub Actions run
- `github-issues`: create, triage, label, comment on, and manage GitHub issues
- `markitdown`: convert PDF, Office, HTML, data, e-book, image, audio, and ZIP files (or YouTube URLs) to Markdown via Microsoft's markitdown CLI or Python API
- `test-generation`: generate unit, integration and UI tests plus coverage gap analysis — framework detection, case selection, source-set placement across Kotlin/KMP, Compose, Flutter/Dart, Swift, Rust and C++

## Conventions

### Skill directories (`skills/`)
- Directory name: **kebab-case** (e.g. `github-commit-pr`)
- Every skill dir must contain exactly one `SKILL.md`
- The frontmatter `name:` **must** equal the directory name
- Required YAML frontmatter fields: `name`, `description`
- Optional fields: `category`, `risk`, `tags`, `allowed-tools`, `argument-hint`, `license`
- No other top-level frontmatter keys — the validator rejects unknown fields so that
  tooling-generated blocks (e.g. the `metadata:` block written by `gh skill install`)
  don't drift into the catalog

### Frontmatter fields

| Field | Required | Value |
|-------|----------|-------|
| `name` | yes | kebab-case, equal to the directory name |
| `description` | yes | what the skill does **and** when to use it (see below) |
| `category` | no | free-form single token grouping the skill (e.g. `testing`, `git`, `3d`) |
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
README/AGENTS catalog sync, and broken relative Markdown links.

## Adding a new skill

Use Anthropic's **skill-creator** skill to author the skill body — it walks through
scaffolding, description writing, and evaluation:
<https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md>
(available as the `skill-creator` skill in Claude Code). Then apply this repo's
conventions on top:

1. Create `skills/<kebab-name>/SKILL.md` with valid frontmatter
2. Add an entry to **Available Skills** in both [README.md](README.md) and this file
3. Run `bash .github/scripts/validate.sh`
