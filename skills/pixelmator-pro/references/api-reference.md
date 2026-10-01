# Pixelmator Pro AppleScript reference (3.8)

A condensed version of the app's dictionary. To see the full text, dump it yourself:
`sdef "/Applications/Pixelmator Pro.app" > pxm.sdef`. The dictionary's `<documentation>`
blocks contain worked examples. Everything below lives inside
`tell application "Pixelmator Pro"`.

## Contents
- [Documents](#documents)
- [Layers](#layers)
- [Text](#text)
- [Shapes and styles](#shapes-and-styles)
- [Colour adjustments](#colour-adjustments)
- [Effects](#effects)
- [Commands by area](#commands-by-area)
- [Export](#export)
- [Enumerations](#enumerations)

## Documents

```applescript
set d to make new document with properties {width:1080, height:1350}   -- also resolution
set d to open ("/abs/path/photo.jpg" as POSIX file)  -- coerce locally (see gotchas)
set d to front document
close d saving no
save d in ("/abs/out.pxd" as POSIX file)            -- native .pxd, keeps layers
```

`document` properties: `width`, `height` and `resolution` (reals, read-only; change them
with `resize image` / `resize canvas`), `bits per channel` (8/16/32), `color profile`
(ro), `current layer`, `selected layers`, `selection bounds` (ro), `document info`
(title, author, copyright and other metadata). Elements: `layers` (top-first),
`image layers`, `text layers`, `shape layers`, `group layers`, `color adjustments
layers`, `effects layers`, `video layers`.

## Layers

All layer classes inherit from `layer`:

| property | type | notes |
|---|---|---|
| `name` | text | |
| `opacity` | integer 0–100 | |
| `visible`, `locked`, `selected`, `clipping mask` | boolean | |
| `blend mode` | enum | see [Enumerations](#enumerations) |
| `width`, `height` | real | writable. Image and shape layers keep their aspect when `constrain proportions` is true |
| `position` | point `{x, y}` | top-left in canvas pixels; can be negative or off-canvas |
| `bounds` | `{x, y, w, h}` | |
| `rotation` | real, degrees | |
| `color adjustments` | record | see below |
| `styles` | record | fill, stroke, shadow (shapes and text) |
| `parent`, `layer mask` | layer (ro) | |
| `index` | integer (ro) | 1 = top |

Make layers with `make new <class> at beginning of layers with properties {…}`
(`beginning` is the top of the stack, `end` the bottom). Inside `tell d` you can drop
`of d`.

| class | key properties / how to make |
|---|---|
| `image layer` | `{file:(p as POSIX file)}` places the image at its native pixel size, centred. Also `preserve transparency`, `constrain proportions` |
| `text layer` | `{text content:"Hello"}`, plus `horizontal alignment` (left/center/right/justify) and `vertical alignment` (top/center/bottom) |
| `rectangle shape layer` | `{width, height, position}` |
| `rounded rectangle shape layer` | plus `corner radius` |
| `ellipse shape layer`, `line shape layer` | |
| `polygon shape layer`, `star shape layer` | plus `sides` |
| `group layer` | `make group d` groups the selected layers. `ungroup` reverses it |
| `color adjustments layer`, `effects layer` | adjustment and effect layers that apply to the layers below |

Other ways to add layers: `make image d from f`, `make rectangle d width W height H
color {r,g,b}` and `make rounded rectangle …`. Remove a layer with `delete L`, copy
one with `duplicate L`. Select layers with `select {L1, L2}`.

## Text

`text content` is rich text. Style it as a whole or per `character` / `word` /
`paragraph`:

```applescript
set t to make new text layer at beginning of layers with properties {text content:"Sale"}
tell text content of t
    set its font to "Helvetica-Bold"   -- PostScript name; unknown -> falls back silently
    set its size to 120                -- integer points (= px at 72 ppi)
    set its color to {65535, 65535, 65535}
end tell
tell word 1 of text content of t to set its color to {65535, 0, 0}
set text content of t to "New text"   -- keeps the current style
```

`replace d text "Winter" with "Spring"` replaces text across every text layer of a
document. It takes `with properties {match words:true, case sensitive:true}`.

## Shapes and styles

`styles of L` holds `fill color`, `fill opacity` (0–100), `fill blend mode`,
`stroke width`, `stroke position` (inside/center/outside), `stroke type`
(line/dash/dot), `stroke color`, `stroke opacity`, and `shadow …` and `inner shadow …`
(`blur`, `distance`, `angle`, `color`, `opacity`). Set them one at a time:
`set fill color of styles of L to {0, 0, 0}`. `reset styles L` and `flatten styles L`
also exist.

## Colour adjustments

`color adjustments of L` holds integers, most of them −100…100: `temperature`, `tint`,
`hue`, `saturation`, `vibrance`, `exposure`, `highlights`, `shadows`, `brightness`,
`contrast`, `black point`, `texture`, `clarity`, `fade`, `vignette exposure`,
`vignette black point`, `vignette softness`, `grain`, `grain size`, `sharpen`. It
also has `sharpen radius` (real) and the booleans `black and white`, `sepia`,
`invert` and `vignette`.

```applescript
set exposure of color adjustments of L to -30
apply color adjustments preset L name "Vivid"      -- a preset name as shown in the app
reset color adjustments (color adjustments of L)
export as lut (color adjustments of L) to (p as POSIX file)
```

## Effects

Effects are elements of a layer:
`make new gaussian effect at end of effects of L with properties {radius:8}`. Each one
has `name` and `enabled`.

| effect class | properties |
|---|---|
| gaussian / box / disc | radius |
| motion | radius, angle |
| zoom / spin | position, amount |
| tilt shift / focus | blur, transition |
| bump / pinch | position, radius, scale |
| circle splash / hole | position, radius |
| light tunnel | position, radius, rotation |
| twirl / vortex | position, radius, angle |
| pixelate | scale |
| pointillize / crystallize | radius |
| checkerboard / stripes | position, color 1, color 2, width, sharpness, opacity |
| color fill | fill color |
| image fill / pattern fill | image, position, scale, angle, opacity, blend mode |

`apply effects preset L name "…"` applies a saved effects preset.

## Commands by area

ML and auto-adjust commands take the document (or a layer) and are synchronous:

| command | notes |
|---|---|
| `remove background d` (or a layer) | on a document, it acts on the current layer. The canvas size doesn't change |
| `super resolution d` | always ×3 |
| `enhance d` | ML Enhance |
| `denoise d [intensity N]` | ML Denoise |
| `deband d` | |
| `match colors d to f` | copies the look of another image |
| `auto white balance`, `auto light`, `auto color balance`, `auto hue and saturation`, `auto levels contrast`, `auto levels color`, `auto curves contrast`, `auto curves color` | |
| `detect face d` / `detect QR code d` | return position, size and bounds records (QR also returns its text) |
| `decontaminate colors L` | removes colour fringes left on a cut-out's edges |

Canvas and geometry:

| command | notes |
|---|---|
| `resize image d [width W] [height H] [resolution R] [algorithm lanczos]` | giving only width or only height keeps the aspect |
| `resize canvas d width W height H [anchor position middle center] [relative false]` | |
| `crop d bounds {x, y, w, h}` | |
| `trim canvas d [mode transparency]` | |
| `reveal canvas d` | |
| `rotate left` / `rotate right` / `rotate 180` | |
| `flip horizontally` / `flip vertically` | |
| `change color profile d to "sRGB IEC61966-2.1" [mode assign|match]` | |

Selections and masks: `select all`, `deselect`, `invert selection`,
`select subject d [smart refine true]`, `select color range d color {…} [range N]`,
`draw selection d bounds {…}`, `draw elliptical selection`, `refine selection d
[roundness] [softness] [expand]`, `smart refine selection`, `load selection L`,
`convert selection into shape`, `fill d with color {…}` (current layer or selection),
`clear d` (deletes the selected pixels), `mask L [from f] [mask mode reveal all|hide
all]`, `unmask L`.

Layers: `replace image L with f [scale mode scale to fill|scale to fit|stretch|original]`
(keeps adjustments, effects and styles, but renames the layer after the file),
`convert into pixels L`, `convert into shape t`, `merge d layers {…}`, `merge all`,
`merge visible`, `flatten`.

## Export

```applescript
export d to (p as POSIX file) as PNG
export d to (p as POSIX file) as JPEG with properties {compression factor:85}
export for web d to (p as POSIX file) as WebP with properties {compression factor:80, keep transparency:true, convert to sRGB:true, scale:100}
save as new document d in (p as POSIX file) as JPEG quality 85
```

- `export … as`: PNG, TIFF, JPEG, HEIC, GIF, JPEG2000, BMP, WebP, SVG, PDF, PSD, AVIF
  (`HDR AVIF`), OpenEXR, `HDR JPEG`/`HDR HEIC`/`HDR PNG`, and for animation `Motion`,
  `MP4`, `QuickTime Movie`, `Animated GIF`, `Animated PNG`.
- Export options: `compression factor` (1–100, the same scale as `sips formatOptions`),
  `bits per channel`, `color profile`, `frame rate`.
- `export for web` (PNG/JPEG/GIF/SVG/WebP) adds `advanced compression`,
  `reduce colors`, `keep transparency`, `convert to sRGB` and `scale` (percent).
- `export optimized d to f` picks the format from the file extension.
- `save as new document` writes Pixelmator Pro, HEIC, JPEG, PNG, WebP, TIFF, SVG, GIF
  or PSD, and the open document then points at the new file. To leave the session
  unchanged, use `export` and close the document without saving.

## Enumerations

- blend mode: normal, darken, multiply, color burn, linear burn, darker color, lighten,
  screen, color dodge, linear dodge, lighter color, overlay, soft light, hard light, vivid
  light, linear light, pin light, hard mix, difference, exclusion, subtract, divide, hue
  blend mode, saturation blend mode, color blend mode, luminosity, pass through, behind
  blend mode
- resampling algorithm: none, bilinear, lanczos, nearest, ml super resolution
- scale mode: original, stretch, scale to fill, scale to fit
- selection mode: new selection, add selection, subtract selection, intersect selection
- anchor: top left … bottom right (`middle center` is the centre)
- trim mode: transparency, top left color, bottom right color
- application properties: `image opening workflow` (open in original format / import
  as pixelmator pro), `sidecar location`, `appearance`
