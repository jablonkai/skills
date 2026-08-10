---
name: github-do-issue
description: "Fetch a GitHub issue, understand its requirements, plan and implement the solution, then run verification — without committing, pushing, or creating a PR. Works one issue at a time: when several issues are named at once, implement them sequentially so each one lands as its own commit and its own pull request, never bundled together. Use when someone says 'work on issue #N', 'do #N', 'implement #N', 'fix issue #N', 'dolgozz a #N-es issue-n', 'csináld meg a #12, #13 és #14 issue-kat', or pastes one or more GitHub issue URLs and wants them implemented. The user always reviews each issue's result and decides when to commit. Pairs naturally with github-commit-pr, which runs once per issue."
summary: "fetch GitHub issues and implement them one at a time — each issue reviewed, committed and shipped as its own PR"
category: development-workflow
risk: low
tags:
  - github
  - issues
  - development
  - workflow
allowed-tools: Bash, Read, Grep, Glob, Edit, Write
argument-hint: "<issue-number-or-url> [<issue-number-or-url> ...]"
---

# github-do-issue

## Purpose

Structured workflow for implementing a GitHub issue in any project. Fetch the issue, understand the requirements, plan the approach, implement the solution, and verify it — then stop and let the user review before any git operations happen.

## When to use

- User says "work on issue #N", "do #N", "implement #N", or similar
- User provides one or more GitHub issue URLs
- User references several issue numbers at once ("do #12, #13 and #14") — that is a queue of separate jobs, not one big job

## One issue, one commit, one PR

Each issue is a self-contained unit of work all the way through: its own implementation, its own review, its own commit, its own branch, its own pull request. Even when the user names five issues in a single sentence, that is five runs of this workflow, not one run covering five issues.

This matters because a pull request is the unit people review, discuss, revert and link back to an issue. A PR that closes three issues at once can't be reviewed in pieces, can't be reverted in pieces, and forces a reviewer who only cares about one of them to read all three. Interleaving the implementations is worse still: once two issues' edits are mixed in the working tree, they can no longer be split into clean commits without picking the diff apart by hand.

So when the input names more than one issue:

1. Confirm the queue and the order with the user before touching any code:

```
You've given me 3 issues. I'll do them one at a time, each with its own commit and PR:
1. #12 — <title>
2. #13 — <title>
3. #14 — <title>

Starting with #12. Order OK?
```

If the issues have a natural dependency (one builds on another), say so and propose that order. Otherwise take them in the order given.

2. Run the full workflow below — Steps 1 to 6 — for the first issue only.
3. Stop and let the user review and land it (`github-commit-pr --issue <N>` handles commit → branch → PR for that one issue; the `--issue` argument is what keeps its staging and its `Closes #N` scoped to this issue alone).
4. Only once that issue's changes have left the working tree — committed, or explicitly set aside by the user — start Step 1 for the next issue.

Never fetch all the issues up front and implement them together: keeping only the current issue in view is exactly what keeps its diff clean and reviewable.

## Prerequisites

Before starting, verify the environment:

1. **Repository context:**

```bash
git rev-parse --show-toplevel
```

If not in a git repository, abort with a clear message.

2. **Clean starting point:**

```bash
git status --porcelain
```

Uncommitted changes are not automatically a problem — but if they are the *previous* issue's work, starting the next one on top of them is how two issues end up in one commit. If the tree is dirty, show the user what's there and ask whether to commit it first (via `github-commit-pr --issue <N>` for the issue that work belongs to), stash it, or continue on purpose.

## Workflow

Run these steps for **one** issue at a time. When several issues are queued, return to Step 1 for the next one only after the previous issue has been reviewed and landed.

### Step 1: Fetch issue details

Parse the issue references from `$ARGUMENTS`. If there are several, keep the list as a queue and take only the first one now — the rest wait until this one is landed:

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
- Touch nothing that belongs to another queued issue, even if the fix is one line away and you'll be back for it in ten minutes. That line belongs in the other issue's commit, where a reviewer can connect it to the issue that asked for it. Note it and move on.

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

Present a summary of the changes made **for this issue**:

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

When more issues are queued, end the report by naming what's left and what has to happen first — the next issue starts from a clean tree, not on top of this diff:

```
Remaining: #13, #14.
Next step for #12: review, then commit + PR (github-commit-pr --issue 12).
I'll start #13 once #12 is committed.
```

**STOP HERE.** Do not commit, push, create a branch, or create a PR. The user decides what to do next. If they want to commit and open a PR, the `github-commit-pr` skill handles that workflow end-to-end — run it once per issue as `github-commit-pr --issue <N>`, so each issue gets its own branch, commit and pull request, with its own `Closes #N` link. Naming the issue matters when the tree still holds another issue's work: it tells that skill which paths to stage and which to leave for the next PR.

### Step 7: Move to the next issue

Once the current issue is landed (or the user has explicitly parked it), pick the next issue from the queue and go back to Step 1. Re-check `git status --porcelain` first: leftover changes mean the previous issue isn't really finished, and building on them is how two issues end up in one PR.

If the user asks you to start the next issue while the previous one is still uncommitted, say plainly what it costs — the two diffs mix and can only be separated by hand afterwards — and offer to commit the current work first. If they still want to continue, that's their call: proceed, and warn once that the resulting commit will span both issues.

## Error handling

| Scenario | Detection | Action |
|----------|-----------|--------|
| `gh` not installed | `command -v gh` fails | Direct user to https://cli.github.com |
| Not in a git repo | `git rev-parse` fails | Abort with clear message |
| Issue not found | `gh issue view` exits non-zero | Verify issue number and repo |
| Permission denied | `gh` returns 403/404 | Check repo access and auth scopes |
| Issue already closed | `state` field is `CLOSED` | Warn user, proceed only if confirmed |
| Issue from different repo | URL doesn't match current repo | Warn user, ask whether to proceed |
| Several issues requested at once | More than one issue number/URL in the input | Confirm the queue and order, implement only the first |
| Dirty tree from a previous issue | `git status --porcelain` non-empty at Step 1 | Show the changes, offer commit / stash before starting |
| Scope larger than expected | Discovered during planning/implementation | Pause, inform user, suggest splitting |
| Verification tools not found | Commands not available | Inform user, suggest manual verification |

## Critical constraints

These boundaries exist because this skill handles only the implementation phase — the user controls the git workflow:

- Implement one issue at a time, and never let two issues share a commit or a pull request — a PR is what a reviewer reads and what a revert undoes, so it should map to exactly one issue
- Do not fetch or start the next queued issue until the current one's changes have left the working tree — mixed diffs can't be split cleanly afterwards
- Do not commit after completing the implementation — the user needs to review the changes first and may want to adjust them
- Do not push to any remote — pushing is a separate decision that belongs to the user
- Do not create a PR automatically — PR creation involves title, description, and reviewer choices the user should make
- Do not create a branch — stay on the current branch; the user may have their own branching strategy or want to use `github-commit-pr` for this
- Do not modify files outside the scope of the issue — scope creep creates review burden and makes it harder to revert changes
- Ask for clarification rather than guessing when requirements are ambiguous — a wrong guess wastes more time than a quick question
- If implementation reveals unexpected complexity, pause and inform the user rather than expanding scope — they may want to split the work into multiple issues
