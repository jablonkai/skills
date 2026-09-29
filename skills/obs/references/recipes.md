# OBS recipes

Job-script patterns for `obs-run.sh`. Each one relies on the injected helpers (see SKILL.md)
and is re-runnable. Names are prefixed per layout because OBS input names are global.

## Contents

- [Stream layout: Starting Soon / Main / BRB](#stream-layout-starting-soon--main--brb)
- [Lower third](#lower-third)
- [Webcam or screen in a frame](#webcam-or-screen-in-a-frame)
- [Browser overlay](#browser-overlay)
- [Record a take with chapters](#record-a-take-with-chapters)
- [Replay buffer](#replay-buffer)
- [Audio: volume, mute, noise suppression](#audio-volume-mute-noise-suppression)
- [Media input playback](#media-input-playback)
- [Transitions and switching scenes](#transitions-and-switching-scenes)
- [Hotkeys, vendor requests, Advanced Scene Switcher](#hotkeys-vendor-requests-advanced-scene-switcher)
- [Working on the user's existing scenes](#working-on-the-users-existing-scenes)

## Stream layout: Starting Soon / Main / BRB

For several scenes at once, write a spec and use `obs_collection.py apply` — see
[scene-collection.md](scene-collection.md). It handles nesting, ordering and re-runs for you.

## Lower third

```python
scene, p = ARGS.get("scene", "Interview"), ARGS.get("prefix", "LT")
W, H = (lambda v: (v["baseWidth"], v["baseHeight"]))(call("GetVideoSettings"))
ensure_scene(scene)
ensure_input(scene, f"{p} · Bar", "color_source_v3",
             {"color": obs_color("#00adefe6"), "width": int(W * .42), "height": int(H * .10)})
set_transform(scene, f"{p} · Bar", positionX=int(W * .04), positionY=int(H * .92), alignment=9)  # bottom-left
kind = input_kind("text_ft2_source_v2", "text_gdiplus_v3")
ensure_input(scene, f"{p} · Name", kind, text_settings(kind, ARGS["name"], size=int(H * .045)))
set_transform(scene, f"{p} · Name", positionX=int(W * .06), positionY=int(H * .87), alignment=1)  # left, v-centered
screenshot(scene, f"{OUT}/{scene}.png", width=960)
```

The bar's vertical center is `0.92H − 0.05H = 0.87H`, so the text anchored at left-center
sits in the middle of the bar. For a name + role pair, use two text inputs at ±0.02H.
To show/hide it live: `call("SetSceneItemEnabled", sceneName=scene, sceneItemId=item_id(scene, f"{p} · Name"), sceneItemEnabled=False)`.

## Webcam or screen in a frame

```python
kind = input_kind("macos-avcapture", "av_capture_input_v2", "dshow_input", "v4l2_input")
ensure_input(scene, "Cam", kind, {})
devices = call("GetInputPropertiesListPropertyItems", inputName="Cam",
               propertyName="device" if kind != "dshow_input" else "video_device_id")["propertyItems"]
print([(d["itemName"], d["itemValue"]) for d in devices])       # pick one, or ask the user
call("SetInputSettings", inputName="Cam", inputSettings={"device": devices[0]["itemValue"]})
set_transform(scene, "Cam", boundsType="OBS_BOUNDS_SCALE_INNER", boundsWidth=640, boundsHeight=360,
              positionX=W - 40, positionY=H - 40, alignment=10)  # bottom-right, fit into 640×360
```

Screen: `screen_capture` on macOS (`type` 0 display, list with `propertyName="display_uuid"`),
`monitor_capture` on Windows. A black result on macOS means OBS lacks Screen Recording or
Camera permission — only the user can grant it.

## Browser overlay

```python
ensure_input(scene, "Alerts", "browser_source", {"url": ARGS["url"], "width": 1920, "height": 1080,
                                                 "css": "body{background:transparent;margin:0}"})
call("PressInputPropertiesButton", inputName="Alerts", propertyName="refreshnocache")  # reload
screenshot(scene, f"{OUT}/overlay.png", width=960, settle=2.0)   # pages need time to load
```

If the source stays empty in the screenshot **and** in the OBS preview, the browser plugin
(CEF) itself is not rendering on that machine — seen with OBS 32.2.2 on macOS 27, for URLs and
local files alike. That cannot be fixed over the websocket: tell the user, and suggest
toggling Settings ▸ Advanced ▸ *Browser Source Hardware Acceleration* and restarting OBS.

## Record a take with chapters

```python
import time
if call("GetRecordStatus")["outputActive"]:
    raise SystemExit("already recording — ask the user before touching it")
call("StartRecord")
started = wait_event("RecordStateChanged", 15, lambda d: d["outputState"] == "OBS_WEBSOCKET_OUTPUT_STARTED")
time.sleep(float(ARGS.get("chapter_at", 5)))
call("CreateRecordChapter", chapterName=ARGS.get("chapter", "5s"))  # Hybrid MP4/MOV only
time.sleep(float(ARGS.get("rest", 5)))
path = call("StopRecord")["outputPath"]
wait_event("RecordStateChanged", 30, lambda d: d["outputState"] == "OBS_WEBSOCKET_OUTPUT_STOPPED")
print("recorded:", path)
```

Check the file with `ffprobe -show_chapters "<path>"`. `CreateRecordChapter` fails
(702) on plain MP4/MKV output — fall back to noting timestamps, or ask the user to switch the
recording format to Hybrid MP4/MOV. `SplitRecordFile` needs automatic file splitting enabled.
The recording folder comes from `GetRecordDirectory`; change it only when asked.

## Replay buffer

`GetReplayBufferStatus` fails with 604 until the user enables *Replay Buffer* in Settings ▸
Output (it is a profile setting). Then:

```python
if not call("GetReplayBufferStatus")["outputActive"]:
    call("StartReplayBuffer")
    wait_event("ReplayBufferStateChanged", 15, lambda d: d["outputState"] == "OBS_WEBSOCKET_OUTPUT_STARTED")
# … later, after the moment happened:
call("SaveReplayBuffer")
print(wait_event("ReplayBufferSaved", 30)["savedReplayPath"])
```

## Audio: volume, mute, noise suppression

```python
mic = call("GetSpecialInputs")["mic1"] or next(
    (i["inputName"] for i in call("GetInputList")["inputs"] if "input_capture" in i["inputKind"]), None)
call("SetInputVolume", inputName=mic, inputVolumeDb=-6.0)       # or inputVolumeMul=0.5
call("SetInputMute", inputName=mic, inputMuted=False)
ensure_filter(mic, "Noise", "noise_suppress_filter_v2", {"method": "rnnoise"})
ensure_filter(mic, "Gate", "noise_gate_filter", {"open_threshold": -26.0, "close_threshold": -32.0})
```

`GetSpecialInputs` returns the Settings ▸ Audio global devices, and they may all be `None`: a
fresh collection often has its mic as a plain input instead, as the second branch shows.

## Media input playback

```python
ensure_input(scene, "Intro", "ffmpeg_source", {"local_file": "/abs/intro.mp4", "is_local_file": True,
                                               "restart_on_activate": True, "looping": False})
call("TriggerMediaInputAction", inputName="Intro", mediaAction="OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART")
st = call("GetMediaInputStatus", inputName="Intro")       # mediaState, mediaDuration, mediaCursor (ms)
wait_event("MediaInputPlaybackEnded", st["mediaDuration"] / 1000 + 5, lambda d: d["inputName"] == "Intro")
```

## Transitions and switching scenes

```python
names = [t["transitionName"] for t in call("GetSceneTransitionList")["transitions"]]  # localized!
call("SetCurrentSceneTransition", transitionName=names[0])
call("SetCurrentSceneTransitionDuration", transitionDuration=500)
call("SetSceneSceneTransitionOverride", sceneName="BRB", transitionName=names[0], transitionDuration=800)
call("SetCurrentProgramScene", sceneName="BRB")
wait_event("SceneTransitionEnded", 5)
```

In studio mode (`GetStudioModeEnabled`), set the preview with `SetCurrentPreviewScene`, and go
live with `TriggerStudioModeTransition` only when the user says so. Timed sequences:
`batch([...], execution_type=1)` with `("Sleep", {"sleepFrames": 60})` between steps.

## Hotkeys, vendor requests, Advanced Scene Switcher

- `GetHotkeyList` lists names such as `OBSBasic.StartRecording`, `OBSBasic.Screenshot`,
  `libobs.show_scene_item.<id>`; `TriggerHotkeyByName {hotkeyName}` fires one. Prefer the
  direct request when one exists — a hotkey can have side effects such as
  `OBSBasic.Screenshot`, which writes a PNG into the recording folder.
- Plugins expose requests through `CallVendorRequest {vendorName, requestType, requestData}`.
  Advanced Scene Switcher: `vendorName="AdvancedSceneSwitcher"`,
  `requestType="AdvancedSceneSwitcherMessage"`, `requestData={"message": "…"}`; its macros see
  the message through a *Websocket* condition, and they reply with `VendorEvent`
  (`AdvancedSceneSwitcherEvent`). A 204/600-range failure means the plugin is not installed.
- `BroadcastCustomEvent {eventData}` reaches every connected client (e.g. a browser-source
  overlay listening with obs-websocket-js) as `CustomEvent`.

## Working on the user's existing scenes

Start from `--state`. Change only what was asked: `SetInputSettings` with `overlay=True`
merges, and `set_transform` only touches the fields passed. Before changing an item, record its
current transform/settings (`GetSceneItemTransform`, `GetInputSettings`) and print them, so the
change can be undone on request. If `stream.outputActive` is true, the user is live — confirm
before anything that changes the program output.
