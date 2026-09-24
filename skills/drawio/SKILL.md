---
name: drawio
description: 'Create and edit draw.io (diagrams.net) diagrams — either by remote-controlling the running draw.io desktop app with JavaScript over its DevTools port (shapes appear live in the window the user is looking at, then get laid out, saved and exported), or, when live control is not possible, by writing .drawio XML files directly and rendering them headless with the draw.io CLI. Covers flowcharts, architecture and network diagrams, swimlanes, sequence, UML and ER diagrams, multi-page files, ELK auto-layout, Mermaid/CSV to draw.io conversion, and PNG/SVG/PDF export. Use whenever the user mentions draw.io, diagrams.net, .drawio files, or asks to draw, sketch or diagram an architecture, process, flow, org chart or data model as an editable diagram — even if they do not name the tool. Also covers Hungarian: "rajzold meg draw.io-ban", "csinálj egy diagramot", "folyamatábra", "architektúra ábra", "vezéreld a draw.io-t", "exportáld PNG-be". Not for charts of numeric data (use a plotting library) or Obsidian .canvas files.'
summary: "remote-control the draw.io desktop app with JavaScript over its DevTools port — live shape building, ELK auto-layout, pages, save — or author .drawio XML directly and export PNG/SVG/PDF or convert Mermaid/CSV with the headless CLI"
category: design-automation
risk: medium
tags:
    - drawio
    - diagrams
    - flowchart
    - architecture
    - scripting
---

# draw.io Control

draw.io desktop (`/Applications/draw.io.app`) is an Electron app whose editor is the
same JavaScript runtime as diagrams.net (mxGraph + `EditorUi`). Started with a
DevTools port, it can be driven live: a script runs **inside the editor window**, the
user watches the shapes appear, and every change lands on the normal undo stack. When
that isn't possible, draw.io files are plain XML and the app's CLI renders them
headless. Everything here was run against **draw.io 31.4.5**; needs Node 22+.

- [scripts/drawio-start.sh](scripts/drawio-start.sh) — launch draw.io with the control
  port, opening or creating a `.drawio` file.
- [scripts/drawio-eval.mjs](scripts/drawio-eval.mjs) — run a script (or `-c 'code'`)
  in the live window; `--ping` for status, `--screenshot out.png` to see the window.
- [scripts/drawio-helpers.js](scripts/drawio-helpers.js) — the `D` helper object
  injected before every script.
- [scripts/drawio-export.sh](scripts/drawio-export.sh) — headless export (png, svg,
  pdf, jpg, html) and Mermaid/CSV/Visio → `.drawio` conversion; no port needed.
- [scripts/example-architecture.mjs](scripts/example-architecture.mjs) — a complete
  build → layout → verify → save script to copy the shape from.
- [references/api-reference.md](references/api-reference.md) — the verified live API:
  all `D` helpers, raw mxGraph calls, menu actions, layouts, gotchas. **Read it before
  writing anything past the cheatsheet below.**
- [references/file-format.md](references/file-format.md) — `.drawio` XML, style keys,
  shape names, palette, hand-layout rules. Needed for file mode, and for style strings
  in live mode.

## Choose the mode

| Situation | Mode |
|-----------|------|
| User wants to see/edit the diagram in draw.io, or refers to "the diagram I have open" | **Live** |
| Diagram should land in a repo or docs folder, or the user just wants the file/PNG | **File** — faster, no window pops up |
| draw.io is running without the port and the user doesn't want to restart it | **File**, then they open the result |
| draw.io isn't installed (`/Applications/draw.io.app` missing) | **File**, suggest `brew install --cask drawio` for rendering |
| Source is Mermaid, CSV, or `.vsdx` | `drawio-export.sh in.mmd out.drawio` first, then either mode |

## Live mode

1. **Check the connection**: `node scripts/drawio-eval.mjs --ping` → `{"ok": true,
   "windows": [...], "info": {file, path, modified, pages, …}}`. Exit code 3 means
   nothing is listening:

   - **draw.io not running** → `bash scripts/drawio-start.sh path/to/diagram.drawio`.
     It creates the file if missing and opens a window on the user's screen — say so.
     Always pass a file: an Untitled window cannot be saved by script.
   - **draw.io running without the port** (start script exits 3) → the port can only be
     set at launch, and quitting would put the user's open work at risk. Ask them to
     save and quit draw.io themselves, then start it again. Never kill it.
   - **Port is up but the wanted file isn't among `windows`** → a running draw.io
     ignores files handed to it from outside. Ask the user to open it via File ▸ Open,
     or use the window that is open.

2. **Write a build script** to the scratchpad and run it:
   `node scripts/drawio-eval.mjs /path/build.js [args…]`. The file is either a plain
   function body (`ui`, `graph`, `model`, `D`, `ARGS` in scope, `return` the result) or
   an ES module with `export default async function ({ D, ARGS })` like the example.
   With several windows open, add `--window <title substring>`. Wrap cell creation in
   `D.batch(...)` — one undo step, one repaint.

3. **Lay out**: for more than a handful of nodes, create them at 0,0 and
   `await D.layout('horizontalFlow')` (or an ELK array) instead of computing
   coordinates. It is asynchronous — await it before reading positions or saving.
   Layouts run in one direction, so a long linear pipeline (8+ steps in a chain) comes
   out as one very wide row: use `'verticalFlow'`, or place stages by hand in two or
   three rows (one container per stage) — whichever reads at 100% zoom.

4. **Verify** — read back structure, then look:
   `node scripts/drawio-eval.mjs -c 'return D.dump()'` for ids, geometry and edge
   endpoints; then `--screenshot /tmp/x.png` (the window as the user sees it) or save
   and `drawio-export.sh file.drawio /tmp/x.png -b 10` (the diagram alone). Look at the
   image — overlaps, clipped labels and crossing edges only show up visually.

5. **Save**: `return await D.save()` writes the open file to its own path. Then export
   if asked: `bash scripts/drawio-export.sh diagram.drawio diagram.png -b 10 -s 2`.

### Cheatsheet

```js
D.clear();                                        // empty the current page
D.batch(() => {
  D.vertex('Web client', 'rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;', {id: 'web'});
  D.vertex('Backend', 'swimlane;startSize=26;html=1;', {id: 'be', w: 360, h: 200});
  D.vertex('API', null, {id: 'api', parent: 'be', x: 20, y: 60});   // child: coords relative to container
  D.vertex('Postgres', 'shape=cylinder3;boundedLbl=1;size=12;whiteSpace=wrap;html=1;', {id: 'db', w: 80, h: 90});
  D.edge('web', 'api', 'HTTPS');
  D.edge('api', 'db', 'SQL', 'edgeStyle=orthogonalEdgeStyle;html=1;dashed=1;');
});
await D.layout([{layout: 'elkLayered', config: {'elk.direction': 'RIGHT'}}]);
D.fit();
D.setStyle(['api'], 'fillColor', '#d5e8d4');     // restyle
D.setXml(xmlString);                             // replace page from <mxGraphModel>, ids kept
D.addPage('Deployment');                         // new page, now current
return {saved: await D.save(), cells: D.dump()};
```

Editing an existing diagram: `D.dump()` or `D.find('Orders')` first to learn the ids,
then change only what was asked — the user's layout is part of their work.

## File mode

1. Write the XML following [references/file-format.md](references/file-format.md):
   `<mxfile>` → `<diagram>` per page → `<mxGraphModel>` → cells `0`, `1`, then shapes
   and edges. Readable ids, uncompressed content.
2. For more than ~8 nodes, don't compute coordinates: write them at 0,0 and let draw.io
   lay out a copy — `bash scripts/drawio-export.sh draft.drawio final.drawio --layout
   horizontalFlow` (any preset or ELK JSON works).
3. Validate: `xmllint --noout final.drawio`, then render
   `drawio-export.sh final.drawio /tmp/check.png -b 10` and look at it.
4. Hand over the `.drawio` (plus PNG/SVG if asked). `.drawio.svg` / `.drawio.png` with
   the diagram embedded: add `-e` to the export.

Mermaid is often the quickest source for flowcharts and sequence diagrams:
`drawio-export.sh flow.mmd flow.drawio` gives a fully editable draw.io diagram.

## Diagram quality

A diagram is read, not executed, so the layout carries the meaning:

- one primary direction of flow (left→right for systems, top→bottom for processes);
- label edges with what moves along them (`HTTPS`, `order.created`), not just arrows;
- group with containers/swimlanes by the boundary that matters (team, network zone,
  deployable) instead of by colour alone;
- one colour per role and a legend when there are more than two;
- split into pages rather than cramming — overview first, detail pages after.

## Safety

- The control port listens on `127.0.0.1` only, but while it is open any local process
  can run code in draw.io. Launch it for the task; the user closes draw.io when done.
- draw.io only lets a window read or save paths the user opened. Don't try to get
  around that from a script (it fails with *path not authorised*); open the file through
  `drawio-start.sh` or ask the user.
- Don't quit, kill or reload a draw.io the user started, and don't save over a file
  whose unsaved changes you didn't make — check `D.info().modified` before your first
  edit and ask if it is already `true`.
