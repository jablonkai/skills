---
name: libreoffice
description: 'Automate documents with a real office engine: headless LibreOffice and its UNO API. Batch-convert between ODF, OOXML (docx/xlsx/pptx), legacy doc/xls/ppt, RTF and PDF including PDF/A; fill a Calc model from CSV, recalculate every formula and export xlsx/ods/PDF with the computed values, or read real recalculated values; fill Writer templates ({{placeholders}}, fields, bookmarks) into one file per record or a combined PDF; export Impress/Draw pages as PNG/SVG. Use whenever a task would run soffice or LibreOffice, or needs rendering fidelity, recalculation or ODF: "convert this folder of docx to PDF/A", "recalculate this xlsx and give me the real totals", "generate letters from this template and CSV", "export every slide as PNG", "convert legacy .doc files", or Hungarian "konvertáld PDF/A-ra a docx fájlokat". Not for editing docx/xlsx/pptx in Python without an office engine (use docx, xlsx, pptx), documents to Markdown (use markitdown), PDF merging or OCR (use pdf), or Pages, Numbers and Keynote files.'
summary: "automate documents with headless LibreOffice and UNO — ODF/OOXML/PDF and PDF/A batch conversion, Calc recalculation with real values, Writer template fill and mail merge, Impress/Draw page export"
category: document-conversion
risk: low
tags:
    - libreoffice
    - soffice
    - uno
    - pdf-a
    - docx
    - xlsx
    - odf
    - mail-merge
---

# LibreOffice Automation

Every call is one short **headless `soffice` process on the skill's own profile**. The
scripts run [scripts/lo_ops.py](scripts/lo_ops.py) *inside* LibreOffice as a Python macro
(UNO API), pass the request as a private JSON file, and read a JSON result back. Nothing
listens on a port or pipe, and the user's own LibreOffice window and profile are never
touched. Verified against **LibreOffice 26.8.0.3** on macOS 27; the scripts also find
`soffice` on Linux.

Use the scripts rather than raw `soffice --convert-to`. They encode fixes for behaviour
that looks right but isn't (see Pitfalls). For anything they don't cover (formatting,
charts, building documents or decks, tracked changes, native mail merge), run a UNO
snippet in the same sandboxed instance with `python3 scripts/lo_run.py --script my.py
--arg '{…}'`. Tested snippets are in [references/recipes.md](references/recipes.md).

| Script | Does |
|---|---|
| `bash scripts/lo.sh --check` | soffice path, version, profile, poppler/veraPDF, running instances. Run first. |
| `python3 scripts/lo-convert.py SRC... --to FMT` | files or folders (`-r`, mirrored) to pdf, PDF/A, docx, odt, xlsx, pptx, … |
| `python3 scripts/lo-calc.py read FILE` | sheets, **recalculated** values, formula errors |
| `python3 scripts/lo-calc.py fill FILE --csv … -o OUT…` | write data/cells/formulas, recalculate, export |
| `python3 scripts/lo-merge.py TEMPLATE DATA …` | Writer template × records → a file per record or one combined PDF |
| `python3 scripts/lo-export-pages.py SRC --out-dir D` | every slide/page as PNG, JPG or SVG |
| `python3 scripts/lo-verify.py FILE …` | PASS/FAIL checks: pages, PDF/A, fonts, text, cell values, errors |
| `python3 scripts/lo_run.py --script F.py --arg JSON` | run your own UNO snippet in the headless instance |
| `bash scripts/lo.sh --stop` | kill leftover skill `soffice` processes (stop path) |

All scripts are standard-library Python on the system `python3` (3.9+). They exit
non-zero on failure, and most take `--json`. A call takes about 2 s to start, so batch
work into one command (lo-convert does 20 files per `soffice`).

## Workflow

1. `bash scripts/lo.sh --check`. If LibreOffice is missing: `brew install --cask libreoffice`.
   Poppler (`pdfinfo`/`pdffonts`/`pdftotext`/`pdftoppm`/`pdfunite`) and veraPDF are
   optional, but needed for PDF checks, Writer/Calc page images and some combined merges.
2. Inspect inputs you didn't write: `lo-calc.py read`, or `lo-merge.py TEMPLATE --list`.
3. Run the conversion, fill, merge or export.
4. **Verify the outputs** with `lo-verify.py`, not the exit code alone (below). To check
   the look, render pages with `lo-export-pages.py` and Read the PNGs.

## Convert

```bash
S=scripts
python3 $S/lo-convert.py report.docx --to pdf
python3 $S/lo-convert.py ~/Contracts -r --to pdf --pdfa 2 --out-dir ~/Contracts-pdfa
python3 $S/lo-convert.py deck.pptx --to odp --out /tmp/deck.odp
python3 $S/lo-convert.py old/ --to docx --ext doc,rtf
python3 $S/lo-convert.py book.odt --to pdf --update-indexes --pdf-opt PageRange=1-3
```

- `--pdfa 1|2|3|4` gives PDF/A-1b, 2b, 3b or 4; all four passed veraPDF. `--pdf-ua` adds
  tagging for accessibility. Any other export option goes through `--pdf-opt KEY=VALUE`
  ([references/filters.md](references/filters.md)).
- Each source's container is checked first. **A corrupt or mislabelled file is reported as
  FAIL, not converted.** LibreOffice itself would import it as plain text and "succeed".
  Tell the user which files failed and why.
- Folder runs skip hidden files, `~$…` Word owner files and `.~lock…#` files. The tree is
  mirrored under `--out-dir`; without it, outputs land next to their sources. Existing
  outputs are skipped unless `--force`, and an output that would collide is refused.
- `--to csv` writes the first sheet as comma-separated UTF-8 with `.` decimals and computed
  values (not formulas, not display formatting). `--all-sheets` writes one
  `<name>-<Sheet>.csv` per sheet. Rename the files afterwards if the user wants bare sheet
  names.
- The target must suit the document kind: a spreadsheet can't become `.docx`. `png`/`svg`
  here renders the first page only; use lo-export-pages for every page.
- Fonts that aren't installed are **substituted**, and the substitute gets embedded. The
  PDF is still valid PDF/A, but its layout can differ from Word's. `pdffonts` shows which
  font was used; mention a substitution when fidelity matters.

## Calc: fill, recalculate, read

```bash
python3 $S/lo-calc.py read model.xlsx                              # sheets, errors
python3 $S/lo-calc.py read model.xlsx --range Summary.B1:B9 --formulas
python3 $S/lo-calc.py fill model.xlsx --csv data.csv --at Data.A2 --skip-header \
  --clear Data.A2:F1000 -o out.xlsx -o out.pdf --read Summary.B1:B9
python3 $S/lo-calc.py fill model.xlsx --set Inputs.B2=0.21 --set-text Inputs.B3=007 \
  --formula "Summary.C9==SUM(C2:C8)" -o model-2.ods
```

- **Everything is recalculated.** An xlsx stores cached results, which may be stale (and
  openpyxl-written files have none); Calc trusts them on load. The scripts always run
  `calculateAll()`. `read --no-recalc` shows what the file had cached.
- The source is never modified; results go to `-o` files (xlsx, ods, xls, pdf, csv, html).
  Write the updated workbook as a new file and say where it is.
- CSV is parsed in Python, not by Calc's locale: `"1,250"` → 1250, `12%` → 0.12, while
  `007` and `1,5` stay text. Options: `--decimal , --thousands .`, `--delimiter`, and
  `--iso-dates` (YYYY-MM-DD → date serial). Empty CSV cells clear the cell. A CSV cell
  starting with `=` stays text unless `--csv-formulas`.
- `--clear` the old data range when the new data may have fewer rows than the old.
- Formulas take **Excel syntax** (`=SUM(Data!B2:B9,C1)`). `--native-formulas` takes
  Calc's syntax (`=SUM($Data.B2:B9;C1)`). Formulas read back in Calc syntax with English
  function names.
- `fill` and `read` exit 1 when any formula in the workbook evaluates to an error, and
  list the cells (`Summary.B4  #DIV/0!  =1/0`). `fill --allow-errors` exits 0 when the
  errors were already in the template; report them anyway.
- Cell references: `Sheet.A1`, `Sheet!A1`, `'My sheet'.A1:B4`, a named range, or `A1` on
  the first sheet.

## Writer: templates and mail merge

```bash
python3 $S/lo-merge.py letter.docx --list          # placeholders, fields, bookmarks
python3 $S/lo-merge.py letter.docx people.csv --out-dir letters --to pdf --name "{n:02}-{name}"
python3 $S/lo-merge.py letter.odt people.csv --combined all.pdf --no-per-record
python3 $S/lo-merge.py invoice.ott rows.json --out-dir out --to pdf,docx --pdfa 2
```

- Fill targets are matched by column name:
  - `{{column}}` placeholders anywhere: body, tables, headers, footers, frames
  - user fields named `column`
  - bookmarks named `column`
  - mail-merge (database) fields for that column, and input fields whose hint is the column
- Run `--list` first and compare it with the data's columns. A placeholder without a
  column stops the run before anything is written; `--allow-unfilled` overrides that.
  Unused columns are reported.
- Values go in as plain text. The template is opened as a copy and never saved.
- `--combined` puts every record in one file, each starting on a new page. When the
  header or footer holds a fill target, the combined PDF is joined from per-record PDFs
  with `pdfunite`. That PDF isn't PDF/A, so combining it with `--pdfa` is refused.

## Slides and drawings to images

```bash
python3 $S/lo-export-pages.py deck.pptx --out-dir slides --width 1920
python3 $S/lo-export-pages.py deck.odp --out-dir slides --pages 1,3-5 --format svg
python3 $S/lo-export-pages.py report.docx --out-dir pages --dpi 150   # via PDF + pdftoppm
```

Impress and Draw pages render one by one; hidden slides are skipped unless
`--include-hidden`. For PDF output use lo-convert (`--pdf-opt ExportNotesPages=true` adds
the notes pages).

## Verify

```bash
python3 $S/lo-verify.py out.pdf --pdfa 2B --fonts-embedded --pages 3 --verapdf
python3 $S/lo-verify.py out.pdf --contains "Kovács Ágnes" --not-contains "{{"
python3 $S/lo-verify.py out.xlsx --expect 'Summary!B4=1935' --formula 'Summary!B4' --no-errors
python3 $S/lo-verify.py out.ods --expect Summary.B4=1935 --no-errors
```

For xlsx, `--expect` checks the **cached** values in the file, which is what Excel,
openpyxl and viewers show. `--recalc` checks Calc's own result instead.

## Pitfalls (all measured on 26.8)

- **Exit codes lie.** `soffice --convert-to` exits 0 for a missing input and for a
  corrupt file it rendered as text. Judge success by the checked outputs.
- **One profile, one process.** A second `soffice` on the same profile hands its command
  line to the first. The skill uses its own profile, locks it per call and refuses to
  start while a leftover runs: then run `lo.sh --stop`.
- **Edit an opened file only via `as_template=True`** in a snippet. A `ReadOnly` document
  takes value writes but silently drops formatting, and a plain load leaves a
  `.~lock.<name>#` file next to the user's file.
- **The locale is pinned to en-US** on the skill profile (`LO_LOCALE=hu-HU` to change).
  Otherwise it follows the system: CSV exports `1,5`, shown values `1370,5`, errors
  `#ZÉRÓOSZTÓ!`, and new TOC and style names come out in Hungarian. An error cell reads
  as 0 over UNO, which is why errors are checked separately.
- **Headless can't answer dialogs.** A password-protected source fails to load (pass
  `--password`); nothing ever waits for a click.
- **macOS: don't run the bundled `…/Contents/Resources/python`.** Once it writes `.pyc`
  files into its signed framework, macOS kills it on every start, and `lo.sh --check`
  reports that. The skill never uses it; scripts run inside `soffice` with bytecode
  writing off.

More pitfalls, with the reasons behind the scripts' choices:
[references/gotchas.md](references/gotchas.md). UNO services and calls:
[references/uno-api.md](references/uno-api.md). Filter names and options:
[references/filters.md](references/filters.md).

## Safety

- Nothing listens: no socket, no pipe, no port, so there's nothing for another process
  or a web page to reach.
- Input documents load hidden, with **macro execution off** (`MacroExecutionMode`
  NEVER) and **link updates off**, so macros and external links in files never run.
- Sources are never written. Outputs are new files; an existing one is replaced only with
  `--force`. Values reach LibreOffice through a JSON request file (mode 600, deleted
  after the call), never spliced into code.
- Stop path: every call ends at `LO_TIMEOUT` (default 300 s), and the driver kills the
  process group it started. `lo.sh --stop` kills leftovers on the skill profile only.
  `lo.sh --reset-profile` also deletes that profile.
- A `--password` shows in the process arguments of the Python script, not of `soffice`.
