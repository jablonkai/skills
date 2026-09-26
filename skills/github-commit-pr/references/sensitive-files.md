# Sensitive file detection

Run this scan **before staging anything**, in both the New PR flow and the Push to existing PR
flow. A secret committed to a branch stays in the history even if a later commit removes it, and
pushing it makes it public to everyone with repo access — this check is the only gate between
`git add` and that outcome.

A secret can hide in two places: in a file that exists to hold one (`.env`, a key file), or pasted
into an ordinary source file (a hard-coded API key left over from debugging). File names only catch
the first, so check both names and content.

## 1. Files that are secrets by nature — always flag

- `.env`, `.env.*` files
- `id_rsa`, `id_ed25519`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.p8`, `*.keystore`, `*.jks`
- `*.json` files that look like service account keys (e.g. `*-credentials.json`,
  `serviceaccount*.json`, `google-services.json` with an `api_key` block)
- `.npmrc`, `.pypirc`, `.netrc`, `credentials` files that carry auth lines

## 2. Suspicious names — look before flagging

Names containing `secret`, `credential`, `password`, `token` or `apikey` are only a hint:
`tests/test_token.sh`, `src/auth/TokenRefresher.kt` or `password_reset_screen.dart` are ordinary
code. Look at what the diff adds to such a file — flag it only when the content holds an actual
value (section 3). Flagging every file with `token` in its name trains the user to wave warnings
through, which defeats the check.

## 3. Secret-looking content — scan every change

Scan the added lines of tracked changes and the contents of new untracked files:

```bash
pat='-----BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_|sk_live_|sk-[A-Za-z0-9_-]{20,}|xox[abpr]-|AIza[0-9A-Za-z_-]{30,}|(api[_-]?key|secret|token|passw(or)?d)[A-Za-z_]*["'\'']?[[:space:]]*[:=][[:space:]]*["'\''][^"'\''[:space:]]{12,}'
git diff HEAD -U0 | grep -E '^\+[^+]' | grep -inE -e "$pat"
git ls-files --others --exclude-standard -z | xargs -0 grep -inE -e "$pat" 2>/dev/null
```

A hit is a real-looking credential assigned to a name, or a known token format. Obvious
placeholders (`"changeme"`, `"<your-key>"`, `"xxx"`, `${ENV_VAR}` references, test fixtures that
are clearly fake) are not hits — but when in doubt, flag it: a false alarm costs one question, a
leaked key costs a rotation.

## What to do on a hit

**Warn the user explicitly** — name the file, and for content hits the line — and ask whether to
exclude or fix it. Do NOT silently stage it, and do not decide on the user's behalf that a match is
a false positive: an `.env.example` full of placeholders is fine to commit, but only the user knows
that. A pre-approval like "don't ask, just ship it" covers the commit message and the merge, not
publishing a credential.

- **Whole file is sensitive** (`.env`, a key) → leave it out: stage everything else explicitly
  rather than using `git add -A`, and suggest adding the path to `.gitignore`.
- **Secret inside a file that otherwise belongs in the commit** → don't commit that file as-is.
  Stop and ask; the usual fix is moving the value to an environment variable or the untracked
  config. If the user can't be asked, ship nothing that contains it and say what is waiting on them.

Keep this check inline in the main agent — it needs the user interaction, so it can't be handed to a
read-only subagent.
