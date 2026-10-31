# gridcraft-cli 0.14.2 reference

`gridcraft-cli` is the headless front end of GridCraft's engine: same command registry,
same calculation engine, same file readers and writers as the app, with no window.
Binary: `~/.local/bin/gridcraft-cli`. `gridcraft-cli version` prints `0.14.2`.

## run: commands, then save

```sh
gridcraft-cli run [--in FILE | --sample budget|sales|grades] \
    [--cmd 'id={json}']... [--script FILE.jsonl] [--out FILE] [--print RANGE] [--quiet]
```

- **Input**: `--in` opens xlsx, xlsm, xls, xlsb/ods (data import), csv, tsv, txt or json.
  `--sample` starts from a built-in sample. Neither means a blank workbook.
- **Commands** run in order: every `--cmd`, then the `--script` lines. A script line is
  `id={json}` or `{"command": "id", "params": {…}}`. Blank lines and lines starting with
  `#` or `//` are skipped.
- **Output**: each command that returns something prints one JSON line
  `{"command": id, "result": …}`. Commands with nothing to return (`edit.autoFill`,
  most formatting) print **nothing**. Then `wrote FILE (N bytes)`.
- **`--out`**: the format follows the extension (`.xlsx` default; `.csv`, `.tsv`,
  `.json`, `.html`, `.pdf`). Without `--out`, nothing is saved. An existing file is
  overwritten without a prompt, including the `--in` file.
- **`--print RANGE`**: prints the range as an aligned text table of display values
  after the commands.
- **`--quiet`**: hides the per-command lines. `wrote …` is still printed.
- **Failure**: the first failing step prints
  `gridcraft-cli: step N (file:line, id): <reason>` to stderr, exits 1 and writes no
  output at all.

## Read-back

```sh
gridcraft-cli info FILE [--json]
gridcraft-cli cat FILE [--range A1:D20] [--sheet S] [--formulas] [--csv]
```

- `info`: per sheet, the used range and cell count, tables (name, range, style) and
  charts (kind such as `BarClustered`, title, anchor cell, series count), plus names.
  `--json` adds merges, freeze, comments, validations, conditional formats, visibility,
  calc mode and theme.
- `cat`: display values (number formats applied). `--formulas` shows formulas in place
  of values. `--csv` quotes any display value containing a comma (`"$1,200.00"`).
- For raw values, number-format codes and styles, use the `sheet.read` and `cell.get`
  commands through `run` (or `scripts/gc_verify.py`):
  - `sheet.read {range, sheet, formulas?, formatted?}` returns `values` rows of raw
    numbers, strings, bools and nulls.
  - `cell.get {cell, sheet}` returns `value`, `formula`, `text` (the display string),
    `type`, and `style.num_fmt`, for example `"$"#,##0.00`.

## eval and functions

```sh
gridcraft-cli eval '=SUM(B2:B4)*2' [--in FILE] [--sheet S] [--cell A1] [--json]
gridcraft-cli functions [--json] [--search X] [--category C]
```

- `eval` evaluates the formula against the workbook without changing it. `--cell` sets
  the formula's home cell for relative references. It prints the raw value.
- `functions` lists the 514 supported functions with their signature and a one-line
  description.

## check: calculation oracle and round trip

```sh
gridcraft-cli check FILE-OR-DIR... [--json] [--tolerance 1e-9] [--max-report N]
```

- For every formula cell with a cached value, `check` recalculates it and compares the
  result. It also saves and reopens the workbook in memory and compares 14 categories:
  values, formulas, numFmts, charts, tables, names, merges and others.
- A folder is searched recursively, for `.xlsx`/`.xlsm` only. Other files are ignored
  without a mention.
- **Exit status**: 1 on any mismatch, round-trip difference or file that fails to open,
  and 0 otherwise. A file whose formulas have no usable cached value is counted as
  `no oracle`, and still gives exit 0.
- The text report gives a `== file` block per workbook with
  `mismatch Sheet!Cell =FORMULA expected X got Y [FUNC]`, then a table and totals.
  **`expected` is the value saved in the file, and `got`/`actual` is GridCraft's
  recalculation.** `gc_batch.py check` prints them as `saved` and `recalculated`.
- The `--json` schema is `gridcraft-check/1`:
  - `files[]` holds `path`, `opened`, `error`, `calc` and `roundTrip`.
    - `calc` has `formulaCells`, `checked`, `matched`, `mismatched`, `noOracle`,
      `volatile`, `staleCache`, and `mismatches[]` of `{cell, formula, expected, actual}`.
    - `roundTrip` has `differing[]` and `categories{}`.
  - `totals` is at the top level.
- `staleCache: true` means the file asked for a full recalculation on load, so its
  cached values are not trusted.

## convert

```sh
gridcraft-cli convert IN OUT [--sheet NAME]
```

- Both formats follow the extension: xlsx, csv, tsv, json, html or pdf.
- For csv, tsv and pdf, the **active sheet** is used unless `--sheet` is given. The PDF
  uses that sheet's page setup, so a wide sheet with a chart can run to 2+ pages. The
  reply is `wrote OUT (N bytes, P pages)`.
- One file per call. An existing OUT is overwritten without a prompt. For folders, use
  `scripts/gc_batch.py convert`.

## Registry and live app

```sh
gridcraft-cli commands [--json] [--search X]
gridcraft-cli mcp [--connect PORT] [--in FILE | --sample NAME]
gridcraft-cli send PORT METHOD [json]
```

- `commands --search` matches ids, menu labels and params. Each hit shows the id, the
  label and menu path, its shortcut, and the param shape on the next line. The count
  line (`N commands`) goes to stderr.
- `mcp` without `--connect` serves the same registry over MCP on stdio, against a
  workbook held in the server. This skill doesn't need it.
- `mcp --connect PORT` and `send PORT …` talk to a running app started with
  `GridCraft --control PORT` (or `GRIDCRAFT_CONTROL_PORT`). That channel has no
  authentication, so this skill doesn't use it (see gotchas).
