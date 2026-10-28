# cadcraft-cli 0.14.0 reference

Universal binary at `~/.local/bin/cadcraft-cli`. `cadcraft-cli --version` prints
`cadcraft-cli 0.14.0`. `--help`/`-h`/`help` print the usage to stdout and exit 0; bad
usage prints it and exits 1. Since 0.14.0 every subcommand has
its own `--help` (`cadcraft-cli run --help` lists the flags and the `{last}` chaining).

## Subcommands

| Command | Does |
|---|---|
| `info [--compact] FILE.dxf|dwg|svg|svgz` | JSON summary: `counts` by type, `entityCount`, `extents` `[[x0,y0],[x1,y1]]`, `layers` (name, color, linetype, on/frozen/locked), `blocks`, `layouts`, `dimStyles`, `textStyles`, `linetypes`, `view`, `skipped` (sections not read). No units field — use ezdxf `$INSUNITS`. |
| `convert IN OUT [FRAMING]` | IN: DXF/DWG/SVG/SVGZ (an SVG imports as polylines). OUT by extension: dxf, dwg, dwt, svg, png, pdf. Writes over OUT without asking; OUT == IN exits 2 unless `--in-place`. An image output warns on stderr about entities it can't draw — report those. |
| `run [FILE | --sample | --metric] [--script TEXT] [--script-file F.scr] [--cmd 'id {json}']… [--in-place] [--save OUT] [--export OUT.(png|svg|pdf)] [FRAMING]` | Opens FILE (or a new drawing: MEASUREINIT units, imperial out of the box; `--metric` for mm, `--sample` for a demo), runs scripts and commands **in command-line order**, then saves/exports. A `--cmd` param value of exactly `"{last}"` (at any depth, e.g. `"handles":["{last}"]`) becomes the last handle an earlier `--cmd` returned; with none the run fails. |
| `commands [FILTER]` | JSON list: `id`, `aliases`, `label`, `menu`, `params` (signature text), `interactive`, `enabled`, `shortcut`. Use `scripts/cc_commands.py`. |
| `sample (bracket|floorplan) OUT.(dxf|dwg|svg|png)` | Demo drawings. `bracket`: 46 entities, hatches, dims, notes MText, no blocks. `floorplan`: 16 entities on A-WALL/A-DOOR/A-GLAZ/A-ANNO…, 2 texts (LIVING ROOM, BEDROOM), no blocks. |
| `mcp [--connect HOST:PORT [--lazy] [--launch]]` | MCP server on stdio. Without `--connect`: headless backend in-process (what the scripts use). With it: bridge to the app's token-authenticated control port — not used by this skill ([security.md](security.md)). |
| `perf [N | FILE]` | Performance diagnostics only. |

Settings flags on `info`/`convert`/`run`/`mcp`: `--config-dir DIR` (env
`CADCRAFT_CONFIG_DIR`; plotter configs live in `plotters/`), `--fontalt FONT`,
`--fontfallback A,B` (envs `CADCRAFT_FONTALT`, `CADCRAFT_FONTFALLBACK`).

## Framing (png, svg, pdf; always model space)

- `--view extents` — fit the drawing extents.
- `--view current` — the current view (last ZOOM/PAN/`view.set`; a freshly opened
  drawing's view is its extents + 10 %).
- `--window x0,y0,x1,y1` — that rectangle in drawing units (x0<x1, y0<y1), centred and
  scaled without distortion.
- Default differs: `convert` fits extents; `run --export` uses the current view **if the
  commands changed it**, else extents. Always pass one explicitly.
- `--window`/`--view` without an image output is an error.
- PNG is 2400×1600 RGBA on a dark background with layer colours, like the app's model
  space. PDF via `convert`/`--export`/`save` is one page, white, landscape: A4 for a
  metric drawing, Letter for an imperial one.
  For paper size, scale or a layout use the `exportpdf`/`plot` command.

## Output and exit codes

- `run`: each `--cmd` prints its JSON result as one line on **stdout** (commands that
  return nothing print nothing — e.g. `layer.new`); script echo (`Command: LINE`,
  prompts) goes to **stderr**; `wrote OUT (N bytes)` per file.
- First failing command or script line (`unknown command`, `invalid parameters for
  \`x\`: …`) → message, **exit 1, nothing saved**.
- `info`/`run` on a missing file: `invalid parameters for \`open\`: … No such file`, exit 1.

## MCP tools (headless session, used by `cc_session.py`)

| Tool | Args | Returns |
|---|---|---|
| `new_drawing` | `metric?` | `{index, title}` |
| `open` | `path` | `{entities, index, warnings}` |
| `execute` | `command`, `params` | the command's JSON (`{handle}` for most draw commands) |
| `command_line` | `text` | command-line state (`output`, `prompt`, `running`) |
| `script` | `text` | `{output, state}` |
| `list_commands` | `filter?` | as `commands` |
| `inspect_drawing` | `entities?`, `limit?` | as `info`, plus `entities` with handles |
| `query_entities` | `type?` (`Insert` and `Block Reference` both match block references), `layer?`, `selected?` (the current selection), `window?`, `crossing?`, `limit?`, `offset?` | `{count, returned, entities}` — `returned < count` means pass a larger `limit` |
| `find_text` | `contains?`, `layer?`, `window?`, `limit?`, `offset?` | texts, MText, attributes (with `tag`), leaders |
| `render` | `path?`, `window?`, `width?`, `height?`, `fit?` | PNG (default 1600×1000) |
| `save` | `path?` | DXF/DWG by extension (`version` 2018); .pdf/.svg/.png export instead |
| `cancel` | — | Escape |

Errors come back as `isError: true` with a text message; the session stays usable.
