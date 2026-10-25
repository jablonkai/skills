---
name: apple-motion
description: 'Author, edit and install Apple Motion templates for Final Cut Pro as ozml XML, without opening Motion: Titles (.moti), Generators (.motn), Effects (.moef) and Transitions (.motr). Change text, PostScript fonts, sizes, text and shape colours; set and publish the parameters FCP shows in its inspector; turn one base template into a branded variant set from JSON or CSV; install into ~/Movies/Motion Templates with thumbnails and get the FCPXML uid; render a headless preview through Compressor with pixel colour checks. Use for "make a lower third template for Final Cut", "rebrand this Motion title in our colours and font", "title variants for each event from a CSV", "publish the backplate colour", "install this .moti so FCP sees it", "what parameters does this template publish". Not for building or editing FCP timelines (final-cut-pro), transcoding (compressor/handbrake), procedural motion graphics in Cavalry (cavalry), Resolve/Fusion titles (davinci-resolve) or 3D (blender).'
summary: "author and install Apple Motion templates for Final Cut Pro as ozml XML — lower-third titles, generators and effects with published parameters, branded variant sets, headless renders through Compressor and use in FCPXML timelines"
category: motion-design
compatibility: "Built for Motion 6.4, Final Cut Pro 12.4 and Compressor 5.4 on macOS 27."
risk: low
tags:
    - apple-motion
    - final-cut-pro
    - motion-templates
    - titles
    - lower-thirds
    - branding
metadata:
  version: "1.0.1"
---

# Apple Motion templates

Motion has **no usable scripting API**: `NSAppleScriptEnabled` is false and there is no
dictionary. What it does have is a text file format: every template is **ozml XML**
(`<!DOCTYPE ozxmlscene>`). This skill edits that XML, installs the result where Final
Cut Pro looks, and checks it with a headless **Compressor** render. The Motion window
never opens. Verified against **Motion 6.4**, **Final Cut Pro 12.4** and **Compressor**
on macOS 27.

| Script | Does |
|---|---|
| `python3 scripts/motn-find.py [RE] [--kind titles] [--stock\|--user]` | list stock and installed templates (user ones with their uid) |
| `python3 scripts/motn-find.py --copy "Cat/Name" --out DIR/New.moti` | copy a template out as a seed to edit |
| `python3 scripts/motn-read.py FILE [--table]` | text fields in FCP order, fonts, colours, shapes, widgets, published params, rigs, missing fonts |
| `python3 scripts/motn-edit.py IN --out OUT --text/--font/--size/--color/--fill/--set/--publish/--unpublish …` | edit → new file, re-parsed and font-checked |
| `python3 scripts/motn-variants.py SPEC.json` / `--csv ROWS --base B --category C` | one base → N branded variants, optionally rendered and installed |
| `python3 scripts/motn-install.py FILE --category C [--name N] [--thumb PNG]` | install into Motion Templates; prints the FCPXML uid. `--list`, `--uninstall Cat/Name`, `--in-library LIB` (templates an FCP library resolved) |
| `python3 scripts/motn-render.py FILE --out DIR [--at 2,5] [--expect "X,Y=#hex"]` | Compressor render → movie + PNG frames, blank and pixel-colour checks |
| `bash scripts/motn-fcp-browser.sh "Name" …` | does FCP's Titles/Generators browser list them? (FCP running, Accessibility) |

All Python is standard library (system `python3` 3.9+). Rendering needs Compressor and
`ffmpeg`/`ffprobe` (`brew install ffmpeg`). Every script prints JSON and exits non-zero
on failure, so read the JSON rather than assuming success.

## Workflow

1. **Start from a seed, never from scratch.** A Motion document references internal
   factory UUIDs that can't be guessed, so copy a template that already has the
   layout you need (`motn-find.py --copy "Category/Name" --out work/Brand.moti`).
   Pick by what the plate must cover, because moving a plate fights its rig:

   | Seed | Layout |
   |---|---|
   | `Lower Thirds/Information Bar` | **one bar behind both lines** (65 % opacity: `--opacity background=1` for solid); publishes Bar Color, Bar Length, Line 1/2 Font/Size/Color |
   | `Basic Text/Lower Third Text & Subhead` | backplate sized to the **headline only**, subhead below it; Backplate on/off, colour, roundness |
   | `Basic Text/Lower Third Text` | one text field (+ optional backplate) |
   | `Lower Thirds/Soft Bar` | soft gradient bar behind both lines |
   | `Solids/Custom` (generator) | one colour; `Elements/Shapes` for basic shapes |

   Use the user's own template when they have one; it is the best seed.
   `motn-find.py "lower third" --kind titles` lists more, and render a candidate to
   see its layout before committing to it.
2. **Read it**: `motn-read.py work/Brand.moti --table`. Note the text-field order (FCP
   fills `<text>` lines in this order), the layer names, the published parameters and
   which channels a **rig widget** drives.
3. **Edit** into a new file:
   ```bash
   python3 scripts/motn-edit.py work/Brand.moti --out work/Brand-EMU.moti \
     --text "#1=Kovács Anna" --text "#2=Versenyigazgató" \
     --font "*=Georgia-Bold" --color "*=#FFFFFF" \
     --set "Bar Color=#00ADEF" \
     --publish "#1:font=Name Font"
   ```
   LAYER is a name, `#N` (Nth text field) or `*`. `--opacity LAYER=0..1` sets a layer's opacity. `--set` changes any **published**
   parameter by its FCP name: a colour, font, text, checkbox `0/1`, popup index or
   slider value. `--fonts georgia` looks up PostScript names. A font that isn't
   installed is an error, because Motion would silently fall back to Helvetica.
4. **Render and look**: `motn-render.py work/Brand-EMU.moti --out render --at 5
   --expect "0.06,0.8=#00ADEF"`, then **view the PNG**. Titles render over FCP's
   grey drop-zone placeholder, which is normal. `--expect` converts the template
   colour the way the render encodes it (sRGB in the file, gamma-1.961 Rec. 709 out).
5. **Install**: `motn-install.py work/Brand-EMU.moti --category "EMU" --thumb
   render/Brand-EMU@5s.png`. Use the printed `uid` in the timeline.
6. **In Final Cut Pro**: FCP scans templates at launch, so **relaunch FCP** (ask
   first if it's open with the user's work) and confirm with
   `motn-fcp-browser.sh "Brand-EMU"`. For a timeline, pass the template to the
   `final-cut-pro` skill's builder as
   `"template": {"name": "Brand-EMU", "uid": "~/Titles.localized/EMU/Brand-EMU/Brand-EMU.moti"}`.
   **Leave out `font`/`size`/`color`**, because any FCPXML text style replaces the
   template's own styling. FCP imports a wrong uid without a warning, so after
   `fcp-import.py` run `motn-install.py --in-library LIB`. It lists the user
   templates the library actually resolved.

## Variant sets

```json
{"base": "Brand.moti", "category": "EMU Lower Thirds", "out_dir": "variants",
 "common": {"font": {"*": "Georgia-Bold"}, "set": {"Backplate": "1"}},
 "variants": [
   {"name": "EMU 6-Day", "set": {"Backplate Color": "#00ADEF"}},
   {"name": "EMU 24h",   "set": {"Backplate Color": "#C8102E"}, "text": {"#2": "24 órás verseny"}}]}
```

`motn-variants.py spec.json --render` writes `variants/<name>.moti`, renders each one
(the frame becomes the browser thumbnail) and installs it. Use `--no-install` to stop
short of that. The CSV form has a `name` column plus `OP:TARGET` columns such as
`set:Backplate Color`, `text:#1` or `font:*`. One template per variant is what FCP
needs: an editor picks "EMU 24h" from the browser and gets its colours by default.

## Rules that keep templates loading

- Edit only through the scripts or ElementTree, never with string replacement. Keep
  the `<!DOCTYPE ozxmlscene>` header and the extension, since the extension decides
  the template type.
- `--text` also rewrites the `styleRun` length (UTF-16 units). Otherwise extra
  characters lose their style or the text gets cut off.
- A **rigged** channel (popup "ColorWay", checkbox "Backplate"…) also stores one value
  per widget option, and FCP applies that value when the editor picks the option.
  `motn-edit` writes your value into the snapshot of the widget's current option too
  (the log says "also set 'ColorWay' option snapshot …"). The template then shows
  your colour by default, and the other options keep Apple's colourways. `--unrig`
  removes the rig for that channel instead, after which the widget no longer affects it.
- Colours are sRGB 0–1 in the file (`#00ADEF` = 0, 0.678, 0.937). Stock templates
  can hold values outside 0–1 (wide gamut); `motn-read` clamps those when it shows hex.
- Install layout is `~/Movies/Motion Templates.localized/Titles.localized/<Category>/<Name>/<Name>.moti`.
  A template placed directly under `Titles.localized` doesn't show in FCP.
- Copying a stock FCP template into your own templates is fine (FCP's "Open a copy
  in Motion" does the same), but don't redistribute Apple's templates.

## When the user wants it opened in Motion

`open -a Motion FILE` opens the file for hand-tuning (keyframes, behaviours, new
layers), which this skill doesn't author. After the user saves, run `motn-read.py`
again, because Motion may renumber ids.

## References

- [references/ozml.md](references/ozml.md): file anatomy, object and parameter ids,
  channel paths, publishSettings, rigs, colour encoding, text styles
- [references/recipes.md](references/recipes.md): lower third, rebrand, variant set,
  generator colour, FCPXML use, uninstall
- [references/gotchas.md](references/gotchas.md): what goes wrong, and how it shows
