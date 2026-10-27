# filmcraft-cli 0.13.0 reference

`filmcraft-cli [OPTIONS] <SUBCOMMAND> [ARGS]`. It runs a headless FilmCraft engine by
default, or sends commands to the running app with `--bridge`. `filmcraft-cli help` is the
authoritative list. The CLI is a symlink into `~/.local/share/artcraft-cli/filmcraft/`.

## Options

| Option | Meaning |
|---|---|
| `--project p.fcproj` | open this project first (headless) |
| `--demo` | open the built-in demo project |
| `--save` | save back to `--project` at the end. **Without it, edits are discarded** |
| `--save-as p.fcproj` | save to a new path at the end |
| `--bridge 127.0.0.1:PORT` | send commands to an app started with `filmcraft --control PORT` |
| `--data-dir dir` | the data directory holding user export presets (headless) |
| `--keep-going` | `run`: report failing lines and continue |
| `--compact` | one-line JSON |

## Subcommands

| Subcommand | What it does |
|---|---|
| `exec <id> [k=v …]` / `exec <id> '<json>'` | one command. Values parse as JSON when they can (`seconds=3.5`, `items=[1,2]`), otherwise as strings |
| `run <script.jsonl \| ->` | `{"id","params"}` per line, `#` comments allowed, in order. Prints `{"id","line","ok","result"\|"error"}` per line. **The first failing line stops the run and nothing is saved.** No way to pass one line's result to the next: use `fc_run.py` |
| `commands [filter] [--json]` | the registry: id, label, shortcut, param string. In `--json`, `params` is a **string**, not a schema |
| `describe <id>` | one command, plus `enabled` in the current state |
| `inspect [project\|sequence]` | JSON. `project`: bins and items with `item` ids, types, durations, `activeSequence`. `sequence`: settings, tracks, clips, transitions, markers, in/out, playhead. With no argument: `{project, sequence}` |
| `import <file>…` | import media into the project (needs `--save`/`--save-as` to keep) |
| `export <out> [--preset n \| --format f] [--range entire\|inOut\|workArea] [--start s --end s] [--scale f] [--quality q] [--no-audio] [--settings json] [--queue] [--allow-offline] [--gpu-rendering auto\|off]` | exports the **active** sequence and waits. The format is guessed from the extension if neither flag is given |
| `export --list-presets [query]` | presets as JSON: `name, category, format, extension, frameSize, builtin` |
| `render --seconds S --out f.png [--scale 0.5]` | one Program frame of the active sequence |
| `probe <media> [--image-sequence]` | media info: container, duration (ticks), video codec/size/frame rate/colour, audio streams, start timecode |
| `mcp` | MCP server on stdio. Headless, or `--bridge` for the live app. `fc_run.py` uses it to keep one engine session |

## Time

- 254016000000 ticks per second. At 25 fps one frame is 10160640000 ticks. At 23.976
  (24000/1001) it is 10594584000.
- Many commands take `seconds=`, `frame=` or `timecode=` as well as `time=` (ticks). Check
  `describe`: `markers.add` and `timeline.razor` document only `time`.
- `inspect` reports `start`/`duration` in ticks and `startFrame`/`endFrame`/`durationFrames`
  at the sequence rate. `endFrame` is exclusive.
- Sequences count from frame 0 (`00:00:00:00`). Subtract a source list's `01:00:00:00`
  start (`fc_markers.py --sequence-start`).

## Export presets (built in, 0.13.0)

- **Match Source**: Adaptive High, Medium and Low Bitrate (H.264 at the sequence size).
- **Web & Social**: High Quality 1080p HD and 2160p 4K, YouTube 1080p Full HD and 2160p 4K
  Ultra HD, Vimeo 1080p and 2160p, Social Vertical 1080×1920. All are **fixed frame size**.
- **Broadcast**: Apple ProRes 422 HQ, 422, 422 LT, 422 Proxy, 4444, 4444 with Alpha and
  4444 XQ. Avid DNxHR HQ, SQ and LB. APV 422-10 and 422-12. MXF OP1a DNxHR HQ, ProRes 422
  HQ and H.264. MXF OP-Atom DNxHR (Avid).
- **Image Sequence**: PNG, TIFF, BMP, JPEG, Targa, DPX and OpenEXR.
- **Animated GIF**: 640×360. **Audio Only**: WAV 16 and 24-bit, AIFF, AAC 320 kbps, FLAC.

User presets live in the app's data directory (`--data-dir`) and appear in
`--list-presets` with `builtin: false`.

## Exit status

`0` success. `1` a command failed, or export/render drew offline media without
`--allow-offline`. `2` usage error. An unknown preset name exits 1 with
`no export preset named …`.

## MCP tools (`filmcraft-cli mcp`)

`command_run {id, params}`, `command_batch {steps, stop_on_error}`, `command_list`,
`doc_inspect`, `project_inspect`, `sequence_inspect`, `media_import`, `render_frame`.
With `--bridge`, `ui_*` tools (click, drag, key, type, screenshot) also drive the window.
