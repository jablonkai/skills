---
name: github-do-issue
description: "Fetch a GitHub issue, understand its requirements, plan and implement the solution, then run verification — without committing, pushing, or creating a PR. Use when someone says 'work on issue #N', 'do #N', 'implement #N', 'fix issue #N', 'dolgozz a #N-es issue-n', or pastes a GitHub issue URL and wants it implemented. The user always reviews the result and decides when to commit. Pairs naturally with github-commit-pr for the commit step afterward."
category: development-workflow
risk: low
tags:
  - github
  - issues
  - development
  - workflow
allowed-tools: Bash, Read, Grep, Glob, Edit, Write
argument-hint: "<issue-number-or-url>"
---

# github-do-issue

## Purpose

Structured workflow for implementing a GitHub issue in any project. Fetch the issue, understand the requirements, plan the approach, implement the solution, and verify it — then stop and let the user review before any git operations happen.

## When to use

- User says "work on issue #N", "do #N", "implement #N", or similar
- User provides a GitHub issue URL
- User references an issue number and asks to implement it

## Prerequisites

Before starting, verify the environment:

1. **Repository context:**

```bash
git rev-parse --show-toplevel
```

If not in a git repository, abort with a clear message.

## Workflow

### Step 1: Fetch issue details

Parse the issue number from `$ARGUMENTS`:

- `42` or `#42` → use directly
- `https://github.com/owner/repo/issues/42` → extract `42` and the `owner/repo` from the URL. If the URL points to a different repo than the current working directory, warn the user and ask whether to proceed (the implementation will happen in the current repo, but the issue context comes from the referenced repo).

Fetch the issue:

```bash
gh issue view "$ISSUE_NUMBER" ${ISSUE_REPO:+--repo "$ISSUE_REPO"} --json number,title,body,labels,assignees,milestone,state,comments
```

`ISSUE_REPO` is set to `owner/repo` only when the input was a URL pointing to a different repository; otherwise it is left unset and `gh` defaults to the current repository.

If the command fails (issue not found, permission denied), report the error and stop.

**Check issue state:** If the issue is already closed, warn the user:

```
Issue #42 is already closed. Do you still want to implement it?
```

Proceed only if the user confirms.

Display a summary to the user (the `comments` field is included in the fetch above — they often contain clarifications, decisions, or updated requirements):

```
Issue #42: <title>
State: open | Labels: enhancement
---
<issue body, trimmed to key requirements>
<key points from comments, if any>
```

### Step 2: Understand requirements

Extract from the issue body and comments:

- **What needs to change** — the feature, fix, or improvement
- **Acceptance criteria** — checkboxes or explicit requirements
- **Scope boundaries** — what is NOT in scope (if mentioned)
- **Related context** — linked issues, mentioned files, or referenced PRs

If the issue is unclear or missing critical details, ask the user for clarification before proceeding.

### Step 3: Plan the approach

Before writing any code:

1. Identify which files need to be created or modified
2. Check for existing tests that cover the affected code — new changes should maintain or extend test coverage, not break it
3. Consider the project's existing patterns and conventions — read project documentation (README.md, CLAUDE.md, AGENTS.md, CODEX.md, CONTRIBUTING.md, or similar), check existing code for patterns, review configuration files
3. Present a brief implementation plan to the user:

```
Implementation plan for #42:
1. <specific change>
2. <specific change>
3. <specific change>
```

4. If the plan reveals the issue is larger than expected, tell the user and suggest breaking it into smaller steps or separate issues.

Wait for the user to approve or adjust the plan.

### Step 4: Implement

Execute the approved plan:

- Follow existing code conventions and patterns discovered in Step 3
- Keep the issue comments in view while implementing — they often carry the most recent decisions, clarifications, or requirement changes that supersede the original body. Implement what the latest comment thread agreed on, not just the opening description.
- Write clean, focused changes — only what the issue requires, no scope creep
- If the project uses i18n, add translation keys for new user-visible strings
- If a sub-task turns out to be more complex than planned, pause and inform the user rather than expanding scope silently

### Step 5: Verify

After implementation, run the project's verification checks. Detect which tools are available and run the appropriate ones:

- **TypeScript/JavaScript:** `npx tsc --noEmit`, `npm test`, `npm run lint`
- **Rust:** `cargo check`, `cargo test`
- **Python:** `python -m pytest`, `mypy .`, `ruff check .`
- **Go:** `go build ./...`, `go test ./...`
- **Android (Kotlin/Java):** `./gradlew build`, `./gradlew test`, `./gradlew lint`
- **Flutter/Dart:** `flutter analyze`, `flutter test`
- **Swift:** `swift build`, `swift test`
- **Ruby:** `bundle exec rspec`, `bundle exec rubocop`
- **.NET (C#/F#):** `dotnet build`, `dotnet test`
- **Elixir:** `mix compile --warnings-as-errors`, `mix test`, `mix credo`
- **Other:** check `package.json` scripts, `Makefile`, CI config, or `build.gradle` for available checks

Also check for CI configuration (`.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `.circleci/`) to understand which checks the project runs in CI — these are the verification steps the PR will need to pass.

If no verification commands are found, inform the user and suggest they run their own checks manually.

Run at minimum the type checker / compiler. Fix any errors before proceeding.

### Step 6: Report and stop

Present a summary of all changes made:

```
Done — Issue #<number>: <title>

Files modified:
- <path> (new)
- <path> (modified)

Verification:
- Type check: clean
- Tests: passed

Ready for review.
```

**STOP HERE.** Do not commit, push, create a branch, or create a PR. The user decides what to do next. If they want to commit and open a PR, the `github-commit-pr` skill handles that workflow end-to-end.

## Error handling

| Scenario | Detection | Action |
|----------|-----------|--------|
| `gh` not installed | `command -v gh` fails | Direct user to https://cli.github.com |
| Not in a git repo | `git rev-parse` fails | Abort with clear message |
| Issue not found | `gh issue view` exits non-zero | Verify issue number and repo |
| Permission denied | `gh` returns 403/404 | Check repo access and auth scopes |
| Issue already closed | `state` field is `CLOSED` | Warn user, proceed only if confirmed |
| Issue from different repo | URL doesn't match current repo | Warn user, ask whether to proceed |
| Scope larger than expected | Discovered during planning/implementation | Pause, inform user, suggest splitting |
| Verification tools not found | Commands not available | Inform user, suggest manual verification |

## Critical constraints

These boundaries exist because this skill handles only the implementation phase — the user controls the git workflow:

- Do not commit after completing the implementation — the user needs to review the changes first and may want to adjust them
- Do not push to any remote — pushing is a separate decision that belongs to the user
- Do not create a PR automatically — PR creation involves title, description, and reviewer choices the user should make
- Do not create a branch — stay on the current branch; the user may have their own branching strategy or want to use `github-commit-pr` for this
- Do not modify files outside the scope of the issue — scope creep creates review burden and makes it harder to revert changes
- Ask for clarification rather than guessing when requirements are ambiguous — a wrong guess wastes more time than a quick question
- If implementation reveals unexpected complexity, pause and inform the user rather than expanding scope — they may want to split the work into multiple issues
