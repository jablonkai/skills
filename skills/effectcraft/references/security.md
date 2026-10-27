# Security posture

## What the skill runs

Only `effectcraft-cli` subcommands, headless, as the current user: `info`, `exec`, `run`,
`props`, `get`, `set`, `render`, `render-frame`, `script`, and `mcp` over stdio. Nothing
listens on a network port.

## File roots

`effectcraft-cli mcp` takes `--automation-read-root DIR` and `--automation-write-root DIR`
(repeatable). With roots, reads are allowed only inside a read or write root and writes
only inside a write root; everything else is refused (`outside the automation roots`).
`ec_build.py` always starts `mcp` with roots: the spec's folder and the footage folders
for reading, the output folders for writing. The plain subcommands (`set`, `render`…)
read and write as the user who started them, so keep their paths to the task's folders.

## Scripts

`effectcraft-cli script` runs JavaScript with the After Effects object model. By default
scripts may read only the project's folder and may not write files or use the network;
the user can lift that in Preferences ▸ Scripting & Expressions. Don't ask them to, and
read any `.jsx` you didn't write before running it.

## No live-app bridge

The desktop app's control port (`--control PORT`, used by `effectcraft-cli --bridge PORT`
and `mcp --bridge PORT`) is TCP on 127.0.0.1 with **no authentication**. It refuses
browser-style requests, but any local process that can reach the port can drive the app
and its file access. That does not meet this repository's bridge rules (token auth,
cross-origin rejection, a documented stop path), so the skill ships no launcher or client
for it and never starts the app with a control port. If the user runs one themselves,
it should be on only while in use and stopped by quitting the app. Should a later
EffectCraft add authentication, a live bridge can be added as a MINOR version.

## Data handling

Projects, footage and renders stay local; nothing is uploaded.
