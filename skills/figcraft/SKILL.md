---
name: figcraft
description: 'Automate FigCraft, the Figma-style UI/interface design app, headless with figcraft-cli: build app and web screens from a spec (frames with auto layout, components and instances, text and colour styles), open and inspect .fig, Figma REST-API JSON and .figcraft files and report what an import dropped, edit text and layer properties, export frames or named nodes as PNG @1x/@2x, SVG, and print PDF with bleed, crop marks and CMYK, and render pages to check, all verified by a read-back. Use when the user mentions FigCraft, figcraft-cli or a .figcraft file, or wants a UI screen, mockup or design-system file made, a .fig/REST JSON design opened, edited or exported, without the Figma app: "design a 390x844 login screen in FigCraft", "export every frame of this .fig as PNG", "print PDF of the card frame with 3 mm bleed". Not for vector illustration or logos (vectorcraft, inkscape), Affinity (affinity), diagrams (drawio), raster/PSD editing (photocraft), or the Figma web app, its REST API or Figma plugins.'
summary: "automate FigCraft headless with figcraft-cli — UI screens from a spec with auto layout, components and text styles, .fig and REST JSON import with dropped-feature report, text and property edits, PNG @2x, SVG and print PDF with bleed and crop marks, info and inspect read-back verified"
category: design-automation
compatibility: "Built for figcraft-cli 0.11.2 and FigCraft.app 0.11.2 on macOS, Python 3.9+; pre-1.0, so command ids may change."
risk: medium
tags: [figcraft, figma, ui-design, fig, auto-layout, components, export, headless]
metadata:
  version: "1.0.0"
---

# FigCraft via figcraft-cli

FigCraft is a Figma-style interface design app: pages, frames, auto layout, components
and instances, styles and variables. Every menu item, panel action and shortcut is a
command in one engine registry (597 of them in 0.11.2). The same commands run from
`figcraft-cli run`, from a headless session (`figcraft-cli mcp`) and in the app. This skill
drives them **headless**, so no window opens, and checks every result by reading the
document back. It is verified against **figcraft-cli 0.11.2** and **FigCraft.app 0.11.2** on
macOS. The software is pre-1.0, so if a pinned id fails, look it up rather than guessing.

```sh
command -v figcraft-cli || ls ~/.local/bin/figcraft-cli
figcraft-cli --version
```

Don't launch the app to read help: `figcraft-cli --help` covers everything, and running the
app binary opens a window.

## Pick the route

| Task | Route |
|---|---|
| Build screens/components from scratch, save and export | `scripts/fc_build.py spec.json` |
| Edit an existing file (text, properties, styles, add layers) | `scripts/fc_session.py steps.json` |
| What is in a file: pages, top-level frames, missing fonts, dropped features | `figcraft-cli info FILE --json` |
| Every layer, its text, components, auto layout | `scripts/fc_verify.py doc FILE` |
| Export the screens, one file each (no components) | `scripts/fc_export.py FILE OUTDIR [--format png] [--scale 2]` |
| All screens as one multi-page PDF (no components) | `scripts/fc_export.py FILE out.pdf --one-pdf [--cmyk] [--bleed 3mm --crop-marks]` |
| Export one layer by id or name | `figcraft-cli export FILE -o x.png --node ID [--page NAME] [--scale 2]` |
| Print PDF of one frame with bleed and marks | `figcraft-cli export FILE -o x.pdf --node ID --bleed 3mm --crop-marks [--cmyk]` |
| Convert `.fig` / REST JSON / SVG ↔ `.figcraft` | `figcraft-cli convert IN OUT` |
| One-shot command list on a new or existing file | `figcraft-cli run steps.json [--in F] --out F` |
| A look at a page | `figcraft-cli render FILE -o page.png [--page NAME]` |

## Scripts

`S=<this skill>/scripts`; call as `python3 $S/<script>`. Python 3.9+, standard library
only, each with a full `--help`.

- **`fc_commands.py WORD…`** (`--prefix style.`, `--id node.set`): filtered registry lookup
  with each command's params. Never dump `figcraft-cli commands` — it is ~600 entries.
- **`fc_build.py SPEC.json`**: paint and text styles, components and variant sets
  (`"variants": [...]`), frames with nested children (auto layout via `props`; children of
  a vertical layout stretch by default), instances with text overrides and
  `"variant": {"Style": "Secondary"}`, then save, exports
  (`{"frames": "each", "dir": …}` for one file per frame) and a rendered preview. All layers
  are created in one batch (one undo step; a failure creates nothing). Refuses to overwrite
  without `--overwrite`. Spec: [recipes.md](references/recipes.md#mobile-screen-from-a-spec).
- **`fc_export.py FILE OUT`**: the screens (top-level frames) of a page, skipping main
  components and loose layers — one file each (`--format`, `--scale`, `--suffix @2x`,
  `--frames A B`, `--page`) or `--one-pdf` (one page per screen, print options). Never
  saves the source.
- **`fc_session.py STEPS|-`**: one stateful headless session. Steps: `open`, `cmd`, `batch`,
  `find`, `inspect`, `node`, `export`, `save`, `screenshot`, `tool`. `"@name:Headline"`,
  `"@name:Home/Headline"` (scoped to a top-level frame), `"@text:Sign in"` and
  `"@type:COMPONENT"` resolve to the one matching layer id. Stops at the first error.
- **`fc_verify.py`** prints JSON and exits 1 on any failed check:
  - `doc FILE --frame Login=390x844 --text Home/Headline="Hi" --names Email Password --component Button --instance Button@Login --auto-layout Login --style H1 --text-style "Welcome back=H1" --no-notes --fonts-ok`
  - `files DIR --ext png --count 3 --px 780x1688` · `files x.svg --svg`
  - `files x.pdf --pdf-pages 1 --trim 255x156 --bleed 3mm --marks`
  - `hash DIR [--compare manifest.json]`

## Workflow

1. **Inspect first.** `figcraft-cli info FILE --json` gives pages, top-level frames, `notes`
   (what a `.fig` or REST JSON import skipped) and `missingFonts`. It shows no child layers
   or text — for those use `fc_verify.py doc FILE` or a `find`/`node` session step. Look up
   any command you haven't used this session with `fc_commands.py`.
2. **Never touch the originals.** Write to new paths; snapshot inputs with
   `fc_verify.py hash IN > manifest.json` before batch work. `export` and `convert` overwrite
   silently, and `convert IN IN` rewrites the source.
3. **Do the work** with the route from the table. The session's file access is confined to
   `--root` (default: the current directory), so pick a root that holds inputs and outputs.
4. **Read back** with `fc_verify.py`: `doc` for structure and text, `files` for counts,
   pixel sizes and PDF boxes, `hash --compare` for untouched inputs.
5. **Look at it.** View the preview, a `screenshot` step or the exported PNG. Overlapping
   layers, clipped or tiny text and wrong colours only show up there.
6. **Report** outputs, what was verified, and the import `notes` — say explicitly when an
   import dropped nothing, and name what it dropped otherwise.

## The traps that cost the most (details in [gotchas.md](references/gotchas.md))

- **Refer to earlier steps with `{"$step": n}`, never `"$0.id"`.** In `run` scripts and
  `batch` steps, `"parent": {"$step": 0}` is step 0's created id; the string form is
  rejected. Anything that must *find* a layer by name goes through `fc_session.py`.
- **Names aren't unique.** Two screens can each have a `Headline`; `export --node NAME`
  then silently picks one. Scope refs as `@name:Home/Headline`, or export by id.
- **Every whole-page export includes the main components.** `export -o DIR` writes a
  `Button.png` next to the screens, and `export -o x.pdf` / `file.exportFramesPdf` add the
  component as an extra PDF page. Use `fc_export.py`, which exports screens only.
- **`-o file.png` without `--node` composites the whole page** into one image; `-o x.pdf`
  writes one page per top-level layer.
- **Inside an auto-layout frame, x/y are ignored** — order is the children's order. Use
  `layout`, `gap`, `padding`, `mainAlign`/`crossAlign`.
- **A fixed width doesn't follow the screen.** Inputs, buttons and body text in a screen
  should use `sizingH: "fill"`, so they stretch when the frame is resized to another
  device width (and text wraps). `fc_build.py` does this for children of a vertical
  layout that have no `width`; check with `fc_verify.py doc … --fill Login/Email`.
- **New text is Inter 12 px black, frames are white.** Set `fontSize`/`fill` explicitly.
- **Instances copy the component's text**; override it on the instance's child
  (`node.set {"ids": [child], "characters": …}`, or `fc_build.py`'s `"text": {"Label": …}`).
- **`.fig` import is best effort.** Read `info`'s `notes` on the *source* file and report
  them — the converted `.figcraft` no longer carries them.

## References

- [references/cli.md](references/cli.md): subcommands, flags, formats, print options, verified behaviour.
- [references/commands.md](references/commands.md): pinned 0.11.2 ids by task, with key params.
- [references/session.md](references/session.md): the MCP tools, refs, and the inspect JSON fields.
- [references/recipes.md](references/recipes.md): worked specs and step files.
- [references/gotchas.md](references/gotchas.md): silent failures and surprises.
- [references/security.md](references/security.md): file roots, and why there is no live-app bridge.
