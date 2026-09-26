# Filing issues from an audit report

Used by `from-audit`. The input is a report file listing findings — typically a
`CODE_AUDIT_<date>_<time>_<auditor>.md` written by the code-analyzer skill, but any review or
audit file with one entry per finding works. The output is one well-formed issue per selected
finding, then a question about what to do with the report.

## 1. Locate and parse the report

- Use the path the user gave. Otherwise look for `CODE_AUDIT_*.md` at the repository root; with
  several, take the newest (the timestamp in the name sorts correctly) and name it in the review
  table so the user can object. If none exists, ask for the path — don't guess from other files.
- A code-analyzer report groups findings under `### Critical|High|Medium|Low|Ideas`, each as
  `#### [<id>] <title>` with **Where**, **Category**, **Severity / Confidence**, **What**,
  **Why it matters**, **Suggested fix**. Read every field; the severity heading and the
  **Severity** field should agree — if they don't, trust the field.
- For other formats, map whatever is there onto the same fields. If a finding has no stable id,
  number them yourself (`F-01`, `F-02`, …) so the user can refer to them.
- "None" under a heading means no findings there, not a finding called "None".

## 2. Settle the scope

File what the user asked for: explicit ids ("SEC-01, BUG-02"), severities ("the high and critical
ones"), or "all". With no scope given, propose Critical + High and list the rest as available on
request — a flood of Low items buries the important ones in the backlog.

- Ideas are feature suggestions, not defects: include them only when asked (or when the scope is
  "all").
- Flag findings marked low confidence in the review table; the user may want to verify first.

## 3. Duplicate check and labels

- Look up the repository's labels once (`gh label list`, see [labels.md](labels.md)), not per
  finding.
- For **each** in-scope finding run the duplicate search from the `create` operation (step 2 in
  SKILL.md): distinctive keywords from the title plus the file name from **Where**. Also search for
  the finding id together with the report name — an earlier import of the same report leaves that
  in the issue body, and re-running the import must not file everything twice:

```bash
gh issue list -R "$REPO" --state all --search "<keywords>" --json number,title,state,url --limit 20
gh issue list -R "$REPO" --state all --search "\"<report file name>\" <id> in:body" --json number,title,state,url
```

  A matching open issue → action `update #N` (comment with the new detail, per step 6b) or `skip`
  if it already says everything. A matching closed issue → action `ask` and let the user decide.

**Category → type label** (use a project label instead when the repo has a closer one, e.g.
`security`, `performance`, `tech-debt`, `testing`):

| Audit category | Type label |
|----------------|-----------|
| bug, security | `bug` (+ `security` if it exists) |
| performance, quality, architecture, tests | `enhancement` |
| docs | `documentation` |
| idea | `enhancement` |

Add a priority/severity label only if the repo already has such labels (e.g. `priority: high`,
`P1`) — never invent them. A missing type label follows the normal rule in labels.md: ask before
creating.

## 4. Draft the issues

- **Title**: imperative, ≤72 chars, no id or type prefix — "Fix SQL injection in /search query
  builder", not "[SEC-01] SQL injection". The id belongs in the body.
- **Body**: bug template for bug/security findings, enhancement template for the rest (see
  [issue-templates.md](issue-templates.md)):
  - Summary ← What + Why it matters
  - Current / Expected behavior ← What, and the behavior the fix implies
  - Steps to reproduce ← derive them when the finding describes a trigger (input, request, call
    sequence). Static findings often have none — then state the triggering condition and
    `file:line` instead of inventing steps.
  - Proposed Solution ← Suggested fix, with the **Where** locations as concrete file paths
  - Additional context ← `From code audit <report file name>, finding <id> (severity <s>,
    confidence <c>).`
- **Make each body self-contained.** The report is usually untracked and may be deleted in step 7,
  so never write "see the audit file" — copy the substance in. Keep the source line anyway; it is
  what makes step 3's re-import check work.

## 5. Review the batch once

Show a single table instead of asking issue by issue:

```
Source: CODE_AUDIT_2026-09-20_1410_claude-opus-5-5.md — 5 of 9 findings in scope

Id      Proposed title                                   Labels             Action
SEC-01  Fix SQL injection in /search query builder       bug, security      create
BUG-02  Fix off-by-one in paginate() last page           bug                update #14 (comment)
Q-01    Extract duplicated retry logic in http client    enhancement        create
BUG-03  Handle empty config file in load_config()        bug                skip — #9 already covers it
PERF-01 Cache compiled regexes in tokenizer (low conf.)  enhancement        create
```

Offer the full drafted bodies on request (or show them if the batch is small). Wait for the user
to confirm, drop, or edit rows before touching GitHub.

## 6. Create

Write each body to a temp file and pass it with `--body-file` — long bodies full of backticks and
code are fragile inside shell quoting:

```bash
gh issue create -R "$REPO" --title "<title>" --label "<labels>" --body-file "$TMPDIR/issue-<id>.md"
```

Create sequentially. If one fails (e.g. an unknown label, a secondary rate limit), keep going with
the rest and report the failures — don't abort half a batch silently. Then report:

```
Id      Issue
SEC-01  https://github.com/owner/repo/issues/31
BUG-02  #14 (commented)
Q-01    https://github.com/owner/repo/issues/32
BUG-03  skipped (#9)
```

## 7. Ask about the audit file

Once the batch is done — at least one issue created or updated from the report — ask whether to
delete the audit file. Its findings now live in issues, and stale reports at the repo root pile up
(code-analyzer writes a new timestamped one per run). The answer is the user's, so give them what
they need to decide in the same message:

- the file's path;
- which findings were **not** filed (out of scope, skipped, failed) — deleting the report loses
  those unless they exist elsewhere; if everything in it is covered, say so;
- whether git tracks it (`git ls-files --error-unmatch <file>`): untracked means deletion is final
  (there is no copy in history); tracked means it is a `git rm` that still has to be committed.

Only delete on an explicit yes — `rm <file>` if untracked, `git rm <file>` if tracked (don't
commit). If the user declines or doesn't answer, leave the file untouched. Don't ask when the run
created or updated nothing.
