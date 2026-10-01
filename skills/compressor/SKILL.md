---
name: compressor
description: 'Batch-transcode video with Apple Compressor from the command line: encode files or whole folders with built-in or custom Compressor settings (ProRes 422/LT/HQ/4444/Proxy, H.264, HEVC, Apple Devices, Website Sharing, proxy sizes, MXF, TIFF/EXR image sequences), several deliverables per source in one batch, outputs next to the originals or in a folder; look up settings by name; derive and save a custom setting with a new frame size; monitor, stop and resume batches; verify outputs with ffprobe (codec, frame size, duration). Use for "make ProRes Proxy files of this card with Compressor", "H.264 and HEVC deliverables from this master", "use my Compressor setting on these", "create a 720p HEVC Compressor preset", "which Compressor settings make HEVC?", or Hungarian "kódold át Compressorral". Not for HandBrake or open-source encodes (use handbrake), plain ffmpeg conversions, FCPXML timelines (use final-cut-pro), or rendering inside DaVinci Resolve (use davinci-resolve).'
summary: "batch-transcode with Apple Compressor via its CLI — ProRes, H.264, HEVC and image-sequence deliverables from files or folders, built-in and custom settings lookup, derived custom settings, monitored, stoppable and resumable batches, ffprobe-verified outputs"
category: video
risk: medium
tags: [compressor, apple, prores, hevc, h264, transcode, proxy, macos, video]
---

# Apple Compressor via its CLI

Compressor's binary takes command-line batches: `-batchname`, `-jobpath`, `-settingpath`
and `-locationpath` to submit, then `-monitor` and `-kill`. Jobs run in Compressor's
background service, so the app window doesn't need to be open. There is no AppleScript
dictionary and no network listener. This skill uses the CLI and the settings files only.
It was verified against **Compressor 5.4** on macOS 27 (arm64).

The CLI's `-help` text is incomplete and partly wrong, and its failure modes are easy to
miss. The scripts handle that:

- [scripts/cmp.sh](scripts/cmp.sh): `--check` prints the version, the settings folders and
  ffprobe status, and exits 2 if Compressor is missing. `--status ID` and `--kill ID` act
  on a batch. Any other arguments go straight to the binary.
- [scripts/cmp-settings.py](scripts/cmp-settings.py): lists built-in and custom settings
  with their English names (as shown in Compressor's sidebar), container, video FourCC
  and frame-size rule. Filter with `SEARCH` or `--codec hvc1`. `--resolve NAME` prints one
  setting's path.
- [scripts/cmp-encode.py](scripts/cmp-encode.py): files or folders × one or more settings
  in **one batch**. It works out the output paths, refuses collisions and source
  overwrites, skips outputs that are already complete, waits and reports each job, and
  kills the batch on Ctrl-C or `--timeout`. `--dry-run` prints the exact Compressor
  command.
- [scripts/cmp-setting-new.py](scripts/cmp-setting-new.py): derives a custom setting from
  any setting with a new name and frame size. It saves it where the Compressor app lists
  custom settings.
- [scripts/cmp-verify.py](scripts/cmp-verify.py): ffprobe checks of every output against
  its source and setting: codec, expected frame size, and duration or frame count.
- [references/gotchas.md](references/gotchas.md): **read this before writing raw
  Compressor commands.** It covers what `-help` gets wrong.
- [references/cli-reference.md](references/cli-reference.md): the full `-help` text with
  corrections.
- [references/settings.md](references/settings.md): built-in groups, where settings live,
  the setting XML, and how frame size is encoded.
- [references/recipes.md](references/recipes.md): worked examples: card proxies,
  deliverable sets, custom settings, image sequences, long batches.

## Workflow

```bash
H=scripts   # relative to this skill's directory
bash $H/cmp.sh --check                                  # 1. Compressor there? version?
python3 $H/cmp-settings.py hevc                         # 2. pick settings by name
python3 $H/cmp-encode.py SRC... --setting "NAME" [--setting ...] [layout] --dry-run
python3 $H/cmp-encode.py SRC... --setting "NAME" [...] [layout] --summary OUT.json
python3 $H/cmp-verify.py --summary OUT.json [--audio]   # 3. prove it
```

1. **Choose settings by their real names.** Never guess a path: built-ins sit deep inside
   the app bundle and some use localisation-key file names
   (`proRes422ProxyName.compressorsetting`). `--setting` takes a display name, a unique
   substring or a path. An ambiguous name is an error that lists the candidates, so pick
   one and pass it exactly.
2. **Encode with `cmp-encode.py`.** The raw CLI returns right away with exit 0 while the
   encode is still running. It creates a 0-byte output file at once. It overwrites
   existing files without asking. Its monitor drops jobs from the listing. The script
   handles all of this, and its exit code is the batch result: 0 all Successful or
   skipped, 1 a job failed, 2 rejected, 124 timeout, 130 interrupted.
3. **Verify with `cmp-verify.py`** before saying the job is done. Report one line per
   output (codec, size, duration) and anything that failed.

## Request → setting

Names below are the built-in display names. Confirm them with `cmp-settings.py`, since
they can change between Compressor versions.

| The user says | `--setting` |
|---|---|
| "ProRes Proxy, full resolution" (for editing) | `"Apple ProRes 422 Proxy"` (`apco`, `.mov`) |
| "half / quarter-size proxies" | `"ProRes Proxy half size"`, `"... quarter size"`, `"... eighth size"`. H.264 and HEVC proxies come in the same three sizes |
| "ProRes 422 / LT / HQ / 4444 / XQ master" | `"Apple ProRes 422"`, `"Apple ProRes 422 LT"`, `"Apple ProRes 422 HQ"`, `"Apple ProRes 4444"`, `"Apple ProRes 4444 XQ"`. MXF wrappers: give the path from `cmp-settings.py mxf` |
| "H.264 for the web / YouTube / Vimeo" | `"HD 1080p"` or `"HD 720p"` (Website Sharing: `.mov`, `avc1`, fits inside the size, never upscales). `"Up to 4K"` keeps up to UHD |
| "H.264 for Apple devices / most compatible" | `"Apple Devices HD (Best Quality)"`, `"Apple Devices HD (Most Compatible)"` (`.m4v`) |
| "HEVC" / "H.265" for Apple devices | `"Apple Devices 4K (HEVC 8-bit)"` or `"... (HEVC 10-bit)"` (`.m4v`, fits inside 3840×2160) |
| "HEVC MP4 for social" | `"HEVC 8-bit 420"` (Social Platforms HEVC: `.mp4`, fits inside 4096×2304. 10-bit and 4:2:2 variants are also available) |
| "image sequence / TIFF frames / EXR" | `"TIFF Image Sequence"`, `"OpenEXR Image Sequence"`. The output is a **folder** of `frame-NNNNNN.tiff` |
| "uncompressed" | `"Uncompressed 8-bit 422"` (`2vuy`), `"Uncompressed 10-bit 422"` (`v210`) |
| "my own preset", a file from a colleague | `--setting "/path/to/X.compressorsetting"`, or its name once it is in the custom folder |

Built-in H.264/HEVC settings don't let you set the size or bitrate from the CLI. For a
specific frame size, create a custom setting (next section). Don't edit `data-rate` in the
XML: on 5.4 it didn't cap the bitrate (see gotchas).

## Output layout

- **Default: next to each source**, named `<name><suffix>.<ext>`. The default suffix is
  `_<setting-slug>`, e.g. `A001_C001_apple-prores-422-proxy.mov`. Pass `--suffix _proxy`
  for each `--setting`, in the same order, to choose the name.
- **`--out-dir DIR`**: everything goes into DIR. With `--recursive`, subfolders are
  mirrored.
- The extension comes from the setting (`.mov`, `.m4v`, `.mp4`, `.mxf`). Image sequences
  become a folder named `<name><suffix>/`.
- Re-running the same command **resumes**: outputs that are complete (full duration) are
  skipped. When a folder is scanned, files that look like this run's own outputs (same
  suffix and extension) aren't treated as new sources. Use `--force` to re-encode.
- The script never writes over a source and never maps two jobs to one output.

## Custom settings

```bash
python3 $H/cmp-setting-new.py --from "Apple Devices 4K (HEVC 8-bit)" \
    --name "HEVC 720p Review" --size 1280x720            # or --fit 1920x1080 / --scale 50
python3 $H/cmp-encode.py SRC... --setting "HEVC 720p Review" --out-dir review/
```

The new file goes to `~/Library/Application Support/Compressor/Settings/<name>.compressorsetting`.
That's where the Compressor app lists custom settings, so the user can pick it there too.
The codec, container and audio come from `--from`, so choose the base for those. The
script writes the frame size into **both** `<automatic>` and `<bounds>`, because editing
`<bounds>` alone has no effect. Custom settings win over a built-in with the same name.
Check the result with `cmp-settings.py --user`.

## Long batches

- **One background service serves every client.** That means the Compressor app, other
  scripts and other agents on the same Mac. A heavy load, or any client running
  `-resetBackgroundProcessing`, can fail jobs with `Failed: … job controller down`, return
  `Cancelled`, or drop a batch from `-monitor` entirely. `cmp-encode.py` reports a dropped
  batch as `lost` after 90 s. In every case, run the same command again: complete outputs
  are skipped and only the missing ones are encoded. If it keeps failing, check the
  Activity window for other batches and let them finish. Don't reset the service: that
  kills everyone else's jobs too.
- `--timeout SEC` cancels the batch in Compressor, which deletes the partial files, and
  exits 124. Ctrl-C does the same and exits 130.
- `--no-wait` submits and prints the batch ID. Check it later with
  `bash scripts/cmp.sh --status ID` and stop it with `--kill ID`.
- Before starting hours of work, tell the user the scale (files × settings × duration)
  and offer to test one file first.

## Safety

- Everything is local. Sources are read, and new files are written beside them or into
  `--out-dir`. Nothing listens on a port.
- Commands are built as argument lists, never through a shell, so names with spaces or
  accents are safe. Pass the plain path: Compressor reads `file://` URLs literally and
  rejects `%20`.
- Existing outputs are replaced only with `--force`. Custom settings are replaced only with
  `cmp-setting-new.py --force`.
- Never run `-resetBackgroundProcessing [cancelJobs]` or `-repairCompressor` on your own
  initiative, not even to "fix" `job controller down`. They restart the service that every
  Compressor client shares, so other people's encodes get cancelled. Suggest them to the
  user only when Compressor fails on a single job while nothing else is queued.
