# Command ids pinned to 0.19.0

Look any of these up with `ec_commands.py --id ID` before relying on a parameter; the
registry rejects unknown keys and lists the accepted ones. Layer refs are id, `#n` or name;
comp refs id or name. Commands without `comp` act on the **active comp**; `comp.new` opens
the new comp.

## Project and comps

| Id | Key params |
|---|---|
| `file.open` / `file.save` / `file.saveAs` | `{path}` |
| `file.import` | `{paths: [..], sequence?}` → `{items: [id], errors, warnings}` |
| `comp.new` | `{name, width, height, frameRate, duration, background?: #hex, open?}` → `{comp}` |
| `comp.open` | `{comp}` — make it active (needed before layer commands on another comp) |
| `comp.info` | `{comp?}` → settings + `layers[]` (index, name, type, in/out, start, switches) |
| `comp.settings` | `{comp?, name?, width?, height?, frameRate?, duration?, background?}` |

## Layers

| Id | Key params |
|---|---|
| `layer.newText` | `{text, name?, position?, box? [x,y,w,h], font?, style?, size?, fill?, stroke?, strokeWidth?, tracking?, justify?: left\|center\|right}` → `{layer}` |
| `layer.newShape` | `{kind: rect\|rounded\|ellipse\|star\|polygon, name?, size?, fill?, stroke?, strokeWidth?, position?}` |
| `layer.newSolid` | `{name?, color?, width?, height?}` |
| `layer.newNull` / `layer.newAdjustment` | `{name?}` |
| `layer.addItem` | `{item, time?, index?, position?, duration?}` — footage item → layer |
| `layer.rename` | `{layer, name}` |
| `layer.setText` | `{layer, text?, range?, font?, size?, fill?, justify?, …}` — text and character style |
| `layer.timing` | `{layers, start?, in?, out?}` (comp seconds) |
| `layer.setParent` | `{layers, parent}` |
| `layer.setTrackMatte` | `{layer, matte, kind?: alpha\|luma…}` |
| `layer.setBlendMode` | `{layers, mode}` |
| `layer.addMask` | `{layer, shape: rect\|ellipse, rect}` |
| `text.fonts` | `{query?}` → families with styles |

## Properties, keyframes, expressions

| Id | Key params |
|---|---|
| `prop.set` | `{layer, path, value, time?, timeBase?: layer\|comp}` |
| `prop.addKey` | `{layer, path, time, value, timeBase?}` |
| `prop.get` | `{layer, path, time?}` |
| `prop.setExpression` | `{layer, path, expression}` |
| `keys.select` | `{keys: [{layer, path, time}]}` then `keys.easyEase {which?}` / `keys.interpolation {interpolation}` / `keys.velocity` |
| `keys.setEase` | `{layer, path, time, side: in\|out, speed?, influence?}` |

Common paths: `transform/position`, `transform/scale`, `transform/rotation`,
`transform/opacity`, `transform/anchor`, `text/sourceText`,
`contents/group/contents/fill/color`, `contents/group/contents/rect/size`,
`effects/#1/<param>`. Get the exact list with `props COMP LAYER --flat`.

## Effects

| Id | Key params |
|---|---|
| `effect.apply` | `{effect: name\|id, layers?}` → `{effects: [uid], paths: ["effects/#n"]}` |
| `effect.remove` / `effect.toggle` / `effect.reorder` | `{layer, effect, …}` |
| `effect.list` | `{filter}` → `[{id, name, category, gpu, params: [{id, name, type, default}]}]` (MCP `list_effects`) |

Verified names: `Gaussian Blur` (`blurriness`), `Glow` (`threshold`, `radius`,
`intensity`), `Drop Shadow` (`color`, `opacity`, `direction`, `distance`, `softness`).

## Essential Graphics and templates

| Id | Key params |
|---|---|
| `essential.addProperty` | `{comp, layer, path, name}` — expose a property as a control |
| `essential.addMedia` | `{layer, name}` — replaceable footage |
| `essential.list` | `{comp}` |
| `essential.exportTemplate` | `{comp, path: .ectemplate, name?}` — fails with no controls |
| `essential.templateInfo` | `{path}` → name, size, duration, frameRate, `controls[]` (name, type, value), media |
| `essential.set` | `{layer, control, value}` — on a placed template instance |

## Render queue (inside a project)

`renderQueue.add {comp, format, output, channels?, proresProfile?}` then
`renderQueue.render {wait: true}`. The CLI's `render` is simpler for one comp.
