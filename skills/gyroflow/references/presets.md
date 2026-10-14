# Presets and projects

Both are JSON. A **preset** carries reusable settings. A **project**
(`.gyroflow` with `videofile`) is a preset plus one clip's paths, gyro source,
sync offsets, trims and, for types 2/3, the motion data itself.

## Preset

```json
{
  "version": 2,
  "stabilization": {
    "method": "Default",
    "smoothing_params": [{"name": "smoothness", "value": 0.8}],
    "fov": 1.1,
    "max_zoom": 130.0,
    "horizon_lock_amount": 100.0,
    "horizon_lock_roll": 0.0,
    "lens_correction_amount": 1.0
  },
  "output": {"codec": "ProRes", "codec_options": "HQ"},
  "synchronization": {"do_autosync": true, "search_size": 3}
}
```

- Only the keys present are applied. Everything else keeps the defaults from the
  GUI's `settings.json` and the CLI.
- `version` isn't checked on import. Exported projects say 3.
- Save presets as `.gyroflow`. A `.json` positional input is a lens profile.
- `output.codec` in a preset doesn't change the file extension. `gf-render.py`
  moves the `output` block into `-p`. With the raw CLI, pass the codec in `-p`.

## `stabilization` keys

| Key | Meaning |
|---|---|
| `method` | `Default`, `Plain 3D`, `Fixed camera`, `No smoothing` (exact; unknown → Default) |
| `smoothing_params` | list of `{name, value}` for the method (table below) |
| `fov` | FOV factor. 1.0 = default crop; >1 zooms out (wider, may show edges) |
| `max_zoom` | dynamic zoom cap in percent (default 130) |
| `max_zoom_iterations` | zoom solver iterations (default 5) |
| `adaptive_zoom_window` | seconds of smoothing for dynamic zoom; 0 = no zoom, -1 = static zoom |
| `adaptive_zoom_center_offset` | `[x, y]` |
| `adaptive_zoom_method` | integer as in the GUI |
| `horizon_lock_amount` | percent 0–100 (**both** horizon keys must be present) |
| `horizon_lock_roll` | degrees added to the locked horizon |
| `use_gravity_vectors` | use the camera's gravity vectors when available |
| `horizon_lock_integration_method` | integer as in the GUI |
| `lens_correction_amount` | 0–1 (0 keeps the fisheye look, 1 fully rectilinear) |
| `frame_readout_time` | rolling-shutter readout in ms (negative = bottom-to-top); clip-specific |
| `additional_rotation`, `additional_translation` | `[pitch, yaw, roll]` / `[x, y, z]` |
| `video_speed`, `video_speed_affects_smoothing`, `video_speed_affects_zooming`, `video_speed_affects_zooming_limit` | for retimed clips |
| `frame_offset` | clip-specific frame shift |

### Smoothing parameters per method

| Method | Params (range, default) |
|---|---|
| Default | `smoothness` (0.001–1, 0.5); `smoothness_pitch`/`_yaw`/`_roll` (used when `per_axis` > 0.1); `per_axis` (0/1); `max_smoothness` (0.1–5 s, 1); `alpha_0_1s` (0.01–1, 0.1); `trim_range_only` (0/1) |
| Plain 3D | `time_constant` (0.01–10 s, 0.25); `trim_range_only` |
| Fixed camera | `roll`, `pitch`, `yaw` (degrees, 0): a locked-off virtual tripod |
| No smoothing | none: lens correction and rolling-shutter fix only |

Booleans are numbers (> 0.1 means true).

## `output` and `synchronization`

The same keys as `-p` and `-s`: see [cli-reference.md](cli-reference.md). In a
preset, `output_width`/`output_height` become the preset output size.

## Merge order (per source, `render_queue.rs`)

1. built-in defaults + GUI `settings.json` (smoothing method, crop mode, codec)
2. `-p`, `-s`
3. the lens profile matched automatically by camera ID
4. `~/Library/Application Support/Gyroflow/lens_profiles/default.gyroflow`, if
   it exists, applied to **every** job. The scripts never write it. Tell the user
   when you find one, because it silently changes results.
5. a positional `.json` lens profile
6. `--preset`s, in order. Each overwrites only its own keys, `output` included

## Project file (exported)

The top-level keys are `title`, `version`, `app_version`, `videofile`,
`calibration_data` (the lens profile), `video_info`, `stabilization`,
`gyro_source` (`filepath`, `detected_source`, `imu_orientation`,
`file_metadata`), `offsets` (sync points, ms), `keyframes`, `trim_ranges_ms`,
`output` and `synchronization`, plus background and `*_bookmark` fields
(sandbox bookmarks, safe to drop).

`gf-preset.py create NEW.gyroflow --from PROJECT.gyroflow` keeps
`stabilization` (minus the readout time, frame offset and zoom centre),
`output` codec settings (minus the folder, filename, size and auto bitrate) and
`synchronization`. That turns a clip tuned in the GUI into a preset for the rest
of the shoot.
