---
name: github-do-issue
description: "Fetch GitHub issues, understand their requirements, plan and implement the solution, then run verification — without committing, pushing, or creating a PR. Works one issue at a time: when several issues are named, or when no issue number is given at all (then it takes every open issue of the current repo as the queue), implement them sequentially so each one lands as its own commit and its own pull request, never bundled together. Use when someone says 'work on issue #N', 'do #N', 'implement #N', 'fix issue #N', 'work through the open issues', 'do all the issues', 'dolgozz a #N-es issue-n', 'csináld meg a #12, #13 és #14 issue-kat', 'csináld meg az összes issue-t', or pastes one or more GitHub issue URLs and wants them implemented. Not for creating, labeling or triaging issues (github-issues) or for committing and opening the PR (github-commit-pr, which runs once per issue afterwards). The user always reviews each issue's result and decides when to commit."
summary: "fetch GitHub issues — the named ones, or every open one when none is named — and implement them one at a time, each reviewed, committed and shipped as its own PR"
category: development-workflow
risk: low
tags:
  - github
  - issues
  - development
  - workflow
allowed-tools: Bash, Read, Grep, Glob, Edit, Write
argument-hint: "[<issue-number-or-url> ...]  (none = all open issues)"
---

# github-do-issue

## Purpose

Structured workflow for implementing GitHub issues in any project. For each issue: fetch it, understand the requirements, plan the approach, implement, verify — then stop and let the user review before any git operation happens.

## Which issues: the queue

Work out the queue from `$ARGUMENTS` before anything else:

| Input | Queue |
|-------|-------|
| `42`, `#42` | that issue |
| `https://github.com/owner/repo/issues/42` | that issue; note `owner/repo` (see Step 1) |
| several numbers / URLs | those issues, in the order given |
| nothing, or "all" / "the open issues" / "az összes issue" | **every open issue of the current repo** — see [Backlog mode](#backlog-mode-no-issue-given) |

A single issue is simply a queue of one. Either way the rule below holds.

## One issue, one commit, one PR

Each issue is a self-contained unit of work all the way through: its own implementation, its own review, its own commit, its own branch, its own pull request. Five issues named in one sentence — or fifteen found in the backlog — are five (or fifteen) runs of this workflow, not one run covering all of them.

A pull request is the unit people review, discuss, revert and link back to an issue. A PR that closes three issues can't be reviewed or reverted in pieces, and forces a reviewer who cares about one of them to read all three. Interleaving the implementations is worse: once two issues' edits are mixed in the working tree, they can only be split into clean commits by picking the diff apart by hand.

So when the queue holds more than one issue:

1. Confirm the queue and the order with the user before touching any code:

```
I'll do these one at a time, each with its own commit and PR:
1. #12 — <title>
2. #13 — <title>
3. #14 — <title>

Starting with #12. Order OK?
```

If one issue builds on another, say so and propose that order. Otherwise keep the given order (backlog mode has its own default, below).

2. Run Steps 1–6 for the first issue only.
3. Stop and let the user review and land it (`github-commit-pr --issue <N>` handles commit → branch → PR for that one issue; `--issue` keeps its staging and its `Closes #N` scoped to this issue alone).
4. Only once that issue's changes have left the working tree — committed, or explicitly set aside by the user — start Step 1 for the next issue.

The queue is a list of numbers and titles, nothing more. Don't fetch every issue's full body and plan them together: keeping only the current issue in view is what keeps its diff clean and reviewable.

## Backlog mode (no issue given)

When no issue is named, the user wants the repo's open issues worked through. List them — titles and metadata only, not bodies:

```bash
gh issue list --state open --limit 200 \
  --json number,title,labels,assignees,createdAt,blockedBy,closedByPullRequestsReferences
```

(`--limit` defaults to 30 and would silently truncate a larger backlog. If exactly 200 come back, say the list may be incomplete.)

Build the queue from that list:

- **Order:** oldest first (ascending number), except that an issue listed in another's `blockedBy` goes before it, and issues labeled as bugs or with an explicit priority label may be moved forward — say why when you reorder.
- **Set aside, don't silently drop**, and show them in a separate list so the user can pull any back in:
  - issues that already have a linked PR (`closedByPullRequestsReferences` non-empty) — someone is on it;
  - issues assigned to someone other than the current user (`gh api user --jq .login`);
  - issues that aren't implementation work — labels like `question`, `discussion`, `duplicate`, `wontfix`, `invalid`, or an epic/tracking issue whose sub-issues are in the list anyway.
- If nothing is left, say so and stop. If the queue is long (more than ~10), show it all but suggest the user trims it or picks a label/milestone to focus on — each item costs a review round.

Then present both lists and confirm, exactly as for a named queue:

```
14 open issues. Queue (one commit + PR each):
1. #3  — <title>   [bug]
2. #5  — <title>
3. #9  — <title>   (blocks #11)
...
Set aside: #7 (open PR #40), #8 (assigned to @alice), #10 (question)

Starting with #3. Order OK?
```

From here it is the ordinary one-at-a-time loop. Re-list open issues before starting each next one — an issue may have been closed or picked up in the meantime.

## Prerequisites

1. **Tooling and repo:**

```bash
command -v gh && gh auth status && git rev-parse --show-toplevel
```

If `gh` is missing, point to https://cli.github.com; if not authenticated, ask the user to run `gh auth login`; if not in a git repository, abort with a clear message.

2. **Clean starting point:**

```bash
git status --porcelain
```

Uncommitted changes are not automatically a problem — but if they are the *previous* issue's work, starting the next one on top of them is how two issues end up in one commit. If the tree is dirty, show the user what's there and ask whether to commit it first (via `github-commit-pr --issue <N>` for the issue that work belongs to), stash it, or continue on purpose.

## Workflow

Run these steps for **one** issue at a time.

### Step 1: Fetch the issue

Take the first issue from the queue. For a URL, extract the number and `owner/repo`; if that repo differs from the current one, warn the user and ask whether to proceed (the implementation happens in the current repo, the issue context comes from the other one).

```bash
gh issue view "$ISSUE_NUMBER" ${ISSUE_REPO:+--repo "$ISSUE_REPO"} --json number,title,body,labels,assignees,milestone,state,comments
```

`ISSUE_REPO` is set to `owner/repo` only when a URL pointed to a different repository; otherwise `gh` defaults to the current one. If the command fails (not found, permission denied), report the error — in a queue, ask whether to skip to the next issue — and otherwise stop.

If the issue is already closed, warn the user and proceed only if they confirm.

Show a summary, including comments — they often carry clarifications, decisions or changed requirements:

```
Issue #42: <title>
State: open | Labels: enhancement
---
<issue body, trimmed to key requirements>
<key points from comments, if any>
```

### Step 2: Understand requirements

Extract from the body and comments:

- **What needs to change** — the feature, fix, or improvement
- **Acceptance criteria** — checkboxes or explicit requirements
- **Scope boundaries** — what is NOT in scope (if mentioned)
- **Related context** — linked issues, mentioned files, referenced PRs

Where comments contradict the body, the latest agreed comment wins. If the issue is unclear or missing critical details, ask before proceeding.

### Step 3: Plan the approach

Before writing any code:

1. Read the project's conventions — README.md, CLAUDE.md, AGENTS.md, CONTRIBUTING.md or similar, config files, and the existing code around the change.
2. Identify which files need to be created or modified.
3. Find the existing tests covering the affected code — the change should extend coverage, not break it.
4. Present a brief plan:

```
Implementation plan for #42:
1. <specific change>
2. <specific change>
3. <specific change>
```

If the plan shows the issue is larger than expected, say so and suggest splitting it. Wait for the user to approve or adjust the plan.

### Step 4: Implement

- Follow the conventions found in Step 3.
- Implement what the latest comment thread agreed on, not just the opening description.
- Change only what the issue requires. If the project uses i18n, add translation keys for new user-visible strings.
- If a sub-task turns out more complex than planned, pause and tell the user rather than expanding scope silently.
- Touch nothing that belongs to another queued issue, even if the fix is one line away and you'll be back for it in ten minutes. That line belongs in the other issue's commit, where a reviewer can connect it to the issue that asked for it. Note it and move on.

### Step 5: Verify

Run the project's own checks. Prefer what CI runs (`.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `.circleci/`) and what `package.json` scripts, `Makefile` or project docs name — those are what the PR must pass. Typical commands by stack:

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

Run at minimum the compiler / type checker and the tests touching the change, and fix failures before reporting. Filter long output for the relevant lines rather than pasting whole logs. If no verification command exists, say so and suggest manual checks.

### Step 6: Report and stop

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

When more issues are queued, end by naming what's left and what has to happen first:

```
Remaining: #13, #14.
Next step for #12: review, then commit + PR (github-commit-pr --issue 12).
I'll start #13 once #12 is committed.
```

**STOP HERE.** Do not commit, push, create a branch, or create a PR. The user decides what happens next. If they want to ship it, `github-commit-pr --issue <N>` does commit → branch → PR for that one issue with its own `Closes #N` — naming the issue tells that skill which paths to stage when the tree holds anything else.

### Step 7: Move to the next issue

Once the current issue is landed (or the user has explicitly parked it), re-check `git status --porcelain` — leftover changes mean the previous issue isn't really finished — then take the next issue from the queue and go back to Step 1. In backlog mode, re-list the open issues first and drop any that were closed or picked up meanwhile.

If the user asks to start the next issue while the previous one is still uncommitted, say plainly what it costs — the two diffs mix and can only be separated by hand — and offer to commit the current work first. If they still want to continue, that's their call: proceed, and warn once that the resulting commit will span both issues.

## Error handling

| Scenario | Detection | Action |
|----------|-----------|--------|
| `gh` not installed / not logged in | `command -v gh` / `gh auth status` fails | Point to https://cli.github.com or `gh auth login` |
| Not in a git repo | `git rev-parse` fails | Abort with clear message |
| Issue not found / no access | `gh issue view` non-zero, 403/404 | Report; in a queue, offer to skip it |
| Issue already closed | `state` is `CLOSED` | Warn, proceed only if confirmed |
| Issue from a different repo | URL doesn't match current repo | Warn, ask whether to proceed |
| Several issues, or none named | Queue longer than one | Confirm queue and order, implement only the first |
| No open issues | `gh issue list` returns `[]` | Say so and stop |
| Dirty tree from a previous issue | `git status --porcelain` non-empty | Show the changes, offer commit / stash first |
| Scope larger than expected | Found during planning/implementation | Pause, inform user, suggest splitting |
| Verification tools not found | Commands not available | Inform user, suggest manual verification |

## Critical constraints

This skill owns only the implementation phase — the user controls the git workflow:

- Never let two issues share a commit or a pull request, and don't start the next queued issue until the current one's changes have left the working tree.
- Do not commit, push, create a branch or open a PR — the user reviews first and may have their own branching strategy; `github-commit-pr` is the shipping step.
- Do not modify files outside the issue's scope — scope creep makes the change harder to review and to revert.
- Ask rather than guess when requirements are ambiguous — a wrong guess costs more than a quick question.
