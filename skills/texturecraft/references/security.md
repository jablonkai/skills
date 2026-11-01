# Security posture

## What the skill runs

The skill runs only `texturecraft-cli` subcommands, headless, as the current user: `info`,
`commands`, `run`, `batch`, `bake`, `export`, `render` and `new`. They read and write files.
Nothing listens on a network port, no window opens, and projects, textures and renders stay
on the machine. The skill ships **no bridge of its own**.

## File access

The plain subcommands read and write any path the user can, so keep their paths inside
the task's folders. The scripts never write to their input. They refuse existing outputs
(and non-empty export folders) unless given `--overwrite`, and `tc_build.py` checks the
input's hash before and after. `bake.highPoly.add` and `bake.cage.set` *read* the given
mesh and copy it into the project.

## `serve` and `mcp` (not used by the skill)

These were checked against 0.2.0:

- `texturecraft-cli serve` speaks JSON lines on stdio. `serve --port P` listens on
  **127.0.0.1 only** and writes a fresh token to
  `$TMPDIR/texturecraft-control-P.token` with mode `0600`. Every request before
  `{"method": "auth", "params": {"token": …}}` gets `authenticate first`. The token file
  stays after the server stops; it opens nothing once the port is closed. (#32)
- A plain HTTP request, which is what a web page's cross-origin `fetch` sends, gets no HTTP
  response, so a browser page can neither read the channel nor present the token. (#17)
- `--read-root` and `--write-root` limit `serve` and headless `mcp` to those folders. Give
  them only the task's folders when a client is attached.
- `texturecraft-cli mcp --bridge PORT [--token T]` relays MCP to a running app started
  with `texturecraft --control PORT`. Use it only when the user asks to change their
  open project, and never print, log or pass the token anywhere: keep it out of reports
  and out of prompts to delegate tools.
- Stop path: kill the `serve` process, or quit the app, to close the port. Shut down a
  server the skill started for a task when the task ends. (#35)

## Config the app may write

The vendor README registers TextureCraft with Claude Code through
`claude mcp add texturecraft -- texturecraft-cli mcp --read-root … --write-root …`. The
skill never adds or changes MCP client config unless asked, and it mentions any
`texturecraft` MCP entry it finds. (#22)
