---
name: cavalry
description: 'Remote-control Cavalry (Scene Group''s 2D motion-design app) by script: build scenes procedurally, animate with keyframes and magic easing, do per-letter text animation, load image/JSON assets, and render PNG frames or full videos. Use whenever the user wants to create or edit a Cavalry scene (.cv file), a motion-graphics sting, logo animation, animated title, countdown, lower third, or particle-style burst in Cavalry — or says ''Cavalry'', ''logo sting'', ''make an animation in Cavalry'', ''intro animation'', ''render from Cavalry'' — even if they don''t mention scripting. Also use when a video project needs an animated overlay that DaVinci Resolve or ffmpeg alone can''t produce.'
summary: "remote-control Cavalry (Scene Group's 2D motion-design app) via a scriptable bridge — build scenes procedurally, animate with keyframes and per-letter text effects, then render PNG frames or alpha overlay videos"
category: motion-design
risk: medium
tags:
    - cavalry
    - motion-graphics
    - animation
    - rendering
---

# Cavalry Control

Cavalry (`/Applications/Cavalry.app`) is scriptable in JavaScript (V8 12.4 since 2.6, so
ES2024 — `let`/`const`, arrow functions, `Set` methods all work; `api.*` / `ui.*` / `cavalry.*`
modules). Drive it through the **Cavalry Bridge** — a small script UI running inside Cavalry
that executes whatever is POSTed to `127.0.0.1:8731`. Everything below was proven against
**Cavalry 2.7.2** (May 2026, the current release) on real projects; the reference file covers
the rest of the API surface.

Since 2.7 Cavalry belongs to Canva: sign-in uses a Canva account and the former *Professional*
features are free for everyone — so don't plan around licence tiers. The one casualty is the
**CLI, which is not shipped in 2.7.x** (see Rendering).

- [references/api-reference.md](references/api-reference.md) — condensed module reference (api, cavalry, ui, WebClient/WebServer, render scripts, CLI). Read it when you need something outside the cheatsheet below.
- [references/cavalry-types/](references/cavalry-types/README.md) — the **complete** API as vendored TypeScript definitions with JSDoc examples; grep it for any function the reference doesn't cover.
- [scripts/cavalry-bridge.js](scripts/cavalry-bridge.js) — the bridge to install into Cavalry.
- [scripts/cavalry-helpers.js](scripts/cavalry-helpers.js) — `setAttrs`/`keyAttrs` (set and keyframe that fail loudly instead of silently), `newComp`/`useComp`/`findComp`, `splitLetters` (per-letter text), `renderFrames`, `writeJSON`. Pull it in with `api.load("<abs path>/scripts/cavalry-helpers.js")` at the top of each build script.
- [scripts/cavalry-send.sh](scripts/cavalry-send.sh) — send a JS file (or `-c 'inline code'`) to the bridge and wait for completion; exits non-zero and prints the JS error on failure. `--ping` checks the bridge is reachable and reports the bridge and Cavalry versions.

## The control loop

1. **User starts the bridge** (one-time per session): Cavalry must be running with
   `Cavalry Bridge.js` started from its Scripts menu. This cannot be done remotely — if
   `bash scripts/cavalry-send.sh --ping` gets no answer, ask the user to open Cavalry and run
   **Scripts ▸ Cavalry Bridge**. To install the bridge the first time, copy
   [scripts/cavalry-bridge.js](scripts/cavalry-bridge.js) into the Cavalry Scripts folder as
   `Cavalry Bridge.js` (`~/Library/Application Support/Cavalry/Scripts/` — create it if missing;
   **Help ▸ Show Scripts Folder** confirms the path). If `--ping` answers without a `"version"`
   field, an old bridge is running: copy the current one over it and restart it.
2. **Write a build script** to the scratchpad and send it:
   `bash scripts/cavalry-send.sh /path/to/build.js`. Each send gets a request id and waits for
   its own result file in the user's Cavalry preferences folder (discovered from the bridge's
   `GET /get` reply), so several callers can share one bridge safely. Long renders need
   `CAVALRY_SEND_TIMEOUT=600` (seconds).
3. **Feedback comes back through files, not HTTP.** The bridge reports ok/failed plus the
   exception message and stack of a thrown error; `console.log` output stays in Cavalry's Log
   window. So every script must *write its results to disk* to be read back:
   - visual state → `api.setFrame(f); api.renderPNGFrame(dir + "/check_" + f, 50)` at a few key
     frames (50 = 50% scale preview), then Read the PNGs. Render from a **separate send after
     the build** — connections made in a script (deformers, staggers) aren't evaluated until it
     returns, so same-send previews can lie;
   - data (ids, bounding boxes, attribute values) → `api.writeToFile(path, JSON.stringify(x), true)`.
4. **Iterate**: inspect previews, fix the script, resend. Build scripts should be re-runnable —
   create a fresh comp per version (`api.createComp("Thing v2")`) so reruns don't stack layers
   into the old comp. The active comp is shared UI state (the user, or another caller, can
   change it between sends), so any script that renders or edits in a *later* send should find
   its comp by name first — `useComp("Thing v2")` from the helpers.
5. **Final render**: PNG frame loop + ffmpeg (see Rendering below).

A failed send prints `Cavalry error: <message + stack>` to stderr — line numbers match the sent
script. A failure *without* a message means a syntax error (the script never started) or a
declined permission prompt: check with `node --check build.js`, and ask the user to look at
Cavalry for an open dialog. A send that times out while rendering is usually just a long render
— raise the timeout rather than resending, or the render runs twice.

## Scene-building cheatsheet (proven patterns)

### `api.set` never complains — check names, don't guess them

`api.set` **silently ignores** an attribute the layer doesn't have: a typo, or a name from an
older Cavalry, just does nothing and the send still reports ok. So a try/catch fallback chain
("try `frameRate`, else `fps`") is worse than useless — the first guess always "works". Use
`setAttrs(id, {...})` from the helpers (it checks `api.hasAttribute` and throws, naming the
attribute and layer type), and when unsure list the real names with `api.getAttributes(id)`.

### Comp setup

```js
api.load("/abs/path/to/skills/cavalry/scripts/cavalry-helpers.js");
var comp = newComp("My animation v1", {width: 1920, height: 1080, fps: 30, frames: 240,
                                       background: "#121212"});   // or "transparent"
```

That is `api.createComp` + `api.setActiveComp` + `resolution`, `fps`, `startFrame`/`endFrame`
(inclusive — 240 frames is 0–239) and `backgroundColor`. **New comps default to an opaque
background** (white, unless the user's preferences differ): set `backgroundColor` for a solid
colour — no oversized BG rectangle needed — and `"#00000000"` (alpha 0) for transparent output.

### Shapes and attributes

```js
var rect = api.primitive("rectangle", "Bar");        // also: "ellipse", "polygon", "star"...
setAttrs(rect, {"generator.dimensions": [400, 60],   // rectangle: [w, h]
                "position": [0, 0],                  // origin = comp centre, +y = UP
                "material.materialColor": "#00ADEF"});
var dot = api.primitive("ellipse", "Dot");
setAttrs(dot, {"generator.radius": [20, 20]});        // ellipse: radius [rx, ry], not dimensions
```

Common attribute paths: `position` `[x,y]`, `position.x`, `scale.x`/`scale.y`, `rotation.z`,
`opacity`, `material.materialColor` (hex string), `material.alpha` (**0–100 scale** — values
≤ 1 are near-invisible), `generator.dimensions` (rectangle), `generator.radius` (ellipse).
To discover names: `api.getAttributes(id)`, `api.getAttributeDefinition(id, attr)` (type,
default, enum values), or in the UI right-click an attribute → *Copy Scripting Path*.

### Sizing you can trust: measure, don't assume

Text and imported images have no size attribute to set, so **measure the real size and
normalise with scale**:

```js
var bb = api.getBoundingBox(layer, true);          // world space: {x,y,width,height,left,right,top,bottom,centre}
var s = 470 / bb.height;                           // e.g. scale an image or title to 470 px tall
setAttrs(layer, {"scale.x": s, "scale.y": s});
```

In world space `top` > `bottom` (+y is up). Measure *before* keyframing scale.

### Keyframes and easing

```js
api.keyframe(layer, 22, {"position.y": 940});
api.keyframe(layer, 50, {"position.y": 150});
api.magicEasing(layer, "position.y", 22, "BounceOut");   // easing is applied per-attr AT a keyframe
```

**`api.keyframe` only takes scalar leaves.** An array — `{"position": [x, y]}`,
`{"generator.dimensions": [w, h]}` — or a bare number on a vector attribute —
`{"rotation": 45}` (rotation is x/y/z since 2.x; 2D spin is `rotation.z`) — creates **no
keyframe and no error**. Key `position.x`/`position.y`, `scale.x`, `rotation.z`, … directly,
or use `keyAttrs(id, frame, {...})` from the helpers, which splits arrays, maps a bare rotation
to `rotation.z` and refuses unknown names. `magicEasing` likewise names one leaf
(`"rotation.z"`, not `"rotation"`); check keys with `api.getKeyframeTimes(id, "position.x")`.
(`api.set` is more forgiving: arrays and a bare rotation number both work there.)

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
setAttrs(t, {"text": "EMU 6-DAY RACE",
             "horizontalAlignment": 1, "verticalAlignment": 1,   // 1 = centre
             "fontSize": 150, "font.font": "Nebula Sans", "font.style": "Black",
             "material.materialColor": "#FFFFFF", "autoWidth": true, "autoHeight": true,
             "position": [0, -190]});
```

Without `autoWidth` the text box wraps long lines. Unicode (accents, ő/ű) works as-is. Check a
font before using it: `cavalry.fontExists(family, style)` (**both** arguments are required) and
`cavalry.getFontStyles(family)`; fall back to a font that exists rather than letting Cavalry
substitute silently.

**Per-letter animation** (each glyph drops with a stagger) — keep one text layer and wire a
**Sub-Mesh deformer + Stagger driving its time offset**. Sub-Mesh defaults to Level Mode
*Text (Characters)* (`levelMode` 3), so each glyph gets its own copy of the Sub-Mesh keyframes,
shifted by the stagger:

```js
var subMesh = api.create("subMesh", "Title bounce");
api.keyframe(subMesh, 34, {"shapePosition.y": 990});   // start above frame (+y = up)
api.keyframe(subMesh, 64, {"shapePosition.y": 0});
api.magicEasing(subMesh, "shapePosition.y", 34, "BounceOut");
api.connect(subMesh, "id", t, "deformers");
api.parent(subMesh, t);

var stagger = api.create("stagger", "Title stagger");
setAttrs(stagger, {"minimum": -12, "maximum": 0});     // frames of per-letter offset
api.flipGraph(stagger, "graph", "vertical");           // so the FIRST letter lands first
api.connect(stagger, "id", subMesh, "shapeTimeOffset");
api.parent(stagger, t);
```

**Preview it from a separate send.** Cavalry evaluates new connections (deformers, staggers,
behaviours) only after the script that made them returns — frames rendered in the *same* send
show every letter moving together, which looks exactly like a broken stagger. Build in one
send, then `useComp(...)` + render in the next. Likewise `api.get` on the Sub-Mesh returns the
un-staggered value; only rendered frames prove the per-letter motion.

When each glyph needs its own easing, colour or path (or the line must be re-laid out by
script), `splitLetters(str, style, cx, cy)` from the helpers makes one text layer per glyph,
placed exactly where it sits in the whole string (kerning included); keyframe each with its own
start frame:

```js
var letters = splitLetters("NIGHT RUN 2026",
    {"fontSize": 150, "font.font": "Helvetica", "font.style": "Bold",
     "material.materialColor": "#FFFFFF"}, 0, 40);          // line centred on [0, 40]
letters.forEach(function (id, i) {
    var y = api.get(id, "position.y"), f0 = 10 + i * 3;     // 3-frame stagger
    api.keyframe(id, f0, {"position.y": y + 700});
    api.keyframe(id, f0 + 20, {"position.y": y});
    api.magicEasing(id, "position.y", f0, "BounceOut");
});
```

### Images and other assets

```js
var asset = api.loadAsset("/abs/path/logo.png", false);   // false = not an image sequence
var layer = api.addAssetToComp(asset);
var bb = api.getBoundingBox(layer, true);
var s = 470 / bb.height;                                  // scale to ~470px tall
setAttrs(layer, {"scale.x": s, "scale.y": s});
```

Data-driven scenes: `api.jsonFromAsset(assetId)` parses a JSON/CSV asset,
`api.loadGoogleSheet(spreadsheetId, sheetId)` pulls a live sheet, and `api.WebClient` fetches
from any HTTP API — see the reference.

## Rendering

**Default: PNG frame loop + ffmpeg.** Needs nothing beyond the bridge, gives you the frames to
inspect, and ffmpeg runs from your own shell afterwards:

```js
api.load("/abs/path/to/skills/cavalry/scripts/cavalry-helpers.js");
useComp("My animation v1");
renderFrames(OUT, "name", 0, 239, 100);   // OUT/name_0000.png … name_0239.png
```

`renderPNGFrame(pathWithoutExtension, scalePercent)` renders the **current** frame of the
**active** comp; `.png` is appended, and only visible layers render (solo state counts — clear
it with `api.soloLayers([])`). A 240-frame 1080p render takes a while — raise
`CAVALRY_SEND_TIMEOUT`. Then assemble:

```bash
ffmpeg -framerate 30 -i name_%04d.png -c:v libx264 -pix_fmt yuv420p out.mp4       # opaque
ffmpeg -framerate 30 -i name_%04d.png -c:v qtrle out.mov                          # alpha overlay
```

For alpha output give the comp a transparent background (`newComp(..., {background:
"transparent"})`, i.e. `backgroundColor` `"#00000000"`) — a comp left at its default renders an
opaque white background even with no BG layer. The PNGs then carry alpha, and the qtrle .mov
drops straight into DaVinci Resolve as an overlay (ProRes 4444, `-c:v prores_ks -profile:v 4
-pix_fmt yuva444p10le`, is the smaller alternative). Verify it:
`ffprobe -v error -show_entries stream=pix_fmt out.mov` should say `argb`/`rgba`, not `rgb24`.
Run ffmpeg from the shell, not via `api.runProcess` — from a script UI such as the bridge that
call raises a "trust this script" dialog and blocks until the user answers.
`api.renderSVGFrame(path, scale, skipComps)` exists for vector snapshots.

**Render Queue** (in-app): `api.addRenderQueueItem(compId)` → configure → `api.render(itemId)`
or `api.renderAll()`. Useful for native mp4/ProRes/GIF output and for batching several comps or
scenes (`api.openScene(path, true)` per file). Render Queue Items can carry Setup/Pre/Post
**render scripts** (e.g. swap assets or text per render) — see the reference.

**Cavalry CLI — not available in 2.7.x.** Scene Group's release notes for 2.7.0–2.7.2 say the
CLI is missing ("please remain on your current version… working towards reinstating this"),
and before 2.7 its `render`/`list` commands needed an Enterprise licence. A `CavalryCLI.app`
still sits inside the 2.7.2 bundle, but its `Contents/MacOS/` is empty — there is no binary
to call. For headless-style batch renders, drive
the running app through the bridge instead (open each scene, render, ffmpeg); see the
reference for the pre-2.7 CLI flags if the user is pinned to an older version.

## Gotchas (hard-won)

- **The bridge is fire-and-forget** — design every script around file-based feedback (status
  JSON, preview PNGs, error catch-files). Never assume you'll see `console.log`.
- **`api.exec` code is wrapped in an IIFE by the bridge**, so bare `var` at top level is fine but
  nothing persists between sends. Persist state in the scene or on disk.
- **Silent `api.set`/`api.keyframe`**: unknown names are ignored without an error, and
  `keyframe` also drops arrays and bare numbers on vectors — use `setAttrs`/`keyAttrs`.
  The names in this file are the ones 2.7.2 uses (`fps`, `endFrame`, `text`,
  `backgroundColor`); earlier notes about `frameRate`/`string`/`frameRangeEnd` are wrong for
  2.7. Branch on `api.getCavalryVersion()` if a script must also run on older releases.
- **Colour**: 2.6 removed *Linear Gamma* (comp settings) and the *Color Filter* shader — use
  Color Management with Working Color Space *Linear sRGB* instead.
- **`material.alpha` is 0–100**, not 0–1.
- **New layers land in the active comp.** `api.create`/`api.primitive`/`addAssetToComp` add to
  whatever comp is active *now* — call `newComp`/`useComp` before creating anything, even in a
  throwaway probe script.
- **Stacking and grouping**: a layer created later draws on top — create backgrounds and
  plates before the text on them. To move several layers as one (a lower-third plate, bar and
  text), `api.parent` them under `api.create("null", "Group")` and animate the null.
- **Vector attributes read back as objects**: `api.get(id, "position")` is `{x, y}` (likewise
  `resolution`, `generator.radius`, `backgroundColor` → `{r,g,b,a}`), while `api.set` takes
  `[x, y]`. Read `position.x`/`position.y` when you need numbers.
- **Preview cheaply**: render check frames at 50% scale at a handful of story beats, not every
  frame; full-res full-range renders only once the previews look right.
- **Re-runs**: `api.createComp` a fresh versioned comp per attempt; reruns into the same comp
  duplicate every layer.
- Save the scene from script — `api.saveSceneAs("/path/scene.cv")` — so work survives a crash;
  it returns `false` (or throws) if a modal dialog is open, so check the result. Never call
  `api.newScene()`/`api.openScene()` without asking — they discard the user's open scene.
- The vendored type definitions double as offline docs — nearly every function has a JSDoc
  example; grep before guessing a signature.

## Security

Running the bridge means running a **code-execution server** on the user's machine. Say so
before asking them to start it.

- The bridge binds `127.0.0.1:8731` and executes any JavaScript POSTed to it inside the
  live session — the user's privileges, the user's open scene. Raw non-JSON bodies are run
  as JS directly. Requests carry **no authentication**: every local process, and every
  other user on a shared machine, can drive Cavalry through it.
- Web pages **cannot**. Requests carrying an `Origin` header or a cross-site
  `Sec-Fetch-Site` are rejected with 403, so a page in the user's browser can't reach the
  bridge. That check is the only gate — there is no token.
- **Nothing listens until the user runs it.** Copying `cavalry-bridge.js` into the Scripts
  folder only puts it in the menu; the port opens when they pick **Scripts ▸ Cavalry
  Bridge** and stays open for that session.
- **To stop the bridge, quit Cavalry.** There is no remote shutdown; the port is released
  with the process.
