# Gyroflow CLI gotchas (1.7.1, macOS)

Everything here was reproduced against Gyroflow 1.7.1 (Mac App Store build,
`_MASReceipt`) on macOS 27.2 unless marked "per source". Where 1.6.x behaved
differently it is noted, because the scripts still support it. The scripts
handle all of these. Read this before running the raw CLI.

## The sandbox (App Store build)

- The app is sandboxed. Its only file exception is
  `~/Library/Application Support/Gyroflow/` (read-write). Anything outside it:
  - **input**: `[<job>] Error: ... Unable to read the video file.`, exit 1;
  - **output folder**: `Failed to create the output ...: creating a temporary
    file in ...: Operation not permitted`, exit 1;
  - **symlinks** into the folder that point outside it are refused too
    (`Unable to read the video file.`). Use copies or APFS clones (`cp -c`),
    which cost no extra disk space on the same volume.
- **Relative paths** resolve against the sandbox container
  (`~/Library/Containers/xyz.gyroflow/Data/`), not the working directory. Always
  pass absolute paths.
- `Failed to create bookmark: ... URL type isn't supported`,
  `CFURLCopyResourcePropertyForKey failed ... no scheme`,
  `sandbox_extension_issue_file failed` and
  `[h264_videotoolbox] -constant_bit_rate true is not supported` (printed on
  every run, whatever the codec) are noise. Ignore them.
- Check with `codesign -d --entitlements - /Applications/Gyroflow.app | grep
  sandbox`, or `gf-probe.py --check`.
- The DMG build from gyroflow.xyz (and `brew install --cask gyroflow`) is not
  sandboxed. With `GYROFLOW_BIN` pointing at it, the scripts skip staging.
- Info.plist reports `1.71.0`; `--version` prints `Gyroflow v1.7.1`.

## Exit codes and hangs

- **1.7.0+**: 0 success, 1 render failure (unreadable input, write denied,
  encoder error, failed optical analysis), 2 invalid arguments (missing input
  file, bad `--optical-tracking` value). An unknown flag exits 1.
- **1.6.x**: the exit code is always 0, and an unreadable input (corrupt file,
  folder, sandbox-denied path) makes the process **hang** and blocks the good
  clips of the queue. Fixed in 1.7.0 ("render queue hanging on unreadable
  files"): the bad job errors and the rest render.
- Exit 0 still doesn't prove a stabilized result: a clip without motion data
  renders unstabilized with exit 0 (see Inputs), and a wrong `codec_options`
  string gives exit 0 with the wrong profile. The scripts judge from the log and
  the files.
- Success signals in the log are:
  - `[<job>] Rendering completed: <name>` per job (only with `--stdout-progress`);
  - `[INFO] Done in <s>s` for the run;
  - errors as `[ERROR] [<job>] Error: <message>`.
- **A missing input aborts the whole queue** with `File X doesn't exist.`, exit
  2, and nothing renders.
- Wrap raw calls in a timeout anyway; the scripts keep their stall watchdog.

## Inputs

- **Folders are not expanded**: a directory is queued as a video and fails
  (`Unable to read the video file.`; 1.6.x hung). Only `--watch` walks folders.
- A positional `*.json` is read as a **lens profile**. Two of them is an error,
  and a bad one panics. A `.gyroflow` with `videofile` is a project; one without
  is a preset.
- A clip with **no motion data** "succeeds": it renders unstabilized (lens
  correction only) and exits 0. Check `gf-probe.py`'s IMU sample count. Since
  1.7.0, `--optical-correction 100` measures the motion from the picture
  instead (`gf-render.py --optical 100`).
- The CLI does **not** pick up a `<clip>.gcsv` sidecar for a video file on its
  own (re-checked in 1.7.1; 1.7.0 added it for image sequences only). Pass it
  with `-g`. `-g` applies to every clip of the run, so clips with different logs
  need separate runs (`gf-render.py` groups them).
- External logs only line up after sync: add `-s '{"do_autosync": true}'`. The CLI
  defaults leave autosync off. Since 1.7.0 the default offset method is the new
  "Optical analysis" (rs-sync before).
- 1.7.0+ accepts image sequences as input (first frame or a `A001_%06d.dng`
  pattern, `--image-sequence-fps`). The scripts only collect video files.
- 1.7.1 added "Default CLI behavior" in the app's Advanced settings: with input
  files **and no options**, the CLI may open the files in the app or queue them
  instead of rendering. Any option (`-f`, `-p`) restores rendering; the scripts
  always pass options.

## Optical correction (1.7.0+)

- `--optical-correction PCT` corrects the file's motion data with an optical
  analysis; on a clip without motion data it measures all of it.
  `--ignore-file-motion` measures everything from the video,
  `--optical-per-frame` gives one correction per frame (global shutter),
  `--optical-tracking klt|dis|gmflow` picks the tracker. The last three imply
  `--optical-correction`.
- Log lines: `Optical analysis: N frames, M measured pairs ...` and
  `Optical correction: measured in X of N frames, correction D deg`.
- `dis` failed on both test clips (`OpenCV ... dis_flow.cpp ... Assertion` on an
  848×480 GoPro clip, `Not enough of the image could be tracked` on a synthetic
  one): exit 1, no output. `klt` (the default) worked on both.
- An exported project keeps the analysis (`gyro_source.optical_correction`), so
  the NLE plugins get the corrected motion.

## Output settings

- **The codec must go in `-p`.** A preset's `output.codec` is applied, but the
  file extension stays `.mp4`. ProRes in MP4 then fails (`Could not find tag for
  codec prores`, `ffmpeg error: ... Invalid argument`), exit 1 in 1.7 (exit 0
  and a 0-byte `*.mp4.tmp` in 1.6.3). Per source, a preset's `output` block
  also overrides `-p`. So keep presets out of the output business on the CLI, or
  lift `output` into `-p` (the scripts do).
- **`codec_options` must match exactly.** For ProRes that is `HQ`. The
  `'ProRes 422 HQ'` example in 1.7.1's own `--help` silently gives ProRes
  **Standard**, as does any other wrong string (reproduced).
- The default codec comes from the GUI's `settings.json` (`defaultCodec`; here
  1 = H.265). Set `codec` explicitly.
- The default bitrate is auto: 2.4 Mbps for an 848×480 HEVC. Set `bitrate` for
  delivery-quality H.264/H.265.
- `--export-project` writes nothing (`IOError NotFound`, exit 1) unless
  `output_folder` is given in `-p`.
- Without `-f`, an existing output is a job error. The scripts always render into a
  fresh staging folder and check existence themselves.
- **PNG/EXR sequences are broken in the sandboxed build.** 1.7.1 fails with
  `Failed to check the output .../<name>_000…` and writes no frames, exit 1
  (1.6.3 wrote one 0-byte `<name>_%2505d.png`). Workaround: ProRes 4444, then
  `ffmpeg -i in.mov -start_number 0 out_%05d.png` (or `.exr`).

## Stabilization values

- `horizon_lock_amount` is a **percentage** (0–100), and it only applies when
  `horizon_lock_roll` is present too. A preset with only the amount silently gives
  0 (reproduced in 1.7.1).
- `method` must match exactly: `Default`, `Optimal path` (1.7.0+), `Plain 3D`,
  `Fixed camera`, `No smoothing`. Unknown names (even `Optimal`) fall back to
  `Default` (reproduced).
- `smoothing_params` is a list of `{"name": ..., "value": ...}`, and only the
  names you give are changed. `Fixed camera` has no `smoothness`.
- Horizon lock needs accelerometer data (`+accel` in `gf-probe.py`). GoPro since
  HERO5 has it. A gyro-only blackbox log doesn't. 1.7.1 fixed horizon drift in
  high-motion clips (a 1.7.0 regression).

## Lens profiles

- 12k+ profiles ship with the app and are matched automatically by camera
  identifier and resolution. The GoPro sample clips at 848×480 matched nothing and
  still rendered, with lens correction left at the default. Optical correction
  needs a valid profile to look right.
- Projects embed the matched or given profile as `calibration_data`. A preset has
  no `lens_profile` key.

## Logs

- Every run prints `[DEBUG]` lines and an MDK banner to stdout/stderr. Filter on
  `[ERROR]`, `[WARN]`, `Rendering progress`, `Rendering completed`, `Queue:`.
- `IMU duration X is different than video duration (Y)` and
  `This GoPro clip declares projection "GPRO", which this build does not render`
  are normal warnings for GoPro clips.
