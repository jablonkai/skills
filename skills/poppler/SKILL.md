---
name: poppler
description: 'Work on PDFs fast from the command line with poppler (pdfinfo, pdffonts, pdftotext, pdfimages, pdftoppm, pdftocairo, pdfseparate, pdfunite) and qpdf: extract page ranges or every n-th page, merge files in a given order, reorder, rotate and remove pages, split into single pages or chunks, extract text with layout or word boxes, pull embedded images out in their original format, render pages to PNG/JPEG/SVG at a chosen DPI, add or remove passwords, linearise for the web, check and repair damaged files, and report page count, page sizes, fonts (embedded or not) and metadata, every output checked by qpdf --check. Use for "merge these PDFs but only pages 1-3 of the second", "render page 2 at 300 DPI", "extract all images from this PDF", "password-protect this PDF", "which fonts are not embedded", "this PDF is corrupted, fix it". Not for PDF to Markdown (markitdown), Office to PDF or PDF/A (libreoffice), creating PDFs or filling forms in Python (pdf), OCR or redaction (pdfcraft), or when the user names PdfCraft.'
summary: "split, merge and inspect PDFs with the poppler and qpdf CLIs — page extract, reorder, rotate and remove, text with layout, original-format image extraction, DPI page renders, password add and remove, linearise and repair, qpdf --check verified"
category: document-conversion
compatibility: "Built for poppler 26.10.0 and qpdf 12.4.2 (Homebrew) on macOS 27.2; Python 3.9+ for the helper scripts. Also runs with poppler-utils and qpdf on Linux."
risk: low
tags: [pdf, poppler, qpdf, pdftotext, pdfimages, pdftoppm, merge, split, encryption]
license: GPL-3.0-only
metadata:
  version: "1.0.0"
  author: "Tamás Jablonkai"
---

# PDF work with poppler and qpdf

Headless command-line tools only: no app, no bridge. Each operation is one short
process. poppler reads and renders, qpdf rewrites structure (pages, encryption,
linearisation, repair). The bundled scripts wrap both. They pick the right tool for each
job, keep passwords off the command line, and **check every output**: `qpdf --check`,
page count, text or pixel size. Verified against **poppler 26.10.0** and **qpdf 12.4.2**
on macOS 27.2.

```sh
S=<this skill>/scripts
bash $S/pdf.sh --check        # poppler + qpdf paths and versions; exit 1 names what to install
```

Missing tools: `brew install poppler qpdf` (Debian/Ubuntu: `apt install poppler-utils qpdf`).

## Scripts

Every script prints a JSON report with `"ok"` and exits 0 only when its own checks pass.
Read the report: it is your verification, not decoration.

| Script | Does |
|---|---|
| `pdf_inspect.py FILE_OR_DIR… [--json]` | pages, page sizes (pt, mm, paper name, by page group), fonts with embedded/subset flags, metadata, encryption, linearised, tagged, `qpdf --check` |
| `pdf_pages.py merge OUT a.pdf b.pdf:1-3 c.pdf` | merge in the given order, with an optional range per file |
| `pdf_pages.py select IN OUT --pages R` / `--every N [--start K]` | keep pages in range order / every N-th page |
| `pdf_pages.py remove IN OUT --pages R` | delete pages |
| `pdf_pages.py reorder IN OUT --order "3,1,2,4-z"` | reorder (`z-1` reverses); reports any pages left out |
| `pdf_pages.py rotate IN OUT --angle +90 [--pages R]` | rotate; `+90`/`-90` relative, bare `90` absolute |
| `pdf_pages.py split IN OUTDIR [--size N]` | one file per page or per N pages |
| `pdf_extract.py text IN [OUT\|-] [--pages R] [--mode layout\|raw\|plain\|bbox]` | text, layout kept by default; pages separated by form feeds; `bbox` gives word boxes as XHTML |
| `pdf_extract.py images IN OUTDIR [--pages R] [--drop-smasks]` | embedded images in their **native** format, sizes checked against `pdfimages -list` |
| `pdf_extract.py render IN OUTDIR [--pages R] [--dpi 300] [--format png\|jpeg\|tiff\|svg\|pdf]` | `PREFIX-<page>.<ext>`, pixel size checked against page size × DPI |
| `pdf_secure.py encrypt IN OUT --user-password-file F [--owner-password-file F] [--no-print --no-modify --no-copy]` | AES-256; verifies the result needs the password |
| `pdf_secure.py decrypt IN OUT --password-file F [--compare-to ORIG]` | removes the password; verifies text and pages are unchanged |
| `pdf_secure.py linearize IN OUT` / `repair IN OUT` | fast web view / rebuild a damaged xref, both re-checked |
| `pdf_compare.py A B [--pages-a R] [--pages-b R] [--ignore-rotation]` | the oracle: page count, sizes, rotation and normalised text, page by page; exit 0 = identical |

`R` is qpdf page-range syntax: `1,3,5-7`, `z` = last page, `r2` = second from last,
`5-1` counts down, `1-z,x3-4` excludes, a trailing `:odd`/`:even` keeps every other
page *of the selection*. The scripts expand ranges themselves and report the exact
pages they used. Pass that list back to the user.

## Recipes

```sh
# merge, keeping only pages 1-3 of the second file, then prove it
python3 $S/pdf_pages.py merge out.pdf a.pdf b.pdf:1-3 c.pdf
python3 $S/pdf_compare.py out.pdf b.pdf --pages-a 5-7 --pages-b 1-3   # a.pdf has 4 pages

# every 3rd page from page 2; rotate the first of them; linearise
python3 $S/pdf_pages.py select in.pdf sel.pdf --every 3 --start 2
python3 $S/pdf_pages.py rotate sel.pdf rot.pdf --angle +90 --pages 1
python3 $S/pdf_secure.py linearize rot.pdf web.pdf

# page 2 at 300 DPI plus its text with the column layout kept
python3 $S/pdf_extract.py render report.pdf out --pages 2 --dpi 300        # out/page-2.png
python3 $S/pdf_extract.py text report.pdf out/page-2.txt --pages 2

# all embedded images in their original encoding
python3 $S/pdf_extract.py images doc.pdf images/

# encrypt, then decrypt and prove nothing changed
printf '%s\n' "$PASSWORD" > pw.txt && chmod 600 pw.txt     # or --user-password-env VAR
python3 $S/pdf_secure.py encrypt doc.pdf locked.pdf --user-password-file pw.txt
python3 $S/pdf_secure.py decrypt locked.pdf open.pdf --password-file pw.txt --compare-to doc.pdf
```

`encrypt` without an owner password generates a random one. It is saved to
`OUT.owner-password.txt` (0600), because an empty or identical owner password is
insecure. Tell the user where that file is.

For anything the scripts don't wrap (overlays/watermarks with `qpdf --overlay`,
attachments, `qpdf --json` queries, `pdftocairo` PostScript/EPS, `pdftotext -tsv`),
use the tools directly: [references/recipes.md](references/recipes.md). Flags by tool:
[references/cli-reference.md](references/cli-reference.md).

## Verify before you report

- **Read the script's JSON report.** `ok: false`, a page count that differs from
  `expected_pages`, or `check: errors` means the job isn't done.
- After a hand-written qpdf or poppler command, verify the same way:
  `qpdf --check OUT` (exit 0 ok, **3 = warnings, still usable**, 2 = errors),
  `qpdf --show-npages OUT`, and `pdf_compare.py` against the source pages.
- For text extraction, an empty page means the page is a scan with no text layer. Say
  so; OCR isn't part of this skill (pdfcraft or `ocrmypdf` do it).
- Never overwrite an input. The scripts refuse unless `--in-place` is given.

## Pitfalls that look right but aren't

Full list with explanations: [references/gotchas.md](references/gotchas.md).

- **Passwords on argv** are visible to every process (`ps`) and land in shell history.
  poppler only accepts them as `-upw`/`-opw`. The scripts decrypt to a private temp copy
  and give qpdf the password through a 0600 `@argfile`. Do the same by hand
  (`--password-file=F`, or `@args.txt`).
- **`pdfunite`** drops outlines, links and form fields and refuses encrypted input. Merge
  with `qpdf --empty --pages a.pdf b.pdf 1-3 -- out.pdf` (what `merge` does).
- **`pdfimages -j`** keeps only JPEG and re-encodes everything else. `-all` keeps every
  native format. A transparent image comes out as **two files**: the colour image and
  its soft mask (`smask`) as a separate gray PNG. Report images, not files.
- **`pdftoppm` file names** are zero-padded to the page count (`-02.png` in a 10+-page
  file). Use `-singlefile` per page for a predictable name (what `render` does).
- **Pixel size** is `ceil(points × DPI / 72)`. A4 at 300 DPI is 2481 × 3508, not
  2480 × 3508. A page with `/Rotate 90` renders with width and height swapped.
- **`:odd`/`:even`** in qpdf ranges act on the *selection*, not on original page
  numbers, and qpdf has **no every-n-th syntax** for n > 2 (use `select --every N`).
- **Owner-password-only files** open without a password and decrypt without one. They
  only carry permission flags, which aren't real protection. Say so if the user thinks
  the file is locked.
