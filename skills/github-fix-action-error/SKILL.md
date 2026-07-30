---
name: github-fix-action-error
description: "Diagnose and fix the most recent failing GitHub Actions CI run on the current branch. Fetches the failing run's logs via the GitHub CLI, locates the root cause (failing test, compile error, lint violation, etc.), applies a targeted fix in the local working tree, and — only after user confirmation — commits and pushes. Use when someone says 'fix the CI', 'fix the failing action', 'the build is red', 'javítsd a CI hibát', 'piros a build', or pastes a failing Actions run URL for the current branch. Refuses to run on protected branches (main, master, develop)."
category: development-workflow
risk: medium
tags:
  - github
  - actions
  - ci
  - debugging
  - workflow
allowed-tools: Bash, Read, Grep, Glob, Edit, Write
---

# github-fix-action-error

## Purpose

Close the loop between a red CI run and a green one. The skill identifies the most recent failing GitHub Actions run on the current branch, pulls the logs, finds the underlying problem in the code, fixes it locally, and — after the user approves — commits and pushes the fix so CI can re-run.

## When to use

- User says "fix the CI", "fix the failing workflow", "make the build green", or the Hungarian equivalents ("javítsd a CI-t", "piros a build, nézd meg")
- User pastes a failing Actions run URL and wants it fixed
- User references a failing check and asks for a fix

## Prerequisites

Verify the environment before doing anything else:

1. **Inside a git repository**

```bash
git rev-parse --show-toplevel
```

If not, abort with a clear message.

2. **Clean-enough working tree**

```bash
git status --porcelain
```

If there are uncommitted changes, show them to the user and ask whether to proceed. Mixing the user's in-flight work with an automated fix makes the resulting commit hard to review — prefer to pause and let the user stash or commit first.

## Workflow

### Step 1: Safety check — branch

Get the current branch:

```bash
git rev-parse --abbrev-ref HEAD
```

If the branch is `main`, `master`, or `develop`, **refuse and stop** with a message like:

```
Refusing to run on protected branch '<name>'.
This skill commits and pushes a fix directly; that's unsafe on shared branches.
Switch to a feature branch (or open one from the failing commit) and try again.
```

Do not continue. Do not offer a "force" escape hatch — the whole point of the guard is that these branches should go through PR review.

### Step 2: Find the latest failing run

```bash
gh run list --branch "$BRANCH" --status failure --limit 1 \
  --json databaseId,displayTitle,workflowName,headSha,conclusion,createdAt
```

If the command returns an empty list, tell the user there are no failing runs on this branch and stop. It's worth checking for other non-success states too — a run may be `cancelled` or `timed_out` rather than `failure`. If nothing useful is found, stop.

Extract the `databaseId` as `RUN_ID`. Show the user a one-line summary so they know which run is being inspected:

```
Inspecting run <RUN_ID>: <workflowName> — "<displayTitle>" (sha <short-sha>)
```

### Step 3: Download and scan the logs

```bash
gh run view "$RUN_ID" --log
```

This can be large. Before fixing anything, narrow to the failing portion:

- `gh run view "$RUN_ID" --log-failed` returns only the failed steps' logs — prefer this when available
- Search for common failure markers: `FAIL`, `error:`, `Error:`, `✗`, `failed`, `AssertionError`, `Traceback`, `error TS`, `error[E`, `FAILED`, `npm ERR!`

Identify:

- **Which job/step failed** (workflow name, job name, step name)
- **The failure category** — test failure, compile/type error, lint/format violation, dependency install failure, script error, flaky infrastructure (network, runner), missing secret
- **The concrete signal** — test name, file path, line number, stack frame, rule name

If the failure looks like infrastructure flake (runner lost, network timeout, rate limit, missing secret) rather than a code defect, surface that to the user and suggest re-running the workflow (`gh run rerun <RUN_ID>`) instead of patching code. Do not invent a fix.

### Step 4: Locate the problem in the code

Map the log signal back to the repo:

- Test failure → open the test file, understand the assertion, then trace to the production code under test
- Compile/type error → open the reported file at the reported line
- Lint/format → open the file; if the tool can autofix (`eslint --fix`, `ruff --fix`, `cargo fmt`, `gofmt -w`, `./gradlew spotlessApply`), prefer running it over hand-editing
- Missing import / undefined symbol / failing build script → read surrounding code and recent commits (`git log -n 5 --oneline`) to understand what changed

If the log points at files that don't exist locally or the local commit differs from the one CI ran (`headSha` from Step 2 vs. `git rev-parse HEAD`), tell the user. Fixing against a different tree than CI ran against is unreliable.

### Step 5: Apply a focused fix

Make the smallest change that addresses the root cause:

- Do not reformat, rename, or refactor unrelated code
- Do not silence a real failure (e.g., deleting an assertion, adding a blanket try/except, disabling a lint rule file-wide, marking a test `skip`) unless the user explicitly asks for that. If the test is genuinely wrong, fix the test; if the production code is wrong, fix the code. Explain which and why.
- If the fix is non-obvious or has multiple plausible interpretations, pause and discuss with the user before editing

### Step 6: Verify locally when feasible

Before asking the user to approve a push, re-run the same check locally if it's cheap and available:

- Test failure → run the specific test file or test name
- Type error → `npx tsc --noEmit`, `cargo check`, `mypy`, `go build ./...`, etc.
- Lint → the same linter CI runs

If local verification passes, say so. If the check can't be reproduced locally (needs secrets, specific OS, large services), say that too and flag that CI is the real gate.

### Step 7: Summarize and ask for approval

Present a concise summary:

```
Failing run: <RUN_ID> — <workflowName> / <jobName> / <stepName>
Root cause: <one-sentence diagnosis>

Files changed:
- <path>  (<what changed, in a few words>)
- <path>  (<what changed, in a few words>)

Local verification: <passed | not runnable — reason>

Commit and push? [Y/n]
```

Wait for the user. Do not push without an explicit affirmative. Anything other than `y`/`Y`/`yes` (or the Hungarian `i`/`igen`) means stop — let the user iterate or take over.

### Step 8: Commit and push

On approval:

```bash
git add -- <files you actually edited>
git commit -m "<generated message>"
git push
```

Prefer `git add -- <path>` with the specific files; avoid `git add -A` / `git add .` to prevent sweeping in unrelated work. Do not amend. Do not force-push. Do not `--no-verify` — if a pre-commit hook fires, treat it the same as any other failure: fix the underlying issue and make a new commit.

**Commit message**: use a Conventional-Commits-flavored subject that names the fix, not the CI symptom. Match the repo's existing style if one is visible in `git log --oneline -n 20`.

Good examples:

- `fix(parser): handle trailing comma in object literal`
- `fix(ci): pin node to 20 to match lockfile`
- `test(user-service): correct expected timestamp format`

Poor examples (don't do these):

- `fix CI` — says nothing about what changed
- `fix failing test` — same
- `attempt 3` — noise

After pushing, report:

```
Pushed <short-sha> to origin/<branch>.
Watch the re-run with: gh run watch
```

Do not poll CI yourself unless the user asks — the push is the hand-off.

## Error handling

| Scenario | Detection | Action |
|----------|-----------|--------|
| `gh` not installed | `command -v gh` fails | Direct user to https://cli.github.com |
| Not in a git repo | `git rev-parse` fails | Abort with clear message |
| Protected branch | branch is main/master/develop | Refuse and stop (Step 1) |
| Dirty working tree | `git status --porcelain` non-empty | Show changes, ask whether to proceed |
| No failing runs | `gh run list` empty | Report "nothing to fix" and stop |
| Local HEAD ≠ CI sha | `headSha` vs. `git rev-parse HEAD` | Warn user; fixing against different tree is unreliable |
| Infrastructure flake | Log shows runner/network/secret issue, not code | Suggest `gh run rerun`, do not patch code |
| Ambiguous root cause | Multiple plausible fixes | Pause, ask user which interpretation is right |
| Can't reproduce locally | Needs secrets/services/OS | Note it explicitly in the summary; CI will be the real gate |
| Pre-commit hook fails | `git commit` non-zero | Fix the hook's complaint, create a new commit (never `--no-verify`) |
| Push rejected (non-fast-forward) | `git push` non-zero | Stop and tell the user; do not force-push |

## Critical constraints

These boundaries exist because this skill writes to shared history:

- Never run on `main`, `master`, or `develop` — no override
- Never push without explicit user approval in Step 7
- Never force-push, amend published commits, or skip hooks
- Never silence a failure (delete assertions, blanket-catch, skip tests, disable lint rules) as a shortcut; fix the real cause or hand back to the user
- Never include changes unrelated to the CI fix in the same commit — if you notice other issues, mention them separately and let the user decide
- Never invent a fix for an infrastructure flake; recommend a rerun instead
- Stop and ask whenever the diagnosis is ambiguous — a wrong guess costs more than a clarifying question
