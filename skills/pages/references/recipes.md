# Raw AppleScript recipes

For what the scripts don't cover. Every snippet ran against Pages 15.4. Run it with
`osascript file.applescript arg…`, and pass paths and values as `argv`. Never splice
user text into the script source.

Wrap each run in `with timeout` and close what you open. If a call hangs, run
`bash scripts/pages.sh --dialog`.

## New document with styled text, a text box and a table

```applescript
on run argv
	set outPath to item 1 of argv
	with timeout of 120 seconds
		tell application id "com.apple.Pages"
			set d to make new document with properties {document template:template id "Application/Blank/ISO"}
			save d in POSIX file outPath -- at once, or an Untitled copy lands in iCloud
			set body text of d to "Quarterly report" & return & "Summary paragraph."
			-- set properties on the element directly; "tell paragraph 1 … set color" fails (-10003)
			set font of paragraph 1 of body text of d to "Helvetica-Bold"
			set size of paragraph 1 of body text of d to 24
			set color of paragraph 1 of body text of d to {0, 26000, 52000} -- 16-bit RGB
			tell page 1 of d
				make new text item with properties {object text:"Note", position:{72, 500}, width:300, height:60}
				set t to make new table with properties {row count:3, column count:2, position:{72, 200}}
			end tell
			set rowsData to {{"Region", "Sales"}, {"North", "120"}, {"South", "95"}}
			repeat with r from 1 to 3
				repeat with c from 1 to 2
					set value of cell c of row r of t to item c of item r of rowsData
				end repeat
			end repeat
			save d
			close d saving no
		end tell
	end timeout
end run
```

Numeric-looking strings become numbers in cells: `"95"` reads back as `95.0`.

## Read a document's structure

```applescript
tell application id "com.apple.Pages"
	set d to open (POSIX file p as alias)
	set info to {count pages of d, count sections of d, count images of d, ¬
		count tables of d, count text items of d, document body of d}
	set tags to tag of every placeholder text of d -- the template's sample texts
	close d saving no
end tell
```

`document body` true = a word-processing document, false = page layout.

## Password protect

```applescript
set password "secret" to d hint "the usual"
remove password "secret" from d
```

Opening a protected document later shows a password dialog, which blocks scripting.
Export with `pages-export.py --password` when only the PDF or DOCX needs protection.

## Styling part of a paragraph

Character ranges can be read and styled, just not *set* as text:

```applescript
set font of characters 1 thru 7 of paragraph 2 of body text of d to "Helvetica-Bold"
```

To find the indices, take `offset of "needle" in (body text of d as text)` inside
`considering case`.

## Everything the scripts do

`scripts/pages_ops.applescript` is plain AppleScript and can be read as a reference:
`replaceIn` (the style-keeping replace), `swapImage`, `addImage`, `exportDoc` (the
record-building for export options), `openOwned` (the refusal to touch documents the
user has open).
