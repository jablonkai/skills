# Gotchas (gridcraft-cli 0.14.2)

Everything here was reproduced on 0.14.2. Most of these fail **silently**: exit 0 and a
plausible file, but the wrong content.

## Saving

- **`run` without `--out` discards every change** and exits 0. `gc_run.py` requires `--out`.
- **`run --out` and `convert` overwrite an existing file without asking**, including the
  `--in` file itself. `gc_run.py` and `gc_batch.py convert` refuse unless `--overwrite`.
- **One failed step aborts the run and writes nothing**, not even the work of the
  earlier steps. The error names the step and line:
  `step 2 (s.jsonl:3, nope.cmd): unknown command`. Fix it and rerun the whole list.
- **Unknown or misspelled params fail the run** (`invalid parameters for …`). Look up
  the shape with `commands --search`.

## Reading back

- **The result lines are not a progress count.** Commands with nothing to return
  (`edit.autoFill`, number formats, bold, column widths) print no line. Verify by reading
  the file back, not by counting lines.
- **`cat`, `--print` and `sheet.read formatted:true` return display text**, such as
  `$1,200.00` or `$ (64.35)`, and `cat --csv` quotes values that contain commas. For
  numbers, use `sheet.read` (raw), `cell.get` → `value`, `gc_verify.py read`, or `eval`.
- **Number formats are only visible through `cell.get`** → `style.num_fmt`. `info`
  doesn't show them.
- **A chart inserted without `title` is saved as "Chart Title".** Pass a real title.

## PDF output

- **Numbers wider than their column print as `####` in the PDF.** In the eval fixture,
  default-width columns holding `$2,940.00` printed eight `########` cells. `cat`,
  `--print` and `cell.get` → `text` all show the full value, so the workbook looks fine
  until the PDF text is read. Fix it with `home.autofitColumnWidth {"sheet": "Data",
  "cols": "A:D"}` before converting. **Without `cols` it changes nothing.** You can
  also use `home.columnWidth {cols, chars}`. Then verify the PDF text:
  `gc_verify.py files DIR --ext pdf --expect-text '$18,093.65'`. It uses `pdftotext`
  from poppler.
- The PDF takes the sheet's page setup. A wide sheet with a chart beside the data runs
  to 2+ pages. Use `pageLayout.orientation landscape` and `pageLayout.scaleToFit
  {width: 1}` when the user wants one page.

## Structure

- **A CSV becomes one sheet named after the file stem** (`b.csv` → `b`). Use that name
  for `--sheet` and for references to other sheets.
- **Table total rows write over the row below the table.** `insert.table A1:E4` +
  `table.totalRow` turned row 5, which held hand-written `=AVERAGE` formulas, into
  `=SUBTOTAL(101,T[…])` cells. Formula cells dropped from 7 to 4, and the run still said
  ok. `gc_run.py` reports `LOST FORMULAS`. Leave a blank row under a table, or use the
  total row instead of your own.
- **`range.fill {range, input}` adjusts relative references from the active cell, not
  from the range.** With A1 active, `range.fill {"range": "E2:E4", "input":
  "=SUM(B2:D2)"}` writes `=SUM(F3:H3)` into E2, and the values come out 0. Either
  `selection.set {"range": "E2:E4"}` first and then `range.fill {input}`, or use
  `cell.set` on the first cell followed by `edit.autoFill`.
- **`insert.chart` puts the chart on `sheet`** (default: the active sheet). A
  multi-area range with sheet prefixes (`"Data!A1:A8,Data!D1:D8"`) fails with
  `no sheet named …` unless `sheet` is given. Without prefixes, the range is read on
  `sheet`.
- **Total-row cells don't inherit the column's number format.** Format them after
  `table.totalRow`.
- **`home.insertSheet` makes the new sheet active**, and the active sheet is saved. A
  later `convert` to PDF/CSV, or `--out x.pdf`, then exports the new, often empty,
  sheet. Pass `--sheet` to `convert`, or end with `sheet.activate {sheet: …}`.
- **`data.fromTextCsv` imports into a new sheet as a table**, not into the current
  sheet. Opening the CSV with `--in` is simpler for one file.

## Input parsing

- **`range.setValues` and `cell.set` parse strings by en-US rules**: `"2.500"` → 2.5,
  `"05.04.2026"` → May 4, `"1,200"` → 1200. Pass `parse: false` to `range.setValues` to
  keep strings as text, and write real numbers as JSON numbers.
- **An opened European CSV**: the `;` delimiter is detected, but `2.500,50` stays text
  and `05.04.2026` is read month-first. Use `file.open {csvAsText: true}` and convert
  the values deliberately (recipes §6).

## check

- **Exit 0 does not mean verified.** A workbook whose formulas have no cached values,
  for example one written by openpyxl or flagged for full recalculation on load, reports
  `0 checked … N no oracle` and exits 0. `gc_batch.py check` calls it `NOT VERIFIED`.
- **Folders are searched recursively for `.xlsx`/`.xlsm` only.** CSV, ODS and XLS files
  in the folder are ignored without a mention. `gc_batch.py check` lists them.
- **Volatile functions** (`NOW`, `TODAY`, `RAND`, `OFFSET`, `INDIRECT`) are not
  compared and are counted as `volatile`.
- `--tolerance` defaults to 1e-9. Excel-written files sometimes differ in the last bits
  of floating point, so retry with `--tolerance 1e-6` before calling a 1e-12 difference
  a mismatch.

## Live app channel

`GridCraft --control PORT` (or the `GRIDCRAFT_CONTROL_PORT` environment variable) opens a
JSON-lines channel on 127.0.0.1. `gridcraft-cli mcp --connect PORT` and
`gridcraft-cli send PORT METHOD` drive the running app through it.

In 0.14.2 the channel has **no token or other authentication**: any local process,
including a web page that can reach localhost, could run any command, among them
`file.saveAs` to arbitrary paths. That fails this repo's bridge rules (token auth,
cross-origin rejection, documented posture, stop path), so this skill:

- never starts the app with `--control` and never sets `GRIDCRAFT_CONTROL_PORT`;
- never uses `mcp --connect` or `send`;
- edits files headless instead. If the user has the workbook open in GridCraft, it asks
  them to close it, or saves to a new file and tells them to reopen it.

If a later GridCraft adds authentication to this channel, a live mode can be added.
