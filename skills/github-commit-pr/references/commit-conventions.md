# Commit message and branch naming conventions

## Commit message

Write a conventional commit message based on the diff:

- **Format:** `<type>(<optional scope>): <short summary>` — add a scope when the repo's history
  uses them (`git log --oneline -10` shows the house style; match it)
- **Types:** `feat`, `fix`, `refactor`, `docs`, `style`, `chore`, `test`, `ci`, `build`, `perf`
- **Summary:** imperative mood, lowercase, no period, max 72 chars
- Add a body (blank line + wrapped paragraphs) for complex changes

Present the proposed message to the user:

1. **Accept** — use as-is
2. **Edit** — user provides their own

Commit with a heredoc so multi-line bodies survive shell quoting:

```bash
git commit -m "$(cat <<'EOF'
<type>: <summary>

<optional body>
EOF
)"
```

If the commit fails due to a pre-commit hook, read the hook output, fix the issue, re-stage, and
create a NEW commit — do not amend, and never pass `--no-verify`.

Issue closing keywords (`Closes #N`) belong in the PR body, not the commit message — see
[pr-body.md](pr-body.md) for why.

A commit message that needs "and" to describe two unrelated changes ("add dark mode and fix token
refresh") is the tell that the staged set spans two issues. Unstage the second one and give it its
own commit — the message gets easier to write, and each issue keeps a revertable commit of its own.

## Branch name

Derive the branch name from the commit message:

1. Take the summary part (after `type: ` or `type(scope): `)
2. Lowercase, replace spaces with hyphens, remove special characters (including parentheses from
   scoped types)
3. Prefix with the type: `feat/add-dark-mode`, `fix/null-token-settings`
4. Truncate to 60 characters max

**Example:** `feat(auth): implement JWT tokens` → `feat/implement-jwt-tokens`

```bash
git checkout -b <branch-name>
```

If the branch already exists, append a numeric suffix (e.g. `-2`).
