# Gotchas

Every item was reproduced on LibreOffice 26.8.0.3 (macOS 27, system locale hu-HU)
unless noted. Each one says what the scripts do about it.

## Process and profile

- **`--convert-to` exit codes are meaningless.** `soffice --convert-to pdf missing.docx
  bad.docx` exits 0: it prints `Error: source file could not be loaded` for the missing
  file and imports the corrupt `.docx` **as plain text**, producing a PDF of its bytes.
  → lo-convert checks each file's container against its extension first. It reports the
  import filter, and fails a document LO could only read as `Text`.
- **One profile = one process.** A second `soffice` started on a profile that is in use
  hands its command line to the running instance and exits. A stray instance then
  swallows every later call. → Each call locks the profile, and refuses to start while a
  leftover runs (`lo.sh --stop`).
- **soffice stays alive while a document is open.** After a macro returns, headless
  soffice exits only if no component is open. A macro that raised with a document open
  hung until killed. → `lo_ops.main` closes everything left open; the driver's timeout
  kills the process group.
- **The user's LibreOffice window is safe.** With the GUI open on a document, skill
  calls ran on their own profile, and `lo.sh --stop` left the GUI process alone.
- **The locale follows the system unless pinned.** Under hu-HU:
  - shown values read `1370,5` and errors `#ZÉRÓOSZTÓ!`
  - CSV export wrote `"1,5"` whatever the CSV language token said
  - a new table of contents was titled "Tartalomjegyzék", and style display names were
    Hungarian

  → The skill profile pins `UILocale` and `ooSetupSystemLocale` to `LO_LOCALE`
  (default en-US). Writing `ooLocale` alone doesn't work, because LO rewrites it at
  start from `UILocale`.
- **The macOS bundled Python dies.** `LibreOffice.app/Contents/Resources/python` exits
  137 (SIGKILL) at once when `codesign --verify` reports
  `LibreOfficePython.framework: a sealed resource is missing or invalid`. The listed
  files were `__pycache__/*.pyc`, written into the signed framework by an earlier run of
  that interpreter. External UNO clients (`import uno` outside soffice) are therefore
  unreliable on macOS. → The skill runs its code *inside* soffice with
  `PYTHONDONTWRITEBYTECODE=1`, which added no `.pyc` files. `lo.sh --check` reports the
  broken seal, and reinstalling LibreOffice restores it.
- System `python3` can't `import uno`: that module ships only with LibreOffice's own
  Python (3.13 in 26.8).

## Calc

- **Cached xlsx values are trusted.** On load, Calc shows the values stored in the file.
  After the cached `<v>1936</v>` was edited to 999, `getValue()` returned 999 until
  `calculateAll()`. openpyxl-written files have no cached values, and those were
  computed on load. → Every read and fill recalculates; `read --no-recalc` shows the
  cache.
- **`setFormula` needs Calc grammar.** `=SUM(Data!B2,Data!B3)` → Err:508;
  `=SUM($Data.B2;$Data.B3)` works, and localized names (`=ÖSSZEG(…)`) give `#NAME?`.
  → Formulas go through `FormulaParser` with the OOXML op-code map, so Excel syntax
  works (`--native-formulas` for Calc's).
- **Error cells read as 0.** `getValue()` of `=1/0` is 0.0; only `getError()` (532)
  shows the error. → Every result carries `e`, and fill/read exit 1 on errors.
- **Formulas read back in Calc grammar**, e.g.
  `=IFERROR(VLOOKUP("Dél";$Data.A2:C100;3;FALSE());0)`. The xlsx gets Excel syntax
  (`VLOOKUP("Dél",Data!A2:C100,3,FALSE())`).
- **A ReadOnly load drops formatting.** Number formats, weights and colours set on a
  document loaded with `ReadOnly=True` read back unchanged and don't reach the export;
  value writes do. → Fill and the recipes load with `AsTemplate=True`, which also leaves
  no `.~lock.<name>#` next to the source.
- **View settings don't apply to hidden documents.** `freezeAtPosition` left
  `hasFrozenPanes()` false and no `<pane>` in the xlsx.
- `setString` never re-parses, so `007`, `1/2` and `=x` stay text. The CSV parser types
  numbers itself (`"1,250"` → 1250 only as a well-formed grouping; `1,5` stays text).

## Writer

- **`findAll()` with no match aborts soffice**, with SIGABRT in
  `SwXTextRanges::Create` (called from `SwXTextDocument::findAll`). It happened as soon
  as every placeholder had been replaced. → A `findFirst`/`findNext` loop.
- **User fields are document-global.** In a document concatenated from records, every
  record showed the last record's amount. → Before concatenating, each part's user
  fields are flattened to text.
- **Headers belong to page styles.** Inserted documents take the base document's page
  styles, so a per-record header (`Ref: {{ref}}`) showed record 1's value on every page.
  → When a header or footer holds a fill target, the combined PDF is joined from
  per-record PDFs with `pdfunite`. That output isn't PDF/A (pdfunite drops the XMP and
  output intent: veraPDF FAIL), so `--combined` with `--pdfa` is refused in that case.
- `replaceAll` reaches the body, tables, headers, footers and text frames; checked.
- Style names over UNO are programmatic: `Text body` (not "Body Text"), `Standard`
  (not "Default Page Style"). The UI names raise `NoSuchElementException`.
- `insertDocumentFromURL` renames clashing bookmarks in the inserted part.
- A tracked change made through the API has the author "Unknown Author" (the skill
  profile has no user name).

## Impress / Draw

- `--convert-to png` renders only the first slide or page. → `GraphicExportFilter`
  per page.
- Placeholder shape type names: `SubtitleShape` (lower-case t), `OutlinerShape`,
  `TitleTextShape`, `NotesShape`.

## PDF

- PDF/A-1b, 2b, 3b and 4 (`SelectPdfVersion` 1/2/3/4) all pass veraPDF 1.30. Value 4
  is missing from the Help page.
- Missing fonts are substituted and embedded: PDF/A stays valid, but the metrics
  differ. `pdffonts` names the substitute.
- `--pdf-ua` sets the flags; the content decides compliance. A document with an image
  that had no alt text failed `verapdf --flavour ua1`.
- Encryption and PDF/A exclude each other.

## Tools

- `pdfinfo`, `pdffonts`, `pdftotext`, `pdftoppm`, `pdfunite`: poppler
  (`brew install poppler`). veraPDF: `brew install verapdf`; it prints Java warnings on
  stderr, and its first stdout line is `PASS`/`FAIL <file> <flavour>`.
