# PR body construction

## Check for a repository PR template

```bash
cat .github/PULL_REQUEST_TEMPLATE.md 2>/dev/null || \
  cat .github/pull_request_template.md 2>/dev/null || \
  cat PULL_REQUEST_TEMPLATE.md 2>/dev/null || \
  cat docs/PULL_REQUEST_TEMPLATE.md 2>/dev/null
```

If a template exists, use its structure and fill in the sections from the diff context. If no
template exists, use this default structure:

```markdown
## Summary
<1-3 bullet points describing the actual changes from the diff>

## Test plan
<bulleted checklist of testing steps>
```

The body must reflect the actual changes from the diff, not boilerplate — reviewers rely on it to
understand the change.

## Issue linking

Apply this when `$ARGUMENTS` contains `--issue <number>`, the user mentions an issue number, or the
branch name contains one.

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

**Valid closing keywords** (all work the same): `Closes`, `Fixes`, `Resolves`. Use `Closes` by
default. For bug fixes (commit type `fix`), use `Fixes` instead.

Closing keywords go in the **PR body**, never the commit message — GitHub only processes closing
keywords from the PR body on the default branch.

3. If the issue has labels, apply matching labels to the PR after creation:

```bash
gh pr edit <pr-number> --add-label "<label1>,<label2>"
```

## Creating the PR

```bash
gh pr create --title "<summary>" --base "<base-branch>" --body "$(cat <<'EOF'
<PR body>
EOF
)"
```

- **Title:** first line of the commit summary without the `type:` prefix, max 70 chars
- **Base branch:** detected in pre-flight or taken from `$ARGUMENTS`
