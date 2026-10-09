---
name: github-do-all-issues
description: "Work through a repo's open GitHub issues autonomously: confirm the queue once, then for each issue implement, verify, self-review, and ship it as its own branch, commit and pull request (Closes #N) without stopping between issues — PRs are opened, never merged. Issues that are ambiguous, too large or can't be made green are skipped with a reason instead of blocking the run, and everything ends in one report. Use when someone wants the backlog done unattended: 'do all the issues and open PRs', 'work through every open issue on your own', 'clear the backlog overnight', 'ship a PR for each open bug', 'csináld meg az összes issue-t és nyiss mindegyikhez PR-t', 'menj végig a backlogon megállás nélkül', 'oldd meg az összes nyitott issue-t önállóan'. Not when the user wants to review each implementation before it is committed — that is github-do-issue (it stops after every issue); not for filing or triaging issues (github-issues)."
summary: "work through every open GitHub issue unattended — confirm the queue once, then implement, verify and open one PR per issue, skipping blocked ones with a reason"
category: development-workflow
risk: medium
tags:
  - github
  - issues
  - pull-request
  - automation
  - workflow
allowed-tools: Bash, Read, Grep, Glob, Edit, Write
argument-hint: "[<issue-number-or-url> ... | --label <name> | --milestone <name>]  (none = all open issues)"
metadata:
  version: "1.0.0"
---

# github-do-all-issues

## Purpose

Turn a backlog into a stack of reviewable pull requests in one unattended run. The user approves
the queue once; after that the skill does not pause between issues. Each issue still gets the full
treatment — fetch, plan, implement, verify, self-review — and lands as **its own branch, its own
commit and its own PR**, so the human review that github-do-issue does per issue happens afterwards,
on GitHub, one PR at a time.

The run never merges. Opening a PR is reversible and invites review; merging code nobody has read
is not. That single boundary is what makes it safe to not stop in between.

Sibling skills this one builds on — follow their rules where they apply:
[github-do-issue](../github-do-issue/SKILL.md) (queue building, the per-issue implementation steps)
and [github-commit-pr](../github-commit-pr/SKILL.md) (commit message and branch conventions,
sensitive-file check, PR body).

## Step 0: Pre-flight

```bash
command -v gh && gh auth status && git rev-parse --show-toplevel
git status --porcelain
BASE=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||'); echo "${BASE:=main}"
gh api user --jq .login
```

- `gh` missing / not logged in, or not a git repo → stop with the fix (`https://cli.github.com`,
  `gh auth login`).
- **Dirty tree → stop and ask.** Every issue's branch is cut from a clean base; uncommitted work
  would ride along into the first PR. Offer to commit it (github-commit-pr), stash it, or abort.
- Find the project's verification commands now, once — what CI runs (`.github/workflows/`), then
  `package.json` scripts, `Makefile`, README/AGENTS/CLAUDE/CONTRIBUTING. Note them for Step 2.5.
  If there are none, say so in the confirmation: PRs will be shipped on review alone.

## Step 1: Build the queue and confirm once

Build the queue exactly as github-do-issue's
[Backlog mode](../github-do-issue/SKILL.md#backlog-mode-no-issue-given) does — named issues in the
given order, or all open issues (`--limit 200`), oldest first, blockers before what they block,
with issues that already have a PR, are assigned to someone else, or aren't implementation work
(`question`, `discussion`, `duplicate`, `wontfix`, `invalid`, epics) set aside in a visible list.
`--label` / `--milestone` narrow the listing (`gh issue list --label … --milestone …`).

Then a single confirmation that also states the contract, since this is the last stop:

```
12 open issues. Queue — each becomes its own branch + PR against main, none merged:
1. #3  — <title>   [bug]
2. #5  — <title>
3. #9  — <title>   (blocks #11 → #11 will be stacked on #9's branch)
...
Set aside: #7 (open PR #40), #8 (assigned to @alice), #10 (question)
Verification per issue: npm run lint, npm test

I won't stop between issues. Unclear or oversized issues are skipped with a reason.
Go?
```

Long queues are fine here — that's the point — but past ~15 mention the time cost and offer to
cap it. After "go", don't ask again unless a [hard stop](#hard-stops) fires.

## Step 2: The per-issue loop

For each issue in the queue:

**2.1 Fresh base.** Re-check the issue is still open and has no linked PR
(`gh issue view N --json state,closedByPullRequestsReferences`); drop it silently into the report
if not. Then start from the up-to-date base so this PR contains only this issue:

```bash
git switch "$BASE" && git pull --ff-only
```

If the issue is blocked by one shipped earlier in this run whose PR is still unmerged, branch from
that PR's branch instead and target it as the PR base (a stacked PR — GitHub retargets it to
`$BASE` when the blocker merges with its branch deleted). Say so in the PR body.

**2.2 Understand.** `gh issue view N --json number,title,body,labels,comments` — body plus comments;
where they disagree, the latest agreed comment wins. Extract what changes, acceptance criteria,
and scope limits.

**2.3 Plan — and decide whether to skip.** Read the code around the change and the project
conventions, then write a 2–5 line plan for yourself (it goes into the PR body). No one is there
to answer a question, so instead of asking, **skip** the issue when:

- the requirements are ambiguous enough that two reasonable readings lead to different code;
- it needs a decision a maintainer should make (API/UX design, dependency choice, data migration,
  breaking change) and the thread hasn't made it;
- it is clearly bigger than one reviewable PR (rule of thumb: touches several modules or needs
  more than ~400 changed lines) — suggest a split in the report;
- it needs things you don't have: credentials, external accounts, hardware, manual QA.

A guess dressed up as a PR costs a reviewer more than a skip with a clear reason. Skipping is a
normal outcome, not a failure.

**2.4 Implement.** Only what this issue asks. Follow house conventions (i18n keys for new strings,
tests next to existing tests, etc.). Add or extend tests for the change when the project has
tests. A one-line fix belonging to another queued issue stays out — it goes in that issue's PR.

**2.5 Verify.** Run the commands found in Step 0 — at minimum the compiler/type checker, linter
and the tests touching the change; filter the output for failures rather than dumping logs. Fix
what fails. If it is still red after a few honest attempts, or the failure is pre-existing and
unrelated (check with `git stash; <test>; git stash pop`), see [When an issue doesn't land](#when-an-issue-doesnt-land).

**2.6 Self-review the diff.** `git diff` once as a reviewer would: every hunk tied to the issue,
no debug leftovers, no unrelated reformatting, no secret in the added lines (run github-commit-pr's
[sensitive-file check](../github-commit-pr/references/sensitive-files.md); a hit is a hard stop).

**2.7 Ship.** Follow github-commit-pr's
[commit and branch conventions](../github-commit-pr/references/commit-conventions.md) and
[PR body rules](../github-commit-pr/references/pr-body.md), minus their confirmation prompts — the
queue approval covers them:

```bash
git switch -c <type>/<slug>            # e.g. fix/null-token-settings; suffix -2 if taken
git add -A && git status --short       # the tree is this issue's work only
git commit -m "<type>(<scope>): <summary>"   # never --no-verify; on hook failure fix and commit anew
git push -u origin HEAD
gh pr create --base "<base>" --title "<type>(<scope>): <summary>" --body "<body>"
```

PR body: Summary bullets, `Closes #N` (`Fixes #N` for `fix`), the plan from 2.3, the verification
commands that passed, and anything a reviewer should look at first. Don't wait for CI here — that
happens once at the end.

**2.8 Log and move on.** Append one line to the run log (`#N → <pr-url>` or `#N skipped: <reason>`),
switch back to `$BASE`, and continue. Keep only that line in mind, not the issue's details — on a
long run the earlier issues' context is dead weight.

## When an issue doesn't land

Skipping must leave the tree clean so the next issue starts fresh. Decide what the partial work is
worth:

- **Nothing useful yet** (skipped at planning) → nothing to clean up.
- **Partial work worth keeping** → commit it on a local branch `wip/<N>-<slug>` and **don't push**.
  The report names the branch; the user decides.
- **Implemented but verification is red** → same local `wip/` branch; record the failing command
  and the first relevant error lines.

Never post comments on the issue or open a draft PR for a skip unless the user asked for that up
front — those are public, and a run log entry does the same job privately.

## Hard stops

Stop the whole run (report what was done so far) when continuing would compound damage rather than
just skip one issue:

- `git push` rejected, auth expired, or rate limited by GitHub;
- a secret found in a diff;
- the base branch can't be fast-forwarded or the tree is dirty at 2.1 with changes you can't
  attribute;
- three issues in a row skipped for the *same* reason (broken toolchain, failing baseline tests) —
  that's a systemic problem, not three bad issues.

Never force-push, never `--admin`, never merge.

## Step 3: CI sweep

After the last issue, check every PR the run opened:

```bash
gh pr checks <pr> --watch --fail-fast   # or poll: gh pr view <pr> --json statusCheckRollup
```

For a red PR: switch to its branch, root-cause the failure (logs filtered — see
github-commit-pr's [CI reference](../github-commit-pr/references/ci-and-merge.md), including the
billing-limit case where the code never ran), fix, commit, push, re-check. One round per PR; if it's
still red, leave it and say so. Return to `$BASE` when done.

## Step 4: Report

```
Backlog run: 12 queued → 8 PRs, 3 skipped, 1 dropped

Opened (none merged):
  #3  fix: handle empty config        → <url>   CI ✓
  #5  feat: export as CSV             → <url>   CI ✓
  #11 feat: bulk edit (stacked on #9) → <url>   CI ✓
  #14 fix: date parsing in Safari     → <url>   CI ✗ lint (one fix attempted)
Skipped:
  #6  ambiguous: "faster" with no target metric — needs a number
  #12 too large: auth rewrite — suggest split into token storage / refresh / UI
  #13 tests red after 3 attempts — local branch wip/13-retry-backoff (not pushed)
Dropped: #4 (closed during the run)

Merge order: #9 before #11 (stacked).
```

End there. Merging, following up on skips, and deleting `wip/` branches are the user's calls.
