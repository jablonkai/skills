# Recipes

`S=<skill>/scripts`. All verified on effectcraft-cli 0.18.0.

## Lower third from a spec

`lt.json` (paths relative to the spec):

```json
{
  "project": "out/lower-third.ecproj",
  "comp": {"name": "Lower Third", "width": 1920, "height": 1080, "frameRate": 25, "duration": 5},
  "layers": [
    {"type": "text", "name": "Name", "text": "Jane Doe", "size": 64, "fill": "#ffffff",
     "justify": "left", "position": [160, 905],
     "keys": {"transform/position": [[0.2, [-800, 905]], [0.8, [160, 905]],
                                     [4.2, [160, 905]], [4.8, [-800, 905]]]}},
    {"type": "text", "name": "Title", "text": "Producer", "size": 36, "fill": "#dff6ff",
     "justify": "left", "position": [160, 960],
     "keys": {"transform/opacity": [[0.6, 0], [1.0, 100], [4.2, 100], [4.6, 0]]}},
    {"type": "shape", "name": "Bar", "kind": "rect", "size": [900, 150], "fill": "#00ADEF",
     "position": [610, 920],
     "keys": {"transform/position": [[0, [-460, 920]], [0.6, [610, 920]],
                                     [4.4, [610, 920]], [5.0, [-460, 920]]]},
     "effects": [{"effect": "Drop Shadow", "values": {"distance": 6, "softness": 12}}]}
  ],
  "essential": [{"layer": "Name", "path": "text/sourceText", "name": "Name"},
                {"layer": "Title", "path": "text/sourceText", "name": "Title"}],
  "template": "out/lower-third.ectemplate",
  "preview": {"time": 2.0, "out": "out/preview.png", "transparent": true},
  "render": [{"out": "out/lower-third.mov", "format": "prores", "prores": "4444", "channels": "rgba"}]
}
```

```sh
python3 $S/ec_build.py lt.json
python3 $S/ec_verify.py project out/lower-third.ecproj --comp "Lower Third" --size 1920x1080 \
  --duration 5 --layer Name:Text Title:Text Bar:Shape --animated Name:transform/position Bar:transform/position
python3 $S/ec_verify.py render out/lower-third.mov --codec prores --profile 4444 --alpha --duration 5 --size 1920x1080
```

Layout rules: shapes are centred on `position`; point text sits on its baseline at
`position`, centred unless `justify` says otherwise. Without a background layer the comp
is transparent in an RGBA render and black in RGB ones and previews without
`--transparent`.

Other layer types: `{"type": "solid", "color": "#202020", "name": "BG"}` (comp-sized),
`{"type": "footage", "path": "clip.mp4", "name": "Plate", "position": [960, 540]}`,
`{"type": "null", "name": "Ctrl"}`. Expressions: `"expressions": {"transform/rotation":
"time*90"}`; static values: `"props": {"transform/scale": [80, 80]}`; layer timing:
`"timing": {"start": 1.0}` (comp s).

## Template batch

```sh
python3 $S/ec_verify.py template out/lower-third.ectemplate     # control names, duration
cat > names.csv <<'EOF'
Name,Title,out
Anna Kovács,Director,anna
Ben Ito,Editor,ben
Cleo Diaz,Composer,cleo
EOF
python3 $S/ec_template.py out/lower-third.ectemplate names.csv renders/            # H.264 MP4s
python3 $S/ec_template.py out/lower-third.ectemplate names.csv stills/ --still 2.0  # PNG check frames
python3 $S/ec_verify.py render renders/*.mp4 --codec h264 --duration 5 --count 3
```

Look at the stills: each should show its own name. For alpha deliverables add
`--format prores --prores 4444 --channels rgba`. A colour control takes `"#00c080"`, a
number control a number, a Media Replacement control a footage path.

Raw CLI equivalent for one instance: `effectcraft-cli render --template T --values v.json
--out x.mp4 --format h264` with `v.json` = `{"Name": "Anna Kovács", "Title": "Director"}`.

## Open, edit, render

```sh
python3 $S/ec_verify.py hash promo.ecproj > before.json
effectcraft-cli info --project promo.ecproj --json             # comps, active comp's layers
effectcraft-cli props Main Title --flat --project promo.ecproj | grep -E 'sourceText|position'
effectcraft-cli get Main Title transform/position --project promo.ecproj --json   # keys[]
# first edit writes the copy; later ones save into it
effectcraft-cli set Main Title text/sourceText "Summer Sale" --project promo.ecproj --save-as promo-edit.ecproj
effectcraft-cli set Main Title transform/position '[960,500]' --time 1.0 --project promo-edit.ecproj --save
effectcraft-cli render-frame --project promo-edit.ecproj --comp Main --time 2.0 --out frame-2s.png
python3 $S/ec_verify.py project promo-edit.ecproj --comp Main --text "Title=Summer Sale" \
  --key 'Title:transform/position@1.0=[960,500]'
python3 $S/ec_verify.py hash promo.ecproj --compare before.json
```

`set --time T` on an existing key replaces its value and keeps its easing; at a new time
it adds a key. Its time is **layer** time. Read the layer's `start` first:

```sh
effectcraft-cli exec comp.info --params '{"comp":"Main"}' --project F --json   # layers[].start
```

When `start` isn't 0, key by comp time instead (the time the user reads off the timeline):

```sh
effectcraft-cli run --project promo-edit.ecproj --save \
  prop.set '{"layer":"Card","path":"transform/opacity","value":60,"time":2.5,"timeBase":"comp"}'
```

Then compare `get … --json` before and after: the same number of keys, only the one value
changed (`keys[].compTime` is comp time, `time` is layer time).

Several edits in one process: `effectcraft-cli run --project F --save-as G
layer.setText '{"layer":"Title","text":"Hi","size":90}' prop.addKey
'{"layer":"Title","path":"transform/opacity","time":0,"value":0}'` (a different comp:
`comp.open '{"comp":"Other"}'` first).

## Effects and a still

```sh
effectcraft-cli run --project in.ecproj --save-as fx.ecproj \
  effect.apply '{"effect":"Gaussian Blur","layers":["Logo"]}' \
  effect.apply '{"effect":"Glow","layers":["Logo"]}'
effectcraft-cli props Main Logo --flat --project fx.ecproj | grep effects/   # paths, in order
effectcraft-cli set Main Logo 'effects/#1/blurriness' 6 --project fx.ecproj --save
effectcraft-cli set Main Logo 'effects/#2/radius' 40 --project fx.ecproj --save
effectcraft-cli render-frame --project fx.ecproj --comp Main --time 1 --out fx.png
python3 $S/ec_verify.py project fx.ecproj --comp Main --effect "Logo=Gaussian Blur" "Logo=Glow" \
  --value 'Logo:effects/#1/blurriness=6'
```

Effect numbering is per layer, in stack order, and a layer that already has effects
starts later than `#1`. Effect names and parameter ids:
`effectcraft-cli --empty exec effect.list --params '{"filter":"glow"}' --json` (each with
`id`, `name`, `category`, `params[].id`); `props` after applying shows the paths.

## Image sequence, half-res review, GIF

```sh
mkdir -p seq && effectcraft-cli render --project F --comp Main --out 'seq/main_[#####].png' --format png
effectcraft-cli render --project F --comp Main --out review.mp4 --format h264 --resolution half
effectcraft-cli render --project F --comp Main --out loop.gif --format gif --start 0 --end 2
```
