# Sensitive file detection

Run this scan on the `git status` output **before staging anything**, in both the New PR flow and
the Push to existing PR flow. A secret committed to a branch stays in the history even if a later
commit removes it, and pushing it makes it public to everyone with repo access — this check is the
only gate between `git add -A` and that outcome.

## Patterns to flag

- `.env`, `.env.*` files
- Files containing `secret`, `credential`, `token`, `password`, `key` in their name
- `id_rsa`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.p8`, `*.keystore` files
- `*.json` files that look like service account keys (e.g. `*-credentials.json`,
  `serviceaccount*.json`)

## What to do on a hit

**Warn the user explicitly** and ask whether to exclude the file. Do NOT silently stage sensitive
files, and do not decide on the user's behalf that a given match is a false positive — an
`.env.example` full of placeholders is fine to commit, but only the user knows that.

If the user wants the file excluded, stage everything else explicitly rather than using `git add -A`,
and suggest adding the path to `.gitignore` so the next run doesn't have to re-litigate it.

Keep this check inline in the main agent — it needs the user interaction, so it can't be handed to a
read-only subagent.
