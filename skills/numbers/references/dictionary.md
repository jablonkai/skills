# Numbers scripting dictionary

Checked with `sdef "/Applications/Numbers Creator Studio.app"` on **Numbers Creator
Studio 15.4** (bundle id `com.apple.Numbers`). The suites are Numbers Suite, iWork
Suite, iWork Text Suite, Compatibility Suite and CocoaStandard (open, save, close).
Nothing that the documented Numbers dictionary offers is missing from the Creator
Studio edition.

Address the app by bundle id, `application id "com.apple.Numbers"` in AppleScript or
`Application("com.apple.Numbers")` in JXA. The app's display name includes "Creator
Studio" and may change again.

## Object model

```
application ─ documents ─ sheets ─ tables ─ rows / columns / ranges / cells
            └ templates         └ charts, images, shapes, text items, groups, lines, movies, audio clips
```

| Class | Properties (r/o = read only) |
|---|---|
| document | `name`, `file`, `modified`, `id` (r/o), `password protected` (r/o), `document template` (r/o), `active sheet`, `selection` |
| template | `id`, `name` (localized) |
| sheet | `name` |
| table | `name`, `row count`, `column count`, `header row count`, `header column count`, `footer row count`, `cell range` (r/o), `selection range`, plus iWork item `position`, `width`, `height`, `locked`, `parent`; in JXA also `filtered`, `headerRowsFrozen`, `headerColumnsFrozen` |
| range | `name` (r/o, e.g. `"B2:C5"`), `format`, `font name`, `font size`, `text color`, `background color`, `alignment`, `vertical alignment`, `text wrap` |
| cell (a range) | `value`, `formatted value` (r/o), `formula` (r/o), `row`, `column` |
| row / column (ranges) | `address`, `height` / `width` |
| chart | only the iWork item properties: `position`, `width`, `height`, `locked`, `parent` |

The `document` properties call fails in JXA (`doc.properties()` → -10000). Read the
properties one at a time.

## Commands

| Command | Signature | Notes |
|---|---|---|
| `make` | `make new document` / `tell doc to make new sheet` / `make new table with properties {…}` inside `tell sheet …` | `make new sheet at end of sheets of d` and `make new sheet with properties {name:…}` fail. In JXA use `doc.sheets.push(N.Sheet())` and `sheet.tables.push(N.Table({rowCount: …}))`. |
| `add row above` / `add row below` | `add row below row 3` (in a `tell table` block) | Formula references shift to follow |
| `add column before` / `add column after` | `add column after column 2` | |
| `sort` | `sort <table> by column N direction ascending/descending in rows <range>` | Sorts the body rows; empty cells go last |
| `merge` / `unmerge` | `merge range "A5:B5"` | |
| `clear` | `clear range "C2:C4"` | Clears contents and style |
| `transpose` | `transpose` (in a `tell table` block) | Swaps rows and columns |
| `set password` | `set password "pw" to d hint "…" saving in keychain false` | |
| `remove password` | `remove password "pw" from d` | |
| `export` | `export d to POSIX file p as FORMAT with properties {…}` | See below |
| `open` / `save` / `close` | `open (POSIX file p as alias)`, `save d in POSIX file p`, `close d saving no` | Open as an alias (see gotchas) |
| `delete` | `delete table 2 of sheet 1 of d`, `delete chart 1 of …` | |

`value` accepts a number, text, a boolean or a formula string (`"=SUM(A2:A9)"`, with
English function names). Setting `format` before `value` controls how text is
interpreted.

## Enumerations

- **format**: `automatic`, `checkbox`, `currency`, `date and time`, `fraction`,
  `number`, `percent`, `pop up menu`, `scientific`, `slider`, `stepper`, `text`,
  `duration`, `rating`, `numeral system`. In JXA they are the same strings (`"date and
  time"`).
- **alignment**: `auto align`, `center`, `justify`, `left`, `right`. **vertical
  alignment**: `top`, `center`, `bottom`.
- **sort direction**: `ascending`, `descending`.
- **export format**: `Numbers`, `PDF`, `Microsoft Excel`, `CSV`, `Numbers 09`.
- **image quality** (PDF): `Good`, `Better`, `Best`.

## Export options (`with properties`)

| Key (AppleScript / JXA) | Formats | Effect |
|---|---|---|
| `exclude summary worksheet` / `excludeSummaryWorksheet` | XLSX | Leave out the index sheet Numbers adds when a document has several sheets or tables. It is named in the UI language ("Összegzés exportálása"). |
| `password`, `password hint` / `password`, `passwordHint` | XLSX, PDF, Numbers 09 | Open password |
| `image quality` / `imageQuality` | PDF | `Good`, `Better`, `Best` |
| `include comments` / `includeComments` | PDF | Print comments |

Output shapes:

- XLSX: one worksheet per table, named `Sheet - Table`, or just `Sheet` when the table
  still has its default name ("1. táblázat"). The table name is written in row 1. Formulas are English array
  formulas (`<f t="array">SUM(C3:C5)</f>`) with cached values.
- CSV: a single file for one table. For several tables it writes a folder `X.csv/`
  holding `Sheet-Table.csv` files. The list separator comes from the region (`;` where
  `,` is the decimal mark), and cells hold formatted values.
- PDF: every sheet, laid out as printed.

## Not in the dictionary

- **Chart creation or chart data.** `make new chart` fails (-10000), and charts expose
  only their frame. Charts can be counted, moved, resized and deleted. Their type,
  series and data ranges can be changed only in the UI.
- Conditional highlighting, filters (only `filtered`, read only), pivot tables,
  categories, cell borders, per-character text styles in cells, and column widths
  beyond `width`.
- Custom number formats (decimal places, currency code): only the `format` enumeration.
  The currency and its rounding come from the region (`1357 Ft`, no decimals, under
  hu_HU).
