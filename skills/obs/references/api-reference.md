# obs-websocket v5 — condensed API reference

Checked against **OBS 32.2.2 / obs-websocket 5.7.4** (151 requests). The authoritative spec,
with every field and event, is
[protocol.md](https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md).
On any other version, `call("GetVersion")["availableRequests"]` lists what exists.

Every request that names a scene or source accepts either `sceneName`/`sourceName`/`inputName`
**or** the matching `…Uuid`. UUIDs survive renames; names are what users see.

## Contents

- [Requests by category](#requests-by-category)
- [Scene item transform](#scene-item-transform)
- [Input kinds and their settings](#input-kinds-and-their-settings)
- [Filter kinds](#filter-kinds)
- [Status codes](#status-codes)
- [Events](#events)
- [Batches](#batches)

## Requests by category

**General** — `GetVersion` (obsVersion, availableRequests, supportedImageFormats), `GetStats`
(fps, CPU, dropped frames), `BroadcastCustomEvent {eventData}`, `CallVendorRequest {vendorName,
requestType, requestData}`, `GetHotkeyList`, `TriggerHotkeyByName {hotkeyName, contextName?}`,
`TriggerHotkeyByKeySequence {keyId, keyModifiers}`, `Sleep {sleepMillis | sleepFrames}` (batches only).

**Config** — `GetPersistentData`/`SetPersistentData {realm, slotName, slotValue}`,
`GetSceneCollectionList`, `SetCurrentSceneCollection`, `CreateSceneCollection` (both block
until the switch is done; there is **no** remove), `GetProfileList`, `SetCurrentProfile`,
`CreateProfile`, `RemoveProfile`, `GetProfileParameter`/`SetProfileParameter {parameterCategory,
parameterName, parameterValue}`, `GetVideoSettings`/`SetVideoSettings {baseWidth, baseHeight,
outputWidth, outputHeight, fpsNumerator, fpsDenominator}`, `GetStreamServiceSettings` (contains the
stream key — never print), `SetStreamServiceSettings`, `GetRecordDirectory`/`SetRecordDirectory`.

**Sources** — `GetSourceActive`, `GetSourceScreenshot {sourceName, imageFormat, imageWidth?,
imageHeight?, imageCompressionQuality?}` → `imageData` (a `data:` URI), `SaveSourceScreenshot`
(same + `imageFilePath`, written by OBS on its machine), `Get/SetSourcePrivateSettings`.

**Canvases** — `GetCanvasList` (OBS 32: the main canvas is named `Main`; error comments mention it).

**Scenes** — `GetSceneList` (→ `scenes` in *reverse* Scenes-dock order, plus current program/preview),
`GetGroupList`, `GetCurrentProgramScene`, `SetCurrentProgramScene`, `GetCurrentPreviewScene`,
`SetCurrentPreviewScene` (studio mode only), `CreateScene`, `RemoveScene`, `SetSceneName {sceneName,
newSceneName}`, `Get/SetSceneSceneTransitionOverride {transitionName, transitionDuration}`. The
Scenes-dock order cannot be changed over the websocket.

**Inputs** — `GetInputList {inputKind?}`, `GetInputKindList {unversioned?}`, `GetSpecialInputs`
(desktop/mic audio device inputs), `CreateInput {sceneName, inputName, inputKind, inputSettings?,
sceneItemEnabled?}` → `sceneItemId`, `RemoveInput`, `SetInputName`, `GetInputDefaultSettings
{inputKind}`, `GetInputSettings`, `SetInputSettings {inputName, inputSettings, overlay=true}`
(`overlay=false` resets unspecified keys to defaults), `Get/SetInputMute`, `ToggleInputMute`,
`Get/SetInputVolume {inputVolumeMul | inputVolumeDb}`, `Get/SetInputAudioBalance` (0–1),
`Get/SetInputAudioSyncOffset` (ms), `Get/SetInputAudioMonitorType`
(`OBS_MONITORING_TYPE_NONE|MONITOR_ONLY|MONITOR_AND_OUTPUT`), `Get/SetInputAudioTracks`
(`{"1": true, …}`), `Get/SetInputDeinterlaceMode`, `…FieldOrder`,
`GetInputPropertiesListPropertyItems {inputName, propertyName}` (e.g. the camera list for
`device`, displays for `display_uuid`), `PressInputPropertiesButton {inputName, propertyName}`
(e.g. a browser source's `refreshnocache`), `OpenInputPropertiesDialog`/`FiltersDialog`/`InteractDialog`.

**Transitions** — `GetTransitionKindList`, `GetSceneTransitionList`, `GetCurrentSceneTransition`,
`SetCurrentSceneTransition {transitionName}`, `SetCurrentSceneTransitionDuration {transitionDuration}`
(ms), `SetCurrentSceneTransitionSettings`, `GetCurrentSceneTransitionCursor`,
`TriggerStudioModeTransition`, `SetTBarPosition {position, release?}`. Transition names are
localized ("Fade" is "Áttűnés" in Hungarian) — read them, don't assume.

**Filters** — `GetSourceFilterKindList`, `GetSourceFilterList {sourceName}`,
`GetSourceFilterDefaultSettings {filterKind}`, `CreateSourceFilter {sourceName, filterName,
filterKind, filterSettings?}`, `RemoveSourceFilter`, `SetSourceFilterName`, `GetSourceFilter`,
`SetSourceFilterIndex {filterIndex}`, `SetSourceFilterSettings {filterSettings, overlay}`,
`SetSourceFilterEnabled {filterEnabled}`. Filters go on inputs *and* scenes.

**Scene items** — `GetSceneItemList {sceneName}` (bottom-to-top), `GetGroupSceneItemList`,
`GetSceneItemId {sceneName, sourceName, searchOffset?}`, `GetSceneItemSource`, `CreateSceneItem
{sceneName, sourceName, sceneItemEnabled?}` (adds an existing input or a scene — nesting),
`RemoveSceneItem`, `DuplicateSceneItem {destinationSceneName?}`, `Get/SetSceneItemTransform`,
`Get/SetSceneItemEnabled`, `Get/SetSceneItemLocked`, `Get/SetSceneItemIndex` (0 = bottom),
`Get/SetSceneItemBlendMode` (`OBS_BLEND_NORMAL|ADDITIVE|SUBTRACT|SCREEN|MULTIPLY|LIGHTEN|DARKEN`),
`Get/SetSceneItemPrivateSettings`.

**Outputs** — `GetVirtualCamStatus`, `Start/Stop/ToggleVirtualCam`, `GetReplayBufferStatus`
(fails with 604 when the replay buffer is disabled in Settings ▸ Output),
`Start/Stop/ToggleReplayBuffer`, `SaveReplayBuffer`, `GetLastReplayBufferReplay` → `savedReplayPath`,
`GetOutputList`, `GetOutputStatus`, `Start/Stop/ToggleOutput`, `Get/SetOutputSettings {outputName}`.

**Stream** — `GetStreamStatus` (outputActive, outputTimecode, outputSkippedFrames, …),
`StartStream`, `StopStream`, `ToggleStream`, `SendStreamCaption {captionText}`. See Safety in SKILL.md.

**Record** — `GetRecordStatus`, `StartRecord`, `StopRecord` → `outputPath`, `ToggleRecord`,
`PauseRecord`, `ResumeRecord`, `ToggleRecordPause`, `SplitRecordFile` (needs "automatic file
splitting" enabled), `CreateRecordChapter {chapterName?}` (Hybrid MP4/MOV output only).

**Media inputs** — `GetMediaInputStatus` (mediaState, mediaDuration, mediaCursor ms),
`SetMediaInputCursor {mediaCursor}`, `OffsetMediaInputCursor {mediaCursorOffset}`,
`TriggerMediaInputAction {mediaAction: OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PLAY|PAUSE|STOP|RESTART|NEXT|PREVIOUS}`.

**Ui** — `GetStudioModeEnabled`/`SetStudioModeEnabled`, `OpenSourceProjector`,
`OpenVideoMixProjector {videoMixType, monitorIndex?}`, `GetMonitorList`.

## Scene item transform

`GetSceneItemTransform` returns, and `SetSceneItemTransform {sceneItemTransform: {…}}` accepts a
subset of:

| Field | Meaning |
|---|---|
| `positionX`, `positionY` | canvas pixels of the anchor point |
| `alignment` | anchor bitmask: left 1, right 2, top 4, bottom 8; center 0 → top-left 5, top-right 6, bottom-left 9, bottom-right 10 |
| `scaleX`, `scaleY` | 1.0 = source size |
| `rotation` | degrees, clockwise |
| `boundsType` | `OBS_BOUNDS_NONE` · `STRETCH` · `SCALE_INNER` (fit) · `SCALE_OUTER` (fill) · `SCALE_TO_WIDTH` · `SCALE_TO_HEIGHT` · `MAX_ONLY` |
| `boundsWidth`, `boundsHeight`, `boundsAlignment` | the box used when `boundsType` ≠ NONE (width/height must be ≥ 1) |
| `cropLeft/Right/Top/Bottom` | pixels, before scaling |
| `sourceWidth/Height`, `width/height` | read-only: native and on-canvas size |

## Input kinds and their settings

Ask for the platform's list with `GetInputKindList`, then `GetInputDefaultSettings` for the keys.
Defaults below are OBS 32.2 on macOS.

| Kind | Key settings |
|---|---|
| `color_source_v3` | `color` (ABGR int), `width`, `height` |
| `text_ft2_source_v2` (macOS/Linux) | `text`, `font {face, size, style, flags}` (size defaults to **256**), `color1`/`color2` (gradient top/bottom, ABGR), `outline`, `drop_shadow`, `word_wrap`, `custom_width`, `from_file`, `text_file` |
| `text_gdiplus_v3` (Windows) | `text`, `font {…}`, `color` (BGR), `opacity` 0–100, `bk_color`, `bk_opacity`, `align`, `valign`, `outline`, `extents`, `extents_cx/cy` |
| `image_source` | `file` (absolute path), `unload`, `linear_alpha` |
| `ffmpeg_source` (media) | `local_file`, `is_local_file`, `input` (URL when not local), `looping`, `restart_on_activate`, `clear_on_media_end`, `close_when_inactive`, `speed_percent` |
| `browser_source` | `url` or `is_local_file` + `local_file`, `width`, `height`, `css`, `fps`, `reroute_audio`, `shutdown`, `restart_when_active` |
| `slideshow_v2` | `files [{value: path}]`, `slide_time` ms, `transition`, `playback_mode`, `use_custom_size` |
| `screen_capture` (macOS 13+ ScreenCaptureKit) | `type` 0 display / 1 window / 2 application, `display_uuid`, `window`, `application`, `show_cursor`, `hide_obs` |
| `macos-avcapture` / `av_capture_input_v2` | `device` (id from `GetInputPropertiesListPropertyItems … propertyName="device"`), `preset`, `enable_audio` |
| `coreaudio_input_capture` / `coreaudio_output_capture` | `device_id` (`default`) |
| Windows | `monitor_capture`, `window_capture`, `game_capture`, `dshow_input` (webcam), `wasapi_input_capture`, `wasapi_output_capture` |

## Filter kinds

Video: `color_filter_v2` (`brightness`, `contrast`, `saturation`, `gamma`, `hue_shift`,
`opacity`, `color_multiply`, `color_add` — works in linear light), `chroma_key_filter_v2`
(`key_color_type` green/blue/magenta/custom, `key_color`, `similarity` 400, `smoothness` 80, `spill`),
`color_key_filter_v2`, `luma_key_filter_v2`, `crop_filter` (`left/right/top/bottom`, `relative`),
`scroll_filter` (`speed_x`, `speed_y`, `loop`), `mask_filter_v2` (`image_path`, `type`),
`sharpness_filter_v2`, `scale_filter`, `clut_filter` (LUT: `image_path`, `clut_amount`),
`gpu_delay`, `hdr_tonemap_filter`.
Audio: `noise_suppress_filter_v2` (`method` rnnoise/speex, `suppress_level`), `noise_gate_filter`,
`gain_filter` (`db`), `compressor_filter`, `limiter_filter`, `expander_filter`,
`upward_compressor_filter`, `basic_eq_filter`, `invert_polarity_filter`, `async_delay_filter`, `vst_filter`.

## Status codes

| Code | Name | Usual cause |
|---|---|---|
| 100 | Success | |
| 204 | UnknownRequestType | typo, or a request newer than this OBS |
| 300 / 400 / 402 | MissingRequestField / InvalidRequestField / …FieldType | wrong field name or type (e.g. string for a number) |
| 500 / 501 | OutputRunning / OutputNotRunning | start while running, stop while stopped |
| 505 / 506 | StudioModeActive / NotActive | preview-scene calls outside studio mode |
| 600 | ResourceNotFound | wrong (case-sensitive) name |
| 601 | ResourceAlreadyExists | input/scene name already taken — names are global |
| 604 | InvalidInputKind / resource state | kind not on this platform; replay buffer not enabled |
| 700–702 | Creation/Action/Processing failed | OBS refused the operation; read the comment |

## Events

The client subscribes to every non-high-volume category and buffers events; `wait_event` reads
them. Useful ones: `RecordStateChanged` / `StreamStateChanged` / `ReplayBufferStateChanged` /
`VirtualcamStateChanged` (`outputState`: `OBS_WEBSOCKET_OUTPUT_STARTING|STARTED|STOPPING|STOPPED|PAUSED|RESUMED`,
`outputPath`), `ReplayBufferSaved {savedReplayPath}`, `RecordFileChanged`, `CurrentProgramSceneChanged`,
`SceneTransitionEnded`, `MediaInputPlaybackEnded`, `InputSettingsChanged`, `CurrentSceneCollectionChanged`,
`ExitStarted`, `CustomEvent`, `VendorEvent`. High-volume events (`InputVolumeMeters`,
`InputActiveStateChanged`, `SceneItemTransformChanged`) need an explicit mask:
`ObsClient(events=EVENTS_ALL | (1 << 16))` for volume meters.

## Batches

`batch([...], execution_type=…)`: 0 serial-realtime (default), 1 serial-frame (each request on
its own rendered frame; `("Sleep", {"sleepFrames": n})` for frame-exact timing), 2 parallel (no
ordering). `halt_on_failure=True` stops at the first error. With `raise_on_error=False` a failed
request comes back as `None` in its slot.
