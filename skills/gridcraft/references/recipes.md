# Recipes

`S=<skill>/scripts`. Every recipe saves to a new file, reads it back, and only then
converts or reports.

## 1. CSV → budget workbook with totals, averages, currency and a chart, then PDF

Input: `budget.csv` with a header row (`Category,Jan,Feb,Mar`) and N category rows,
which become rows 2..N+1 of the sheet named after the file stem.

First look at it with `gridcraft-cli cat budget.csv`. Then write `steps.json` (here
N = 5, so the data is rows 2–6, the Total column is F and the Average row is 7):

```json
[
  {"command": "cell.set", "params": {"cell": "E1", "input": "Total"}},
  {"command": "cell.set", "params": {"cell": "E2", "input": "=SUM(B2:D2)"}},
  {"command": "edit.autoFill", "params": {"source": "E2", "target": "E2:E6"}},
  {"command": "cell.set", "params": {"cell": "A7", "input": "Average"}},
  {"command": "cell.set", "params": {"cell": "B7", "input": "=AVERAGE(B2:B6)"}},
  {"command": "edit.autoFill", "params": {"source": "B7", "target": "B7:E7"}},
  {"command": "home.numberFormat", "params": {"range": "B2:E7", "format": "Currency"}},
  {"command": "home.bold", "params": {"range": "A1:E1"}},
  {"command": "home.bold", "params": {"range": "A7:E7"}},
  {"command": "home.autofitColumnWidth", "params": {"cols": "A:E"}},
  {"command": "insert.chart", "params": {"range": "A1:D6", "type": "bar", "title": "Monthly budget", "at": "G2"}},
  {"command": "pageLayout.orientation", "params": {"orientation": "landscape"}},
  {"command": "pageLayout.scaleToFit", "params": {"width": 1, "height": 1}}
]
```

```sh
python3 $S/gc_run.py --in budget.csv --out budget.xlsx --print A1:E7 steps.json
python3 $S/gc_verify.py cells budget.xlsx --has-formula E2:E6 --has-formula B7:E7 \
    --formula 'E2==SUM(B2:D2)' --formula 'B7==AVERAGE(B2:B6)' --numfmt 'B2:E7=$'
python3 $S/gc_verify.py charts budget.xlsx --count 1 --kind bar
gridcraft-cli check budget.xlsx
gridcraft-cli convert budget.xlsx budget.pdf
python3 $S/gc_verify.py files . --ext pdf --expect-text '$4,350.00'   # no ####, total printed
python3 $S/gc_verify.py read budget.xlsx --range A1:E7     # numbers for the report
```

- Chart the monthly columns (`A1:D6`) and leave out the Total column and the Average
  row. Otherwise the totals dwarf the months and the average becomes a category. Chart
  the totals only if the user asks for that.
- Use `type: "bar"` for horizontal bars and `"column"` for vertical ones. If the user
  says "bar chart" casually, either is defensible, so say which one you used.
- Want a table as well? Make it `A1:E6` and keep the Average row separate with a blank
  row in between, or use the table's own total row (`table.totalRow` +
  `table.totalFunction function=average`) **instead of** a hand-written Average row,
  never both. Total-row cells don't inherit the column's number format, so format them
  afterwards.

## 2. What-if: change an input, report the dependants

```sh
gridcraft-cli info forecast.xlsx
gridcraft-cli cat forecast.xlsx --formulas          # find the input cell and what depends on it
gridcraft-cli run --in forecast.xlsx --cmd 'formulas.traceDependents={"cell":"B3","sheet":"Inputs"}'
python3 $S/gc_verify.py read forecast.xlsx --sheet Summary --range A1:D10     # before
echo '[{"command":"cell.set","params":{"sheet":"Inputs","cell":"B3","input":"0.07"}}]' \
  | python3 $S/gc_run.py --in forecast.xlsx --out forecast-7pct.xlsx -
python3 $S/gc_verify.py read forecast-7pct.xlsx --sheet Summary --range A1:D10   # after
gridcraft-cli check forecast-7pct.xlsx
```

- Save to a **new** file unless the user explicitly wants the original changed. Then
  say which file holds the new numbers.
- `traceDependents` returns direct dependants only. Totals further down the chain show
  up in the before/after read of the summary range.
- A percentage input takes the fraction (`0.07`) or `"7%"`. Check how the cell is
  formatted (`cell.get` → `num_fmt`) and read the value back.
- Report each changed total as old → new, from the raw values. Don't report the
  formatted text.
- For a quick answer with no file, `eval` can't override an input. Use `run` without
  `--out`, which is fine here because nothing should be saved:
  `gridcraft-cli run --in f.xlsx --cmd 'cell.set={…}' --cmd 'sheet.read={"sheet":"Summary","range":"B10"}'`.

## 3. Folder check: which workbooks don't recalculate to their saved values?

```sh
python3 $S/gc_batch.py check ~/Reports            # verdict per file, exit 1 if any MISMATCH
gridcraft-cli check ~/Reports/q3.xlsx              # detail for one file, if needed
```

- Report every `MISMATCH` with the file, the cell, the formula, and the expected (cached)
  and actual (recalculated) values.
- Name the clean files too, and list `NOT VERIFIED` files separately: they have
  formulas but no cached values to compare. Mention the files `check` skipped.
- A mismatch means the saved value disagrees with GridCraft's recalculation. It might be
  a stale cache, a manual-calc workbook, a value edited outside Excel, or an engine
  difference. Don't call it a GridCraft bug or a file bug without evidence.
- `check` never modifies the files.

## 4. Folder conversion

```sh
python3 $S/gc_batch.py convert ~/In ~/Out --to pdf --ext xlsx            # xlsx → PDF (active sheet)
python3 $S/gc_batch.py convert ~/In ~/Out --to xlsx --ext csv            # CSV → xlsx
python3 $S/gc_batch.py convert ~/In ~/Out --to csv --ext xlsx --sheet Data
python3 $S/gc_verify.py files ~/Out --ext pdf --count 12
```

To get several sheets of one workbook out, convert once per sheet with `--sheet`, to
`stem-Sheet.csv`, using single `gridcraft-cli convert` calls.

## 5. Formula questions

```sh
gridcraft-cli eval '=NPV(0.08,B2:B9)' --in model.xlsx --sheet Cashflow
gridcraft-cli eval '=XLOOKUP("Rent",A2:A9,E2:E9)' --in budget.xlsx
gridcraft-cli functions --search XLOOKUP
gridcraft-cli functions --category Financial
```

## 6. European CSV (semicolons, decimal commas, dd.mm.yyyy)

`--in eu.csv` detects the `;` delimiter, but it parses `2.500,50` as text and
`05.04.2026` by en-US rules (May 4). Convert the data explicitly instead:

- Open it with `file.open {path, csvAsText: true}`. Every field stays text.
- Then write numeric columns with `range.setValues` (real numbers, `parse: false`), and
  dates as `=DATE(y,m,d)`. Or convert the values in Python and write them in one
  `range.setValues`.
- Read a few cells back with `gc_verify.py cells --value` before building on them.
