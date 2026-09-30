# UNO API used by the skill

This is the subset of the LibreOffice API (https://api.libreoffice.org/) that
`lo_ops.py` and the recipes use, with the details that matter for headless work. Every
call was run on 26.8.0.3. Lengths are in 1/100 mm.

## Loading and storing

- `desktop.loadComponentFromURL(url, "_blank", 0, props)` opens a document or a new one
  (`private:factory/swriter|scalc|simpress|sdraw`). The load properties used:
  - `Hidden=True`, and `Silent=True` so no UI appears
  - `MacroExecutionMode=0` (NEVER_EXECUTE) and `UpdateDocMode=0` (NO_UPDATE), so
    embedded macros and external links stay inert
  - `ReadOnly=True` to inspect only: **formatting edits are silently dropped** on it
  - `AsTemplate=True` for an editable, untitled copy with no lock file
  - `FilterName`/`FilterOptions` to force an import filter, `Password` for protected files
  - It returns `None` or raises `IllegalArgumentException`/`IOException` on failure.
    Headless never shows the password dialog.
- `doc.getArgs()` → the load MediaDescriptor. `FilterName` names the import filter
  actually used: `MS Word 2007 XML`, `Calc MS Excel 2007 XML`, … and `Text` when LO fell
  back to plain text.
- `doc.storeToURL(url, props(FilterName=…, FilterData=…, FilterOptions=…))` exports and
  leaves the document untitled. The scripts never call `store()` or `storeAsURL()` on a
  source. Pass `FilterData` as
  `uno.Any("[]com.sun.star.beans.PropertyValue", tuple)`, since a plain tuple fails to
  convert for some filters.
- `doc.close(True)`: `soffice --headless` exits after the macro **only when no document is
  left open**, so always close in `finally`.
- Kind: `doc.supportsService(…)` with `text.TextDocument`, `sheet.SpreadsheetDocument`,
  `presentation.PresentationDocument` or `drawing.DrawingDocument`.

## Calc

- `doc.Sheets.getByName(n)` / `getByIndex(i)`, `sheet.getCellRangeByName("A1:C9")`, and
  `range.getCellByPosition(col, row)` (relative).
- Write: `cell.setValue(float)`, `cell.setString(str)` (never parsed, so `007` stays
  text), `cell.setFormula(str)`, and `range.setDataArray(tuple_of_tuples)`.
- `setFormula` takes Calc's API grammar: English function names, `;` separators and
  `$Sheet.A1` references. `=SUM(Data!B2,Data!B3)` gives Err:508. For Excel syntax, parse
  to tokens:

  ```python
  from com.sun.star.sheet.FormulaLanguage import OOXML
  from com.sun.star.sheet.FormulaMapGroup import SPECIAL, ALL_EXCEPT_SPECIAL
  mapper = doc.createInstance("com.sun.star.sheet.FormulaOpCodeMapper")
  parser = doc.createInstance("com.sun.star.sheet.FormulaParser")
  parser.CompileEnglish = True
  parser.FormulaConvention = 3  # AddressConvention.XL_OOX
  parser.OpCodeMap = (mapper.getAvailableMappings(OOXML, SPECIAL)
                      + mapper.getAvailableMappings(OOXML, ALL_EXCEPT_SPECIAL))
  cell.setTokens(parser.parseFormula('=IFERROR(VLOOKUP("x",Data!A2:C9,3,FALSE),0)',
                                     cell.getCellAddress()))
  ```
- `doc.calculateAll()` recalculates everything. Without it, values loaded from an xlsx
  are the file's cached results: a cached 999 stayed 999 until `calculateAll()` gave 1936.
- Read:
  - `cell.getType().value`: `EMPTY`, `VALUE`, `TEXT` or `FORMULA`
  - `cell.getValue()` and `cell.getString()` (the shown text)
  - `cell.getFormula()`
  - `cell.getError()`: 0, or a code such as 532 `#DIV/0!`, 519 `#VALUE!`, 524 `#REF!`,
    525 `#NAME?`, 503 `#NUM!`, 32767 `#N/A`, 508 bracket, 522 circular. **An error cell's
    `getValue()` is 0.0.**
  - `cell.FormulaResultType2`: 1 value, 2 string, 4 error
- `sheet.queryContentCells(CellFlags.FORMULA).getCells()` enumerates every formula cell.
  `sheet.createCursor()` + `gotoStartOfUsedArea`/`gotoEndOfUsedArea(True)` gives the used
  range.
- `doc.NamedRanges.getByName(n).getReferredCells()`.
- `clearContents(flags)`: VALUE 1, DATETIME 2, STRING 4, ANNOTATION 8, FORMULA 16,
  HARDATTR 32, STYLES 64.
- Formatting (on an `AsTemplate` load): `NumberFormat` (a key from
  `doc.NumberFormats.queryKey/addNew(code, Locale)`), `CharWeight` 150 = bold,
  `CellBackColor` 0xRRGGBB, column `OptimalWidth`, `sheet.protect(pw)`, and charts via
  `sheet.Charts.addNewByName(name, Rectangle, (CellRangeAddress,), colHeaders, rowHeaders)`.

## Writer

- `doc.Text`, `text.createTextCursor()`, `text.insertString(cur, s, absorb)`,
  `insertControlCharacter(cur, PARAGRAPH_BREAK, False)`, `insertTextContent(cur, obj, False)`.
- Search: `doc.createSearchDescriptor()` / `createReplaceDescriptor()` with
  `SearchString`, `ReplaceString`, `SearchRegularExpression` and `SearchCaseSensitive`,
  then `doc.replaceAll(rd)`. It covers the body, tables, headers, footers and frames.
  **`doc.findAll()` with no match aborts soffice (SIGABRT in `SwXTextRanges::Create`)**;
  loop `findFirst`/`findNext(found.getEnd(), sd)` instead.
- User fields: `doc.TextFieldMasters.getByName("com.sun.star.text.fieldmaster.User.<name>").Content = "…"`.
  They are document-global, so every instance shows the same value.
- Bookmarks: `doc.Bookmarks.getByName(n).getAnchor().setString(s)` inserts at a
  collapsed bookmark or replaces a spanned one.
- Mail-merge fields: `TextField.Database`, where the column is
  `getTextFieldMaster().DataColumnName`. Input fields: `TextField.Input` with its `Hint`.
  To replace a field with text: `anchor = f.getAnchor();
  anchor.getText().insertString(anchor, s, True)`.
- `doc.TextFields.refresh()`, `doc.DocumentIndexes.getByIndex(i).update()` (tables of
  contents) and `doc.refresh()`.
- Pages: `doc.CurrentController.PageCount`.
- Concatenate: `cursor.gotoEnd(False)`, a paragraph break, `cursor.BreakType =
  PAGE_BEFORE`, then `cursor.insertDocumentFromURL(url, ())`. Page styles (and so
  headers) are the base document's.
- Styles: `doc.StyleFamilies.getByName("ParagraphStyles"|"PageStyles"|…)`. The names are
  programmatic (`Text body`, `Heading 1`, `Standard`), and `DisplayName` is the UI name.
- Tracked changes: `doc.RecordChanges` and `doc.Redlines`. Accept all with the dispatcher
  (`.uno:AcceptAllTrackedChanges`) on `doc.CurrentController.Frame`.

## Impress / Draw

- `doc.DrawPages`: `getByIndex`, `insertNewByIndex(n)` (inserts after n and returns the
  new page), `getCount`. `page.Layout` is the AutoLayout (0 title slide, 1 title +
  content). `page.Visible` is false for a hidden slide.
- Shapes: `page.getByIndex(k).getShapeType()`, e.g.
  `com.sun.star.presentation.TitleTextShape`, `SubtitleShape`, `OutlinerShape`.
  `page.getNotesPage()` has a `NotesShape`.
- Image per page: create `com.sun.star.drawing.GraphicExportFilter`, call
  `setSourceDocument(page)`, then `filter(props(URL=…, MediaType="image/png",
  FilterData=filter_data({"PixelWidth": w, "PixelHeight": h})))`. The page's
  `Width`/`Height` give the aspect ratio. `--convert-to png` renders only the first page.

## Script runner facts

- A Python macro in `<profile>/user/Scripts/python/x.py` exposing `g_exportedScripts` is
  run by `soffice … "vnd.sun.star.script:x.py$main?language=Python&location=user"`. Its
  `XSCRIPTCONTEXT` gives `getDesktop()` and `getComponentContext()`.
- The environment of the `soffice` process reaches the macro (`LO_REQ`). Set
  `PYTHONDONTWRITEBYTECODE=1` so nothing writes `.pyc` files into the app bundle.
