# Recipes

Recipes are verified end to end on 0.9.0, and again on 0.16.0 (composition, template
and comps, data sets, session measuring, smart-object swap, droplet, live app), except
the `.atn` playback and the `pixelReplacement` variable, which follow the registry docs. `S` is this skill's `scripts/` folder, so
call scripts as `python3 $S/pc_….py` (zsh doesn't word-split a `$VAR` that holds a
command and its arguments). Use absolute paths in every JSON param.

## Contents
- [Layered composition from a spec](#layered-composition-from-a-spec)
- [Folder batch: resize, sharpen, convert](#folder-batch-resize-sharpen-convert)
- [Template edit and layer comps](#template-edit-and-layer-comps)
- [Move a layer to an anchored position](#move-a-layer-to-an-anchored-position)
- [Replace a smart-object image](#replace-a-smart-object-image)
- [Variants from a CSV (data sets)](#variants-from-a-csv-data-sets)
- [Export layers as files](#export-layers-as-files)
- [Photoshop actions (.atn) and droplets](#photoshop-actions-atn-and-droplets)
- [Adjustments and filters on one file](#adjustments-and-filters-on-one-file)
- [Watching it live in the app](#watching-it-live-in-the-app)

## Layered composition from a spec

```json
{
  "canvas": {"width": 1080, "height": 1080, "background": "white"},
  "layers": [
    {"image": "assets/beach.jpg", "fit": "cover", "name": "Photo"},
    {"fill": "#000000", "rect": [0, 760, 1080, 320], "opacity": 0.35, "name": "Shade"},
    {"image": "assets/logo.png", "width": 160, "anchor": "top-right", "margin": 40, "name": "Logo"},
    {"text": "Summer Sale", "size": 110, "color": "#ffffff", "font": "Inter",
     "anchor": "bottom-left", "margin": 80, "name": "Headline",
     "style": {"dropShadow": {"distance": 6, "size": 12, "opacity": 60}}}
  ],
  "save": ["out/post.psd", "out/post.png"],
  "preview": "out/preview.png"
}
```

```sh
python3 $S/pc_compose.py spec.json      # prints layers with ids and [x, y, w, h] bounds
python3 $S/pc_verify.py doc out/post.psd --size 1080x1080 --text "Headline=Summer Sale" \
  --effect "Headline=Drop Shadow" --order Headline,Logo,Photo
python3 $S/pc_verify.py files out --size 1080x1080
```

Then look at `out/preview.png`, which is the check for overlaps, contrast and cropping
that a read-back can't catch. Layers are listed **bottom to top**. Anything the spec keys
don't cover goes in as a raw step `{"cmd": "<id>", "params": {…}}`, which applies to the
active layer (the one created last).

## Folder batch: resize, sharpen, convert

```sh
python3 $S/pc_verify.py hash ~/Photos/in > /tmp/in.manifest.json          # snapshot originals
cat > /tmp/actions.json <<'EOF'
[["file.automate.fitImage", {"width": 2048, "height": 2048}],
 ["filter.sharpen.unsharpMask", {"amount": 80, "radius": 1, "threshold": 2}]]
EOF
photocraft-cli batch --actions /tmp/actions.json --in ~/Photos/in --out ~/Photos/web \
  --format webp --quality 80
python3 $S/pc_verify.py files ~/Photos/web --count 5 --ext webp --long-edge 2048 --webp lossy
python3 $S/pc_verify.py hash ~/Photos/in --compare /tmp/in.manifest.json  # originals untouched
```

`fitImage` with a square box sets the **long edge** for both orientations, keeps the
aspect ratio, and enlarges smaller images (add `"dontEnlarge": true` to skip that). For an
exact size use `image.imageSize`; for a crop-to-fill use `image.crop` with
`targetWidth`/`targetHeight`. The output folder must differ from the input.

The `batch` subcommand reads only the top level of `--in`. For a folder tree, call the
engine's batch command (0.10.0+); each result keeps its subfolder under `output`, and the
reply lists every written file:

```sh
photocraft-cli run --new '{"width":1,"height":1}' --cmd file.automate.batch --params '{
  "steps": [["file.automate.fitImage", {"width": 2048, "height": 2048}]],
  "input": "/abs/in", "includeSubfolders": true, "output": "/abs/web",
  "format": "webp", "quality": 9}'
```

Its `quality` is the engine's **0..12** scale. `pc_verify.py files` checks one folder, so
run it per subfolder, or compare the reply's `files` list with the inputs.

## Template edit and layer comps

Change text, hide a layer, and export every comp. Comps re-apply their recorded
visibility (see [gotchas.md](gotchas.md#layer-comps-override-visibility-edits)), so fold
the hide into each comp:

```sh
python3 $S/pc_inspect.py layers promo.psd          # names, ids, comps (Day, Night)
python3 $S/pc_inspect.py ids promo.psd Title Badge # {"Title": 6, "Badge": 8}
mkdir -p out/comps
photocraft-cli run promo.psd \
  --cmd type.edit        --params '{"layer":6,"text":"Summer Collection"}' \
  --cmd layer.setProps   --params '{"layer":8,"visible":false}' \
  --cmd layerComp.apply  --params '{"comp":"Day"}' \
  --cmd layer.setProps   --params '{"layer":8,"visible":false}' \
  --cmd layerComp.update --params '{"comp":"Day","what":"visibility"}' \
  --cmd layerComp.apply  --params '{"comp":"Night"}' \
  --cmd layer.setProps   --params '{"layer":8,"visible":false}' \
  --cmd layerComp.update --params '{"comp":"Night","what":"visibility"}' \
  --cmd file.export.layerCompsToFiles --params '{"dir":"/abs/out/comps","format":"png"}' \
  --out out/promo-edited.psd
python3 $S/pc_verify.py doc out/promo-edited.psd --text "Title=Summer Collection" --hidden Badge
python3 $S/pc_verify.py files out/comps --count 2 --size 1200x800
```

Then look at one exported comp to confirm the layer stays hidden. Leave the source PSD
unchanged unless the user asked to save over it. The files come out as
`<prefix>_0000_<comp>.png`, and `prefix` defaults to the document name.

In `serve`, which has no comp-export method, do the same per comp:
`{"cmd":"layerComp.apply","params":{"comp":"Day"}}` then
`{"method":"doc.save","params":{"path":"/abs/out/Day.png"}}`.

## Move a layer to an anchored position

Measure, compute the delta, translate, and read back:

```json
[{"method":"doc.open","params":{"path":"/abs/promo.psd"}},
 {"cmd":"select.loadSelection","params":{"channel":"mask","layer":"@layer:Badge"}},
 {"method":"doc.inspect"}]
```

Text, pixel, shape and Smart Object layers report `bounds` `[x, y, w, h]` in `doc.inspect`.
Fill layers report `null`, so load the mask as a selection and use `selectionBounds`, as
above. For bottom-right with a 40 px margin: `dx = W - 40 - (x + w)`,
`dy = H - 40 - (y + h)`. Move every layer that belongs to the element by the same delta
(a badge's shape and its text), with `layer.translate {"layer": id, "dx", "dy"}`, and
save. The measuring selection only lives in that session. Run `select.deselect` there,
not in a later `photocraft-cli run`, where it fails with "no selection". For alignment within a selection or the canvas,
`layer.align.*` with `"to": "canvas"` works on the selected layers.

## Replace a smart-object image

```sh
photocraft-cli run mockup.psd \
  --cmd layer.smartObjects.replaceContents --params '{"layer":7,"path":"/abs/new.jpg"}' \
  --cmd edit.transform --params '{"layer":7,"quad":[[880,40],[1040,40],[1040,200],[880,200]]}' \
  --out out/mockup-new.psd
```

The replacement keeps the old *scale*. The quad (the old `[x, y, w, h]` box from `info`,
as its corners clockwise from top-left) refits it. If the aspect ratio differs, shrink
the quad to the new aspect inside the old box so the image isn't distorted.

In `serve` (`pc_session.py`), `layer.smartObjects.replaceContents` is disabled; use the
scoped method, which has the same scale behaviour, then the same `edit.transform`:

```json
[{"method":"doc.open","params":{"path":"/abs/mockup.psd"}},
 {"method":"doc.replaceSmartObject","params":{"path":"/abs/new.jpg","layer":"@layer:Photo"}},
 {"cmd":"edit.transform","params":{"layer":"@layer:Photo","quad":[[880,40],[1040,40],[1040,200],[880,200]]}},
 {"method":"doc.save","params":{"path":"/abs/out/mockup-new.psd"}}]
```

Without `layer` it acts on the active layer and fails unless that is a Smart Object.

## Variants from a CSV (data sets)

```csv
dataSet,headline,showBadge
spring,Spring Collection,true
summer,Summer Sale,false
```

```sh
python3 $S/pc_inspect.py ids promo.psd Title Badge      # numeric ids: define refuses names
mkdir -p out/variants
photocraft-cli run promo.psd \
  --cmd image.variables.define --params '{"defs":[{"name":"headline","layer":6,"type":"textReplacement"},{"name":"showBadge","layer":8,"type":"visibility"}]}' \
  --cmd file.import.variableDataSets --params '{"path":"/abs/variants.csv"}' \
  --cmd file.export.dataSetsAsFiles --params '{"dir":"/abs/out/variants","format":"png","naming":"{name}"}'
```

This writes `spring.png` and `summer.png`. The first column must be headed `dataSet` to
name the sets. For an image swap, define a `pixelReplacement` variable on a Smart Object
or pixel layer (`method` fit|fill|asIs|conform). Its CSV values should be image paths:
check with one data set before exporting all of them. Add
`--out template-with-vars.psd` to keep the definitions.

## Export layers as files

```sh
mkdir -p out/layers
photocraft-cli run design.psd --cmd file.export.layersToFiles \
  --params '{"dir":"/abs/out/layers","format":"png","visibleOnly":true}'
```

In `serve`: `{"method":"doc.exportLayers","params":{"dir":"/abs/out/layers"}}`.
For one layer: `layer.exportAs {"layer":id,"path":"/abs/logo.png"}`.

## Photoshop actions (.atn) and droplets

```sh
# What's in the set, and what won't play (no --out: nothing is written)
photocraft-cli run --new '{"width":8,"height":8}' --cmd actions.load --params '{"path":"/abs/Vintage.atn"}'
# Play one action of the set over a folder
photocraft-cli batch --actions /abs/Vintage.atn --action "Faded Film" --in raw --out graded --format jpg --quality 90
# Run an existing droplet
photocraft-cli droplet /abs/web.pcdroplet raw/ --out out/web
```

Report the `unsupported` steps from `actions.load` to the user before running the batch;
they are skipped. To make a droplet, see [cli.md](cli.md#droplet).

## Adjustments and filters on one file

Destructive edit, flattened output:

```sh
photocraft-cli run in.jpg --cmd image.autoTone \
  --cmd image.adjustments.hueSaturation --params '{"saturation":15}' \
  --cmd filter.sharpen.smartSharpen --params '{"amount":80,"radius":1}' \
  --out out/in-graded.jpg --quality 92
```

Non-destructive edit: use `layer.newAdjustmentLayer.<kind>` and save `.psd` or
`.pcraft`. To check visually, render a preview through `serve`:

```json
[{"method":"doc.open","params":{"path":"/abs/out/in-graded.psd"}},
 {"method":"doc.render","params":{"path":"/abs/out/preview.png","maxSide":1024}}]
```

## Watching it live in the app

Only when the user wants to see the edits happen in PhotoCraft:

```sh
python3 $S/pc_live.py start --root /abs/project        # opens the app with a control port
python3 $S/pc_live.py call app.open '{"path":"design.psd"}'   # relative to the root
python3 $S/pc_live.py steps steps.json                  # same step format as pc_session.py
python3 $S/pc_live.py call app.save '{"path":"out/design-edited.psd"}'
python3 $S/pc_live.py stop                              # app.quit: save first
```

`ui.screenshot {"path":"shot.png"}` captures the window into the write root. The
security posture is in [control-protocol.md](control-protocol.md#security-posture).
