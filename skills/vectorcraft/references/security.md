# Security posture

## What the skill runs

Everything runs locally and headless. There are three kinds of process:

- **One-shot CLI calls:** `vectorcraft-cli run`, `convert`, `info` and `commands`.
  They read and write only the paths on their command line.
- **A session:** `vectorcraft-cli mcp --headless --automation-read-root R --automation-write-root W`.
  - It is a child process on stdio. It opens **no network port** and lives only as
    long as the script that started it, which closes its stdin on exit.
  - Every file the session's commands read must be under `R`, and every file they
    write must be under `W`. Links are followed before the check.
  - A root left out grants no access of that kind. Each flag may be given more than
    once; the scripts pass one of each.
  - The scripts default both roots to the narrowest directory that holds the inputs
    and outputs: the current directory for `vc_session.py`, or a root given with
    `--root`/`--read-root`/`--write-root`.
- **No app process.** The desktop app is never launched.

## Why there is no live-app bridge

VectorCraft can expose a running app for remote control:

- `vectorcraft --control PORT` (or `VECTORCRAFT_CONTROL_PORT`) starts a localhost
  JSON-lines server.
- `vectorcraft-cli mcp --connect ADDR` bridges to it.
- Plain `vectorcraft-cli mcp` without `--headless` tries `127.0.0.1:7979` first.

In 0.17.0 that server still **has no authentication**: any local process that can reach the
port can run any of the 811 commands. The app does offer `--automation-read-root` and
`--automation-write-root` to confine its file access, but that is not authentication.

This repo's bridge rules require four things of a live bridge:

- token authentication (#32);
- rejection of cross-origin or browser-originated requests (#17);
- a documented posture (#22);
- an explicit stop path (#35).

The first two can't be met on top of an unauthenticated port, so this skill ships no
launcher for it. It also always passes `--headless`, so a port someone else opened is
never used by accident.

If the user explicitly wants to watch edits live, tell them all of the following:

- the port is unauthenticated while it is open;
- the app should be started with both automation roots set to a scratch folder;
- the port should be closed by quitting the app when they're done.

Leave starting it to them. A future VectorCraft with token auth would justify a
`vc_live.py` (a MINOR version bump of this skill).

## Data handling

- The originals are never written:
  - `vc_batch.py` refuses an output folder inside the input folder.
  - `vc_build.py`, `vc_variants.py` and `vc_batch.py` refuse to overwrite existing
    outputs without `--overwrite`.
  - `vc_variants.py` refuses `--save-template` equal to the template.
- `--replace-lossy` (convert writing over a lossily read input) needs the user's
  explicit consent.
- Nothing is sent over the network.
