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
- Validate every change with `bash .github/scripts/validate.sh`, and any change under
  `scripts/` with `bash .github/scripts/lint.sh` as well.
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
| `.github/scripts/lint.sh` | Static checks for the shipped `scripts/` (run before committing) |
| `.github/scripts/generate-catalog.sh` | Renders the Available Skills sections from frontmatter |
| `.github/scripts/catalog-lib.sh` | Helpers shared by the scripts above |

## Available Skills

<!-- Generated from the `summary:` and `category:` frontmatter of each skill.
     Edit skills/<name>/SKILL.md, then run .github/scripts/generate-catalog.sh -->
<!-- BEGIN GENERATED SKILLS -->
- `affinity`: remote-control Affinity (the unified Affinity by Canva app) with JavaScript via its local automation endpoint — document edits, batch operations, and reusable library scripts, with no MCP client configuration
- `apple-photos`: query, export and organise the Apple Photos library with osxphotos and AppleScript — searches by date, place, people and keywords, yearly statistics, original or edited exports with XMP sidecars, albums from a query, and file import
- `apple-shortcuts`: list, inspect and run Apple Shortcuts from the CLI — file and text input and output, folder batches, timeout-guarded agent steps, decoding exported .shortcut files, and generating signed shortcuts for one-click import
- `blender`: remote-control a running Blender by Python via a local bridge — bmesh/modifier modeling, shader and geometry nodes, animation, rigging, physics, Grease Pencil and the VSE, EEVEE/Cycles stills and video, glTF/FBX/USD/OBJ/STL export
- `brl-cad`: model CSG solids headless with BRL-CAD — mged command scripts for primitives, boolean regions and materials, rt raytraced views, gqa overlap, volume and mass checks, STL/OBJ/STEP export
- `cavalry`: remote-control Cavalry (Scene Group's 2D motion-design app) via a scriptable bridge — build scenes procedurally, animate with keyframes and per-letter text effects, then render PNG frames or alpha overlay videos
- `code-analyzer`: holistic read-only project audit for bugs, security vulnerabilities, code quality issues, performance risks, missing tests, documentation gaps, and prioritized improvement ideas
- `compressor`: batch-transcode with Apple Compressor via its CLI — ProRes, H.264, HEVC and image-sequence deliverables from files or folders, built-in and custom settings lookup, derived custom settings, monitored, stoppable and resumable batches, ffprobe-verified outputs
- `davinci-resolve`: remote-control a running DaVinci Resolve by Python via its scripting API — media import and bins, timeline assembly, markers, titles and lower thirds, subtitles, LUT/CDL grades, render queue deliverables, EDL/FCPXML/OTIO export
- `documentation-generator`: generate and refresh documentation from code — doc comments and API reference via Dokka, dartdoc, DocC, rustdoc and Doxygen, OpenAPI-driven REST docs, README scaffolding, conventional-commit changelogs, and architecture diagrams
- `drawio`: remote-control the draw.io desktop app with JavaScript over its DevTools port — live shape building, ELK auto-layout, pages, save — or author .drawio XML directly and export PNG/SVG/PDF or convert Mermaid/CSV with the headless CLI
- `duv`: search and retrieve data from the DUV Ultramarathon Statistics website (statistik.d-u-v.org) via its JSON API — runner profiles, event results, rankings, calendars, and national/continental records by distance, gender and age group
- `emu-branding`: brand guidelines and visual identity for EMU (Egyesület a Magyar Ultrafutásért), including logo, color palette, and typography
- `error-debugging`: analyze a stack trace, crash report, panic or error log down to its root cause, then propose a fix and a way to verify it — Kotlin/Android, KMP/Compose, Flutter/Dart, Swift, Rust and C++, including deobfuscation and symbolication of release traces
- `final-cut-pro`: build and inspect Final Cut Pro timelines through FCPXML — rough cuts with gaps, connected clips, transitions, titles, markers and keywords, exact rational-time math, DTD validation, import with AppleScript read-back, FCPXML parsing and Resolve interchange
- `freecad`: remote-control a running FreeCAD (parametric CAD) by Python via a local bridge — primitives and booleans, constrained Sketcher profiles, PartDesign features, metrics and viewport screenshots, STEP/IGES/STL/OBJ export
- `gimp`: remote-control a running GIMP by Python through its built-in Script-Fu server — layer stacks, selections and masks, brush and gradient drawing, text layers, non-destructive GEGL filters, and PNG/JPEG/.xcf export or batch conversion in the live session
- `github-audit-to-issues`: audit a project and file the findings as GitHub issues in one run — scoped severities, duplicate checks, one review table, security findings kept out of public issues
- `github-commit-pr`: end-to-end workflow for committing changes, pushing a branch, and opening or updating a GitHub pull request
- `github-do-all-issues`: work through every open GitHub issue unattended — confirm the queue once, then implement, verify and open one PR per issue, skipping blocked ones with a reason
- `github-do-issue`: fetch GitHub issues — the named ones, or every open one when none is named — and implement them one at a time, each reviewed, committed and shipped as its own PR
- `github-fix-ci-error`: diagnose the latest failing GitHub Actions run on the current branch, apply a targeted fix locally, and — after user approval — commit and push; refuses to run on main/master/develop or the default branch
- `github-issues`: standardized issue creation (including batch filing from audit reports), labeling, triage, commenting, and issue management through the GitHub CLI
- `godot`: build, run, test and export Godot 4 projects headless from the CLI — author scenes, GDScript and project settings as text, catch script errors from the log, test gameplay and UI signals with headless test scripts, capture Movie Maker frames, export Web and macOS builds
- `handbrake`: transcode and compress video with HandBrakeCLI — file and folder batches, DVD/Blu-ray title selection, built-in and GUI-exported presets, H.265/AV1 quality targets, audio and subtitle track picking with burn-in, ffprobe-verified outputs
- `inkscape`: drive Inkscape headless from the CLI — author SVG illustrations directly, run actions such as text to path, boolean path ops, simplify and bitmap trace, then export PNG at any DPI or @2x, PDF, EPS and plain SVG, one file or whole folders
- `keynote`: automate Apple Keynote via AppleScript/JXA — build decks from an outline with themes, layouts and presenter notes, edit .key text without losing formatting, skip or reorder slides, and PDF/PPTX/image export or batch conversion
- `kicad`: automate KiCad 10 — DRC/ERC with JSON violation summaries, JLCPCB-ready fabrication zips (Gerbers, drill, CPL, BOM, STEP), board renders, and scripted footprint placement in a running PCB editor via the IPC API
- `krita`: remote-control a running Krita by Python through a local bridge — layer stacks, brush-engine strokes and QPainter pixels, SVG vector text, filters, masks, animation frames, and PNG/JPEG/.kra export or batch conversion in the running session
- `libreoffice`: automate documents with headless LibreOffice and UNO — ODF/OOXML/PDF and PDF/A batch conversion, Calc recalculation with real values, Writer template fill and mail merge, Impress/Draw page export
- `markitdown`: convert PDF, Office, HTML, data, notebook, e-book, audio, and ZIP files (or YouTube URLs) to clean Markdown using Microsoft's markitdown tool, via CLI, batch script or Python API
- `musescore`: write, engrave and convert sheet music headless with MuseScore Studio 4 — MusicXML lead sheets and arrangements from a compact spec, PDF/PNG/SVG/MP3/MIDI export, folder batch conversion, transposition and part extraction, score-meta verified output
- `nuke`: build and render Nuke comps headless with Nuke Non-commercial — .nk scripts authored as text, plate-swap templates, slates and burn-ins, Roto via Python hooks, EXR/DPX/PNG or ProRes renders with frame-count checks
- `numbers`: automate Apple Numbers via AppleScript/JXA — build spreadsheets from CSV with formulas and formats, read recalculated values back, and XLSX/CSV/PDF export or batch conversion
- `obs`: remote-control a running OBS Studio by Python over obs-websocket v5 — scenes, sources and filters, scene-item transforms, recording, streaming, replay buffer and virtual camera, screenshot verification, and scene collections built from a JSON spec
- `pages`: automate Apple Pages via AppleScript/JXA — fill templates and {{placeholders}} without losing formatting, swap images, CSV mail merge, and PDF/DOCX/EPUB export or batch conversion of .pages files
- `pixelmator-pro`: remote-control Pixelmator Pro via AppleScript — layered compositions with image, text and shape layers, adjustments and effects, ML Super Resolution, Remove Background and Enhance, .pxd template fill, and single-file or folder-batch export to PNG, JPEG, HEIC, WebP and PSD
- `qcad`: draft 2D CAD drawings headless with QCAD — ECMAScript scripts for layers, entities, blocks, dimensions and hatches, title blocks on existing DXF, batch DXF/DWG to PDF/PNG, ezdxf-verified output
- `rebelle`: remote-control Rebelle and Rebelle Motion IO with JSON events — live WebSocket painting in Rebelle Pro, batch-rendered painted animation frames, and visual verification through canvas exports
- `refactoring`: behavior-preserving refactoring — duplication extraction, complexity reduction, dead-code removal, naming and idiom cleanups, driven by each stack's own linter and verified step by step against the tests
- `scribus`: lay out print documents headless with Scribus — multi-page layouts with master pages, styles, threaded text and images, CSV-driven badges and catalogues, PDF/X-4 export with bleed and marks
- `sonic-pi`: live-code music in Sonic Pi 5 via a headless OSC session — run and live re-evaluate live_loops, record exact-length WAV takes, stop jobs, surface runtime and syntax errors with line numbers
- `testing`: write unit, integration and UI tests for existing code to at least 80% coverage — framework detection from the build files, case selection for boundaries and error paths, correct source-set placement, and measured coverage gap analysis across Kotlin/KMP, Compose, Flutter/Dart, Swift, Rust and C++
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
| `name` | yes | kebab-case, equal to the directory name — max 64 characters |
| `description` | yes | what the skill does **and** when to use it (see below) — max 1024 characters |
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

The validator warns — it does not fail — when a `SKILL.md` runs past **250 lines** and
the skill has no `references/` directory, since that combination means detail that
could load on demand is loaded on every invocation instead. Splitting the detail out
clears the warning; so does deciding the skill genuinely has nothing to split.

## Validation

Always run before committing:

```bash
bash .github/scripts/validate.sh
```

Checks: frontmatter completeness, the allowed frontmatter field set and `risk`
vocabulary, `name:` and `description:` length caps, `name:`↔directory match, skill
directory structure, kebab-case names, README/AGENTS catalog sync (by regenerating both
sections and failing on any difference), and broken relative Markdown links (links
inside fenced code blocks are examples, not targets, and are skipped). It also
warns — without failing — on a `SKILL.md` over the progressive-disclosure line budget.

### Linting the shipped scripts

Whenever a `scripts/` file changes, also run:

```bash
bash .github/scripts/lint.sh
```

Checks every `.sh`, `.py`, `.js` and `.mjs` under `.github/scripts/` and the
`scripts/` of each published skill: `shellcheck` for shell, `python3 -m py_compile`
for Python, `node --check` for JavaScript. These are static checks only — the app
bridges need a live Blender, FreeCAD, Cavalry, GIMP, Krita, Rebelle or Affinity on
the other end, so CI cannot execute them, which makes a syntax error the failure
mode most likely to reach a consumer.

`python3` and `node` you already have; shellcheck is the one extra tool:

```bash
brew install shellcheck
```

The same script runs as the `lint` job in
[.github/workflows/validate.yml](.github/workflows/validate.yml), where all three
tools are preinstalled on the runner.

## Adding a new skill

Use Anthropic's **skill-creator** skill to author the skill body — it walks through
scaffolding, description writing, and evaluation:
<https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md>
(available as the `skill-creator` skill in Claude Code). Then apply this repo's
conventions on top:

1. Create `skills/<kebab-name>/SKILL.md` with valid frontmatter, including `summary` and `category`
2. Run `.github/scripts/generate-catalog.sh` to render the **Available Skills** entry into
   [README.md](README.md) and this file
3. Run `bash .github/scripts/validate.sh`, plus `bash .github/scripts/lint.sh` if the
   skill ships anything under `scripts/`
