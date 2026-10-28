# Pinned command ids (lightcraft-cli 0.15.0)

The registry has 376 commands in 0.15.0. This page pins the ones the common jobs need.
For anything else, or when a pinned id fails after an upgrade, look it up instead of
guessing. Unknown params are often ignored silently.

```sh
python3 $S/lc_query.py commands export preset   # ids/labels matching every word, with params
lightcraft-cli commands | grep -A1 '^develop.wb '  # one command's signature
lightcraft-cli commands --json                    # [{id, label, params, enabled, menu}]
lightcraft-cli controls                           # develop control ids, ranges, defaults
```

There is **no `describe` command**. The `params` text in `commands` is the whole
documentation of a command. **A** in the table below marks a command that acts on the
**active photo only** (select it first; it ignores `ids`, see
[gotchas.md](gotchas.md#active-photo-vs-ids)).

## Contents

- [Library and selection](#library-and-selection)
- [Rating, flags, labels, keywords, metadata](#rating-flags-labels-keywords-metadata)
- [Develop](#develop)
- [Presets and profiles](#presets-and-profiles)
- [Export](#export)
- [Develop control ids](#develop-control-ids)

## Library and selection

| Id | Params (abridged) |
|---|---|
| `library.import` | `{paths: [..], mode?: add\|copy\|move, destination?, organize?: date\|month\|flat\|template, …}`. `add` (the default) references the files in place |
| `library.select` | `{ids: [..], active?: id, mode?: replace\|add\|toggle\|range}` |
| `library.selectAll` / `library.selectNone` | `{}`; acts on the current view |
| `library.selectBy` | `{flag?, rating?, ratingOp?: gte\|eq\|lte, label?, add?}`; among the photos in view |
| `library.filter` | partial Filter (the same keys as `catalog.query`); not persisted |
| `library.state` | `{}` → filter, selection `{active, ids}`, clipboard, undo/redo |
| `library.folders` | `{}` → the folders the photos were imported from, with counts |
| `catalog.query` | `{filter?, sort?, offset?, limit?}` → `{photos: [{id, fileName, rating, flag, label, keywords, edited, captured, width, height, kind, format, …}], total}` |
| `catalog.stats` | `{}` → photos, edited, picks, rejects, keywords, byDate |
| `photo.inspect` | `{id?}`: one photo's record |
| `photo.allMetadata` | the full EXIF/IPTC of a photo |
| `photo.virtualCopy` | `{ids?, name?}` → `{ids}`: a new entry sharing the file, with independent settings |
| `photo.delete` | `{ids?}` → Recently Deleted. Ask before using; never use `deletePermanently` unasked |

**Filter keys:** `text`, `rating`, `ratingOp` (`atLeast`\|`exactly`\|`atMost`), `flag`
(`pick`\|`reject`\|`none`), `label`, `kind` (`image`\|`raw`\|…), `merged`, `edited`, `date`
(`YYYY[-MM[-DD]]`), `dateFrom`, `dateTo`, `keyword`, `person`, `camera`, `lens`, `album`,
`folder`, `libraryFolder`, `subfolders`, `imported`, `importedFrom`, `deleted`.

**Sort:** `{key: captureDate|importDate|editDate|fileName|rating|fileSize|random, ascending?}`.

## Rating, flags, labels, keywords, metadata

| Id | Params |
|---|---|
| `photo.rate` | `{rating: 0..5, ids?, advance?}` |
| `photo.flag` | `{flag: pick\|reject\|none, ids?}`. `photo.pick` / `photo.reject` / `photo.unflag` are the shortcuts |
| `photo.label` | `{label: red\|yellow\|green\|blue\|purple\|none, ids?}` |
| `photo.setMeta` | `{ids?, title?, caption?, creator?, copyright?, city?, country?, gps?, keywords?: [..] (replace), addKeywords?: [..], removeKeywords?: [..]}` |
| `keyword.create` | `{name, parent?, synonyms?, addToSelected?, ids?}`. Builds the tree; with `ids` it also assigns |
| `keyword.list` | `{}` → the tree `[{name, path, count, children}]`. `a\|b\|c` means hierarchy |
| `keyword.rename` / `keyword.merge` / `keyword.delete` | tree maintenance |
| `metadata.applyPreset` | `{name, ids?}` |

Keywording a photo is `photo.setMeta addKeywords=[..]`. There is no `keyword.add`.

## Develop

| Id | Params |
|---|---|
| `develop.set` | `{control, value}` or `{values: {control: value}}`, `ids?`. **Absolute** |
| `develop.quickAdjust` | `{control, delta, ids?}`. **Relative**, each photo from its own value |
| `develop.adjust` **A** | `{control, delta}`. Relative, active photo |
| `develop.auto` **A** | `{}` → the auto values it applied |
| `develop.wb` **A** | `{mode: asShot\|auto\|daylight\|cloudy\|shade\|tungsten\|fluorescent\|flash\|custom, temp?, tint?}` |
| `develop.treatment` **A** | `{bw?: bool}`; toggles when omitted |
| `develop.profile` **A** | `{id, amount?: 0..200}` (ids from `profiles.list`) |
| `develop.copy` **A** | `{groups?: [settingsGroup]}` (default: all but crop, masks, remove) |
| `develop.paste` | `{ids?, groups?}`; needs a `develop.copy` **in the same process** |
| `develop.sync` | `{groups?}`: the active photo's settings → all selected photos |
| `develop.autoSync` | `{on?}`: a **mode** where edits to the active photo copy to the selection |
| `develop.merge` **A** | `{settings: partial DevelopSettings JSON}` |
| `develop.reset` | `{ids?}` |
| `develop.resetControl` **A** | `{control}` |
| `develop.get` | `{id?}` → the full settings (snake_case keys, e.g. `light.exposure`, `wb.temp`) |
| `history.list` / `history.restore` | the active photo's edit steps |

**Settings groups** (`develop.copy`'s reply): `profile`, `treatment`, `whiteBalance`, `light`,
`toneCurve`, `color`, `colorMixer`, `colorGrading`, `effects`, `vignette`, `grain`,
`detail`, `optics`, `geometry`, `lensBlur`, `calibration` (plus `crop`, `masks`, `remove`
when named).

## Presets and profiles

| Id | Params |
|---|---|
| `presets.list` | `{}` → 41 built-ins in 0.15.0 (`lc.warm-glow`, `lc.teal-orange`, `lc.bw-high-contrast`, `lc.crisp-landscape`, …) plus user presets |
| `preset.apply` | `{id, amount?: 0..200, ids?}` |
| `preset.create` | `{name, group?, groups?}`: from the active photo |
| `preset.import` | `{paths, group?, dryRun?}`: .lcpreset, XMP, .lrtemplate, DNG presets, .zip |
| `preset.export` | writes `.lcpreset` |
| `profiles.list` / `develop.profile` | camera and creative profiles, imported LUTs |

## Export

| Id | Params (abridged) |
|---|---|
| `app.export` | `{ids?, dir?, path?, format?: jpeg\|png\|tiff\|webp\|avif\|jxl\|psd\|dng\|original, longEdge?\|shortEdge?\|width?+height?\|megapixels?\|percent?, quality?: 1..100, colorSpace?: srgb\|displayP3\|adobeRgb\|proPhoto\|rec2020, bitDepth?, sharpen?: none\|screen\|matte\|glossy, metadata?: all\|allExceptCamera\|copyright\|none, removeLocation?, naming?, conflict?: unique\|overwrite\|skip, watermark?, preset?}` → `{files: [{path, width, height, bytes}], bytes}` |
| `export.presets` | `{}` → `[{name, builtin, params}]`; use as `app.export {preset: name, …overrides}` |
| `export.savePreset` | `{name, params?}` |
| `export.contactSheet` | a contact-sheet PDF |

Use `dir=` for a folder and `path=` only for a single file with an extension (see
[gotchas.md](gotchas.md#export-paths-formats-and-re-runs)). The default `longEdge` is
3000, and `longEdge=0` means full size.

## Develop control ids

`lightcraft-cli controls` lists 122 of them. The common ones (range, default):

| Control | Range |
|---|---|
| `light.exposure` | −5..5 EV (0) |
| `light.contrast`, `light.highlights`, `light.shadows`, `light.whites`, `light.blacks` | −100..100 (0) |
| `wb.temp` | 2000..50000 K (6500) |
| `wb.tint` | −150..150 (0) |
| `color.vibrance`, `color.saturation` | −100..100 (0) |

Other prefixes: `effects.*` (clarity, dehaze, texture), `detail.*` (sharpening, noise
reduction), `vignette.*`, `grain.*`, `curve.*`, `mixer.*`, `grading.*`, `bw.*`, `optics.*`,
`geometry.*`, `calibration.*`, `hdr.*`, `crop.angle`. Values outside a range are
**clamped silently**: `light.exposure value=9` stored 5.0 with `ok: true`. Read them back
with `develop.get`.
