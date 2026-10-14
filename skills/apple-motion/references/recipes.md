# Recipes

Paths assume `S=<skill>/scripts`. Each recipe ends in a check. Don't skip it.

## Lower third with two text fields on one plate, installed for FCP

```bash
python3 $S/motn-find.py --copy "Lower Thirds/Information Bar" --out "work/Race LT.moti"
python3 $S/motn-read.py "work/Race LT.moti" --table      # 2 fields, Bar Color published
python3 $S/motn-edit.py "work/Race LT.moti" --in-place \
  --text "#1=Runner Name" --text "#2=Club / Country" \
  --font "#1=AvenirNext-Bold" --font "#2=AvenirNext-Medium" --color "*=#FFFFFF" \
  --set "Bar Color=#1A1A1A" --opacity "background=1"
python3 $S/motn-render.py "work/Race LT.moti" --out work/render --at 2 \
  --expect "0.05,0.82=#1A1A1A"                                  # then look at the PNG
python3 $S/motn-install.py "work/Race LT.moti" --category "Race" --thumb "work/render/Race LT@2s.png"
```

The placeholder text ("Runner Name") is what the editor sees on dropping the title,
so pick text that says what goes there. The bar ships at 65 % opacity (`motn-read`
shows `opacity 0.65`), so over footage it is see-through, not the colour asked for.
`--opacity "background=1"` makes it solid; leave it if the user wants a translucent
bar. The bar has a fixed length: if the names are
long, `--set "Bar Length=1.3"` (a scale factor). Want the headline-only backplate
look instead? Seed with `Basic Text/Lower Third Text & Subhead`, and use
`--set "Backplate=1" --set "Backplate Color=…"`.

## Recolour and retype an existing template into a brand variant

```bash
python3 $S/motn-read.py base.moti --table      # find text layers, shapes, published colours, rigs
python3 $S/motn-edit.py base.moti --out "Brand LT.moti" \
  --font "*=Georgia-Bold" --color "*=#FFFFFF" \
  --set "Backplate=1" --set "Backplate Color=#00ADEF"
python3 $S/motn-render.py "Brand LT.moti" --out r --at 5 --expect "0.06,0.8=#00ADEF"
```

- Prefer the template's **published** colours (`--set`). They are what the
  designer meant to be changed, and the editor can still adjust them in FCP.
- If the colour you need isn't published, use `--color LAYER=…` for text or
  `--fill SHAPE=…` for shapes. Add `--publish "SHAPE:fill=Accent Color"` when the
  editor should be able to change it later.
- A log line *"also set 'ColorWay' option snapshot 3"* means a popup drives this
  colour. Your value became that option's value, and the other options still switch
  to Apple's colourways. Pass `--unrig` if the colour must never change with the popup,
  and `--unpublish ColorWay` if the popup no longer does anything useful.
- `--expect` coordinates are fractions of the frame (or pixels). Sample inside the
  shape, away from text and anti-aliased edges.

## Branded variant set (per event)

```bash
cat > events.csv <<'EOF'
name,set:Backplate Color,text:#2
EMU 6-Day,#00ADEF,6 napos verseny
EMU 24h,#C8102E,24 órás verseny
EMU 100 km,#2E7D32,100 km
EOF
python3 $S/motn-variants.py --csv events.csv --base "Brand LT.moti" --category "EMU Lower Thirds" \
  --out-dir variants --render
```

Check each reported `render.frames[].png`. Then relaunch FCP and run
`motn-fcp-browser.sh "EMU 6-Day" "EMU 24h" "EMU 100 km"`.

## A brand-colour generator (solid)

```bash
python3 $S/motn-find.py --copy "Solids/Custom" --kind generators --out "work/EMU Blue.motn"
python3 $S/motn-edit.py "work/EMU Blue.motn" --in-place --set "Color=#00ADEF"
python3 $S/motn-render.py "work/EMU Blue.motn" --out r --at 2 --expect "0.5,0.5=#00ADEF"
python3 $S/motn-install.py "work/EMU Blue.motn" --category "EMU"
```

## Use the new title in an FCP timeline (final-cut-pro skill)

```json
{"project": "Race recap", "library": "~/Movies/Race.fcpbundle",
 "spine": [{"clip": "finish.mov"}],
 "titles": [{"at": 2, "duration": 5, "text": ["Kovács Anna", "Versenyigazgató"],
             "template": {"name": "EMU 6-Day",
                          "uid": "~/Titles.localized/EMU Lower Thirds/EMU 6-Day/EMU 6-Day.moti"}}]}
```

Build with `fcpxml-build.py`, import with `fcp-import.py --library …`. Leave out
`font`/`size`/`color`; then the builder writes plain `<text>` and the template's
styling survives. FCP imports an unknown uid **without a warning**, so confirm with
`motn-install.py --in-library ~/Movies/Race.fcpbundle`: the template must be listed
there with `exists: true`.

## Remove a template

```bash
python3 $S/motn-install.py --uninstall "EMU Lower Thirds/EMU 24h"   # moved to the Trash
```
