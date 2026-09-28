# DaVinci Resolve — recipes

Job scripts for `bash scripts/resolve-run.sh job.py`. The names they use without defining —
`resolve`, `project`, `mp`, `OUT`, `ARGS`, `need`, `import_media`, `place`, `render`, … — are
injected by the runner (see the table in [SKILL.md](../SKILL.md#injected-namespace)).
Recipes marked *verified* were run against Resolve Studio 21.1.0; the rest follow the 21.1
stub and are unverified — check return values.

## Contents

- [Rough cut from a folder](#rough-cut-from-a-folder) *(verified)*
- [Titles and lower thirds](#titles-and-lower-thirds) *(verified)*
- [Markers from a list or transcript](#markers-from-a-list-or-transcript) *(verified)*
- [Multi-format delivery](#multi-format-delivery) *(verified)*
- [Subtitles](#subtitles)
- [Color: LUT, CDL, DRX, groups, stills](#color-lut-cdl-drx-groups-stills)
- [Audio](#audio)
- [Timeline interchange](#timeline-interchange) *(verified)*
- [Project management](#project-management)
- [Media Pool housekeeping](#media-pool-housekeeping)
- [Inspecting what's there](#inspecting-whats-there) *(verified)*
- [Running inside Resolve (free edition)](#running-inside-resolve-free-edition)

## Rough cut from a folder

*Verified.* Imports every media file in a folder into a bin, lays A-roll on V1/A1 in name
order, puts every third clip as B-roll on V2 (video only), and marks each A-roll cut.

```python
import os
src = ARGS["folder"]
clips = import_media(media_files(src), "Footage/" + os.path.basename(src.rstrip("/")))
tl = new_timeline(ARGS.get("name", "Rough cut"), replace=ARGS.get("replace") == "1")
ensure_tracks("video", 2)
for i, c in enumerate(clips):
    if i % 3 == 2:                                   # B-roll over the previous A-roll clip
        prev = tl.GetItemListInTrack("video", 1)[-1]
        place(c, at=prev.GetStart() + sec(1), track=2, media="video", src_out=sec(3))
    else:
        (item,) = place(c)
        marker((item.GetStart() - tl.GetStartFrame()) / fps(), c.GetName(), "Blue")
dump(timeline_summary(), OUT + "/rough_cut.json")
```

Trim a source range with `src_in`/`src_out` in **source** frames (`src_out` exclusive);
position with `at=` in **absolute** frames (`at(seconds)`, `tc_to_frame("01:00:12:00")`).

## Titles and lower thirds

*Verified.* Never use `Insert*IntoTimeline` on a timeline that already holds an edit — it
ripple-inserts (see [gotchas §6](gotchas.md#6-insert-ripples-the-whole-timeline)).

```python
# A standalone title on its own track, any length, any position
t = title_clip("Day 3 — Night stage", seconds=8, center=(0.5, 0.15), size=0.06)
ensure_tracks("video", 3)
place(t, at=at(12), track=3, media="video", src_out=sec(8))

# Text burned into one clip (moves with it, no extra track)
item = timeline.GetItemListInTrack("video", 1)[0]
tool = overlay_text(item, "Anna K. — race director", size=0.045, center=(0.25, 0.12))
tool.SetInput("Font", "Open Sans"); tool.SetInput("Style", "Bold")
tool.SetInput("Red1", 1.0); tool.SetInput("Green1", 0.8); tool.SetInput("Blue1", 0.1)   # fill colour
```

Title compounds are Media Pool items — reuse one for every placement of the same text. For
other Fusion titles pass `template=` a name from the Effects library (`"Text+"`,
`"Scroll"`…); the Text+ inside must still be the `TextPlus` tool.

## Markers from a list or transcript

*Verified* (markers); transcript part unverified.

```python
import csv
for row in csv.DictReader(open(ARGS["csv"])):          # columns: seconds,name,color,note
    marker(float(row["seconds"]), row["name"], row.get("color") or "Blue", row.get("note", ""))

# Marker list back out, with timecodes
tl = current_timeline()
for off, m in sorted(tl.GetMarkers().items()):
    print(frame_to_tc(tl.GetStartFrame() + off), m["color"], m["name"], m["note"])
```

Use `customData` to tag markers your script owns, then `DeleteMarkerByCustomData` removes
only those. From a Studio transcription (`clip.TranscribeAudio()` first, then
`clip.GetTranscription()`), each segment has `start`/`end` timecodes, `text` and `speaker`
— convert with `tc_to_frame` relative to the clip's own start timecode.

## Multi-format delivery

*Verified* (render helper, presets, custom-resolution timeline, `copy_timeline`).

```python
src = use_timeline(ARGS["timeline"])
jobs = [("16x9", "YouTube - 1080p", None)]
vert = timeline_by_name(src.GetName() + " 9x16") or copy_timeline(src, src.GetName() + " 9x16")
need(vert.SetSettings({"useCustomSettings": "1", "timelineResolutionWidth": "1080",
                       "timelineResolutionHeight": "1920"}), "vertical timeline settings")
jobs.append(("9x16", "TikTok - 1080p", vert))
for tag, preset, tl in jobs:
    info = render(OUT, name=f"{ARGS['name']}_{tag}", preset=preset, tl=tl or src)
    print(tag, info["path"])
```

- Copied timelines share clips but not settings; after changing the resolution, reframe
  with `SetProperties({"ZoomX": …, "Pan": …})` or `SmartReframe()` (Studio).
- A custom codec instead of a preset: `render(OUT, name="master", format="mov",
  codec="ProRes422HQ")`. List options with `project.GetRenderFormats()` and
  `project.GetRenderCodecs("mov")`.
- A range: `settings={"SelectAllFrames": False, "MarkIn": at(10), "MarkOut": at(40)}`.
- Audio only: `settings={"ExportVideo": False, "AudioFormat": ..., "AudioCodec": ...}` — see
  `project.GetAudioRenderFormats()`.
- Queue many and render together: `render(..., wait=False)` per timeline returns the job id —
  but each call also starts rendering; for a real batch use `project.AddRenderJob()` per
  timeline, then one `project.StartRendering(ids)` and `wait_render(id)` for each.
- Burned-in or sidecar subtitles: `settings={"ExportSubtitle": True, "SubtitleFormat":
  "BurnIn" | "SeparateFile" | "EmbeddedCaptions"}`.

## Subtitles

SRT import is *verified*; auto-captioning needs Studio and speech in the audio.

```python
# From an .srt file
(srt,) = import_media([ARGS["srt"]], "Subtitles")
ensure_tracks("subtitle", 1)
place(srt, at=current_timeline().GetStartFrame())          # one timeline item per caption

# Auto-captions (Studio, AI)
tl = current_timeline()
need(tl.CreateSubtitlesFromAudio({"language": resolve.AUTO_CAPTION_ENGLISH,
                                  "charsPerLine": 42, "lineBreak": resolve.AUTO_CAPTION_LINE_SINGLE}),
     "CreateSubtitlesFromAudio")
for it in tl.GetItemListInTrack("subtitle", 1):
    print(frame_to_tc(it.GetStart()), it.GetName())      # GetName() is the caption text
```

To hand the captions over as a file, render with `ExportSubtitle`/`SeparateFile`, or write
the SRT yourself from the subtitle items above. Language constants: `bash
scripts/resolve-api.sh AutoCaptionLanguage`.

## Color: LUT, CDL, DRX, groups, stills

LUT and CDL *verified*.

```python
resolve.OpenPage("color")
for _, item in items("video"):
    g = item.GetNodeGraph()                                     # layer 1
    need(g.SetLUT(1, "Blackmagic Design/Blackmagic 4.6K Film to Rec709.cube"), "SetLUT")
    need(item.SetCDL({"NodeIndex": 1, "Slope": "1.05 1.0 0.95", "Offset": "0 0 0",
                      "Power": "1 1 1", "Saturation": 1.1}), "SetCDL")
```

- LUT paths are relative to the LUT folder (`…/DaVinci Resolve/LUT/`) or absolute; new files
  need `project.RefreshLUTList()` first. `GetLUT` returns the relative path.
- Node indices are 1-based; `SetLUT`/`SetCDL` only address existing nodes — the API cannot
  add nodes. Build the node tree once in the UI, save it as a PowerGrade/DRX, then apply:
  `item.GetNodeGraph().ApplyGradeFromDRX(path, 0)` (0 = no keyframes, 1 = source-TC aligned,
  2 = start-frame aligned).
- Shared grades: `g = project.AddColorGroup("Interviews")`, `item.AssignToColorGroup(g)`,
  then `g.GetPreClipNodeGraph()` / `GetPostClipNodeGraph()`.
- Versions: `item.AddVersion("warm", 0)`, `LoadVersionByName("warm", 0)` (0 local, 1 remote).
- Copy a grade: `src_item.CopyGrades([dst1, dst2])`.
- Stills: `tl.GrabStill()` / `tl.GrabAllStills(2)` on the Color page, then
  `project.GetGallery().GetCurrentStillAlbum().ExportStills(stills, folder, "prefix", "png")`.
- A frame for review: `ExportCurrentFrameAsStill(OUT + "/f.png")` (playhead frame, full
  timeline resolution).

## Audio

```python
tl = current_timeline()
print(tl.GetNormalizeAudioModes())
need(tl.NormalizeAudioLevel([it for _, it in items("audio")],
                            {"normalizationMode": "Sample Peak Program", "targetLevel": -3.0}),
     "NormalizeAudioLevel")
item.SetFades({"FadeIn": sec(0.5), "FadeOut": sec(1)})            # verified; frames
item.SetProperties({"AudioVolume": -6.0, "AudioPan": 0.0})          # dB, -100..100
tl.SetVoiceIsolationState(1, {"isEnabled": True, "amount": 60})     # track 1, Studio
```

`AudioDialogueLeveler*` and `AudioVoiceIsolation*` item properties only work on the current
timeline. Sync double-system sound: `mp.AutoSyncAudio([video, wav], {resolve.AUDIO_SYNC_MODE:
resolve.AUDIO_SYNC_WAVEFORM})`.

## Timeline interchange

*Verified* (EDL, FCPXML 1.10, OTIO, CSV export).

```python
tl = current_timeline()
tl.Export(OUT + "/cut.edl", resolve.EXPORT_EDL, resolve.EXPORT_NONE)
tl.Export(OUT + "/cut.otio", resolve.EXPORT_OTIO, resolve.EXPORT_NONE)
tl.Export(OUT + "/cut.fcpxml", resolve.EXPORT_FCPXML_1_10, resolve.EXPORT_NONE)   # a directory
tl.Export(OUT + "/cut.csv", resolve.EXPORT_TEXT_CSV, resolve.EXPORT_NONE)
tl.Export(OUT + "/cut.drt", resolve.EXPORT_DRT, resolve.EXPORT_NONE)              # Resolve-native

new = mp.ImportTimelineFromFile(ARGS["file"], {"timelineName": "Imported cut",
                                               "importSourceClips": True,
                                               "sourceClipsPath": ARGS["media_root"]})
```

OTIO is the easiest to post-process in Python (it is JSON). For an edit you generate
yourself, writing an OTIO/FCPXML and importing it is an alternative to many
`AppendToTimeline` calls — and it can express things the API cannot (clip speed, positions
on arbitrary tracks in one step).

## Project management

Switching project changes what the user has open — save first and ask.

```python
pm.SaveProject()
p = pm.LoadProject("Client X") or pm.CreateProject("Client X")
need(p.SetSettings({"timelineFrameRate": "25", "timelineResolutionWidth": "1920",
                    "timelineResolutionHeight": "1080"}), "project settings")   # before any timeline
pm.ExportProject("Client X", OUT + "/client_x.drp", True)        # with stills and LUTs
pm.ArchiveProject("Client X", OUT + "/client_x.dra", True, False, False)   # + media, no caches
```

Projects live in the current database folder: `pm.GetProjectListInCurrentFolder()`,
`OpenFolder(name)`, `GotoRootFolder()`. `DeleteProject` only works on a project that is not
loaded — and is irreversible; ask.

## Media Pool housekeeping

```python
for clip in bin("Footage").GetClipList():
    props = clip.GetClipProperty()                  # dict: "File Path", "FPS", "Resolution", "Duration", ...
    clip.SetMetadata({"Scene": "3", "Comments": "b-roll"})
    clip.SetClipColor("Orange"); clip.AddFlag("Green")
mp.MoveClips(clips, bin("Selects"))
mp.RelinkClips(offline_clips, "/Volumes/NewDrive/Footage")
clip.LinkProxyMedia("/path/proxy.mov")
mp.ExportMetadata(OUT + "/metadata.csv", clips)
```

## Inspecting what's there

*Verified.*

```bash
bash scripts/resolve-run.sh --state                    # project, timelines, tracks, render queue
bash scripts/resolve-run.sh -c 'dump(timeline_summary())'
bash scripts/resolve-run.sh -c 'dump([(c.GetName(), c.GetClipProperty()["File Path"]) for c in bin("Footage").GetClipList()])'
bash scripts/resolve-run.sh -c 'print(project.GetRenderPresetList()); print(project.GetRenderCodecs("mp4"))'
```

For a picture of the current frame: `tl.SetCurrentTimecode(...)` then
`project.ExportCurrentFrameAsStill(OUT + "/f.png")` and Read the PNG. For the delivered file,
`ffprobe` it and pull frames with `ffmpeg -ss <t> -i out.mp4 -frames:v 1 f.png`.

## Running inside Resolve (free edition)

The free edition has no external scripting from a terminal, but runs Python from
**Workspace ▸ Scripts**. Copy the job and the helpers into the user Scripts folder, then ask
the user to run it from the menu:

```bash
dst="$HOME/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Utility"
# Windows: %APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Utility
# Linux:   ~/.local/share/DaVinciResolve/Fusion/Scripts/Utility
mkdir -p "$dst" && cp scripts/resolve_helpers.py "$dst/" && cp job.py "$dst/My Job.py"
```

Inside Resolve `resolve` and `fusion` are globals; nothing else is injected, so start the job
with:

```python
import os, sys
# __file__ is not reliably set for menu scripts — name the folder the helpers were copied to
sys.path.insert(0, os.path.expanduser(
    "~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Utility"))
from resolve_helpers import bind, need
H = bind(resolve); project = H.project; mp = H.media_pool
```

and call helpers as `H.place(...)`. Output goes to Workspace ▸ Console. `ARGS`/`OUT` do not
exist there — hard-code paths or read a JSON next to the script.
