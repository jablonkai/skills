---
name: github-fix-action-error
description: "Diagnose and fix the most recent failing GitHub Actions CI run on the current branch. Fetches the failing run's logs via the GitHub CLI, locates the root cause (failing test, compile error, lint violation, broken workflow file, etc.), applies a targeted fix in the local working tree, and — only after user confirmation — commits and pushes. Recognizes infrastructure flakes and already-fixed failures instead of patching code. Use when someone says 'fix the CI', 'fix the failing action', 'the build is red', 'why did the workflow fail', 'javítsd a CI hibát', 'piros a build', or pastes a failing Actions run URL for the current branch. Refuses to run on protected branches (main, master, develop, or the repo's default branch). Not for opening or merging PRs — use github-commit-pr for that."
summary: "diagnose the latest failing GitHub Actions run on the current branch, apply a targeted fix locally, and — after user approval — commit and push; refuses to run on main/master/develop or the default branch"
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

Close the loop between a red CI run and a green one. The skill identifies the most recent failing GitHub Actions run on the current branch, pulls the relevant part of its logs, finds the underlying problem in the code, fixes it locally, and — after the user approves — commits and pushes the fix so CI can re-run.

## Prerequisites

Verify the environment before doing anything else:

```bash
git rev-parse --show-toplevel   # inside a git repo?
gh auth status                  # gh installed and logged in?
git status --porcelain          # clean-enough working tree?
```

- Not a repo, `gh` missing (point to https://cli.github.com) or not authenticated (`gh auth login`) → stop with a clear message.
- Uncommitted changes → show them and ask whether to proceed. Mixing the user's in-flight work with an automated fix makes the resulting commit hard to review — prefer to pause and let the user stash or commit first.

## Workflow

### Step 1: Safety check — branch

```bash
BRANCH=$(git branch --show-current)
DEFAULT=$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name)
```

- Empty `BRANCH` means a detached HEAD — stop and ask the user to check out the branch CI ran on.
- If `BRANCH` is `main`, `master`, `develop`, or equal to `DEFAULT` (repos name it `trunk`, `production`, …), **refuse and stop**:

```
Refusing to run on protected branch '<name>'.
This skill commits and pushes a fix directly; that's unsafe on shared branches.
Switch to a feature branch (or open one from the failing commit) and try again.
```

Do not offer a "force" escape hatch — these branches should go through PR review. Offering to create a fix branch for the user is fine; it doesn't bypass anything.

### Step 2: Find the failing run — and make sure it's still relevant

If the user pasted a run URL (`…/actions/runs/<RUN_ID>[/job/<JOB_ID>]`), take `RUN_ID` from it and confirm with `gh run view "$RUN_ID" --json headBranch,headSha,conclusion,workflowName` that it belongs to `BRANCH`. If it's from another branch, say so and stop — fixing it here would push to the wrong place.

Otherwise list recent runs rather than only failures, because "the most recent failure" is often already stale:

```bash
gh run list --branch "$BRANCH" --limit 20 \
  --json databaseId,workflowName,displayTitle,headSha,status,conclusion,createdAt,url
```

Runs come newest first. For each workflow, look at its **newest** run:

- `success` → that workflow is already green; older failures of it are not something to fix. If every workflow's newest run is green, report "nothing to fix — the latest runs pass" and stop.
- `in_progress` / `queued` on the current HEAD → a fix may already be under test; tell the user and suggest `gh run watch <id>` instead of patching blind.
- `failure`, `timed_out`, `startup_failure` → candidate. `cancelled` is usually a superseded or manually stopped run, not a code defect — mention it but don't treat it as one.

If nothing is red, stop. Otherwise take the newest candidate as `RUN_ID` (if several workflows are red, handle each in turn) and show a one-line summary:

```
Inspecting run <RUN_ID>: <workflowName> — "<displayTitle>" (sha <short-sha>)
```

### Step 3: Read the failure — narrowly

Find what failed first, then pull only that log. Full `--log` output of a CI run is routinely thousands of lines and buries the signal:

```bash
gh run view "$RUN_ID"                       # jobs, failed steps, annotations (lint/compiler annotations often name file:line)
gh run view "$RUN_ID" --log-failed | tail -n 200
```

Grep the failed log instead of reading it whole when it is still long: `FAIL`, `error:`, `Error:`, `✗`, `AssertionError`, `Traceback`, `error TS`, `error[E`, `FAILED`, `npm ERR!`, `##[error]`. Use `--job <JOB_ID>` to focus on one job.

Special cases:

- `startup_failure`, or a run with no jobs → the workflow file itself is invalid (YAML error, unknown action/input, bad `uses:` ref). There are no logs; the annotation or the run page names the problem, and the fix goes in `.github/workflows/`.
- "log not found" → logs expired or were deleted; ask the user to re-run, then diagnose the fresh run.
- Several failed jobs → check whether they share one root cause (typically: one compile error breaks every matrix leg). Different causes → fix them one at a time and say so.

Identify the failing job/step, the **category** (test failure, compile/type error, lint/format, dependency install, script error, workflow config, infrastructure) and the **concrete signal** (test name, file:line, stack frame, rule id).

If it is an infrastructure flake — runner lost, network timeout / `ECONNRESET` / 5xx from a registry, rate limit, GitHub outage, billing or spending-limit refusal, missing secret on a fork PR — tell the user and suggest `gh run rerun "$RUN_ID" --failed` instead of patching code. Don't rerun it yourself unless asked, and don't invent a code fix for a problem that isn't in the code.

### Step 4: Locate the problem in the code

Compare the tree CI ran with the local one first:

```bash
git fetch --quiet && git rev-parse HEAD "@{u}"   # vs. headSha from Step 2
```

- Local **behind** the upstream → `git pull --ff-only` before editing, or the fix lands on a stale tree.
- Local **ahead** (unpushed commits) → they may already fix the failure; check. Either way the Step 8 push will carry them too — say so in the summary.
- Log names files that don't exist locally → tell the user; fixing against a different tree than CI ran is unreliable.

Then map the signal back to the repo:

- Test failure → open the test, understand the assertion, trace to the production code under test. Decide which side is wrong before editing.
- Compile/type error → the reported file at the reported line.
- Lint/format → if the tool autofixes (`eslint --fix`, `ruff check --fix`, `cargo fmt`, `gofmt -w`, `./gradlew spotlessApply`, `dart format`), run it on the affected files rather than hand-editing.
- Environment mismatch (passes locally, fails in CI: timezone, locale, OS, tool version) → read the workflow file; the fix may belong in the code (don't depend on local TZ) or in the workflow (pin the version).
- Anything else → read surrounding code and recent commits (`git log -n 5 --oneline`) to see what changed.

### Step 5: Apply a focused fix

Make the smallest change that addresses the root cause:

- Do not reformat, rename, or refactor unrelated code.
- Do not silence a real failure — deleting an assertion, blanket try/except, disabling a lint rule file-wide, marking a test skipped, adding `continue-on-error`, or loosening a check in the workflow — unless the user explicitly asks. If the test is wrong, fix the test; if the code is wrong, fix the code. Say which and why.
- If the fix is non-obvious or has several plausible interpretations, pause and discuss before editing.

### Step 6: Verify locally when feasible

Re-run the check CI ran — read the failing step's `run:` line in the workflow to get the exact command:

- Test failure → the specific test file or test name, then the full suite step if cheap
- Type/compile error → `npx tsc --noEmit`, `cargo check`, `mypy`, `go build ./...`, `./gradlew compileKotlin`, …
- Lint → the same linter with the same config CI uses

Report the result. If the check can't run locally (secrets, OS, services), say so and flag that CI is the real gate.

### Step 7: Summarize and ask for approval

```
Failing run: <RUN_ID> — <workflowName> / <jobName> / <stepName>
Root cause: <one-sentence diagnosis>

Files changed:
- <path>  (<what changed, in a few words>)

Local verification: <passed | not runnable — reason>
Also pushed: <unpushed local commits, if any — otherwise omit>

Commit and push? [y/N]
```

Wait for the user. Only an explicit yes (`y`, `yes`, `i`, `igen`, "go ahead", …) counts; anything else means stop and let the user iterate or take over. If the original request already pre-approved committing and pushing ("fix it and push", "előre jóváhagyom"), that counts as the yes — still print the summary, then continue.

### Step 8: Commit and push

```bash
git add -- <files you actually edited>
git commit -m "<generated message>"
git push            # branch already has an upstream: CI ran on it
```

Stage only the specific files — never `git add -A` / `git add .`. Do not amend, force-push, or use `--no-verify`: if a pre-commit hook fails, fix what it reports and commit again. A non-fast-forward rejection means someone else pushed — stop and tell the user rather than rebasing on your own.

**Commit message**: a Conventional-Commits subject that names the fix, not the CI symptom; match the repo's style (`git log --oneline -n 20`).

- Good: `fix(parser): handle trailing comma in object literal`, `fix(ci): pin node to 20 to match lockfile`, `test(user-service): correct expected timestamp format`
- Poor: `fix CI`, `fix failing test`, `attempt 3`

Then report:

```
Pushed <short-sha> to origin/<branch>.
Watch the re-run with: gh run watch
```

Don't poll CI unless the user asks — the push is the hand-off.

## Error handling

| Scenario | Detection | Action |
|----------|-----------|--------|
| `gh` missing / not logged in | `gh auth status` fails | Point to https://cli.github.com or `gh auth login`; stop |
| Not in a git repo | `git rev-parse` fails | Abort with clear message |
| Detached HEAD | `git branch --show-current` empty | Ask the user to check out the branch |
| Protected branch | main/master/develop or repo default | Refuse and stop (Step 1) |
| Dirty working tree | `git status --porcelain` non-empty | Show changes, ask whether to proceed |
| No failing runs / already green | newest run per workflow is `success` | Report "nothing to fix" and stop |
| Run still in progress | newest run `in_progress`/`queued` | Suggest `gh run watch`; don't patch blind |
| Pasted run from another branch | `headBranch` ≠ current branch | Say so and stop |
| Invalid workflow file | `startup_failure`, no jobs | Fix the YAML in `.github/workflows/` |
| Logs expired | `--log-failed` returns not found | Ask to re-run, diagnose the fresh run |
| Local HEAD ≠ CI sha | `headSha` vs. `HEAD` / `@{u}` | Pull if behind; flag unpushed commits if ahead |
| Infrastructure flake | runner/network/billing/secret, not code | Suggest `gh run rerun --failed`; do not patch code |
| Ambiguous root cause | Multiple plausible fixes | Pause, ask which interpretation is right |
| Can't reproduce locally | Needs secrets/services/OS | Note it in the summary; CI is the real gate |
| Pre-commit hook fails | `git commit` non-zero | Fix the complaint, new commit (never `--no-verify`) |
| Push rejected (non-fast-forward) | `git push` non-zero | Stop and tell the user; do not force-push |

## Critical constraints

These boundaries exist because this skill writes to shared history:

- Never run on `main`, `master`, `develop` or the default branch — no override
- Never push without explicit user approval (Step 7)
- Never force-push, amend published commits, or skip hooks
- Never silence a failure (delete assertions, blanket-catch, skip tests, disable lint rules, `continue-on-error`) as a shortcut
- Never include changes unrelated to the CI fix in the same commit — mention other issues separately
- Never patch code for an infrastructure flake or an already-green workflow
- Stop and ask whenever the diagnosis is ambiguous — a wrong guess costs more than a clarifying question
