# Filters and export options

Checked against the LibreOffice 26.8 Help pages (*PDF export command line parameters*,
*File conversion filter names*, *CSV filter options*, *Starting LibreOffice with
parameters*) and run live on 26.8.0.3.

## Export filter per document kind

`lo-convert.py --to EXT` and `store(doc, dst)` pick the filter from the document kind
and the output extension. Override it with `--filter NAME`.

| Kind | Extension → filter |
|---|---|
| Writer | `pdf` writer_pdf_Export · `odt` writer8 · `docx` MS Word 2007 XML · `doc` MS Word 97 · `rtf` Rich Text Format · `txt` Text (encoded) `UTF8,LF` · `html` HTML (StarWriter) · `epub` EPUB · `fodt` OpenDocument Text Flat XML · `png`/`jpg`/`svg` writer_*_Export (first page) |
| Calc | `pdf` calc_pdf_Export · `ods` calc8 · `xlsx` Calc MS Excel 2007 XML · `xls` MS Excel 97 · `csv` Text - txt - csv (StarCalc) · `html` HTML (StarCalc) · `fods` · `png`/`svg` calc_*_Export |
| Impress | `pdf` impress_pdf_Export · `odp` impress8 · `pptx` Impress MS PowerPoint 2007 XML · `ppt` MS PowerPoint 97 · `fodp` · `html` impress_html_Export · `png`/`jpg`/`svg` (first slide) |
| Draw | `pdf` draw_pdf_Export · `odg` draw8 · `fodg` · `png`/`jpg`/`svg` (first page) |

The Help pages also list `Office Open XML Text`, `Calc Office Open XML` and
`Impress Office Open XML`. Those write the ISO/strict flavour; the `MS … 2007 XML`
filters write what Microsoft Office itself writes, so the scripts use those.

Import filters are detected. Force one with `--infilter`, e.g.
`--infilter "Text (encoded):UTF8"` or `--infilter "Calc Office Open XML"`.

## PDF export FilterData (`--pdfa`, `--pdf-ua`, `--pdf-opt KEY=VALUE`)

`--pdf-opt` values are typed automatically: `true`/`false` → boolean, digits → integer,
anything else → string.

| Key | Type (default) | Notes |
|---|---|---|
| `SelectPdfVersion` | long (0) | 0 PDF 1.7 · 1 PDF/A-1b · 2 PDF/A-2b · 3 PDF/A-3b · 15/16/17 PDF 1.5/1.6/1.7. **4 = PDF/A-4** is not in the Help page but works: veraPDF PASS on 26.8. `--pdfa N` sets this. |
| `PDFUACompliance` | bool (false) | `--pdf-ua` sets it together with `UseTaggedPDF`. The *content* must be accessible too (alt text on images, a document title); validate with `verapdf --flavour ua1`. A report with an image lacking alt text fails UA-1, while its PDF/A-2b part passes. |
| `UseTaggedPDF` | bool (false) | structure tags |
| `PageRange` | string (all) | `1-3,5` |
| `ExportNotes` | bool (false) | comments as PDF annotations |
| `ExportNotesPages` / `ExportOnlyNotesPages` | bool (false) | Impress notes pages |
| `ExportHiddenSlides` | bool (false) | Impress |
| `ExportBookmarks` | bool (true) | outline from headings |
| `ExportFormFields` | bool (true) | fillable form fields |
| `Quality` | long (90) | JPEG quality 1–100 |
| `ReduceImageResolution` / `MaxImageResolution` | bool (false) / long (300) | 75, 150, 300, 600, 1200 |
| `EncryptFile` / `DocumentOpenPassword` | bool / string | not allowed with PDF/A |
| `Watermark` | string | also `WatermarkColor`, `WatermarkFontHeight`, `WatermarkRotateAngle`, `WatermarkFontName`, `TiledWatermark` |
| `SinglePageSheets` | bool (false) | Calc: each sheet on one page |
| `IsSkipEmptyPages` | bool (false) | Writer |

Checked live: PDF/A-1b, 2b, 3b and 4 pass veraPDF. `Watermark=DRAFT` with
`EncryptFile=true`/`DocumentOpenPassword=pw` gives a file that `pdfinfo` refuses without
the password and whose text contains `DRAFT`.

## Raw `--convert-to` syntax (outside the scripts)

```bash
soffice -env:UserInstallation=file:///tmp/lo-profile --headless \
  --convert-to 'pdf:writer_pdf_Export:{"SelectPdfVersion":{"type":"long","value":"2"}}' \
  --outdir out/ in.docx
```

The JSON form: each key is `{"type": "long|boolean|string", "value": "<as string>"}`.
Always pass a private `-env:UserInstallation`. Never judge the result by the exit code,
because it is 0 even for a missing input.

## CSV (`Text - txt - csv (StarCalc)`) FilterOptions

A comma-separated token list, in this order:

1. Field separator: ASCII code (`44` comma, `59` semicolon, `9` tab); `/` joins several; `FIX` for fixed width
2. Text delimiter (`34` = `"`)
3. Character set (`76` = UTF-8, or a name such as `UTF8` or `ANSI`)
4. First line to import (import)
5. Column formats (import), `col/format/…` (1 standard, 2 text, 3 MM/DD/YY, 5 YY/MM/DD, 9 skip)
6. Language (`1033` = en-US); decides the decimal mark on import
7. Quoted field as text
8. Detect special numbers (import); keep numbers as numbers (export)
9. Save cell contents as shown (export, default true: formatted values)
10. Export cell formulas
11. Remove spaces (import)
12. Sheet to export: `0` the first/current, `N` the Nth, **`-1` every sheet to `<name>-<Sheet>.csv`**
13. Evaluate formulas (import)
14. Include BOM (export)

The scripts export with `44,34,76,1,,1033,false,true,false,false`: comma, UTF-8 and
raw values. `lo-convert.py --to csv --all-sheets` appends token 12 = `-1`.

**The decimal mark on export follows the profile's locale setting, not token 6.** Under
a hu-HU profile, every option combination wrote `"1,5"`. The skill pins its profile to
en-US (`LO_LOCALE`), which gives `1.5`.
