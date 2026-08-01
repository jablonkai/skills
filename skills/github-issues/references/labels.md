# Label taxonomy

Always apply at least ONE type label and optionally a status label. Use GitHub's built-in default
labels unless the project defines its own.

## Type labels (apply exactly one)

| Label | When to use |
|-------|-------------|
| `bug` | Something is broken or not working as expected |
| `enhancement` | New feature or improvement to existing functionality |
| `documentation` | Documentation needs to be added or updated |
| `question` | Needs clarification or discussion before action |

## Status labels (apply as needed)

| Label | When to use |
|-------|-------------|
| `duplicate` | Issue already exists — link the original and close |
| `good first issue` | Simple enough for a newcomer to tackle |
| `help wanted` | Extra attention or community help is needed |
| `invalid` | Issue is not valid (wrong repo, not reproducible, etc.) |
| `wontfix` | Acknowledged but will not be addressed |

## Validating labels before use

Never apply a label without confirming it exists in the target repository — `gh` fails the whole
edit on an unknown label:

```bash
gh label list -R "$REPO" --json name --jq '.[].name'
```

Compare the output against the type labels above and note any that are missing.

- If all required type labels are present: proceed normally.
- If the expected type label is **missing**: inform the user, then either ask them to pick an
  existing label from the list as a substitute, or ask them to confirm creating the missing label
  before continuing.

## Custom project labels

If the project uses additional labels beyond GitHub defaults, use them when they exist and are
relevant. Do NOT create new labels without user confirmation — labels are shared across the entire
repository and affect everyone's workflow.

## Editing labels on an existing issue

Use `--add-label` / `--remove-label`, never `--label`:

```bash
gh issue edit <number> -R "$REPO" --add-label "<label>"
gh issue edit <number> -R "$REPO" --remove-label "<label>"
```

`--label` on `gh issue edit` replaces the full label set, silently dropping categorization someone
else applied. (`--label` is correct only on `gh issue create`, where there is nothing to replace.)
