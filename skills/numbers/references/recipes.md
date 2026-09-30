# Raw AppleScript recipes

For what the scripts don't cover. Every snippet here ran against Numbers Creator Studio
15.4, except moving and deleting a chart. No chart can be created by script, so that
part follows the dictionary and wasn't run. Run them with `osascript file.applescript /abs/path.numbers` and read values
from `argv`. Never splice values into the script text.

Always open a **copy**, and close without saving unless the user asked for the edit:

```applescript
on run argv
	set p to item 1 of argv
	tell application id "com.apple.Numbers"
		set d to open (POSIX file p as alias)   -- alias, not a bare POSIX file
		try
			-- ... work on d ...
			save d                                -- only when the edit is wanted
			close d saving no
		on error e number n
			close d saving no
			error e number n
		end try
	end tell
end run
```

## Rows, columns and formulas

```applescript
tell table 1 of sheet 1 of d
	add row below row 2
	add column after column 2
	set value of cell 3 of row 3 to "=A3*2"      -- English function names
	set value of cell "D2" to "=SUM(B2:C2)"
	log (value of cell "D2")                     -- recalculated at once
end tell
```

`formula of cell` reads back in the UI language (`=SZUM(B2:C2)`, `=1÷0`). Compare
values, not formula text.

## Styling a range

```applescript
tell table 1 of sheet 1 of d
	tell range "A1:C1"
		set font name to "Helvetica-Bold"
		set font size to 13
		set background color to {65535, 60000, 40000}   -- 16-bit RGB
		set alignment to center
	end tell
	set text wrap of range "A2:A4" to true
	set format of range "B2:B20" to currency              -- region's currency
end tell
```

## Sort, merge, clear, transpose

```applescript
tell table 1 of sheet 1 of d
	sort by column 2 direction descending    -- body rows only; empty cells go last
	merge range "A5:B5"
	unmerge range "A5:B5"
	clear range "C2:C4"                      -- contents and style
	transpose                                -- rows <-> columns
end tell
```

## A second table, with a cross-table reference

```applescript
tell table 1 of sheet 1 of d to set name to "Costs"
tell sheet 1 of d
	set t2 to make new table with properties {name:"Rates", row count:3, column count:2, header column count:0}
	set value of cell "A2" of t2 to "=SUM(Costs::A2:A4)"   -- Table::range
	set position of t2 to {20, 400}
end tell
```

`numbers-build.py --into --sheet NAME --table NAME` does the same from a CSV.

## A new sheet

```applescript
tell d to make new sheet                 -- not "make new sheet at end of sheets of d"
set name of last sheet of d to "Notes"   -- not "with properties {name:…}"
```

## Password

```applescript
set password "s3cret" to d hint "demo"
log (password protected of d)            -- true
remove password "s3cret" from d
```

Opening a password-protected document by script shows a password prompt. The prompt
blocks every later Apple event (see gotchas).

## Charts

```applescript
tell sheet 1 of d
	log (count charts)
	set position of chart 1 to {40, 300}
	delete chart 1
end tell
```

Charts can't be created, and their data can't be read or set (`make new chart` →
-10000). When the user needs a chart, build the table by script and tell them to insert
the chart in the UI (select the table, then Chart ▸ type). If a picture of the chart is
enough, render it with matplotlib and place the image, or export XLSX and add a chart
with openpyxl.

## JXA equivalents

JXA returns locale-free numbers. AppleScript's `value as text` prints `42,5` under a
comma-decimal region. `scripts/numbers_ops.js` is written in JXA for that reason.

```javascript
const N = Application("com.apple.Numbers");
const d = N.open(Path("/abs/file.numbers"));
const t = d.sheets[0].tables[0];
t.cells["B2"].value = 12.5;
t.ranges["B2:B9"].format = "currency";
const vals = t.ranges["A1:D9"].cells.value();   // one Apple event, row-major
d.sheets.push(N.Sheet());                       // new sheet
d.sheets[0].tables.push(N.Table({ rowCount: 5, columnCount: 3 }));
N.export(d, { to: Path("/abs/out.xlsx"), as: "Microsoft Excel",
              withProperties: { excludeSummaryWorksheet: true } });
d.close({ saving: "no" });
```
