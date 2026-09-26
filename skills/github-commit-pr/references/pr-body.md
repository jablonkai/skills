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

**One closing keyword per PR.** A second `Closes #N` means the PR is carrying a second issue — the
reviewer can no longer approve or revert either one on its own. If you're about to write two, stop
and split the work into two PRs instead (see the SKILL's "One issue, one commit, one PR"). The
exception is a bundle the user explicitly asked for: then list every issue, so no issue silently
stays open after the merge.

Related-but-not-closed issues are different — reference them without a keyword (`Related to #7`) so
GitHub links them without closing them.

Closing keywords go in the **PR body**, not the commit message. The PR body is where GitHub links
the issue in the PR sidebar and closes it on merge; a keyword in a commit message also closes the
issue whenever that commit reaches the default branch — including via a cherry-pick or a rebase
nobody meant as "done". Keywords only act when the PR targets the **default branch**; for a PR into
another base, write `Related to #N` and tell the user the issue will need closing by hand.

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

- **Title:** the commit subject as-is, conventional prefix included (`fix(auth): refresh expired
  token`), max 70 chars. A squash merge uses the PR title as the commit subject on the base branch,
  so stripping `type:` here would leave a non-conventional commit in the shared history
- **Base branch:** detected in pre-flight or taken from `$ARGUMENTS`
