---
name: github-issues
description: "Create, view, close, comment on, label, triage, and list GitHub issues with standardized structure — including batch-filing issues from a code audit or review report (e.g. a CODE_AUDIT_*.md from code-analyzer). Use when someone says 'create an issue', 'file a bug', 'open an issue for this', 'turn the audit findings into issues', 'open issues for the high/critical items', 'triage issues', 'label issue #N', 'close #N as duplicate', 'list open issues', 'hozz létre egy issue-t', 'csinálj issue-kat az audit alapján', or wants to manage GitHub issues in any way. Checks for duplicates first, enforces templates with required sections (Summary, Proposed Solution), and validates labels exist before use. Not for implementing an issue (github-do-issue) or opening pull requests (github-commit-pr)."
summary: "standardized issue creation (including batch filing from audit reports), labeling, triage, commenting, and issue management through the GitHub CLI"
category: project-management
risk: low
tags:
  - github
  - issues
  - labels
  - project-management
  - triage
allowed-tools: Bash, Read, Grep, Glob
argument-hint: "[create <title> | from-audit [<file>] [<ids or severities>] | view <number> | close <number> [reason] | comment <number> <text> | assign <number> <user> [--remove] | label <number> <label> [--remove] | triage | list [--label <label>]]"
---

# github-issues

## Purpose

Standardize GitHub issue creation and management across any project. Ensure every issue has a clear structure, proper labels, and actionable content. Guide the user through creating well-formed issues and applying GitHub's default label taxonomy consistently.

## Prerequisites

Before any operation, verify the environment:

1. **Check `gh` is installed and authenticated** — `gh auth status`. If it isn't, stop and point the user to `gh auth login`; every later step would fail anyway.

2. **Detect repository context:**

```bash
gh repo view --json nameWithOwner --jq .nameWithOwner
```

Store the result as `REPO="owner/repo"`. `gh` resolves the remote itself (SSH or HTTPS, and the configured base repo in a fork). If it fails — not a git repository, or no GitHub remote — ask the user for `owner/repo`.

Do this **before** any `gh issue` or `gh label` command, and pass `-R "$REPO"` to each of them so they always target the correct repository, regardless of the current directory.

## When to use

- Creating a new GitHub issue (with a duplicate check first — updating an existing issue when one already covers the request)
- Filing a batch of issues from an audit or review report file
- Viewing issue details
- Closing issues with explanation
- Commenting on existing issues
- Triaging or labeling existing issues
- Listing open issues with their labels

## Detailed references

Load these on demand — don't read them up front:

- [references/issue-templates.md](references/issue-templates.md) — title rules, the enhancement and bug body templates, the body-section rules, and type detection from title/context. Read before writing or rewriting an issue body.
- [references/labels.md](references/labels.md) — the type/status label taxonomy, how to validate a label exists before applying it, and the `--add-label` vs `--label` rule. Read before applying or changing labels.
- [references/audit-import.md](references/audit-import.md) — turning an audit/review report into issues: parsing findings, category→label mapping, per-finding duplicate check, the batch review table, and the closing question about deleting the report. Read for `from-audit`.

## Operations

Based on `$ARGUMENTS`, perform ONE of these operations. If the request is to file issues from a report file — "open issues for the audit findings", "csinálj issue-kat az audit alapján", or picking option 2 after a code-analyzer audit — use `from-audit`, even when the user said "create".

### `create <title>`

1. Determine the issue type from the title and context — see the type-detection indicators in [references/issue-templates.md](references/issue-templates.md).
2. **Check for an existing issue covering the same thing — before creating anything.** Filing a second issue for a problem that already has one fragments the discussion and wastes triage effort, so always search first. Pull the most distinctive keywords from the title (drop generic verbs like "add"/"fix" and stop-words) and search across both open and closed issues:

```bash
gh issue list -R "$REPO" --search "<keywords>" --state all --json number,title,state,url,updatedAt --limit 20
```

   Read the candidates and judge whether any describes the **same underlying request or bug** — not just a keyword overlap. Two issues that touch the same file but ask for different things are not duplicates; two issues worded differently that would be resolved by the same change are. When unsure, treat the closest candidate as a possible match and let the user decide rather than guessing.

   - **No real match:** proceed to step 3 and create a new issue.
   - **A matching OPEN issue exists:** do not create a duplicate. Open it (`gh issue view <number> -R "$REPO"`) and compare its body against the new details. If the request brings genuinely new information (extra repro steps, an affected file the issue is missing, a clearer proposed solution, new context), update the existing issue instead — see step 6b. If the existing issue already covers everything, tell the user it's already filed (with the link) and stop without changing anything.
   - **A matching CLOSED issue exists:** surface it to the user with its link and state. Ask whether to reopen it (if the problem has resurfaced), add the new context as a comment, or file a fresh issue (e.g. the old one was a different root cause). Don't reopen silently.

3. **Check which labels are available** in the target repository and handle any missing type label — follow [references/labels.md](references/labels.md).
4. Select the matching body template (enhancement or bug) from [references/issue-templates.md](references/issue-templates.md) and pre-fill the "Summary" section from context. If the user has provided enough detail, fill all applicable sections. Otherwise, ask for the missing required sections — especially "Proposed Solution" with specific file paths and implementation approach.
5. Suggest appropriate labels based on the type detection and available labels discovered in step 3.
6. **Present the full issue (title, body, labels) for user review before creating.** Wait for confirmation or edits.
7. Create the issue:

```bash
gh issue create -R "$REPO" --title "<title>" --label "<label1>,<label2>" --body "$(cat <<'EOF'
<body content>
EOF
)"
```

8. Output the issue URL.

#### Step 6b: Updating an existing issue instead of creating

Reached only when step 2 found a matching open issue that's missing information the new request provides. The goal is to enrich the existing issue without clobbering what's already there — its body may contain edits, discussion references, or detail the user added by hand.

1. Decide what genuinely needs to change. For a small addition (an extra repro step, a link, a newly identified cause), a comment is the least destructive and keeps an audit trail:

```bash
gh issue comment <number> -R "$REPO" --body "$(cat <<'EOF'
<the new information, e.g. additional repro steps or an affected file>
EOF
)"
```

2. If the issue's **structured body** is materially incomplete (missing the "Proposed Solution", wrong/empty "Summary") and rewriting it makes the issue clearer, edit the body — but show the user the proposed new body first and merge with the existing content rather than replacing it wholesale:

```bash
gh issue edit <number> -R "$REPO" --body "$(cat <<'EOF'
<merged body — existing content plus the new details>
EOF
)"
```

3. If the new context changes the categorization (e.g. it turns out to be a bug, not just an enhancement), add the appropriate label with `--add-label` (never `--label`, which would wipe existing labels).
4. Output the issue URL and a one-line note of what you changed.

### `from-audit [<file>] [<ids or severities>]`

Batch-create issues from the findings of an audit or review report — follow [references/audit-import.md](references/audit-import.md) end to end. In short:

1. Locate the report (the given path, else the newest `CODE_AUDIT_*.md` at the repo root — confirm it if more than one exists) and parse every finding.
2. Settle the scope — the ids or severities the user named, otherwise propose Critical + High and ask.
3. Run the `create` step-2 duplicate check **per finding**, and look up the available labels once.
4. Draft every issue from the templates, making each body self-contained (the report may be deleted afterwards).
5. Show **one** review table for the whole batch — finding id, proposed title, labels, and action (create / update #N / skip) — and wait for confirmation.
6. Create/update the confirmed issues and report a finding → issue URL table.
7. **Ask whether to delete the audit file.** Never delete it on your own — see the reference for what to tell the user before they answer.

### `view <number>`

1. Display the issue details:

```bash
gh issue view <number> -R "$REPO"
```

2. If the user wants to see discussion, show comments:

```bash
gh issue view <number> -R "$REPO" --comments
```

### `close <number> [reason]`

1. Fetch the issue to verify state:

```bash
gh issue view <number> -R "$REPO" --json title,labels,state
```

2. If the issue is already closed, inform the user and stop.
3. **If closing as duplicate**, require the user to specify the original issue number. Verify the original exists, then close with GitHub's native duplicate reason — it records the link in the issue timeline:

```bash
gh issue view <original> -R "$REPO" --json number,title,state
gh issue close <number> -R "$REPO" --duplicate-of <original> --comment "Closing as duplicate of #<original>."
```

If the repository has a `duplicate` label, also add it (`gh issue edit <number> -R "$REPO" --add-label "duplicate"`); if it doesn't, skip it — the close reason already carries the meaning. On an old `gh` without `--duplicate-of` (it fails with "unknown flag"), fall back to `--reason "not planned"` plus the comment.

4. **For other closures**, close with a comment explaining why, and pick the reason — `completed` (done/fixed) or `not planned` (won't fix, invalid, obsolete):

```bash
gh issue close <number> -R "$REPO" --reason "<completed|not planned>" --comment "<reason>"
```

5. If the user provides a reason in the arguments, use it. Otherwise, ask for a reason before closing — never close silently.

### `comment <number> <text>`

1. Verify the issue exists:

```bash
gh issue view <number> -R "$REPO" --json number,title,state
```

2. Add the comment:

```bash
gh issue comment <number> -R "$REPO" --body "<text>"
```

3. Confirm the comment was posted with a link.

### `assign <number> <user> [--remove]`

1. Verify the issue exists:

```bash
gh issue view <number> -R "$REPO" --json number,title,state,assignees
```

2. If `--remove` is **not** provided, assign the user:

```bash
gh issue edit <number> -R "$REPO" --add-assignee "<user>"
```

   If `--remove` **is** provided, unassign:

```bash
gh issue edit <number> -R "$REPO" --remove-assignee "<user>"
```

3. If `<user>` is `@me` or `me`, resolve to the authenticated user:

```bash
gh api user --jq '.login'
```

4. Confirm the assignment change.

### `label <number> <label> [--remove]`

1. Fetch available labels to validate the requested label exists:

```bash
gh label list -R "$REPO" --json name --jq '.[].name'
```

2. Add or remove the label with `--add-label` / `--remove-label` — see [references/labels.md](references/labels.md) for the exact commands and why `--label` must never be used on `gh issue edit`.
3. If the label does not exist, warn the user and list available labels. Suggest the closest match if possible.

### `triage`

1. List all open issues with their labels:

```bash
gh issue list -R "$REPO" --state open --json number,title,body,labels,createdAt --limit 100
```

2. Filter for issues where `labels` is empty.
3. If no unlabeled issues are found, inform the user ("All open issues are labeled") and stop.
4. Analyze the title and body of each unlabeled issue to suggest a label, using the type-detection indicators in [references/issue-templates.md](references/issue-templates.md) and the taxonomy in [references/labels.md](references/labels.md).
5. Present a summary table with suggested labels:

```
#   Title                                    Suggested Label
37  Add database corruption recovery         enhancement
33  Fix error state on successful ops        bug
30  Update API documentation                 documentation
```

6. Ask the user to confirm, modify, or skip each suggestion before applying.
7. Apply confirmed labels:

```bash
gh issue edit <number> -R "$REPO" --add-label "<label>"
```

### `list` (default when no arguments given)

1. List open issues:

```bash
gh issue list -R "$REPO" --state open --json number,title,labels,assignees --limit 50
```

If `--label <label>` is specified in the arguments, add `--label "<label>"` to filter.

2. Display in a readable table format:

```
#   Title                                    Labels              Assignee
12  Add dark mode toggle                     enhancement         @user
11  App crashes on startup with empty DB     bug, good first     —
10  Update README with build instructions    documentation       @user
```

3. Show summary: total count and label distribution.
4. If there are more issues than the displayed limit, inform the user and suggest using `--label` to filter or increasing the limit.

## Error handling

| Scenario | Detection | Action |
|----------|-----------|--------|
| `gh` not installed | `command -v gh` fails | Direct user to https://cli.github.com |
| `gh` not authenticated | `gh auth status` fails | Ask the user to run `gh auth login` |
| Not in a git repo | `git rev-parse --show-toplevel` fails | Ask user for `owner/repo` manually |
| No remote configured | `git remote get-url origin` fails | Ask user for `owner/repo` manually |
| Issue not found | `gh issue view` exits non-zero | Verify the issue number and repository |
| Label not found | Label not in `gh label list` output | Show available labels, suggest closest match |
| Permission denied | `gh` returns 403/404 | Check repo access and authentication scopes |
| Rate limited | `gh` returns 429, or 403 mentioning "secondary rate limit" (common when creating many issues in a row) | Pause, then retry once; in a batch, report which items were not created yet |

## Constraints

These rules keep issue quality high and prevent accidental damage to existing labels and issues:

- Search for an existing issue before creating a new one, and update that issue rather than filing a duplicate — duplicate issues split discussion and double the triage burden
- Every issue needs at least one type label — labels are the primary categorization mechanism and enable filtering and triage
- Present the full issue (title, body, labels) for user review before creating — the user owns the final content
- Add a comment explaining why before closing any issue — future readers need to understand the decision
- Link the original issue before closing as duplicate — this preserves the relationship in GitHub's UI
- Use `--add-label` (not `--label`) when editing issues — `--label` replaces all existing labels, which can silently remove important categorization
- Do not create new labels without user confirmation — labels are shared across the entire repository and affect everyone's workflow
- Include specific file paths and code references in issue bodies when context is available — actionable issues with concrete pointers get resolved faster
- Never delete a source report (audit file) without the user's explicit yes — it may hold findings that were not filed
