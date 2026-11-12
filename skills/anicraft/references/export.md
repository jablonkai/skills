# Exports

All are commands (run them as spec steps or with `exec`). `from`/`to` are frames —
1-based in an `ac_build.py` spec, 0-based with `exec`/`run` — and span every scene in
order. `confirm: true` overwrites an existing file. Folders must exist (`ac_build.py`
creates them).

| Command | Output | Check |
|---|---|---|
| `file.export_video {path .mp4/.webm, from, to, scale, audio, ffmpeg}` | H.264+AAC / VP9+Opus via ffmpeg (`ANICRAFT_FFMPEG` or PATH) | `ac_verify.py media F --frames N --size WxH --fps F` |
| `file.export_gif {path, from, to, scale, loop}` | animated GIF | `ac_verify.py media F --frames N` |
| `file.export_png_sequence {dir, from, to, scale}` | `frame_00001.png`… (1-based names) | `ac_verify.py seq DIR --frames N --size WxH` |
| `file.export_sprite_sheet {path .png, from, to, scale, columns, padding, background}` | PNG + `<name>.json` (TexturePacker-style `frames` hash + `meta`) | `ac_verify.py sheet F.json --frames N` |
| `file.export_lottie {path, from, to, background}` | Lottie JSON (`fr`, `ip`, `op`, `w`, `h`, `layers`) | `ac_verify.py lottie F --frames N --fps F` |
| `file.export_html {path, title, sound, fit}` | one self-contained page with a player; runs actions and the AS3 subset | `ac_verify.py html F` |
| `file.export_svg {path, frame}` | one frame as SVG (text becomes paths) | open/render it |
| `file.export_png {path, frame, scale}` | one frame | view it |
| `file.export_audio {path .wav, from, to, rate, bits}` | the mixed soundtrack | ffprobe |

Notes from 0.2.1:
- **Sprite-sheet limit**: 16 777 216 px total. 60 frames of 800×800 fail; `scale: 0.25` fits.
  The map's per-frame `duration` is in ms, rounded.
- **Lottie** reports what it approximated or left out in `notes`/`report` — bitmap fills
  are "not exported yet" in 0.2.1. Read the report and tell the user.
- **HTML** embeds code, paths, images and sounds; `stored_frames`/`timelines` show what it kept.
- Video frame count equals the timeline frame count; duration = frames / fps.
- Text is outlined in SVG/Lottie, so verify text changes in the document
  (`ac_verify.py doc --text`), not in the exports.
- For a quick look without a deliverable, the CLI's `render`, `render-seq` and `gif`
  (1-based) are faster than export steps.
