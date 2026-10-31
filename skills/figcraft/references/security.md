# Security posture

## What the skill runs

Only `figcraft-cli` subcommands, headless, as the current user: `info`, `export`, `convert`,
`render`, `run`, `commands`, and `mcp` over stdio. Nothing listens on a network port.

## File roots

`figcraft-cli` subcommands and `mcp` take `--automation-read-root DIR` and
`--automation-write-root DIR` (repeatable; the folders must exist). With roots given,
reads are allowed only inside a read or write root and writes only inside a write root;
everything else is refused (`automation path rejected`). Without them a subcommand reads
and writes as the user who started it.

`fc_session.py`, `fc_build.py` and `fc_verify.py doc` always start `mcp` with roots:
`--root` (default the current directory, or the spec's folder for `fc_build.py`) for both,
or separate `--read-root` / `--write-root`. Keep roots as narrow as the task allows — the
folder with the inputs and the output folder, not `$HOME`.

## No live-app bridge

The desktop app can be started with `figcraft --control PORT` and attached to with
`figcraft-cli mcp --attach PORT`. In 0.13.1 that control port still shows **no token or key** option in `--help`:
any local process that can reach the port can drive the app and, within the app's roots,
read and write files. That does not meet this repository's bridge rules (token auth,
cross-origin rejection, a documented stop path), so the skill ships no launcher or
client for it and never starts the app with `--control`.

If the user runs a controlled app themselves, the confinement comes from the roots the
app was started with (`--attach` refuses its own root flags). Should a later FigCraft add
authentication to the control port, a live bridge can be added as a MINOR version.

## Data handling

Designs and fonts stay local; nothing is uploaded. `plugin publish` (sends a plugin to a
figcraft-server) and library publishing commands are outside this skill's scope.
