"""Job: N-up badges / cards / labels from a CSV, laid out on sheets.

Run through the runner (arguments after ``--``):

  scribus.py run badges.py -- --csv people.csv --out out/badges \\
      [--size 90x55] [--paper 210x297] [--gap 0] \\
      [--fields "name:18:bold,role:11,organisation:10"] \\
      [--logo logo.png] [--accent 100,60,0,0] [--cut-guides] [--marks] [--preset x4]

- One badge per CSV row, in row order, filling each sheet left-to-right, top-to-bottom.
  The grid is as many badges as fit inside the sheet, centred.
- ``--fields``: CSV column[:size_pt[:bold]], stacked top to bottom, centred. A value
  that is too long shrinks (down to 60%), then wraps to two lines; a badge that still
  cannot hold its text fails the job instead of overflowing.
- Writes ``<out>.sla`` and ``<out>.pdf``; RESULT has counts and any shrunk values.
"""
import argparse
import csv
import os

import scribus

import scribus_lib as L

ap = argparse.ArgumentParser()
ap.add_argument("--csv", required=True)
ap.add_argument("--out", required=True, help="output path without extension")
ap.add_argument("--size", default="90x55", help="badge WxH in mm")
ap.add_argument("--paper", default="210x297", help="sheet WxH in mm")
ap.add_argument("--gap", type=float, default=0.0, help="mm between badges")
ap.add_argument("--fields", default="name:18:bold,role:11,organisation:10")
ap.add_argument("--logo")
ap.add_argument("--accent", help="C,M,Y,K percentages for a top band")
ap.add_argument("--padding", type=float, default=5.0)
ap.add_argument("--cut-guides", action="store_true", help="hairline outline per badge")
ap.add_argument("--marks", action="store_true")
ap.add_argument("--preset", default="x4")
ap.add_argument("--regular", default="Helvetica Neue Regular,Arial Regular,DejaVu Sans Book")
ap.add_argument("--bold", default="Helvetica Neue Bold,Arial Bold,DejaVu Sans Bold")
a = ap.parse_args()

bw, bh = (float(v) for v in a.size.lower().split("x"))
pw, ph = (float(v) for v in a.paper.lower().split("x"))
cols = int((pw + a.gap) // (bw + a.gap))
rows = int((ph + a.gap) // (bh + a.gap))
if cols < 1 or rows < 1:
    raise L.LayoutError("a %gx%g badge does not fit on a %gx%g sheet" % (bw, bh, pw, ph))
per_page = cols * rows
x0 = (pw - (cols * bw + (cols - 1) * a.gap)) / 2
y0 = (ph - (rows * bh + (rows - 1) * a.gap)) / 2

with open(a.csv, encoding="utf-8-sig", newline="") as fh:
    records = list(csv.DictReader(fh))
if not records:
    raise L.LayoutError("no rows in %s" % a.csv)
fields = []
for spec in a.fields.split(","):
    parts = spec.strip().split(":")
    col = parts[0]
    if col not in records[0]:
        raise L.LayoutError("column %r not in CSV (have %s)" % (col, list(records[0])))
    fields.append((col, float(parts[1]) if len(parts) > 1 else 11.0,
                   len(parts) > 2 and parts[2] == "bold"))

pages = (len(records) + per_page - 1) // per_page
L.new_doc(pw, ph, margins=(0, 0, 0, 0), pages=pages)
regular = L.font(*a.regular.split(","))
bold = L.font(*a.bold.split(","))
for i, (col, size, is_bold) in enumerate(fields):
    L.para_style("F%d" % i, bold if is_bold else regular, size, "auto", align="center")
accent = L.cmyk("Accent", *(float(v) for v in a.accent.split(","))) if a.accent else None
band = 8.0 if accent else 0.0
logo_h = 12.0 if a.logo else 0.0

shrunk = []
for n, rec in enumerate(records):
    page = n // per_page + 1
    slot = n % per_page
    bx = x0 + (slot % cols) * (bw + a.gap)
    by = y0 + (slot // cols) * (bh + a.gap)
    if accent:
        L.rect(page, bx, by, bw, band, fill=accent)
    if a.cut_guides:
        L.rect(page, bx, by, bw, bh, line="Black", line_width=0.1)
    top = by + band + a.padding
    if a.logo:
        L.image_box(page, a.logo, bx + a.padding, top, bw - 2 * a.padding, logo_h)
        top += logo_h + 2
    # Stack the lines, then centre the stack in the remaining area. A value too long
    # for one line even at 60% size gets a second line before giving up.
    frames, y = [], top
    for i, (col, size, _) in enumerate(fields):
        value = (rec.get(col) or "").strip()
        line = size * 1.3 * 25.4 / 72
        if not value:
            y += line
            continue
        f = L.text_box(page, bx + a.padding, y, bw - 2 * a.padding, line, [(value, "F%d" % i)])
        try:
            final = L.fit_text(f, min_size=size * 0.6)
        except L.LayoutError:
            line = 2 * (size * 0.8) * 1.3 * 25.4 / 72
            scribus.sizeObject(bw - 2 * a.padding, line, f)
            final = L.fit_text(f, min_size=size * 0.6, start=size * 0.8)
        if final < size:
            shrunk.append({"row": n + 1, "field": col, "value": value, "pt": final})
        frames.append(f)
        y += line
    avail = by + bh - a.padding - top
    if y - top > avail + 0.01:
        raise L.LayoutError("row %d does not fit a %gx%g badge (needs %.1f mm, has %.1f)"
                            % (n + 1, bw, bh, y - top, avail))
    for f in frames:
        scribus.moveObject(0, (avail - (y - top)) / 2, f)

sla = L.save_sla(a.out + ".sla")
pdf = L.export_pdf(a.out + ".pdf", preset=a.preset, marks=a.marks)
RESULT = {"badges": len(records), "per_page": per_page, "grid": [cols, rows],
          "pages": pages, "sla": sla, "pdf": pdf, "shrunk": shrunk,
          "fonts": [regular, bold], "csv": os.path.abspath(a.csv)}
