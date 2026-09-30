---
name: handbrake
description: 'Transcode and compress video with HandBrakeCLI (free, open-source HandBrake): scan files, DVD/Blu-ray folders or ISOs for titles, audio and subtitle tracks; encode one file or whole folders with built-in presets or presets exported from the HandBrake GUI; H.265/H.264/AV1 with a quality (RF) target and max resolution; keep chosen audio tracks by number or language, burn in or keep subtitles; resumable, stoppable batches checked with ffprobe. Use for "convert this folder to H.265 1080p", "shrink these videos with HandBrake", "rip the main feature from this VIDEO_TS", "burn in the Hungarian subtitles and keep English and Hungarian audio", "use my HandBrake preset on all of these", or Hungarian "tömörítsd HandBrake-kel ezeket a videókat". Not for Apple Compressor or ProRes/Apple pipeline deliverables (use compressor), rendering an editor timeline (use davinci-resolve or final-cut-pro), plain ffmpeg trims, cuts, concatenation or frame grabs, screen recording (use obs), or copy-protected discs.'
summary: "transcode and compress video with HandBrakeCLI — file and folder batches, DVD/Blu-ray title selection, built-in and GUI-exported presets, H.265/AV1 quality targets, audio and subtitle track picking with burn-in, ffprobe-verified outputs"
category: video
risk: low
tags:
    - handbrake
    - transcode
    - video
    - hevc
    - subtitles
---

# HandBrake via HandBrakeCLI

HandBrake is driven through **`HandBrakeCLI`**, the command-line encoder built from the
same libhb as the GUI. The GUI has no scripting interface, and **HandBrake.app does
not contain the CLI**. Install it separately (`brew install handbrake`, or
`HandBrakeCLI-<version>.dmg` from handbrake.fr/downloads2.php). Verified against
**HandBrake 1.11.2** (Homebrew build, arm64) on macOS 27.

The scripts wrap the CLI's sharp edges: they scan before encoding, resolve tracks,
force square pixels, write outputs atomically, and parse the JSON progress.

- [scripts/hb.sh](scripts/hb.sh): `--check` prints the CLI path, version, video
  encoders and ffprobe status, and exits 2 with install hints if the CLI is missing.
  Any other arguments pass through to HandBrakeCLI.
- [scripts/hb-scan.py](scripts/hb-scan.py): lists titles (duration, size, fps),
  audio and subtitle tracks, each with the **1-based number** that `-a`/`-s` take and
  its language code. Works on files, folders (`--recursive`), VIDEO_TS/BDMV folders
  and ISOs. `--json` for machine use.
- [scripts/hb-encode.py](scripts/hb-encode.py): encodes one file or a batch, with
  presets, encoder, quality, max size, and audio and subtitle selection by number or
  language. It is resumable (skips existing outputs), stoppable (Ctrl-C/SIGTERM/
  `--timeout`), `--dry-run` prints the exact commands, and it writes a JSON summary.
- [scripts/hb-verify.py](scripts/hb-verify.py): runs ffprobe on the outputs against
  expectations: codec, max height, square pixels, container, audio count, languages
  and codec, subtitle count, and duration against the source.
- [scripts/hb-preset.py](scripts/hb-preset.py): lists presets in GUI/CLI JSON exports
  with their key settings, lists built-ins (`--builtin GREP`), and prints the
  effective settings of one preset (`--resolve NAME`).
- [references/cli-reference.md](references/cli-reference.md): the raw flags, grouped
  by task, checked against `--help` on 1.11.2.
- [references/presets.md](references/presets.md): built-in presets, the GUI export
  steps, the JSON layout, and overriding preset settings.
- [references/recipes.md](references/recipes.md): worked examples for batches, discs,
  track selection, burn-in, device targets and size budgets.
- [references/gotchas.md](references/gotchas.md): **read before writing raw
  HandBrakeCLI commands.** Silent exit 0 on bad options, anamorphic surprises,
  1-based indices, and more.

## Workflow

```bash
H=scripts   # paths are relative to this skill's directory
bash $H/hb.sh --check                                   # 1. CLI present? (exit 2 → install it)
python3 $H/hb-scan.py film.mkv                          # 2. what tracks and titles exist
python3 $H/hb-encode.py SRC... --out-dir OUT [settings] --dry-run   # 3. check the plan
python3 $H/hb-encode.py SRC... --out-dir OUT [settings] --summary OUT/hb-summary.json
python3 $H/hb-verify.py --summary OUT/hb-summary.json [expectations]   # 4. prove it (e.g. --codec hevc --max-res 1080p --square-pixels)
```

1. **Scan first** whenever tracks, languages or disc titles matter. Never guess
   track numbers: they are 1-based and follow the source order, which is not
   the order ffprobe shows streams in.
2. **Translate the request into settings** (table below). A dry run shows the exact
   `HandBrakeCLI` command. Keep it for the user, because it is the reproducible
   answer.
3. **Encode with `hb-encode.py`**, not raw HandBrakeCLI. HandBrakeCLI exits **0**
   on an unknown option and writes nothing. It stores anamorphic video when you only
   cap the height. After Ctrl-C it leaves a broken half-file. The script catches all
   three.
4. **Verify with `hb-verify.py`** using the expectations the user stated (codec,
   height, languages, subtitle count). Report the summary: done/skipped/failed per
   file, sizes, and anything that didn't match.

## Request → settings

| The user says | hb-encode.py flags |
|---|---|
| "H.265 / HEVC" | `--encoder x265` (10-bit: `x265_10bit`; fast hardware: `vt_h265`, larger files at the same visual quality) |
| "AV1" | `--encoder svt_av1` (`svt_av1_10bit`) |
| "H.264, plays everywhere" | `--encoder x264`, or a preset like `"Fast 1080p30"` |
| "quality 22" / "RF 22" / "good quality" | `--quality 22`. x265: 20–24 for HD at good quality, 26–28 for small files. x264: 18–22. SVT-AV1: 25–35. **VideoToolbox (`vt_*`) is reversed: higher = better**, around 50–65 |
| "1080p" / "max 720p" | `--max-res 1080p`. It scales down only, keeps the aspect ratio, and never upscales. Each file uses its own orientation: 4K → 1920x1080, and a portrait phone clip → 1080x1920 (rotation metadata is applied). For a fixed box, use `--max-height 1080`, which gives 608x1080 for that clip |
| "keep English and Hungarian audio" | `--audio eng,hun` (first track of each, in that order). Every English track: `eng*`. By number: `--audio 1,3` |
| "pass the audio through untouched" | `--aencoder copy` (each track is copied when the container accepts its codec, including FLAC in MP4 on 1.11. Otherwise it is re-encoded with the fallback, AAC) |
| "burn in the Hungarian subtitles" | `--subtitle hun --burn` |
| "keep subtitles as selectable tracks" | `--subtitle eng,hun` (text subtitles → MP4 tx3g or MKV. Bitmap PGS/VobSub subtitles need MKV or `--burn`) |
| "use my preset" | `--preset-file export.json --preset "Name"` (see [presets.md](references/presets.md)) |
| "the main movie from this DVD" | `--main-feature`. Specific titles: `--title 2,5` (disc sources only) |
| "MKV" / "MP4" | `--format mkv` (default: the `-o` extension, then the preset's container, then mp4) |

Flags you pass override the preset's value for that setting only. Anything else
HandBrakeCLI supports goes after `--`, for example
`-- --encoder-preset slow --optimize`.

Without `--preset`, the CLI's own defaults apply. The main ones are an AAC audio
track from the first source track, no subtitles, and the source frame rate. For
consumer targets ("for my iPhone", "for Plex", "for YouTube"), start from a built-in
preset instead: `python3 scripts/hb-preset.py --builtin iphone` (see
[presets.md](references/presets.md)).

## Output layout

- **`--out-dir DIR`**: each source becomes `DIR/<name>.<ext>`. Subfolders are
  mirrored with `--recursive`. Disc titles become `DIR/<disc>-t02.<ext>`. **`-o
  FILE`** takes a single source.
- Outputs are written as `.NAME.hbpart.EXT` and renamed only when the encode
  succeeds. An existing output is **skipped** when ffprobe shows it complete (full
  duration), so re-running the same command resumes a batch. A truncated or
  unreadable file, such as one left by a killed raw HandBrakeCLI run, is re-encoded.
  Use `--force` to re-encode everything.
- The script refuses to write over a source, and refuses two sources mapping to one
  output (e.g. `a.mov` and `a.mp4`).

## Long encodes

x265 and SVT-AV1 at slow presets can run for hours. For big batches:

- Run `hb-encode.py` in the background and read its stderr for per-file progress
  (every 10%).
- Or bound it with `--timeout SEC`. It stops cleanly with exit 124, and running the
  command again continues from the next file.
- Ctrl-C/SIGTERM stops the running encode, deletes its partial file, marks the
  remaining jobs `pending`, and exits 130.
- Before starting a multi-hour job, tell the user the estimated scale (files ×
  duration). Offer a fast test first:
  `python3 scripts/hb-encode.py one.mkv -o /tmp/test.mp4 [same flags] -- --stop-at seconds:30`.

## Discs

HandBrake reads **unencrypted** DVD/Blu-ray folders (`VIDEO_TS`, `BDMV`) and ISOs.
It does not decrypt copy-protected discs, and this skill does not help work around
that. Scan to see the titles (menus and trailers are filtered by `--min-duration`,
default 10 s), then choose with `--main-feature` or `--title N[,N]`. Disc title
selection was checked against the documented CLI behaviour only, not against a real
disc image on this machine.

## Safety

- Everything is local. The scripts read sources and write new files. Nothing
  listens on a port, and nothing is uploaded.
- Commands are built as argument lists, never through a shell, so file names with
  spaces, quotes or accents are safe.
- Sources are never modified or overwritten. Existing outputs are only replaced
  with `--force`.
- Presets are imported only from JSON files the user supplies.
  `--preset-import-gui` is not used: the sandboxed GUI keeps its presets in a
  container the CLI cannot read, so export them from the GUI instead.
