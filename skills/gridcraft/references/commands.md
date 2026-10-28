# Command ids (pinned to GridCraft 0.13.0)

The ids below cover the common jobs. For anything else, or if one of these fails with
`unknown command`, look it up. Never guess a param name: an unknown param fails the run.

```sh
gridcraft-cli commands --search chart          # id, menu path, param shape
gridcraft-cli commands --json | python3 -c 'import json,sys; [print(c) for c in json.load(sys.stdin) if c["id"]=="insert.chart"]'
```

Ranges are A1 strings (`"B2:E6"`, `"Sheet2!A1:C3"`). Most commands take `sheet?`
(name) and act on the active sheet without it. `range?`/`cell?` default to the current
selection, so always pass them explicitly in scripts.

## Files and sheets

| Id | Params |
|---|---|
| `file.new` | `{sample?: budget\|sales\|grades}` |
| `file.open` | `{path, password?, csvAsText?: bool}`: replaces the open workbook |
| `file.saveAs` | `{path}`: .xlsx/.csv/.tsv/.json/.html/.pdf (PDF = active sheet). Prefer `--out` |
| `file.exportCsv` | `{path, sheet?}` |
| `file.properties` | `{title?, subject?, author?, company?, keywords?, description?}` |
| `home.insertSheet` | `{name?, before?: index}`: **the new sheet becomes active** |
| `sheet.rename` | `{sheet?, name}` |
| `sheet.activate` | `{sheet: index \| name}` |
| `sheet.move` | `{sheet?, to: index, copy?: bool}` |
| `home.deleteSheet` | `{sheet?}` |
| `data.fromTextCsv` | `{path \| text, delimiter?, sheet?}`: imports a CSV into a **new sheet as a table** |

## Entering data and formulas

| Id | Params |
|---|---|
| `cell.set` | `{cell, input, sheet?, array?: bool}`: input is text, a number or `=formula` |
| `range.setValues` | `{range: top-left cell, values: [[…]], parse?: true}`: `"=…"` strings become formulas. `parse:false` keeps other strings as text |
| `range.fill` | `{range, input}`: same input in every cell. **Relative references adjust from the active cell, not from `range`**, so `selection.set` the range first or use `edit.autoFill` |
| `edit.autoFill` | `{source: "E2", target: "E2:E9", mode?}`: fill-handle drag. Formulas adjust. Prints no result |
| `edit.fillDown` / `edit.fillRight` | `{range}` |
| `formulas.autoSum` | `{function?: SUM\|AVERAGE\|COUNT\|MAX\|MIN, range?}` |
| `home.insertRows` / `home.insertColumns` | `{rows: "3:5"}` / `{cols: "B:C"}` |
| `home.deleteRows` / `home.deleteColumns` | `{rows}` / `{cols}` |
| `edit.clearContents` | `{range}` |
| `formulas.defineName` | `{name, refersTo: "=Sheet1!$B$2", scope?}` |
| `insert.checkbox` / `cell.toggleCheckbox` | `{range?}` / `{cell?}`: new in 0.13.0. Turns TRUE/FALSE/empty cells into checkboxes (empty becomes FALSE, `num_fmt` `checkbox`); the toggle flips the stored boolean. `check` round-trips clean |
| `formulas.calculateNow` | `{}`: recalculation is automatic. This is only for manual-calc workbooks |

## Number formats and styling

| Id | Params |
|---|---|
| `home.numberFormat` | `{range, format: General\|Number\|Currency\|Accounting\|Short Date\|Long Date\|Time\|Percentage\|Fraction\|Scientific\|Text}` or `{range, code: "0.00"}` |
| `home.percent` / `home.comma` | `{range}` |
| `home.formatCells` | `{range, style: {font?, fill?, borders?, align?, numFmt?, protection?}}`: partial style merged in |
| `home.bold` | `{range, on?: bool}` |
| `home.fontColor` / `home.fillColor` | `{range, color: "#C00000"}` |
| `home.borders` | `{range, preset: bottom\|all\|outside\|thickBottom\|topDoubleBottom\|…, style?}` |
| `home.columnWidth` | `{cols: "A:E", width: px \| chars: 12}` |
| `home.autofitColumnWidth` | `{sheet?, cols: "A:E"}`: **pass `cols`**, because without it nothing changes. Run it before any PDF export |
| `home.cellStyle` | `{range, name: "Total"\|"Heading 1"\|"Good"\|…}` |
| `home.conditionalFormat` | look it up: `commands --search conditional` |
| `view.freezeTopRow` | `{sheet?}` |

`Currency` gives `"$"#,##0.00`. For another currency, pass a `code`, such as
`'#,##0.00 "€"'` or `'[$£-809]#,##0.00'`. Read it back with `cell.get` → `style.num_fmt`.

## Tables

| Id | Params |
|---|---|
| `insert.table` | `{range, header?: true, style?: "TableStyleMedium2", name?}` |
| `home.formatAsTable` | `{range, style, header?}` |
| `table.totalRow` | `{table?, on?: bool}`: **adds a row below the table and writes over whatever is there** |
| `table.totalFunction` | `{table?, column: "Jan", function: sum\|average\|count\|max\|min\|…}` |
| `table.style` / `table.rename` / `table.resize` | `{table?, style}` / `{table?, name}` / `{table?, range}` |
| `table.convertToRange` | `{table?}` |

## Charts

| Id | Params |
|---|---|
| `insert.chart` | `{sheet?: where the chart goes, range, type?: column\|bar\|line\|pie\|doughnut\|area\|scatter\|combo\|…, subtype?: clustered\|stacked\|stacked100\|markers, title?, at?: "H2", width?, height?}` → `{chart: id}` |
| `insert.chartRecommendations` | `{range}` → suggested types |
| `chart.set` | `{chart?: id, type?, title?, legend?: none\|bottom\|…, dataLabels?, xTitle?, yTitle?, at?, width?, height?}` |
| `chart.selectData` | `{chart?, range?, byRows?, categories?}` |
| `chart.switchRowColumn` / `chart.delete` | `{chart?}` |
| `chart.move` | `{chart?, sheet?, at?}` |

`type: "bar"` makes horizontal bars (`info` shows `BarClustered`), and `column` makes
vertical ones (`ColumnClustered`). Include the header row and the label column in
`range`: the first row gives the series names and the first column the categories.
`info` reports the series count, so check that it matches.

## Reading (through run or gc_verify.py)

| Id | Params |
|---|---|
| `sheet.read` | `{range?, sheet?, formulas?, formatted?}` → `{values}` raw by default |
| `cell.get` | `{cell, sheet?}` → `value`, `formula`, `text`, `type`, `style.num_fmt` |
| `document.inspect` | `{}`: the same as `info --json` |
| `formulas.evaluate` | `{formula, cell?}` → value, without changing the sheet |
| `formulas.traceDependents` / `formulas.tracePrecedents` | `{cell}` → cells / ranges |
| `formulas.errorChecking` | `{}` → cells with errors |

## Page setup (PDF output)

| Id | Params |
|---|---|
| `pageLayout.orientation` | `{orientation: portrait\|landscape}` |
| `pageLayout.scaleToFit` | `{width?: pages, height?: pages, scale?}`: `{width: 1}` fits the columns on one page |
| `pageLayout.printArea` | `{range?, clear?}` |
| `pageLayout.margins` | `{preset?: normal\|wide\|narrow}` |
| `pageLayout.headerFooter` | `{header?, footer?: "&CPage &P of &N"}` |

## Avoid in automation

- `automate.runScript` / `automate.trustScripts` run scripts stored inside a workbook.
  Don't trust workbook scripts on the user's behalf. Use your own step list instead.
- Clipboard (`edit.copy` / `edit.paste`) works in one process, but `range.setValues` and
  `edit.autoFill` are deterministic and need no selection state.
