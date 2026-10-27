# Recipes

`S=<skill>/scripts`. Every recipe ends with a read-back and a look at a render.

## Mobile screen from a spec

`login.json` (paths relative to the spec):

```json
{
  "styles": {"paint": {"Brand/Primary": "#2563EB"},
             "text": {"H1": {"fontFamily": "Inter", "fontStyle": "Bold", "fontSize": 28}}},
  "components": [
    {"name": "Button", "width": 342, "height": 48, "fillStyle": "Brand/Primary",
     "props": {"layout": "horizontal", "mainAlign": "center", "crossAlign": "center",
               "padding": 12, "cornerRadius": 8},
     "children": [{"type": "text", "name": "Label", "text": "Button",
                   "props": {"fill": "#FFFFFF", "fontSize": 16}}]}
  ],
  "frames": [
    {"name": "Login", "width": 390, "height": 844,
     "props": {"fill": "#FFFFFF", "layout": "vertical", "padding": 24, "gap": 16},
     "children": [
       {"type": "text", "name": "Title", "text": "Welcome back", "style": "H1"},
       {"name": "Email", "height": 48,
        "props": {"fill": "#F1F5F9", "cornerRadius": 8, "layout": "horizontal",
                  "crossAlign": "center", "padding": [0, 16, 0, 16]},
        "children": [{"type": "text", "name": "Placeholder", "text": "Email",
                      "props": {"fill": "#94A3B8", "fontSize": 16}}]},
       {"name": "Password", "height": 48,
        "props": {"fill": "#F1F5F9", "cornerRadius": 8, "layout": "horizontal",
                  "crossAlign": "center", "padding": [0, 16, 0, 16]},
        "children": [{"type": "text", "name": "Placeholder", "text": "Password",
                      "props": {"fill": "#94A3B8", "fontSize": 16}}]},
       {"instance": "Button", "name": "Sign in", "text": {"Label": "Sign in"}}
     ]}
  ],
  "save": "out/login.figcraft",
  "exports": [{"node": "Login", "path": "out/login@2x.png", "scale": 2},
              {"node": "Login", "path": "out/login.svg"}],
  "preview": "out/preview.png"
}
```

```sh
python3 $S/fc_build.py login.json
python3 $S/fc_verify.py doc out/login.figcraft --frame Login=390x844 --text Title="Welcome back" \
  --names Email Password --component Button --instance Button@Login --auto-layout Login --style H1
python3 $S/fc_verify.py files out/login@2x.png --px 780x1688
python3 $S/fc_verify.py files out/login.svg --svg
```

Then view `out/preview.png`. Components are placed in a row to the right of the frames,
so they don't overlap the screens. Email, Password and the button instance have no
`width`, so inside the vertical Login frame they get `sizingH: "fill"` and stretch when the
screen is resized (`fc_verify.py doc … --fill Login/Email`); give a child a `width` only
when it must stay fixed.

## Screens only: PNG set or one PDF

```sh
python3 $S/fc_export.py checkout.fig out/png --scale 2 --suffix @2x       # one PNG per screen
python3 $S/fc_export.py checkout.fig out/screens.pdf --one-pdf --cmyk     # one page per screen
python3 $S/fc_verify.py files out/screens.pdf --pdf-pages 3
```

Main components on the page are skipped (listed under `skipped`); `--frames A B` picks
screens, `--page NAME` another page. The source file is never saved.

## Edit a .fig and export every frame

```sh
figcraft-cli info app.fig --json          # frames + notes (import losses) + missingFonts
python3 $S/fc_verify.py hash . > /tmp/manifest.json
python3 $S/fc_session.py - <<'EOF'
[{"open": "app.fig"},
 {"find": {"name": "Headline"}},
 {"cmd": "node.set", "params": {"ids": ["@name:Home/Headline"], "characters": "Welcome back, Ada"}},
 {"save": "out/app-edited.figcraft"}]
EOF
python3 $S/fc_export.py out/app-edited.figcraft out/frames --format png
python3 $S/fc_verify.py doc out/app-edited.figcraft --text Home/Headline="Welcome back, Ada" Settings/Headline=Settings
python3 $S/fc_verify.py files out/frames --ext png --count 3 --px 390x844
```

To change one instance's label among several identical ones (a "Continue" button on
every screen), scope the ref to the screen: `"@name:Payment/Label"`. `edit.findReplace`
would change every copy. Report `notes` — "nothing was dropped" when empty.

## Print PDF of one node

```sh
figcraft-cli export card.figcraft -o out/business-card.pdf --node "Business Card" \
  --bleed 3mm --crop-marks            # add --cmyk for a CMYK print file
python3 $S/fc_verify.py files out/business-card.pdf --pdf-pages 1 --trim 255x156 --bleed 3mm --marks
```

The TrimBox is the layer's size in pt (1 px = 1 pt). Check `info` first that the name is
unique; otherwise pass the id.

## Figma REST JSON → FigCraft

```sh
figcraft-cli info marketing.json --json        # notes: e.g. WIDGET layers skipped
figcraft-cli convert marketing.json out/marketing.figcraft
mkdir -p out/svg && figcraft-cli export out/marketing.figcraft -o out/svg --format svg
python3 $S/fc_verify.py files out/svg --ext svg --count 3 --svg
```

Variables are read from `<name>.variables.json` next to the file when present.

## Design-system kit: variant set, styles, several screens

In an `fc_build.py` spec, a component with `variants` becomes a component set; instances
pick a variant and override the label:

```json
{"components": [{"name": "Button", "width": 200, "height": 48, "variants": [
   {"name": "Style=Primary", "fillStyle": "Brand/Primary",
    "props": {"layout": "horizontal", "mainAlign": "center", "crossAlign": "center", "cornerRadius": 8},
    "children": [{"type": "text", "name": "Label", "text": "Button", "props": {"fill": "#FFFFFF", "fontSize": 16}}]},
   {"name": "Style=Secondary",
    "props": {"fill": "#FFFFFF", "stroke": "#2563EB", "layout": "horizontal", "mainAlign": "center",
              "crossAlign": "center", "cornerRadius": 8},
    "children": [{"type": "text", "name": "Label", "text": "Button", "props": {"fill": "#2563EB", "fontSize": 16}}]}]}],
 "frames": [{"name": "Welcome", "width": 390, "height": 844,
   "props": {"fill": "#FFFFFF", "layout": "vertical", "padding": 24, "gap": 16},
   "children": [
     {"type": "text", "name": "Heading", "text": "Welcome", "style": "Heading"},
     {"type": "text", "name": "Body", "text": "One line of intro.", "style": "Body", "fillStyle": "Text/Muted"},
     {"instance": "Button", "name": "Get started", "text": {"Label": "Get started"}},
     {"instance": "Button", "name": "Sign in", "variant": {"Style": "Secondary"}, "text": {"Label": "I have an account"}}]}]}
```

Then `fc_export.py kit.figcraft out/screens --scale 2` and
`fc_export.py kit.figcraft out/kit.pdf --one-pdf` (screens only, no component pages).

## Styles and a variant set in a session

```json
[{"cmd": "style.create", "params": {"type": "paint", "name": "Brand/Surface", "value": "#F8FAFC"}},
 {"batch": [
   {"command": "node.create", "params": {"type": "component", "name": "State=Default", "width": 160, "height": 40}},
   {"command": "node.create", "params": {"type": "component", "name": "State=Pressed", "x": 200, "width": 160, "height": 40}},
   {"command": "component.combineVariants", "params": {"ids": [{"$step": 0}, {"$step": 1}]}}]},
 {"save": "out/system.figcraft"}]
```
