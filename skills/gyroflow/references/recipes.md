# Recipes

Paths are relative to the skill directory (`S=scripts`). Every recipe starts with
`python3 $S/gf-probe.py` on the clips.

## GoPro folder → ProRes HQ, two at a time

```bash
python3 $S/gf-probe.py ~/Footage/day1
python3 $S/gf-render.py ~/Footage/day1 --out-dir ~/Footage/day1/stabilized \
  --codec ProRes --profile HQ --smoothing 0.8 -j 2 --summary ~/Footage/day1/stabilized/gf-summary.json
python3 $S/gf-verify.py --summary ~/Footage/day1/stabilized/gf-summary.json --codec prores --profile HQ
```

- GoPro HERO5 and later embed gyro and accelerometer data (GPMF). HERO8+ with
  HyperSmooth on is already stabilized in camera, so turn it off when shooting
  for Gyroflow, or expect little gain.
- `.LRV`/`.THM` proxies next to the clips are ignored when a folder is given.

## FPV footage with a Betaflight blackbox log

```bash
python3 $S/gf-probe.py flight.mp4 -g flight.bbl          # does the log parse? IMU samples?
python3 $S/gf-render.py flight.mp4 -g flight.bbl --out-dir out --codec h264 --bitrate 80 \
  --smoothing 0.7 --lens caddx_ratel2_4k.json
```

- Autosync is on by default with an external log (`do_autosync`). For long
  flights, give it a hint with `--sync '{"initial_offset": 0.5, "search_size": 3}'`.
- Many FPV cameras (naked GoPro, Runcam) need a lens profile from Gyroflow's
  database or a GUI calibration. Pass it with `--lens`.
- A gyro-only log has no accelerometer data, so `--horizon-lock` has nothing to
  work with.
- Several flights, each with its own log: name the logs `<clip>.gcsv` (or
  convert them), put each next to its clip, and give the folder. The script runs
  one Gyroflow pass per log.

## Insta360, DJI, Sony

- **Insta360** (`.insv`, `.mp4`): the gyro data is in the file. For 360° footage,
  Gyroflow stabilizes a flat crop only. Reframing belongs to Insta360 Studio.
- **DJI** (Action, Avata, O3): the gyro data is in the MP4. DJI's own EIS/RockSteady
  must be off for Gyroflow to have anything to do.
- **Sony** (recent a7/FX/ZV bodies): gyro is embedded in the MP4/MXF metadata.
  In-body or lens stabilization should be off when shooting for Gyroflow.
- **Blackmagic BRAW/RED R3D**: supported when their gyro metadata is present.
  Decoding needs the vendor SDKs Gyroflow bundles.

## Build a preset, apply it to a new clip

```bash
python3 $S/gf-preset.py create ~/Presets/fpv-smooth.gyroflow \
  --smoothing 0.9 --fov 1.1 --horizon-lock 100 --codec ProRes --profile HQ
python3 $S/gf-preset.py show ~/Presets/fpv-smooth.gyroflow
python3 $S/gf-render.py new_clip.mp4 --out-dir out --preset ~/Presets/fpv-smooth.gyroflow
python3 $S/gf-export.py new_clip.mp4 --out-dir out --project 1 --preset ~/Presets/fpv-smooth.gyroflow  # read-back
```

From a clip already tuned in the GUI (File → Export → project):
`gf-preset.py create day1.gyroflow --from tuned.gyroflow`.

## STMap for Nuke or Fusion

```bash
python3 $S/gf-export.py shot010.mp4 --out-dir handoff --stmap --smoothing 0.8
#  handoff/shot010-undistort-0.exr  (output size)   handoff/shot010-redistort-0.exr  (source size)
```

- **Nuke**: `Read` (plate) → `STMap` (input `stmap` = `Read` of the undistort
  EXR, UV channels `rgb`) gives the undistorted plate. Comp at that size, then a
  second `STMap` with the redistort EXR on the CG/comp layer re-applies the lens
  distortion. The maps are 32-bit float; R = x/width, G = 1 − y/height (bottom-left
  origin, the standard Nuke STMap convention).
- **Fusion / Resolve Fusion page**: `Loader` (EXR) → `Texture` node or a
  `CustomTool` UV lookup; or install the Gyroflow OFX plugin instead (below).
- `--stmap frame` is lens distortion only, the same for every frame. For the
  stabilization motion as STMaps, use `--stmap all` (one pair per frame, about
  230 KB per pair at 848×480; scale up for 4K). Warn about size before running.
- STMaps ignore keyframes and use static zoom.

## `.gyroflow` project for the Resolve / FCP / Premiere plugin

```bash
python3 $S/gf-export.py A001.mp4 --out-dir handoff --project 2 --smoothing 0.6 --horizon-lock 100
```

- Type 2 embeds the gyro data, so the project works even when the plugin can't
  read the clip's metadata, and it is required for external logs. Type 1 is
  enough for embedded-gyro clips the plugin can read itself.
- **Resolve OpenFX**: install `Gyroflow.ofx.bundle` into
  `/Library/OFX/Plugins/` (from github.com/gyroflow/gyroflow-plugins). Then add
  the Gyroflow effect to the clip and click "Browse" to load the `.gyroflow`.
  "Load for current file" needs Resolve Studio with scripting set to Local.
- **FCP / Premiere**: per the plugin docs, a `.gyroflow` with the clip's base name
  next to the clip is loaded automatically. Pass the clip's own folder as
  `--out-dir` for that.
- The script rewrites the project's `videofile` and gyro paths to the original
  clip (they would otherwise point at the deleted sandbox copy) and drops sandbox
  bookmarks.

## Camera motion for 3D/compositing

```bash
python3 $S/gf-export.py shot010.mp4 --out-dir handoff --metadata camera.csv   # or .json, .usd, .jsx
```

This gives per-frame original and stabilized orientation (quaternions and Euler
angles) and FOVs. `.jsx` is an After Effects script and `.usd` a USD camera.

## Image sequences (App Store build)

```bash
python3 $S/gf-render.py shot.mp4 --out-dir tmp --codec ProRes --profile 4444
mkdir -p shot_png && ffmpeg -i tmp/shot_stabilized.mov -start_number 0 shot_png/shot_%05d.png
```
