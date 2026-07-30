---
allowed-tools: Bash, Read, Grep, Glob, Task
argument-hint: '[<base-branch>] [--issue <number>] [--no-merge]'
category: git
description: 'Commit changes, create a feature branch, open a GitHub pull request, wait for CI, and merge the PR once GitHub Actions go green — or push new commits to an existing PR and merge after CI succeeds. Use whenever someone says ''commit and push'', ''create a PR'', ''open a pull request'', ''send for review'', ''push my changes'', ''merge when CI passes'', or is done with their work and ready to ship it. Also triggers for ''commitold be'', ''nyiss PR-t'', ''mergeld ha zöld a CI'', or any variation of wanting to get changes into a pull request and landed. Handles conventional commit messages, issue linking with auto-close keywords (Closes #N), sensitive file detection, PR template integration, and auto-merge with branch cleanup.'
metadata:
    github-path: skills/github-commit-pr
    github-ref: refs/heads/main
    github-repo: https://github.com/jablonkai/agent-tools
    github-tree-sha: 225890dce3e11154c2039fcfb720ca904827ce86
name: github-commit-pr
risk: low
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

Before staging, scan `git status` output for potentially sensitive files:

- `.env`, `.env.*` files
- Files containing `secret`, `credential`, `token`, `password`, `key` in their name
- `id_rsa`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.p8`, `*.keystore` files
- `*.json` files that look like service account keys (e.g., `*-credentials.json`, `serviceaccount*.json`)

If any are detected, **warn the user explicitly** and ask whether to exclude them. Do NOT silently stage sensitive files.

### Step 3: Propose commit message

Write a conventional commit message based on the diff:

- **Format:** `<type>: <short summary>`
- **Types:** `feat`, `fix`, `refactor`, `docs`, `style`, `chore`, `test`, `ci`
- **Summary:** imperative mood, lowercase, no period, max 72 chars
- Add a body (blank line + wrapped paragraphs) for complex changes

Present the proposed message to the user:
1. **Accept** — use as-is
2. **Edit** — user provides their own

### Step 4: Create branch

Derive a branch name from the commit message:

1. Take the summary part (after `type: ` or `type(scope): `)
2. Lowercase, replace spaces with hyphens, remove special characters (including parentheses from scoped types)
3. Prefix with the type: `feat/add-dark-mode`, `fix/null-token-settings`
4. Truncate to 60 characters max

**Example:** `feat(auth): implement JWT tokens` → `feat/implement-jwt-tokens`

```bash
git checkout -b <branch-name>
```

If the branch already exists, append a numeric suffix (e.g., `-2`).

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

Check if the repository has a PR template:

```bash
cat .github/PULL_REQUEST_TEMPLATE.md 2>/dev/null || \
  cat .github/pull_request_template.md 2>/dev/null || \
  cat PULL_REQUEST_TEMPLATE.md 2>/dev/null || \
  cat docs/PULL_REQUEST_TEMPLATE.md 2>/dev/null
```

If a template exists, use its structure and fill in the sections from the diff context. If no template exists, use this default structure:

```markdown
## Summary
<1-3 bullet points describing the actual changes from the diff>

## Test plan
<bulleted checklist of testing steps>
```

#### Issue linking

If `$ARGUMENTS` contains `--issue <number>`, or the user mentions an issue number, or the branch name contains an issue number:

1. Fetch the issue details:

```bash
gh issue view <number> --json title,body,labels
```

2. Add a closing keyword to the PR body at the end of the Summary section:

```markdown
## Summary
- <change description>
- <change description>

Closes #<number>
```

**Valid closing keywords** (all work the same): `Closes`, `Fixes`, `Resolves`. Use `Closes` by default. For bug fixes (commit type `fix`), use `Fixes` instead.

3. If the issue has labels, apply matching labels to the PR after creation:

```bash
gh pr edit <pr-number> --add-label "<label1>,<label2>"
```

### Step 8: Create PR

```bash
gh pr create --title "<summary>" --base "<base-branch>" --body "$(cat <<'EOF'
<PR body from Step 7>
EOF
)"
```

- **Title:** first line of commit summary without the `type:` prefix, max 70 chars
- **Base branch:** detected in pre-flight or from `$ARGUMENTS`

### Step 9: Watch CI

After the PR is created, wait for the GitHub Actions run triggered by the push to finish:

```bash
gh run watch $(gh run list --branch <branch-name> --limit 1 --json databaseId --jq '.[0].databaseId') --exit-status
```

- `--exit-status` makes the command exit non-zero when the run fails, so failure is easy to detect.
- If no run is found yet, retry after a short delay (CI may not have registered the push immediately).
- If the run **succeeds** → continue to Step 10.
- If the run **fails** → when the logs are long, first delegate root-causing to a read-only subagent (see [Delegating to subagents](#delegating-to-subagents)) and pass its conclusion — failing step, error, and `file:line` — into the `github-fix-action-error` skill; otherwise invoke that skill directly. After the fix is committed and pushed, re-watch the new run. Repeat until the build is green or the user aborts.

### Step 10: Merge the PR

CI is green — the user's intent in invoking this skill is to land the change, so proceed to merge unless `--no-merge` was passed in `$ARGUMENTS`. If `--no-merge` is set, skip to Step 11.

Merging is a shared-state action visible to collaborators, and it's effectively irreversible (revert PRs are possible but messy), so confirm with the user once before doing it — keep the prompt short, since they already opted in by invoking this skill.

#### Step 10a: Verify mergeability

```bash
gh pr view --json number,mergeable,mergeStateStatus,reviewDecision
```

Interpret the result:

- `mergeable: MERGEABLE` and `mergeStateStatus: CLEAN` → ready to merge
- `mergeStateStatus: HAS_HOOKS` → ready (post-merge hooks will run, that's fine)
- `mergeStateStatus: BLOCKED` → branch protection blocks the merge (e.g., required reviewers, required signed commits, code owner review). Report which gate is blocking and stop — do not bypass with `--admin` unless the user explicitly asks
- `mergeStateStatus: BEHIND` → base branch moved forward and the repo requires an up-to-date branch. Offer `gh pr update-branch <number>` and re-watch CI afterward
- `mergeable: CONFLICTING` → conflicts with the base branch. Stop and ask the user to resolve manually
- `mergeStateStatus: UNSTABLE` → required checks haven't completed even though our watched run passed. Investigate which check is pending before merging
- `reviewDecision: CHANGES_REQUESTED` → at least one reviewer has requested changes. Stop and let the user address the review

#### Step 10b: Choose a merge strategy

Read the repo's allowed strategies so the chosen flag will actually work:

```bash
gh repo view --json mergeCommitAllowed,squashMergeAllowed,rebaseMergeAllowed
```

Preference order: `--squash` (cleanest history for feature PRs), then `--merge`, then `--rebase`. Pick the first one that's allowed. The skill exists to land PRs cleanly, so squash is the right default — but never pick a strategy the repo doesn't permit, or `gh pr merge` will reject it.

#### Step 10c: Confirm and merge

Tell the user concisely what you're about to do and ask once for confirmation:

> "CI is green. Merge PR #<number> with `--squash` and delete the branch? (y/n)"

If the user declines, skip to Step 11 and just report. If they confirm:

```bash
gh pr merge <number> --<strategy> --delete-branch
```

Notes:

- `--delete-branch` removes both the local and remote branch after merge — this is the usual cleanup, but skip the flag if the user objects.
- If the merge command fails because of branch protection (e.g., 405 method not allowed, "Pull Request is not mergeable"), surface the error and stop. Do not retry with `--admin` unless explicitly asked.
- If `gh pr merge` succeeds, the local branch is gone; subsequent `git` commands should not assume it still exists. Switch back to the base branch and pull:

```bash
git checkout <base-branch>
git pull
```

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

Same check as New PR flow Step 2.

### Step 3: Propose commit message

Same conventions as New PR flow Step 3.

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

After pushing, wait for the GitHub Actions run triggered by the new commit to finish:

```bash
gh run watch $(gh run list --branch "$(git branch --show-current)" --limit 1 --json databaseId --jq '.[0].databaseId') --exit-status
```

- `--exit-status` makes the command exit non-zero when the run fails.
- If the run **succeeds** → continue to Step 6.
- If the run **fails** → when the logs are long, first delegate root-causing to a read-only subagent (see [Delegating to subagents](#delegating-to-subagents)) and pass its conclusion — failing step, error, and `file:line` — into the `github-fix-action-error` skill; otherwise invoke that skill directly. After the fix is committed and pushed, re-watch the new run. Repeat until the build is green or the user aborts.

### Step 6: Merge the PR

Same flow as **New PR flow → Step 10**. Skip this step if `--no-merge` was passed in `$ARGUMENTS`.

1. Verify mergeability with `gh pr view --json mergeable,mergeStateStatus,reviewDecision` — only proceed when the PR is `MERGEABLE` and `CLEAN` (or `HAS_HOOKS`). Stop on `BLOCKED`, `BEHIND`, `CONFLICTING`, `UNSTABLE`, or `CHANGES_REQUESTED`.
2. Pick a strategy allowed by the repo (`gh repo view --json mergeCommitAllowed,squashMergeAllowed,rebaseMergeAllowed`). Prefer `--squash` → `--merge` → `--rebase`.
3. Ask the user once: "CI is green. Merge PR #<number> with `--squash` and delete the branch? (y/n)"
4. On confirmation: `gh pr merge <number> --<strategy> --delete-branch`, then `git checkout <base-branch> && git pull`.
5. If branch protection blocks the merge, report the gate and stop — do not use `--admin` unless the user explicitly asks.

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
- Do not merge a PR until the watched GitHub Actions run has actually finished green — `gh run watch --exit-status` is the gate, never trust an in-flight or pending status
- Always confirm with the user once before merging — merging is shared state, visible to collaborators, and reverts are messy; the confirmation is the user's final chance to pause
- Do not use `gh pr merge --admin` to bypass branch protection unless the user explicitly asks — protection rules exist to enforce review and quality gates, and bypassing them silently undermines the team's process
- Respect `--no-merge` in `$ARGUMENTS` — when set, push and report but never call `gh pr merge`, so the user can hand the PR off for human review
