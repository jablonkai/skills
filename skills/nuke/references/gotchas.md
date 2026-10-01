# Gotchas (Nuke 17.1v2 Non-commercial, macOS arm64)

All measured on this install. Where Foundry's docs differ, these observations win.

## Licence and modes

- **`--nc` is mandatory.** Without it, Nuke looks for an RLM licence or login token, finds
  none, prints "No license for product", and exits with **100**. `nk.py` adds `--nc` itself.
  Pass `nk.py --licensed …` only on a machine with a commercial licence.
- Headless **works** under NC: `-t script.py` runs Python and `-x` renders. No GUI and no
  Foundry login are needed.
- The `.app` bundles named "Non-Commercial" are launchers (a `droplet` binary). The real
  executable is `Nuke17.1v2.app/Contents/MacOS/Nuke17.1`, which `nk.py find` locates.
  Set `NUKE_BIN` to override.

## Non-commercial limits

| Limit | Symptom | Fix |
|---|---|---|
| Output ≤ 1920×1080 | `nuke.execute` raises "The bounding box exceeds the maximum resolution allowed in Non-commercial mode (1920 x 1080)" | Scale plates (Reformat `type scale`) and Crop to format before the Write. Templates do this via `@@KEY_FIT_W@@`. Note that a bbox larger than the format also trips it, for example a Transform pushing a FG outside the frame, so use Merge `bbox B` and a final Crop. |
| 10 Node objects in Python | `toNode`/`nodes.X()` return `None` | Author as `.nk` text, address by name (see python-api.md) |
| Encrypted saves | Any save is "Nuke NC mode encrypted text" (`.nknc`) | Keep your `.nk` text as the source of truth. Never save over it from Nuke. |
| `-x` and `scriptOpen` refuse `.nk` | "Please specify an existing .nknc script" | Render `.nk` via `nk.py render`, which uses `scriptReadFile` in `-t` |
| h264 and mpeg4 disabled | "h264 codecs are disabled in non-commercial Nuke" | Use ProRes (`mov64_codec appr`/`apch`/`ap4h`), MJPEG, or an image sequence; transcode to H.264 afterwards with ffmpeg/handbrake if needed |

Image formats confirmed writable: EXR, DPX, TIFF, PNG, JPEG. MOV codecs confirmed:
ProRes Proxy/HQ/4444, MJPEG, Animation (rle), v210, PNG. The default MOV codec is
ProRes 422 HQ (`apch`).

## Rendering

- MOV renders also log `Write1: mpeg4 codecs are disabled in non-commercial Nuke`, even
  when no node is called Write1. It is harmless; the ProRes file is written. Judge
  success by `nk.py`'s per-Write result and the frame count, not by grepping the log.
- `-x` stops at the **first** failing Write. Name the Writes (`-X W1,W2`), or use
  `nk.py render`, which runs each Write separately and reports each.
- Nuke's progress dots (`.9`) are printed without a newline, so log lines run together.
  Parse Nuke's output by searching inside lines, not by matching line starts.
- A Write without `create_directories true` fails if the folder is missing. `nk.py`
  creates the folders anyway.
- Exit status: `nk.py render`/`batch` exit 1 if any Write fails **or** any expected frame
  is missing on disk afterwards, so a range typo or a Write pointed at the wrong
  folder is caught even when `nuke.execute` itself returns cleanly.

## Text

- The **`Text`** node's default font is `/Library/Fonts/Arial.ttf`, which recent macOS
  does not have. The text then renders **blank with no error**. Always set
  `font "/System/Library/Fonts/Supplemental/Arial.ttf"` (or Helvetica.ttc, Menlo.ttc).
  `nk.py check` warns about this.
- Also set `xjustify`, `yjustify` and `box`, or the text may land outside the frame.
- `Text2` (the newer node) resolves fonts by family. Its multi-line slates rendered blank
  in testing, so the templates use `Text`.
- TCL in `message`: `\[frame]`, `\[format %04d \[frame]]`, `\[date %Y-%m-%d]` and
  `\[expr a-b+1]` are verified.

## Colour

- Nuke works in scene-linear. Read nodes convert from each file's default colourspace
  (sRGB for PNG/JPEG, linear for EXR), and Writes convert back. A PNG through a
  do-nothing comp comes out matching. An EXR viewed in a non-colour-managed tool looks
  dark; that is expected.
- PNG alpha is *straight*. Add `Premult` after the Read before a Merge over. EXR from a
  renderer is usually already premultiplied, so disable the Premult then
  (`@@FG_PREMULTIPLIED:true@@`).
- A plate with no alpha channel (most EXR/DPX plates) reads with alpha **0**. After a
  Merge over, the output alpha is only the FG matte. Set `auto_alpha true` on BG Reads
  (the `fg_over_bg` template does) so the comp's alpha is solid.
- Grade `white` 0.6 means ×0.6 in linear light, which is about 0.79× in sRGB code values.
  Keep this in mind when checking a grade by pixel values.

## Security posture

- No server, socket or bridge. Every call is one short-lived Nuke process running
  `scripts/nk_driver.py` on a script you chose, so there is no network surface
  (cross-origin, auth and token concerns do not arise).
- `--py HOOK.py` and any `.nk` with `[python …]` TCL execute arbitrary code with your
  user's rights, as opening the script in Nuke would. Render only scripts you trust.
- Stop path: `--timeout` (default 1800 s per script) kills the whole Nuke process group.
  Ctrl-C stops `nk.py` and its Nuke child. `batch` runs one Nuke at a time.
