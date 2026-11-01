# Security posture

## What the skill runs

Everything is local and headless:

- **One-shot CLI calls:** `cadcraft-cli run`, `convert`, `info`, `sample`, `commands`.
  They read and write only the paths on their command line.
- **A session:** `cadcraft-cli mcp` with no `--connect`. It is a child process on stdio,
  opens **no network port**, and lives only as long as the script that started it
  (closing its stdin ends it — that is the stop path, #35). `cclib.Session` checks the
  server's instructions say "headless backend" and refuses otherwise.
- **No app process.** `/Applications/CADCraft.app` is never launched.

CADCraft 0.16.0 has no file-root confinement of its own (unlike VectorCraft's automation
roots), so the scripts confine themselves. (It only limits xref and data-link paths
*stored in a drawing* to this computer or the drawing's share — see
[gotchas.md](gotchas.md); paths passed to commands are used as given.)

- `cc_session.py` rejects any path outside `--root` (default: the current directory)
  and refuses to save over a drawing it opened.
- `cc_build.py`, `cc_titleblock.py` and `cc_batch.py` refuse to overwrite existing
  outputs without `--overwrite`, and never write to their inputs.
- `cc_batch.py` refuses an output folder inside the input folder and hashes every input
  before and after.

The `lisp` and `appload` commands run arbitrary AutoLISP inside the engine. Don't run
LISP the user didn't write or ask for.

## Why there is no live-app bridge

The app can be remote-controlled: started with `--control PORT` (or
`CADCRAFT_CONTROL_PORT`), it listens for commands, and
`cadcraft-cli mcp --connect 127.0.0.1:PORT [--lazy] [--launch]` bridges to it
(`--launch` starts the app). The port binds `127.0.0.1` and speaks JSON lines, with no
file roots: an authenticated client can run any of the ~450 commands, including LISP and
file writes. It closes a connection at the first line that is not a JSON request — an
HTTP request line included — and bounds idle time, blocked writes and queued requests.

Since **0.12.0** (storytold/cadcraft#1844) the server issues a 256-bit per-session token
at startup, stores it owner-only (`0600`) as `cadcraft-control-<port>.token` in the
per-user runtime directory, and rejects any request without it before dispatch; the
`--connect` bridge reads that file itself. This was taken from the release notes and the
PR, not reproduced here — the skill never starts the app.

This repo's bridge rules require token authentication (#32), rejection of cross-origin
requests (#17), a documented posture (#22, this file) and a stop path (#35). 0.12.0 makes
#32 achievable, but the skill still ships no launcher and never passes
`--connect`/`--launch`: every job it covers runs headless, and a live bridge would need
its own stop path and tests against a running app.

If the user explicitly wants to watch edits happen live, tell them: the port is open
until they quit the app, it binds 127.0.0.1 only, and anyone who can read their token
file can drive it. Leave starting it to them. A bridge script would be a MINOR version
bump of this skill.
