# Presets

A preset is a complete, named set of encode settings. HandBrakeCLI knows the
built-in presets and any preset imported from a JSON file. Flags passed on the
command line override single settings of the chosen preset.

## Built-in presets

```bash
python3 scripts/hb-preset.py --builtin            # every built-in, as Folder/Name
python3 scripts/hb-preset.py --builtin 1080p      # filter
python3 scripts/hb-preset.py --resolve "H.265 MKV 1080p30"   # what it really does
```

Pass the name **without** its folder: `-Z "Fast 1080p30"`. Names are case-sensitive.
The folders on 1.11.2:

| Folder | What for |
|---|---|
| `General/` | `Very Fast`/`Fast`/`HQ`/`Super HQ` × 480p–2160p. H.264 in MP4, plus 4K HEVC and AV1 variants. `Fast 1080p30` is the GUI's default |
| `Web/` | `Creator 720p60`–`2160p60` (uploads), `Social 25 MB 30 Seconds 1080p60` … `Social 10 MB 2 Minutes 360p60` (size-capped clips) |
| `Devices/` | Amazon Fire, Android, Apple, Chromecast, Playstation, Roku, Xbox targets |
| `Matroska/` | H.264/H.265/AV1/VP9 in MKV, 480p–2160p |
| `Hardware/` | `H.265 Apple VideoToolbox 1080p`/`2160p 4K` are the ones that run on a Mac. NVENC, QSV, VCN and MF need PC hardware |
| `Professional/` | Production Max/Standard/Proxy, DNxHR, ProRes: intermediate formats, huge files |
| `CLI Defaults/` | `CLI Default`, the settings used when you give no preset |

Resolved example: `H.265 MKV 1080p30` = `x265_10bit` RF 22 slow, max 1920x1080,
peak 30 fps, AAC 160k stereo from the first audio track, MKV. `…30` presets use a
**peak frame rate** (`VideoFramerateMode: pfr`). Sources up to 30 fps keep their
rate, but a 50/60 fps source is reduced to 30 fps. Pick a `…60` preset, or add
`-- --pfr -r 60`, when motion smoothness matters.

## Presets from the HandBrake GUI

The GUI is sandboxed on macOS. Its preset store lives under
`~/Library/Containers/fr.handbrake.HandBrake/…`, which the CLI (and a terminal
without Full Disk Access) cannot read, so **`--preset-import-gui` does not see GUI
presets**. Export them instead:

1. In HandBrake: open the **Presets** window (⌘T, or Window ▸ Presets), select the
   custom preset, then **gear/⋯ menu ▸ Export…** (or **Presets ▸ Export…** in the
   menu bar), and save a `.json` file.
2. Inspect it: `python3 scripts/hb-preset.py MyPreset.json`. This prints the exact
   `-Z` name and the key settings.
3. Use it:
   `python3 scripts/hb-encode.py SRC… --out-dir OUT --preset-file MyPreset.json --preset "My Preset"`.

If the user can't find the file, ask them to export it. Don't try to read the
sandbox container.

## JSON layout

```json
{
  "PresetList": [
    { "PresetName": "Archive 720p AV1", "Type": 1, "Folder": false,
      "FileFormat": "av_mkv",
      "VideoEncoder": "svt_av1", "VideoQualityType": 2, "VideoQualitySlider": 30.0,
      "VideoPreset": "8", "PictureWidth": 1280, "PictureHeight": 720,
      "AudioTrackSelectionBehavior": "first", "AudioLanguageList": [],
      "AudioList": [{ "AudioEncoder": "opus", "AudioBitrate": 160, "AudioMixdown": "stereo" }],
      "SubtitleTrackSelectionBehavior": "none", "SubtitleBurnBehavior": "none", ... }
  ],
  "VersionMajor": 72, "VersionMinor": 0, "VersionMicro": 0
}
```

- A preset with `"Folder": true` holds more presets in `ChildrenArray`, and
  `hb-preset.py` walks them. On the CLI, address a nested preset by its own name.
- `VersionMajor` is the **preset format** version, not the app version. A newer CLI
  upgrades older exports on import. An export from a newer HandBrake than the CLI may
  carry keys the CLI ignores, so resolve it (`--resolve NAME --preset-file F`) and
  check the settings.
- `VideoQualityType`: 2 = constant quality (`VideoQualitySlider` is the RF), 1 = average
  bitrate (`VideoAvgBitrate` kbit/s), 0 = target size (legacy).
- `PictureWidth/Height` are maxima. The picture is never upscaled unless
  `PictureAllowUpscaling` is set.
- `AudioList` is the **output** track template. Which **source** tracks feed it comes
  from `AudioTrackSelectionBehavior` (`first` | `all` | `none`) and
  `AudioLanguageList`. The same holds for subtitles (`SubtitleTrackSelectionBehavior`,
  `SubtitleLanguageList`, `SubtitleBurnBehavior`: `none` | `foreign` | `first` |
  `foreign_first`).

## Making a preset from the CLI

A preset for the user to import into the GUI, or to reuse later:

```bash
HandBrakeCLI -Z "Fast 1080p30" -e x265 -q 24 -E opus -B 128 \
  --preset-export "My HEVC 1080p" --preset-export-description "x265 RF24, Opus" \
  --preset-export-file my-hevc-1080p.json
```

The file is in the same format as a GUI export (GUI: Presets ▸ Import…).
