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
- `test-generation`: write unit, integration and UI tests for existing code — framework detection from the build files, case selection for boundaries and error paths, correct source-set placement, and coverage gap analysis across Kotlin/KMP, Compose, Flutter/Dart, Swift, Rust and C++

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

1. Create `skills/<kebab-name>/SKILL.md` with `name` and `description` frontmatter. The
   `name` must match the directory name.
2. Write the description so it triggers reliably — say what the skill does *and* when to
   use it, with concrete trigger phrases.
3. Keep `SKILL.md` short; push long reference material into `references/` and
   deterministic work into `scripts/`.
4. Add an entry to **Available Skills** in this file and in [AGENTS.md](AGENTS.md).
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

- required frontmatter fields (`name`, `description`)
- frontmatter `name` matches the directory name
- only documented frontmatter fields are used, and `risk` is `low`, `medium` or `high`
  (see [AGENTS.md](AGENTS.md#frontmatter-fields))
- kebab-case skill directory names
- every skill directory contains a `SKILL.md`
- README and AGENTS skill lists match the actual directories
- broken relative Markdown links

The same script runs in CI on every push and pull request
(see [.github/workflows/validate.yml](.github/workflows/validate.yml)).

## License

[MIT](LICENSE). Bundled third-party assets keep their own licenses — see the
license file shipped alongside each one (for example
[Nebula Sans](skills/emu-branding/assets/fonts/NebulaSans/license.txt) and
[cavalry-types](skills/cavalry/references/cavalry-types/LICENSE)).
