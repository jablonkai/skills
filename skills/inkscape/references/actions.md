# Inkscape actions and export flags

Verified on **Inkscape 1.4.4** (macOS). Action names and argument formats changed
between 1.0, 1.2 and 1.4. Before using anything not listed here, confirm it exists:

```bash
bash scripts/inkscape.sh --actions-grep 'trace|simplify'
```

## How action chains run

```bash
inkscape IN.svg --actions="action1:arg;action2:a,b;export-filename:OUT;export-do"
```

- Actions run in order against **one open document** and **one selection**. Every
  action that edits something acts on the current selection. `select-*` adds to it,
  and `select-clear` empties it.
- Arguments follow a `:`. Multiple values are separated by `,`. Paths therefore must
  not contain `;` or `,`, but spaces are fine.
- Nothing is saved until an `export-do`. `export-filename:X` (the extension picks the
  format) plus `export-do` writes X. `export-overwrite;export-do` writes back to the
  input file.
- Export settings (`export-dpi`, `export-id`, `export-area-*`, …) **persist** for
  the rest of the chain. Set them again before every `export-do` that needs
  something different.
- Failures are printed but the **exit code stays 0**. Check stderr for
  `Did not find`, `Select … at least`, `expected argument format`, `was not found`.
- Many files in one process: `inkscape --shell` reads one action line per input line.
  Use `file-open:PATH;…;export-do;file-close` for each file, then `quit`
  (see `scripts/ink-batch.sh`).

## Selection

| Action | Argument | Notes |
|--------|----------|-------|
| `select-by-id` | `id1,id2,…` | Unknown IDs print `Did not find object with id` |
| `select-by-element` | `rect`, `text`, `path`, `image`, … | Also matches inside groups |
| `select-by-selector` | CSS selector, e.g. `.badge`, `rect` | |
| `select-all` | `all` / `layers` / `no-layers` / `groups` / `no-groups` | The default `no-groups` skips groups |
| `select-clear` | — | |
| `unselect-by-id` | `id,…` | |
| `select-list` | — | Prints the selection to stdout, for debugging a chain |
| `delete-selection` | — | `delete` also works but also targets nodes and text |

## Objects and transforms

| Action | Argument | Result (tested) |
|--------|----------|-----------------|
| `object-to-path` | — | Shapes and **text** → `<path>`. Text becomes outlines |
| `object-stroke-to-path` | — | Returns a group with the same id holding fill and stroke paths |
| `transform-translate` | `dx,dy` | Moves by user units |
| `transform-rotate` | `deg` | Rotates about the bounding-box centre |
| `transform-scale` | `factor` | Scales about the centre; stroke width scales too |
| `transform-remove` | — | Removes `transform` attributes |
| `object-align` | `hcenter page`, `left top drawing`, … | Relative to `last\|first\|biggest\|smallest\|page\|drawing\|selection` |
| `object-flip-horizontal` / `-vertical` | — | |
| `object-rotate-90-cw` / `-ccw` | — | |
| `object-set-attribute` | `name,value` | e.g. `opacity,0.5` |
| `object-set-property` | `name,value` | Sets a CSS property in `style`, e.g. `fill,#123456`. Use one call per property: a full `style` string cannot be passed to `object-set-attribute` because its `;` ends the action |
| `selection-group` / `selection-ungroup` | — | |
| `selection-top` / `-bottom` / `-raise` / `-lower` | — | z-order |
| `duplicate` / `clone` / `clone-unlink` | — | |
| `object-set-clip` / `object-set-mask` | — | The top object is the clip or mask |

## Paths

| Action | Keeps id/style of | Notes |
|--------|-------------------|-------|
| `path-union` | bottom object | Needs ≥ 2 paths or shapes; shapes are converted |
| `path-difference` | bottom object | bottom minus top |
| `path-intersection` | bottom object | |
| `path-exclusion` | bottom object | XOR |
| `path-division` / `path-cut` | — | Produce several new paths |
| `path-combine` | **top** object | One path with several subpaths |
| `path-break-apart` | — | The inverse of combine |
| `path-simplify` | same object | Fewer nodes. The threshold comes from preferences (default 0.002) and takes no argument |
| `path-fill-between-paths`, `path-flatten`, `path-fracture`, `path-split` | — | 1.4 additions |

Boolean operations **drop presentation attributes** (`fill="red"`) and keep only
`style=""`. Author shapes with `style="fill:…"`, or set it first with
`object-set-property:fill,#…`.

## Text

| Action | Notes |
|--------|-------|
| `object-to-path` on a `<text>` | Converts to outlines: one `<path>` that keeps the text's `id` and an `aria-label` with the string |
| `text-put-on-path` | Select the text and the path |
| `text-flow-into-frame` | Select the text and the frame shape |
| `text-convert-to-regular`, `text-unflow`, `text-unkern` | |

## Bitmap trace

```
object-trace:SCANS,SMOOTH,STACK,REMOVE_BG,SPECKLES,SMOOTH_CORNERS,OPTIMIZE
object-trace:8,true,true,true,2,1.0,0.2
```

- All 7 arguments are required. `--action-list` shows no help for this action; the
  format only appears in the error message.
- It traces colour by quantizing to `SCANS` colours; there is no brightness or
  edge-detection mode through this action.
- **Select the `<image>` itself.** Opening a PNG directly (`inkscape in.png`) wraps it
  in a group, so use `select-by-element:image`.
- The result is a new group of paths, which becomes the selection. The source
  `<image>` is **kept**: remove it with
  `select-clear;select-by-element:image;delete-selection`.
- Tracing an `<image>` in an SVG works with a relative `xlink:href` resolved against
  the SVG's folder.

## Querying

```bash
inkscape --query-all in.svg          # id,x,y,width,height for every object
inkscape --query-id=disc --query-width in.svg
```

The values are in user units (px at 96 DPI) and give the visual bounding box,
including stroke.

## Export: CLI flags (equivalent actions in brackets)

| Flag | Meaning |
|------|---------|
| `-o, --export-filename=F` [`export-filename`] | Output; the extension picks the format |
| `--export-type=png,pdf` [`export-type`] | Several formats from one run, named after the input |
| `-d, --export-dpi=N` [`export-dpi`] | PNG resolution (96 = 1 px per user unit) |
| `--export-width=PX` / `--export-height=PX` | Fixed pixel size; the other side scales |
| `-i, --export-id=ID[;ID]` + `-j, --export-id-only` | Export one object, layer or group; hide the rest |
| `-C/-D, --export-area-page/-drawing` | The page (default) or the drawing's bounding box. Only one per run: they persist and override each other |
| `--export-area=x0:y0:x1:y1` | An explicit area in user units. Use the `=` form: `-a 0:0:48:48` fails to parse |
| `--export-margin=N` | Margin in user units (px for PNG) |
| `-b, --export-background=COLOR` + `-y, --export-background-opacity=1` | PNG background |
| `-T, --export-text-to-path` | Outline text in PDF, EPS, PS or SVG |
| `-l, --export-plain-svg` [`export-plain-svg`] | Strip `inkscape:`/`sodipodi:` metadata |
| `--export-page=all\|N` | Multi-page documents; PNG defaults to page 1 |
| `--export-pdf-version=1.4\|1.5`, `--export-ps-level=2\|3` | |
| `--export-overwrite` [`export-overwrite`] | Write back to the input |

Formats written: png, svg, pdf, eps, ps, emf, wmf (plus xaml, pov, odg, sif and
others through output extensions).
