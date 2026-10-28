# deckcraft-cli 0.11.1

`deckcraft-cli help SUBCOMMAND` explains any subcommand; this page is what the help
leaves implicit. Slides are 960 × 540 pt by default (16:9); positions are points, x right,
y down, a rect is `[x, y, w, h]`.

## Subcommands

| Subcommand | What it does |
|---|---|
| `info FILE` | JSON: `slides` (index, id, title, layout, shapes count, notes, hidden, transition, animations), `layouts`, `theme`, `fonts`, `sections`, `media`, `slideSize`. The read-back oracle. |
| `render FILE [--slide N \| --all] [--scale S] [--edit] [--transparent] OUT` | PNG of slide N (0-based, default 0), or `--all` into folder OUT as `slide-01.png …`. `--scale` is px per point (2 → 1920×1080). `--edit` also draws placeholder prompts. |
| `render-transition FILE --slide N --t 0.25,0.5 [--width PX] OUT.png` | Frames of the transition *into* slide N; several times write `OUT-t0.250.png` … |
| `convert IN OUT` | By OUT's extension: `.deckcraft`, `.pptx`, `.pdf`, `.md`/`.txt` (outline), `.png`/`.jpg` (first slide), `.gif` (one frame per slide). Anything else is refused. |
| `run [--in FILE \| --sample] --cmd ID=JSON … [--save OUT] [--export OUT [--export-params JSON]] [--print]` | Commands in order on one presentation, then save and/or export. |
| `commands [FILTER]` | One line per command: `id — Label: {params} → answer`. ~35 KB unfiltered; use `scripts/dk_commands.py`. |
| `describe ID` | One command's parameters, where it lives in the app, and how `run` calls it. |
| `app [--port P] ID [JSON]` / `app --method M [JSON]` | Sends one request to an app started with `deckcraft --control P` (not used by this skill; see security.md). |
| `mcp [--sample] [--automation-read-root DIR] [--automation-write-root DIR] [--connect PORT]` | MCP server on stdio. |
| `bench FILE`, `links`, `--version` | Timing, project links, version. |

## `run` in detail

- Without `--in` or `--sample`, `run` starts from a **new presentation with one empty
  title slide** (default theme). `file.new {theme?, template?, size?, blank?}` inside the
  run replaces it with another new one — still with one starter slide.
- `--cmd ID=JSON`: quote the JSON for the shell; an id with no params is just `ID`.
  Build long JSON with `python3 -c 'import json; print(json.dumps(…))'` or use the
  scripts, so quotes and newlines (`\n` = new paragraph, `\t` at line start = bullet
  level) survive.
- `--print` prints `ID → answer` per command (inserted shape ids, `slide.inspect` JSON,
  `text.replace` counts). Parse the answer with `line.split(" → ", 1)[1]`.
- **One failing command stops the run and nothing is saved** (exit 1, `deckcraft-cli:
  invalid parameters for \`text.set\`: no such shape`).
- `--save OUT`: `.deckcraft` keeps everything; `.pptx`, `.pdf` and `.md` are written as
  `convert` writes them. `--save` and `--export` can both be given.
- `--export OUT`: `.png`/`.jpg` = **the current slide**; `.pdf`, `.pptx`, `.gif` = the
  deck. `--export-params` takes `file.export` options as one JSON object.

## file.export options (also `--export-params`, MCP `export`)

| Option | Values |
|---|---|
| `format` | `png`, `jpeg`, `pptx`, `deckcraft`, `outline`, `rtf`, `pdf`, `gif` (else from the extension) |
| `slide` / `all` | png/jpeg: one slide (0-based) or every slide (`all: true` writes `NAME1.png`, `NAME2.png` … next to `path`) |
| `scale`, `dpi` | px per point for images |
| `layout` | pdf: `slides` (default), `notes` (notes pages, Letter portrait by default), `handouts` (`perPage` 1/2/3/4/6/9) |
| `paper`, `orientation` | pdf notes/handouts: `letter`, `a4`, `legal`, `a3`; `portrait`/`landscape` |
| `slides` | a list of **0-based** indices `[0, 2]`, or a **1-based** range string `"1-3,5"` |
| `includeHidden` | include hidden slides (left out by default) |
| `textLayer`, `frame`, `transparentBackground` | pdf text layer; slide frame; png without background |
| `width`, `secondsPerSlide`, `loop` | gif: px 16–3840 or `small`/`medium`/`large`/`extraLarge`; 0.1–600 s (default 5); loop forever (default) |

## MCP tools (`deckcraft-cli mcp`)

`run_command {command, params}` runs any registry command; `batch {commands:[{command,
params}], keepGoing?}` runs several. Convenience tools: `new_presentation {theme?,
blank?}`, `open_presentation {path}`, `save_presentation {path}` (format by extension),
`export {…file.export options}`, `inspect_document`, `inspect_slide {index}`,
`render_slide {slide, scale}` (returns the PNG), `add_slide`, `go_to_slide`, `add_shape`,
`add_text_box`, `set_text`, `insert_picture`, `insert_table`, `insert_chart`, `select`,
`list_commands {filter}`. `screenshot` and `call_app` work only with `--connect`.

- `--automation-read-root DIR` / `--automation-write-root DIR` confine every file read
  (open, pictures, media) and write (save, export). **Each may be given once.** A root
  left out grants none of that access; a path outside is refused with `automation path
  rejected: outside the write root …`. Roots conflict with `--connect`.
- The scripts in this skill speak MCP through `dklib.Session` so one presentation stays
  open across many commands — shape ids from `slide.inspect` stay valid — and file
  access stays in the task's folders.
