# Cavalry scripting reference

Condensed from the official docs (https://cavalry.studio/docs/tech-info/scripting/ — the old
docs.cavalry.scenegroup.co URLs redirect there) plus production experience, checked against
Cavalry 2.7.2. Cavalry scripts are JavaScript (V8 12.4 / ES2024 since 2.6); modules: `api` (scene + filesystem + web), `cavalry` (math/geometry/color/text
utilities), `ui` (script windows), `render` (inside render scripts only), `console`.

User scripts live in `~/Library/Application Support/Cavalry/Scripts/` (**Help ▸ Show Scripts
Folder**) and appear in the Scripts menu. The JavaScript Editor window runs ad-hoc code.

## Contents

- [api — composition & playhead](#api--composition--playhead)
- [api — layers & attributes](#api--layers--attributes)
- [api — keyframes & easing](#api--keyframes--easing)
- [api — connections & hierarchy](#api--connections--hierarchy)
- [api — assets & data](#api--assets--data)
- [api — rendering](#api--rendering)
- [api — scene I/O & selection](#api--scene-io--selection)
- [api — filesystem & processes](#api--filesystem--processes)
- [api — WebClient / WebServer](#api--webclient--webserver)
- [cavalry — utilities](#cavalry--utilities)
- [ui — script windows](#ui--script-windows)
- [Render scripts](#render-scripts)
- [Cavalry CLI](#cavalry-cli)
- [Recipes](#recipes)

## api — composition & playhead

| Function | Notes |
|---|---|
| `createComp(niceName) → id` | new comp |
| `getComps() → [id]` | all comps — find one by `getNiceName` |
| `getActiveComp() → id` / `setActiveComp(id)` | active comp = what `renderPNGFrame` renders |
| `getCompLayers(topLevelOnly) → [id]` | enumerate layers |
| `setFrame(f)` / `getFrame()` | move playhead (needed before `renderPNGFrame`) |
| `play()` / `stop()` | stop playback before frame-loop renders |

Comp attributes (2.7.2, layer type `compNode`): `resolution` `[w,h]`, `fps`, `startFrame`,
`endFrame` (inclusive), `playbackStart`/`playbackEnd`, `backgroundColor` (hex, or `"#00000000"`
/ `backgroundColor.a: 0` for transparent — default is opaque), `motionBlur`, `shutterAngle`.
There is no `frameRate`/`frameRangeEnd` — and `api.set` would ignore them without an error.

## api — layers & attributes

| Function | Notes |
|---|---|
| `create(layerType, name) → id` | any layer type, e.g. `"textShape"`, `"subMesh"`, `"stagger"` |
| `primitive(type, name) → id` | `"rectangle"`, `"ellipse"`, `"polygon"`, `"star"`… |
| `createEditable(path, name) → id` | editable shape from a `cavalry.Path` |
| `deleteLayer(id)` / `duplicate(id, withInputConnections)` | |
| `set(id, {attr: value, ...})` / `get(id, attr)` | `set` **silently ignores unknown names**; `get` returns `undefined` |
| `hasAttribute(id, attr)` | works on nested paths (`position.y`, `backgroundColor.a`) — guard `set` with it |
| `getAttributes(id)` / `getAttrType(id, attr)` / `getAttributeDefinition(id, attr)` | discovery (definition carries type, default, enum values) |
| `getNiceName(id)` / `rename(id, name)` | |
| `resetAttribute(id, attr)` | |
| `getLayerType(id)` | |
| `getBoundingBox(id, worldSpace) → {x,y,width,height,centre,left,right,top,bottom}` | measure real size |

Attribute discovery from the UI: right-click layer → *Copy Layer Id*; right-click attribute →
*Copy Scripting Path*.

Common paths: `position` `[x,y]` (origin = comp centre, +y up), `position.x/.y`, `scale.x/.y`,
`rotation` (x/y/z — `rotation.z` for 2D), `material.materialColor` (hex string), `material.alpha` (0–100),
`opacity`, `generator.dimensions` `[w,h]` (rectangle only), `generator.radius` `[rx,ry]`
(ellipse); text: `text` (reads back as `{text, overrides}`), `fontSize`, `font.font`,
`font.style`, `horizontalAlignment`/`verticalAlignment` (0 = left/top, 1 = centre),
`autoWidth`/`autoHeight`, `letterSpacing`, `lineSpacing`. Sub-Mesh: `shapePosition`,
`shapeRotation`, `shapeScale`, `shapeOpacity`, `shapeTimeOffset`, `levelMode` (default 3 =
characters), `indexMode`. Stagger: `minimum`, `maximum`, `offset`, `graph`, `strength`.

## api — keyframes & easing

| Function | Notes |
|---|---|
| `keyframe(id, frame, {attr: value, ...})` | **scalar leaves only** — arrays and bare numbers on vectors (`rotation`) are silently dropped |
| `getKeyframeTimes(id, attr)` / `isAnimatedAttribute(id, attr)` | verify keys landed |
| `deleteKeyframe(id, attr, frame)` / `modifyKeyframe(id, data)` | |
| `magicEasing(id, attr, frame, presetName)` | applies at that keyframe |

Presets: `SlowIn`, `SlowOut`, `SlowInSlowOut`, `VerySlowIn`, `VerySlowOut`,
`VerySlowInVerySlowOut`, `SpringIn`, `SpringOut`, `SpringInSpringOut`, `SmallSpringIn`,
`SmallSpringOut`, `SmallSpringInSmallSpringOut`, `AnticipateIn`, `OvershootOut`,
`AnticipateInOvershootOut`, `BounceIn`, `BounceOut`, `BounceInBounceOut`, `Custom`, `None`.

## api — connections & hierarchy

| Function | Notes |
|---|---|
| `connect(fromId, fromAttr, toId, toAttr, force)` | e.g. `connect(stagger, "id", subMesh, "shapeTimeOffset")` |
| `disconnect(fromId, fromAttr, toId, toAttr)` | |
| `parent(id, newParentId)` / `unParent(id)` | |
| `flipGraph(id, "graph", "vertical")` | e.g. reverse a stagger's direction |

## api — assets & data

| Function | Notes |
|---|---|
| `loadAsset(path, isSequence) → assetId` | images, movies, JSON, CSV |
| `addAssetToComp(assetId) → layerId` | footage layer |
| `jsonFromAsset(assetId) → object` | parse a JSON/CSV asset — data-driven scenes |
| `loadGoogleSheet(spreadsheetId, sheetId) → assetId` | live sheet import |

## api — rendering

| Function | Notes |
|---|---|
| `renderPNGFrame(pathNoExt, scalePercent)` | renders the **current** frame of the active comp; appends `.png`; 50 = half-size preview; visible (soloed) layers only |
| `renderSVGFrame(pathNoExt, scalePercent, skipComps)` | vector snapshot; `skipComps` drops comp backgrounds |
| `soloLayers([ids])` | solo for per-layer renders; `soloLayers([])` clears |
| `getRenderPath()` | the scene's render output folder |
| `addRenderQueueItem(compId) → itemId` | then set its attrs (output path, format, range) |
| `render(itemId)` / `renderAll()` | run queue jobs |

Transparent output: leave the comp background empty (no BG rect) — PNG frames carry alpha.

## api — scene I/O & selection

| Function | Notes |
|---|---|
| `newScene()` / `openScene(path, force)` | |
| `saveScene()` / `saveSceneAs(path)` → bool / `exportSceneAs(path)` | check the result — false while a modal is open |
| `getSceneFilePath()` | path of the open scene ("" if unsaved) |
| `getSelection(sortByHierarchy)` / `select([ids])` / `invertSelection()` | |
| `getSelectedKeyframes()` | |

## api — filesystem & processes

| Function | Notes |
|---|---|
| `filePathExists(path)` / `isFile(path)` / `isDirectory(path)` | |
| `listDirectoryPaths(path, includeDirectories)` → `[path]` | the documented one; `listDirectory(path)` also works in 2.7.2 but isn't in the typings |
| `writeToFile(path, content, overwrite)` / `readFromFile(path)` | the feedback channel back to the caller |
| `makeFolder(path)` / `deleteFilePath(path)` | |
| `exec(scriptId, source)` | run JS from a string (scriptId = reverse-domain name) |
| `load(path)` | run a JS file |
| `runProcess(cmd, [args]) → {output, error}` | blocking system command; from a UI script (the bridge is one) it first raises a "trust this script" dialog — prefer running tools from the shell |
| `runDetachedProcess(cmd, [args])` | non-blocking; same trust prompt |
| `getPreferencesPath()` / `getTempFolder()` | where the bridge keeps its status and result files / scratch space |
| `getCavalryVersion()` → `"2.7.2"` | branch on version when attribute names differ |

## api — WebClient / WebServer

`api.WebClient` (HTTP from scripts): constructor takes a base URL.
`get(path)`, `post(path, content, contentType)`, `put(...)`, `postFromFile`/`putFromFile`,
`status()`, `body()`, `getHeaders()`, `writeBodyToBinaryFile(path)` (download files),
auth: `setBasicAuthentication`, `setDigestAuthentication`, `setTokenAuthentication`,
`addHeader(key, value)`.

`api.WebServer` (what the Cavalry Bridge uses): `listen(host, port)`, `stop()`, `postCount()`,
`getNextPost()`, `getNewestPost()`, `clearPosts()`, `setResultForGet(text)` (static GET reply),
`addCallbackObject({onPost: fn})` (polls every 3 s by default), `setHighFrequency()` (1 Hz) /
`setRealtime()` (60 Hz).
No websockets; binary POST bodies unsupported.

## cavalry — utilities

- **Math**: `random()`, `noise1d/2d/3d()`, `dist()`, `map()`, `norm()`, `clamp()`, `lerp()`,
  angle/vector conversions.
- **Color**: `rgbToHex()`, `hexToRgba()`, `rgbToHsv()`, `hsvToHex()`, `nameThatColor()`.
- **Text/fonts**: `fontExists(family, style)` (both args required), `getFontFamilies()`,
  `getFontStyles(family)`, `measureText(str, family, style, size)` (ink box),
  `fontMetrics(family, style, size)`.
- **`cavalry.Path`**: `moveTo`, `lineTo`, `cubicTo`, `quadTo`, `arcTo`, `close`, plus
  `addText()`, `addRect()`, `addEllipse()`, booleans (`unite`, `intersect`, `difference`),
  `pointAtParam()`, `tangentAtParam()`, `length()`. Feed into `api.createEditable(path, name)`.
- Also: `Line`, `Mesh`, `Material`, `Matrix`, `PointCloud`, `Point`, `versionLessThan()`.

## ui — script windows

Window: `ui.setTitle(s)`, `ui.add(widget)`, `ui.show()`, `ui.setBackgroundColor(hex)`,
`ui.addStretch()`, `ui.addSpacing(n)`, `ui.setMargins(l,t,r,b)`.
Layouts: `ui.HLayout`, `ui.VLayout`, `ui.FlowLayout`, `ui.TabView`, `ui.PageView`, `ui.ScrollView`.
Widgets: `Button`, `Checkbox`, `ColorChip/ColorPicker/ColorWheel/ColorPalette`, `DropDown`,
`FilePath`, `Image`, `ImageButton`, `Label`, `LineEdit`, `MultiLineEdit`, `NumericField`,
`Slider`, `ProgressBar`, `List`, `Container`, `Draw` (custom drawing from `cavalry.Path`),
`Modal` (dialogs — since 2.6 also outside UI scripts). Polling timers are `new api.Timer(obj)`
(`onTimeout`), not a ui widget.
Widget callbacks: `onClick`, `onValueChanged`, `onValueCommitted`.
App-level callbacks via `ui.addCallbackObject({...})`: `onSelectionChanged`, `onCompChanged`,
`onAttrChanged`, `onLayerAdded`, `onAssetUpdated`, and since 2.6 `onAttrConnected`,
`onAttrDisconnected`, `onToolChanged`.
Misc: `ui.scriptLocation` (script's folder), `ui.runFileScript(path)`,
`ui.registerDragDropMimeType()` + `onDrop`.

## Render scripts

Render Queue Items have a **Scripts** tab (Render Manager) with three hooks:

1. **Setup** — before render setup; `render.renderQueueItem` gives the item id to modify.
2. **Pre-Render** — before rendering; `render.composition` gives the comp id (mutate the scene,
   fetch data, swap assets).
3. **Post-Render** — after the item finishes; `render.path` gives the resolved output path
   (e.g. `api.runProcess` an ffmpeg assembly or upload step).

For image sequences the hooks run before/after the whole sequence, not per frame.

## Cavalry CLI

**Not available in Cavalry 2.7.0–2.7.2** — the release notes tell CLI users to stay on 2.6.x
until it is reinstated. On 2.7.x render through the app (bridge + `renderPNGFrame`, or the
Render Queue). The rest of this section applies to **2.6.x and earlier** only.

Binary: `/Applications/Cavalry.app/Contents/Applications/CavalryCLI.app/Contents/MacOS/cavalry-cli`.

Commands: `render`, `list` (comp + render-queue ids), `version`, `auth`, `proxy`, and
`--prompt` (interactive JS REPL). **`render`, `list` and `--prompt` required an Enterprise
licence.**

Render flags: `-s/--startFrame`, `-e/--endFrame`, `-n/--name`, `-d/--directory`,
`--composition compNode#1`, `--format` (png, jpeg, svg, gif, apng, webm, webp, mp4, quicktime,
audio), `--scale`, `--assetSwap`.

```bash
./cavalry-cli render ~/Desktop/scene.cv -n out -d ~/Desktop/ -s 0 -e 50 --format mp4
```

## Recipes

Cheap radial particle burst (confetti/sparks) — no particle system:

```js
// needs cavalry-helpers.js loaded (setAttrs)
var cols = ["#00ADEF", "#FFFFFF", "#DFF4FD", "#006BA6"];
for (var i = 0; i < 16; i++) {
    var ang = (i / 16) * Math.PI * 2 + 0.2;
    var dist = 260 + (i % 4) * 70;
    var p = api.primitive("ellipse", "Spark " + i);
    var r = 9 + (i % 3) * 4;
    setAttrs(p, {"generator.radius": [r, r], "material.materialColor": cols[i % 4]});
    api.keyframe(p, 0, {"scale.x": 0, "scale.y": 0});          // hidden until the burst
    api.keyframe(p, 184, {"position.x": 700, "position.y": 110, "scale.x": 0, "scale.y": 0});
    api.keyframe(p, 187, {"scale.x": 1, "scale.y": 1});
    api.keyframe(p, 210, {"position.x": 700 + Math.cos(ang) * dist,
                          "position.y": 110 + Math.sin(ang) * dist,
                          "scale.x": 0, "scale.y": 0});
    api.magicEasing(p, "position.x", 184, "SlowOut");
    api.magicEasing(p, "position.y", 184, "SlowOut");
}
```

Running-gait loop (bob + rock, alternating every 8 frames):

```js
var step = 0;
for (var f = startF; f <= endF; f += 8) {
    api.keyframe(layer, f, {"position.y": baseY + ((step % 2) ? 10 : 0),
                            "rotation.z": ((step % 2) ? 5 : -3)});
    step++;
}
api.keyframe(layer, endF + 4, {"position.y": baseY, "rotation.z": 0});
```

Piecewise-linear position lookup (for coordinating secondary elements — e.g. dust puffs at a
runner's feet — with a keyframed move):

```js
function xAtFrame(kfs, f) {   // kfs = [[frame, x], ...]
    if (f <= kfs[0][0]) return kfs[0][1];
    for (var i = 1; i < kfs.length; i++)
        if (f <= kfs[i][0]) {
            var t = (f - kfs[i-1][0]) / (kfs[i][0] - kfs[i-1][0]);
            return kfs[i-1][1] + (kfs[i][1] - kfs[i-1][1]) * t;
        }
    return kfs[kfs.length - 1][1];
}
```

## Complete API surface

This file is a curated condensation. The **full** API is vendored as TypeScript definitions in
[cavalry-types/](cavalry-types/README.md) — when a function isn't listed above, grep there:

```bash
grep -n "functionName" references/cavalry-types/namespaces/api.d.ts   # or cavalry / ui / ctx
```

Notable extras only found there: the `ctx` namespace (expression context inside Duplicator /
Connect Shape / Trails — `ctx.index`, `ctx.count`, `ctx.positionX/Y`), `magicEasing`'s `Custom`
mode with an expression string (e.g. `'1 - pow(1 - x, 5)'`), and JSDoc examples for nearly every
function.
