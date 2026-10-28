# Running app and MCP (SoundCraft 0.14.0)

Use these only when the user wants to watch the edit in SoundCraft or is already working
in the open app. Headless `run`/`script` is the default and needs neither.

## Control port

- Start: `open -n -a SoundCraft --args --control 7979` (or set `SOUNDCRAFT_CONTROL_PORT`).
  Without the flag the app opens no port, and `soundcraft-cli app` fails with
  "cannot reach SoundCraft at 127.0.0.1:7979: Connection refused".
- Call: `soundcraft-cli app --port 7979 ID '{"json":"params"}'`, using the same command ids
  and params as headless, e.g. `soundcraft-cli app transport.status`,
  `soundcraft-cli app session.open '{"path":"/abs/S.scraft"}'`,
  `soundcraft-cli app session.inspect`.
- Stop: `soundcraft-cli app app.quit`. Save first (`session.save`), because quitting this
  way does not prompt and may discard unsaved edits.

## Security posture

- The port listens on **127.0.0.1 only** and speaks newline-delimited JSON over raw TCP,
  not HTTP. A web page can't send it a request, but **there is no token**: any local
  process running as the user can drive the app, including opening and writing files
  anywhere the user can.
- So: open the port only for the task, close it with `app.quit` when done, and don't
  leave it running on a shared machine. This skill ships no bridge of its own.

## MCP server

`soundcraft-cli mcp` exposes the command registry as MCP tools on stdio:

- In-process (no app): `soundcraft-cli mcp --automation-read-root ~/Audio/in
  --automation-write-root ~/Audio/out`. The roots confine every path commands read
  (open, import, presets) or write (save, bounce, export), with symlinks resolved. A kind
  left out grants no access of that kind, so give both.
- Against the app: `soundcraft-cli mcp --connect 7979`. Roots can't be combined with
  `--connect`, so the app's unrestricted file access applies.

Prefer the rooted in-process server when an MCP client, rather than this skill, should
drive SoundCraft.
