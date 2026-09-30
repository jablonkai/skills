# Gotchas (HandBrakeCLI 1.11.2, macOS)

Each item was reproduced on this machine unless it says otherwise.

## Failures that look like success

- **An unknown option exits 0.** `HandBrakeCLI … --bogus` prints
  `unknown option (--bogus)` to stderr, writes **no output**, and returns 0. A typo in
  a raw command therefore "succeeds". Always check that the output file exists and
  run ffprobe on it. `hb-encode.py` marks such a job `failed` with the stderr reason.
- **Argument splitting.** In zsh, `F="--non-anamorphic --keep-display-aspect"; HandBrakeCLI … $F`
  passes **one** argument (zsh does not word-split), which becomes an unknown
  option, so it exits 0 with no output. Use arrays, or `hb-encode.py`.
- **Ctrl-C leaves a broken file.** SIGINT gives exit 1 and leaves a partial MP4
  (e.g. 272 bytes, no duration). Later runs skipping "existing" outputs would then
  keep it. `hb-encode.py` writes to `.NAME.hbpart.EXT` and renames only on success.

## Picture size

- **Capping only the height gives anamorphic video.** With no preset,
  `-Y 1080` on a 3840x2160 source stores **3840x1080 at PAR 1:2**. With
  `-Z "Fast 1080p30" -Y 720` you get 1920x720 at PAR 2:3. Players that ignore PAR
  (many web players, editors, thumbnails) show it squashed. A built-in preset on a
  **portrait** 1080x1920 source gives 1080x1080 at PAR 9:16. The fix is
  `--non-anamorphic --keep-display-aspect` together with `-X`/`-Y`: that gives
  1920x1080, 1280x720 and 608x1080 respectively. `hb-encode.py` adds both unless
  `--keep-anamorphic`. `hb-verify.py --square-pixels` catches the problem.
- `-X`/`-Y` never upscale: a 720p source stays 720p under `-Y 1080`.
- `-l` is height and `-h` is help. `-w/-l` set an exact storage size. Prefer
  `-X/-Y`.
- Auto crop is on by default (`--crop-mode auto`), so letterboxed sources lose their
  black bars and the height is smaller than the cap. Use `-- --crop-mode none` when the
  user wants the full frame, for example to match a delivery spec.

## Tracks

- **Track numbers are 1-based HandBrake indices** from the scan (`hb-scan.py`), per
  type: audio 1..N, subtitles 1..M. They are **not** ffprobe stream indices, where
  video is stream 0.
- **`--subtitle-burned=N` indexes the `-s` list**, not the source. `-s 2 --subtitle-burned`
  burns source track 2, while `-s 1,2 --subtitle-burned=2` also burns source track 2.
  Only one track can be burned.
- `-E`, `-B` and `-6` take **one value per selected audio track**. When fewer are
  given, the last one repeats: `-a 1,2 -E opus` gives two Opus tracks. To mix
  encoders, list them in order: `-a 1,2 -E copy,opus`.
- Without `-a`, the CLI takes the **first** audio track only, and presets usually do
  the same (`AudioTrackSelectionBehavior: first`). "Keep all audio" needs
  `--audio all`.
- Without `-s`, the CLI adds no subtitles. Presets may add "foreign audio" burn-in
  (`SubtitleBurnBehavior: foreign`), which only acts when a foreign-audio search finds
  something.
- Language codes are **ISO 639-2** (`eng`, `hun`, `deu`/`ger`, `fre`/`fra`). An
  untagged track is `und`. `hb-encode.py --audio eng` fails loudly when no track
  matches, instead of silently taking the first.
- Output audio **language tags are kept** from the source. The video stream is
  tagged `und`.
- **Bitmap subtitles** (PGS from Blu-ray, VobSub from DVD) can't be soft subtitles in
  MP4. Use `--format mkv` or `--burn`. Text subtitles (SRT, SSA, tx3g) become
  `mov_text` in MP4.

## Encoders and quality

- Quality scales differ per encoder, so don't carry a number across encoders.
  - x264/x265 RF: **lower is better**. As a rough rule, x265 RF ≈ x264 RF + 2–3 at a
    similar look.
  - SVT-AV1: lower is better too, with good results around 25–35.
  - **VideoToolbox (`vt_h265`, `vt_h264`) runs the other way: higher `-q` is better
    and bigger.** On a 7 s 1080p clip, `vt_h265 -q 30` gave 0.7 MB, `-q 60` 4.7 MB,
    and x265 RF 24 5.9 MB. A user saying "RF 22" with `vt_h265` gets a very
    low-quality file.
- x265 embeds its settings in the stream: `strings out.mp4 | grep -o 'crf=[0-9.]*'`
  proves which RF was used.
- The Homebrew build has `ca_aac` (Core Audio) and no `av_aac`, but `-E av_aac` is
  still accepted and produces AAC.
- x265 on 4K is slow (minutes per minute of video on the default `medium` preset).
  For quick tests add `-- --encoder-preset ultrafast --stop-at seconds:10`.

## Scan output

- With `--json`, the JSON goes to **stdout** as labelled blocks (`Version: {…}`,
  `JSON Title Set: {…}`, many `Progress: {…}`), and the human-readable log goes to
  **stderr**. Parse by label, don't `json.load` the stream. `hb_lib.json_blocks()`
  does this.
- Durations are `{"Hours","Minutes","Seconds","Ticks"}` with ticks at **90 kHz**.
- Subtitle `SourceName` is the character set or format (`UTF-8`, `PGS`, `VOBSUB`).
  `Format` is `text` or `bitmap`.
- For files, `MainFeature` is 0. Only discs set it.

## Presets

- Preset names are **case-sensitive**, and you pass them without the folder
  (`-Z "Fast 1080p30"`, not `General/Fast 1080p30`). An unknown name exits 2.
- `--preset-import-gui` reads nothing useful on macOS, because the GUI is sandboxed.
  Use GUI **Export…** + `--preset-import-file`.
- Command-line flags override the preset for that setting only. A preset's
  `PictureWidth/Height` cap still applies when you pass only `-Y`.
