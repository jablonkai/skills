# Recipes

Every recipe is a job file, run as
`python3 <skill>/scripts/scribus.py run job.py --strict -- <args>`, then checked with
`verify` and `render`. All of them were run against Scribus 1.6.6 as written.

## Contents
1. Fixed-page flyer (fit the copy to 4 pages)
2. Booklet: threaded story, auto pages, page numbers, facing pages
3. Product catalogue from CSV (image grid)
4. Certificates / one page per CSV row
5. Badges, cards and labels (`badges.py`)
6. Exporting an existing .sla
7. Editing an existing .sla

## 1. Fixed-page flyer (fit the copy to 4 pages)

The [SKILL.md](../SKILL.md) job is the skeleton: a cover with a full-bleed band, a story
threaded across pages 1–3, and a back page with images. When the page count is fixed,
fit the copy instead of adding pages. In order:

1. Thread every text frame of the flyer (`L.link(a, b, c)`).
2. Check `L.overflows(a)`. If it's true, reduce in small steps and re-check:
   - body size 10 → 9.5 → 9 pt, keeping leading at about 1.3×
   - image heights
   - frame gaps
3. If it still doesn't fit at 8.5 pt, tell the user the copy is too long for 4 A5 pages.
   Don't go smaller, and never cut text silently.

```python
for size in (10, 9.5, 9, 8.5):
    # Redefining a style updates every frame using it. Char style first: the paragraph
    # style picks up its char style's values when it is (re)created.
    scribus.createCharStyle(name="Body_c", font=serif, fontsize=size)
    scribus.createParagraphStyle(name="Body", linespacingmode=0, linespacing=size * 1.3,
                                 alignment=3, charstyle="Body_c")
    if not L.overflows(story):
        break
```

Headline-and-image pages read better with the story frames sized to the leftover space:
place images first, then compute the text frames from what remains.

## 2. Booklet: threaded story, auto pages, page numbers, facing pages

```python
import sys, scribus
import scribus_lib as L

src, out = sys.argv[1], sys.argv[2]
paras = [p.strip() for p in open(src, encoding="utf-8").read().split("\n") if p.strip()]
L.new_doc(148, 210, margins=(18, 12, 15, 20), pages=1, bleed=3, facing=True)  # l=inside, r=outside
serif = L.font("Georgia Regular", "Times New Roman Regular")
L.para_style("Body", serif, 10, 14, align="justify", first_indent=4)
L.para_style("Title", L.font("Georgia Bold", "Times New Roman Bold"), 20, 24, space_after=6)
L.para_style("Folio", serif, 8, 10, align="center")

def folio():
    f = L.text_box(None, 12, 196, 124, 6, [("", "Folio")])
    scribus.insertText(chr(0x1E), 0, f)          # automatic page number
L.master("Text", folio)
L.apply_master("Text")
first = L.text_box(1, *L.margin_box(1), [(paras[0], "Title")] + [(p, "Body") for p in paras[1:]])
added = L.flow(first, master="Text")               # appends pages until it fits
while scribus.pageCount() % 4:                      # booklets need a multiple of 4 pages
    scribus.newPage(-1, "Text")
L.assert_clean()
L.save_sla(out + ".sla")
L.export_pdf(out + ".pdf", preset="x4")
RESULT = {"pages": scribus.pageCount(), "flowed_onto": len(added)}
```

- In facing documents, `margins=(l, r, t, b)` means (inside, outside, top, bottom), and
  the default masters are named "<Normal> left/right" in the UI language.
- `chr(0x1E)` is the automatic page number. It goes in a master-page frame.
- Keep headings with their text and avoid single lines at page tops: after `save_sla`,
  `L.paragraph_keeps(out + ".sla", keep_with_next=["Title"], orphans=2, widows=2)` and
  `L.reopen(out + ".sla")`, then `L.assert_clean()` again before exporting.
- A saddle-stitched booklet needs a multiple of 4 pages. The printer imposes it; deliver
  single pages in reading order.
- `verify --text story.txt` proves no text was lost (coverage of words with 4+ letters).

## 3. Product catalogue from CSV (image grid)

CSV columns: `sku,name,price,image,blurb`.

```python
import csv, sys, scribus
import scribus_lib as L

src, out = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(src, encoding="utf-8-sig")))
COLS, ROWS, M, GAP = 2, 3, 12, 6            # 6 products per A4 page
W, H = 210, 297
cw = (W - 2 * M - (COLS - 1) * GAP) / COLS
ch = (H - 2 * M - 10 - (ROWS - 1) * GAP) / ROWS   # 10 mm for the page header
per = COLS * ROWS
L.new_doc(W, H, margins=(M, M, M, M), pages=(len(rows) + per - 1) // per, bleed=3)
sans = L.font("Helvetica Neue Regular", "Arial Regular")
bold = L.font("Helvetica Neue Bold", "Arial Bold")
L.para_style("Name", bold, 12, 14)
L.para_style("Price", bold, 12, 14, align="right")
L.para_style("Blurb", sans, 8.5, 11)
L.para_style("Head", bold, 16, 18)
L.master("Cat", lambda: L.text_box(None, M, M, W - 2 * M, 8, [("Spring catalogue", "Head")]))
L.apply_master("Cat")
for i, r in enumerate(rows):
    page, slot = i // per + 1, i % per
    x = M + (slot % COLS) * (cw + GAP)
    y = M + 10 + (slot // COLS) * (ch + GAP)
    L.image_box(page, r["image"], x, y, cw, ch * 0.55)
    L.text_box(page, x, y + ch * 0.57, cw * 0.7, 7, [(r["name"], "Name")])
    L.text_box(page, x + cw * 0.7, y + ch * 0.57, cw * 0.3, 7, [("€ " + r["price"], "Price")])
    blurb = L.text_box(page, x, y + ch * 0.57 + 8, cw, ch * 0.43 - 8, [(r["blurb"], "Blurb")])
    L.fit_text(blurb, min_size=7)
L.assert_clean()
L.save_sla(out + ".sla")
L.export_pdf(out + ".pdf", preset="x4", marks=True)
RESULT = {"products": len(rows), "pages": scribus.pageCount()}
```

- One job builds every page. A Scribus run costs 2–5 s of startup, so never run once per
  row.
- `fit_text` shrinks a long blurb rather than letting it overflow. If it would go under
  7 pt, the job fails and you shorten the copy.
- `image_box` shows the whole photo (letterboxed). Pass `fit="cover"` to fill the
  frame and crop instead — better for photos, worse for products that must stay whole.

## 4. Certificates / one page per CSV row

```python
import csv, sys, scribus
import scribus_lib as L

src, out = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(src, encoding="utf-8-sig")))
L.new_doc(297, 210, margins=(20, 20, 20, 20), pages=len(rows))   # A4 landscape: just swap w/h
L.para_style("Big", L.font("Georgia Bold", "Times New Roman Bold"), 36, "auto", align="center")
L.para_style("Small", L.font("Georgia Regular", "Times New Roman Regular"), 14, 18, align="center")
gold = L.cmyk("Gold", 0, 20, 60, 20)
for p, r in enumerate(rows, start=1):
    L.rect(p, 10, 10, 277, 190, line=gold, line_width=3)
    L.text_box(p, 20, 50, 257, 12, [("Certificate of completion", "Small")])
    name = L.text_box(p, 20, 75, 257, 25, [(r["name"], "Big")], name="name_%d" % p)
    L.fit_text(name, min_size=20)
    L.text_box(p, 20, 115, 257, 20, [("%s — %s" % (r["role"], r["organisation"]), "Small")])
L.save_sla(out + ".sla")
L.export_pdf(out + ".pdf", preset="print")
RESULT = {"certificates": len(rows)}
```

- Landscape: swap the width and height. The `orientation` argument isn't needed with
  explicit sizes.
- Long names shrink (`fit_text`, automatic leading). Name frames you want to find again
  (`name="name_%d" % p`); default names are localized.
- For a designed background, place it first at the page size plus bleed:
  `L.image_box(p, "bg.png", -3, -3, 303, 216)`. Use PNG, JPEG or TIFF at ≥ 300 ppi. A
  PDF or EPS background needs Ghostscript (`brew install ghostscript`); without it the
  frame stays empty and `image_box` raises.

## 5. Badges, cards and labels (`badges.py`)

```bash
python3 $SC run <skill>/scripts/badges.py --strict -- --csv people.csv --out out/badges \
    --size 90x55 --paper 210x297 --fields "name:18:bold,role:11,organisation:10" \
    --accent 100,30,0,0 --logo logo.png --cut-guides
```

- **Grid**: as many as fit, centred on the sheet. 90×55 on A4 is 2×5 = 10 per page;
  `--gap 4` adds gutters for easier cutting.
- **Avery-style label sheets**: set `--size`, `--paper` and `--gap` to the label spec.
  The grid is centred, so check one printout against the sheet.
- **Long values** shrink to 60% of their size, then wrap to two lines. The `RESULT`
  `shrunk` list tells you which rows were affected.
- **Business cards**: `--size 85x55` (EU) or `--size 89x51` (US). For trimmed full-bleed
  cards, copy `badges.py` and give each card its own page with `bleed=3` (the N-up sheet
  has no per-card bleed).
- **Table tents / place cards**: one card per page, mirrored halves. Copy the job and
  rotate the top half's frames 180° with `scribus.rotateObject(180, name)`.

## 6. Exporting an existing .sla

```bash
python3 $SC inspect brochure.sla           # sizes, masters, fonts, images (MISSING flagged)
python3 $SC export brochure.sla -o brochure-x4.pdf --preset x4 --marks
python3 $SC verify brochure-x4.pdf --pdfx4 --trim 210x297 --bleed 3 --marks
python3 $SC render brochure-x4.pdf -o pages/
```

- `export` exits 1 when images are missing or fonts were substituted. Fix the inputs
  (install the font, relink the image), or use `--allow-problems` if the user accepts it.
- `--bleed 3` overrides a document that has no bleed set, but objects that don't extend
  into the bleed won't magically fill it. Look at the render's edges.
- For a batch of files, write a job that loops over them:
  `L.open_doc(p); L.export_pdf(...); scribus.closeDoc()`, with absolute paths
  (`closeDoc` moves the working directory to `~/Documents`).

## 7. Editing an existing .sla

Open it, change it with the API, save to a **new** file:

```python
import sys, scribus
import scribus_lib as L
L.open_doc(sys.argv[1])
for p in range(1, scribus.pageCount() + 1):
    for name in scribus.getAllObjects(page=p - 1):
        if scribus.getObjectType(name) == "TextFrame" and "2025" in scribus.getAllText(name):
            scribus.setText(scribus.getAllText(name).replace("2025", "2026"), name)
L.save_sla(sys.argv[2])
```

`setText` replaces the story and **loses local formatting** inside it, though paragraph
styles applied to the frame remain. For surgical edits, use `selectText` on the match
range and `insertText`/`deleteText`.
