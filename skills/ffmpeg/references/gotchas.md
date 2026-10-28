# ffmpeg gotchas

Read before writing raw ffmpeg commands. Each item is a mistake that produces a
file that *looks* fine (exit 0, plays) but is wrong. All checked on FFmpeg 9.0.2.

## Cutting and seeking

- **Stream copy cuts start on a keyframe.** `-ss 4.3 -i in.mp4 -c copy` starts at
  the keyframe at or before 4.3 s. MP4/MOV writes an edit list that hides the
  extra frames in some players but not in others (and not in editors). Real
  frame accuracy needs a re-encode. Check the keyframes first:
  `ff_probe.py in.mp4 --keyframes --near 4.3`. Phone and camera files often use
  1–2 s GOPs; screen recordings and streams can use 10 s or more.
- **Copy cut ends overshoot by a few frames.** B-frame reordering means
  `-to 10 -c copy` keeps 2–3 packets that decode before the end point but display
  after it (6.08 s for a 6 s request here), and the audio runs on too. Cap the video
  with the output option `-frames:v N` (N = duration × fps) plus `-t D`. `ff_cut.py`
  does both.
- **Input seek vs output seek.** `-ss` *before* `-i` seeks the input. It is fast,
  and frame-accurate when re-encoding, because ffmpeg decodes from the previous
  keyframe and discards frames up to the target. `-ss` *after* `-i` decodes and
  throws away everything up to that point, so it is slow on long files and gives
  no extra accuracy. Use input seek unless you need filters to see the earlier
  frames.
- **`-to` with input seek.** As an input option, `-to` is a position in the input
  (`-ss 4 -to 10` = 6 s). As an output option after an input `-ss`, timestamps
  were reset, so `-to 10` means 10 s of output. Prefer `-t DURATION` when in
  doubt.
- **`-avoid_negative_ts make_zero`** on copy cuts keeps timestamps starting at 0,
  so segments concatenate without gaps.

## Concatenation

- **The concat demuxer (`-f concat`) is lossless but strict.** Every file needs the
  same codecs, resolution, pixel format, frame rate, time base, audio sample rate
  and channel count. If they differ, the output plays with frozen video, A/V drift
  or broken timestamps, often with exit 0. `ff_cut.py` compares the parameters
  first. Different sources need the **concat filter** (re-encode, normalised to
  one size and rate).
- List files need `-safe 0` for absolute paths, and single quotes in names are
  written as `'\''`.
- **Joins of copy-cut parts open small gaps.** The demuxer starts each next file
  at the previous one's *longest* stream end. Audio overshoot and the B-frame start
  delay (first video pts ≈ 0.08–0.1 s) leave a ~0.1 s hole in the video at every
  join, and the average fps drops below nominal. Write a `duration` line after
  each `file` line: this part's video end minus the next part's first video pts.
  `ff_cut.py` probes the parts and does that.
- The demuxer re-inserts SPS/PPS into keyframes (packets grow by a few bytes). The
  stream is still a copy.

## Encoding

- **`-pix_fmt yuv420p` for anything people will play.** libx264/libx265 keep the
  input's chroma: 4:2:2 or 4:4:4 sources (ProRes, screen captures, PNG sequences)
  become High 4:4:4 H.264 that QuickTime, browsers and phones won't play.
- **libx264 refuses odd dimensions.** Use `scale=-2:720` (even rounding), not
  `-1`.
- **"480p" means the short side.** `scale=-2:480` on a 1080x1920 phone clip gives
  270x480. Scale portrait sources by width (`scale=480:-2`), or use
  `ff_encode.py --max-res 480`.
- **Reset the SAR after scaling.** `scale=-2:480` on a 1280x720 source gives
  854x480 with SAR 1280:1281, a non-square pixel aspect that players stretch.
  Append `setsar=1`.
- **HEVC for Apple players needs `-tag:v hvc1`.** The default `hev1` tag plays in
  VLC but not in QuickTime, Safari, Photos or iOS.
- **VideoToolbox quality is `-q:v 1–100`, and higher is better.** It doesn't
  accept `-crf`. Without `-q:v` or `-b:v` it picks a low bitrate. The hardware
  encoders are 5–10x faster, but files are larger at the same visual quality.
  `prores_videotoolbox` is real-time ProRes on Apple silicon.
- **`-movflags +faststart`** moves the index to the front so web players can
  start before the download ends. Use it for every MP4 delivery.
- **`-map 0` also maps data and attachment streams.** For example, the timecode
  track `tmcd` in camera MOVs makes MP4 muxing fail or carries junk. Use
  `-map 0 -map -0:d` or explicit `-map 0:v -map 0:a`.
- Without `-map`, ffmpeg picks **one** video and **one** audio stream (the "best"
  ones). Extra audio languages and subtitles are silently dropped.

## Audio

- **loudnorm outputs 192 kHz.** Always set `-ar 48000` (or the source rate) after
  it.
- **Single-pass loudnorm is dynamic** and pumps. Two-pass with `linear=true` gives
  a clean gain change, but only when the target fits under the true-peak ceiling.
  Otherwise loudnorm falls back to dynamic mode on its own. A very quiet source
  (−40 LUFS → −16) always ends up dynamic.
- **True peak can overshoot after lossy encoding.** The limiter works at 192 kHz.
  After resampling and AAC encoding, measure again with
  `ebur128=peak=true` (`ff_loudnorm.py` re-runs pass 2 with a lower ceiling when
  that happens).
- `atempo` quality drops outside 0.5–2.0. Chain it (`atempo=2,atempo=2` for 4x).
- `-shortest` combined with filtergraphs can overshoot by a frame or a packet.
  Trim with `-t` when the length must be exact.

## Subtitles and text

- **Homebrew's `ffmpeg` has no libass or freetype**, so `subtitles`, `ass` and
  `drawtext` are not there ("No such filter"). Use the keg-only
  `/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg` (`brew install ffmpeg-full`).
  `ff.sh --check` shows which build has them.
- **Filter-argument escaping.** A path inside `subtitles=` needs `:` `,` `'` `\`
  `[` `]` escaped at two levels. The easy way out is to copy the subtitle file to a
  plain temp name (what `ff_recipe.py burnsubs` does).
- SRT that isn't UTF-8 (e.g. CP1250 Hungarian subtitles) shows mojibake. Add
  `:charenc=CP1250`.
- **MP4 accepts only `mov_text` text subtitles.** `-c copy` of an SRT into MP4
  fails. Use `-c:s mov_text`. MKV takes SRT/ASS as they are.

## Images and GIF

- A single image output needs `-frames:v 1` (plus `-update 1` for a fixed name),
  or ffmpeg complains about the pattern and may write many files.
- **GIF without palettegen uses a generic 256-colour palette** that bands and
  dithers badly. Use `palettegen` → `paletteuse` in one graph (`split`).
  `-loop 0` = loop forever, and `-loop -1` = play once.

## Shell and batch

- **ffmpeg reads stdin.** In `while read f; do ffmpeg …; done < list` it eats the
  list. Pass `-nostdin`.
- In zsh (the macOS default) `F="ffmpeg -y"; $F …` doesn't word-split. Use arrays,
  a function, or `bash script.sh`.
- `-y` overwrites without asking, while `-n` never overwrites. Without either,
  ffmpeg blocks waiting for a y/N answer.
- Phone footage is often **variable frame rate**. Editors and `xfade` want a
  constant rate: add `fps=30` or `-fps_mode cfr -r 30`.
- Rotation: phone MOVs carry a display matrix. A re-encode applies it (autorotate),
  and a stream copy keeps the matrix. `ff_probe.py` shows `rotation=`.
