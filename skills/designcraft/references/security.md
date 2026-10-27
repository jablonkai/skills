# Security posture

## What the skill runs

Only `designcraft-cli` subcommands, headless, as the current user: `run`, `script`,
`commands`, `describe`, `validate-pdf`, and `mcp` over stdio. Nothing listens on a
network port, and no window opens.

## File roots

`designcraft-cli mcp` takes `--automation-read-root DIR` and `--automation-write-root DIR`
(repeatable). With roots, every file a command reads (open, placed images, data sources,
the links a document names) must lie inside a read root and every file it writes (save,
exports, package) inside a write root; anything else is refused (`automation path
rejected: outside the write root …`). A kind left out grants none of its access.
`dc_build.py` and `dc_merge.py` always start `mcp` with roots: the spec/template folder and
the image, text and data folders for reading, the output folders for writing. The plain
`run` and `script` subcommands read and write as the user who started them, so keep their
paths to the task's folders.

## No live-app bridge

The desktop app's control port (`designcraft --control PORT`, used by `designcraft-cli
app` and `script`/`mcp --connect PORT`) is JSON lines on 127.0.0.1 with **no
authentication** — the vendor's control-protocol doc says so. It rejects HTTP request
lines, so a web page's cross-origin `fetch` can't inject commands, but any local process
that reaches the port can drive the app and its file access (`--automation-*-root` don't
confine a running app). That does not meet this repository's bridge rules (token auth,
cross-origin rejection, a documented stop path), so the skill ships no launcher or client
for it and never starts the app with a control port. If the user runs one themselves, it
should be on only while in use and stopped by quitting the app. Should a later DesignCraft
add authentication, a live bridge can be added as a MINOR version.

## Data handling

Documents, images, data files and exports stay local; nothing is uploaded.
