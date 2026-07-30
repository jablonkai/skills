---
name: cavalry
description: 'Remote-control Cavalry (Scene Group''s 2D motion-design app) by script: build scenes procedurally, animate with keyframes and magic easing, do per-letter text animation, load image/JSON assets, and render PNG frames or full videos. Use whenever the user wants to create or edit a Cavalry scene (.cv file), a motion-graphics sting, logo animation, animated title, countdown, lower third, or particle-style burst in Cavalry — or says ''Cavalry'', ''logo sting'', ''make an animation in Cavalry'', ''intro animation'', ''render from Cavalry'' — even if they don''t mention scripting. Also use when a video project needs an animated overlay that DaVinci Resolve or ffmpeg alone can''t produce.'
category: motion-design
risk: medium
tags:
    - cavalry
    - motion-graphics
    - animation
    - rendering
---

# Cavalry Control

Cavalry (`/Applications/Cavalry.app`) is scriptable in JavaScript (ES6, `api.*` / `ui.*` /
`cavalry.*` modules). Drive it through the **Cavalry Bridge** — a small script UI running
inside Cavalry that executes whatever is POSTed to `127.0.0.1:8731`. Everything below was
proven on a real project (EMU logo sting + race animation); the reference file covers the rest of
the API surface.

- [references/api-reference.md](references/api-reference.md) — condensed module reference (api, cavalry, ui, WebClient/WebServer, render scripts, CLI). Read it when you need something outside the cheatsheet below.
- [references/cavalry-types/](references/cavalry-types/README.md) — the **complete** API as vendored TypeScript definitions with JSDoc examples; grep it for any function the reference doesn't cover.
- [scripts/cavalry-bridge.js](scripts/cavalry-bridge.js) — the bridge to install into Cavalry.
- [scripts/cavalry-send.sh](scripts/cavalry-send.sh) — send a JS file (or `-c 'inline code'`) to the bridge and wait for completion. `--ping` checks the bridge is reachable first.

## The control loop

1. **User starts the bridge** (one-time per session): Cavalry must be running with
   `Cavalry Bridge.js` started from its Scripts menu. This cannot be done remotely — if
   `curl -s -m 2 http://127.0.0.1:8731/` gets no answer, ask the user to open Cavalry and run
   **Scripts ▸ Cavalry Bridge**. To install the bridge the first time, copy
   [scripts/cavalry-bridge.js](scripts/cavalry-bridge.js) into the Cavalry Scripts folder
   (`~/Library/Application Support/Cavalry/Scripts/` — verify via **Help ▸ Show Scripts Folder**).
2. **Write a build script** to the scratchpad and send it:
   `bash scripts/cavalry-send.sh /path/to/build.js`. The helper waits for the bridge's status file
   to change — it discovers the path from the bridge's `GET /get` reply, so it lives in the user's
   own Cavalry preferences folder rather than a guessable `/tmp` name (`CAVALRY_BRIDGE_STATUS`
   overrides). Long renders need `CAVALRY_SEND_TIMEOUT=600` (seconds).
3. **Feedback comes back through files, not HTTP.** The bridge only reports ok/failed;
   `console.log` output stays in Cavalry's Log window. So every script must *write its results to
   disk* to be read back:
   - visual state → `api.setFrame(f); api.renderPNGFrame(dir + "/check_" + f, 50)` at a few key
     frames (50 = 50% scale preview), then Read the PNGs;
   - data (ids, bounding boxes, attribute values) → `api.writeToFile(path, JSON.stringify(x), true)`.
4. **Iterate**: inspect previews, fix the script, resend. Build scripts should be re-runnable —
   create a fresh comp per version (`api.createComp("Thing v2")`) so reruns don't stack layers
   into the old comp.
5. **Final render**: PNG frame loop + ffmpeg (works on every licence tier — see Rendering below).

A failed send (`ok: false`) usually means a JS exception; there is no stack trace over HTTP.
Re-send the script wrapped so the error lands in a file:
`try { /* body */ } catch (e) { api.writeToFile("/tmp/cavalry-error.txt", String(e), true); }`

## Scene-building cheatsheet (proven patterns)

### Comp setup — attribute names vary between Cavalry versions

Wrap `api.set` in a try/catch fallback chain rather than trusting one attribute name:

```js
function trySet(id, obj) { try { api.set(id, obj); return true; } catch (e) { return false; } }
var comp = api.createComp("My animation v1");   // or api.getActiveComp()
api.setActiveComp(comp);
trySet(comp, {"resolution": [1920, 1080]});
trySet(comp, {"frameRate": 30}) || trySet(comp, {"fps": 30});
trySet(comp, {"frameRangeEnd": 240}) || trySet(comp, {"endFrame": 240}) || trySet(comp, {"outFrame": 240});
```

### Shapes and attributes

```js
var rect = api.primitive("rectangle", "BG");         // also: "ellipse", "polygon", "star"...
api.set(rect, {"generator.dimensions": [1980, 1120],  // oversize the BG ~40px past frame edges
               "position": [0, 0],                    // origin = comp centre, +y = up
               "material.materialColor": "#121212"});
```

Common attribute paths: `position` `[x,y]`, `position.x`, `scale.x`/`scale.y`, `rotation`,
`material.materialColor` (hex string), `material.alpha` (**0–100 scale** — values ≤ 1 are
near-invisible), `generator.dimensions` `[w,h]`, `generator.radius` `[rx,ry]` (ellipse).
To discover names: right-click a layer → *Copy Layer Id*, right-click an attribute →
*Copy Scripting Path*, or `api.getAttributes(id)` / `api.getAttributeDefinition(id, attr)`.

### Sizing you can trust: measure, don't assume

Generator attrs also differ between versions (`radius` vs `dimensions`), so set what works, then
**measure the real size and normalise with scale**:

```js
var e = api.primitive("ellipse", "Dot");
trySet(e, {"generator.radius": [px/2, px/2]}) || trySet(e, {"generator.dimensions": [px, px]});
var bb = api.getBoundingBox(e, true);              // {x,y,width,height,centre,...} world space
var s = (bb.width > 1) ? (px / bb.width) : 1;      // multiply into every later scale keyframe
```

The same trick sizes imported images: load, measure height, scale to target pixel height.

### Keyframes and easing

```js
api.keyframe(layer, 22, {"position.y": 940});
api.keyframe(layer, 50, {"position.y": 150});
api.magicEasing(layer, "position.y", 22, "BounceOut");   // easing is applied per-attr AT a keyframe
```

Magic easing presets: `SlowIn/SlowOut/SlowInSlowOut`, `VerySlowIn/VerySlowOut/VerySlowInVerySlowOut`,
`SpringIn/SpringOut/SpringInSpringOut`, `SmallSpring…` variants, `AnticipateIn`, `OvershootOut`,
`AnticipateInOvershootOut`, `BounceIn/BounceOut/BounceInBounceOut`, `None`.
Taste notes from production: `OvershootOut` for pop-in text, `BounceOut` for drops/landings,
`SlowOut` for bursts (particles, dust), `SlowInSlowOut` for drifts and pulses.

Cheap particle burst (no particle system needed): N small ellipses keyframed from one origin
outward on `Math.cos/sin(angle) * dist`, scaling to 0, `SlowOut` — see the reference for the
full confetti/spark snippet.

### Text — and the per-letter animation recipe

```js
var t = api.create("textShape", "Title");
api.set(t, {"horizontalAlignment": 1, "verticalAlignment": 1,   // 1 = centre
            "fontSize": 150, "font.font": "Nebula Sans", "font.style": "Black",
            "material.materialColor": "#FFFFFF", "autoWidth": true, "autoHeight": true,
            "position": [0, -190]});
trySet(t, {"text": "EMU 6-DAY RACE"}) || trySet(t, {"string": "EMU 6-DAY RACE"});  // attr name varies
```

Per-letter bounce-in (each glyph drops with a stagger) — the proven wiring is
**subMesh deformer + stagger driving its time offset**:

```js
var subMesh = api.create("subMesh", "Title bounce");
api.keyframe(subMesh, 34, {"shapePosition.y": 990});   // start above frame
api.keyframe(subMesh, 64, {"shapePosition.y": 0});
api.magicEasing(subMesh, "shapePosition.y", 34, "BounceOut");
api.connect(subMesh, "id", t, "deformers");
api.parent(subMesh, t);

var stagger = api.create("stagger", "Title stagger");
api.set(stagger, {"minimum": -12, "maximum": 0});      // frames of per-letter offset
api.flipGraph(stagger, "graph", "vertical");           // so the FIRST letter lands first
api.connect(stagger, "id", subMesh, "shapeTimeOffset");
api.parent(stagger, t);
```

Check fonts before using them: `cavalry.fontExists(family)`, `cavalry.getFontStyles(family)`.

### Images and other assets

```js
var asset = api.loadAsset("/abs/path/logo.png", false);   // false = not an image sequence
var layer = api.addAssetToComp(asset);
var bb = api.getBoundingBox(layer, true);
var s = 470 / bb.height;                                  // scale to ~470px tall
api.set(layer, {"scale.x": s, "scale.y": s});
```

Data-driven scenes: `api.jsonFromAsset(assetId)` parses a JSON/CSV asset,
`api.loadGoogleSheet(spreadsheetId, sheetId)` pulls a live sheet, and `api.WebClient` fetches
from any HTTP API — see the reference.

## Rendering

**Default: PNG frame loop + ffmpeg.** Works on every licence tier and gives you the frames to
inspect:

```js
function pad(n) { return ("0000" + n).slice(-4); }
api.stop();
for (var f = 0; f <= END; f++) { api.setFrame(f); api.renderPNGFrame(OUT + "/name_" + pad(f), 100); }
```

`renderPNGFrame(pathWithoutExtension, scalePercent)` renders the **current** frame; `.png` is
appended. A 240-frame 1080p render takes a while — raise `CAVALRY_SEND_TIMEOUT`. Then assemble:

```bash
ffmpeg -framerate 30 -i name_%04d.png -c:v libx264 -pix_fmt yuv420p out.mp4       # opaque
ffmpeg -framerate 30 -i name_%04d.png -c:v qtrle out.mov                          # alpha overlay
```

For alpha output leave the comp background transparent (add no BG rectangle) — the PNGs then
carry alpha, and the qtrle .mov drops straight into DaVinci Resolve as an overlay.
`api.renderSVGFrame(path, scale, skipComps)` exists for vector snapshots.

**Render Queue** (in-app, all tiers): `api.addRenderQueueItem(compId)` → configure → `api.render(itemId)`
or `api.renderAll()`. Render Queue Items can carry Setup/Pre/Post **render scripts** (e.g. swap
assets or text per render) — see the reference.

**Cavalry CLI** (`/Applications/Cavalry.app/Contents/Applications/CavalryCLI.app/Contents/MacOS/cavalry-cli`):
headless `render`/`list` and the interactive `--prompt` REPL are **Enterprise-licence only**, so
don't plan around them unless the user confirms an Enterprise licence; `version`/`auth` work
everywhere. Formats include png, svg, gif, webm, webp, mp4, quicktime; `--assetSwap` replaces
assets at render time.

## Gotchas (hard-won)

- **The bridge is fire-and-forget** — design every script around file-based feedback (status
  JSON, preview PNGs, error catch-files). Never assume you'll see `console.log`.
- **`api.exec` code is wrapped in an IIFE by the bridge**, so bare `var` at top level is fine but
  nothing persists between sends. Persist state in the scene or on disk.
- **Version drift**: comp attrs (`frameRate` vs `fps`), text (`text` vs `string`), generators
  (`radius` vs `dimensions`) all changed names across releases — always use the `trySet` chain.
- **`material.alpha` is 0–100**, not 0–1.
- **Preview cheaply**: render check frames at 50% scale at a handful of story beats, not every
  frame; full-res full-range renders only once the previews look right.
- **Re-runs**: `api.createComp` a fresh versioned comp per attempt; reruns into the same comp
  duplicate every layer.
- Save the scene from script — `api.saveSceneAs("/path/scene.cv")` — so work survives a crash;
  wrap in try/catch (fails if a modal dialog is open).
- The vendored type definitions double as offline docs — nearly every function has a JSDoc
  example; grep before guessing a signature.
