---
name: vectorcraft
description: 'Automate VectorCraft, the Illustrator-style vector editor, headless with vectorcraft-cli: build vector artwork (shapes, paths, text, layers, swatches, symbols) on one or more artboards from a spec, edit text and recolour existing .vectorcraft/SVG/AI/PDF files, fill templates from CSV with variables and data sets, export per-artboard PNG at @1x/@2x, SVG with outlined text, multi-page PDF and AI/EPS/DXF, inspect files and lossy imports, and batch-convert folders, all verified by an info read-back and a rendered preview. Use when the user mentions VectorCraft, vectorcraft-cli, a .vectorcraft or .vctemplate file, or wants a logo sheet, icon set, badge set or vector conversion made with VectorCraft: "make a logo sheet in VectorCraft", "convert these .ai files to SVG with VectorCraft", "export every artboard as PNG", "VectorCraftban cseréld le a szöveget". Not for Inkscape or hand-written SVG (inkscape), Affinity (affinity), diagrams (drawio), raster/PSD layer editing (photocraft), or fonts (fontforge).'
summary: "automate VectorCraft headless with vectorcraft-cli — vector art on multiple artboards from a spec, text and colour edits, CSV data-set variants, per-artboard PNG, outlined SVG, multi-page PDF and AI/EPS/DXF export, folder conversion, info read-back verified"
category: design-automation
risk: medium
tags: [vectorcraft, vector, svg, illustrator, artboards, batch, data-sets, headless]
metadata:
  version: "1.0.0"
---

# VectorCraft via vectorcraft-cli

VectorCraft is an Illustrator-style vector editor. Every menu item, tool and dialog is a
command in one engine registry: 811 of them in 0.17.0. The same commands run from the CLI,
from a headless session and in the desktop app. This skill drives them **headless**, so
no window opens, and checks every result by reading the document back. It is verified
against **vectorcraft-cli 0.17.0** and **VectorCraft.app 0.17.0** on macOS. The software
is pre-1.0, so command ids may change. When a pinned id fails, look it up.

```sh
command -v vectorcraft-cli || ls ~/.local/bin/vectorcraft-cli
vectorcraft-cli --version
```

Don't launch the app to read help: `vectorcraft-cli --help` covers the CLI, and running
the app binary opens a window.

## Pick the route

| Task | Route |
|---|---|
| Build artwork on artboards from scratch, then save and export | `scripts/vc_build.py spec.json` |
| Convert one file, or one artboard of it | `vectorcraft-cli convert IN OUT [flags]` |
| Convert a folder (`.ai`/`.eps`/`.pdf` → SVG/PDF/PNG…) | `scripts/vc_batch.py IN OUT --to svg,…` |
| Edit an existing file (text, colours, move, hide, add art) | `scripts/vc_session.py steps.json` |
| One variant per CSV row (badges, cards, name tags) | `scripts/vc_variants.py TEMPLATE CSV OUT` |
| One-shot command chain on a file, ids chained by `"$N.id"` | `vectorcraft-cli run --in F --commands steps.jsonl --export …` |
| What is in a file (artboards, fonts, counts, import warnings) | `vectorcraft-cli info FILE` |

## Scripts

Paths are relative to this skill's directory, and `S=<skill>/scripts`. Call them as
`python3 $S/<script>`. They need Python 3.9+ and the standard library only. Each has a
full `--help`.

- **`vc_commands.py WORD…`** (`--prefix text.`, `--id text.setText`): filtered catalogue
  lookup with each command's params signature. Never dump `vectorcraft-cli commands`:
  it is ~811 entries.
- **`vc_build.py SPEC.json`**: builds from a spec:
  - artboards laid out in a row;
  - swatches and layers;
  - shapes, SVG-data paths, text and symbols, positioned **relative to their artboard**;
  - save, exports (`"artboards": "each"` with `{index}`/`{name}` in the path) and
    per-artboard previews.

  It refuses to overwrite unless given `--overwrite`, and prints the created ids and an
  `info` read-back. Spec example: [recipes.md](references/recipes.md#logo-sheet).
- **`vc_session.py STEPS|-`**: runs one stateful headless session
  (`vectorcraft-cli mcp --headless`). The steps are `open`, `cmd`, `batch`, `find`,
  `inspect`, `export`, `save`, `preview` and `tool`. `"@name:Headline"`,
  `"@text:Spring"` and `"@kind:Type"` in params resolve to the one matching object id.
  It stops with exit 1 at the first error.
- **`vc_batch.py IN OUT --to svg`**: `convert` over a folder. It refuses an OUT inside
  IN, and names stem clashes `<stem>-<srcext>`. Flags: `--outline-text`, `--decimals`,
  `--scale`, `--each-artboard`. It reports every file's `importWarnings`.
- **`vc_variants.py TEMPLATE CSV OUT`**: defines and binds variables
  (`--bind text:Name=@name:Title visibility:Badge=@name:Badge`), loads the CSV as data
  sets, then applies and exports one file per row. The template is never written; use
  `--save-template` for a copy that carries the data sets.
- **`vc_verify.py`** prints JSON and exits 1 on any failed check:
  - `doc FILE --artboards 3 --size 1024x1024 512x512 --min-kind Type=1 --text Title=… --color '#hex' --no-import-warnings --fonts-ok`
  - `files DIR --ext png --count 3 --px 1024x1024 512x512 64x64`
  - `files DIR --ext svg --no-svg-text --max-decimals 2`
  - `files DIR --ext pdf --pdf-pages 3`
  - `hash DIR [--compare manifest.json]`

## Workflow

1. **Inspect first.** Run `vectorcraft-cli info` on any input: artboards, object kinds,
   fonts (`status` other than `exact` means substituted) and `warnings`, which are the
   import warnings. For edits, list the objects with
   `{"find": {"kind": "Type"}}` / `{"inspect": {"depth": 3}}` steps. Look up any command
   you haven't used this session with `vc_commands.py`. Unknown ids fail, and some
   unknown params are ignored silently.
2. **Never touch the originals.** Write to new paths. Before a batch, snapshot the
   inputs with `vc_verify.py hash IN > manifest.json`. `convert IN IN` and `save` without
   a path overwrite the source.
3. **Do the work** with the route from the table. Use absolute paths in session steps
   (the scripts absolutize `path`/`folder` keys). File access is confined to the
   session's `--root`, so pick a root that holds both inputs and outputs.
4. **Read back** with `vc_verify.py`:
   - `doc`: artboard count and sizes, kinds, text by object name, colours used, fonts,
     import warnings;
   - `files`: count, pixel sizes, SVG `<text>` and decimals, PDF pages;
   - `hash --compare`: inputs unchanged.
5. **Look at it.** Open a rendered PNG (`vc_build.py`'s `preview`, a `preview` step, or
   the exported PNG) and view the image. Overlaps, clipped text and wrong colours only
   show up there.
6. **Report** the outputs, what was verified, and any import or export warnings.
   Name lossy imports explicitly: an EPS read from its preview, or `.ai` editing data
   that was skipped.

## The traps that cost the most (details in [gotchas.md](references/gotchas.md))

- **New art gets a 1 pt black stroke.** The default appearance is a white fill and a
  black stroke, as in Illustrator. Pass `"stroke": "none"` to `draw_shape`/`draw_path`
  (`vc_build.py` does this by default) or set it with `paint.setStroke {"none": true}`.
- **Ids come from `find`, never from guessing.** The ids of an imported SVG or AI
  follow its structure (layers and groups take ids too). Use `@name:`/`@text:` refs or
  a `find` step. An untitled text object's *name is its content*, so after `setText`
  find it by the new text. An explicit name (`object.setProps {"name"}`, an SVG `id`)
  sticks.
- **Coordinates are document points, y down.** The origin is the first artboard's
  top-left. Further artboards sit to its right, so offset by the artboard's `x`.
  `text.create` `y` is the **baseline**. `justify: "center"` centres point type on `x`.
- **`run` chains by step number, not by lookup.** `"$1.id"` in a later step's params
  is step 1's result id (steps count from 0, `file.new` included). Steps can come from a
  JSON/JSONL file or stdin with `--commands`. `run` without `--export` saves nothing.
  Anything that has to *find* an object first (by name or text) belongs in
  `vc_session.py`.
- **Exports pick by extension:**
  - PNG/SVG write the **first** artboard unless you pass `artboard`.
  - PDF and `.ai` write every artboard as a page.
  - SVG outlines text only with `outlineText: true` (session) or `--outline-text`
    (convert).
  - PDF outlines text with `options.advanced.outlineText`.
- **Recolour by colour, not by object:** `select.all`, then
  `recolor.apply {"map": {"#e4572e": "#1b998b"}}`. It changes every use, fills and
  strokes. For a global swatch, `swatch.edit {"name", "color"}` recolours everything
  linked to it.
- **Lossy imports:** `info`'s `warnings` (`importWarnings` in `convert`) say what didn't
  come in. `convert` refuses to write over such an input unless `--replace-lossy` is
  given. Never pass that without the user's consent.

## Common jobs

- **Logo sheet or icon set:** write a spec → `vc_build.py` → `vc_verify.py doc` + `files` →
  view the previews. [recipes.md](references/recipes.md#logo-sheet)
- **Folder conversion:** `vc_verify.py hash IN > m.json` →
  `vc_batch.py IN OUT --to svg --outline-text --decimals 2` → `vc_verify.py files OUT …` →
  `hash IN --compare m.json`.
- **Edit text and recolour an SVG/AI:** `vc_session.py` with `open`, `text.setText`,
  `recolor.apply`, then `export` (SVG, and PNG at `scale: 2`).
  [recipes.md](references/recipes.md#edit-text-and-recolour)
- **CSV variants:** `vc_variants.py`. [recipes.md](references/recipes.md#csv-variants)

## References

- [references/cli.md](references/cli.md): every subcommand and flag, the formats, and
  verified behaviour.
- [references/commands.md](references/commands.md): pinned 0.17.0 command ids by task,
  with key params.
- [references/recipes.md](references/recipes.md): worked specs and step files for each
  job above.
- [references/gotchas.md](references/gotchas.md): silent failures and surprises.
- [references/security.md](references/security.md): file roots, the session, and why
  there is no live-app bridge.
