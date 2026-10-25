---
name: cadcraft
description: 'Draft, edit, inspect and convert 2D CAD drawings with CADCraft, the AutoCAD-style drafting app, headless through cadcraft-cli: layers, filleted polylines, circles, text, hatches, dimensions and attributed title blocks from a JSON spec, JSON commands or .scr scripts; title-block fill, text replace, layer moves and purge on existing DXF/DWG; DXF↔DWG and PDF/SVG/PNG export with explicit framing; hash-checked folder batches; results read back with info and ezdxf. Use when the user mentions CADCraft or cadcraft-cli, or asks for an AutoCAD-like job in it: "draw a dimensioned mounting plate in CADCraft", "convert these DWGs to PDF with CADCraft", "fill the title block", "run this .scr script". Not for QCAD or a DXF job that does not name CADCraft (qcad), 3D or parametric parts and STEP/STL (freecad), CSG solids (brl-cad), PCBs (kicad), vector art (vectorcraft, inkscape) or diagrams (drawio).'
summary: "draft and convert 2D CAD drawings headless with cadcraft-cli — layers, filleted polylines, hatches, dimensions and attributed title blocks from a JSON spec, JSON commands or .scr scripts, DXF/DWG/PDF/SVG/PNG export with explicit framing, folder batches, info and ezdxf read-back verified"
category: cad
compatibility: "Built for cadcraft-cli 0.13.0 and CADCraft.app 0.13.0 on macOS; pre-1.0, so command ids may change."
risk: medium
tags: [cadcraft, cad, dxf, dwg, autocad, drafting, title-block, headless]
metadata:
  version: "1.0.1"
---

# CADCraft via cadcraft-cli

CADCraft is an AutoCAD-style 2D drafting app. Its ~440 commands (LINE, PLINE, DIMLINEAR,
BLOCK, ATTEDIT, LAYER, PLOT…) live in one engine that `cadcraft-cli` runs **headless**:
no window opens and nothing listens on a port. This skill drives that engine and reads
every result back. Verified against **cadcraft-cli 0.13.0** and **CADCraft.app 0.13.0** on
macOS. The software is pre-1.0, so command ids may change: when a pinned id fails, look
it up with `cc_commands.py`.

## Setup

```sh
command -v cadcraft-cli || ls ~/.local/bin/cadcraft-cli
cadcraft-cli --version
python3 -c 'import ezdxf' 2>/dev/null || { python3 -m venv .venv-dxf && .venv-dxf/bin/pip -q install ezdxf; }
```

`ezdxf` is needed only for `cc_verify.py`'s independent geometry checks; run that script
with whichever interpreter has it. Never start the app to read help, and never pass
`--connect`/`--launch` to `cadcraft-cli mcp` ([security.md](references/security.md)).

## Pick the route

| Task | Route |
|---|---|
| New drawing (or additions to one) from a description | spec → `scripts/cc_build.py spec.json` |
| Add a title block / fill its attributes | `scripts/cc_titleblock.py add|fill|list` |
| Convert one file | `cadcraft-cli convert IN OUT --view extents` (or `--window`) |
| Convert a folder | `scripts/cc_batch.py IN OUT --to pdf,svg` |
| Multi-step edit that needs handles from an earlier step | `scripts/cc_session.py steps.json` |
| Short command chain, at most the last handle needed | `cadcraft-cli run IN --cmd 'id {json}' … --save OUT` |
| What is in a drawing | `cadcraft-cli info FILE` (+ a `query`/`find_text` session step) |

## Scripts

`S=<this skill>/scripts`; call `python3 $S/<script>`. Python 3.9+, stdlib only (ezdxf
optional). Each has a full `--help`.

- **`cc_commands.py WORD… | --id ID | --prefix layer.`**: catalogue lookup with the full
  params signature. Never dump `cadcraft-cli commands` (441 entries).
- **`cc_build.py SPEC`**: one session: new metric drawing (or `base`), layers, `draw`
  items (`{"layer", "cmd", "params", "as"}`; `"@name"` = handle of an earlier `as`),
  optional `titleBlock`, save, then each export through `convert` with explicit framing.
  Refuses to overwrite without `--overwrite`. Spec: [recipes.md](references/recipes.md#mounting-plate).
- **`cc_titleblock.py add IN OUT --at X,Y --size W,H TAG=VALUE…`** builds frame +
  attdefs, makes the block from exactly those handles and inserts it with the values.
  **`fill IN OUT [--block TB] TAG=VALUE…`** sets values on every reference carrying the
  tags (fails on an unknown tag). **`list IN`** prints all attribute values.
- **`cc_session.py STEPS|-`**: steps `new`, `open`, `cmd`, `line`, `script`, `inspect`,
  `query`, `find_text`, `save`, `render`. `"$N"` = step N's handle (0-based), `"$N.handles"`
  its list (after a `query`: the handles of the entities it returned). Paths must be under `--root` (default cwd); an opened input is never saved over.
- **`cc_batch.py IN OUT --to pdf,svg,png,dxf,dwg`**: refuses OUT inside IN, renames stem
  clashes `<stem>-<ext>`, writes `manifest.json` with every input's SHA-256 before/after,
  exits 1 if any input changed.
- **`cc_verify.py`** (JSON, exit 1 on any failed check):
  - `doc F --layer GEOM DIM --count Circle=4 'Dimension>=3' --type-on Circle=GEOM --on-layer A-ANNO=0 --attr TITLE=… --text …`
  - ezdxf: `doc F --units mm --circles 3=4 --size GEOM=100x60`
  - `files DIR --ext png --count 5 --px 2400x1600` · `--ext pdf --pdf-pages 1` · `--ext svg`
  - `hash DIR > m.json`, later `hash DIR --compare m.json`

## Workflow

1. **Inspect first.** `cadcraft-cli info` on every input: layers, counts by type, blocks,
   extents. For edits, list what you'll touch (`query` by type/layer, `find_text`,
   `cc_titleblock.py list`). Look up any command you haven't used with `cc_commands.py`.
2. **Never write over an input.** Save to a new path. `convert IN IN` and `save` to the
   opened path overwrite silently; the scripts refuse it. Batch: snapshot hashes first.
3. **Units are a decision.** A new drawing follows MEASUREINIT — **imperial (inches)** out
   of the box — unless `--metric` / `{"new": {"metric": true}}`; pass it explicitly every
   time. `cc_build.py` defaults to metric. mm work in an inch
   drawing scales wrong in every other CAD app.
4. **Do the work** with the route above. Prefer JSON commands with complete params over
   `.scr` scripts: a script line that leaves a prompt open silently swallows the next
   lines — TEXT without a following blank line turns the rest of the script into text
   ([scr-syntax.md](references/scr-syntax.md)). After any script, check `info` counts
   against what the script should have drawn.
5. **Read back** with `cc_verify.py doc` (layers, counts, layer membership, attributes,
   texts; ezdxf for units, radii, sizes) and `files` for exports.
6. **Look at it.** Export or `render` a PNG and view it: overlapping dimensions, text in
   the wrong place and a blank framing only show there.
7. **Report** the outputs, what was verified (with the numbers), and anything skipped.

## The traps that cost the most ([gotchas.md](references/gotchas.md))

- **Framing is explicit, always.** `run --export` uses the *current view* when anything
  changed it (ZOOM, view.set), `convert` fits the extents. Pass `--view extents` or
  `--window x0,y0,x1,y1` every time. PNG is always 2400×1600, model space.
- **Text height defaults to 2.5 in a metric drawing but 0.2 in an imperial one** (and
  whatever TEXTSIZE an opened file carries) for `text`/`attdef`. Always pass `height`
  (cc_build adds `textHeight`, default 2.5 mm).
- **"interactive": true does not mean unusable.** It means the command also prompts in
  the GUI. `line`, `circle`, `rectang`, `dimlinear`, `block`… run headless with full JSON.
- **`run` is one-shot and all-or-nothing.** Steps run in command-line order; the first
  error exits 1 and nothing is saved. A param value of exactly `"{last}"` becomes the
  last handle an earlier `--cmd` returned (`circle` → `select {"handles":["{last}"]}`);
  anything older needs `cc_session.py`. The selection carries over too: `qselect {layer}`
  → `laymch {layer}` works in one `run`.
- **`layer.new` fails on an existing layer** — use `layer.set` / `layer.current`.
- **`block` needs a selection** (`select {handles}`), and its default `keep: "convert"`
  already inserts one reference; use `keep: "delete"` + `insert {attribs}` to place it
  with values. Never select by window in a full drawing — it swallows neighbours.
- **Attribute edits:** `attedit {handle, values}` (handle of the Insert, from `query`).
  An unknown tag is not an error: check `unknownTags` in the result. `-attedit` needs a literal `find` string, `"*"` changes nothing.
- **Fillet arcs on a polyline aren't circles:** `dimradius {handle}` rejects them; use
  `{center, point}`. For an associative overall size use `dimlinear {object, at}`.

## Common jobs

- **Dimensioned part:** spec → `cc_build.py` → `cc_verify.py doc … --units mm --circles …
  --size GEOM=WxH` → view the PNG. [recipes.md](references/recipes.md#mounting-plate)
- **Folder DWG/DXF → PDF + SVG:** `cc_batch.py IN OUT --to pdf,svg` →
  `cc_verify.py files OUT --ext pdf --count N` and `--ext svg` → manifest shows inputs
  unchanged. [recipes.md](references/recipes.md#batch-conversion)
- **Title block + layer move + windowed PNG:** `cc_titleblock.py add`, `qselect`/`laymch`
  run, `convert --window`. [recipes.md](references/recipes.md#title-block-and-layer-move)

## References

- [cli.md](references/cli.md): subcommands, flags, framing, exit codes, the MCP tools.
- [commands.md](references/commands.md): pinned 0.13.0 command ids by task with params.
- [scr-syntax.md](references/scr-syntax.md): what works in `.scr` scripts and what breaks.
- [formats.md](references/formats.md): read/write matrix, DXF/DWG versions, image output.
- [recipes.md](references/recipes.md): worked specs and command chains for the jobs above.
- [gotchas.md](references/gotchas.md): silent failures and surprises, with evidence.
- [security.md](references/security.md): what runs, and why there is no live-app bridge.
