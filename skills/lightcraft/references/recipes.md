# LightCraft recipes

Worked jobs for lightcraft-cli 0.17.0. `S` is this skill's `scripts/` folder. Every path
in JSON params is absolute. `LIB`, `IN` and `OUT` stand for absolute paths.

## Contents

- [Import a shoot, auto tone, nudge exposure, export](#import-a-shoot-auto-tone-nudge-exposure-export)
- [Copy one photo's look to others](#copy-one-photos-look-to-others)
- [Cull: rate, flag, label, keyword, then list](#cull-rate-flag-label-keyword-then-list)
- [Develop raws: white balance, profile, preset](#develop-raws-white-balance-profile-preset)
- [One file, no library](#one-file-no-library)
- [Query the library](#query-the-library)
- [Export variants](#export-variants)
- [HDR and panorama merge](#hdr-and-panorama-merge)

## Import a shoot, auto tone, nudge exposure, export

The trap is that auto tone acts on the active photo only, so loop with `forEach`. The
"+0.5 EV" is relative to each photo's auto result, so use `quickAdjust`, not `set`.

```sh
python3 $S/lc_verify.py hash "$IN" > /tmp/originals.json      # before anything else
mkdir -p "$OUT"
python3 $S/lc_run.py --library "$LIB" --import "$IN" - <<EOF
[{"forEach": "all", "do": [{"cmd": "develop.auto"}]},
 {"command": "develop.quickAdjust", "params": {"control": "light.exposure", "delta": 0.5, "ids": "@all"}},
 {"command": "app.export", "params": {"ids": "@all", "dir": "$OUT", "format": "jpeg", "longEdge": 2048, "quality": 90}}]
EOF
python3 $S/lc_query.py photos  --library "$LIB"                             # 5 photos? (duplicates are skipped)
python3 $S/lc_query.py develop --library "$LIB" --ids all --keys light      # each one's auto values, exposure +0.5
python3 $S/lc_verify.py files "$OUT" --count 5 --ext jpg --long-edge 2048
python3 $S/lc_verify.py hash "$IN" --compare /tmp/originals.json
```

`lc_run.py` resolves `forEach: "all"`, filters and `"@all"` after the `--import`. In a
library that already holds other photos, use a filter instead of `"@all"` so that only
this shoot is touched, e.g. `{"forEach": {"folder": "$IN"}, …}`, or the ids from
`lc_query.py photos --json`.

## Copy one photo's look to others

The copy and the paste must happen in **one process**. Both ways below work:

```json
[{"command": "library.select", "params": {"ids": [1], "active": 1}},
 {"command": "develop.copy"},
 {"command": "develop.paste", "params": {"ids": [2, 3, 4, 5]}}]
```

```json
[{"command": "library.select", "params": {"ids": [1, 2, 3, 4, 5], "active": 1}},
 {"command": "develop.sync"}]
```

- Both leave crop, masks and spot removal out by default. Pass
  `groups: ["light", "whiteBalance", …]` to copy only part of the look.
- Verify with `lc_verify.py same --library LIB --ids 1,2,3,4,5`. It compares every
  setting except crop, masks, spots, red eye and orientation, and exits 1 on a difference.
- Then export as above. The originals are unchanged because edits live in the library.

## Cull: rate, flag, label, keyword, then list

```sh
python3 $S/lc_run.py --library "$LIB" - <<'EOF'
[{"command": "photo.rate",    "params": {"rating": 5, "ids": [2, 4]}},
 {"command": "photo.setMeta", "params": {"ids": [2, 4], "addKeywords": ["portfolio"]}},
 {"command": "photo.flag",    "params": {"flag": "pick", "ids": [2, 4]}},
 {"command": "photo.label",   "params": {"label": "green", "ids": [2]}}]
EOF
python3 $S/lc_query.py photos --library "$LIB" --rating 5           # 5 stars (atLeast = exactly for 5)
python3 $S/lc_query.py photos --library "$LIB" --rating 3 --op exactly
python3 $S/lc_query.py photos --library "$LIB" --keyword portfolio --flag pick
```

To work by file name, look the ids up first with `lc_query.py photos --text IMG_0004`.
`text` matches file names, titles and captions.

## Develop raws: white balance, profile, preset

```json
[{"forEach": {"kind": "raw"}, "do": [
   {"command": "develop.wb", "params": {"mode": "custom", "temp": 5200, "tint": 5}},
   {"command": "develop.profile", "params": {"id": "<id from profiles.list>"}}]},
 {"command": "preset.apply", "params": {"id": "lc.crisp-landscape", "amount": 80, "ids": [1, 2, 3]}},
 {"command": "app.export", "params": {"ids": [1, 2, 3], "dir": "/abs/out", "format": "tiff", "bitDepth": 16, "colorSpace": "adobeRgb", "longEdge": 0}}]
```

- `develop.wb` and `develop.profile` act on the active photo, hence the `forEach`.
  `preset.apply` takes `ids`.
- List the built-in presets with `lightcraft-cli run --demo presets.list`. Import the
  user's own with `preset.import {paths: [...]}` (.lcpreset, XMP, .lrtemplate, .zip).
- B&W: `develop.treatment bw=true` per photo, or `preset.apply lc.bw-high-contrast`.
- For raw test files, `lightcraft-cli synth-merge hdr -o DIR` writes three DNGs.

## One file, no library

```sh
lightcraft-cli render in.dng -o out.jpg --set light.exposure=0.3 --set wb.temp=5600 \
    --preset lc.warm-glow --size 2048 --quality 90
```

This route has no auto tone, catalogue or keywords. Use it when the user only wants a
developed copy of a file or two.

## Query the library

```sh
python3 $S/lc_query.py photos --library "$LIB" --from 2024-06-01 --to 2024-08-31
python3 $S/lc_query.py photos --library "$LIB" --filter '{"camera": "X-T5", "rating": 4}'
python3 $S/lc_query.py photos --library "$LIB" --filter '{"edited": false}' --json
lightcraft-cli run --library "$LIB" catalog.stats        # counts per year/month/day, picks, rejects
lightcraft-cli run --library "$LIB" keyword.list         # the keyword tree with counts
```

Report the `total` along with the list, and say which filter was used.

## Export variants

```json
{"command": "app.export", "params": {
  "ids": [1, 2, 3], "dir": "/abs/web", "format": "jpeg", "longEdge": 1600, "quality": 82,
  "colorSpace": "srgb", "sharpen": "screen", "metadata": "copyright", "removeLocation": true,
  "watermark": {"text": "© 2026 Name", "anchor": "bottomRight", "opacity": 0.6},
  "naming": "<as listed by photo.renameTokens>", "conflict": "overwrite"}}
```

- Other sizes: `width`+`height` (fit inside), `shortEdge`, `megapixels`, `percent`. Use
  `longEdge: 0` for full size.
- `format: "original"` copies the original plus an XMP sidecar of the edits.
- Save a reusable preset with `export.savePreset {name, params}`, then use
  `app.export {preset: name, ids, dir}`.
- `export.contactSheet` writes a PDF proof sheet.

## HDR and panorama merge

`merge` writes next to the **first input**. Copy the brackets to a work folder unless
the user wants the DNG beside the originals.

```sh
cp -R /path/brackets /tmp/hdr-work
lightcraft-cli merge hdr --deghost medium /tmp/hdr-work/*.dng       # → <first>-HDR.dng, JSON result
lightcraft-cli merge hdr --preview /tmp/hdr.png /path/brackets/*.dng  # preview only, writes nothing beside the inputs
lightcraft-cli merge hdr-batch /tmp/shoot-copy                      # every bracket set in a folder
```

Inside a library: `merge.hdr {ids, deghost, stack}` / `merge.panorama`.
