# skills

Personal catalog of reusable, task-oriented skills for AI coding agents (Claude Code and
compatible tools). One directory per skill, each with a `SKILL.md` entry point and any
reference material, scripts, or assets it needs.

Skills here follow the open **Agent Skills** format documented at
[agentskills.io](https://agentskills.io/) — the reference for the `SKILL.md` structure,
frontmatter fields, and progressive disclosure model used throughout this repo. The format
is supported by Claude Code and a growing number of other agents, so these skills are
portable beyond a single tool.

## Available Skills

<!-- Generated from the `summary:` and `category:` frontmatter of each skill.
     Edit skills/<name>/SKILL.md, then run .github/scripts/generate-catalog.sh -->
<!-- BEGIN GENERATED SKILLS -->
### App automation
- `affinity`: remote-control Affinity (the unified Affinity by Canva app) with JavaScript via its local automation endpoint — document edits, batch operations, and reusable library scripts, with no MCP client configuration
- `apple-photos`: query, export and organise the Apple Photos library with osxphotos and AppleScript — searches by date, place, people and keywords, yearly statistics, original or edited exports with XMP sidecars, albums from a query, and file import
- `apple-shortcuts`: list, inspect and run Apple Shortcuts from the CLI — file and text input and output, folder batches, timeout-guarded agent steps, decoding exported .shortcut files, and generating signed shortcuts for one-click import
- `blender`: remote-control a running Blender by Python via a local bridge — bmesh/modifier modeling, shader and geometry nodes, animation, rigging, physics, Grease Pencil and the VSE, EEVEE/Cycles stills and video, glTF/FBX/USD/OBJ/STL export
- `brl-cad`: model CSG solids headless with BRL-CAD — mged command scripts for primitives, boolean regions and materials, rt raytraced views, gqa overlap, volume and mass checks, STL/OBJ/STEP export
- `cavalry`: remote-control Cavalry (Scene Group's 2D motion-design app) via a scriptable bridge — build scenes procedurally, animate with keyframes and per-letter text effects, then render PNG frames or alpha overlay videos
- `compressor`: batch-transcode with Apple Compressor via its CLI — ProRes, H.264, HEVC and image-sequence deliverables from files or folders, built-in and custom settings lookup, derived custom settings, monitored, stoppable and resumable batches, ffprobe-verified outputs
- `davinci-resolve`: remote-control a running DaVinci Resolve by Python via its scripting API — media import and bins, timeline assembly, markers, titles and lower thirds, subtitles, LUT/CDL grades, render queue deliverables, EDL/FCPXML/OTIO export
- `drawio`: remote-control the draw.io desktop app with JavaScript over its DevTools port — live shape building, ELK auto-layout, pages, save — or author .drawio XML directly and export PNG/SVG/PDF or convert Mermaid/CSV with the headless CLI
- `final-cut-pro`: build and inspect Final Cut Pro timelines through FCPXML — rough cuts with gaps, connected clips, transitions, titles, markers and keywords, exact rational-time math, DTD validation, import with AppleScript read-back, FCPXML parsing and Resolve interchange
- `freecad`: remote-control a running FreeCAD (parametric CAD) by Python via a local bridge — primitives and booleans, constrained Sketcher profiles, PartDesign features, metrics and viewport screenshots, STEP/IGES/STL/OBJ export
- `gimp`: remote-control a running GIMP by Python through its built-in Script-Fu server — layer stacks, selections and masks, brush and gradient drawing, text layers, non-destructive GEGL filters, and PNG/JPEG/.xcf export or batch conversion in the live session
- `handbrake`: transcode and compress video with HandBrakeCLI — file and folder batches, DVD/Blu-ray title selection, built-in and GUI-exported presets, H.265/AV1 quality targets, audio and subtitle track picking with burn-in, ffprobe-verified outputs
- `inkscape`: drive Inkscape headless from the CLI — author SVG illustrations directly, run actions such as text to path, boolean path ops, simplify and bitmap trace, then export PNG at any DPI or @2x, PDF, EPS and plain SVG, one file or whole folders
- `kicad`: automate KiCad 10 — DRC/ERC with JSON violation summaries, JLCPCB-ready fabrication zips (Gerbers, drill, CPL, BOM, STEP), board renders, and scripted footprint placement in a running PCB editor via the IPC API
- `krita`: remote-control a running Krita by Python through a local bridge — layer stacks, brush-engine strokes and QPainter pixels, SVG vector text, filters, masks, animation frames, and PNG/JPEG/.kra export or batch conversion in the running session
- `musescore`: write, engrave and convert sheet music headless with MuseScore Studio 4 — MusicXML lead sheets and arrangements from a compact spec, PDF/PNG/SVG/MP3/MIDI export, folder batch conversion, transposition and part extraction, score-meta verified output
- `nuke`: build and render Nuke comps headless with Nuke Non-commercial — .nk scripts authored as text, plate-swap templates, slates and burn-ins, Roto via Python hooks, EXR/DPX/PNG or ProRes renders with frame-count checks
- `obs`: remote-control a running OBS Studio by Python over obs-websocket v5 — scenes, sources and filters, scene-item transforms, recording, streaming, replay buffer and virtual camera, screenshot verification, and scene collections built from a JSON spec
- `pixelmator-pro`: remote-control Pixelmator Pro via AppleScript — layered compositions with image, text and shape layers, adjustments and effects, ML Super Resolution, Remove Background and Enhance, .pxd template fill, and single-file or folder-batch export to PNG, JPEG, HEIC, WebP and PSD
- `qcad`: draft 2D CAD drawings headless with QCAD — ECMAScript scripts for layers, entities, blocks, dimensions and hatches, title blocks on existing DXF, batch DXF/DWG to PDF/PNG, ezdxf-verified output
- `rebelle`: remote-control Rebelle and Rebelle Motion IO with JSON events — live WebSocket painting in Rebelle Pro, batch-rendered painted animation frames, and visual verification through canvas exports
- `scribus`: lay out print documents headless with Scribus — multi-page layouts with master pages, styles, threaded text and images, CSV-driven badges and catalogues, PDF/X-4 export with bleed and marks
- `sonic-pi`: live-code music in Sonic Pi 5 via a headless OSC session — run and live re-evaluate live_loops, record exact-length WAV takes, stop jobs, surface runtime and syntax errors with line numbers

### GitHub workflows
- `github-commit-pr`: end-to-end workflow for committing changes, pushing a branch, and opening or updating a GitHub pull request
- `github-do-all-issues`: work through every open GitHub issue unattended — confirm the queue once, then implement, verify and open one PR per issue, skipping blocked ones with a reason
- `github-do-issue`: fetch GitHub issues — the named ones, or every open one when none is named — and implement them one at a time, each reviewed, committed and shipped as its own PR
- `github-fix-ci-error`: diagnose the latest failing GitHub Actions run on the current branch, apply a targeted fix locally, and — after user approval — commit and push; refuses to run on main/master/develop or the default branch
- `github-issues`: standardized issue creation (including batch filing from audit reports), labeling, triage, commenting, and issue management through the GitHub CLI

### Development & analysis
- `code-analyzer`: holistic read-only project audit for bugs, security vulnerabilities, code quality issues, performance risks, missing tests, documentation gaps, and prioritized improvement ideas
- `documentation-generator`: generate and refresh documentation from code — doc comments and API reference via Dokka, dartdoc, DocC, rustdoc and Doxygen, OpenAPI-driven REST docs, README scaffolding, conventional-commit changelogs, and architecture diagrams
- `error-debugging`: analyze a stack trace, crash report, panic or error log down to its root cause, then propose a fix and a way to verify it — Kotlin/Android, KMP/Compose, Flutter/Dart, Swift, Rust and C++, including deobfuscation and symbolication of release traces
- `keynote`: automate Apple Keynote via AppleScript/JXA — build decks from an outline with themes, layouts and presenter notes, edit .key text without losing formatting, skip or reorder slides, and PDF/PPTX/image export or batch conversion
- `libreoffice`: automate documents with headless LibreOffice and UNO — ODF/OOXML/PDF and PDF/A batch conversion, Calc recalculation with real values, Writer template fill and mail merge, Impress/Draw page export
- `markitdown`: convert PDF, Office, HTML, data, notebook, e-book, audio, and ZIP files (or YouTube URLs) to clean Markdown using Microsoft's markitdown tool, via CLI, batch script or Python API
- `numbers`: automate Apple Numbers via AppleScript/JXA — build spreadsheets from CSV with formulas and formats, read recalculated values back, and XLSX/CSV/PDF export or batch conversion
- `pages`: automate Apple Pages via AppleScript/JXA — fill templates and {{placeholders}} without losing formatting, swap images, CSV mail merge, and PDF/DOCX/EPUB export or batch conversion of .pages files
- `refactoring`: behavior-preserving refactoring — duplication extraction, complexity reduction, dead-code removal, naming and idiom cleanups, driven by each stack's own linter and verified step by step against the tests
- `testing`: write unit, integration and UI tests for existing code to at least 80% coverage — framework detection from the build files, case selection for boundaries and error paths, correct source-set placement, and measured coverage gap analysis across Kotlin/KMP, Compose, Flutter/Dart, Swift, Rust and C++

### Game development
- `godot`: build, run, test and export Godot 4 projects headless from the CLI — author scenes, GDScript and project settings as text, catch script errors from the log, test gameplay and UI signals with headless test scripts, capture Movie Maker frames, export Web and macOS builds

### Ultrarunning domain
- `duv`: search and retrieve data from the DUV Ultramarathon Statistics website (statistik.d-u-v.org) via its JSON API — runner profiles, event results, rankings, calendars, and national/continental records by distance, gender and age group
- `emu-branding`: brand guidelines and visual identity for EMU (Egyesület a Magyar Ultrafutásért), including logo, color palette, and typography
<!-- END GENERATED SKILLS -->

## Repository Layout

```
skills/<name>/
├── SKILL.md          # required — frontmatter + instructions
├── references/       # optional — docs loaded on demand
├── scripts/          # optional — helper scripts
└── assets/           # optional — templates, fonts, images
```

## Installing These Skills

Install straight from GitHub — no clone needed. Both installers below read this repo's
`skills/` directory and drop the chosen skills into the right place for your agent.

### With the `skills` CLI ([skills.sh](https://skills.sh))

```bash
# pick interactively from this repo
npx skills add jablonkai/skills

# a single skill, non-interactively (repeat the name for more)
npx skills add jablonkai/skills --skill error-debugging

# or address the skill by its path in the repo
npx skills add https://github.com/jablonkai/skills/tree/main/skills/error-debugging

# install globally (~/.claude/skills/) instead of into the current project
npx skills add jablonkai/skills --global
```

Other useful commands: `npx skills list`, `npx skills check`, `npx skills update`,
`npx skills remove <name>`.

### With the GitHub CLI (`gh` v2.90.0+)

```bash
# pick interactively from this repo
gh skill install jablonkai/skills

# a single skill
gh skill install jablonkai/skills error-debugging

# every skill in the repo, installed for Claude Code, user-wide
gh skill install jablonkai/skills --all --agent claude-code --scope user
```

`--scope project` (the default) installs into the current repository; `--scope user`
installs into your home directory so the skill is available everywhere. Pin a version
with `--pin <tag-or-sha>`, and update later with `gh skill update --all`.

## Adding a New Skill

Start with Anthropic's [skill-creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)
skill — it's the recommended way to scaffold a new skill, sharpen its description, and
evaluate whether it triggers reliably. It ships with Claude Code as the `skill-creator`
skill. Then apply this repo's conventions:

1. Create `skills/<kebab-name>/SKILL.md` with `name`, `description`, `summary` and
   `category` frontmatter. The `name` must match the directory name.
2. Write the description so it triggers reliably — say what the skill does *and* when to
   use it, with concrete trigger phrases. Keep `summary` to the one line that should
   appear in the catalog.
3. Keep `SKILL.md` short; push long reference material into `references/` and
   deterministic work into `scripts/`.
4. Regenerate the **Available Skills** sections of this file and
   [AGENTS.md](AGENTS.md) — never edit them by hand:

   ```bash
   .github/scripts/generate-catalog.sh
   ```

   A `category` that no theme covers yet is an error; add it to `CATALOG_SECTIONS` in
   the script.
5. Run the validator.

See [AGENTS.md](AGENTS.md) for the full conventions, and
[agentskills.io](https://agentskills.io/) for the format spec
([specification](https://agentskills.io/specification),
[quickstart](https://agentskills.io/skill-creation/quickstart)).

## Validation

```bash
bash .github/scripts/validate.sh
```

The validator checks:

- required frontmatter fields (`name`, `description`, `summary`, `category`)
- frontmatter `name` matches the directory name
- only documented frontmatter fields are used, and `risk` is `low`, `medium` or `high`
  (see [AGENTS.md](AGENTS.md#frontmatter-fields))
- kebab-case skill directory names
- every skill directory contains a `SKILL.md`
- the README and AGENTS skill lists match what the frontmatter renders — the check
  regenerates them and fails on any difference
- broken relative Markdown links, ignoring links inside fenced code blocks

The same script runs in CI on every push and pull request
(see [.github/workflows/validate.yml](.github/workflows/validate.yml)).

## License

[MIT](LICENSE). Bundled third-party assets keep their own licenses — see the
license file shipped alongside each one (for example
[Nebula Sans](skills/emu-branding/assets/fonts/NebulaSans/license.txt) and
[cavalry-types](skills/cavalry/references/cavalry-types/LICENSE)).
