---
name: ffmpeg
description: 'Cut, convert and process video and audio with the ffmpeg/ffprobe CLI: lossless keyframe-aware trims and joins, H.264/HEVC/AV1/ProRes delivery encodes and proxies (VideoToolbox too), files or folders, two-pass loudnorm to a LUFS target, burned-in or soft subtitles, 9:16 versions with blurred fill, watermarks, crossfades, GIF/WebM loops, contact sheets, frame grabs, speed changes and audio extract/replace, ffprobe-checked. Also for writing or debugging any ffmpeg command or filtergraph (xfade timebase errors, missing filters). Use for "trim this without re-encoding", "join these clips", "normalize to -16 LUFS", "burn the SRT in", "make a vertical version", "turn this into a GIF", "thumbnail grid", "4x timelapse". Not for HandBrake presets or disc rips (handbrake), Apple Compressor settings (compressor), a Resolve/Final Cut/FilmCraft timeline (davinci-resolve, final-cut-pro, filmcraft), gyro stabilization (gyroflow), beat or pitch analysis (aubio), recording or streaming (obs), multitrack mixing (soundcraft).'
summary: "cut, convert and process video and audio with the ffmpeg CLI — lossless keyframe-aware trims and joins, H.264/HEVC/AV1/ProRes encodes and proxies incl. VideoToolbox, two-pass loudnorm, subtitle burn-in and muxing, 9:16 reframes, crossfades, GIF loops and contact sheets, ffprobe-verified outputs"
category: video
compatibility: "Built for FFmpeg 9.0.2 (Homebrew ffmpeg, plus the keg-only ffmpeg-full 9.0.2 for libass/drawtext) on macOS 27, Apple silicon."
risk: low
tags:
    - ffmpeg
    - ffprobe
    - video
    - audio
    - transcode
    - subtitles
metadata:
  version: "1.0.1"
  author: "Tamás Jablonkai"
---

# FFmpeg via ffmpeg / ffprobe

FFmpeg is a headless CLI: every job is a single command, and nothing runs in the
background between them. The hard part is not running it but picking the right
command. Stream copy or re-encode? Which seek, which concat? And there are the
silent traps: exit 0 with an unplayable pixel format, non-square pixels, 192 kHz
audio, a cut that lands on the wrong frame. The scripts make those choices
explicitly and check the result. Verified against **FFmpeg 9.0.2** (Homebrew,
arm64) on macOS 27.

**Two builds.** Homebrew's `ffmpeg` has no libass or freetype, so it lacks the
`subtitles`/`ass`/`drawtext` filters. The keg-only `ffmpeg-full`
(`/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg`) installs beside it and has them. The
scripts pick the build each job needs. Run `bash scripts/ff.sh --check` to see what
is installed. If no build has libass, tell the user `brew install ffmpeg-full`
rather than faking subtitles some other way.

## Scripts

Paths are relative to this skill's directory. All scripts write atomically (a
temp file is renamed only on success), refuse to overwrite their sources, accept
`--dry-run` to print the exact ffmpeg command, and print an ffprobe summary of
what they wrote.

| Script | Use it for |
|---|---|
| [ff.sh](scripts/ff.sh) `--check` | builds, versions, encoders, text filters. Exit 2 if ffmpeg is missing |
| [ff_probe.py](scripts/ff_probe.py) | summary · `--json` · `--keyframes [--near T]` · `--loudness` · `--expect duration=12,vcodec=h264,size=1920x1080,streams=v1a1,arate=48000,loudness=-16,tp_max=-1.5` (exit 1 on mismatch) |
| [ff_cut.py](scripts/ff_cut.py) | trim and/or join: `a.mp4@4-10 b.mp4@2-8 -o out.mp4`. Copies when every cut start is on a keyframe and the clips match; otherwise re-encodes frame-accurately and says why. `--mode copy` snaps to keyframes, `--mode reencode` forces accuracy; `--size 1920x1080 --fps 25` sets the re-encode target (others are pillar/letterboxed) |
| [ff_loudnorm.py](scripts/ff_loudnorm.py) | two-pass loudnorm with the measured values fed back, video copied, source sample rate kept, ebur128 read-back (exit 1 if off-target) |
| [ff_encode.py](scripts/ff_encode.py) | `--profile h264\|hevc\|av1\|vp9\|prores\|proxy\|proxy-h264`, `--hw` (VideoToolbox), `--quality`, `--max-res 720` (short side, portrait-aware). One file (`-o`) or folders (`--out-dir`, `--recursive`). Resumable, `--timeout`, `--summary` JSON |
| [ff_recipe.py](scripts/ff_recipe.py) | `xfade` takes `--size/--fps` for mixed sources and fills silent clips with silence; also `burnsubs` `mux-subs` `vertical` `fit` `watermark` `gif` `sheet` `frames` `speed` `extract-audio` `replace-audio` |

## Workflow

1. **Inspect** the inputs with `ff_probe.py FILE`: codecs, size, fps, rotation, SAR,
   audio rate and channels, duration. For cuts, add `--keyframes --near T`.
2. **Pick the path** with the decision guide below. Use a script when one fits,
   and keep `--dry-run` output when the user wants the command itself.
3. **Run** it. For long encodes, tell the user the scale first (files × duration)
   and offer a short test (`ff_encode.py … -- -t 20`).
4. **Verify** every output with `ff_probe.py OUT --expect …` using the numbers the
   user asked for: duration, codec, size, stream count, loudness. Report what was
   checked. If an image or GIF matters visually, grab a frame and look at it.

## Decision guide

**Copy or re-encode?** Stream copy (`-c copy`) is lossless and instant, but it can
only cut on keyframes and can't change anything the decoder sees. Anything that
touches pixels or samples re-encodes: scale, crop, burn-in, overlay, speed, fades,
loudness. When re-encoding video, copy what isn't touched, e.g. `-c:v copy` for
an audio-only fix.

**Trims.** If the cut points are on keyframes, or the user accepts "roughly here",
copy. If they need an exact frame (dialogue cuts, sync), re-encode, and say that
this is why. `ff_cut.py` decides and reports. Never claim a copy cut is
frame-accurate.

**Joins.** Same codec, size, rate and audio format → the concat demuxer (lossless).
Anything different → the concat filter, normalised to one size and rate. Pass the
user's target (`--size`, `--fps`), or it defaults to the first clip's. Clips from
different cameras and phones almost always differ. Portrait clips in a landscape
reel are pillarboxed, never stretched.

**Encoder.**

| The user says | Use |
|---|---|
| "MP4 that plays everywhere", "for the web" | `--profile h264` (yuv420p, faststart) |
| "smaller", "HEVC/H.265", "for iPhone/Apple TV" | `--profile hevc` (hvc1-tagged) |
| "AV1", "smallest" | `--profile av1` |
| "fast", "use the GPU/hardware", big batch | add `--hw` (VideoToolbox, `--quality` 1–100 and higher is better) |
| "for editing", "master", "ProRes" | `--profile prores [--prores 422\|hq\|4444]` |
| "480p/720p/1080p", "no bigger than" | `--max-res N`: it caps the short side, so a portrait phone clip at 480 becomes 480x854, not 270x480 |
| "proxies" | `--profile proxy` (ProRes Proxy half-res) or `proxy-h264` |
| "WebM" | `--profile vp9`, or `ff_recipe.py gif … -o x.webm` for a loop |

Quality defaults: x264 CRF 20, x265 CRF 24, SVT-AV1 CRF 32, VideoToolbox q 60–65.
Lower CRF means better quality. The full matrix and platform targets are in
[encoding.md](references/encoding.md).

**Audio loudness.** Always run two passes with `ff_loudnorm.py`. Targets: −16 LUFS
podcasts and streaming, −14 Spotify, −23 EBU broadcast. The report says
whether the gain was linear or loudnorm had to limit dynamically. Pass that on.

**Subtitles.** "Burn in", "hardcode", "for Instagram" → `burnsubs` (ffmpeg-full).
"Add a subtitle track", "selectable" → `mux-subs` (mov_text in MP4, as-is in MKV).
SRT not in UTF-8 → `--charenc CP1250`.

**Reframing.** Into a different aspect ratio: `vertical` (blurred fill, default
1080x1920; `--fill black|crop`) or `fit --size WxH` (pad). Burn subtitles before
reframing unless they should be sized for the new frame.

## Raw ffmpeg

When no script fits, write the command yourself, but read
[gotchas.md](references/gotchas.md) first. It is short, and every item is a bug
that exits 0. Always: `-hide_banner -nostdin`, explicit `-map`, `-pix_fmt yuv420p`
for delivery, `setsar=1` after scaling, `-tag:v hvc1` for HEVC, `-ar 48000` after
loudnorm, `+faststart` for MP4. Pass the filtergraph as a single quoted argument
or `-/filter_complex file.txt`. `-filter_complex_script` was removed in 9.0. This
machine's shell is zsh, so `$CMD args` doesn't word-split. Run multi-step ffmpeg
work from a bash script or use arrays.

## References

- [gotchas.md](references/gotchas.md): seeking and copy-cut accuracy, concat
  rules, pixel formats, SAR, VideoToolbox, loudnorm, escaping, shell traps.
- [filters.md](references/filters.md): filtergraph syntax, plus the recipes behind
  `ff_recipe.py` (fit/pad, blurred 9:16, watermark, the xfade offset formula,
  palette GIF, contact sheet, speed, drawtext).
- [encoding.md](references/encoding.md): encoder and quality matrix, platform
  targets, audio codecs, VMAF checks.
- [audio.md](references/audio.md): loudness targets, extract/replace/mix, ducking,
  sync fixes, cleanup filters.
- [subtitles.md](references/subtitles.md): burn-in styling, charsets, fonts, soft
  tracks per container.
- [cli-reference.md](references/cli-reference.md): stream specifiers, seek
  options, concat, `-progress`, metadata, ffprobe one-liners.

## Safety

Everything runs locally: nothing is uploaded and nothing listens on a port.
Sources are only read. Outputs that already exist are replaced only by the script
that owns them (`ff_encode.py` skips complete ones unless `--force`). Commands are
built as argument lists, so names with spaces, quotes or accents are safe. Before
deleting or overwriting any user file outside these scripts, ask.
