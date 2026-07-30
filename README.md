# skills

Personal catalog of reusable, task-oriented skills for AI coding agents (Claude Code and
compatible tools). One directory per skill, each with a `SKILL.md` entry point and any
reference material, scripts, or assets it needs.

This repository is the home for these skills — they were previously kept alongside agents
and instruction files in `agent-tools`, which now keeps only the agents, the global
instruction file, and the `update-all` bootstrap script.

## Available Skills

### App automation
- `affinity`: remote-control Affinity (the unified Affinity by Canva app) with JavaScript via its local automation endpoint — automate document edits, batch operations, and reusable library scripts with a zero-dependency CLI, no MCP client configuration
- `blender`: remote-control a running Blender by Python via a local bridge — build 3D scenes live with bmesh/modifiers, shader and geometry nodes, animation, rigging, physics, Grease Pencil and the VSE; verify with metrics + viewport screenshots; render EEVEE/Cycles stills and video; export glTF/FBX/USD/Alembic/OBJ/STL
- `cavalry`: remote-control Cavalry (Scene Group's 2D motion-design app) via a scriptable bridge — build scenes procedurally, animate with keyframes/easing and per-letter text effects, then render PNG frames or alpha overlay videos
- `freecad`: remote-control a running FreeCAD (parametric CAD) by Python via a local bridge — build models live from primitives/booleans, constrained Sketcher profiles, and PartDesign features; measure via metrics + inline viewport screenshots; export STEP/IGES/STL/OBJ

### GitHub workflows
- `github-commit-pr`: end-to-end workflow for committing changes, pushing a branch, and opening or updating a GitHub pull request
- `github-do-issue`: workflow for fetching a GitHub issue, implementing it in the current repository, and stopping before commit or PR creation
- `github-fix-action-error`: diagnoses the latest failing GitHub Actions run on the current branch, applies a targeted fix locally, and — after user approval — commits and pushes (refuses to run on `main`/`master`/`develop`)
- `github-issues`: standardized issue creation, labeling, triage, commenting, and issue management through the GitHub CLI

### Development & analysis
- `code-analyzer`: holistic read-only project audit for bugs, security vulnerabilities, code quality issues, performance risks, missing tests, documentation gaps, and prioritized improvement ideas
- `error-debugging`: analyze a stack trace, crash report, panic or error log down to its root cause, then propose a fix and a way to verify it — covers Kotlin/Android, KMP/Compose, Flutter/Dart, Swift, Rust and C++, including deobfuscation and symbolication of release traces
- `markitdown`: convert PDF, Office, HTML, data, e-book, image, audio, and ZIP files (or YouTube URLs) to clean Markdown using Microsoft's markitdown tool, via CLI or Python API

### Ultrarunning domain
- `duv`: search and retrieve data from the DUV Ultramarathon Statistics website (statistik.d-u-v.org), including runner profiles, events, and rankings
- `emu-branding`: brand guidelines and visual identity for EMU (Egyesület a Magyar Ultrafutásért), including logo, color palette, and typography

## Repository Layout

```
skills/<name>/
├── SKILL.md          # required — frontmatter + instructions
├── references/       # optional — docs loaded on demand
├── scripts/          # optional — helper scripts
└── assets/           # optional — templates, fonts, images
```

## Using These Skills

Claude Code discovers skills from `~/.claude/skills/`. To make a skill from this repo
available globally, symlink it:

```bash
ln -s "$PWD/skills/<name>" ~/.claude/skills/<name>
```

Symlinking (rather than copying) keeps the installed skill in sync with the repo. To
install all of them:

```bash
for d in skills/*/; do
  ln -sfn "$PWD/$d" ~/.claude/skills/"$(basename "$d")"
done
```

Skills can also be used per-project by placing them under a repository's `.claude/skills/`.

## Adding a New Skill

1. Create `skills/<kebab-name>/SKILL.md` with `name` and `description` frontmatter. The
   `name` must match the directory name.
2. Write the description so it triggers reliably — say what the skill does *and* when to
   use it, with concrete trigger phrases.
3. Keep `SKILL.md` short; push long reference material into `references/` and
   deterministic work into `scripts/`.
4. Add an entry to **Available Skills** in this file and in [AGENTS.md](AGENTS.md).
5. Run the validator.

See [AGENTS.md](AGENTS.md) for the full conventions.

## Validation

```bash
bash .github/scripts/validate.sh
```

The validator checks:

- required frontmatter fields (`name`, `description`)
- frontmatter `name` matches the directory name
- kebab-case skill directory names
- every skill directory contains a `SKILL.md`
- README and AGENTS skill lists match the actual directories
- broken relative Markdown links

The same script runs in CI on every push and pull request
(see [.github/workflows/validate.yml](.github/workflows/validate.yml)).
