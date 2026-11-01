# lightcraft-cli reference (0.17.0)

`lightcraft-cli --help` is the authoritative usage, and it is cheap to read. This page
records what the help leaves out, verified by running it.

## Contents

- [run](#run)
- [render](#render)
- [Other subcommands](#other-subcommands)
- [Libraries](#libraries)

## run

```sh
lightcraft-cli run (--library DIR | --demo) [--import PATH]… [--keep-going] \
    COMMAND [key=value | '{json}']… [COMMAND …]…
lightcraft-cli run --library DIR --script steps.jsonl      # or --script - (stdin)
```

- A word without `=` starts the next command. Values are parsed as JSON when they
  parse (`5`, `true`, `[1,2]`, `{"a":1}`), and are strings otherwise. Quote JSON for
  the shell: `ids='[1,2]'`.
- `--script` lines are `{"command": id, "params": {…}}` (or `{"method": …}` for
  control-protocol methods). They run **after** any positional commands, in the same
  process.
- Output is **one JSON line per command**: `{"command", "ok", "result" | "error", "ms"}`.
  The summary `lightcraft-cli: N command(s) failed` goes to stderr.
- Exit status is 1 when any command failed. Without `--keep-going` the run stops at the
  first failure, so later commands produce no reply. Count replies against the steps.
- **One process = one session.** The develop clipboard and other in-memory state are
  gone when the process ends. Library data, edits, ratings and keywords, and the
  selection (`view.json`) are saved.
- `--demo` is a procedural, in-memory library of 24 photos, which is good for trying a
  command. Nothing in it persists.
- `--import PATH` runs `library.import` (mode `add`) before the commands. It can be
  repeated and recurses into folders.
- `--connect [ADDR]` drives a running `LightCraft --control 7980`. That port is
  unauthenticated, and this skill doesn't use it (see
  [gotchas.md](gotchas.md#live-app-port)).

## render

The one-file route: no library is needed, nothing is catalogued, and the original is
never touched.

```sh
lightcraft-cli render IN -o OUT.jpg [--set CONTROL=VALUE]… [--settings FILE] \
    [--preset ID] [--size N] [--quality Q] [--opt KEY=VALUE]…
```

- The format comes from `OUT`'s extension: `.jpg .png .tif .webp .avif .jxl .psd .dng`.
- `--set` is **absolute**, like `develop.set`. There is no auto tone flag, so use `run`
  when "auto" is asked for.
- `--size N` is the long edge, and the default is the full (cropped) size. That differs
  from `app.export`, whose default is 3000.
- `--settings FILE` merges a partial develop-settings JSON, or applies the one preset of
  a `.lcpreset`/XMP preset.
- `--opt` passes any `app.export` option: `--opt colorSpace=displayP3 --opt metadata=none`.
- It prints `lightcraft-cli: wrote OUT (W×H)` and exits 0 on success. Verified: `--set
  light.exposure=0.5 --size 1200 --quality 80` on a 3000 px JPEG wrote a 1200 px WebP.

## Other subcommands

| Subcommand | Use |
|---|---|
| `commands [--json]` | the registry: ids, labels, params, shortcuts |
| `controls [--json]` | develop control ids with ranges and defaults |
| `merge hdr\|panorama\|hdr-panorama\|hdr-batch FILES…` | Photo Merge. It writes `<first>-HDR.dng` etc. **next to the first input**, so copy the inputs to a work folder first, or use `--preview OUT.png` |
| `synth-merge hdr\|panorama -o DIR` | synthetic bracketed DNGs or panorama PNGs, useful as raw test files |
| `snapshot [--library DIR] [--script FILE] -o OUT.png` | the full UI rendered headless to PNG, to show the user a library or develop view |
| `mcp [--compact] [--library DIR]` | the same registry as an MCP server over stdio. It isn't needed when the CLI is available |
| `calibrate`, `denoise-serve` | camera profile fitting and a remote AI-denoise server; out of scope unless asked |

## Libraries

- A library is a folder: `catalog.snap`, `catalog.log`, `catalog.lock`, `view.json`, plus
  previews. `--library DIR` creates it when missing.
- `catalog.lock` allows **one process per library**. A second `run`, or the desktop
  app, on the same library fails at once with exit 1: "This library is already open in
  … (process N). Close it there first." Run the commands for one library one after
  another, never in parallel (background jobs, `xargs -P`). If the app has it open, ask
  the user to close the library, or work on a copy.
- Back up an existing library before bulk edits by copying the folder while nothing
  has it open.
