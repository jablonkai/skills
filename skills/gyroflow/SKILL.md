---
name: gyroflow
description: 'Stabilize video with Gyroflow''s CLI using gyroscope data: GoPro, Sony, DJI, Insta360 and other cameras with embedded motion data, or footage plus an external gyro log (.gcsv, Betaflight blackbox for FPV). Single clips or parallel folder batches with progress; smoothing, FOV, horizon lock and lens profile settings; ProRes/H.264/H.265/DNxHR output; reusable JSON presets; .gyroflow projects for the Resolve/FCP/Premiere plugins and STMap EXRs for Nuke or Fusion. Use for "stabilize my GoPro clips", "gyro-stabilize this FPV footage with the blackbox log", "batch stabilize this folder to ProRes", "make a Gyroflow preset with horizon lock", "export an STMap for Nuke", "Gyroflow project for the Resolve plugin". Not for footage without gyro data or stabilizing in a Resolve timeline (davinci-resolve), plain transcoding or compression (handbrake, compressor), Nuke comps beyond the STMap handoff (nuke), or FCP timelines (final-cut-pro).'
summary: "stabilize video with the Gyroflow CLI from embedded or external gyro data — single clips and parallel folder batches with progress, reusable JSON presets, .gyroflow project and STMap export for Resolve and Nuke, ffprobe-verified outputs"
category: video
compatibility: "Built for Gyroflow 1.6.3 (Mac App Store build) on macOS 27."
risk: low
tags:
    - gyroflow
    - stabilization
    - gyro
    - gopro
    - fpv
    - stmap
metadata:
  version: "1.0.2"
  author: "Tamás Jablonkai"
---

# Gyroflow via its CLI

Gyroflow stabilizes video from the camera's **gyroscope log**, not from image
analysis. It needs motion data, either embedded in the clip (GoPro GPMF, Sony,
DJI, Insta360, ...) or in an external log. The app ships a headless CLI at
`/Applications/Gyroflow.app/Contents/MacOS/gyroflow` that renders, and exports
projects, STMaps and metadata, without opening a window. Verified against
**Gyroflow 1.6.3** (Mac App Store build) on macOS 27.

Use the scripts, not the raw CLI. In 1.6.3 the CLI:
- **exits 0 on every failure** (missing file, write denied, unreadable input);
- **hangs** after an unreadable input, and one bad clip stalls the whole queue;
- in the App Store build, is **sandboxed**: it can only touch
  `~/Library/Application Support/Gyroflow/`.

The scripts stage clips into that folder (APFS clones, so no extra disk space),
check every clip first, judge success from the log and the files, kill stalled
runs, and move finished files to where you asked.

| Script | Does |
|---|---|
| [gf-probe.py](scripts/gf-probe.py) | `--check`: CLI path, version, sandbox, ffprobe. `CLIP/FOLDER...`: camera, IMU sample count, size, fps, frames. Exit 1 if a clip is unreadable or has **no gyro data** |
| [gf-render.py](scripts/gf-render.py) | Stabilize files or folders. Codec/profile, stabilization flags or `--preset`, `-j N`, `--gyro-file`, `--lens`. Progress per clip, resumable (existing outputs skipped), `--timeout`, `--stop`, `--dry-run`, JSON `--summary` |
| [gf-export.py](scripts/gf-export.py) | `--project [1-3]` `.gyroflow`, `--stmap [frame\|all]` EXR pairs, `--metadata NAME.csv\|json\|usd\|jsx`. Same settings flags as a render. Project paths are rewritten to point at the original clip |
| [gf-preset.py](scripts/gf-preset.py) | `create OUT.gyroflow` from flags or `--from` an existing preset or project (keeps only the reusable parts). `show FILE` summarizes a preset or project |
| [gf-verify.py](scripts/gf-verify.py) | ffprobe check of outputs against their sources (frames, duration, size) and expectations (`--codec`, `--profile`, `--size`, `--audio`) |

References, loaded when needed:
- [cli-reference.md](references/cli-reference.md): every raw flag, the `-p`/`-s` keys, and codec names with their `codec_options`.
- [presets.md](references/presets.md): the preset and project JSON schema, smoothing methods and their parameters, merge order.
- [recipes.md](references/recipes.md): GoPro batch, FPV with blackbox/gcsv, Insta360/DJI/Sony notes, STMap in Nuke and Fusion, `.gyroflow` in the Resolve/FCP/Premiere plugins.
- [gotchas.md](references/gotchas.md): **read before running the raw CLI.** Sandbox, exit codes, hangs, units, broken image sequences.

## Workflow

```bash
S=scripts   # relative to this skill's directory
python3 $S/gf-probe.py --check                          # 1. installed? sandboxed?
python3 $S/gf-probe.py CLIPS_OR_FOLDER                  # 2. does each clip carry gyro data?
python3 $S/gf-render.py CLIPS_OR_FOLDER --out-dir OUT [settings] --dry-run
python3 $S/gf-render.py CLIPS_OR_FOLDER --out-dir OUT [settings] --summary OUT/gf-summary.json
python3 $S/gf-verify.py --summary OUT/gf-summary.json --codec prores --profile HQ
```

1. **Probe first.** A clip without gyro data cannot be stabilized from embedded
   data. Gyroflow would still render it, just unstabilized, and still exit 0. So
   `gf-render.py` refuses such clips unless they have an external log: pass
   `--gyro-file LOG`, or put `CLIP.gcsv` next to the clip, where it is picked up
   automatically. Report "no gyro data" to the user rather than rendering anyway.
2. **Translate the request into flags** (table below) and show the dry run. Its
   `gyroflow ...` line is the reproducible raw command.
3. **Render.** Progress goes to stderr per clip in 10 % steps (`--progress-json`
   also prints JSON lines to stdout). Each clip ends up `done`, `skipped` or
   `failed` with a reason. One bad clip never blocks the others.
   - **When the user asks to be kept posted**, start the render in the background
     with stderr going to a log file, poll that log, and pass on what it actually
     says, e.g. "hero7 40 % (153/381 frames), hero8 30 %". Do this for every batch,
     even a short one. "Both reached 100 %" afterwards is not a progress update.
4. **Verify** with `gf-verify.py` against the user's expectations, then report:
   outputs, codec/profile, frame counts against the source, and any failures with
   their reasons.

## Request → flags

| The user says | Flags |
|---|---|
| "ProRes" / "ProRes 422 HQ" / "4444" | `--codec ProRes --profile HQ` (profiles: `Proxy`, `LT`, `Standard`, `HQ`, `4444`, `4444XQ`; anything else silently falls back to the default) |
| "H.265" / "H.264" + "100 Mbps" | `--codec hevc` / `--codec h264`, `--bitrate 100`. The default bitrate is auto, and small |
| "DNxHR for Resolve" | `--codec dnxhd --profile "DNxHR HQ"` (`DNxHR LB/SQ/HQ/HQX/444`) |
| "smoothing 0.8", "smoother", "less smooth" | `--smoothing 0.8` (0.001–1, default 0.5; FPV/action 0.6–0.9) |
| "locked-off / tripod look" | `--method "Fixed camera"` |
| "keep the horizon level" | `--horizon-lock 100` (percent; `--horizon-roll DEG` to tilt). Needs accelerometer data, which `gf-probe` shows as `+accel` |
| "less crop / zoom out" | `--fov 1.2` (>1 shows more of the frame and may expose black edges), or raise `--max-zoom` |
| "1080p output" | `--size 1920x1080` |
| "in parallel" / "use 3 renders at once" | `-j 3` (2–3 is a sensible maximum for 4K on Apple Silicon) |
| "use my preset" / "same settings as last time" | `--preset FILE` (a preset or a `.gyroflow` project). Flags override it |
| "blackbox log" / "external gyro" / "gcsv" | `--gyro-file LOG` (applies to every clip; autosync runs by default). One log per clip: `CLIP.gcsv` sidecars |
| "use this lens profile" | `--lens profile.json` (when Gyroflow didn't match one; GoPro, DJI and Insta360 usually match automatically) |
| "no audio" | `--no-audio` |

## Presets

A preset is plain JSON (`version`, `stabilization`, `output`, `synchronization`).
Create one with `gf-preset.py create my.gyroflow --smoothing 0.8 --horizon-lock 100
--codec ProRes --profile HQ`, or derive one from a project tuned in the GUI with
`--from tuned.gyroflow`. Apply it with `gf-render.py ... --preset my.gyroflow`.
Save presets as **`.gyroflow`**: a positional `.json` input is read as a lens
profile. Schema and parameter ranges: [presets.md](references/presets.md).

## Handoff to editors and compositors

- **Resolve / FCP / Premiere plugins** stabilize inside the NLE from a
  `.gyroflow` project: `gf-export.py CLIP --out-dir DIR --project 2`. Type 2
  embeds the gyro data, which is required for external logs or synced clips. Type
  1 is fine when the clip has embedded gyro.
- **Nuke / Fusion / After Effects**: `gf-export.py CLIP --out-dir DIR --stmap`
  writes `CLIP-undistort-0.exr` and `CLIP-redistort-0.exr`. Wire them into an
  STMap node: the undistort map at output size removes lens distortion, and the
  redistort map at source size puts it back after comp work. `--stmap all` writes
  one pair per frame, which includes the stabilization motion. That is large, so
  say so first.
- Camera motion for 3D apps: `--metadata camera.csv` (or `.json`, `.usd`, `.jsx`
  for After Effects).

Recipes for each: [recipes.md](references/recipes.md).

## Stopping and long runs

- Speed scales with resolution and codec: 848×480 to ProRes ran at about 100 fps
  here, and 4K is many times slower. For big batches, time one clip first, then
  run `gf-render.py` in the background and read its stderr.
- `--timeout SEC` stops cleanly with exit 124, and re-running the same command
  resumes, because finished outputs are skipped.
- `gf-render.py --stop` kills any render started by these scripts and removes
  its staging folder.
- `--stall SEC` (default 120) kills a run that has gone silent, which is how
  Gyroflow fails on an input it can't read.

## Limits

- **Image sequences (PNG/EXR) don't render in the App Store build.** It writes
  one empty `..._%2505d.png`, and the script refuses the job with that message.
  Render `--codec ProRes --profile 4444` and extract frames with ffmpeg, or
  install the DMG build from gyroflow.xyz and point `GYROFLOW_BIN` at it, which
  also skips staging.
- `--watch FOLDER` (the CLI's hot-folder daemon) is not wrapped: it never exits,
  and in the sandbox it can only watch inside the Gyroflow folder. See
  [cli-reference.md](references/cli-reference.md).
- Gyroflow can't stabilize footage that has no motion data. Optical-flow
  stabilization belongs to the NLE (Resolve's stabilizer, the `davinci-resolve`
  skill).

## Safety

- Everything is local. Sources are cloned, never modified, and existing outputs
  are only replaced with `--force`.
- Staging lives in `~/Library/Application Support/Gyroflow/agent-runs/<run>/` and
  is deleted when the run ends, including on failure, timeout and `--stop`.
- Commands are built as argument lists, never through a shell.
- Gyroflow's GUI settings (`settings.json`) supply defaults the CLI inherits, such
  as the default codec. The scripts never edit them. Pass explicit flags when a
  setting matters.
