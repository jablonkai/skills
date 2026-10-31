---
name: photocraft
description: 'Automate PhotoCraft, the Photoshop-style layered image editor, headless with photocraft-cli: build layered compositions (image, text, shape, fill and adjustment layers, layer styles) from a spec, apply filters and adjustments, edit PSD/.pcraft templates (text, visibility, smart-object images), export layer comps, layers or CSV data-set variants, batch-process folders with JSON actions, Photoshop .atn sets or .pcdroplet droplets, and convert formats, all verified by an info read-back and a rendered preview. Use when the user mentions PhotoCraft, photocraft-cli, a .pcraft file or a .pcdroplet droplet, or wants a PSD edited, a layered image built or an action run over a folder with PhotoCraft: "make a 1080x1080 post in PhotoCraft", "run Vintage.atn over this folder", "export every layer comp". Not for GIMP (gimp), Krita (krita), Pixelmator Pro (pixelmator-pro), Affinity (affinity), SVG (inkscape), or plain resizing with no PhotoCraft (sips/ImageMagick).'
summary: "automate PhotoCraft headless with photocraft-cli — layered compositions with text, shape and adjustment layers and styles, filters, PSD template edits, layer-comp, layer and CSV data-set export, folder batches from JSON actions, .atn sets or droplets, info read-back verified"
category: design-automation
compatibility: "Built for photocraft-cli 0.18.0 and PhotoCraft.app 0.18.0 on macOS; pre-1.0, so command ids may change."
risk: medium
tags: [photocraft, psd, image-editing, layers, batch, photoshop-actions, droplet, headless]
license: GPL-3.0-only
metadata:
  version: "1.2.5"
  author: "Tamás Jablonkai"
---

# PhotoCraft via photocraft-cli

PhotoCraft is a Photoshop-style layered editor. All of its features are commands in one
engine registry: every menu item, tool and dialog is a command (948 in 0.18.0). The same
commands are reachable from the CLI, a headless JSON session and the desktop app. This
skill drives them headless, so no window or GPU is needed, and checks every result by
reading the document back. Verified against **photocraft-cli 0.18.0** and
**PhotoCraft.app 0.18.0** on macOS. The software is pre-1.0, so the command ids pinned in
`references/` may change. When a pinned id fails, look it up.

```sh
command -v photocraft-cli || ls ~/.local/bin/photocraft-cli   # the CLI
photocraft-cli --version
```

## Pick the route

| Task | Route |
|---|---|
| One file: open, run commands, save | `photocraft-cli run` |
| A folder of images through one action list, `.atn` action or droplet | `photocraft-cli batch` / `droplet` |
| Build a layered composition (place images, text, fills, styles, anchors) | `scripts/pc_compose.py spec.json` |
| Many dependent steps, previews, or edits that need ids from earlier replies | `scripts/pc_session.py` (headless `serve`) |
| Exports that write folders (layer comps, layers, data sets) | `photocraft-cli run` (serve refuses raw paths) |
| The user wants to **watch** the edits in the app | `scripts/pc_live.py` (opt-in desktop control port) |

The headless routes are the default. Don't launch the GUI to read help: use
`photocraft-cli <sub> --help`, because running the app binary opens a window.

## Scripts

Paths are relative to this skill's directory. They need Python 3.9+ and the standard
library only. Call them as `python3 $S/<script>` with `S=<skill>/scripts`.

- **`pc_inspect.py`**
  - `layers FILE` prints the size, mode, depth, comps and the layer tree (id, kind,
    visibility, name, `[x,y,w,h]`, text, effects). Run it before editing anything.
  - `ids FILE NAME...` maps layer names to numeric ids.
  - `commands WORD...` prints matching registry ids with their full params signature.
- **`pc_compose.py SPEC.json`**: builds a composition from a canvas (or an opened
  template) and a bottom-to-top layer list:
  - images (`fit` cover/contain, `width`, `scale`), text, solid or gradient fills,
    adjustment layers and raw `cmd` steps;
  - placement by `anchor` + `margin` or `at`;
  - per-layer `name`, `opacity`, `blend`, `visible` and `style`;
  - outputs in `save` and a `preview` PNG.

  It refuses to overwrite existing outputs or its inputs unless given `--overwrite`.
  Spec example: [recipes.md](references/recipes.md#layered-composition-from-a-spec).
- **`pc_session.py STEPS|-`**: runs steps (`{"cmd": id, "params"}` or
  `{"method": "doc.open", …}`) through one `serve` session. Pass `--root DIR` covering
  every input and output (the default is the current directory). It sets the read/write roots,
  normalises paths, and stops at the first error with exit 1. **`"@layer:Name"`** in
  params becomes that layer's id at that moment.
- **`pc_verify.py`** prints JSON and exits 1 on any failed check:
  - `doc FILE --size WxH --text Name=… --hidden Name --effect "Name=Drop Shadow" --order Top,…,Bottom`
    (`--order` lists the layers **top first**)
  - `files DIR --count N --ext webp --long-edge 2048 --webp lossy`
  - `hash DIR [--compare manifest.json]`
- **`pc_live.py`**: `start --root DIR`, `call METHOD PARAMS`, `steps FILE`, `status`,
  `stop` for the running app over its authenticated loopback port.

## Workflow

1. **Inspect first.** Run `pc_inspect.py layers` on any input document, and
   `pc_inspect.py commands <words>` for any command you haven't used in this session.
   Don't guess ids or param keys: unknown ids fail, and unknown keys are often ignored
   silently.
2. **Never touch the originals.** Write to a new path (`--out`, `save`, a separate
   `--out` folder for batches) unless the user explicitly asks for in-place. Before a
   batch, snapshot the inputs with `pc_verify.py hash DIR > manifest.json`.
3. **Do the work** with the route from the table. Use absolute paths in every JSON
   param, and create output folders first.
4. **Read back** with `pc_verify.py`: size, mode and depth; layer names, order and
   visibility; text; effects; output count, format and dimensions; unchanged input
   hashes.
5. **Look at it.** Render a preview of any visual result and view the image:
   `pc_compose.py`'s `preview`, `doc.render {"path": …, "maxSide": 1024}` in a session, or
   the exported PNG itself. Overlaps, cropping and illegible text only show up there.
6. **Report** the output paths, what was verified, and anything PhotoCraft skipped
   (unsupported `.atn` steps, warnings).

## The traps that cost the most (details in [gotchas.md](references/gotchas.md))

- **Pass layer ids, not names.** `type.edit` silently ignores a `layer` name (even a
  correct one) and **edits the active layer instead**, with exit 0; check the `layer` in
  its reply. `image.variables.define` refuses names outright.
  `layer.select {"name": …}` selects by name, which makes a following `type.edit`
  without `layer` safe. Get ids from `pc_inspect.py ids`
  (valid for `run` on that same file) or write `"@layer:Name"` in `pc_session.py` steps.
  Ids change after a save and re-open.
- **Layer comps restore visibility.** Exporting comps re-applies each comp's recorded
  visibility, so a layer you just hid reappears. Per comp: `layerComp.apply`, then the
  change, then `layerComp.update {"what": "visibility"}`, and only then export. Text edits
  aren't part of a comp, so they carry through.
- **Bounds have two shapes:** command replies give `[x0,y0,x1,y1]`; `info` gives
  `[x,y,w,h]`. Fill layers report `null`. Measure their shape with
  `select.loadSelection {"channel":"mask","layer":id}` and then `selectionBounds`.
- **Text:** `type.create` `y` is the baseline, and the size defaults to 12 pt. Always set
  `size`, and place with an anchor or by translating after reading the bounds.
- **`serve` file access fails closed:** read/write roots are required, `..` is rejected,
  and raw-path commands (`file.export.layerCompsToFiles`,
  `file.import.variableDataSets`, `layer.smartObjects.replaceContents`) are disabled.
  Use `doc.*` methods (`doc.replaceSmartObject {path, layer}` for a swap) or
  `photocraft-cli run` for those.
- **Overwrites:** `run`/`convert` refuse an output that is the input unless
  `--in-place`; pass it only when the user asked for an in-place edit. `run` without
  `--out` saves nothing, which makes it a free dry run.
- **Quality scales:** CLI/`doc.save` `quality` is 1..100; engine `quality` params
  (droplets, `file.export.*`) are 0..12. WebP with a quality is lossy, without one
  lossless.
- **`replaceContents` (and `doc.replaceSmartObject`) keeps the old scale, not the
  frame.** Refit it with `edit.transform` and a `quad`.

## Common jobs

- **Composition** (social post, banner, thumbnail): write a spec, run `pc_compose.py`,
  then `pc_verify.py doc` + `files`, then view the preview.
- **Batch**: write a JSON action list (`[["file.automate.fitImage",{"width":2048,"height":2048}],["filter.sharpen.unsharpMask",{"amount":80}]]`),
  run `photocraft-cli batch --actions a.json --in IN --out OUT --format webp --quality 80`,
  then `pc_verify.py files OUT …` and `hash IN --compare`. `batch` doesn't recurse; for
  subfolders use `file.automate.batch` with `includeSubfolders`
  ([recipes.md](references/recipes.md#folder-batch-resize-sharpen-convert)).
- **Template edit and comps, data sets, layer export, smart-object swap, `.atn`,
  droplets**: [recipes.md](references/recipes.md).
- **Filters and adjustments**: `run in.jpg --cmd image.autoTone --cmd filter.sharpen.smartSharpen --params '{"amount":80}' --out out.jpg`.
  For non-destructive edits use `layer.newAdjustmentLayer.<kind>` and save `.psd`.

## References

- [references/cli.md](references/cli.md): every subcommand, its flags and verified
  behaviour, plus formats and quality.
- [references/commands.md](references/commands.md): the pinned command ids by task, with
  their key params.
- [references/recipes.md](references/recipes.md): worked commands for each job above.
- [references/gotchas.md](references/gotchas.md): everything that fails silently.
- [references/control-protocol.md](references/control-protocol.md): `serve` methods,
  filesystem roots, the desktop control port, its **security posture** and limits.

## Live app (opt-in)

`pc_live.py start --root DIR` opens PhotoCraft with `--control 7878`. It listens on
127.0.0.1 only and uses a 256-bit token from `~/.config/photocraft-skill/control.token`
(0600, never on the command line). File access is limited to `DIR`. `app.open`/`app.save`
paths are relative to that root. `pc_live.py stop` sends `app.quit`, which **discards
unsaved edits**, so save first. Start the port only for this, and stop it when done.
