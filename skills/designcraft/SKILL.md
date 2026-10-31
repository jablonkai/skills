---
name: designcraft
description: 'Automate DesignCraft, the InDesign-style page-layout app, headless with designcraft-cli: build multi-page documents from a spec (parent pages with headers and auto page numbers, paragraph styles, threaded text frames, placed images); data-merge CSV/XLSX records into badges, cards or catalogue pages; edit .designcraft or IDML files (restyle, relink images, replace text); export PDF/X-4 with bleed and marks checked by validate-pdf, page PNGs, IDML, EPUB, with every result read back. Use when the user mentions DesignCraft, designcraft-cli or a .designcraft file, or wants an InDesign-style layout made with DesignCraft: "lay out a 4-page brochure in DesignCraft", "merge this CSV into badges with DesignCraft", "change the Body style in this .designcraft and export page 1 as PNG", "press-ready PDF/X-4 from DesignCraft". Not for Scribus .sla (scribus), Affinity Publisher (affinity), Apple Pages (pages), Word or ODF documents (wordcraft, libreoffice), editing existing PDFs (pdfcraft), or vector art (vectorcraft).'
summary: "automate DesignCraft headless with designcraft-cli — multi-page layouts with parent pages, auto page numbers, styles, threaded text and placed images from a spec, CSV data merge for badges and catalogues, style and image edits, PDF/X-4 with bleed and marks checked by validate-pdf, per-page PNG, inspect read-back verified"
category: publishing
compatibility: "Built for DesignCraft 0.15.2 and designcraft-cli 0.15.2 on macOS, Python 3.9+, poppler (pdfinfo, pdftotext) for PDF checks; pre-1.0, so command ids may change."
risk: medium
tags: [designcraft, indesign, page-layout, dtp, data-merge, pdf-x, idml, headless]
license: GPL-3.0-only
metadata:
  version: "1.1.3"
  author: "Tamás Jablonkai"
---

# DesignCraft via designcraft-cli

DesignCraft is an InDesign-style layout app: a document (`.designcraft`, a zip holding
`document.json`) has spreads of pages, parent (master) spreads, frames on layers, stories
threaded through text frames, and paragraph/character/object styles. Every menu item and
panel action is a command in one engine registry (545 in 0.15.2). The same commands run
from `designcraft-cli run`, from command scripts (`script`), from a headless MCP session
(`designcraft-cli mcp`) and in the app. This skill drives them **headless**, so no window
opens, and checks every result by reading the document or the export back. Verified
against **DesignCraft 0.15.2** and **designcraft-cli 0.15.2** on macOS; the software is
pre-1.0, so if a pinned id fails, look it up rather than guessing.

```sh
command -v designcraft-cli || ls ~/.local/bin/designcraft-cli
designcraft-cli --version
```

## Pick the route

| Task | Route |
|---|---|
| New layout: pages, parent items, styles, text, images → save, PNG, PDF | `scripts/dc_build.py spec.json` |
| Merge template (`{{column}}` fields) for badges, cards, catalogue pages | `dc_build.py` with `"data"` |
| Merge records → one PDF / document | `scripts/dc_merge.py T.designcraft --pdf out.pdf [--per-page multiple]` |
| What a document holds: pages, styles, stories, overset, images | `scripts/dc_verify.py doc F` (no flags = summary) |
| Edit an existing document (style, image, text, pages) | copy it, then `run --in copy --cmd … --cmd file.save` ([recipes](references/recipes.md#open-edit-export)) |
| A page as PNG | `designcraft-cli run --in F --page N-1 --scale S --export p.png` |
| PDF/X-4 with bleed and marks | `--cmd 'file.exportPdf={"path":…,"standard":"x4","bleed":true,"marks":true}'`, then `validate-pdf` |
| IDML in or out, EPUB, PPTX | `run --in F.idml …` / `--export out.idml` ([cli.md](references/cli.md#exports)) |
| Many steps with results feeding later ones | a command script: `designcraft-cli script steps.dcs --in F --save G` (`$N.path` refs) |
| Find a command and its params | `scripts/dc_commands.py WORD…` / `--id ID` |

## Scripts

`S=<this skill>/scripts`; call as `python3 $S/<script>`. Python 3.9+, standard library
only, each with a full `--help`.

- **`dc_build.py SPEC.json [--overwrite] [--allow-overset]`**: a new document from a spec —
  `setup` (file.new params; lengths as points or `"3mm"`), paragraph/character `styles`,
  `parent` items (`"{page}"` = the auto page number; `on`: both/left/right), `items` on
  1-based pages with page-relative rects (negative = from the right/bottom edge,
  `"margins"` = the margin box, `"bleed": true` runs edges into the bleed), threaded text
  (`frames: [{page, rect}…]`, `textFile`, `style`, regex `rules` for headings), images
  with fitting, `data` + `{{column}}` merge fields, then save, PNGs (1-based `page`) and the
  PDF (`validate-pdf` run for `"standard": "x4"`). Fails and saves nothing on a command
  error or overset text. Spec reference: [recipes.md](references/recipes.md#brochure-from-a-spec).
- **`dc_merge.py T --pdf OUT [--data F.csv] [--save M] [--per-page multiple]`**: checks
  every `<<field>>` against the data's columns first, merges into a new document (the
  template is never written), fails on overset records or missing images, exports.
  `--per-page multiple` tiles records on a one-page, non-facing template (badges on A4).
- **`dc_verify.py`** prints JSON and exits 1 on any failed check:
  - `doc F --pages 4 --size A4 --no-overset --style Body:size=10.5 --story-style 'first words=Body' --thread 'first words=2,3' --image photo.jpg@1 --parent-text Header --page-number --placeholders name title --data people.csv --fonts-ok`
  - `pdf F.pdf --x4 --pages 4 --size A4 --bleed 3mm --marks --page-numbers --text 'Ada Lovelace' --once`
  - `png F.png --size 1191x1684` · `hash PATH… --compare manifest.json`
- **`dc_commands.py WORD…`** (`--prefix style.`, `--id text.thread`): filtered registry
  lookup with params. Never dump `designcraft-cli commands` (180 KB).

## Workflow

1. **Inspect first.** `dc_verify.py doc F` (pages, styles with attributes, stories with
   their pages and overset state, images per page). Look up any command you haven't used
   this session with `dc_commands.py`; `describe ID` gives the same signature.
2. **Never touch the originals.** Copy the document and edit the copy (`cp`, then
   `--cmd 'file.save={}'`), or `file.saveAs` a new path. Snapshot inputs with `dc_verify.py hash`.
3. **Do the work** with the route from the table.
4. **Read back**: `dc_verify.py doc` (styles, overset, threads, links) and `dc_verify.py pdf`
   (validate-pdf, pages, trim, bleed, text).
5. **Look at it.** Render the pages that matter (`--page` is 0-based) and view them: text
   in the wrong frame, an image cropped badly, a header colliding with the body or the
   default serif where a sans was meant only show up there.
6. **Report** outputs, the checks that passed, and anything you could not verify.

## The traps that cost the most (details in [gotchas.md](references/gotchas.md))

- **`run --page` and MCP `export_png {page}` are 0-based**; `file.exportPdf {pages}`,
  `layout.pages.*` page numbers and what the user says are 1-based. `--page 1` silently
  renders page 2 — on a short document a blank PNG ("0 glyphs" in the log).
- **Everything is in points**, whatever `units` says. `file.new {"units": "millimeters",
  "width": 210}` makes a 210 pt (74 mm) page; `units` only changes the UI display. Convert
  (mm × 72 / 25.4) or use `preset`. Coordinates are **spread** coordinates: on a facing
  spread the right page starts at x = page width.
- **The auto page number is the character U+E000** in story text (`"\ue000"` in JSON).
  There is no registry command for it, and a text variable won't do. Put it in a frame on
  the parent spread (`"spread": {"kind": "parent", "index": 0}`), once per side on
  facing pages.
- **PDF/X-4 is opt-in.** `--export out.pdf` and `script --export` write a plain PDF without
  bleed or marks (and `validate-pdf` then fails). Export with `file.exportPdf` and
  `"standard": "x4", "bleed": true, "marks": true`, or put `--pdf-options` before
  `--export` in `run`. Bleed comes from the document (`file.new {bleed}`).
- **Styles apply to the selection.** `style.paragraph.apply {name}` has no story param:
  `text.select {story, anchor: 0, focus: <length in UTF-8 bytes>}` first. Text offsets
  are byte offsets, not characters. Apply styles after inserting merge fields, or the
  paragraphs that were empty keep `[Basic Paragraph]`.
- **`data.merge` creates a new document** (the template stays unchanged); exports and
  saves after it are of the merged one. `perPage: "multiple"` needs a single page with
  facing pages off. Placeholders go in with `data.placeholder.add {field, story, at}`
  (`at` inserts; `end` does not replace).
- **Overset text is silent.** A story that doesn't fit just stops; exports succeed. Check
  `overset` in `document.inspect` (or `dc_verify.py doc --no-overset`) every time.
- **Run a document, not the default.** `run` without `--in` starts from an empty Letter
  document; `--sample` opens the sample magazine.

## References

- [references/cli.md](references/cli.md): subcommands, `run` ordering, `script` syntax and `$N` refs, exports and PDF options, MCP tools.
- [references/commands.md](references/commands.md): pinned 0.15.2 ids by task, with key params.
- [references/recipes.md](references/recipes.md): brochure spec, badges, open-edit-export, catalogue, IDML round trip.
- [references/gotchas.md](references/gotchas.md): silent failures and surprises.
- [references/security.md](references/security.md): file roots, and why there is no live-app bridge.
