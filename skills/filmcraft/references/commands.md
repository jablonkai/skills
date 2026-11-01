# Command ids (pinned to FilmCraft 0.16.0)

The ids below cover the common jobs. For anything else, or when one of these fails with
`unknown command` or `invalid parameters`, look it up. The param string `describe` prints
is the contract, and an unknown key, enum value or label fails the step.

```sh
filmcraft-cli commands transition            # id, label, shortcut, params (filter on id/label)
filmcraft-cli describe sequence.applyVideoTransition   # one command, plus "enabled" right now
filmcraft-cli exec effects.list kind=VideoTransition   # effect ids for transitions/effects
```

`enabled: false` from `describe` without `--project` only means that no sequence is open
in that empty engine.

Notation: `?` optional, `=x` default, `a|b` alternatives, `ticks` = 254016000000 per
second. Ids (`id`, `itemId`, `binId`) are integers from earlier results or from `inspect`.
Project items (media, sequences) have an `item` id. Timeline clips have a `clip` id. A
placed clip with sound is two clips (video + audio, linked).

## Project, media, sequences

| Id | Params / notes |
|---|---|
| `file.newProject` | `{name}` |
| `file.open` | `{path}`: or start the session with `--project` |
| `file.import` | `{paths:[abs path], bin?, imageSequence?, replace?}` → `{items:[itemId], errors:[]}`. Check `errors` |
| `file.newSequence` | `{name, width=1920, height=1080, fps=23.976, sampleRate, video=3, audio=3, mix?: Stereo\|Mono\|5.1\|Adaptive, fromItem?, fromItems?}` → `{sequence: itemId}`. **Becomes the active sequence.** Pass `fps` explicitly. `fromItem: id` matches that clip's size and rate and places it on V1 |
| `sequence.open` | `{item}`: make a sequence active (export and inspect use the active one) |
| `sequence.settings` | `{width?, height?, fps?, name?, …}` |
| `sequence.addTracks` | `{video=1, audio=0, videoAfter?: "first"\|"V2"\|n}` |
| `sequence.inspect` | `{item?}`: a sequence as JSON without making it active |
| `file.newColorMatte` | `{color:"#rrggbb", seconds}` · `file.newBlackVideo {seconds}`: synthetic items |
| `file.saveAs` | `{path}`: `fc_run.py --out` calls it for you |

## Timeline

| Id | Params / notes |
|---|---|
| `timeline.place` | `{item \| items:[…] (back to back), track?: "V1"\|"V2"\|"new"\|"A1" (sound only), audioTrack?, time \| frame \| seconds, insert?, sourceIn?: ticks, duration?: ticks, video=true, audio=true}` → `{clips:[…], placed:[[video, audio], …]}`. `audio:false` for silent B-roll |
| `timeline.razor` | `{time: ticks, track?, clip?}`: an out-of-range or non-numeric time cuts nothing and returns `{cuts: 0}` |
| `timeline.trim` | `{clip, edge:"in"\|"out", mode:"regular"\|"ripple", delta: ticks \| deltaFrames}` |
| `timeline.move` | `{moves:[{clip, track, time}], insert, linked?, copy?}` |
| `timeline.select` | `{clips:[…], add, toggle}`: for commands that act on the selection |
| `edit.clear` / `edit.rippleDelete` | `{clips?:[…]}`: lift / delete-and-close-gap |
| `clip.speedDuration` | `{clips?, speed: percent, reverse, ripple}` |
| `clip.audioGain` | `{clips?, mode?: set\|adjust\|normalizeMax\|normalizeAll, db}` |
| `effects.apply` | `{clips?, effect: id \| display name}` |

## Transitions

| Id | Params / notes |
|---|---|
| `sequence.applyVideoTransition` | `{clip, effect?: "cross_dissolve"\|…, frames?, edge?: "in"\|"out", params?, reverse?}` → `{transition}`. `edge:"in"` on the clip **after** a cut covers that cut, centred on it. |
| `sequence.applyAudioTransition` | the same for the audio clip id (`constant_power`, …) |
| `sequence.setTransition` / `sequence.removeTransition` | `{transition, duration?, params?}` / `{transitions?:[…]}` |

Effect ids: `filmcraft-cli exec effects.list kind=VideoTransition` (for example
`cross_dissolve`, `dip_to_black`, `dip_to_white`, plus wipes and motion transitions). The
display name (`Cross Dissolve`) works too.

## Titles and graphics

| Id | Params / notes |
|---|---|
| `graphics.newText` | `{text, seconds=5, time?: ticks, track?: 0-based index (1 = V2; an occupied track fails, a missing one is ignored), size=100, font?, fontStyle?, position?:[x,y], box?:[w,h]}` → `{clip, layer}`. Point text, left-aligned at the frame centre unless placed |
| `graphics.align` | `{clip, layers:[0], align: left\|hcenter\|right\|top\|vcenter\|bottom, to="frame"}`: one call per axis |
| `graphics.setText` | `{clip, layer?, text}` |
| `graphics.newRectangle` / `newEllipse` | `{position?, size?, seconds, track?, time?}` |

## Markers and in/out

| Id | Params / notes |
|---|---|
| `markers.add` | `{target:"program", time: ticks, name?, comment?, color?: label, durationFrames?}` → `{marker}`. **Without `time` it goes to the playhead** |
| `markers.edit` | `{target, marker, name?, comment?, color?, durationFrames?}` |
| `markers.addChapter` | `{time, name?, …}`: chapter marker |
| `markers.markIn` / `markers.markOut` | `{time \| frame \| seconds \| timecode, target:"program"}`. The out frame is included in an in/out export |
| `markers.clearInOut` / `markers.clearAll` | `{target:"program"}` |
| `markers.exportCsv` | `{path}`: every marker of the active sequence |

Colour labels: Violet, Iris, Caribbean, Lavender, Cerulean, Forest, Rose, Mango, Purple,
Blue, Teal, Magenta, Tan, Green (default), Brown, Yellow.

## Export inside a step list

`file.exportMedia` `{path, preset? | format?, sequence?: itemId, range?:
"entire"|"inOut"|"workArea"|"custom", startSeconds?, endSeconds?, scale=1, width?, height?,
fps?, bitrateKbps?, crf?, proresProfile?, dnxProfile?, audio=true, captionSidecar?,
loudnessLufs?, wait=false}`. Also takes `format` values `hevc|mjpeg|apv|mxf-op1a|mxf-opatom|aiff|aac|flac|tga|dpx|exr`,
`audioCodec`, `bitrateMode`, `hardwareEncoding`, `alpha`, `burnCaptions`, `apvProfile`, `mxfVideoCodec`,
`exrCompression`; `describe file.exportMedia` prints the full list. In `filmcraft-cli run` it waits for the file before the next
line. Through `fc_run.py` (MCP) the file is only written with `"wait": true`, which `fc_run.py` adds. Prefer `fc_export.py`, which checks
the outputs.
