---
name: code-analyzer
description: "Audit an entire project for bugs, security vulnerabilities, code quality problems, performance issues, missing tests, documentation gaps, and concrete improvement or feature ideas — then produce a prioritized, actionable report with file:line references. Read-only by default; only edits or commits when the user explicitly asks for a fix afterwards. Use when someone says 'review my project', 'audit the codebase', 'find bugs', 'check for security issues', 'what could be improved', 'suggest improvements', 'are there any vulnerabilities', 'do a code quality review', or the Hungarian equivalents 'nézd át a projektet', 'auditáld a kódot', 'találj hibákat', 'milyen biztonsági problémák vannak', 'javasolj fejlesztéseket', 'mit lehetne javítani'. Trigger this skill whenever the user wants a holistic assessment of a project rather than a fix to one specific thing — even if they don't say the word 'audit'."
category: code-quality
risk: low
tags:
  - audit
  - review
  - security
  - code-quality
  - refactoring
  - bugs
allowed-tools: Bash, Read, Grep, Glob, Edit, Write
argument-hint: "[focus: security|quality|performance|tests|docs|ideas|all]"
---

# code-analyzer

## Purpose

Give the user a clear, prioritized picture of the health of their project: what's broken, what's risky, what's messy, what's missing, and what could be added. The output is a structured report — not a pile of speculation. Every finding points at a real file, names the concern in plain terms, and proposes a direction.

This is a diagnostic skill, not a refactor skill. Do not edit code, run formatters, or commit anything as part of the audit. Only after the user reads the report and explicitly picks something to fix do you change code.

## When to use

- User asks for a project review, audit, code quality check, or general "what's wrong with this codebase"
- User asks about security issues, vulnerabilities, or hardening across the project
- User asks "what could be improved" or "what should I work on next"
- User asks for new feature ideas grounded in the existing project
- Hungarian equivalents: "nézd át", "auditáld", "találj hibákat", "javasolj fejlesztéseket"

If the user has a specific bug or feature in mind ("fix this crash", "add this endpoint"), that is **not** this skill — handle it directly.

## Prerequisites

Verify the basics before starting:

1. **Inside a project directory**

```bash
git rev-parse --show-toplevel 2>/dev/null || pwd
```

A git repo is preferred (it lets you read recent history for context) but not required. Note the project root and use it as the base for all paths in the report.

2. **Working tree state**

```bash
git status --porcelain 2>/dev/null
```

Uncommitted changes are fine for an audit — you are not modifying anything. Just be aware the user may already be mid-flight; flag in-progress files if they show up in findings so the user knows whether the issue is theirs or pre-existing.

## Workflow

### Step 1: Scope the audit

A whole-project audit has unbounded scope. Before reading any code, decide the shape of the work along three axes:

- **Focus**: all dimensions, or just one (security / quality / performance / tests / docs / ideas)?
- **Scope**: whole repo, a subdirectory, or a list of changed files? For very large repos (more than ~1000 source files) sample explicitly — pick the most-edited, largest, or most-central modules first — rather than producing a wide-and-shallow report that misses real issues.
- **Constraints**: anything to skip (generated code, vendored deps, legacy modules slated for deletion, third-party SDKs)?

**Interactive use** (a human is in the loop): if the focus argument was passed, use it. Otherwise state your default plan in one short message and proceed unless the user pushes back. Do not turn this into a long interview — the user wants findings, not a kickoff meeting.

**Non-interactive use** (no human to ask — running inside an automation, evaluation, or pipeline): pick reasonable defaults (whole repo, all dimensions, standard ignore set) and write the scoping decision into the report's executive summary instead of asking. Never block waiting for input.

### Step 2: Discover the project

Build a mental model of what you're auditing before judging it. Collect, in parallel where possible:

- **Languages and sizes**: file counts and approximate lines per language. `git ls-files` (or `find`) plus `wc -l` is fine.
- **Package / build manifests**: `package.json`, `pyproject.toml`, `requirements*.txt`, `Cargo.toml`, `go.mod`, `pubspec.yaml`, `Gemfile`, `pom.xml`, `build.gradle*`, `composer.json`, etc. These tell you the framework, runtime version, and dependencies.
- **Existing tooling**: linters, type checkers, formatters, security scanners, test runners — look in config files (`.eslintrc*`, `ruff.toml`, `tsconfig.json`, `pytest.ini`, `.golangci.yml`, `analysis_options.yaml`, etc.) and CI workflows (`.github/workflows/`, `.gitlab-ci.yml`, `Makefile`).
- **Entry points and structure**: `main.*`, `index.*`, top-level dirs (`src/`, `lib/`, `app/`, `cmd/`).
- **Documentation**: `README*`, `CONTRIBUTING*`, `docs/`, `CHANGELOG*`. Skim, don't read in full.
- **Recent activity**: `git log --since="3 months ago" --pretty=oneline | head -50` to see hotspots and intent.

Knowing what tooling is already configured matters: if the project already runs `ruff` and `mypy` in CI, redundant style nitpicks add noise. Bias the report toward issues the existing pipeline is **not** catching.

Skip these by default unless the user says otherwise: `node_modules/`, `.git/`, `dist/`, `build/`, `target/`, `vendor/`, `.next/`, `__pycache__/`, `.venv/`, generated code, lockfiles. They drown signal in noise.

### Step 3: Let the existing tools do the boring work

Before reading code yourself, run the tools the project already configures and capture their output. This is faster, more reliable, and produces signals everyone trusts. Examples (only run what's actually configured or installed in the project):

- JS/TS: `npm audit --json`, `npx eslint . --format json`, `npx tsc --noEmit`
- Python: `pip-audit`, `ruff check .`, `mypy .`, `bandit -r .`
- Go: `go vet ./...`, `staticcheck ./...`, `govulncheck ./...`
- Rust: `cargo clippy -- -D warnings`, `cargo audit`
- Dart/Flutter: `flutter analyze`, `dart pub outdated`
- Generic: `gitleaks detect`, `trufflehog filesystem .` (secrets), `git grep -nE "TODO|FIXME|HACK|XXX"`

If a tool isn't installed, just note in the report that "running `<tool>` would surface more issues here" and move on (see Critical constraints — do not auto-install).

If **none** of the standard tools for the project's primary language are installed or configured, that absence is itself a finding worth surfacing in the report under tooling/DX — it means correctness signals the rest of the team probably assumes are in place actually aren't.

For long-running scans, prefer JSON output and parse a summary into the report rather than dumping raw logs at the user.

### Step 4: Read the code with intent

Now do the manual / LLM-driven pass. Spawn parallel `Agent` (Explore) subagents per area when the codebase is non-trivial — security pass, quality pass, performance pass, etc. — so each one can dig deeply without being distracted. For small codebases, one focused pass is fine.

For each dimension below, look for **concrete, locatable** findings — not vibes. Every finding must point at a real location: usually a file (with a line range when possible), but for project-level absences — no `.gitignore`, no `LICENSE`, no test directory, no CI config — `Where: project root` (or the missing path, e.g. `Where: tests/ (missing)`) is fine and expected. The rule is "no hand-wavy findings", not "must always be a single line".

**Correctness and bugs**
- Unhandled error paths (rejected promises, swallowed exceptions, ignored returns)
- Null / undefined / missing optional handling
- Off-by-one, wrong loop bounds, stale references
- Race conditions and async ordering bugs
- Dead code, unreachable branches, contradictory conditions
- Type confusions (especially in dynamic languages)

**Security**
- Injection: SQL, NoSQL, OS command, path traversal, template, LDAP
- Cross-site scripting (unescaped output to HTML/DOM)
- Hardcoded secrets, API keys, tokens, private keys (also in commit history if the repo is small enough to grep)
- Weak crypto: MD5/SHA1 for security, custom crypto, weak random for tokens
- Insecure defaults: permissive CORS, missing auth checks, debug routes in production code paths
- Insecure deserialization, SSRF, open redirects
- Dependency CVEs not already flagged by the tooling pass
- Logging of sensitive data
- Missing input validation at trust boundaries

**Code quality**
- Large files, long functions, deep nesting, complex conditionals
- Duplication that could be extracted (but only when extraction would clearly help — duplication is sometimes cheaper than a bad abstraction)
- Naming that misleads: variables, functions, modules whose names don't match what they do
- Comments that contradict the code
- Inconsistent style across modules where the project already has a chosen style

**Architecture**
- Tight coupling between layers that should be independent
- Circular dependencies between modules
- Business logic mixed into UI / route handlers / migrations
- Missing or premature abstractions

**Performance**
- N+1 query patterns
- Synchronous I/O on hot paths
- Unbounded loops, missing pagination
- Large allocations in tight loops, repeated regex compilation, string concatenation in loops
- Missing indexes implied by query shape (when schema is visible)

**Testing**
- Critical paths with no tests (auth, payments, anything money- or data-loss-related)
- Tests that assert nothing meaningful or are tautological
- Patterns that produce flakes (real time, real network, shared global state)
- Missing edge cases on parsers, validators, boundary conditions

**Documentation and DX**
- Missing or stale README sections (setup, run, test, deploy)
- Public APIs without docstrings or type hints
- Undocumented environment variables / config
- No CHANGELOG or unclear release process
- Slow build, unclear error messages, missing pre-commit hooks

**Feature and enhancement ideas**
This is the most speculative dimension. Only suggest features when there's a real signal in the code — a TODO, a half-implemented flow, an obvious gap (e.g., "the API exposes list/get/create but no delete"), or a manual workflow that begs to be automated. Mark these clearly as **ideas**, not problems. Do not invent features for the sake of producing a longer list.

### Step 5: Score and prioritize

Assign each finding two attributes. These let the user filter and decide what to act on:

- **Severity**: `critical` (data loss, security breach, broken core flow), `high` (real bug, common-case failure, exploitable in plausible conditions), `medium` (correctness or quality issue with workaround), `low` (style, minor smell), `info` (idea, observation)
- **Confidence**: `high` (you can point at the exact misbehaving line and say what's wrong), `medium` (the pattern is suspicious and likely wrong, but verifying needs running the code), `low` (this might be intentional — flag for the maintainer to confirm)

If you find yourself writing many `low confidence / low severity` items, stop. They make the report unreadable and obscure the things that matter. Cut anything that doesn't change the user's plan for the week.

### Step 6: Produce the report

Save the report to `CODE_AUDIT_<YYYY-MM-DD>_<HHMM>_<auditor>.md` at the project root — e.g. `CODE_AUDIT_2026-06-29_1430_claude-opus-4-8.md`. The timestamp records when the audit ran and `<auditor>` records who ran it, so repeated audits pile up side by side instead of silently overwriting the last one. Build the name from the local clock and the auditor's identity:

```bash
date +%Y-%m-%d_%H%M        # the date + time component, e.g. 2026-06-29_1430
```

For `<auditor>`, use the model id when an agent runs the audit (e.g. `claude-opus-4-8`), or the git `user.name` (slugified, lowercase, spaces → `-`) when a human does. (Or print inline if the user prefers.) Use this structure exactly — it's a contract the user can skim quickly:

```markdown
# Code audit — <project name> — <YYYY-MM-DD HH:MM>

## Executive summary
<3–6 lines: scope of audit, headline counts (critical/high/medium/low), the single biggest concern, and the single highest-leverage improvement>

## Findings

### Critical
<one entry per finding, in the format below — or "None" if nothing critical>

### High
...

### Medium
...

### Low
...

### Ideas (feature & enhancement opportunities)
...

## What was NOT analyzed
<honest list: paths skipped, tools not run, areas you only sampled>

## Suggested next steps
<3–5 bullets: which findings to act on first and why; how the user could attack the list>
```

**Finding entry format:**

```markdown
#### [<id>] <short title>
- **Where**: `path/to/file.ext:LINE` (or `path/to/file.ext` if it's file-level)
- **Category**: bug | security | quality | performance | tests | docs | architecture | idea
- **Severity / Confidence**: high / high
- **What**: <one or two sentences describing the issue>
- **Why it matters**: <impact in plain terms>
- **Suggested fix**: <concrete direction; code sketch only if it really helps>
```

Use stable ids like `SEC-01`, `BUG-01`, `Q-01`, `IDEA-01` so the user can reference them later.

Keep prose tight. The user is going to triage this list — every extra paragraph slows them down.

### Step 7: Hand off and offer next steps

**Interactive use**: after delivering the report, offer the user clear options. Do not start fixing things without being asked:

```
Audit complete. Report at CODE_AUDIT_<YYYY-MM-DD>_<HHMM>_<auditor>.md.

Want me to:
  1. Fix specific findings — name the ids, e.g. "fix SEC-01, BUG-02, Q-03"
  2. Open GitHub issues for the high/critical items (uses `gh issue create`)
  3. Drill into one finding in more depth
  4. Re-run the audit with different scope or focus
```

Wait for direction. If the user picks fixes, treat each finding as an independent small task — read the relevant code, make the smallest change, and confirm before moving on. Do not bundle unrelated fixes into one mega-commit.

**Non-interactive use**: skip the menu. State the absolute path to the report and stop — the calling system will read the report and decide what to do next.

## Output principles

These shape the quality of the report more than any single rule above:

- **Locatable beats clever.** A boring finding with a real file:line is worth ten elegant abstract critiques.
- **Confidence over coverage.** A short, sharp report the user trusts is more valuable than a long one they have to defend against.
- **Respect the user's existing taste.** If the project clearly chose a convention you'd have done differently, that's not a finding — it's their call. Findings are about real costs (correctness, security, maintainability), not preferences.
- **Distinguish ideas from defects.** Feature suggestions should never be mixed in with the bugs. The user needs to know what to fix vs. what to consider.
- **Be honest about what you skipped.** "What was NOT analyzed" is a real section, not a footnote — it tells the user where their blind spots remain.

## Critical constraints

- Read-only audit. Do not run formatters, do not edit files, do not commit, do not push as part of the audit pass.
- Do not run package installers, dependency updates, or anything that mutates `node_modules` / `.venv` / lockfiles. If a tool isn't installed, note it; don't install it silently.
- Every finding must be locatable — a real file (with a line range when possible) or a named project-level location like `project root` or `tests/ (missing)`. If you can't point at any concrete location, the finding doesn't go in the report.
- Don't pad the report. If a category has no findings, write "None" — that's useful information.
- Don't claim something is a vulnerability unless you can describe how it would be exploited and what the impact is. Lower the severity if the exploit path is hand-wavy.
- For very large projects, sample explicitly and disclose what you sampled. Never silently skip half the codebase.
- If the user asks for fixes after the report, treat each finding as a separate small task. Don't smuggle unrelated changes into the same edit.
