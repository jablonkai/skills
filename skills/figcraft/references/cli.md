# figcraft-cli 0.11.2 reference

Verified on macOS with `figcraft-cli 0.11.2` (`~/.local/bin/figcraft-cli`) and
`FigCraft.app 0.11.2` (`ai.storyteller.figcraft`). `figcraft-cli --help` is the vendor
reference; the `docs/cli.md` / `docs/mcp.md` it mentions are not shipped in the bundle.

## Contents
- [Subcommands](#subcommands)
- [File formats](#file-formats)
- [export in detail](#export-in-detail)
- [run in detail](#run-in-detail)
- [Common flags](#common-flags)

## Subcommands

| Command | What it does |
|---|---|
| `info FILE [--json]` | pages, top-level frames (id, name, type, size), node/style/variable/image counts, `notes` (import losses), `missingFonts` |
| `export FILE -o OUT [--format F] [--scale N] [--page NAME] [--node ID\|NAME] [--bleed L] [--crop-marks] [--bleed-marks] [--cmyk]` | images, SVG, PDF or a `.fig` copy |
| `convert IN OUT` | any readable format to `.figcraft`, FigCraft `.json`, `.fig`, `.svg`, images (format from OUT's extension) |
| `render FILE -o OUT.png [--scale N] [--page NAME]` | the whole page with its background, for a look |
| `run SCRIPT.json\|.jsonl [--in FILE] [--out FILE]` | engine commands in a headless session; one JSON line per step |
| `commands [--json] [--filter TEXT]` | the command registry (use `scripts/fc_commands.py`) |
| `mcp [--attach PORT] [--automation-read-root DIR]… [--automation-write-root DIR]…` | MCP server over stdio (use `scripts/fc_session.py`) |
| `plugin publish`, `perf` | plugin upload to a figcraft-server, benchmarks — out of scope |

There is **no `describe` subcommand**: `commands --filter` / `fc_commands.py --id` show a
command's params.

## File formats

- **Read:** `.figcraft` (native), `.json` (FigCraft JSON or Figma REST-API file JSON,
  `GET /v1/files/:key`), `.fig` (best effort), `.svg` (becomes vectors), raster images
  (an image layer).
- **REST JSON:** variables come from `<name>.variables.json` or `variables.json` next to the
  file (the session's `open_file` also takes `variables`). Unsupported node types are
  skipped and listed in `notes`, e.g. `WIDGET layers are not supported and were skipped`.
- **`.fig` write** (`export --format fig`, `convert x.figcraft x.fig`, `save_file x.fig`) is
  experimental: other apps may not open every file.
- **FigCraft JSON** (`convert x.figcraft x.json`) is a readable dump: `nodes` keyed by id
  with `type`, `name`, `parent`, `children`, `characters`, `component` (instances),
  `layout.mode`. Handy for diffing two versions.

## export in detail

- `-o DIR` (no image extension): **one file per top-level layer** of the page, named after
  the layer — main components on the page included.
- `-o FILE.png|jpg|webp|svg` without `--node`: one file of the **whole page**, all
  frames composited. `-o FILE.pdf` without `--node`: one PDF with **a page per top-level
  layer** (main components included — `scripts/fc_export.py --one-pdf` leaves them out).
- `--node ID|NAME`: one layer. With a duplicate name one match is picked silently; prefer
  ids (`info` or `fc_verify.py doc`).
- `--scale N` (raster): 2 → exactly 2× the layer size (390×844 → 780×1688).
- `--page NAME`: another page; an unknown name fails and lists the pages.
- PDF print: `--bleed 3mm` (or `0.125in`, `9pt`, plain points) sets a BleedBox 8.5 pt
  outside the TrimBox (= the layer size in pt, 1 px = 1 pt); `--crop-marks` /
  `--bleed-marks` enlarge the MediaBox for the marks; `--cmyk` writes CMYK colour.
- SVG: text is outlined by default; the session's `export` takes `svgOutlineText: false`
  to keep `<text>`, and `svgIdAttribute: true` for layer names as ids.
- Existing outputs are **overwritten without warning**.

## run in detail

- The script is a JSON array (or JSON lines) of `{"command": id, "params": {...}}`.
- `{"$step": n}` anywhere in params is step n's result id (zero-based);
  `{"$step": n, "field": "…"}` picks another field. A string like `"$0.id"` is rejected.
- `command.batch {"commands": [...]}` groups steps into one undo step, with the same refs.
- The first failing step rolls the whole script back and exits 1; nothing is written.
- Without `--in` it starts from a new file; `--out` saves (format from extension).
- Ids in a fresh document start at 2 (the page is 1), but don't hard-code them.

## Common flags

- `--no-system-fonts` (or `FIGCRAFT_NO_SYSTEM_FONTS=1`): only the built-in fonts (Inter,
  Lato, Liberation, Carlito, Caladea, Merriweather, BIZ UD …) — renders that match on every
  machine.
- `--automation-read-root DIR` / `--automation-write-root DIR`: confine one run; see
  [security.md](security.md).
