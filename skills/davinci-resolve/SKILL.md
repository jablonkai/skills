---
name: davinci-resolve
description: 'Remote-control a running DaVinci Resolve (Studio) with Python through its built-in scripting API — import media into bins, assemble timelines from clips, place B-roll on upper tracks, add markers, titles and lower thirds, import SRT or auto-generate subtitles, apply LUTs/CDL/DRX grades, normalize audio, queue and render deliverables (YouTube, TikTok/vertical, ProRes masters), and export EDL/FCPXML/OTIO/AAF. Use whenever the user wants something done in DaVinci Resolve or with a Resolve project, timeline, bin or render queue — e.g. "cut these clips together in Resolve", "build a rough cut from this folder", "render this timeline for YouTube and TikTok", "add markers from this list", "put a lower third on", "export an EDL", "batch render all timelines", "vágd össze Resolve-ban", "renderelj ki a DaVinciből" — even if they just say "Resolve" or "DaVinci". Not for ffmpeg-only edits with no Resolve involved, and not for Fusion Studio standalone.'
summary: "remote-control a running DaVinci Resolve by Python via its scripting API — media import and bins, timeline assembly, markers, titles and lower thirds, subtitles, LUT/CDL grades, render queue deliverables, EDL/FCPXML/OTIO export"
category: video
risk: medium
tags:
    - davinci-resolve
    - video-editing
    - rendering
    - color-grading
    - scripting
---

# DaVinci Resolve Control

DaVinci Resolve has its own scripting server, so there is nothing to install inside the app:
a job script runs in a local Python process and talks to the **running** Resolve through
`fusionscript`. [scripts/resolve-run.sh](scripts/resolve-run.sh) finds the interpreter
(Resolve 21.1+ ships `ResolvePython`, which needs no environment setup; otherwise `python3` with
the SDK variables), connects, injects the live objects and helpers, and runs your script.
Everything here was executed and verified on **DaVinci Resolve Studio 21.1.0** (macOS). Check
`version` in the ping reply — on another release, the installed stub
(`bash scripts/resolve-api.sh <Name>`) is the source of truth.

- [scripts/resolve-run.sh](scripts/resolve-run.sh) — run a `.py` (or `-c 'inline'`);
  `--ping` checks the connection, `--state` dumps project, timelines, tracks and render queue.
- [scripts/resolve_helpers.py](scripts/resolve_helpers.py) — the helpers injected below.
- [scripts/resolve-api.sh](scripts/resolve-api.sh) — grep the installed API stub for a method
  or parameter dict (`resolve-api.sh RenderSettings`).
- [assets/text-overlay.comp](assets/text-overlay.comp) — Fusion template used by `overlay_text`.

**Read [references/gotchas.md](references/gotchas.md) before writing anything.** The API fails
silently, uses absolute frames in some calls and offsets in others, and several remembered
patterns — `ImportMedia([{"FilePath": …}])`, `AddFusionComp()`, `InsertTitleIntoTimeline` on a
cut — quietly do the wrong thing on 21.1.

## The control loop

1. **Ping**: `bash scripts/resolve-run.sh --ping` →
   `{"ok": true, "product": "DaVinci Resolve Studio", "version": "21.1.0.17", "studio": true, …}`.
   If it fails, the user has to fix it — you can't from here:
   - Resolve not running, or no project open → ask them to open one.
   - "refused the connection" → Studio: Preferences ▸ System ▸ General ▸ *External scripting
     using* = **Local**, then restart Resolve. Free edition: no terminal access — use the
     Scripts-menu route in [recipes.md](references/recipes.md#running-inside-resolve-free-edition).
   - Hangs, then "no answer" → Resolve is starting/quitting, or a **menu or dialog is open**
     in its UI (that stalls every call). Ask the user to close it.
   - `"page": null` in the ping → a message box (e.g. Fusion's "Render completed!") is open;
     most calls return `None` until the user clicks OK.
2. **Look before you build**: `bash scripts/resolve-run.sh --state` — product, page, project,
   timelines, the current timeline's fps/resolution/start frame/tracks, render presets, queue.
3. **Write a job script** into the scratchpad, from the cheatsheet and
   [recipes.md](references/recipes.md).
4. **Run it**: `OUT=/abs/outdir bash scripts/resolve-run.sh /abs/job.py --arg folder=/path`.
   Output streams back; an exception prints its traceback and exits non-zero. Set
   `RESOLVE_JOB_TIMEOUT=<seconds>` (generous if it renders) — Resolve occasionally freezes, and
   without it a stuck job waits forever. Parameters go
   through `--arg KEY=VALUE` (read `ARGS["KEY"]`, strings); `OUT` is where exports and renders go
   — always set it, it defaults to the current directory.
5. **Verify** (below), then **iterate**. Make jobs re-runnable: build into your own named
   timeline with `new_timeline(name, replace=True)`, reuse clips via `import_media` (it dedupes).

Run one job at a time — Resolve's current project/timeline/folder is shared state.

## Reference routing

| Task | Read |
|---|---|
| Anything, before you start | [gotchas.md](references/gotchas.md) |
| A worked pattern: rough cut, titles, markers, delivery, subtitles, color, audio, interchange, projects | [recipes.md](references/recipes.md) |
| Exact signature, parameter dict keys, constants | [api-reference.md](references/api-reference.md) — or `bash scripts/resolve-api.sh <Name>` |
| Full project/timeline settings keys | `bash scripts/resolve-api.sh ProjectSettings` / `TimelineSettings` |

## Injected namespace

`resolve`, `fusion`, `pm` (ProjectManager), `project`, `mp` (MediaPool), `timeline` (current,
may be `None`), `OUT`, `ARGS`, `need`, `ResolveError`, `H` (the helper object), and these
helpers as bare functions:

| Helper | Does |
|---|---|
| `need(value, "what")` | raise if the API returned `False`/`None` — wrap every mutating call |
| `timelines()` / `timeline_by_name(n)` / `use_timeline(tl_or_name)` | list, find, make current |
| `new_timeline(name, replace=False)` | empty timeline, made current; refuses to clobber unless `replace=True` |
| `copy_timeline(src, name)` | duplicate a timeline via DRT round-trip, made current |
| `fps()` / `sec(s)` / `at(s)` | timeline rate; seconds → frame count; seconds → **absolute** record frame |
| `tc_to_frame(tc)` / `frame_to_tc(f)` | absolute frames ↔ timecode, drop-frame aware |
| `bin("A/B")` | get-or-create a Media Pool folder by path |
| `media_files(dir)` / `import_media(paths, bin)` | list media (skips `._*`); import deduped on real file path |
| `ensure_tracks(kind, n)` | add video/audio/subtitle tracks up to `n` |
| `place(clip, at=, track=, src_in=, src_out=, media=)` | append a clip; `src_out` exclusive; `media='video'` for B-roll |
| `marker(seconds, name, color=, note=)` | timeline marker (handles the offset convention) |
| `title_clip(text, seconds=, center=, size=)` | Text+ title as a compound Media Pool item — no ripple |
| `overlay_text(item, text, size=, center=)` | Text+ burned into one clip via its Fusion comp |
| `items(kind)` | `(track, item)` pairs across all tracks, in time order |
| `render(dir, name=, preset=, format=, codec=, settings=, tl=)` | queue, render, wait; returns job info with `path` |
| `timeline_summary()` / `state()` / `dump(obj, path)` | inspection as JSON |
| `save()` | `SaveProject` |

## Cheatsheet

### Assemble

```python
clips = import_media(media_files(ARGS["folder"]), "Footage/Day 1")
tl = new_timeline("Day 1 - rough", replace=True)
for c in clips:
    place(c)                                            # V1 + A1, back to back
ensure_tracks("video", 2)
place(clips[3], at=at(12.0), track=2, media="video", src_in=sec(2), src_out=sec(6))   # B-roll
marker(12.0, "B-roll: aerial", "Cyan")
```

### Titles and text

```python
t = title_clip("EMU 6 Day Race", seconds=6, center=(0.5, 0.15))
ensure_tracks("video", 3)
place(t, at=at(1), track=3, media="video", src_out=sec(6))
overlay_text(timeline.GetItemListInTrack("video", 1)[0], "Budapest, 2026", size=0.04)
```

### Clip look and sound

```python
(item,) = place(clips[0])
need(item.SetProperties({"ZoomX": 1.1, "ZoomY": 1.1, "Opacity": 100.0}), "SetProperties")
need(item.SetFades({"FadeIn": sec(0.5), "FadeOut": sec(1)}), "SetFades")
item.GetNodeGraph().SetLUT(1, "Blackmagic Design/Blackmagic 4.6K Film to Rec709.cube")
```

### Deliver

```python
info = render(OUT, name="day1_youtube", preset="YouTube - 1080p")
print(info["path"])
info = render(OUT, name="day1_master", format="mov", codec="ProRes422HQ")
timeline.Export(OUT + "/day1.otio", resolve.EXPORT_OTIO, resolve.EXPORT_NONE)
```

## Verification

- **Returned output** first — print what you built (`dump(timeline_summary())` gives every
  track with clip names and absolute start/end frames).
- **A frame**: `timeline.SetCurrentTimecode(frame_to_tc(at(3)))`, then
  `project.ExportCurrentFrameAsStill(OUT + "/check.png")` and Read the PNG — seconds, not a
  render.
- **The deliverable**: `render()` raises unless the job ends `Complete`; confirm the file with
  `ffprobe`, and pull a frame or two with `ffmpeg -ss <t> -i <file> -frames:v 1 f.png` to Read.
- A call that returned `True` is not proof: `AddMarker` accepts frames past the end, an
  out-of-range `trackIndex` lands elsewhere. Read the state back.

## Safety

- The open project is the user's work. Build into **new** timelines and bins, and leave
  existing ones alone unless asked. Ask before `DeleteTimelines`, `DeleteClips`,
  `DeleteFolders`, `DeleteProject`, `DeleteAllRenderJobs`, `ResetAllGrades`, `Quit`, or
  switching projects (`LoadProject`/`CreateProject` — `SaveProject()` first).
- `Timeline.Insert*IntoTimeline` ripples every unlocked track — use `title_clip()` instead on
  any timeline that already has an edit.
- Scripts move the user's playhead, page, current timeline and current bin. Put them back when
  the user is working in the same session.
- Renders occupy Resolve until done; warn before long ones and pass `timeout=` to `render()`.
  Render into `OUT`, never over source media.

## Security

- *External scripting using: Local* lets **any local process** drive Resolve with the user's
  privileges — no authentication. *Network* extends that to the LAN (port 1144); recommend
  Local, and None when not scripting.
- Job scripts are ordinary Python running as the user: they can touch any file, not just
  Resolve. Keep them in the scratchpad and show the user anything that deletes or overwrites.
