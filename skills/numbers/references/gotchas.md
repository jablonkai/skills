# Numbers gotchas

Each one was reproduced on Numbers Creator Studio 15.4, macOS 27, region hu_HU (decimal
`,`, grouping no-break space). Where the region matters, an English region behaves the
same way with `.` and `,` swapped.

## Values and locale

| Symptom | Cause | What the scripts do |
|---|---|---|
| `"1,250"` becomes 1.25, and `120.5` stays text | Opening a `.csv` in Numbers parses it with the **region's** separators | `numbers-build.py` parses the CSV in Python (`--decimal`, `--thousands`, `--delimiter`) and sends typed numbers |
| `"007"` becomes 7, `"1/2"` becomes 0.5, `"12%"` becomes 0.12, `"2024-01-05"` becomes a date, `"TRUE"` becomes a checkbox | Setting `value` to text makes Numbers parse it like typed input | The builder sets the `text` format on such cells first; a text-format cell keeps the string as it is |
| A CSV cell `=HACK()` is entered as a formula | Same parsing | It goes into a text-format cell, which keeps `=…` as text; `--csv-formulas` opts in to formulas |
| `value` prints `42,5` | AppleScript coerces numbers to text with the region's decimal mark | The scripts use JXA and JSON, which are locale-free |
| `formula` reads `=SZUM(A2:A3)` and `=1÷0` | Formula text comes back in the UI language, with display operators | Writing English names works. Compare values, not formula text |
| An error cell (`=1/0`) reads as `missing value` | Same as an empty cell | `numbers-read` flags cells that have a formula but no value as errors |
| A date written as `2024-01-05` reads back as `2024-01-04 23:00` | Date values cross Apple events with a timezone skew | The reader reports dates as their formatted value |
| Currency shows `1357 Ft`, no decimals, while the value is 1357.0 | `currency` uses the region's currency and rounding. There is no scripted decimal-places setting | Assertions compare `value`. Mention the display rounding to the user |
| Setting cells takes about 19 ms each | One Apple event per cell; there is no bulk write | The builder warns above 5000 cells. Reads are bulk (one event per property per range) |

## Structure

| Symptom | Cause / fix |
|---|---|
| A new document's table is 22 × 7, with a header row **and a header column** | Default template. The builder sets the exact size, `--header-rows` (default 1) and `--header-cols` (default 0) |
| `make new sheet at end of sheets of d` → -10000; `make new sheet with properties {name:…}` → -10006 | Use `tell d to make new sheet`, then `set name of last sheet of d`. In JXA use `d.sheets.push(N.Sheet())` |
| `N.make({new: "table", at: sheet})` in JXA → "can't convert types" | Use `sheet.tables.push(N.Table({rowCount, columnCount}))` |
| A new sheet already contains a table | The builder reuses it rather than adding a second one |
| Header or footer counts don't stick | They must fit inside `row count`. Set the size first, then the header and footer counts |

## Export

| Symptom | Cause / fix |
|---|---|
| XLSX cell `B14` holds what was `B13` in Numbers | Every exported worksheet starts with the **table name in row 1**. The dictionary has no switch to turn this off. Use `numbers-verify.py --numbers-coords`, or shift row numbers by one |
| XLSX gets an extra first sheet ("Összegzés exportálása") | A summary worksheet, added when the document has several sheets or tables. `numbers-export` excludes it unless `--summary-worksheet` |
| XLSX worksheet names are `Main - Second` | One worksheet per table, named `Sheet - Table`; only a table that still has its default name gives the bare sheet name |
| openpyxl shows `ArrayFormula` objects | Numbers writes array formulas. Read `data_only=True` for the cached values, or `.text` for the formula |
| `x.csv` is a folder | A document with several tables exports one CSV per table into that folder. `--flat-csv` gives `x-Sheet-Table.csv` files |
| CSV has `;` separators and `33 Ft` | Numbers' CSV follows the region and writes formatted values. `--raw-csv` writes comma CSV of the raw values |

## Blocking and sandbox

- **A modal alert blocks all scripting.** Causes include a password prompt, "can't be
  opened", a newer-format warning or missing fonts. Every later call times out (-1712).
  The scripts report it with a screenshot (`numbers.sh --dialog`). Ask the user to click
  it away. Don't try to dismiss it by script.
- `NUMBERS_TIMEOUT` bounds each `osascript` process. JXA ignores a `timeout` argument on
  commands, so the process timeout is the stop path.
- In AppleScript, open files **as an alias** (`POSIX file p as alias`), as with Pages
  and Keynote. JXA's `N.open(Path(p))` worked for foreign files in tests.
- A document that is already open is refused. The user's unsaved edits and the
  script's would collide.
- A new document saved right after `make` leaves no "Untitled" copy in the Numbers
  iCloud folder (checked). The builder always saves at once.
- `.numbers` can be a zip file or a package folder. Both are accepted, and anything
  else is refused before Numbers sees it, because opening junk brings up a blocking
  alert.
