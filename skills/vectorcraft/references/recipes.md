# Recipes

`S=<skill>/scripts`. All of them were verified on vectorcraft-cli 0.17.0.

## Logo sheet

Three artboards, each with a mark and a wordmark. It saves `.vectorcraft`, writes a PNG
per artboard at native size, a multi-page PDF and previews. Coordinates are relative to
each artboard. Point text `y` is the baseline, and `justify: "center"` centres it on `x`.

```json
{
  "units": "Pixels",
  "artboards": [
    {"name": "Logo 1024", "width": 1024, "height": 1024},
    {"name": "Logo 512",  "width": 512,  "height": 512},
    {"name": "Favicon 64", "width": 64,  "height": 64}
  ],
  "swatches": [{"name": "Brand", "color": "#1b998b", "global": true}],
  "layers": ["Mark", "Wordmark"],
  "objects": [
    {"artboard": 0, "layer": "Mark", "name": "Mark 1024", "shape": "ellipse",
     "x": 262, "y": 140, "width": 500, "height": 500, "fill": {"swatch": "Brand"}},
    {"artboard": 0, "layer": "Wordmark", "name": "Wordmark 1024", "text": "NOVA",
     "x": 512, "y": 860, "size": 160, "font": "Helvetica", "style": "Bold",
     "color": "#222222", "justify": "center"},
    {"artboard": 1, "layer": "Mark", "shape": "ellipse",
     "x": 131, "y": 70, "width": 250, "height": 250, "fill": {"swatch": "Brand"}},
    {"artboard": 1, "layer": "Wordmark", "text": "NOVA", "x": 256, "y": 430, "size": 80,
     "font": "Helvetica", "style": "Bold", "color": "#222222", "justify": "center"},
    {"artboard": 2, "layer": "Mark", "shape": "ellipse",
     "x": 6, "y": 6, "width": 52, "height": 52, "fill": {"swatch": "Brand"}}
  ],
  "save": "out/logo.vectorcraft",
  "exports": [
    {"path": "out/png/logo-{index}.png", "artboards": "each"},
    {"path": "out/logo-sheet.pdf"}
  ],
  "preview": "out/preview/logo"
}
```

```sh
python3 $S/vc_build.py spec.json
python3 $S/vc_verify.py doc out/logo.vectorcraft --artboards 3 --size 1024x1024 512x512 64x64 --min-kind Type=2 --fonts-ok
python3 $S/vc_verify.py files out/png --ext png --count 3 --px 1024x1024 512x512 64x64
python3 $S/vc_verify.py files out --ext pdf --pdf-pages 3
```

Then view `out/preview/logo-1.png`… with the image viewer.

- For @2x, add `"scale": 2` to the export.
- For SVGs with outlined text, use `{"path": "out/svg/logo-{index}.svg", "artboards": "each", "outlineText": true}`.
- A tiny favicon reads better as the mark alone; leave text off artboards under ~128 px.
- For a reusable mark, give the first one `"makeSymbol": "Mark"` and place it elsewhere
  with `{"symbol": "Mark", "artboard": 1, "x": …, "y": …}` (registration is the
  centre).

## Folder conversion

```sh
python3 $S/vc_verify.py hash in/ > /tmp/in-manifest.json
python3 $S/vc_batch.py in/ out/svg --to svg --ext ai,eps,pdf --outline-text --decimals 2
python3 $S/vc_verify.py files out/svg --ext svg --count 5 --no-svg-text --max-decimals 2
python3 $S/vc_verify.py hash in/ --compare /tmp/in-manifest.json
```

- `--to svg,pdf` writes both.
- A multi-artboard input gives the first artboard as SVG. Add `--each-artboard` for
  `<stem>-<n>.svg`.
- Report every `importWarnings` entry from the batch output to the user. It means that
  file came in incomplete (for example an EPS read from its preview).

## Edit text and recolour

`steps.json`. The root must contain the input and the outputs:

```json
[
  {"open": "/abs/in/poster.svg"},
  {"find": {"kind": "Type"}},
  {"cmd": "text.setText", "params": {"id": "@name:Headline", "text": "Autumn Open"}},
  {"cmd": "select.all"},
  {"cmd": "recolor.colors"},
  {"cmd": "recolor.apply", "params": {"map": {"#e4572e": "#1b998b"}}},
  {"cmd": "select.none"},
  {"export": {"path": "/abs/out/poster.svg"}},
  {"export": {"path": "/abs/out/poster@2x.png", "scale": 2}}
]
```

```sh
python3 $S/vc_session.py steps.json --read-root /abs/in --write-root /abs/out
python3 $S/vc_verify.py doc out/poster.svg --text Headline=“Autumn Open” --color '#1b998b' --no-color '#e4572e'
```

- Run a first session with only `open` and `find`/`inspect` to see the names, then
  write the edits.
- `@name:` matches the Layers panel name: the SVG `id`/`data-name`, or the content of
  untitled text.
- The colour has a name ("the brand orange", "swatch Brand"):
  - When the document has a **global swatch** of it, `swatch.edit {"name": "Brand", "color": "#1b998b"}`
    recolours every linked object and keeps the swatch.
  - Otherwise, map the hex with `recolor.apply`. `recolor.colors` shows the hex values
    in use.
- To recolour only some objects, select them first (`select.set {"ids": […]}`) and
  then run `recolor.apply`.
- SVG round-trips keep layer `<g>` ids, text as `<text>` (unless `outlineText`), and
  untouched colours.

## CSV variants

A template with a `Title` text object and a `Badge` group, and `people.csv`:

```csv
slug,title,badge
ada,Ada Lovelace,yes
alan,Alan Turing,no
```

```sh
python3 $S/vc_variants.py tpl.vectorcraft people.csv out/badges \
  --bind text:title=@name:Title visibility:badge=@name:Badge \
  --name-col slug --ext png --scale 2 --save-template out/tpl-with-data.vectorcraft
```

- It writes `out/badges/ada.png` and `alan.png`.
- Variables take their column by name. Use `--map COL=VAR` when they differ.
- `--pattern "{row}-{title}"` builds names from columns (`{row}` is the `--name-col` value).
- A `selectWarning` entry means that row changed nothing: no object is bound to a
  variable the row fills. Check the `--bind` refs.
- Check a couple of the outputs visually: an `overflow` entry means the text no longer
  fits its frame.
- An `image` variable takes a file path per row. The CSV column holds the path, which
  must be inside the read root.
- To fill the variables manually inside a session, use
  `dataset.import {"csv": "name,title\nr1,Ada\n"}`, then `dataset.select {"name": "r1"}`
  and `export`.

## One-shot `run`

```sh
vectorcraft-cli run --in in.svg --cmd select.all --cmd type.createOutlines --export out.pdf
vectorcraft-cli run --cmd file.new --params '{"width":512,"height":512,"units":"Pixels"}' \
  --cmd shape.star --params '{"cx":256,"cy":256,"radius1":200,"radius2":90,"points":5}' \
  --cmd paint.setFill --params '{"color":"#f4a259"}' --cmd paint.setStroke --params '{"none":true}' \
  --export star.svg --export star.png
```

When a later step needs an earlier step's id, put the steps in a JSONL file. `"$N.id"`
refers to step N's result (0-based):

```sh
cat > steps.jsonl <<'JSONL'
{"command":"file.new","params":{"width":512,"height":512,"units":"Pixels"}}
{"command":"shape.ellipse","params":{"x":56,"y":56,"width":400,"height":400}}
{"command":"paint.setStroke","params":{"none":true}}
{"command":"object.setProps","params":{"id":"$1.id","name":"Mark"}}
JSONL
vectorcraft-cli run --commands steps.jsonl --export mark.svg
```
