# photocraft-cli reference (0.17.0)

Verified against `photocraft-cli 0.17.0 (b8c3f3aa8, 2026-10-28)`. Every subcommand prints
its own help with `photocraft-cli <sub> --help`; a flag the subcommand doesn't take is
an error. The CLI is the trusted local route: unlike `serve`, MCP and the desktop
control port, it may use ordinary filesystem paths.

## Contents
- [run](#run) · [info](#info) · [convert](#convert) · [batch](#batch) · [droplet](#droplet)
- [commands](#commands) · [serve](#serve) · [mcp](#mcp) · [Formats and quality](#formats-and-quality)

## run

```sh
photocraft-cli run (<file> | --new '<file.new params>') \
  --cmd <id> [--params '<json>'] [--cmd <id> [--params …]]… \
  [--out <file> | --in-place] [--format <ext>] [--quality 1-100] [<format flags>]
```

The format flags, shared by `run`, `convert` and `batch`: `--tiff-layers`,
`--tiff-compression none|lzw|zip`, `--jpeg-format baseline|optimized|progressive`,
`--tga-bits 24|32`, `--dpx-bits 8|10|12|16`, `--dds-compression none|bc1|bc2|bc3`,
`--dds-mipmaps`.

- Opens the file (or creates one with `file.new` params), runs the commands in order, and
  saves to `--out`. Each `--params` belongs to the `--cmd` before it.
- Prints one JSON line per command: `{"command": id, "result": …}`.
- **No `--out` = nothing is written.** The commands still run and report, so it works as a
  dry run.
- **`--out` equal to the input is refused** (0.16.0+: "is the input file, so the result
  would replace the original") unless `--in-place`. Write to a new path; use
  `--in-place` only when the user asked for an in-place edit.
- On the first failing command it prints `error: …`, exits 1 and writes no output.
- Commands that take a folder or file path (`file.export.layerCompsToFiles`,
  `file.export.layersToFiles`, `file.import.variableDataSets`,
  `file.export.dataSetsAsFiles`, `layer.smartObjects.replaceContents`,
  `file.automate.createDroplet`) work here with absolute paths. `serve` refuses them; it
  uses its scoped `doc.*` methods instead.
- One process per call: state (selection, active layer) does not carry over between
  calls, but the saved file does. Layer ids from `info` on the same file stay valid for
  `run` on that file.

## info

```sh
photocraft-cli info <file> [--compact]
```

The document as JSON: `width`, `height`, `mode` (`Rgb`, `Gray`, …), `depth`,
`resolution`, `layers` (top first; groups nest under `children`), `layerComps`
(`[{id, name}]`), `variables` (`defs`, `dataSets`), `channels`, `selectedLayers`,
`activeLayer`. Each layer has `id`, `name`, `kind` (`Pixel`, `Type`, `Smart Object`,
`Fill`, `Adjustment`, `Group`, `Shape`, …), `visible`, `opacity` (0..1), `fill`,
`blend`, and `bounds` **as `[x, y, width, height]`** (`null` for a full-canvas fill).
Type layers add `text: {text, font, sizePt}`; layers with styles add
`effects: {enabled, items: [{kind: "Drop Shadow", enabled}]}`.

It reads flat images too (PNG/JPEG/WebP/TIFF/EXR), which makes it the cheapest way to
check output dimensions. `scripts/pc_inspect.py layers FILE` prints this as a tree.

## convert

```sh
photocraft-cli convert <in> <out> [--in-place] [--format <ext>] [--quality 1-100] [<format flags>]
```

The format comes from the extension (or `--format`). Layers survive only into
`.pcraft`, `.psd`/`.psb`, and `.tif` with `--tiff-layers`. Anything else is flattened,
with a warning on stderr. An `<out>` that is the input is refused unless `--in-place`.

## batch

```sh
photocraft-cli batch --actions <actions.json | set.atn> [--action <name>] \
  --in <dir> --out <dir> [--format <ext>] [--quality 1-100] [--in-place] [<format flags>]
```

- Applies one action list to every image in `--in` (not recursive; for subfolders run
  `file.automate.batch` with `"includeSubfolders": true`, see
  [recipes.md](recipes.md#folder-batch-resize-sharpen-convert)). The output keeps the
  base name and takes the `--format` extension.
- `--out` equal to `--in` is refused unless `--in-place`. Never use `--in-place` unless the
  user explicitly wants the originals replaced.
- The JSON steps can be `[id, params]` pairs, `{"command": id, "params": {…}}` objects
  or bare ids. They come as a list, or wrapped in `{"actions": …}`, `{"steps": …}` or a
  droplet.
- An Actions **set** (`{"actions": [{"name", "steps"}…]}`, the Actions panel's
  `actions.json`) or a Photoshop **`.atn`** file plays the action named by `--action`. The
  name is required when the set holds more than one action. Steps may call other actions
  of the same set.
- Prints `ok    <in> -> <out>` per file and `N succeeded, M failed`, plus per-file
  warnings (`lossy compression`). Exit status is non-zero
  when any file failed.
- Photoshop `.atn` steps that PhotoCraft cannot play are reported. To see what a set
  contains before running it, use `actions.load {"path": "set.atn"}` in a `run` with no
  `--out`. Its `unsupported` list names the steps that won't play.

## droplet

```sh
photocraft-cli droplet <file.pcdroplet> <file-or-dir>… [--out <dir>]
```

Runs a droplet (File › Automate › Create Droplet) on the given files and folders. Without
`--out` it uses the droplet's own output folder, else `<input folder>/droplet-output`. To
create a droplet, use `run --new '{"width":1,"height":1}' --cmd file.automate.createDroplet --params '{"path":"/abs/x.pcdroplet","steps":[[id,params]…],"format":"jpg","quality":10}'`.
It writes the `.pcdroplet` JSON and, on macOS, a double-clickable `.command` shim next
to it. Droplet `quality` is **0..12** (Photoshop's JPEG scale), not 1..100.

## commands

```sh
photocraft-cli commands [--json] [--filter <text>]
```

The engine registry: 945 commands in 0.17.0. `--filter` matches the id and label. Only
`--json` includes each command's `params` signature (ranges, defaults, enum values), so
use `scripts/pc_inspect.py commands <words…>` to see it. That's the source of truth
whenever this reference and the binary disagree.

## serve

```sh
photocraft-cli serve [--port <port>] [--control-token <64-hex> | --control-token-file <path>] \
  --automation-read-root <dir> --automation-write-root <dir>
```

One headless session that answers JSON lines on stdio (or on `127.0.0.1:<port>`, which
needs a token). See [control-protocol.md](control-protocol.md). Use it through
`scripts/pc_session.py` and `scripts/pc_compose.py`.

## mcp

```sh
photocraft-cli mcp [--bridge 127.0.0.1:<port>] [--control-token-file <path>] \
  [--automation-read-root <dir>] [--automation-write-root <dir>]
```

An MCP server on stdio, headless or bridged to a running app. The skill doesn't need it:
`run`, `serve` and `scripts/pc_live.py` cover the same commands without registering an
MCP client. Mention it only if the user wants PhotoCraft as an MCP server in their own
client. Options that don't fit the mode are errors: the automation roots go with headless
mode only (a bridged app sets its own roots at launch).

## Formats and quality

| Ext | Layers | Notes |
|---|---|---|
| `.pcraft` | yes | native, lossless |
| `.psd` / `.psb` | yes | text, effects, smart objects, layer comps and variables round-trip |
| `.tif` | with `--tiff-layers` | flat by default; `--tiff-compression` |
| `.png` | no | alpha kept |
| `.jpg` | no | `--quality 1-100`, `--jpeg-format` |
| `.webp` | no | **with `--quality` it is lossy (VP8), without it lossless (VP8L)**; written as an extended (VP8X) file that keeps the resolution |
| `.exr`, `.tga`, `.dpx`, `.dds` | no | `--tga-bits`, `--dpx-bits`, `--dds-compression`, `--dds-mipmaps` |

The CLI's `--quality` is 1..100. Engine params named `quality` (`file.saveACopy`,
`file.export.*`, droplets, `file.automate.batch`) use **0..12**.
