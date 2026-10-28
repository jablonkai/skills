# Security posture

## What the skill runs

Only `deckcraft-cli` subcommands, headless, as the current user: `info`, `render`,
`convert`, `run`, `commands`, `describe`, and `mcp` over stdio. Nothing listens on a
network port, and no window opens.

## File roots

`deckcraft-cli mcp` takes one `--automation-read-root DIR` and one
`--automation-write-root DIR`. With them, every file a command reads (open, pictures,
audio, video) must lie inside the read root and every file it writes (save, export)
inside the write root, links followed; anything else is refused (`automation path
rejected: outside the write root …`). A kind left out grants none of its access.
`dk_build.py` and `dk_edit.py` always start `mcp` with roots: the common parent of the
input folders (outline, images, source deck) for reading and of the output folders for
writing, and they refuse a root as wide as `/` or `/Users`. The plain `run`, `convert`
and `render` subcommands read and write as the user who started them, so keep their
paths to the task's folders.

## No live-app bridge

The desktop app's control port (`deckcraft --control PORT`, used by `deckcraft-cli app`
and `mcp --connect PORT`) is JSON lines on 127.0.0.1 with **no authentication**: no
token in the app's usage text or the vendor README, and any local process that reaches
the port can drive the app and its file access (`--automation-*-root` don't confine a
running app). That does not meet this repository's bridge rules (token auth,
cross-origin rejection, documented security posture, a stop path — issues #32, #17,
#22, #35), so the skill ships no launcher or client for it and never starts the app with
a control port. If the user runs one themselves, it should be on only while in use and
stopped by quitting the app. Should a later DeckCraft add authentication, a live bridge
can be added as a MINOR version.

## Data handling

Presentations, images and exports stay local; nothing is uploaded.
