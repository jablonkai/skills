# Gyroflow CLI reference (1.6.3)

Binary: `/Applications/Gyroflow.app/Contents/MacOS/gyroflow`. Checked against
`--help` and the v1.6.3 source (`src/cli.rs`, `src/rendering/render_queue.rs`).
Read [gotchas.md](gotchas.md) first: exit codes are always 0, and the App Store
build is sandboxed.

```
gyroflow [<input...>] [-f] [-j N] [-d N] [-p JSON] [-t SUFFIX] [-s JSON]
         [--stdout-progress] [--export-project N] [--export-metadata T:PATH]
         [--export-metadata-fields JSON] [--export-stmap T:FOLDER]
         [--preset FILE|JSON] [--open FILE] [--watch DIR] [-g GYRO]
         [-b N] [-r GPU] [--no-gpu-decoding] [--version]
```

## Inputs

| Input | Read as |
|---|---|
| video file (absolute path) | a job |
| `*.json` | a lens profile, applied to every job (only one allowed) |
| `*.gyroflow` containing `videofile` | a project: a job with all its settings |
| `*.gyroflow` without `videofile` | a preset |
| a folder | **a (bad) video**. Not expanded; it hangs |

## Flags

| Flag | Meaning |
|---|---|
| `-f`, `--overwrite` | overwrite existing outputs (otherwise an existing output is a job error) |
| `-j N` | parallel renders (default 1) |
| `-d N` | when done: 1 shut down, 2 reboot, 3 sleep, 4 hibernate, 5 logout. **Never use this in automation** |
| `-p JSON` | output params, merged into the defaults (keys below) |
| `-t SUFFIX` | output name suffix, default `_stabilized`. Output is `<stem><suffix><ext>` |
| `-s JSON` | sync params (keys below). Without it, the first preset's `synchronization` is used |
| `--stdout-progress` | `[jobid] Rendering progress: n/m frames (p%) ETA xs` lines |
| `--export-project N` | write `<stem>.gyroflow` to `output_folder` instead of rendering: 1 default, 2 with gyro data, 3 with processed gyro data, 4 render **and** write a type-2 project. Needs `output_folder` in `-p` |
| `--export-metadata T:PATH` | 1 full metadata, 2 parsed metadata (JSON), 3 camera data. Type 3's format comes from the extension: csv (default), json, usd, jsx |
| `--export-metadata-fields JSON` | filter for type 3: `{"original": {"gyroscope", "accelerometer", "quaternion", "euler_angles"}, "stabilized": {"quaternion", "euler_angles"}, "zooming": {"minimal_fovs", "fovs", "focal_length"}}`, each a bool |
| `--export-stmap T:FOLDER` | 1 a single frame (frame 0), 2 every frame. Writes `<clip.ext>-<brand>-<model>-<lens>-undistort-<n>.exr` and `...-redistort-<n>.exr` |
| `--preset FILE\|JSON` | apply a preset after processing. Its keys overwrite the defaults and `-p` |
| `--open FILE` | open in the GUI (not headless) |
| `--watch DIR` | hot folder: queues **new** `mp4 mov mxf mkv webm insv gyroflow png exr dng braw` files once their size is stable for 1 s; skips names containing `<suffix>.`. Never exits |
| `-g FILE` | external gyro log for **every** video in the run |
| `-b N` | processing-device index (default: the GUI setting) |
| `-r NAME` | rendering GPU, substring match: `apple m`, `nvidia`, `amd`, `intel` |
| `--no-gpu-decoding` | software decoding (try it when hardware decoding fails) |

## `-p` output params

| Key | Value |
|---|---|
| `codec` | `H.264/AVC`, `H.265/HEVC`, `ProRes`, `DNxHD`, `CineForm`, `AV1`, `EXR Sequence`, `PNG Sequence` |
| `codec_options` | ProRes: `Proxy` `LT` `Standard` `HQ` `4444` `4444XQ`. DNxHD: `DNxHD` `DNxHR LB` `DNxHR SQ` `DNxHR HQ` `DNxHR HQX` `DNxHR 444`. PNG: `8-bit`, `16-bit`. Must match exactly |
| `bitrate` | Mbps (H.264/H.265/AV1) |
| `output_width`, `output_height` | output size (default: source) |
| `output_folder` | absolute folder. Relative paths resolve against the input's folder |
| `output_filename` / `output_path` | explicit name / absolute path (one job only) |
| `use_gpu` | GPU encoding (ProRes on macOS uses `prores_videotoolbox` when true, otherwise `prores_ks`) |
| `audio`, `audio_codec` | bool; `AAC` or `PCM (s16le)` / `PCM (s24le)` ... |
| `pixel_format`, `encoder_options` | ffmpeg pixel format; extra `-key value` encoder options |
| `keyframe_distance` | seconds |
| `interpolation` | `Bilinear`, `Bicubic`, `Lanczos4`, `EWA: RobidouxSharp`, `EWA: Robidoux`, `EWA: Mitchell`, `EWA: Catmull-Rom` |
| `preserve_other_tracks` | keep the data and timecode tracks (forces `.mov`) |
| `pad_with_black`, `export_trims_separately` | bool |
| `metadata` | `{"comment": "..."}` |

Extension per codec: `.mov` for ProRes, DNxHD and CineForm; `.mp4` for H.264,
H.265 and AV1 (`.mov` with `preserve_other_tracks`); `_%05d.png` / `_%05d.exr`
for sequences.

JSON may use single quotes (`"{ 'codec': 'ProRes' }"`, as in `--help`), because the
CLI swaps `'` for `"`. Real JSON works too.

## `-s` sync params

`do_autosync` (bool, **needed for external logs**), `initial_offset` (s),
`initial_offset_inv`, `search_size` (s), `calc_initial_fast`, `max_sync_points`,
`every_nth_frame`, `time_per_syncpoint` (s), `of_method`, `offset_method`,
`pose_method`, `custom_sync_pattern`, `auto_sync_points`, `processing_resolution`
(e.g. 720).

Autosync only runs when `do_autosync` is true and the clip has no accurate
timestamps. Embedded GoPro/Sony/DJI/Insta360 data needs no sync.

## External gyro formats

Gyroflow (telemetry-parser) reads `.gcsv`, Betaflight/INAV blackbox (`.bbl`,
`.bfl`, `.csv` exports), ArduPilot `.bin`/`.log`, Runcam/iFlight/Caddx logs, and
Sony/DJI/Insta360 sidecars. Minimal `.gcsv`:

```
GYROFLOW IMU LOG
version,1.3
id,my_logger
orientation,YxZ
tscale,0.001
gscale,0.00122173047
ascale,0.00048828125
t,gx,gy,gz,ax,ay,az
0,12,40,95,-1002,-15510,-3011
```

Each raw value is multiplied by its scale: t×tscale = s, g×gscale = rad/s,
a×ascale = g. Defaults: tscale 0.001, gscale 1, ascale 1, orientation `xzY`.
`orientation` maps the sensor axes to camera axes. If the stabilized result
rotates the wrong way, the orientation is wrong.
