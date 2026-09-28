# DaVinci Resolve scripting — gotchas

Everything here was reproduced against **DaVinci Resolve Studio 21.1.0** through
`scripts/resolve-run.sh`. Most of what a model remembers about this API comes from the
18–20 era README and blog posts, and several of those habits now fail silently.

## Contents

1. [Failure is silent](#1-failure-is-silent)
2. [Two frame conventions](#2-two-frame-conventions)
3. [21.1 calling conventions](#3-211-calling-conventions)
4. [Import](#4-import)
5. [Appending clips](#5-appending-clips)
6. [Insert* ripples the whole timeline](#6-insert-ripples-the-whole-timeline)
7. [Fusion compositions](#7-fusion-compositions)
8. [Settings](#8-settings)
9. [Rendering](#9-rendering)
10. [Global UI state](#10-global-ui-state)
11. [Blocking and connection](#11-blocking-and-connection)
12. [Free vs Studio](#12-free-vs-studio)
13. [Stale official examples](#13-stale-official-examples)

## 1. Failure is silent

The API never raises for a bad call — it returns `False`, `None`, an empty list or `''`, and
the script carries on. `GetItemListInTrack("video", 99)` → `None`; `SetLUT(1, "typo.cube")` →
`False`; `AddTransition` without handles → `None`. Wrap every mutating call in
`need(result, "what")` (injected), or at least check it — a job that ignores return values
produces a half-built timeline and reports success.

- `SetSettings({...})` applies keys one by one; on failure the earlier keys **stay applied**
  and the call returns `False`.
- `SetProperties({...})` is all-or-nothing: one unknown key (`{"ZoomX": 1.1, "Nope": 1}`) and
  nothing is set.

## 2. Two frame conventions

Timelines start at `01:00:00:00`, so frame numbers are large: 86400 at 24 fps, 90000 at 25,
108000 at 29.97 (timecode counts at the rounded rate — 30 — even for 29.97 non-drop).

| API | Frame means |
|---|---|
| `AppendToTimeline` `recordFrame`, `TimelineItem.GetStart/GetEnd`, `Timeline.GetStartFrame/GetEndFrame` | **absolute** timeline frame |
| `Timeline.AddMarker(frameId)`, `Timeline.GetMarkers()` keys | **offset from timeline start** |
| `TimelineItem.AddMarker(frameId)` | offset from the item's start |
| `MediaPoolItem.AddMarker(frameId)`, `startFrame`/`endFrame` in clip infos | source frame, 0-based |

Mixing them fails quietly: `AddMarker(tl.GetStartFrame() + 50, ...)` returns `True` and puts
the marker an hour past the end; `recordFrame: 0` puts the clip before the visible start.
Use `at(seconds)` for record positions and `marker(seconds, ...)` for markers.

- `endFrame` is **exclusive**: `startFrame 25, endFrame 75` gives 50 frames.
- `endFrame` without `startFrame` is ignored — the whole clip is appended.
- `GetEnd()` is exclusive too (`GetEnd() - GetStart() == GetDuration()`).
- Drop-frame timelines (`timelineDropFrameTimecode == '1'`) format timecode with `;` —
  `tc_to_frame` / `frame_to_tc` handle both.
- Indices are 1-based everywhere: tracks, `GetTimelineByIndex(1..count)`, graph nodes, takes,
  Fusion comps.

## 3. 21.1 calling conventions

21.1 deprecated the overloaded forms. Prefer the canonical form — the old ones still work
today but are on their way out:

| Deprecated | Use |
|---|---|
| `AppendToTimeline(clip1, clip2)` / `([clips])` | `AppendToTimeline([{"mediaPoolItem": c} for c in clips])` |
| `CreateTimelineFromClips(name, [clips])` | `CreateTimelineFromClips(name, [{"mediaPoolItem": c} ...])` |
| `project.SetSetting(k, v)` / `GetSetting(k)` | `SetSettings({k: v})` / `GetSettings()[k]` |
| `item.SetProperty(k, v)` / `GetProperty(k)` | `SetProperties({k: v})` / `GetProperties()[k]` |
| `SetMetadata(k, v)` | `SetMetadata({k: v})` |
| `item.SetLUT` / `GetNumNodes` / `GetNodeLabel` | `item.GetNodeGraph().SetLUT(...)` etc. |
| `GetItemsInTrack`, `GetClips`, `GetSubFolders`, `GetFlags`, `GetMountedVolumes` | the `...List` variants |
| `StartRendering(index...)` | job ids: `StartRendering([job_id])` |

Exception: `SetSetting('superScale', 2, sharpness, noiseReduction)` has no `SetSettings`
equivalent and is not deprecated.

## 4. Import

- **`MediaPool.ImportMedia([{"FilePath": p}])` — the README's canonical form — returns
  `None` for ordinary files in 21.1.0.** It is meant for image sequences (`%04d` +
  `StartIndex`/`EndIndex`). For files, `MediaStorage.AddItemListToMediaPool([{"media": p}])`
  works; `ImportMedia([p1, p2])` (path list) is the fallback. `import_media()` does this.
- Import lands in the Media Pool's **current folder** — `SetCurrentFolder(bin)` first.
- Resolve dedupes by path on its own, but a *different* file with the same name in the bin is
  a separate clip: match on `GetClipProperty()["File Path"]`, never on `GetName()`.
- Skip macOS AppleDouble `._*` files on external drives — they import as broken clips.
- `.srt` imports as a clip of type `Subtitle`; appending it fills a subtitle track (one
  timeline item per caption).

## 5. Appending clips

- `AppendToTimeline` targets the **current** timeline — `SetCurrentTimeline` first.
- A `trackIndex` beyond `GetTrackCount()` does **not** fail: the clip lands somewhere else
  (observed: V1). Create tracks first (`ensure_tracks`, `AddTrack`).
- Without `mediaType` a clip with audio lands on V`n` + A`n`; the returned list holds only
  the video item — `item.GetLinkedItems()` gives its audio. `mediaType: 1` = video only,
  `2` = audio only.
- `recordFrame` past the end leaves a gap; omitted, the clip is appended after the last item.
- No API moves or trims an item already on the timeline. To change placement: `DeleteClips`
  and append again.
- `TimelineItem.AddTransition` needs media handles on the side it overlaps; a full-length clip
  has none. `{"type": "Cross Dissolve", "category": "simple", "position": "end",
  "alignment": "left"}` on an outgoing clip that was trimmed (so has tail handle) works.

## 6. Insert* ripples the whole timeline

`InsertTitleIntoTimeline`, `InsertFusionTitleIntoTimeline`, `InsertGeneratorIntoTimeline`,
`InsertFusionGeneratorIntoTimeline`, `InsertOFXGeneratorIntoTimeline` and
`InsertFusionCompositionIntoTimeline` perform an **Edit-page insert edit**:

- at the playhead, on whichever track the UI's destination control points at (not settable
  from the API),
- **rippling every unlocked track** — clips under the playhead are split and everything after
  shifts right by the item's length (5 s by default),
- the playhead then jumps to the end of the inserted item,
- with the other tracks locked, the call returns `None` instead.

Never call them on a timeline that already holds an edit. `title_clip()` inserts on a
throwaway timeline, compounds the result, and returns a Media Pool item you can `place()` on
any track at any frame. A title is 5 s and cannot be lengthened — trim it with `src_out`;
extending a compound past its own length renders blank. The compound lands in the current
Media Pool folder.

## 7. Fusion compositions

- **`TimelineItem.AddFusionComp()` returns a composition that is never rendered** (21.1.0):
  tools built on it look right, `ExportFusionComp` shows them wired, but the Edit page and
  renders ignore them. `ImportFusionComp(path)` works — `overlay_text()` imports
  [assets/text-overlay.comp](../assets/text-overlay.comp), whose `MediaIn1` rebinds to the host
  clip.
- Live edits to a comp that is already attached do render: a title's comp
  (`item.GetFusionCompByIndex(1)`), or one you imported.
- Find tools with `comp.FindTool("Text1")` (name) or `comp.FindToolByID("TextPlus")` (type);
  a Fusion title's Text+ is named `Template`.
- Set inputs with `tool.SetInput("StyledText", "…")`; points take a dict,
  `SetInput("Center", {1: 0.5, 2: 0.15})` (0–1, origin bottom-left).
- Wire with `merge.ConnectInput("Foreground", tool)`; read with
  `merge.Background.GetConnectedOutput().GetTool().Name`.
- `comp.Lock()` / `comp.Unlock()` around bulk `AddTool` calls suppresses dialogs.
- `fusion.CurrentComp` is `None` unless the Fusion page is showing a clip.

## 8. Settings

- `GetSettings()` values are strings (`'1920'`), except `timelineFrameRate`, which comes back
  as a number (`29.97`) and is set as a string (`'29.97'`, `'29.97 DF'`).
- A new project defaults to **3840×2160**. Set `timelineFrameRate` and resolution right after
  `CreateProject`, before the first timeline or clip — the frame rate locks once a timeline
  has media.
- Per-timeline settings only apply after `{"useCustomSettings": "1"}` (same call is fine —
  it is applied first). Without it `Timeline.SetSettings` returns `False` and
  `Timeline.GetSettings()` returns the project's settings. This is how a 1080×1920 vertical
  timeline lives next to a 16:9 one. A timeline without custom settings has **no**
  `useCustomSettings` key in `GetSettings()` — read it with `.get("useCustomSettings", "0")`.
- Discover a key by changing it in the UI and diffing `GetSettings()` before and after.

## 9. Rendering

- `LoadRenderPreset` **overwrites** format, codec and settings — load the preset first, then
  `SetCurrentRenderFormatAndCodec`, then `SetRenderSettings`.
- Format is the **extension key** (`'mp4'`, `'mov'`); codec is the **value** of
  `GetRenderCodecs(ext)` (`'H264'`, `'H265'`, `'ProRes422HQ'`), not its description.
- `SelectAllFrames: True` ignores `MarkIn`/`MarkOut`; pass `False` for a range (absolute
  frames).
- `AddRenderJob` snapshots the **current** timeline and settings at that moment.
- A `/`, `:` or other path character in the timeline name (used by the default output name)
  makes the render fail without a useful error — pass `CustomName`.
- `GetRenderJobStatus(id)["JobStatus"]` ends as `Complete`, `Failed` or `Cancelled`; the
  output path is `TargetDir` + `OutputFilename` from `GetRenderJobList()`.
- Finished jobs stay in the Deliver queue — `render()` deletes its own; never
  `DeleteAllRenderJobs()` on a user's project.
- `Timeline.Export(path, resolve.EXPORT_FCPXML_1_10, resolve.EXPORT_NONE)` writes an
  `.fcpxmld`-style **directory**, not a file. EDL/AAF need a real subtype
  (`EXPORT_NONE`/`EXPORT_CDL`/… for EDL, `EXPORT_AAF_NEW`/`EXPORT_AAF_EXISTING` for AAF).

## 10. Global UI state

Almost everything acts on "current" state shared with the user's UI: current project,
current timeline, current Media Pool folder, current page, playhead. A script that changes
them leaves the user somewhere else. `title_clip()` restores the current timeline; restore the
rest yourself when it matters (remember `project.GetCurrentTimeline()` and
`resolve.GetCurrentPage()` at the start).

- `ExportCurrentFrameAsStill(path)` exports the frame under the playhead of the current
  timeline — set it with `tl.SetCurrentTimecode(frame_to_tc(f))`. Fast visual check.
- `GrabStill()` / Graph grade calls want the Color page (`OpenPage("color")`).
- `LoadProject`/`CreateProject` switch the user's open project — `SaveProject()` first and
  ask before doing it.

## 11. Blocking and connection

- **An open menu, context menu or modal dialog in Resolve stalls its script server**: every
  call blocks until the user closes it. Output stops mid-script with no error. Tell the user;
  don't retry in a loop.
- Some dialogs don't block but break the API instead: after a render from the **Fusion
  page** (`comp.Render()`), a "Render completed!" message box stays open and calls such as
  `GetCurrentPage()`, `OpenPage()`, `SetCurrentFolder()` and `ExportCurrentFrameAsStill()`
  return `None` until someone clicks OK. If `resolve.GetCurrentPage()` returns `None`,
  stop and ask the user to dismiss the dialog. Don't render from Fusion — use `render()`.
- `scriptapp("Resolve")` blocks while Resolve is starting or quitting; the runner gives up
  after `RESOLVE_CONNECT_TIMEOUT` seconds (default 20).
- **Resolve can freeze outright.** Twice in testing (21.1.0), a job that duplicated a
  timeline stopped mid-way, an unlabelled modal dialog appeared, and Resolve had to be
  force-quit. The same sequence ran cleanly in a fresh session, so the trigger is not
  isolated — both happened in long sessions after heavy Fusion work. Keep jobs small and
  set `RESOLVE_JOB_TIMEOUT` so a stuck job ends instead of waiting forever; after a
  timeout, `--ping` — if that also times out, ask the user to check Resolve. `copy_timeline()`
  (DRT export + import) avoids `DuplicateTimeline()` if you want to rule it out.
- Calls are serialised — two scripts driving the same Resolve interleave on shared current
  state. Run jobs one at a time.
- ResolvePython (21.1+) has no `pip`; for extra packages use your own Python with the SDK
  environment variables (`RESOLVE_PYTHON=python3`).

## 12. Free vs Studio

- External scripting (from a terminal) is configured in **Studio** under Preferences ▸
  System ▸ General ▸ *External scripting using*: None / Local / Network. The free edition
  runs scripts from **Workspace ▸ Scripts** and the Console; install the job there (see
  [recipes.md](recipes.md#running-inside-resolve-free-edition)). UIManager (custom script
  windows) has been Studio-only since 19.1.
- Studio-only and AI calls return `False` on the free edition, on hardware below the
  requirement, or when the Extras package is missing (Extras Download Manager): transcription,
  `CreateSubtitlesFromAudio`, `SmartReframe`, `CreateMagicMask`, `AnalyzeForIntellisearch`,
  `AnalyzeForSlate`, `GenerateSpeech`, `RemoveMotionBlur`, Dolby Vision, stereo 3D.
- `resolve.IsStudio()` tells you which edition you're on.

## 13. Stale official examples

The `Examples/` folder shipped with 21.1 still uses pre-21 calls — e.g.
`timeline.ApplyGradeFromDRX(path, mode, clips)` (now `item.GetNodeGraph().ApplyGradeFromDRX(path,
mode)`) and `StartRendering()` without job ids. Trust `DaVinciResolveScript.pyi`
(`bash scripts/resolve-api.sh <Name>`) over the examples and over blog posts.
