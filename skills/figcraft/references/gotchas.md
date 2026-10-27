# Gotchas (FigCraft 0.11.2)

Each was reproduced with figcraft-cli 0.11.2.

## Building

- **`"$0.id"` is rejected; `{"$step": 0}` works.** `run`, `batch` and `command.batch` all
  take `{"$step": n}` (zero-based) for step n's created id. The error for the string form
  is `` `parent` must be a node id ``.
- **A failing step rolls everything back.** `run` and `batch` are all-or-nothing: nothing
  is created or written, and the error names the step. Fix that step and rerun the whole
  script.
- **Defaults:** frames are white (`#FFFFFF`), rectangles light grey (`#D9D9D9`), text is
  Inter 12 px black and hugs its content. Set `fontSize`, `fill` and widths explicitly.
- **Auto layout overrides x/y.** Children of a layout frame are positioned by order, `gap`
  and `padding`; use `sizingH: "fill"` for full-width children and `crossAlign: "center"`
  to centre text vertically in a horizontal row.
- **`node.create` without x/y puts top-level layers at 0,0**, on top of each other.
  `fc_build.py` lays them out in a row; in raw scripts give each frame an `x`.
- **Instances copy the main's text.** Override it on the instance's own text child; editing
  the main changes every instance that has no override.
- **`style.apply` takes the style name or id** (`S:1`); paint styles need
  `target: "fill"|"stroke"` when both could apply.

## Finding layers

- **Names repeat.** Screens commonly share `Headline`, `Title`, `Label`. A bare
  `@name:Headline` fails with the candidates; scope it (`@name:Home/Headline`).
  `export --node NAME` with a duplicate name **silently picks one** — export by id.
- **`info` shows only top-level layers.** Child layers and text need
  `fc_verify.py doc` or a session `find` / `node` step.

## Exporting

- **`-o DIR` writes every top-level layer**, including main components that sit on the
  page. `-o FILE.png` without `--node` writes the **whole page** composited into one image.
  `-o FILE.pdf` and `file.exportFramesPdf` write one page per top-level layer — the
  component becomes an extra page. `fc_export.py` exports screens only.
- **Fixed widths don't follow the frame.** A child with `width: 342` stays 342 when the
  screen is resized to 430; `sizingH: "fill"` makes it 382. Resizing a screen to another
  device size is the usual test of a layout.
- **Overwrites are silent** for `export`, `convert` and `render`. `convert IN IN` rewrites
  the source. Write to a new folder.
- **Scale is exact:** `--scale 2` on a 390×844 frame gives 780×1688.
- **Output folders must exist** for `save_file` / `export` in a session
  (`No such file or directory`); `fc_session.py` and `fc_build.py` create them.
- **SVG text is outlined by default.** For live `<text>`, use the session export with
  `svgOutlineText: false`.
- **PDF sizes are in points, 1 px = 1 pt.** 3 mm bleed = 8.5 pt per side.

## Importing

- **`.fig` is best effort.** Anything skipped is listed in `info`'s `notes` and the
  session's `opened.warnings`. Report it, also when the list is empty.
- **Notes live on the source only.** `info` on the converted `.figcraft` shows empty
  `notes`; read them from the `.fig`/JSON before (or while) converting and put them in
  the report — afterwards nothing records what was lost.
- **REST JSON drops widgets** (`WIDGET layers are not supported and were skipped`) and
  reads variables only from a sibling `variables.json`.
- **Missing fonts substitute silently** in renders. Check `missingFonts`; use
  `--no-system-fonts` for renders that must match across machines.

## Session

- **Relative paths resolve against the current directory**, not `--root`; a path outside
  the roots is refused with `automation path rejected`.
- **`inspect_document` defaults to depth 4** and truncates large trees; `fc_verify.py` and
  `find` ask for depth 50 on all pages.
