# Security posture

## What the skill runs

The skill runs only `solidcraft-cli` subcommands, headless, as the current user:
`eval`, `run`, `script`, `snapshot`, `commands`, and `mcp --headless` over stdio. Nothing
listens on a network port and no window opens. Designs, parts and renders stay on the
machine.

## File access

`sc_run.py`, `sc_params.py` and `sc_commands.py` start `mcp --headless --param-check
strict`. Each `--allow-path` is one folder of the task: the input's folder and the output
folders. The server also always allows the open design's folder, its own temp folder and
SolidCraft's recovery folder, and refuses any other path. The skill never passes
`--allow-any-path`. The plain `eval`, `run` and `snapshot` subcommands read and write as
the user, so keep their paths to the task's folders.

The scripts never overwrite their input. They refuse existing outputs unless given
`--overwrite`, and they check the input's hash before and after.

## The running app (optional live route)

SolidCraft's own control channel serves a running app to `solidcraft-cli mcp --connect`
and `--connect` on other subcommands. It starts when the app is launched with
`--control PORT`, or with *Settings › Assistant › Let AI agents connect*. These checks
were made against 0.25.0:

- **Loopback only:** it listens on 127.0.0.1 (27878 by default, or the next free port).
- **Token auth:** every request must carry a token made fresh at every start, in
  `~/Library/Application Support/SolidCraft/control/PORT.token` with mode `0600`. A
  request with no token or a wrong one gets `unauthorized`. `mcp --connect` reads the file
  itself when it runs as the same user. Never print, log or pass the token to anyone; it
  stays out of reports and out of prompts to delegate tools. (#32)
- **Browser requests are rejected.** The channel speaks JSON lines, not HTTP. An HTTP
  request, such as a web page's cross-origin `fetch`, gets the connection closed with no
  response, and it could not carry the token anyway. (#17)
- **Stop path:** quitting the app closes the port. A control channel the skill opened
  for a task (`SolidCraft --control PORT`) is quit when the task ends. (#35)

The skill ships **no bridge of its own** and prefers headless work. It uses the live
route only when the user wants changes made in their open design, and asks before any
`open` or `new_design`, because those discard the app's unsaved work.

## Config the app writes

*Settings › Assistant › Make SolidCraft available to AI apps*, and `solidcraft-cli mcp
setup`, add a `solidcraft` MCP entry to the AI clients the app finds: Claude Code, Claude
Desktop, Cursor, OpenCode and others. They back up each file first. The skill never runs
`mcp setup` unless asked, and it mentions this when it finds such an entry. (#22)
