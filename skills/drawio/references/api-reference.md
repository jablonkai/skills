# draw.io live API reference

Everything here was run against **draw.io desktop 31.5.2** through
[drawio-eval.mjs](../scripts/drawio-eval.mjs). Scripts run in the editor window's
renderer, so the whole draw.io JavaScript runtime (mxGraph plus draw.io's `EditorUi`,
`Graph`, `Editor`) is available — the `D` helpers are a thin layer over it.

## Contents

- [Scope inside a script](#scope-inside-a-script)
- [D helpers](#d-helpers)
- [Raw mxGraph / EditorUi calls](#raw-mxgraph--editorui-calls)
- [Menu actions](#menu-actions)
- [Layouts](#layouts)
- [Gotchas](#gotchas)

## Scope inside a script

The file (or `-c` string) becomes the body of an `async` function:

| Name | What it is |
|------|------------|
| `ui` | the running `App` (subclass of `EditorUi`) for this window |
| `graph` | `ui.editor.graph` — the `Graph` (an `mxGraph`) of the current page |
| `model` | `graph.getModel()` — the `mxGraphModel` |
| `D` | helper object below |
| `ARGS` | extra command-line arguments after the script path, as strings |

A file can instead be an ES module — `export default async function ({ ui, graph,
model, D, ARGS }) { … }` — which is called with the same names; its return value is
printed. Use that form for scripts kept on disk (it passes `node --check`).

`return` a JSON-serialisable value to print it. Cells are not serialisable — return
`D.describe(cell)`, ids, or `D.dump()`. A thrown error comes back as
`{"ok": false, "error": "..."}` with exit code 1.

## D helpers

**Inspection**

| Call | Returns |
|------|---------|
| `D.info()` | `{file, path, modified, pages, page, vertices, edges, selected, dialog}` — `dialog` is the text of an open modal, or `null` |
| `D.dump()` | every vertex/edge of the current page as `{id, kind, label, style, parent?, x, y, w, h}` or `{…, source, target}` |
| `D.describe(c)` | one cell in that shape |
| `D.cell(id)` | the `mxCell` (passes cells through unchanged) |
| `D.cells(filter?)` | all vertices and edges, optionally filtered by `c => bool` |
| `D.find(textOrRegex)` | cells whose label contains the text / matches the regex |
| `D.label(c)` | the displayed label string |

**Building** — every helper accepts a cell or an id wherever it takes a cell.

| Call | Notes |
|------|-------|
| `D.batch(fn)` | runs `fn` inside one model update → one undo step, one repaint. Wrap multi-cell builds in it. |
| `D.vertex(label, style?, {id, x, y, w, h, parent}?)` | defaults: 120×60 at 0,0, rounded box. `parent` = container id; x/y are then relative to it. |
| `D.edge(src, tgt, label?, style?, {id, parent}?)` | default style is orthogonal. |
| `D.setLabel(c, text)` | labels are HTML when the style has `html=1` — escape `<`/`&` in plain text. |
| `D.setStyle(cells, key, value)` | sets one style key on one or many cells; `value = null` removes the key. |
| `D.move(c, x, y)`, `D.resize(c, w, h)` | geometry edits, undoable. |
| `D.resetEdges(edges?)` | undoes what a layout left on edges (all by default): waypoints, `exit*`/`entry*` anchors, label offsets, ELK's `noEdgeStyle=1`; sets them orthogonal. Call it after moving cells a layout placed. |
| `D.column(mainIds, {spacing, gap}?)` | straightens a top-to-bottom flowchart after a layout — see [Layouts](#layouts). Returns the ids it placed in the side column. |
| `D.remove(cells)` | removes cells and their connected edges. |
| `D.clear()` | empties the current page — every layer's content; the layers stay. |
| `D.select(cells)` | selects in the UI so the user sees what changed. |
| `D.undo()`, `D.redo()` | the editor's undo stack. |

**XML**

| Call | Notes |
|------|-------|
| `D.getXml()` | current page as pretty `<mxGraphModel>` |
| `D.fileXml()` | whole file as uncompressed `<mxfile>` (all pages) |
| `D.setXml(xml)` | replaces the current page. Accepts `<mxGraphModel>`, bare `<root>`, or `<mxfile>` (first page, compressed or not). Keeps your ids. One undo step. |
| `D.importXml(xml, dx?, dy?)` | adds an `<mxGraphModel>` fragment to the page, **re-assigning ids**; returns the new ids. |

**Layout, view, pages, save**

| Call | Notes |
|------|-------|
| `await D.layout(spec)` | see [Layouts](#layouts). Asynchronous — always `await` it before reading positions or saving. Rejects on an unknown spec, a layout error (and closes draw.io's error dialog), or a dialog already open. |
| `D.fit()` | zoom the window to the diagram. |
| `D.pages()` | `[{index, name, current}]` |
| `D.addPage(name)` | appends and switches to it; returns its index. |
| `D.selectPage(indexOrName)`, `D.renamePage(name)` | `renamePage` renames the current page without a dialog (draw.io's own `ui.renamePage` opens one). |
| `await D.save()` | saves to the file's own path and resolves with it once written; throws for an Untitled window, or if a dialog is open or appears. |

## Raw mxGraph / EditorUi calls

Useful beyond the helpers (all verified):

```js
graph.alignCells(mxConstants.ALIGN_LEFT, cells);      // also ALIGN_CENTER/RIGHT/TOP/MIDDLE/BOTTOM
graph.distributeCells(true, cells);                   // true = horizontal
graph.setAttributeForCell(cell, 'owner', 'team-a');   // custom data (Edit Data…); label stays
graph.setLinkForCell(cell, 'https://example.com');
graph.setTooltipForCell(cell, 'text');
graph.getCellStyle(cell);                             // resolved style object
graph.updateCellSize(cell);                           // autosize to label
graph.orderCells(false, cells);                       // bring to front (true = back)
graph.groupCells(null, 10, cells);                    // group with 10px border
model.setTerminal(edge, newTarget, false);            // reconnect edge target (true = source)
const g = edge.geometry.clone(); g.points = [new mxPoint(300, 40)]; model.setGeometry(edge, g); // waypoints
ui.importCsv(csvText, () => {});                      // Arrange ▸ Insert ▸ Advanced ▸ CSV format
ui.currentPage.getName(); ui.pages.length;
```

Wrap mutations in `D.batch(() => …)` so they are a single undo step — except
`distributeCells`, which measures the rendered view: call it *after* the batch that
created the cells, or it silently does nothing.

## Menu actions

`ui.actions.get(name).funct()` runs a menu command on the current selection. Present in
31.5.2: `fitWindow`, `fitPage`, `resetView`, `zoomIn`, `zoomOut`, `selectAll`,
`selectVertices`, `selectEdges`, `autosize`, `toFront`, `toBack`, `group`, `ungroup`,
`duplicate`, `delete`, `deleteAll`, `lockUnlock`, `alignCellsLeft`, `undo`, `redo`.
Avoid actions and `ui` methods that open dialogs (`editStyle`, `editData`, `save` on Untitled, `ui.renamePage`) — a modal
blocks the next script until someone closes it; `ui.hideDialog()` closes it.

## Layouts

`await D.layout(spec)` wraps `ui.executeLayoutSpec(spec, callback)`, the same engine as
the CLI's `--layout`:

- presets: `verticalFlow`, `horizontalFlow`, `verticalTree`, `horizontalTree`,
  `radialTree`, `organic`
- ELK arrays, e.g. `[{"layout":"elkLayered","config":{"elk.direction":"RIGHT"}}]`,
  `elk.spacing.nodeNode`, `elk.layered.spacing.nodeNodeBetweenLayers` — lays out
  containers (swimlanes) and their children together. Pass the array itself or its
  JSON string.

Tree layouts need a single root; use the flow presets or ELK for graphs with cycles.
ELK sizes nodes to their labels, so widths can grow past what you set.

**Keeping a flowchart's main path in one column.** No preset or ELK option does this
reliably — at a decision ELK is as likely to push the "yes" branch sideways as the "no",
and it leaves uneven gaps. Let ELK order the rows, then straighten with `D.column`:

```js
await D.layout([{layout: 'elkLayered', config: {'elk.direction': 'DOWN'}}]);
D.column(['start', 'check', 'inStock', 'pay', 'paid', 'pack', 'ship', 'end']);   // main path, top to bottom
```

It stacks the listed ids in one column (`{spacing: 40}` apart), puts every other
top-level vertex in a column to the right — level with the decision it branches off, or
under the side node it follows — resets the edges (see `D.resetEdges`) and sends edges
that run back up the page (retry, re-check) out and in on the right, clear of the main
column. Plain centre-aligning the main path instead collides with the side branches.
Then look at it: two branches off one decision, or a side path that rejoins the main
path, may still want a hand move.

Hand-placed coordinates are fine for small diagrams (≤ ~8 nodes) — use a 10px grid and
keep 40–60px gaps.

## Gotchas

- **Layout is async.** Reading geometry or saving right after `executeLayoutSpec`
  without awaiting gets the pre-layout positions (everything at 0,0).
- **Only files draw.io was given can be saved.** The desktop app authorises paths the
  user opened (CLI argument at launch, File ▸ Open, Save As). A renderer script cannot
  open or write arbitrary paths — `ui.loadArgs` with a new path fails with
  *path not authorised*. Do not try to work around this; open the file through
  `drawio-start.sh <file>` or ask the user to open it.
- **A running draw.io ignores files passed from outside** (`open -a draw.io f`, or a
  second launch) in this version — the file never shows up. Use the window that is open.
- `ui.editor.modified` and `file.isModified()` are both set after edits; quitting with
  either set prompts the user. Save, or leave it for the user to decide.
- Saving leaves a backup `.$<name>.drawio.bkp` next to the file (draw.io's own
  feature). Leave it, but don't ship it — exclude it when copying outputs or committing.
- The UI may be localised (menus in Hungarian, etc.); action and helper names are not.
- `importXml` renames ids; `setXml` keeps them. Use `setXml` when later scripts address
  cells by id.
