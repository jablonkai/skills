# Security findings in public repositories

Read when Step 3 routes a `security` finding at High/Critical in a **public** repo. An issue
there is visible to everyone, indexed, and mirrored — describing an exploitable vulnerability in
it is a disclosure before a fix exists. A repository security advisory is private to the
maintainers until they publish it, and is where GitHub expects the fix to be coordinated (it can
open a private fork for the patch and request a CVE later).

## What goes where

| Finding | Public repo | Private / internal repo |
|---------|-------------|-------------------------|
| `security`, High/Critical | draft advisory | issue (`bug` + `security` if it exists) |
| `security`, Medium/Low (hardening, no realistic exploit path) | issue, worded as hardening | issue |
| Leaked secret | no issue, no advisory — tell the user to rotate it now (see below) | same |

Hardening wording means describing the fix, not the attack: "Validate the redirect target in
`/login`" rather than "Open redirect lets attackers steal sessions via `/login?next=`".

## Creating a draft advisory

Needs admin or security-manager rights on the repo (`viewerPermission` `ADMIN`, or a security
manager role). Write the JSON to the run directory and pass it as the request body:

```json
{
  "summary": "SQL injection in /search query builder",
  "description": "<What + Why it matters + Where + Suggested fix, self-contained, Markdown>\n\nFrom code audit <report>, finding SEC-01 (confidence high).",
  "severity": "high",
  "cwe_ids": ["CWE-89"],
  "vulnerabilities": [
    { "package": { "ecosystem": "other", "name": "<repo name or published package name>" } }
  ]
}
```

```bash
gh api -X POST "repos/$REPO/security-advisories" --input "$RUN_DIR/SEC-01.advisory.json" \
  --jq '{ghsa_id, html_url, state}'
```

- `severity`: the finding's severity (`critical`/`high`/`medium`/`low`). Add `cwe_ids` only when
  the CWE is obvious from the finding (CWE-89 SQLi, CWE-79 XSS, CWE-22 path traversal, CWE-78
  command injection, CWE-918 SSRF, CWE-601 open redirect); otherwise leave it out.
- `ecosystem`: the package's real one when the repo publishes a package (`npm`, `pip`, `maven`,
  `go`, `rust`, `pub`, `swift`, `composer`, `nuget`, `rubygems`, `erlang`, `actions`), else
  `other`.
- The advisory is created as a **draft** — nothing is published. Never publish it or request a
  CVE; those are the maintainer's calls.
- Duplicate check: `gh api "repos/$REPO/security-advisories?state=draft" --jq '.[].summary'` (and
  `triage`) before creating — a re-run must not open the same advisory twice.

## When the advisory can't be created

403/404 (not an admin, or advisories unavailable for the account) → don't fall back to a public
issue. Mark the row `not filed (no advisory access)`, keep its draft in the run directory, and
tell the user who can file it: a repo admin, or the owner through private vulnerability
reporting if it is enabled.

## Leaked secrets

A committed key is already public, and rotating it is the only fix — an issue or advisory adds a
second copy of the pointer and no protection. Report it to the user directly, at the top of the
wrap-up: which file, the redacted value and type, "rotate it, then purge it from history". Redact
the way code-analyzer does — the first 4 characters and the type (`sk_l…`, Stripe live secret
key) — also when you found the key yourself and the report gives no redacted form to copy. A
longer prefix narrows the search for anyone holding a partial leak.
