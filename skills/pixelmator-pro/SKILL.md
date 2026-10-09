---
name: pixelmator-pro
description: 'Drive Pixelmator Pro on macOS through its AppleScript dictionary (osascript): remove backgrounds and export transparent PNG cut-outs, ML Super Resolution upscaling, ML Enhance, denoise and auto-adjust, resize and convert whole folders to JPEG/PNG/HEIC/WebP/PSD at a set quality, compose layered graphics (image, text, shape layers) like social posts and banners at exact sizes, fill .pxd templates, colour adjustments and effects. Use when the user mentions Pixelmator, or wants Apple-native ML photo edits or a layered image built by script on a Mac: "remove the background from these product photos", "upscale this folder 3x", "make a 1080x1350 Instagram post with this photo and a headline", "batch-export to WebP at 80%", Hungarian "vágd ki a hátteret", "nagyítsd fel a képeket". Not for GIMP (gimp), painting or brush strokes (krita, rebelle), Affinity files (affinity), SVG/vector art (inkscape), the Photos library (apple-photos), or plain format conversion with no edits (sips).'
summary: "remote-control Pixelmator Pro via AppleScript — layered compositions with image, text and shape layers, adjustments and effects, ML Super Resolution, Remove Background and Enhance, .pxd template fill, and single-file or folder-batch export to PNG, JPEG, HEIC, WebP and PSD"
category: design-automation
risk: medium
tags: [pixelmator, applescript, macos, photo, background-removal, super-resolution, batch, image-editing]
metadata:
  version: "1.0.0"
---

# Pixelmator Pro via AppleScript

Pixelmator Pro has a full AppleScript dictionary (documents, layers, text, shapes,
adjustments, effects, ML commands, export). This skill drives it through `osascript`.
There is no bridge and no network listener. Apple Events stay on the machine and macOS
gates them with the Automation (TCC) permission. It was verified against **Pixelmator
Pro 3.8** (Mac App Store) on macOS 27.

The ML commands (`remove background`, `super resolution`, `enhance`, `denoise`) are
**synchronous**: they return when the work is finished, so there's nothing to poll.

## Scripts

Paths are relative to this skill's directory. All of them refuse to overwrite their
inputs, close every document they open without saving, and return JSON.

- [scripts/pxm.sh](scripts/pxm.sh): `check` prints the version and the Automation
  permission state. `run FILE|- [--timeout N] [ARGS]` runs an AppleScript (or a `.js`
  JXA file). `close-all` closes every open document without saving. **Run every custom
  script through `pxm.sh run`.** It watches for Pixelmator's error alerts, which are
  app-modal and block every later Apple Event: it reports the alert's text, dismisses
  it and fails the run. It also stops the script at the timeout.
- [scripts/pxm-batch.py](scripts/pxm-batch.py): files or folders (recursive,
  subfolders mirrored) go through `--ops` (remove-bg, super-res, enhance, denoise,
  auto-light, auto-color, auto-white-balance, trim), then `--resize` (WxH, wN, hN,
  fitN), then export with `--format`/`--quality` into `--out`. It processes one
  document at a time, skips existing outputs, and has `--dry-run`.
- [scripts/pxm-compose.py](scripts/pxm-compose.py): JSON spec in, layered document
  out. The spec sets the canvas, the background and the layers bottom to top: image
  (cover, contain or none fit, optional remove-background), text (font, size, colour,
  alignment), and rect, rounded-rect, ellipse, polygon or star shapes with fill and
  stroke. It exports any mix of PNG, JPEG, WebP, PSD and `.pxd`, then reports every
  layer as Pixelmator applied it (real bounds, real font).
- [scripts/pxm-info.py](scripts/pxm-info.py): the oracle. Run it on outputs to get
  format, pixel size, alpha at the corners and centre, `transparent_ratio`, and
  `jpeg_quality` on the same 1–100 scale as Pixelmator's compression factor. For
  `.pxd` it lists the layers.

## Workflow

```bash
H=scripts
bash $H/pxm.sh check                                   # 1. installed? permission?
# 2a. per-file pipeline over files/folders
python3 $H/pxm-batch.py IN_DIR --out OUT_DIR --ops remove-bg --format png
python3 $H/pxm-batch.py IN_DIR --out OUT_DIR --ops super-res --format jpeg --quality 85
# 2b. layered design from a spec
python3 $H/pxm-compose.py spec.json
# 2c. anything else: write an AppleScript and run it
bash $H/pxm.sh run my.applescript --timeout 900 ARG1 ARG2
python3 $H/pxm-info.py OUT_DIR                         # 3. verify, then look at it
```

1. **Pick the right tool.** A per-file pipeline (cut-outs, upscales, enhance, resize,
   convert) goes to `pxm-batch.py`. A new layered design goes to `pxm-compose.py`. To
   edit an existing `.pxd`/PSD or use features the two don't cover (template text,
   colour adjustments, effects, presets, selections, masks), write AppleScript using
   [references/recipes.md](references/recipes.md). Look up classes and commands in
   [references/api-reference.md](references/api-reference.md).
2. **Verify before you report.** Run `pxm-info.py` on every output: check its size,
   format, alpha and quality against the request. Then **Read** a PNG of the result
   (for big or non-PNG outputs, convert a copy with `sips -Z 800 -s format png`). Check
   that text isn't clipped, cut-outs kept the subject, and nothing landed off-canvas.
   For compositions, compare the layer report with the spec. Text layers grow
   downward from their `y`, so a headline can overflow its panel.
3. **Report** one line per output: size, format, quality or alpha. Mention any file
   that failed and the alert text `pxm` printed.

## Writing your own AppleScript

Read [references/gotchas.md](references/gotchas.md) first. These are the ones that
break scripts silently:

- **Coerce paths outside the `tell` block**, or with `as POSIX file`, never with
  `POSIX file someVar` inside `tell application "Pixelmator Pro"`. The app is
  sandboxed, and that form is resolved by the app without a sandbox grant. Every file
  it hasn't opened before then fails with "The document is damaged". Literal paths
  and `p as POSIX file` are fine.
- Wrap ML work in `with timeout of 7200 seconds … end timeout`, since Apple Events
  give up after 120 s by default. Close with `close d saving no`, also in an `on
  error` branch, so a failed run doesn't leave documents open.
- `width`/`height`/`position` are reals. Use `as integer` before building strings.
  Otherwise the locale's decimal comma turns `1800.0` into `1800,0`. Get `position of
  L` into a variable before taking `item 1`.
- Colours are 16-bit `{r, g, b}` lists from 0 to 65535 (`#ff8800` is `{65535, 34952, 0}`).
- A new document already has a white `Image Layer` at the bottom. `layers` is listed
  top-first, and `make new … at beginning of layers` puts the new layer on top.
- Text styling goes through the text's rich text: `tell text content of t to set its
  font to "Helvetica-Bold"` (PostScript names; an unknown font silently falls back to
  Helvetica, so read `font` back). `position` is the text box's top-left corner.
- `replace image L with f` **renames the layer** after the file. Hold the layer in a
  variable (references are id-based), then set `name` back.
- `super resolution` is always 3×. To hit a target size, upscale first, then `resize
  image` to the exact size.

## Request → approach

| The user wants | Do |
|---|---|
| transparent product cut-outs | `pxm-batch.py DIR --out OUT --ops remove-bg --format png` (WebP and HEIC keep alpha too; JPEG flattens it) |
| upscale a folder | `--ops super-res` (3×), plus `--resize fitN` for an exact long edge |
| "clean up / enhance / denoise" photos | `--ops enhance` or `denoise`, `auto-light`, `auto-color`, `auto-white-balance` |
| resize and convert only | `pxm-batch.py --resize fit2048 --format webp --quality 80` (no ops); for a plain re-encode with no edits, `sips` alone is enough |
| social post or banner at W×H | `pxm-compose.py`: image `cover`, then panel shape, then text with `align: center` and `width: W` |
| fill a `.pxd` template | recipe "Fill a template" (set text by layer name, `replace image … scale mode scale to fill`) |
| colour grade or effects | `color adjustments of L` properties, `make new gaussian effect at end of effects of L` (recipes) |
| keep it editable | also export `.pxd` (`save d in f`), or PSD for other apps |

## Prerequisites

- Pixelmator Pro installed (`pxm.sh check`). The first scripted run triggers macOS's
  Automation prompt for the terminal. If it was denied, runs fail with `-1743` and
  `pxm.sh` exits 3. The fix is in System Settings › Privacy & Security › Automation.
- The alert watchdog reads Pixelmator's windows through System Events, which needs
  Accessibility permission for the terminal. Without it, alerts aren't dismissed and
  the run ends at the timeout instead.
- Don't use Pixelmator Pro by hand during a batch: every script closes the documents
  it opened, and the timeout path closes **all** open documents without saving.
