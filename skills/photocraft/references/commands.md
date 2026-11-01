# Engine commands most tasks need (pinned to 0.19.0)

The registry has 953 commands. This table pins the ids that were exercised for this
skill. For anything else, look it up instead of guessing an id:

```sh
python3 scripts/pc_inspect.py commands layerStyle          # every id containing the word, with params
python3 scripts/pc_inspect.py commands type create         # all words must match
python3 scripts/pc_inspect.py commands --exact image.imageSize
```

A guessed id fails with `unknown command`. A real id with a wrong param key is usually
ignored, so read the signature. `layer` params take a **numeric id** (see
[gotchas.md](gotchas.md#layer-names-vs-ids)). A trailing `?` marks an optional param; `=x`
is the default.

## Document and canvas

| Id | Key params |
|---|---|
| `file.new` | `width`, `height`, `mode` rgb\|gray\|cmyk\|lab, `depth` 8\|16\|32, `background` white\|black\|transparent\|#rrggbb, `resolution` |
| `image.imageSize` | `width`, `height` or `percent`, `resample` (bicubic, lanczos, preserveDetails…) → `{width,height}` |
| `file.automate.fitImage` | `width`, `height`, `dontEnlarge`: fit inside a box, aspect kept (**long-edge resize**) |
| `image.canvasSize` | `width`, `height`, `relative`, `anchor` topLeft…bottomRight, `extensionColor` |
| `image.crop` | `x`, `y`, `width`, `height`, `targetWidth/Height`, `contentAware` (fills the area a rotated or enlarged crop adds) |
| `image.trim` | `basedOn` transparent\|topLeft\|bottomRight |
| `image.imageRotation.90cw` / `.90ccw` / `.180` / `.flipCanvasHorizontal` | — |
| `image.mode.rgb` / `.grayscale`, `image.mode.bits8` / `.bits16` / `.bits32` | — |
| `layer.flattenImage` | — |
| `file.saveACopy` | `path`, `quality` 0..12, `layers` |

## Layers

| Id | Key params |
|---|---|
| `layer.new.layer` | `name`, `mode`, `opacity` |
| `layer.list` | `flat` → `{layers: [{id, name, kind, visible, bounds [x,y,w,h], selected, active}], activeLayer}` (top-down; the quickest id lookup inside a `run`) |
| `layer.new.group`, `layer.new.groupFromLayers` | `name`; the latter groups `layer` or, without it, the selected layers |
| `layer.setProps` | `layer` or `layers` [id…] (one step for all), `name` (one layer only), `visible`, `opacity` 0..1, `fill`, `blend` ("Multiply"…), `locked`, `clipped` |
| `layer.select` | `layer` id, or `name` + `occurrence` (for duplicate names), `mode` replace\|add\|toggle\|range\|remove |
| `layer.hideLayers` / `layer.showLayers` | `layer` (hideLayers **toggles** when every target is already hidden; prefer `setProps visible`) |
| `layer.duplicate`, `layer.delete`, `layer.mergeDown` | `layer` |
| `layer.moveTo` | `layer`\|`layers`, `target`, `position` above\|below\|into |
| `layer.arrange.bringToFront` / `.sendToBack` / `.bringForward` / `.sendBackward` | `layer` |
| `layer.translate` | `layer`, `dx`, `dy` |
| `edit.transform` | `layer`, `scaleX`/`scaleY` %, `rotate` deg, `dx`/`dy`, or `matrix`/`quad` |
| `layer.align.leftEdges` … `.bottomEdges`, `.horizontalCenters`, `.verticalCenters` | `to` auto\|layers\|selection\|canvas. `auto`: an active selection if any, else **one layer aligns to the canvas** (0.10.0+), several to their combined bounds |
| `layer.rasterize.layer` / `.type` / `.smartObject` | `layer` |
| `layer.exportAs` | `layer`, `path`, `scale` (CLI `run` only) |

## Content layers

| Id | Key params |
|---|---|
| `type.create` | `x`, `y` (**baseline** of point text), `text`, `box` [x,y,w,h] for paragraph text, `name`, `font`, `size` pt (**default 12**), `color` #rrggbb, `align` → `{layer, bounds [x0,y0,x1,y1]}` |
| `type.edit` | `layer`, `text` (replace all, styles kept), `replace {start,end,text}`, `runs` |
| `edit.findAndReplaceText` | `find`, `replace`, `action` changeAll, `allLayers` |
| `layer.newFillLayer.solidColor` | `color`; fills the active selection, or the whole canvas when there is none |
| `layer.newFillLayer.gradient` | `from`, `to`, `angle`, `style` linear\|radial\|… |
| `shape.create` | `kind` rect\|roundedRect\|ellipse\|polygon\|star\|line, `rect` [x,y,w,h], `radii`, `fill`, stroke keys |
| `layer.newAdjustmentLayer.<kind>` | `curves`, `levels`, `brightnessContrast`, `hueSaturation`, `vibrance`, `colorBalance`, `blackWhite`, `photoFilter`, `exposure`, `gradientMap`, `colorLookup`, `selectiveColor`, `channelMixer`, `invert`, `posterize`, `threshold` |
| `file.placeEmbedded` / `file.placeLinked` | `path`, `scale`, `fit`, `center` (CLI `run` only; in serve use `doc.place`) |
| `layer.smartObjects.replaceContents` | `layer`, `path` (CLI `run` only; in `serve` use `doc.replaceSmartObject`) |

## Selections and masks

| Id | Key params |
|---|---|
| `select.rect` | `x`, `y`, `width`, `height`, `ellipse`, `mode`, `feather` |
| `select.all`, `select.deselect`, `select.inverse` | — |
| `select.subject`, `select.sky`, `select.colorRange`, `select.magicWand` | see signature |
| `image.detectFaces` | `minScore` 0..1 → `{faces: [{score, rect [x,y,w,h], landmarks}]}`, best first (e.g. to crop around a face) |
| `layer.layerMask.revealAll` / `.hideAll` / `.revealSelection` / `.hideSelection` | `layer` |

## Layer styles

`layer.layerStyle.dropShadow` (`color`, `opacity` 0..100, `angle`, `distance`, `spread`,
`size`), `.stroke` (`size`, `position`, `color`), `.outerGlow`, `.innerShadow`,
`.innerGlow`, `.colorOverlay`, `.gradientOverlay`, `.patternOverlay`, `.bevelEmboss`,
`.satin`. Each takes `layer` (numeric id); without it they act on the selected layer(s).
`"add": true` stacks a second effect of the same kind. `layer.layerStyle.clear {layer}`
removes a style.

## Filters and pixel adjustments

These act on the active pixel layer. On a Smart Object they become smart filters.

`filter.sharpen.unsharpMask` (`amount` 1..500, `radius`, `threshold`),
`filter.sharpen.smartSharpen`, `filter.blur.gaussianBlur` (`radius`),
`filter.noise.reduceNoise`, and the rest of `filter.*`;
`image.adjustments.curves`, `.levels`, `.hueSaturation`, `.brightnessContrast`,
`.blackWhite`, `.desaturate`, `.invert`; `image.autoTone`, `image.autoContrast`,
`image.autoColor`.

## Layer comps, variables, export

| Id | Key params |
|---|---|
| `layerComp.new` | `name`, `visibility`, `position`, `appearance` (records the current state) |
| `layerComp.apply` | `comp` id\|name. an unknown name fails with `no layer comp named …` (0.10.0+) |
| `layerComp.update` | `comp` id\|name\|"*", `what` all\|visibility\|position\|appearance |
| `layerComp.list` | → `{comps, lastApplied}` |
| `file.export.layerCompsToFiles` | `dir`, `format` png\|jpg\|psd\|tiff, `prefix`, `comps` [id]. Files are named `<prefix>_NNNN_<comp>.<ext>` (CLI `run` only) |
| `file.export.layersToFiles` | `dir`, `format`, `prefix`, `visibleOnly` (CLI `run` only; in serve use `doc.exportLayers`) |
| `image.variables.define` | `defs: [{name, layer: <numeric id>, type: textReplacement\|visibility\|pixelReplacement}]` (**names are refused here**) |
| `file.import.variableDataSets` | `path` (CSV), `delimiter`. Header = variable names; a first column headed **`dataSet`** names each set |
| `image.variables.dataSets` | `dataSets: [{name, values: [{variable, kind, value}]}]`, `append` |
| `file.export.dataSetsAsFiles` | `dir`, `format`, `naming` "{name}" \| "{index}" \| "{document}". Colliding file names are rejected before anything is written |
| `file.export.presets.save` / `.get` / `.list` / `.delete` | `name`, `settings` {format, quality 1..100, scale, width, height, metadata…}. Not kept between `run` processes (see [gotchas.md](gotchas.md#process)) |

## Actions and automation

| Id | Key params |
|---|---|
| `actions.load` | `path` (.atn) → `{set, actions, steps, unsupported, warnings}` |
| `actions.play` | `action` name\|index; check `failed` in the result (the command itself still returns ok) |
| `file.automate.createDroplet` / `.runDroplet` | see [cli.md](cli.md#droplet) |
| `file.automate.batch` | `steps`, `input`, `includeSubfolders` (keeps the tree under `output`), `output`, `format`, `quality` 0..12 |
| `file.scripts.imageProcessor` | `input`, `includeSubfolders`, `output`, `format`, `quality` 0..12, `width`/`height` (fit, never enlarge), `convertToSrgb` |
| `actions.setColor` | `action`, `color` red\|orange\|…\|"" (Button Mode swatch) |
| `file.automate.contactSheetII`, `.photomerge`, `.mergeToHdrPro`, `.lensCorrection` | see signature |
