# effectcraft-cli 0.18.0

Each invocation runs a headless engine, does its work and exits. `--help` lists everything;
running the app binary would open a window, so don't.

## Global options

| Option | Effect |
|---|---|
| `--project F.ecproj` (or a positional `F.ecproj`) | open that project |
| `--empty` | start from an empty project |
| `--demo` / *(none of the above)* | the bundled demo project — never what you want |
| `--save` | save back to the opened file after the command |
| `--save-as F` | save to a new file (the original stays as it was) |
| `--json` | one compact JSON document on stdout |
| `--gpu` | render on the GPU (headless renders on the CPU by default) |
| `--bridge PORT` | send the command to a running app instead (not used by this skill) |

Errors print `{"error": …}` (with `--json`) and exit 1; usage errors exit 2 before anything
runs. `<comp>` is an id, a name or `-` (active comp); `<layer>` is an id, `#n` (1 = top) or
a name; `<value>` is JSON (`50`, `[960,540]`, `"#ff0000"`) or a bare string.

## Subcommands

| Command | Does |
|---|---|
| `info` | project summary: version, active comp with its layers, project items, renderer |
| `commands [--filter T] [--enabled]` | the registry as text (≈730 lines — filter it, or use `ec_commands.py`) |
| `exec ID [--params JSON]` / `exec --list [--schemas] --json` | one command / the registry as JSON |
| `run ID JSON [ID JSON …]` / `run --args-file F` | several commands in order, one process; no `$N` result references |
| `props COMP LAYER [--flat] [--time S]` | a layer's property tree with paths (`--json` nests groups and names effects) |
| `get COMP LAYER PATH [--time S]` | value at comp time S, `keys[]` (time, compTime, value, in/out interpolation), `expression` |
| `set COMP LAYER PATH VALUE [--time S] [--expression E]` | static value, a keyframe at layer time S (replaces a key already there), or an expression |
| `render-frame [--comp C] [--time S \| --frame N] [--max-side PX \| --scale K] --out F.png [--transparent]` | one PNG |
| `render [--comp C] --out FILE [--format F] …` | a deliverable (below) |
| `render`/`render-frame --template T.ectemplate [--values V.json]` | a template instance; can't combine with `--project`, `--comp`, `--queue` |
| `script FILE.jsx [F.ecproj] \| --eval CODE` | After Effects-style JavaScript (below) |
| `mcp [--autosave] [--automation-read-root D] [--automation-write-root D]` | stdio MCP server (see security.md) |
| `bench …` | timings; not needed for normal work |

## render

```
render --project F --comp C --out FILE --format h264|hevc|av1|prores|webm|png|jpeg|tiff|exr|gif|wav|aiff
       [--start S] [--end S] [--work-area] [--fps N] [--resolution full|half|third|quarter|K]
       [--quality best|draft] [--channels rgb|rgba] [--prores proxy|lt|standard|hq|4444|4444xq]
       [--bitrate KBPS] [--audio auto|on|off] [--jpeg-quality N]
       [--profile main|main10] [--rate-control bitrate|quality] [--video-quality N] [--keyint N]
       [--webm-codec vp9|av1] [--level auto|4.1] [--audio-bitrate KBPS] [--opus-app audio|voice]
       [--progress]      # or: render --queue (render the project's queue)
```

- Alpha: `--format prores --prores 4444 --channels rgba` → ffprobe `prores / 4444 / yuva444p12le`.
  WebM VP9 also carries alpha (`--format webm --channels rgba`). H.264 never does.
- Image sequences: `--out 'dir/f_[#####].png'` writes `f_00000.png…`; the folder must exist.
- `--end` is exclusive: `--start 0 --end 0.2` at 25 fps is 5 frames.
- `--profile`, `--level`, `--rate-control`, `--video-quality`, `--keyint` apply to HEVC / AV1; `--audio-bitrate` and `--opus-app` to WebM Opus audio. Listed in 0.18.0 help; only `--webm-codec vp9` alpha was smoke-tested.
- A relative `--out` is relative to the working directory, not the project.
- `--progress` prints `progress <done> <total> <elapsed> <left>` on stderr.
- Verified: H.264 MP4 5.000 s, ProRes 4444 alpha, PNG sequence.

## script

```sh
effectcraft-cli script build.jsx --save-as out.ecproj          # empty project unless one is given
effectcraft-cli script tweak.jsx in.ecproj --save-as out.ecproj
effectcraft-cli script --eval 'app.project.item(1).numLayers' in.ecproj --json
```

The object model is After Effects': `app.project.items.addComp(name, w, h, pa, dur, fps)`,
`comp.layers.addText(…)`, `layer.property("ADBE Transform Group").property("ADBE Position")
.setValueAtTime(t, v)` (comp time). `app.run(id, params)` calls any registry command, so a
loop over `app.run("layer.newShape", …)` works. `writeLn` output is printed, then the value
of the last expression; an error exits 1 with `file:line:col`. Scripts may read only the
project's folder and may not write files or use the network unless the user enables it in
Preferences ▸ Scripting & Expressions. Wrap edits in `app.beginUndoGroup()` /
`app.endUndoGroup()`; a script that throws keeps what it already did.

## MCP tools used by the scripts

`open_project {new|path}`, `save_project {path}`, `execute_command {command, params}`,
`batch {steps, atomic}` (one undo step, rolled back on failure, `"$N.key"` = step N's result,
1-based), `add_keyframe {layer, path, keys, interpolation, timeBase}`,
`add_effect {layer, effect, values}`, `set_property {layer, path, value|expression}`,
`get_comp`, `get_layer`, `get_property`, `render_frame`, `list_effects {filter}`,
`list_fonts {query}`. Vendor docs: `docs/agents.md` and `docs/mcp.md` in
github.com/storytold/effectcraft.
