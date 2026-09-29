---
name: obs
description: 'Remote-control a running OBS Studio through its built-in obs-websocket v5 server with a dependency-free Python client — create and switch scenes, add and configure sources (color, text, image, media, browser, capture), position scene items, add filters, control recording (chapters, split), streaming, replay buffer and virtual camera, set audio volume/mute, screenshot any scene to verify, and build whole scene collections from a JSON spec. Use whenever the user wants something done in OBS or with an OBS scene, source, overlay, recording or stream — e.g. "set up my stream scenes in OBS", "add a lower third in OBS", "switch to the BRB scene", "start recording in OBS", "make a Starting Soon / Main / BRB layout", "mute the mic in OBS", "állítsd be az OBS jeleneteket", "indítsd el a felvételt OBS-ben" — even if they just say "OBS". Not for editing recorded footage (use davinci-resolve), ffmpeg-only conversion, or keyframed motion graphics (use cavalry).'
summary: "remote-control a running OBS Studio by Python over obs-websocket v5 — scenes, sources and filters, scene-item transforms, recording, streaming, replay buffer and virtual camera, screenshot verification, and scene collections built from a JSON spec"
category: video
risk: high
tags:
    - obs
    - streaming
    - recording
    - websocket
    - scripting
---

# OBS Studio Control

OBS Studio 28+ ships **obs-websocket v5** built in: a WebSocket server (default port 4455,
password-protected) that exposes almost everything the UI can do — scenes, inputs, scene
items, filters, transitions, outputs, media and UI state — as JSON requests. A job script
runs in a local Python process and talks to the **running** OBS through
[scripts/obs_client.py](scripts/obs_client.py), a standard-library-only v5 client: nothing
to `pip install`, nothing to load inside OBS. Everything here was run against **OBS 32.2.2
with obs-websocket 5.7.4** (macOS). Check `obsWebSocketVersion` in the ping reply; on
another version, `GetVersion` → `availableRequests` is the source of truth.

- [scripts/obs-run.sh](scripts/obs-run.sh) — run a `.py` (or `-c 'inline'`); `--ping`
  checks the connection, `--state` dumps scenes with items, inputs, outputs and settings.
- [scripts/obs-start.sh](scripts/obs-start.sh) — launch OBS (optionally with
  `--collection/--profile/--scene`) and wait for the websocket.
- [scripts/obs_collection.py](scripts/obs_collection.py) — build a whole scene collection
  from a compact spec and either `apply` it live or `install` it as a file.
- [scripts/example-scene-setup.py](scripts/example-scene-setup.py) — a complete
  build → verify job to copy the shape from.

## The control loop

1. **Ping**: `bash scripts/obs-run.sh --ping` →
   `{"ok": true, "obsVersion": "32.2.2", "obsWebSocketVersion": "5.7.4", …}`. On
   `{"ok": false, …}` the error says which case you are in:
   - OBS not running → `bash scripts/obs-start.sh`.
   - Connection refused while OBS runs → the server is off. Only the user can switch it on:
     **Tools ▸ WebSocket Server Settings ▸ Enable WebSocket server** (then OK/Apply). Never
     start a second OBS instance.
   - `4009 authentication failed` → the password in the local config is not the one in use
     (e.g. OBS on another machine); ask for it and set `OBS_PASSWORD`. Never print it.
2. **Look before you build**: `bash scripts/obs-run.sh --state` — collection, profile,
   program scene, canvas size (`video.baseWidth/Height` — positions are in these pixels),
   every scene's items top-to-bottom, inputs, and record/stream/virtualcam/replay status.
3. **Write a job** into the scratchpad, from the cheatsheet and
   [recipes.md](references/recipes.md).
4. **Run it**: `OUT=/abs/outdir bash scripts/obs-run.sh /abs/job.py --arg scene=Main`.
   Output streams back; a failed request raises `ObsRequestError` with its status code and
   OBS's comment, and the run exits 1. Parameters arrive as strings in `ARGS`; `OUT` is where
   screenshots go.
5. **Verify** (below), then **iterate**. The `ensure_*` helpers create-or-update, so a job
   can simply be re-run after a fix.

## Reference routing

| Task | Read |
|---|---|
| A worked pattern: stream layout, lower third, webcam, recording with chapters, replay buffer, audio, media, transitions, hotkeys, Advanced Scene Switcher | [recipes.md](references/recipes.md) |
| Request names, fields, status codes, events, input/filter kinds and their settings | [api-reference.md](references/api-reference.md) |
| Several scenes at once, a reusable layout, a collection file | [scene-collection.md](references/scene-collection.md) |

## Injected namespace

`obs` (a connected `ObsClient`), `OUT`, `ARGS`, `ObsRequestError`, `obs_color`, and these
bound methods as bare functions:

| Helper | Does |
|---|---|
| `call(type, **fields)` | one request → its `responseData` dict; raises on failure |
| `try_call(type, **fields)` | same, but `None` on failure (existence checks) |
| `batch([(type, {fields}), …], halt_on_failure=, execution_type=, raise_on_error=)` | many requests, one round trip |
| `wait_event(type, timeout, match=lambda d: …)` | block for an event (buffered events count) |
| `screenshot(source, path, width=)` | scene or input → PNG/JPG file here; waits a few frames first |
| `ensure_scene(name)` | create unless it exists |
| `ensure_input(scene, name, kind, settings)` | create, or update settings (and add to the scene) → `sceneItemId` |
| `ensure_filter(source, name, kind, settings)` | create, or update and re-enable |
| `set_transform(scene, source, **fields)` | `positionX/Y`, `scaleX/Y`, `rotation`, `alignment`, `bounds*`, `crop*` |
| `item_id(scene, source)`, `scene_names()`, `input_names(kind=None)` | lookups |
| `input_kind(*candidates)` | first kind this OBS build supports |
| `text_settings(kind, text, size=, color=, face=)` | text-source settings for FreeType (macOS/Linux) or GDI+ (Windows) |
| `obs_color("#RRGGBB[AA]")` | the ABGR integer every OBS color setting expects |

## Cheatsheet

```python
W, H = (lambda v: (v["baseWidth"], v["baseHeight"]))(call("GetVideoSettings"))
ensure_scene("Main")
ensure_input("Main", "BG", "color_source_v3", {"color": obs_color("#0b1f3a"), "width": W, "height": H})
kind = input_kind("text_ft2_source_v2", "text_gdiplus_v3")
ensure_input("Main", "Title", kind, text_settings(kind, "Live now", size=72))
set_transform("Main", "Title", positionX=W / 2, positionY=80, alignment=4)   # 4 = top-center
ensure_input("Main", "Logo", "image_source", {"file": "/abs/logo.png"})
set_transform("Main", "Logo", positionX=W - 40, positionY=40, alignment=6, scaleX=0.5, scaleY=0.5)  # top-right
ensure_filter("Logo", "Fade", "color_filter_v2", {"opacity": 0.8})
call("SetCurrentProgramScene", sceneName="Main")
screenshot("Main", f"{OUT}/main.png", width=960)
```

- **Alignment** is a bitmask for the item's anchor point: left 1, right 2, top 4, bottom 8,
  center 0 — top-left 5, bottom-left 9, bottom-right 10, top-right 6. `positionX/Y` places
  that anchor in canvas pixels.
- **Stacking**: new items go on top. `SetSceneItemIndex` with `0` = bottom,
  `len(items) - 1` = top. `GetSceneItemList` returns bottom-to-top; `GetSceneList` returns
  scenes in reverse Scenes-dock order, and that dock order cannot be changed remotely.
- **Fit to a box**: `boundsType="OBS_BOUNDS_SCALE_INNER", boundsWidth=…, boundsHeight=…`
  instead of computing scale.
- **Outputs**: `StartRecord`/`StopRecord` (returns `outputPath`), `PauseRecord`,
  `CreateRecordChapter`, `StartReplayBuffer`/`SaveReplayBuffer`, `StartVirtualCam`,
  `SetInputMute`, `SetInputVolume(inputVolumeDb=…)`. Wait on `RecordStateChanged` rather than
  sleeping — the start is asynchronous.

## Verification

- **Look at it**: `screenshot(scene, path, width=960)` and Read the PNG. Screenshot the
  scene, not the program output — it works for scenes that aren't live. A transparent region
  in a nested scene shows as white or checkered in the PNG; that is alpha, not a bug.
- **Read the state back**: `--state`, `GetSceneItemList`, `GetInputSettings`,
  `GetSourceFilterList`. A successful call is not proof — settings merge (`overlay=True`)
  and a typo'd settings key is accepted silently.
- **Recordings**: take the path from `StopRecord`, then check it with `ffprobe`.

## Gotchas

- **Names are global and case-sensitive.** An input belongs to every scene it is added to;
  creating a second input with an existing name fails with 601. Prefix names per layout
  (`"Stream · Title"`) and use `ensure_*` or check with `input_names()` first. A wrong name → 600.
- **Kinds differ per platform**: text is `text_ft2_source_v2` on macOS/Linux and
  `text_gdiplus_v3` on Windows; capture kinds are `screen_capture`/`macos-avcapture` on
  macOS, `monitor_capture`/`dshow_input` on Windows. Ask with `input_kind()` or
  `GetInputKindList`; get the settings with `GetInputDefaultSettings`.
- **Removals are deferred**: after `RemoveScene`/`RemoveInput` the name can still be listed
  for a moment (and re-creating it fails with 601). Re-read after a short pause before
  verifying or reusing the name.
- **Colors are ABGR integers** (`0xAABBGGRR`), not `#RRGGBB` — always go through `obs_color`.
- **`color_filter_v2` works in linear light**: even `brightness: -0.05` clips a dark source
  to black. Use `saturation`, `contrast` or `opacity` for gentle tweaks.
- **Screenshot right after a change** can show the previous frame — `screenshot()` waits
  150 ms by default. Raise `settle=` for browser sources and media, which take longer to load.
  A browser source that stays blank in the preview too is a CEF problem on that machine, not
  your settings ([recipes.md](references/recipes.md#browser-overlay)).
- **Collection files**: OBS reads the list only at startup and rewrites the open one from
  memory, so never edit the open collection's JSON. When the user asks for a *collection*
  (not just scenes) and OBS is running, `obs_collection.py apply spec.json --new-collection`
  **is** the install: it creates the collection, builds it, and OBS saves the file. Switching
  collections is harmless — the previous one stays intact and one click away — so do it rather
  than building into the open collection. Also `build` the file into `OUT` as the deliverable.
  File-only `install` is for a closed OBS ([scene-collection.md](references/scene-collection.md)).
- **macOS capture needs permission**: without Screen Recording (and Camera/Microphone)
  permission for OBS, capture sources render black. Only the user can grant it, in System
  Settings ▸ Privacy & Security.
- **Localized UI**: default scene/transition names follow the UI language ("Jelenet",
  "Áttűnés" in Hungarian). Read the names from `--state`; never assume "Scene" or "Fade".

## Safety

- **Streaming publishes.** Never call `StartStream`, `StopStream`, `ToggleStream` or
  `SetStreamServiceSettings` without the user's explicit go-ahead in this conversation, and
  never read `GetStreamServiceSettings` into the output — it holds the stream key.
- The open collection is the user's show. Build into new, prefixed scenes and inputs, and
  ask before `RemoveScene`, `RemoveInput`, `RemoveSceneItem`, `RemoveSourceFilter`,
  switching collection or profile, or changing `SetVideoSettings`/`SetProfileParameter`.
- `SetCurrentProgramScene` changes what viewers see if the user is live — check
  `stream.outputActive` in `--state` first, and in studio mode prefer
  `SetCurrentPreviewScene`.
- Recordings land in the user's recording folder: tell them the path, and delete only test
  files you made yourself.

## Security

- obs-websocket gives any client that has the password full control of OBS, including
  starting a stream and reading the stream key. Keep **authentication on**; the server
  listens on every interface, so on a shared network the password is the only barrier.
- The client reads the password from OBS's own config
  (`…/obs-studio/plugin_config/obs-websocket/config.json`) when `OBS_PASSWORD` is unset,
  and never prints it. Never paste it into output, job scripts or files.
- Job scripts are ordinary Python running as the user. Keep them in the scratchpad.
