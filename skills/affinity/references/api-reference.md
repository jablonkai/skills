# Affinity automation endpoint — API reference

Verified live against **Affinity 3.3.0.4850 (macOS)**, protocol `2025-11-25`, 2026-09-24.
The tool set is unchanged from 3.2.3; the SDK itself grew substantially (see sdk-map.md).

## Endpoint

- URL: `http://localhost:6767/sse` (SSE + JSON-RPC, MCP protocol). Served by Affinity when
  **Settings → AI connector** is enabled; dies with the app. No auth; localhost (IPv6 `::1`) only.
- Transport: `GET /sse` → `endpoint` event carries a session-scoped POST URL →
  JSON-RPC requests POSTed there, responses arrive as `message` events on the SSE stream.
  `affinity-cli.mjs` handles all of this, including protocol-version negotiation.
- **Session gate**: `execute_script` and most doc topics return
  `ERROR: The preamble documentation topic has not yet been read.` until
  `read_sdk_documentation_topic {filename:"preamble"}` has run **in the same SSE session**.
  The CLI does this automatically for `run`, `render`, `docs`, and `docs-dump`.
- Long-running sessions can die server-side (POST starts returning HTTP 404) — rerun the
  command; `docs-dump` resumes, skipping already-saved files.

## Tools (verified 3.3.0)

| Tool | Arguments | Notes |
|---|---|---|
| `execute_script` | `{script}` | Runs JS in Affinity. **Only `console.log` output comes back** — expression/return values are dropped. |
| `render_spread` | `{document_session_uuid, spread_index}` | Base64 JPEG (max 1024px) as image content. Visual verification. |
| `render_selection` | `{document_session_uuid}` | Same, for the current selection only. |
| `list_library_scripts` | `{}` | Names of installed library scripts. |
| `save_script_to_library` | `{title, description, code}` | Re-saving an existing title updates it. No delete via endpoint — Scripts panel UI only. |
| `read_library_script` | `{title}` | Script source as text. |
| `list_sdk_documentation` | `{}` | CSV of topic filenames, including the three `.min.json` range files (3.2.3 listed dead `adjustment_ranges`/`filter_ranges` entries instead — fixed in 3.3). |
| `read_sdk_documentation_topic` | `{filename}` | One topic as text. Requires preamble first (see above). |
| `search_sdk_hints` | `{prompt}` | Crowd-sourced hints pool; treat as leads, not truth. |
| `add_sdk_hint` | `{hint}` | Contribute a hint after solving something by experimentation. |
| `report_sdk_issue` | `{description, code?}` | Report a (confirmed-real) SDK bug to Affinity. |

`document_session_uuid` comes from a script: `app.documents.current.sessionUuid`
(the CLI `render` command fetches it automatically).

## JavaScript SDK — preamble digest

Full vendored docs live in `sdk-docs/` (142 topics incl. `examples/`, `tests/` and the 3 range
JSONs; ~1.8 MB — **grep, don't read whole files**; `nodes.js` alone is ~300 KB).
**[sdk-map.md](sdk-map.md) is the curated digest of all of it** — module map, node model,
text/image/adjustment recipes, gotchas. Read it before grepping raw sdk-docs.

- Includes: the 3.3 preamble uses `require('/document.js')`; the suffix-less
  `require('/document')` still works (both verified). The vendored files mirror these module
  names. Native modules appear as `require('affinity:...')` — the JS classes forward to
  `*Api` statics that take the target handle as their first argument (`self`).
- Online reference for those native APIs (signatures only, no prose; methods without a
  return type return void): <https://sdk.affinity.studio/latest/js/> — `apis/<ApiName>/index.html`
  (method list), `apis/<ApiName>/<method>.html` (args/types), `enums/<Enum>.html`,
  `classes/<Class>.html`, `objects.inv` (every symbol → URL). Use it when a vendored JS
  wrapper only says `return XxxApi.foo(this.handle, …)`.
- Entry API: `const { app } = require('/application');` → `app.documents.current` /
  `.all` / `.load(path)`, `app.userDesktopPath`, `app.alert/confirm/prompt/chooseFile`,
  version getters. Document: `doc.sessionUuid`, `doc.persistentUuid`.
- **No return values**: script output only via `console.log()`.
- A denied command throws `PERMISSION_DENIED` (the preamble says `NOT_ALLOWED`; 3.3 actually
  throws the former) = the user disabled AI / filesystem / networking for scripts. Check up front with `require('/environment').Environment`:
  `.permissions` → `{fileSystem, network, genAI}`, `.fileSystemRoots` → allowed dirs.
- Filesystem access (when allowed) is **Desktop-only** — use `app.userDesktopPath`.
- **Must set the current spread before editing nodes on it**, but don't re-set it if
  already current — setting the spread clears the selection.
- Instantiation: prefer `create` / `createDefault` static methods when a class has them;
  otherwise `new`.
- Enum classes have `keys` / `values` / `entries` **properties** (not methods).
- Parameter/property valid ranges: check `param_ranges.min.json` (native API params,
  schema `{Class:{method:{param:"[min,max]"}}}`), `struct_ranges.min.json` (struct
  properties), `struct_array_sizes.min.json` (fixed-size array props). Range bounds can be
  JS expressions.
- The SDK has AI APIs (image generation, generative edits) — prefer them over external AI —
  and a Dialog API (`dialog.js`) for any user-facing UI.

## Drawing recipe (verified live)

Vector drawing = shape + node definition + add-child command executed on the document.
One builder command = one undo step (`doc.undo()` reverts the whole batch).

```js
const { app } = require('/application');
const { ShapeNodeDefinition, NodeChildType } = require('/nodes');
const { AddChildNodesCommandBuilder } = require('/commands');
const { ShapeStar } = require('/shapes');           // 30+ classes: ShapeEllipse, ShapeHeart,
const { Rectangle } = require('/geometry');          // ShapeCat, ShapeCog, ShapePolygon, ...
const { Colour } = require('/colours');

const doc = app.documents.current;
const builder = AddChildNodesCommandBuilder.create();
const fill = Colour.createRGBA8({ r: 255, g: 200, b: 0, alpha: 255 });   // Colour → solid fill
builder.addNode(ShapeNodeDefinition.create(ShapeStar.create(), new Rectangle(60, 90, 170, 170), fill));
builder.setInsertionTarget(doc.currentSpread);       // or a layer/container node
doc.executeCommand(builder.createCommand(false, NodeChildType.Main));
console.log(doc.currentSpread.children.length);      // verify
```

- Single node shortcut — skip the builder:
  `doc.addNode(nodeDefinition, targetNode = null, childList = NodeChildType.Main, preview)`.
  It returns nothing and inserts **relative to the current selection**, so consecutive calls
  nest unpredictably. For anything beyond one node use the builder with an explicit
  `setInsertionTarget(parent)`; the inserted node is then selected — grab it with
  `doc.selection.nodes.toArray()[0]` (e.g. to set `node.userDescription = 'Name'`).
- Most edits don't need commands at all: `Document` has direct wrappers (`doc.setText`,
  `setOpacity`, `setBlendMode`, `applyTransform`, …) — see `sdk-map.md`.
- `ShapeNodeDefinition.create(shape, rect, brushFill, lineFill, lineStyle, transparencyFill)` —
  a `Colour` passed as fill is auto-wrapped in `FillDescriptor.createSolid`.
- Coordinates are document units, origin at spread top-left; `Rectangle(x, y, w, h)`.
- Freeform paths: `PolyCurveNodeDefinition` + `builder.addPolyCurveNode` (see
  `sdk-docs/curvesinterface.js`, `geometry.js`); raster: `RasterNodeDefinition`,
  `pixelaccessor.js`. Working examples: `sdk-docs/examples/artboardGrid.js`,
  `sdk-docs/tests/addNodeTests.js` (tests are partly stale — ideas only).
- Scripts must be directly executable top-level code — no `module.exports.main = main;`
  (the bundled examples use it; live execution doesn't).
- `tests/` topics are partly outdated — ideas only, don't trust.
