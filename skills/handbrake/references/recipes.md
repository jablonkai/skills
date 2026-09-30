# Recipes

Paths are relative to the skill directory. `E=scripts/hb-encode.py`,
`V=scripts/hb-verify.py`. Every command below can take `--dry-run` first.

## Folder → H.265 1080p at a quality target

```bash
python3 $E ~/Movies/raw --recursive --out-dir ~/Movies/hevc \
  --encoder x265 --quality 24 --max-res 1080p --summary ~/Movies/hevc/hb-summary.json
python3 $V --summary ~/Movies/hevc/hb-summary.json --codec hevc --max-res 1080p --square-pixels
```

- Non-video files are ignored (the extension list is in `hb_lib.VIDEO_EXTS`, and
  `--ext mp4,mov` narrows it). Hidden files and folders are skipped.
- 4K is scaled to 1920x1080, a portrait phone clip to 1080x1920, and 720p stays
  720p. "1080p" is a resolution class, so a portrait clip keeps a 1080-wide short
  side. If the user wants everything inside one landscape 1920x1080 box, use
  `--max-height 1080 --max-width 1920`, which gives 608x1080 for portrait.
- With no `--audio`, only the **first** audio track is kept (encoded as AAC). Add
  `--audio all` to keep every track, and `--aencoder copy` to pass them through.
- 10-bit output (less banding, needs a newer player): `--encoder x265_10bit`.
- Faster but larger: `--encoder vt_h265 --quality 60` (VideoToolbox, higher = better).
- Apple compatibility: HandBrake tags HEVC in MP4 as `hvc1`, which QuickTime plays.

## Burn in one subtitle and keep two audio tracks

```bash
python3 scripts/hb-scan.py film.mkv          # find the languages and track numbers
python3 $E film.mkv -o film.mp4 --encoder x265 --quality 22 \
  --audio eng,hun --subtitle hun --burn --summary hb-summary.json
python3 $V --summary hb-summary.json --container mp4 --audio-langs eng,hun --subtitle-count 0
```

- `--audio eng,hun` keeps the first English and first Hungarian track, **in that
  order**. `--audio 1,3` selects by number.
- Burn-in can't be undone: the text becomes pixels. When the user may want
  subtitles on and off, keep them soft instead: `--subtitle hun --default-subtitle`
  (MP4 for text subtitles, MKV for PGS/VobSub).
- To check the burn-in visually, grab a frame inside a cue and look at it:
  `ffmpeg -ss 6 -i film.mp4 -frames:v 1 /tmp/f.png`.
- Forced-only subtitles (only foreign-language dialogue):
  `--subtitle eng -- --subtitle-forced`.
- External SRT: `HandBrakeCLI … --srt-file hu.srt --srt-lang hun --srt-codeset UTF-8 --srt-burn`
  (raw CLI. `hb-encode.py` passes these through after `--`).

## Reuse a preset exported from the GUI

```bash
python3 scripts/hb-preset.py "Archive 720p AV1.json"      # exact -Z name + settings
python3 $E clips/ --out-dir out --preset-file "Archive 720p AV1.json" --preset "Archive 720p AV1"
python3 $V --summary … --codec av1 --max-height 720 --container mkv --audio-codec opus
```

The container comes from the preset (`FileFormat`) unless `--format` is given. Any
extra flag, such as `--quality 28`, overrides only that one setting.

## DVD / Blu-ray folder or ISO

```bash
python3 scripts/hb-scan.py /Volumes/Backup/MOVIE/            # titles ≥10 s, main feature marked
python3 $E /Volumes/Backup/MOVIE --main-feature --out-dir out --format mkv \
  --encoder x265 --quality 20 --audio all --subtitle all
python3 $E /Volumes/Backup/SERIES_D1 --title 2,3,4,5 --out-dir out/S01   # episodes
```

- The output is named `<disc>-t02.mkv`. Rename it afterwards if the user wants
  episode names.
- DVDs are interlaced or telecined more often than not. Presets turn on
  `--comb-detect --decomb` automatically. Without a preset, add
  `-- --comb-detect --decomb`.
- Episodic discs often repeat the same title under several numbers: scan, then
  compare durations.
- Encrypted discs: HandBrake can't read them. Say so and stop.

## Size-bounded output (e.g. under 25 MB)

Quality mode doesn't hit a size. Use average bitrate with two passes:

```text
bitrate_kbps = (target_MB × 8192 / duration_s) − audio_kbps      # leave ~3% headroom
```

```bash
python3 $E clip.mov -o small.mp4 --encoder x264 -- -b 2400 --multi-pass -T -B 96
```

Or use a `Web/Social 25 MB …` built-in preset when its duration class fits.

## Quick sample before a long batch

```bash
python3 $E big.mkv -o /tmp/sample.mp4 [same flags] -- --start-at seconds:600 --stop-at seconds:30
```

Look at `/tmp/sample.mp4` (size × duration ratio gives the expected full size)
before committing hours of encoding.

## Queue from the GUI

A queue exported from the GUI (Queue ▸ Export…) runs as-is:
`HandBrakeCLI --queue-import-file queue.json`. It bypasses the safety wrapper, so
check the destination paths in the JSON first (`grep -o '"File": *"[^"]*"' queue.json`).
