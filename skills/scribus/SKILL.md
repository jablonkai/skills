---
name: scribus
description: 'Lay out print documents headless with Scribus 1.6 and its Python scripter: multi-page flyers, brochures and booklets with master pages, paragraph/character styles, threaded text frames and images; data-driven layouts from CSV (name badges, place cards, labels, certificates, catalogue pages); and print-ready PDF/X-4 (or X-1a/X-3) export with bleed and crop marks, including exporting an existing .sla. Every run is checked for overflowing text, missing images, substituted fonts, page size and bleed. Use for "make a 4-page A5 flyer from this text and these photos", "generate name badges from this CSV", "export this .sla as PDF/X-4 with 3 mm bleed", "print-ready PDF with crop marks for the printer", "Scribus script", ".sla". Not for a live Affinity Publisher session (affinity), Apple Pages templates (pages), Word/ODF documents or office-to-PDF conversion (libreoffice), vector illustration or posters drawn as SVG (inkscape), or slide decks (keynote).'
summary: "lay out print documents headless with Scribus — multi-page layouts with master pages, styles, threaded text and images, CSV-driven badges and catalogues, PDF/X-4 export with bleed and marks"
category: design-automation
risk: low
tags:
    - scribus
    - dtp
    - layout
    - pdf-x
    - print
    - csv
---

# Scribus via headless Python jobs

Scribus is driven by **one short-lived headless process per job**: a Python script that
runs inside Scribus (`Scribus -g -ns -py`), builds or opens a document, and saves the
`.sla` and PDF. There is no GUI session, server or bridge. The user can open the `.sla` in
Scribus afterwards to fine-tune by hand.

[scripts/scribus.py](scripts/scribus.py) (system `python3`, stdlib only) runs the jobs and
checks the results; [scripts/scribus_lib.py](scripts/scribus_lib.py) is the helper library
jobs import inside Scribus. Verified against **Scribus 1.6.6** (bundled Python 3.13) on
macOS 27; `verify`/`render` need poppler (`brew install poppler`).

## Why the runner exists

Raw `Scribus -g -py job.py` fails in ways that look like success:

| Raw behaviour | What the runner / library does |
|---|---|
| An exception in the job still **exits 0**; `print()` output is lost | Wraps the job, writes a JSON result, exits 1 with the traceback |
| Text that does not fit a frame is **silently cut off** in the PDF | Reports every overflowing story after the job (`--strict` fails) |
| `loadImage` accepts a **missing file**; the PDF just has no picture | `image_box` raises; missing images are reported |
| A font missing from an opened `.sla` is **silently substituted** | `font()` picks from installed fonts; `export` reports substitutions |
| `PAPER_A5` is in points: with mm units it makes an **A2** page | `new_doc(w, h)` takes mm |
| `--` or `-x` after the script path is parsed by Scribus itself | Job arguments travel through the environment |

More traps (localized default names, master-page editing, leading): [references/gotchas.md](references/gotchas.md).

## Commands

```bash
SC=<this skill>/scripts/scribus.py
python3 $SC find                                   # app path, version, bundled Python
python3 $SC run job.py [--strict] [--timeout 180] -- arg1 --opt x   # job args after --
python3 $SC run <skill>/scripts/badges.py -- --csv people.csv --out out/badges [--logo l.png]
python3 $SC export doc.sla -o doc.pdf [--preset x4|x1a|x3|print|screen] [--bleed 3] [--marks]
python3 $SC inspect doc.sla                        # pages, masters, styles, fonts, images (no Scribus)
python3 $SC verify doc.pdf --pages 4 --trim 148x210 [--bleed 3] [--marks] [--pdfx4] \
        [--min-images 3] [--min-ppi 150] [--text source.txt]
python3 $SC render doc.pdf -o pages/ [--dpi 100]   # PNG per page — look at them
```

- Exit codes: 0 ok, 1 job or check failed, 2 usage, 3 Scribus missing or timeout.
- `--json` on `find`, `run`, `export`, `inspect` and `verify`.
- Relative paths in job arguments resolve against **your** working directory.
- `export` never touches the source `.sla`, refuses to overwrite without `--force`, and
  exits 1 on missing images or substituted fonts unless `--allow-problems`.

## Workflow

1. **Gather inputs**: text (keep it UTF-8), images (check they exist and are big enough:
   pixels ÷ (mm ÷ 25.4) ≥ 300 ppi for print, 150 acceptable), CSV columns, finished size,
   page count, bleed (3 mm is the usual default) and the printer's PDF requirement.
2. **Write a job** — a plain Python file that imports `scribus` and `scribus_lib as L`,
   saves the `.sla` and exports the PDF, and sets `RESULT = {...}` with anything worth
   reporting. For CSV badges, cards or labels use `scripts/badges.py` as is, or copy it.
3. **Run it** with `run --strict`. Fix every overflow and missing-image warning — an
   overflow means text is missing from the PDF.
4. **Verify** the PDF with the expected page count, trim, bleed and `--pdfx4`, then
   **render** and look at the pages: overlaps, awkward breaks, images cropped badly, and
   text running into the bleed are only visible there.
5. **Report** the `.sla` and PDF paths, page size, page count, PDF flavour, fonts used and
   anything you compromised on (shrunk text, low-ppi image, added pages).

## Writing a job

```python
import sys, scribus
import scribus_lib as L

out = sys.argv[1]                                   # e.g. "out/flyer"
L.new_doc(148, 210, margins=(12, 12, 12, 15), pages=4, bleed=3)   # mm; (l, r, t, b)
serif = L.font("Minion Pro Regular", "Georgia Regular", "Times New Roman Regular")
sans_b = L.font("Helvetica Neue Bold", "Arial Bold")
L.para_style("Body", serif, 10, 13, align="justify", space_after=1.5)  # pt, pt, mm
L.para_style("H1", sans_b, 22, 26, space_after=4)
blue = L.cmyk("Brand Blue", 100, 30, 0, 0)          # percentages

def footer():                                      # master content: page=None, no gotoPage
    L.text_box(None, 12, 198, 124, 6, [("Spring Fair 2026", "Body")])
L.master("Main", footer)
L.apply_master("Main")

L.rect(1, -3, -3, 154, 70, fill=blue)               # full-bleed band: extend 3 mm past trim
story = L.text_box(1, 12, 75, 124, 120, [("Welcome", "H1"), (intro, "Body")])
p2 = L.text_box(2, 12, 12, 124, 183)
L.link(story, p2)                                   # thread frames; or L.flow(story) to add pages
L.image_box(3, "photos/market.jpg", 12, 12, 124, 90)  # whole image, raises if missing
L.image_box(4, "photos/hero.jpg", -3, -3, 154, 100, fit="cover")  # fill + crop, full bleed
L.assert_clean()                                    # overflow / missing image -> exception
L.save_sla(out + ".sla")
L.paragraph_keeps(out + ".sla", keep_with_next=["H1"], orphans=2, widows=2)
L.reopen(out + ".sla")                              # keeps live only in the .sla, see below
L.export_pdf(out + ".pdf", preset="x4", marks=True)  # PDF/X-4, doc bleed, crop marks
RESULT = {"pages": scribus.pageCount()}
```

- **Units**: every helper takes mm; font sizes and leading are pt. Use the raw
  `scribus.*` API freely next to the helpers — the curated list is in
  [references/api-reference.md](references/api-reference.md).
- **Styles, not local formatting**: create paragraph styles and pass `(text, style)`
  pairs; the `.sla` then stays editable for the user.
- **Fitting text**: `L.flow(frame, master=...)` appends pages until the story fits;
  `L.fit_text(frame, min_size)` shrinks a single frame. A fixed page count (a 4-page
  flyer) means editing type size, leading or image size until `assert_clean()` passes —
  never leave overflow.
- **Images**: `fit="contain"` (default) shows the whole picture; `fit="cover"` fills the
  frame and crops the overflow, centred — the usual choice for photos in shaped frames.
  For full-bleed images, make the frame extend past the trim by the bleed.
- **Headings stranded at a frame bottom, single lines at a column top**: the scripter
  has no keep-with-next or orphan/widow API. `L.paragraph_keeps()` writes them into the
  saved `.sla` styles; `L.reopen()` reloads it so the export honours them. Still look at
  the render — a forced break can push text into overflow, which the runner reports.
- **Name frames** you will look up later (`name="title"`); default names are localized.

## PDF export

`L.export_pdf(path, preset, bleed=None, marks=False)`; `export` on the CLI does the same
for an existing `.sla`.

| preset | Result | Use for |
|---|---|---|
| `x4` (default) | PDF/X-4, PDF 1.6, CMYK output intent (ISO Coated v2 300%) | Most printers today |
| `x1a` / `x3` | PDF/X-1a:2001 / PDF/X-3:2002, PDF 1.3 | Printers that ask for them; no transparency |
| `print` | PDF 1.6, print colours, no PDF/X | Office or digital printing |
| `screen` | PDF 1.5, RGB, 150 ppi | Email and web |

Bleed comes from the document (`new_doc(bleed=3)`) unless `bleed=` overrides it; marks
are crop, bleed, registration and colour bars. veraPDF cannot validate PDF/X, so
`verify --pdfx4` checks the structure instead: the X-4 marker, the output intent,
TrimBox on every page, embedded fonts. Details: [references/pdf-export.md](references/pdf-export.md).

## References

- [references/api-reference.md](references/api-reference.md): the scripter API by task
  (document, pages, masters, frames, text, styles, colours, images, export) with units.
- [references/recipes.md](references/recipes.md): folded flyer, threaded article with
  auto pages, catalogue from CSV, certificates, badges variations, exporting existing files.
- [references/pdf-export.md](references/pdf-export.md): `PDFfile` attributes, version
  codes, bleed and marks, colour profiles.
- [references/gotchas.md](references/gotchas.md): measured traps, and the security posture.
