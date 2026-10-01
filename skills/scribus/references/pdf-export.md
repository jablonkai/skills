# PDF export from the scripter

`scribus.PDFfile()` mirrors the File › Export › Save as PDF dialog. It starts from the
document's last-used PDF settings, so set every attribute that matters instead of
relying on defaults. `L.export_pdf()` does that for the common presets.

## Version codes (`pdf.version`), measured on 1.6.6

| Code | Output | `GTS_PDFXVersion` |
|---|---|---|
| 10 | PDF/X-4, PDF 1.6 | `PDF/X-4` |
| 11 | PDF/X-1a, PDF 1.3 | `PDF/X-1:2001` |
| 12 | PDF/X-3, PDF 1.3 | `PDF/X-3:2002` |
| 13 / 14 / 15 / 16 | PDF 1.3 / 1.4 / 1.5 / 1.6 | — |

- The PDF/X versions require `outdst = 1` (print) and an output profile (`printprofc`).
- The bundled default output profile is **ISO Coated v2 300% (basICColor)**, which suits
  European sheet-fed offset on coated stock. If the printer names another profile
  (for example PSO Uncoated or GRACoL), install the ICC file in a folder Scribus scans
  (Preferences › Paths › ICC Profiles, or `~/Library/ColorSync/Profiles`) and set
  `pdf.printprofc = "<profile description>"`.
- PDF/X-1a and X-3 forbid transparency, so Scribus flattens it or refuses. PDF/X-4 keeps
  live transparency.

## Attributes worth setting

| Attribute | Meaning |
|---|---|
| `file` | Output path (absolute). |
| `pages` | List of 1-based page numbers; the default is all. |
| `version`, `outdst` | See above. `outdst`: 0 screen/RGB, 1 printer. |
| `fontEmbedding` | 0 embeds (subset), 1 outlines, 2 none. Use 0. |
| `subsetList`, `fonts` | Per-font subset/embed lists. Rarely needed. |
| `resolution` | Target ppi for images when downsampling (default 300). |
| `downsample` | 0 = off; otherwise the ppi to downsample to. |
| `compress`, `compressmtd`, `quality` | Image compression: `compressmtd` 0 auto, 1 JPEG, 2 zip, 3 none; `quality` 0 max … 4 min. |
| `useDocBleeds` | True = use the `setBleeds` values; False = use `bleedt/bleedl/bleedr/bleedb` (doc unit). |
| `cropMarks`, `bleedMarks`, `registrationMarks`, `colorMarks`, `docInfoMarks` | Printer marks. |
| `markOffset`, `markLength` | The marks' distance from the trim and their length (doc unit). |
| `printprofc` | Output-intent ICC profile name. |
| `solidpr`, `imagepr`, `profilei`, `profiles`, `intents`, `intenti`, `noembicc` | Source profiles and rendering intents for solids and images. |
| `info` | The PDF/X Info string (title). PDF/X needs one; Scribus fills it if empty. |
| `isGrayscale`, `usespot` | Grayscale output; keep spot colours as separations. |
| `mirrorH`, `mirrorV`, `rotateDeg` | Page transforms, for imposition only. |
| `thumbnails`, `bookmarks`, `article`, `useLayers` | Screen-PDF niceties. |
| `encrypt`, `owner`, `user`, `allowPrinting`… | Security. Not allowed in PDF/X. |

## Boxes, bleed and marks

With `useDocBleeds` and 3 mm bleed on an A5 page, measured:

- **TrimBox** = 148 × 210 mm, the finished size.
- **BleedBox** = TrimBox + 3 mm each side.
- **MediaBox** = BleedBox + room for the marks when any marks are on. Without marks,
  the MediaBox equals the BleedBox.

Objects meant to bleed must extend past the trim by the full bleed. Shorter objects leave
a white sliver when the guillotine drifts. Text and logos stay inside a safe zone, at
least 3–5 mm inside the trim.

## Checking the PDF

`scribus.py verify` reads boxes with `pdfinfo -box`, fonts with `pdffonts`, images with
`pdfimages -list`, text with `pdftotext`, and the PDF/X marker and OutputIntent from the
raw file. veraPDF (1.30) validates PDF/A and PDF/UA only, so it cannot certify PDF/X.
When the printer insists on a validated file, their preflight (or Acrobat Preflight /
callas pdfToolbox) is the authority.

## Other outputs

- `scribus.savePageAsEPS(path)`: the current page as EPS.
- `scribus.ImageExport()`: page to PNG/JPEG/TIFF.

  ```python
  img = scribus.ImageExport()
  img.type = "PNG"; img.dpi = 150; img.scale = 100
  img.name = "/abs/page1.png"
  img.save()                # current page; saveAs(name) also exists
  ```

  Rendering the exported PDF with `scribus.py render` (poppler) is simpler, and it shows
  exactly what the printer gets.
