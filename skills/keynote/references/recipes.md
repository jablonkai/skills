# Raw AppleScript recipes

For what the scripts don't cover. Every snippet ran against Keynote 15.4. Run it with
`osascript file.applescript arg…`, and pass paths and values as `argv`. Never splice
user text into the script source.

Wrap each run in `with timeout` and close what you open. If a call hangs, run
`bash scripts/keynote.sh --dialog`. Find theme ids with `keynote.sh --themes` and
layout indexes with `keynote.sh --layouts THEME`.

## New deck with a styled text box, a table, a chart and a transition

```applescript
on run argv
	set dest to POSIX file (item 1 of argv)
	with timeout of 120 seconds
		tell application id "com.apple.Keynote"
			set d to make new document with properties {document theme:(first theme whose id is "Application/21_BasicWhite/Standard")}
			save d in dest -- at once, or an Untitled copy lands in iCloud
			set s to make new slide at end of slides of d with properties {base layout:slide layout 10 of d}
			set object text of default title item of s to "Results"
			tell s to set tx to make new text item with properties {object text:"Q3 revenue up 12%", position:{80, 600}, width:600, height:80}
			set size of object text of tx to 36
			set color of object text of tx to {0, 26000, 52000} -- 16-bit RGB
			set font of word 1 of object text of tx to "Helvetica-Bold" -- PostScript name
			tell s to set t to make new table with properties {row count:3, column count:2, position:{80, 200}}
			set rowsData to {{"Region", "Sales"}, {"North", "120"}, {"South", "95"}}
			repeat with i from 1 to 3
				repeat with c from 1 to 2
					set value of cell c of row i of t to item c of item i of rowsData
				end repeat
			end repeat
			tell s to add chart row names {"2024", "2025"} column names {"A", "B"} data {{1, 2}, {3, 4}} type vertical_bar_2d group by chart row
			set transition properties of s to {transition effect:dissolve, transition duration:1.5, automatic transition:false}
			set tp to transition properties of s -- read a record property into a variable first
			set eff to (transition effect of tp) as text -- inside the tell: the term is Keynote's
			duplicate s to after s
			save d
			close d saving no
		end tell
	end timeout
	return eff
end run
```

"120" typed into a cell becomes a number: `value` reads back as a real, so use
`formatted value` for the shown text.

## One slide per picture (instead of the broken `make image slides`)

```applescript
on run argv
	with timeout of 300 seconds
		tell application id "com.apple.Keynote"
			set d to open (POSIX file (item 1 of argv) as alias)
			repeat with p in (items 2 thru -1 of argv)
				set f to POSIX file (contents of p) as alias
				-- a layout with a photo placeholder: its index from keynote.sh --layouts
				set s to make new slide at end of slides of d with properties {base layout:slide layout 16 of d}
				set file name of image 1 of s to f -- fills the placeholder frame
			end repeat
			save d
			close d saving no
		end tell
	end timeout
end run
```

## Re-theme a deck, show slide numbers, swap a placeholder picture

```applescript
on run argv
	with timeout of 120 seconds
		tell application id "com.apple.Keynote"
			set d to open (POSIX file (item 1 of argv) as alias)
			set document theme of d to (first theme whose id is "Application/20_BasicBlack/Standard")
			set slide numbers showing of d to true
			set base layout of slide 2 of d to slide layout 6 of d -- a layout with a photo
			set file name of image 1 of slide 2 of d to (POSIX file (item 2 of argv) as alias)
			save d
			close d saving no
		end tell
	end timeout
end run
```

Re-theming keeps each slide's layout by position in the new theme's set, so check the
result: `keynote-verify.py deck.key --show`.

## Movie export

```applescript
on run argv
	set dest to POSIX file (item 2 of argv)
	with timeout of 1800 seconds
		tell application id "com.apple.Keynote"
			set d to open (POSIX file (item 1 of argv) as alias)
			export d to dest as QuickTime movie with properties {movie format:format1080p, movie codec:h264, movie framerate:FPS30}
			close d saving no
		end tell
	end timeout
end run
```

`keynote-export.py deck.key --to m4v --movie-format 1080p` does the same.
