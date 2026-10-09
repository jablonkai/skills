---
name: numbers
description: 'Automate Apple Numbers on macOS via its scripting dictionary (osascript, JXA) — build a .numbers spreadsheet from CSV/JSON with typed values, header and footer rows, formulas such as a SUM totals row, and cell formats; read sheets, tables, recalculated values and formulas back and report totals per table; export or batch-convert .numbers files to XLSX, CSV or PDF. Use whenever the user mentions Numbers or a .numbers file: "import this CSV into Numbers and add a totals row", "what are the totals in budget.numbers", "convert these Numbers files to Excel", "export my .numbers to PDF", or Hungarian "konvertáld a Numbers táblázatot Excelbe". Not for .xlsx work without Numbers (use xlsx), CSV or pandas analysis that never touches Numbers, spreadsheets to Markdown (use markitdown), or Pages and Keynote documents.'
summary: "automate Apple Numbers via AppleScript/JXA — build spreadsheets from CSV with formulas and formats, read recalculated values back, and XLSX/CSV/PDF export or batch conversion"
category: office
risk: low
tags:
    - numbers
    - iwork
    - applescript
    - jxa
    - spreadsheet
    - xlsx
    - csv
metadata:
  version: "1.0.0"
---

# Numbers Automation

Apple Numbers is driven through its **scripting dictionary via `osascript`** (JXA). Each
script call opens the documents it needs, works, and closes them again. There is no
bridge or listener; macOS Automation consent is the only gate. Verified against
**Numbers Creator Studio 15.4** (bundle id `com.apple.Numbers`) on macOS 27.

Everything goes through the scripts below. They encode workarounds for behaviour that
looks right but is locale-dependent or broken (see Pitfalls), so reach for raw
AppleScript only for what they don't cover
([references/recipes.md](references/recipes.md)).

| Script | Does |
|---|---|
| `bash scripts/numbers.sh --check` | app, version, Automation permission, region separators. Run first. |
| `python3 scripts/numbers-build.py IN.csv -o D.numbers ...` | new table from CSV/TSV/JSON: typed values, formats, formulas, totals row, exports |
| `python3 scripts/numbers-read.py D.numbers [--totals]` | sheets, tables, recalculated values, formulas, error cells |
| `python3 scripts/numbers-export.py SRC... --to FMT` | one file or folders (`-r`, mirrored) to xlsx, csv, pdf, numbers09 |
| `python3 scripts/numbers-verify.py FILE ...` | assert on a .numbers, .xlsx or .csv: cell values, formulas, counts, no errors |
| `bash scripts/numbers.sh --dialog` | is a modal Numbers alert blocking scripting? screenshots it |
| `bash scripts/numbers.sh --close-leftovers` | close documents a killed run left open (stop path) |

All Python is standard library only and runs on the system `python3`. Scripts exit
non-zero on failure; `--json` on build and read gives machine-readable output.

## Workflow

1. `bash scripts/numbers.sh --check`. `automation: DENIED` → ask the user to allow the
   terminal in System Settings ▸ Privacy & Security ▸ Automation ▸ Numbers. Note the
   region's `decimal` — Numbers displays and exports CSV with it.
2. Inspect a document you did not write: `python3 scripts/numbers-read.py file.numbers`
   prints every table as a grid with its header/footer rows, formula count and error
   cells; `--json` gives raw values, formatted values and formulas per cell.
3. Build, read or export.
4. **Verify independently** with `numbers-verify.py` on the `.numbers` and on each
   export (below). For looks, export a PDF and read it with the pdf skill or Read it.

## Build from CSV: values, formats, formulas, totals row

```bash
S=scripts
python3 $S/numbers-build.py sales.csv -o sales.numbers --summary-row --export sales.xlsx
python3 $S/numbers-build.py sales.csv -o sales.numbers --sheet Sales --table Q3 \
  --format "Revenue=currency" --format "C:D=number" --formula F2 "=D2-C2" --summary-row
python3 $S/numbers-build.py eu.csv -o eu.numbers --delimiter ';' --decimal , --thousands .
python3 $S/numbers-build.py more.csv -o sales.numbers --into --sheet Sales --table Q4
```

- The CSV is parsed **here, not by Numbers**. Numbers' own CSV import uses the region's
  separators, so `"1,250"` could become 1.25. Defaults: `.` decimal, `,` thousands,
  sniffed delimiter, UTF-8 (BOM ok). Leading-zero codes (`007`) and anything else
  Numbers would reinterpret stay text; `12%` becomes 0.12 with the percent format.
- `--summary-row [FUNC]` appends a **footer row** of `FUNC(first:last)` formulas under
  every numeric column (default `SUM`; `AVERAGE`, `MIN`, `MAX`, `COUNT` …) with
  `--summary-label` (default `Total`) in the first text column. Formulas are
  entered with English function names and recalculated by Numbers; the script reads
  each result back and exits 1 if any formula evaluates to an error.
- `--format` takes a header name, a column letter or range (`C:D`, `Q1:Q2` as two
  header names) or an A1 range, and one of `number currency percent text date duration
  fraction scientific checkbox automatic`. Column formats cover the body and footer.
- `--formula CELL EXPR` sets any cell (the table grows to include it).
- CSV cells starting with `=` stay text (no formula injection) unless `--csv-formulas`.
- `--into` adds the table to an existing document: onto sheet `--sheet` if it exists,
  else a new sheet. It saves that document in place — work on a copy unless the user
  asked. Without `--into` an existing output is refused unless `--force`.
- JSON input: a list of rows (first row = header), or a list of objects (keys become
  the header). JSON numbers stay numbers; strings are never re-parsed.
- About 19 ms per cell (one Apple event each): 1000 cells ≈ 20 s.

## Read values and totals

```bash
python3 $S/numbers-read.py budget.numbers                    # grids, formatted
python3 $S/numbers-read.py budget.numbers --totals           # per table
python3 $S/numbers-read.py budget.numbers --table Costs --cells B7 C7
python3 $S/numbers-read.py budget.numbers --json > budget.json
```

- `--totals` reports, per sheet / table, the **footer row** when the table has one
  (those are the author's totals), else the sum of each numeric column over the body
  rows — the output says which. Name every table and its sheet when answering, and say
  which source applied.
- Values are what Numbers recalculated. Formula text comes back **in the UI language**
  (`=SZUM(B2:B9)` under Hungarian): compare values, not formula text. Error cells are
  listed (`ERRORS in B7`) — they read as empty otherwise.
- Opens `.xlsx` and `.csv` too (read-only; nothing is saved).

## Export and convert

```bash
python3 $S/numbers-export.py budget.numbers --to xlsx                 # next to source
python3 $S/numbers-export.py ~/Reports -r --to xlsx --out-dir ~/Reports-xlsx
python3 $S/numbers-export.py budget.numbers --to pdf --out /tmp/budget.pdf --pdf-quality best
python3 $S/numbers-export.py budget.numbers --to csv --flat-csv       # one CSV per table
python3 $S/numbers-export.py budget.numbers --to csv --raw-csv        # comma, raw values
python3 $S/numbers-verify.py ~/Reports-xlsx/q3.xlsx --numbers-coords --expect B14=1250 --formula B14
```

- **XLSX**: one worksheet per table, named `Sheet - Table` (just `Sheet` while the
  table keeps its default name); the
  **table name sits in row 1, so every address moves down one row** — use
  `--numbers-coords` in verify. Formulas become English array formulas with cached
  values (openpyxl `data_only=True` reads them). The localized summary worksheet is left
  out unless `--summary-worksheet`.
- **CSV**: Numbers' export uses the region's list separator (`;` under a comma-decimal
  region) and formatted values (`33 Ft`); several tables give a folder `X.csv/`.
  `--flat-csv` flattens it; `--raw-csv` writes comma-separated raw values instead —
  prefer it when a program will read the CSV.
- `--password`/`--password-hint` for XLSX, PDF, Numbers 09. Existing outputs are
  skipped unless `--force`; a folder tree is mirrored under `--out-dir`.

## Pitfalls (all measured on 15.4)

- **Charts can't be created or read by script.** `make new chart` fails and charts
  expose only position and size. Build the table, then tell the user to add the chart
  in the UI (or render one with matplotlib, or add it to the XLSX with openpyxl).
  `numbers-read` reports how many charts a sheet has.
- **A modal alert blocks all scripting** (password prompt, "can't be opened", missing
  fonts): every later call times out (-1712). The scripts report it with a screenshot
  (`numbers.sh --dialog`). Ask the user to click it away; don't try to dismiss it.
- **Number formatting follows the region**: currency symbol and rounding (`204 Ft` for
  203.5), decimal mark, CSV separator. There is no scripted decimal-places setting.
  Values stay exact; mention display rounding when it hides decimals.
- **Never open a document the user has open.** Their unsaved edits and yours would
  collide; the scripts refuse.
- In raw AppleScript: open files **as an alias**; create sheets with `tell d to make
  new sheet`, then rename; AppleScript prints numbers with the region's decimal mark —
  use JXA when you need to parse values.

More pitfalls, and why the scripts do what they do:
[references/gotchas.md](references/gotchas.md). Dictionary reference (classes, commands,
formats, export options, what is missing): [references/dictionary.md](references/dictionary.md).

## Safety

- The scripts write new files only; sources are opened and closed without saving.
  `--into` is the one exception (it saves the target document), and an existing output
  is replaced only with `--force`.
- Values reach Numbers through a JSON request file read by `numbers_ops.js`, never
  spliced into script source.
- Stop path: every call ends at `NUMBERS_TIMEOUT` (default 300 s). After an interrupted
  run, `numbers.sh --close-leftovers` closes only the documents the scripts opened. The
  scripts never quit Numbers, never close the user's own documents, and never click
  dialogs.
- A `--password` shows in the Python process's arguments. It reaches Numbers only
  through the request file, which is private (mode 600) and deleted after the call.
