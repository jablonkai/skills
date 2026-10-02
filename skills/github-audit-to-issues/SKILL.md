---
name: github-audit-to-issues
description: "Audit a project and turn the findings straight into GitHub issues in one run: run the code-analyzer audit (or reuse a fresh report), keep the findings worth tracking, check each against existing issues, show one review table, then file the confirmed ones — with security findings in public repos routed to a private advisory instead of a public issue. Use when someone wants the audit to end up in the backlog, not just in a report: 'audit the repo and open issues for what you find', 'find the bugs and file them', 'turn a security review into tickets', 'fill the backlog from a code review', 'auditáld a projektet és nyiss issue-kat a hibákra', 'nézd át a kódot és csinálj belőle issue-kat', 'keress hibákat és vedd fel őket issue-nak'. Supports a dry run that drafts the issues without touching GitHub. Not for a report-only audit (code-analyzer), filing issues from a report that already exists (github-issues from-audit), or fixing the findings (github-do-issue / github-do-all-issues)."
summary: "audit a project and file the findings as GitHub issues in one run — scoped severities, duplicate checks, one review table, security findings kept out of public issues"
category: project-management
risk: medium
tags:
  - github
  - issues
  - audit
  - security
  - workflow
allowed-tools: Bash, Read, Grep, Glob, Agent, Write
argument-hint: "[focus: security|quality|performance|tests|docs|ideas|all] [--severity critical,high,...] [--report <file>] [--repo owner/repo] [--dry-run]"
---

# github-audit-to-issues

## Purpose

Go from "I don't know what's wrong with this repo" to "it's in the backlog" without the user
stitching two skills together. The run audits the project, picks the findings worth an issue, and
files them after **one** confirmation — the batch review table. Everything before that table is
read-only; everything after it is exactly what the table showed.

This skill is the glue, not a reimplementation. Follow the sibling skills' rules where they apply:

- [code-analyzer](../code-analyzer/SKILL.md) — how to audit, the report format, finding ids,
  severity and confidence, verifying critical/high findings before they count.
- [github-issues](../github-issues/SKILL.md) and its
  [audit-import reference](../github-issues/references/audit-import.md) — parsing findings,
  category→label mapping, duplicate and re-import checks, issue titles and bodies, the review
  table, creating with `--body-file`, and the question about deleting the report.

What this skill adds on top: one pre-flight for both halves, reuse of a fresh report, a scope rule
that keeps the backlog clean, the issue language, keeping security findings out of public issues,
a dry run, and the hand-off to fixing.

## Step 0: Pre-flight

```bash
git rev-parse --show-toplevel && git status --porcelain | head -5
command -v gh && gh auth status
gh repo view --json nameWithOwner,visibility,viewerPermission,hasIssuesEnabled
ls -t CODE_AUDIT_*.md 2>/dev/null | head -3
```

- `--repo owner/repo` overrides the detected repository; pass `-R "$REPO"` to every `gh` call.
- **Can't file** — `gh` missing or logged out, no GitHub remote, issues disabled, or
  `viewerPermission` is `READ`/`NONE` → say so now, before spending time on an audit. Offer the dry
  run instead; it still produces the drafted issues as files.
- Note `visibility` — it decides how security findings are handled (Step 3).
- A dirty tree doesn't block an audit; mention it, since findings in uncommitted files describe
  code that isn't on GitHub yet — their issue would point at lines nobody else can see.

## Step 1: Get a report

**Reuse before re-auditing.** If `--report` names a file, use it. Otherwise, if the newest
`CODE_AUDIT_*.md` is newer than the last commit (`git log -1 --format=%cI` vs the timestamp in the
file name) and nothing else changed since
(`git status --porcelain -- . ':!CODE_AUDIT_*.md'` is empty — the untracked report itself
doesn't count), it already describes this code — propose reusing it rather than
paying for a second audit. Older reports describe code that has moved on; audit fresh.

A reused report is someone else's audit: reopen the code behind each in-scope finding before
drafting it, as code-analyzer's verification step does. If that reading turns up a real problem
the report missed, don't silently draft it and don't just mention it — list it under the review
table as `not in report` and offer a supplementary audit pass, so the user decides whether the
report is still good enough to file from.

**Auditing.** Run the audit per code-analyzer with the focus argument (default: all dimensions),
in its non-interactive mode: no hand-off menu at the end — this skill takes over from there. Keep
its verification step; a false critical turned into a public issue is worse than one in a report.
The report is written to the repo root as usual.

## Step 2: Scope the findings

Default scope — what goes into the review table as `create`:

- **Critical and High**, confidence medium or high.
- Low-confidence findings at those severities appear in the table as `verify first` rather than
  `create`: filing a guess makes a maintainer disprove it in public.
- Medium, Low and Ideas are summarized as one line under the table ("also available: 6 medium,
  4 low, 3 ideas") — filing them by default floods the backlog and buries the real problems.

`--severity` or the user's wording ("everything", "the security ones", "SEC-01 and BUG-03")
replaces the default. Ideas go in only when asked for or with "all".

**Group what belongs together.** Several findings with one fix (the same missing validation in
three handlers, the same deprecated call in five files) become one issue listing every location —
five issues for one change is five times the triage. Never merge findings that need different
fixes just to shorten the list.

## Step 3: Draft, deduplicate, and route

Follow audit-import sections 3–4 for each in-scope finding: one `gh label list`, a duplicate
search plus the re-import search, the category→label map, imperative titles, self-contained bodies
that end with the `From code audit <report>, finding <id>` source line.

**Language.** Write issues in the language the repo already uses — look at the last few issue
titles (`gh issue list --state all --limit 10`) and the README. With nothing to go on, use English
for a public repo and the user's language for a private one. The report itself stays in the user's
language.

**Security findings.** In a **public** repo, a public issue describing an exploitable
vulnerability is a disclosure. Route `security` findings at High/Critical to a private draft
security advisory instead — see [references/security-findings.md](references/security-findings.md).
In a private or internal repo they are ordinary issues (with `security` label if it exists).
A **leaked secret** is never filed, in any repo: it is told to the user directly, to rotate now
(same reference).

## Step 4: Review once

Show the audit-import review table with this skill's extra columns and actions:

```
Repo: owner/repo (public) · Report: CODE_AUDIT_2026-10-02_1410_claude-opus-5-5.md (new)
Scope: critical + high — 6 of 17 findings

Id             Title                                          Labels          Action
SEC-01         Parameterize the /search SQL query             bug, security   advisory (private)
BUG-01         Fix off-by-one in paginate() last page         bug             create
BUG-02+BUG-04  Handle missing config in all three loaders     bug             create (grouped)
Q-02           Split the 900-line OrderService                enhancement     update #14
PERF-01        Cache compiled regexes in tokenizer            enhancement     verify first (low conf.)

Also available: 7 medium, 3 low, 1 idea.  Drafts: <dir>  (full bodies on request)
Go? — or change rows ("drop Q-02", "add the mediums", "file PERF-01 anyway")
```

Write every draft to a run directory first (`$TMPDIR/audit-issues-<repo>-<YYYYmmdd-HHMMSS>/<id>.md` — the repo name and
seconds keep two runs from writing into the same directory — plus
`table.md`), so the user can open them and so `--body-file` has something to read. Apply the
user's edits and show the table again only if rows changed substantively. Nothing touches GitHub
before a "go".

**Dry run** (`--dry-run`, "just draft them", or when Step 0 found filing impossible): stop here.
Leave the run directory, print the table and its path, and skip Steps 5–6 except mentioning the
report file. Read-only `gh` calls (labels, duplicate search, visibility) still run when available;
when they can't, say which checks were skipped so the drafts aren't mistaken for deduplicated ones.

## Step 5: File

Per audit-import section 6: sequentially, `--body-file`, keep going past a single failure and
report it. Advisories per the security reference. Stop the batch only for a failure that will hit
every remaining row — auth expired, rate limit, permission lost — and report what was filed.

## Step 6: Wrap up

```
Filed from CODE_AUDIT_2026-10-02_1410_claude-opus-5-5.md:
  BUG-01         → #31
  BUG-02+BUG-04  → #32
  Q-02           → #14 (commented)
  SEC-01         → draft advisory GHSA-xxxx-xxxx-xxxx (private)
  PERF-01        not filed (verify first)
Not in scope: 7 medium, 3 low, 1 idea — still only in the report.
```

Then, in the same message:

1. Ask about the report file exactly as audit-import section 7 does — the unfiled findings above
   are the ones a delete would lose.
2. Offer the next step without starting it: fix them one at a time with review
   (github-do-issue `#31 #32`) or unattended, one PR each (github-do-all-issues `#31 #32`).

## Rules

- One confirmation: the review table. Don't ask per finding, and don't file anything that wasn't
  in the confirmed table.
- The audit half is read-only apart from the report file — no code edits, installs, or commits.
- Never close, relabel, or edit existing issues; a duplicate gets a comment (`update #N`) at most.
- Never create labels, milestones, or projects without asking — use what the repo has.
- Never put an exploitable vulnerability in a public issue, and never a secret value anywhere.
