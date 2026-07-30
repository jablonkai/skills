---
name: affinity
description: 'Remote-control Affinity (the unified Affinity by Canva app: vector, pixel, and layout studios) with JavaScript through its local automation endpoint — no MCP client configuration needed. Automate document edits, batch operations, text/layer manipulation, and reusable library scripts, with rendered-JPEG visual verification. Use whenever the user wants to script or automate Affinity, programmatically edit .af / .afdesign / .afphoto / .afpub documents, batch-process designs, or says "Affinity", "Affinity script", "automate Affinity", "batch edit in Affinity", "control Affinity" — even if they don''t mention scripting.'
category: design-automation
risk: medium
tags:
    - affinity
    - design
    - automation
    - scripting
---

# Affinity Control

Affinity (`/Applications/Affinity.app`, the unified Canva-era app) has **no** AppleScript
dictionary, CLI, or URL scheme, and its file formats are proprietary. Its only automation
surface is the **AI connector**: when enabled, the app serves its JavaScript scripting SDK
on `http://localhost:6767/sse`. The endpoint speaks the MCP protocol, but this skill drives
it directly over HTTP/SSE with a zero-dependency Node CLI — no MCP client configuration,
no tool schemas loaded into context. Verified end-to-end against Affinity 3.2.3.

- [scripts/affinity-cli.mjs](scripts/affinity-cli.mjs) — the CLI (Node ≥ 18, no npm install needed).
- [references/api-reference.md](references/api-reference.md) — verified endpoint tool contracts + SDK preamble digest. **Read it before writing scripts.**
- [references/sdk-map.md](references/sdk-map.md) — curated SDK digest: module map, node model, creation recipes (text, image, adjustments), gotchas. Read it when writing anything beyond the basic drawing recipe.
- [references/sdk-docs/](references/sdk-docs/) — the complete vendored SDK documentation (109 topics, ~1.3 MB). Grep it for exact signatures only after sdk-map.md; never read the big files whole (`nodes.js` is 180 KB).

## The control loop

1. **Preflight** — the endpoint cannot be enabled remotely:

   ```bash
   node scripts/affinity-cli.mjs ping     # → "OK http://localhost:6767 — Affinity 1.0.0"
   ```

   If it fails, ask the user to launch Affinity and enable the AI connector
   (Affinity Settings → AI connector; see the [setup guide](https://www.affinity.studio/help/ai-connector-setup/)
   — the Claude-side connector steps there are NOT needed, only the in-app toggle).

2. **Write the script** — JavaScript against the Affinity SDK. Start from
   [references/api-reference.md](references/api-reference.md), then
   [references/sdk-map.md](references/sdk-map.md) for the right module and recipe;
   grep `references/sdk-docs/` for exact signatures. Scripts are top-level executable code; output ONLY via `console.log()`
   (return values are dropped). Entry point:

   ```js
   const { app } = require('/application');
   const doc = app.documents.current;
   ```

   When an API resists, search the crowd-sourced hints pool:
   `node scripts/affinity-cli.mjs search "set blend mode"`.

3. **Execute**:

   ```bash
   node scripts/affinity-cli.mjs run myscript.js
   ```

   Runs via the endpoint's `execute_script` and prints the script's console output.
   Errors come back as text — iterate on the file and re-run.

4. **Verify visually** — never assume a script worked:

   ```bash
   node scripts/affinity-cli.mjs render --out /tmp/check.jpg            # current spread
   node scripts/affinity-cli.mjs render --selection --out /tmp/sel.jpg  # selection only
   ```

   Then `Read` the JPEG (max 1024 px). The document session uuid is fetched automatically.

5. **Ship** — when the user is happy with a script, install it for reuse:

   ```bash
   node scripts/affinity-cli.mjs add --title "My Script" --description "What it does" --file myscript.js
   ```

   Library scripts appear in Affinity under **Window → General → Scripts**.

## CLI cheatsheet

```bash
node scripts/affinity-cli.mjs ping                          # endpoint alive?
node scripts/affinity-cli.mjs run file.js                   # execute script, print console output
node scripts/affinity-cli.mjs render [--selection] [--spread N] --out f.jpg
node scripts/affinity-cli.mjs tools [--json]                # list endpoint tools (verified list in api-reference)
node scripts/affinity-cli.mjs call <tool> '{"arg":"val"}'   # generic tool call
node scripts/affinity-cli.mjs add --title "T" --description "D" --file f.js
node scripts/affinity-cli.mjs list                          # library scripts
node scripts/affinity-cli.mjs save --title "T" --out f.js   # export library script to disk
node scripts/affinity-cli.mjs search "query"                # SDK hints search
node scripts/affinity-cli.mjs docs [<topic>]                # list / print SDK doc topics
node scripts/affinity-cli.mjs docs-dump <dir>               # (re-)vendor SDK docs; resumable
```

Env overrides: `AFFINITY_MCP_URL` (default `http://localhost:6767`), `AFFINITY_TIMEOUT_MS`
(default 120000 — raise for long batch scripts).

## Known limitations

- `NOT_ALLOWED` from any script command = the user disabled AI / filesystem / networking
  for scripting in Affinity settings — ask them to enable what's needed.
- Script filesystem access is **Desktop-only** (`app.userDesktopPath`); no network from
  script code. Prefer `render` for verification over script-side exports.
- Library scripts **cannot be deleted** through the endpoint — only from the Scripts panel.
- Setting the current spread clears the selection; set it only when actually switching.
- Endpoint sessions can die during long batches (POST → HTTP 404) — just re-run; each CLI
  invocation is a fresh session (the preamble gate is handled automatically).
- If the SDK docs seem stale after an Affinity update, re-run
  `docs-dump references/sdk-docs` and refresh the api-reference digest.
- Fallback if the endpoint route is ever unavailable: macOS GUI automation
  (System Events keystrokes/menus) works but is brittle and unverifiable — use it only for
  trivial one-shot actions, never for document editing.
