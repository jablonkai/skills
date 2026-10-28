---
name: gridcraft
description: 'Automate GridCraft, the Excel-style spreadsheet app, headless with gridcraft-cli: build workbooks from CSV with formulas, number formats, tables and charts, edit inputs in an existing .xlsx and read the recalculated values back, evaluate formulas and search the function list, convert between xlsx/csv/tsv/json/html/pdf one file or a whole folder, and check workbooks for cached-value differences and round-trip fidelity, all verified by read-back and check exit status. Use when the user mentions GridCraft or gridcraft-cli, or wants a spreadsheet built, recalculated, checked or converted with GridCraft: "build a budget workbook from this CSV in GridCraft with a chart", "change B3 and tell me the new totals using gridcraft-cli", "run gridcraft check over this folder". Not for Apple Numbers (numbers), LibreOffice Calc or UNO (libreoffice), openpyxl/pandas work with no GridCraft (xlsx), Word documents (wordcraft) or PDF page edits (pdfcraft).'
summary: "automate GridCraft headless with gridcraft-cli — workbooks from CSV with formulas, number formats, tables and charts, input edits with recalculated read-back, formula eval, xlsx/csv/pdf conversion and folder batches, cached-value and round-trip checks"
category: office
compatibility: "Built for gridcraft-cli 0.13.0 and GridCraft.app 0.13.0 on macOS; pre-1.0, so command ids may change."
risk: low
tags: [gridcraft, spreadsheet, excel, xlsx, csv, formulas, charts, headless]
metadata:
  version: "1.1.0"
---

# GridCraft via gridcraft-cli

GridCraft is an Excel-style spreadsheet app. Every menu item is a command in one engine
registry (355 in 0.13.0), and `gridcraft-cli` runs those commands headless against a
workbook, with its own calculation engine, and saves the result. This skill drives that
route and checks every result by reading the saved file back. Verified against
**gridcraft-cli 0.13.0** and **GridCraft.app 0.13.0** on macOS. The software is pre-1.0,
so when a pinned command id fails, look it up rather than guessing.

```sh
command -v gridcraft-cli || ls ~/.local/bin/gridcraft-cli
gridcraft-cli version
```

## Pick the route

| Task | Route |
|---|---|
| Build or edit a workbook (formulas, formats, tables, charts, sheets) | `scripts/gc_run.py` with a step list, one `run` process |
| Read values, formulas, number formats, charts back | `scripts/gc_verify.py`, or `gridcraft-cli cat` / `info` |
| "What would this formula give?" without changing anything | `gridcraft-cli eval '=…' --in FILE [--sheet S]` |
| Does function X exist / what's its signature? | `gridcraft-cli functions --search X` |
| Convert one file | `gridcraft-cli convert IN OUT [--sheet NAME]` (format by extension) |
| Convert a folder | `scripts/gc_batch.py convert IN_DIR OUT_DIR --to pdf` |
| Do cached values match a recalculation? (one file or folders) | `scripts/gc_batch.py check PATH…` |

The live app channel (`GridCraft --control PORT`, `GRIDCRAFT_CONTROL_PORT`,
`gridcraft-cli mcp --connect` / `send`) has **no authentication** in 0.13.0. This skill
doesn't start it or connect to it ([gotchas](references/gotchas.md#live-app-channel)).
Edit files headless; if the workbook is open in the app, ask the user to close it or save
to a new file.

## Scripts

Python 3.9+, standard library only. Call them as `python3 $S/<script>` with
`S=<this skill>/scripts`. Each prints what it did and exits 1 when something failed.

- **`gc_run.py [--in FILE | --sample NAME] --out FILE [--print RANGE] [--overwrite] STEPS`**
  runs a step list (`.json` list of `{"command", "params"}`, `.jsonl`, or `-` for stdin)
  in one process and saves. It refuses to run without `--out` (plain `run` throws the
  work away), refuses to replace an existing file or the input without `--overwrite`,
  prints each answered step, every sheet's used range, tables and charts, and **flags
  formula cells lost** between input and output.
- **`gc_verify.py`**
  - `read FILE [--sheet S] [--range R] [--formulas]`: raw, unformatted values as JSON.
    Report numbers from here, not from the formatted `cat` text.
  - `cells FILE [--sheet S] --value B2=1200 --formula 'E2==SUM(B2:D2)' --has-formula E2:E6 --numfmt 'B2:E6=$'`
  - `charts FILE [--count N] [--kind bar]`
  - `files DIR --ext pdf [--count N] [--min-pages 1] [--expect-text TEXT]`: for PDFs
    it also reads the text and fails on `####` overflow or missing text
- **`gc_batch.py`**
  - `convert IN_DIR OUT_DIR --to FMT [--ext xlsx,csv] [--sheet NAME] [--recursive] [--overwrite]`
  - `check PATH… [--json]`: one verdict per workbook (`clean`, `MISMATCH` with the
    cells, `ROUND-TRIP`, `NOT VERIFIED`, `FAILED`), plus the files `check` skipped.

## Workflow

1. **Look at the input first.** `gridcraft-cli info FILE` (sheets, used ranges, tables,
   charts) and `gridcraft-cli cat FILE --formulas`. A CSV opens as **one sheet named
   after the file stem** (`budget.csv` → sheet `budget`), not `Sheet1`.
2. **Look up what you haven't used.** `gridcraft-cli commands --search <word>` prints
   the id, the menu path and the param shape. There is no `describe` command. The ids
   most jobs need are in [commands.md](references/commands.md).
3. **Write the whole job as one step list** and run it with `gc_run.py`, saving to a
   **new** file. Enter formulas with `cell.set` (`"input": "=SUM(B2:D2)"`) or
   `range.setValues`, and copy them down with `edit.autoFill`. Never type the computed
   number: the user asked for a live workbook.
4. **Read back** with `gc_verify.py cells` (values, formulas, `has-formula`, `numfmt`)
   and `gc_verify.py charts`. Run `gridcraft-cli check OUT.xlsx`: exit 0 means every
   saved value is what GridCraft recalculates.
5. **Convert last.** Before a PDF, end the step list with
   `home.autofitColumnWidth {"sheet": …, "cols": "A:F"}` so no number prints as `####`.
   Then run `convert OUT.xlsx OUT.pdf --sheet NAME` (or `gc_batch.py convert`) and
   `gc_verify.py files DIR --ext pdf --expect-text '<a total as displayed>'`. That reads
   the PDF text and fails on `####` or a missing value. The PDF and CSV take the
   **active** sheet unless `--sheet` is given.
6. **Report** the output paths, the numbers from `gc_verify.py read`, what was verified,
   and anything left unverified (`NOT VERIFIED`, skipped files).

## The traps that cost the most (details in [gotchas.md](references/gotchas.md))

- **`run` without `--out` saves nothing** and still exits 0. Use `gc_run.py`, which
  requires `--out`.
- **A failed step aborts the whole run and writes nothing**, including the steps before
  it. Fix the step and rerun the whole list.
- **`table.totalRow` writes over the row below the table.** An Average row right under
  the data is silently replaced. Insert a row first (`home.insertRows {"rows": "9:9"}`)
  or use the total row instead of a separate one. `gc_run.py` flags lost formulas.
- **`range.fill` with an explicit `range` shifts relative references** from the active
  cell, not the range (`=SUM(B2:D2)` lands in E2 as `=SUM(F3:H3)`). Use `cell.set` +
  `edit.autoFill`, or `selection.set` first.
- **A chart for another sheet**: `insert.chart {"sheet": "Chart", "range":
  "Data!A1:A8,Data!D1:D8"}`. `sheet` is where the chart goes, and a multi-area range
  with sheet prefixes fails without it.
- **A column too narrow for its numbers prints `####` in the PDF.** `cat` and
  `--print` still show the full value, so only the PDF text reveals it. Currency formats
  and totals widen numbers. Autofit with **explicit `cols`** (without them it does
  nothing) and check with `gc_verify.py files`.
- **`cat`, `--print` and `sheet.read formatted:true` show display text** (`$1,200.00`).
  Compare numbers with `gc_verify.py read` / `cells`, or with `eval`.
- **`convert` and `run --out` overwrite existing files silently.** `gc_run.py` and
  `gc_batch.py convert` refuse unless `--overwrite`.
- **`check` exit 0 isn't proof**: a workbook without cached values (openpyxl, some
  exporters) has nothing to compare and still passes. `gc_batch.py check` reports it as
  `NOT VERIFIED`. `check` on a folder reads `.xlsx`/`.xlsm` only, recursively.
- **Inserting a sheet makes it active**, so a later `convert` to PDF/CSV exports that
  sheet. Pass `--sheet`, or end the step list with `sheet.activate`.
- **`range.setValues` parses strings by en-US rules** (`"2.500"` → 2.5, `"05.04.2026"`
  → a date). For European data pass `parse: false`, or `file.open` with `csvAsText`.

## Common jobs

Worked step lists are in [recipes.md](references/recipes.md):

- **CSV → workbook**: totals and averages, currency format, table, chart, then `.xlsx` + PDF.
- **What-if**: change an input in a copy and report the dependent totals before and after.
- **Folder check**: `gc_batch.py check DIR` and a report naming each mismatched cell.
- **Folder conversion**: xlsx → PDF/CSV, CSV → xlsx.
- **Formula questions**: `eval` against a workbook, and `functions --search` for support.

## References

- [references/cli.md](references/cli.md): every subcommand, its options, script syntax,
  output and exit status.
- [references/commands.md](references/commands.md): pinned command ids by task, with params.
- [references/recipes.md](references/recipes.md): step lists for the common jobs.
- [references/gotchas.md](references/gotchas.md): everything that fails silently, and the
  live-channel security note.
