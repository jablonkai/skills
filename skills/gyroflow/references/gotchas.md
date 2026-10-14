# Gyroflow CLI gotchas (1.6.3, macOS)

Everything here was reproduced against Gyroflow 1.6.3 (Mac App Store build,
`_MASReceipt`) on macOS 27 unless marked "per source". The scripts handle all of
these. Read this before running the raw CLI.

## The sandbox (App Store build)

- The app is sandboxed. Its only file exception is
  `~/Library/Application Support/Gyroflow/` (read-write). Anything outside it:
  - **input**: `Unable to read the video file.`, then the process **hangs**;
  - **output folder**: `Filesystem error IOError(PermissionDenied)`, exit 0;
  - **symlinks** into the folder that point outside it are refused too. Use
    copies or APFS clones (`cp -c`), which cost no extra disk space on the same
    volume.
- `Failed to create bookmark: ... URL type isn't supported` and
  `CFURLCopyResourcePropertyForKey failed ... no scheme` are noise. Ignore them.
- Check with `codesign -d --entitlements - /Applications/Gyroflow.app | grep
  sandbox`, or `gf-probe.py --check`.
- The DMG build from gyroflow.xyz (and `brew install --cask gyroflow`) is not
  sandboxed. With `GYROFLOW_BIN` pointing at it, the scripts skip staging.
- Info.plist reports `1.63.0`; `--version` prints `Gyroflow v1.6.3`.

## Exit codes and hangs

- **The exit code is always 0** in 1.6.3: missing file, permission denied, failed
  encode, unreadable input. Only argument-parse errors exit 1. Upstream master
  documents 0/1/2, but that is not in 1.6.3.
- Success signals in the log are:
  - `[<job>] Rendering completed: <name>` per job;
  - `[INFO] Done in <s>s` for the run;
  - errors as `[ERROR] [<job>] Error: <message>`.
- **An unreadable input (corrupt file, folder, sandbox-denied path) makes the
  process hang** after the error. In a queue, it also stops the *good* clips from
  rendering. Probe every clip first (`gf-probe.py`), and wrap raw calls in a
  timeout.
- **A missing input aborts the whole queue** with `File X doesn't exist.` and
  nothing renders.
- Relative input paths fail when the working directory differs. Always pass
  absolute paths.

## Inputs

- **Folders are not expanded**: a directory is queued as if it were a video, and
  hangs. Only `--watch` walks folders.
- A positional `*.json` is read as a **lens profile**. Two of them is an error,
  and a bad one panics. A `.gyroflow` with `videofile` is a project; one without
  is a preset.
- A clip with **no gyro data** "succeeds": it renders unstabilized (lens
  correction only) and exits 0. Check `gf-probe.py`'s IMU sample count.
- The CLI does **not** pick up a `<clip>.gcsv` sidecar on its own. Pass it with
  `-g`. `-g` applies to every clip of the run, so clips with different logs need
  separate runs (`gf-render.py` groups them).
- External logs only line up after sync: add `-s '{"do_autosync": true}'`. The CLI
  defaults leave autosync off.

## Output settings

- **The codec must go in `-p`.** A preset's `output.codec` is applied, but the file
  extension stays `.mp4`. ProRes in MP4 then fails (`Could not find tag for codec
  prores`), leaving a 0-byte `*.mp4.tmp`, exit 0. Per source, a preset's `output`
  block also overrides `-p`. So keep presets out of the output business on the CLI,
  or lift `output` into `-p` (the scripts do).
- **`codec_options` must match exactly.** For ProRes that is `HQ`, not
  `ProRes 422 HQ`. A wrong string silently gives ProRes Standard.
- The default codec comes from the GUI's `settings.json` (`defaultCodec`; here
  H.265). Set `codec` explicitly.
- The default bitrate is auto: 2.4 Mbps for an 848×480 HEVC. Set `bitrate` for
  delivery-quality H.264/H.265.
- `--export-project` writes nothing (`IOError NotFound`) unless `output_folder` is
  given in `-p`.
- Without `-f`, an existing output is a job error. The scripts always render into a
  fresh staging folder and check existence themselves.
- **PNG/EXR sequences are broken in the sandboxed build.** The `%05d` pattern is
  URL-encoded into a literal file name `<name>_%2505d.png` (0 bytes), and no frames
  are written. Workaround: ProRes 4444, then
  `ffmpeg -i in.mov -start_number 0 out_%05d.png` (or `.exr`).

## Stabilization values

- `horizon_lock_amount` is a **percentage** (0–100), and it only applies when
  `horizon_lock_roll` is present too. A preset with only the amount silently gives
  0 (reproduced).
- `method` must match exactly: `Default`, `Plain 3D`, `Fixed camera`,
  `No smoothing`. Unknown names fall back to `Default` (per source).
- `smoothing_params` is a list of `{"name": ..., "value": ...}`, and only the
  names you give are changed. `Fixed camera` has no `smoothness`.
- Horizon lock needs accelerometer data (`+accel` in `gf-probe.py`). GoPro since
  HERO5 has it. A gyro-only blackbox log doesn't.

## Lens profiles

- 12k+ profiles ship with the app and are matched automatically by camera
  identifier and resolution. The GoPro sample clips at 848×480 matched nothing and
  still rendered, with lens correction left at the default.
- Projects embed the matched or given profile as `calibration_data`. A preset has
  no `lens_profile` key.

## Logs

- Every run prints `[DEBUG]` lines and an MDK banner to stdout/stderr. Filter on
  `[ERROR]`, `[WARN]`, `Rendering progress`, `Rendering completed`, `Queue:`.
- `IMU duration X is different than video duration (Y)` is a normal warning for
  GoPro clips.
