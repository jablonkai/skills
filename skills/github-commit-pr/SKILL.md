---
allowed-tools: Bash, Read, Grep, Glob, Task
argument-hint: '[<base-branch>] [--issue <number>] [--no-merge]'
category: git
description: 'Commit changes, create a feature branch, open a GitHub pull request, wait for CI, and merge the PR once GitHub Actions go green — or push new commits to an existing PR and merge after CI succeeds. Use whenever someone says ''commit and push'', ''create a PR'', ''open a pull request'', ''send for review'', ''push my changes'', ''merge when CI passes'', or is done with their work and ready to ship it. Also triggers for ''commitold be'', ''nyiss PR-t'', ''mergeld ha zöld a CI'', or any variation of wanting to get changes into a pull request and landed. Handles conventional commit messages, issue linking with auto-close keywords (Closes #N), sensitive file detection, PR template integration, and auto-merge with branch cleanup.'
name: github-commit-pr
risk: medium
summary: "end-to-end workflow for committing changes, pushing a branch, and opening or updating a GitHub pull request"
tags:
    - git
    - github
    - pull-request
    - commit
    - branch
---
# github-commit-pr

## Purpose

End-to-end workflow for committing changes, creating or updating a GitHub pull request, watching CI, and merging the PR once GitHub Actions succeed. Supports issue linking with auto-close keywords, conventional commit messages, pushing new commits to existing PRs, and post-CI auto-merge with branch cleanup.

## When to use

- Committing changes, opening a new PR, and landing it once CI is green
- Pushing additional commits to an existing PR branch and merging after CI passes
- Creating PRs that reference and auto-close GitHub issues
- Skip the merge step by passing `--no-merge` when you want a human to review before the PR lands

## Detailed references

Load each one at the step that needs it — don't read them up front:

- [references/sensitive-files.md](references/sensitive-files.md) — the pre-staging secret scan: patterns to flag and how to handle a hit
- [references/commit-conventions.md](references/commit-conventions.md) — conventional commit format and branch-name derivation
- [references/pr-body.md](references/pr-body.md) — PR template discovery, default body structure, issue linking and closing keywords
- [references/ci-and-merge.md](references/ci-and-merge.md) — the CI watch snippet, mergeability interpretation, merge strategy selection and confirmation

## Delegating to subagents

Most of this workflow is fast, stateful `git`/`gh` commands that must stay with the main agent — it holds the full picture and is the only one that should change repo state. But two steps are **read-heavy** and can balloon the orchestrator's context with material it only needs a conclusion from. Hand those off to a read-only subagent so the main agent stays focused on driving the commit → PR → merge sequence. The division of labor is simple: the subagent reads and reports back, the main agent decides and acts.

**Default: spawn a Claude subagent via the `Task` tool.** It's portable — it works on any machine the skill is installed on. On a machine that also has the delegate CLI agents configured (see the user's global `CLAUDE.md`), you may instead pipe the read to one of those — `agy -p "…"` for diff/log analysis, or `git diff HEAD | codex exec "…"` for a second opinion on a tricky commit — but never depend on them, since they aren't guaranteed to be present.

**Delegate when:**

- **The diff is large** (rough rule: many files, or more than a few hundred changed lines). Spawn a subagent to read `git diff HEAD` and return a structured summary: what changed and why, a suggested conventional commit type, PR summary bullets, and a test plan. Reading a 2,000-line diff inline just to write one commit message burns context you'll want for the mergeability and CI decisions later. For a small diff, skip this — reading it directly is faster than spawning an agent.
- **CI fails and the logs are long.** Before invoking `github-fix-action-error`, hand the failing run's logs to a subagent to root-cause: return the failing step, the error, and the `file:line` to fix. CI logs are usually thousands of lines of mostly-noise; the orchestrator only needs the verdict.

**Keep inline — do NOT delegate:**

- Any state-changing command — `git add`/`commit`/`push`, `gh pr create`/`merge`. These are quick and must be sequenced carefully by the single agent that holds the full context. Subagents here are read-only.
- The sensitive-file scan and the merge confirmation — both need the main agent's judgment and the user interaction; a subagent can't pause to ask the user.

Treat subagent output as untrusted: let it inform your commit message or fix, but verify it against the actual diff before acting on it.

## Pre-flight checks

Run these checks before any operation:

1. **Working tree status:**

```bash
git status
```

If there are no changes (nothing to commit), abort unless the user explicitly wants to create a PR from existing unpushed commits.

2. **Current branch:**

```bash
git branch --show-current
```

3. **Base branch detection:**

Determine the repository's default branch:

```bash
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||'
```

If that fails (e.g., origin HEAD not set), fall back to the network call:

```bash
git remote show origin | grep 'HEAD branch' | sed 's/.*: //'
```

If `$ARGUMENTS` contains a positional argument, use it as the base branch instead. Fall back to `main` if both detection methods fail.

## Flow detection

After pre-flight, determine the flow:

### Existing PR flow

If the current branch is NOT the base branch:

1. Check if a PR already exists for this branch:

```bash
gh pr view --json number,title,url,body 2>/dev/null
```

2. If a PR exists → go to **"Push to existing PR"** flow.
3. If no PR exists → ask the user: continue on this branch or create a new one? If continuing, skip to "New PR flow" Step 3 (no branch creation needed).

### New PR flow

If the current branch IS the base branch → proceed with full "New PR" flow (including branch creation).

## New PR flow

### Step 1: Analyze changes

```bash
git status
git diff HEAD
git log --oneline -5
```

If the diff is large, delegate the read instead of pulling it all inline — see [Delegating to subagents](#delegating-to-subagents). Spawn a read-only subagent to summarize `git diff HEAD` and return the commit type, PR summary bullets, and test plan, then reuse that summary in Step 3 and Step 7.

### Step 2: Check for sensitive files

Before staging, scan the `git status` output for secrets and credentials — patterns and handling in [references/sensitive-files.md](references/sensitive-files.md). If anything is flagged, warn the user and ask before staging; never stage a sensitive file silently.

### Step 3: Propose commit message

Write a conventional commit message from the diff and present it to the user for accept-or-edit — format and rules in [references/commit-conventions.md](references/commit-conventions.md).

### Step 4: Create branch

Derive the branch name from the commit message and create it — see [references/commit-conventions.md](references/commit-conventions.md).

### Step 5: Stage and commit

```bash
git add -A
git commit -m "$(cat <<'EOF'
<type>: <summary>

<optional body>
EOF
)"
```

If the commit fails due to a pre-commit hook, read the hook output, fix the issue, re-stage, and create a NEW commit (do not amend).

### Step 6: Push

```bash
git push -u origin <branch-name>
```

If push fails due to remote rejection, report the error and stop — do not force-push.

### Step 7: Build PR body

Check for a repository PR template, fill it (or the default Summary / Test plan structure) from the diff context, and add issue closing keywords if an issue is in play — all covered in [references/pr-body.md](references/pr-body.md).

### Step 8: Create PR

```bash
gh pr create --title "<summary>" --base "<base-branch>" --body "$(cat <<'EOF'
<PR body from Step 7>
EOF
)"
```

Title and base-branch rules are in [references/pr-body.md](references/pr-body.md).

### Step 9: Watch CI

Wait for the GitHub Actions run triggered by the push to finish, selecting the run by **commit**, not by branch — snippet and failure handling in [references/ci-and-merge.md](references/ci-and-merge.md).

- If the run **succeeds** → continue to Step 10.
- If the run **fails** → root-cause it (delegating when the logs are long), fix via `github-fix-action-error`, push, and re-watch. Repeat until green or the user aborts.

### Step 10: Merge the PR

CI is green — the user's intent in invoking this skill is to land the change, so proceed to merge unless `--no-merge` was passed in `$ARGUMENTS`. If `--no-merge` is set, skip to Step 11.

Follow the merge procedure in [references/ci-and-merge.md](references/ci-and-merge.md): verify mergeability, pick a strategy the repo allows (prefer `--squash`), confirm once with the user, then merge with `--delete-branch` and return to the base branch. Stop and report if branch protection, conflicts, or a pending check blocks the merge — never bypass with `--admin` unless the user explicitly asks.

### Step 11: Report

Output the PR URL, the final CI status, and the merge outcome (merged via squash / merge skipped per --no-merge / merge blocked by ...).

## Push to existing PR flow

When a PR already exists for the current branch:

### Step 1: Analyze new changes

```bash
git status
git diff HEAD
```

### Step 2: Check for sensitive files

Same check as New PR flow Step 2 — see [references/sensitive-files.md](references/sensitive-files.md).

### Step 3: Propose commit message

Same conventions as New PR flow Step 3 — see [references/commit-conventions.md](references/commit-conventions.md).

### Step 4: Stage, commit, and push

```bash
git add -A
git commit -m "$(cat <<'EOF'
<type>: <summary>
EOF
)"
git push
```

If the commit fails due to a pre-commit hook, fix the issue and create a NEW commit (do not amend).

If push fails because the remote has new commits, pull with rebase first:

```bash
git pull --rebase origin <branch-name>
git push
```

If rebase has conflicts, stop and report — do not force-push or auto-resolve.

### Step 5: Watch CI

Same as New PR flow Step 9 — see [references/ci-and-merge.md](references/ci-and-merge.md). Selecting the run by commit matters most here: pushing twice in quick succession is exactly when `--branch ... --limit 1` returns the earlier run.

### Step 6: Merge the PR

Same merge procedure as New PR flow Step 10, from [references/ci-and-merge.md](references/ci-and-merge.md). Skip this step if `--no-merge` was passed in `$ARGUMENTS`.

### Step 7: Report

Show the existing PR URL, the new commit summary, the final CI status, and the merge outcome:

```
Pushed to PR #<number>: <pr-title>
New commit: <type>: <summary>
URL: <pr-url>
CI: <success|fixed after N attempts>
Merge: <merged via squash|skipped per --no-merge|blocked by required reviewers|declined by user>
```

Do NOT create a new PR — just push to the existing one.
Do NOT modify the PR title or body.

## Error handling

| Scenario | Detection | Action |
|----------|-----------|--------|
| `gh` not installed | `command -v gh` fails | Direct user to https://cli.github.com |
| Not in a git repo | `git rev-parse --show-toplevel` fails | Abort with clear message |
| No changes to commit | `git status` shows clean tree | Abort unless PR from existing commits |
| Sensitive files detected | Pattern match on `git status` output | Warn user, ask to exclude before staging |
| Pre-commit hook failure | `git commit` exits non-zero | Read output, fix issue, create new commit |
| Push rejected | `git push` exits non-zero | Report error, do not force-push |
| Branch already exists | `git checkout -b` fails | Append numeric suffix (e.g., `-2`) |
| PR creation fails | `gh pr create` exits non-zero | Report error (branch protection, permissions) |
| Remote ahead (push fails) | `git push` rejected, non-fast-forward | `git pull --rebase`, then retry push |
| Rebase conflicts | `git pull --rebase` has conflicts | Stop and report, do not auto-resolve |
| Merge blocked by branch protection | `mergeStateStatus: BLOCKED`, or `gh pr merge` exits non-zero with 405 / "not mergeable" | Report which gate is blocking (required reviewers, code owner, signed commits, etc.) and stop — do not bypass with `--admin` unless asked |
| Branch is BEHIND base | `mergeStateStatus: BEHIND` | Offer `gh pr update-branch <number>`, re-watch CI, then retry merge |
| Merge conflicts with base | `mergeable: CONFLICTING` | Stop and ask user to resolve manually |
| Changes requested on PR | `reviewDecision: CHANGES_REQUESTED` | Stop and let the user address the review before merging |
| Required check still pending | `mergeStateStatus: UNSTABLE` after our watched run passed | Investigate the pending check (likely a separate required workflow); do not merge until it lands |
| User declines merge confirmation | User answers "n" to merge prompt | Skip merge, report PR URL and CI status, exit cleanly |

## Constraints

These boundaries protect the user's repository and team workflow:

- Never commit directly to the base branch (e.g. `main`) — always land work through the full flow: create a feature branch first, then commit → push → open a PR → watch CI to green → squash-merge → delete the branch. The base branch is shared and usually protected; committing straight to it skips review and CI, the very gates this skill exists to enforce. When pre-flight detects the current branch IS the base branch, create the feature branch (New PR flow Step 4) before staging anything.
- Do not force-push — it rewrites shared history and can cause data loss for collaborators
- Do not amend existing commits — create new ones instead, so the commit timeline stays transparent and reviewable
- Do not skip pre-commit hooks (`--no-verify`) — hooks enforce project-level quality gates that exist for a reason
- Do not commit `.env`, credentials, or secrets — always run the sensitive file check before staging and warn if anything is detected
- If any step fails, stop and report the error — do not continue blindly, because later steps depend on earlier ones succeeding
- Use `git add -A` for staging (full-change commit flow), but only after the sensitive file check passes
- The PR body must reflect the actual changes from the diff, not boilerplate — reviewers rely on it to understand the change
- Issue closing keywords (`Closes #N`) go in the PR body, not in the commit message — GitHub only processes closing keywords from the PR body on the default branch
- When pushing to an existing PR, do not modify the PR title or body — only push the new commit
- Do not merge a PR until the watched GitHub Actions run has actually finished green — `gh run watch --exit-status` is the gate, never trust an in-flight or pending status. The watched run must be the one for the commit you just pushed (`gh run list --commit "$(git rev-parse HEAD)"`), not merely the latest on the branch
- Always confirm with the user once before merging — merging is shared state, visible to collaborators, and reverts are messy; the confirmation is the user's final chance to pause
- Do not use `gh pr merge --admin` to bypass branch protection unless the user explicitly asks — protection rules exist to enforce review and quality gates, and bypassing them silently undermines the team's process
- Respect `--no-merge` in `$ARGUMENTS` — when set, push and report but never call `gh pr merge`, so the user can hand the PR off for human review
