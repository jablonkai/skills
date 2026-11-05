# Security and the live app (0.1.2)

## Headless (what this skill uses)

`materialcraft-cli` subcommands read the files named on the command line and write the
outputs named there (`-o`, `save`, `export DIR`, `render OUT`, `file.exportMaterial path`).
Nothing listens on a port. `file.sendToTextureCraft` writes into
`~/Documents/TextureCraft/library` — the user's TextureCraft shelf — so run it only when
asked. `.mcraft` and `.mcmat` files are zips of JSON and images; a package from someone else
can embed bitmaps (`file.importBitmap`) but no code.

## `mcp` and `serve`

- `materialcraft-cli mcp` runs an MCP server on stdio. Headless, it limits file access to
  `--read-root` / `--write-root`; set both to the project folder when wiring it into an
  MCP client.
- `materialcraft-cli serve` speaks JSON lines (`{"id", "method", "params"}`) on stdio, or on
  `127.0.0.1:PORT` with a token when given `--port`. Any local process that has the token
  can drive the engine with your file permissions; keep the token out of logs and stop the
  server (Ctrl-C / kill the process) when done.

## Driving the running app

`materialcraft --control PORT` opens the app's JSON control channel, and
`materialcraft-cli mcp --bridge PORT --token T` forwards MCP calls to it. Use this only when
the user wants their open, unsaved document changed — it edits the live session, including
undo history. Before using it:

1. Confirm the channel binds to `127.0.0.1` and requires the token (start the app yourself
   with a fresh random token; never reuse one from a log or a file you didn't write).
2. Don't expose the port beyond localhost or through a browser page — a web page must not be
   able to reach it (cross-origin requests have to be rejected; check before relying on it).
3. Stop the channel afterwards: quit the app or restart it without `--control`, and stop the
   `mcp --bridge` process.

The headless route covers every task in this skill, so prefer it: work on a copy, show the
result, and let the user open it.
