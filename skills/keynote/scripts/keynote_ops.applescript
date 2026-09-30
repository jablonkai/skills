-- Apple Keynote operations driven by argv, so no value is ever spliced into script
-- source. Called by the Python helpers through keynote_osa.py; usable directly:
--
--   osascript keynote_ops.applescript layouts THEME_ID SCRATCH.key
--   osascript keynote_ops.applescript build OUT.key THEME_ID [slide commands]... [O k v]... [X out fmt]...
--   osascript keynote_ops.applescript fill DOC.key [T token value]... [K n true|false]...
--             [M from to]... [D n]... [O k v]... [X out fmt]... [S] [L prefix]
--   osascript keynote_ops.applescript export FMT [O key value]... -- SRC DST [SRC DST]...
--   osascript keynote_ops.applescript info DOC.key
--   osascript keynote_ops.applescript close PATH...
--
-- build slide commands: SL layoutIndex starts a slide (the first reuses the new
--   document's own slide 1), then for that slide: TI title, BO body, NO notes,
--   IM image (fills the layout's first photo placeholder, else is placed in the right
--   half), SK (skipped). Tags differ by more than case: AppleScript's "is" ignores it.
-- fill: T replaces every occurrence of token (case-sensitive) in text items, shapes,
--   tables, groups and presenter notes of every slide, keeping the token's character
--   style. K sets skipped, M moves slide `from` to position `to`, D deletes slide n,
--   all by current slide number in argument order. S saves, L sets the prefix the
--   LEFTOVER check looks for (default "{{").
-- Output lines are TAB-separated; text fields are escaped (\n, \t, \\).
-- Documents this script opens are closed again, even on error; documents the user
-- already had open are refused rather than touched.

property leftoverPrefix : "{{"

on run argv
	set timeoutSecs to 300
	try
		set timeoutSecs to (system attribute "KEYNOTE_TIMEOUT") as integer
	end try
	set op to item 1 of argv
	set opArgs to {}
	if (count argv) > 1 then set opArgs to items 2 thru -1 of argv
	with timeout of timeoutSecs seconds
		if op is "layouts" then return themeLayouts(item 1 of opArgs, item 2 of opArgs)
		if op is "build" then return buildDoc(opArgs)
		if op is "fill" then return fillDoc(opArgs)
		if op is "export" then return exportMany(opArgs)
		if op is "info" then return docInfo(item 1 of opArgs)
		if op is "close" then return closePaths(opArgs)
	end timeout
	error "unknown op: " & op number 2
end run

-- ---------------------------------------------------------------- open / close

on findOpenDoc(p)
	tell application id "com.apple.Keynote"
		repeat with d in documents
			try
				if POSIX path of ((file of d) as alias) is p then return contents of d
			end try
		end repeat
	end tell
	return missing value
end findOpenDoc

on openOwned(p)
	if findOpenDoc(p) is not missing value then error "already open in Keynote (close it first, unsaved edits would conflict): " & p number 3
	-- An alias carries the sandbox read grant; a bare POSIX file makes Keynote show
	-- an error alert that blocks every later Apple Event.
	set f to POSIX file p as alias
	tell application id "com.apple.Keynote" to return open f
end openOwned

on closeQuietly(d)
	if d is missing value then return
	try
		tell application id "com.apple.Keynote" to close d saving no
	end try
end closeQuietly

on closePaths(paths)
	set n to 0
	repeat with p in paths
		set d to findOpenDoc(contents of p)
		if d is not missing value then
			tell application id "com.apple.Keynote" to close d saving no
			set n to n + 1
		end if
	end repeat
	return "CLOSED" & tab & n
end closePaths

on newDoc(themeId, outPath)
	set dest to POSIX file outPath
	tell application id "com.apple.Keynote"
		set thm to first theme whose id is themeId
		set d to make new document with properties {document theme:thm}
		-- Save at once: an unsaved new document is autosaved as "Untitled" into the
		-- iCloud Keynote folder and stays there even after close saving no.
		try
			save d in dest
		on error e number n
			close d saving no
			error e number n
		end try
	end tell
	return d
end newDoc

-- ---------------------------------------------------------------- layouts

on themeLayouts(themeId, scratchPath)
	set d to newDoc(themeId, scratchPath)
	set out to {}
	try
		tell application id "com.apple.Keynote"
			set out to {"SIZE" & tab & (width of d) & tab & (height of d)}
			set n to count slide layouts of d
			repeat with i from 1 to n
				set lay to slide layout i of d
				set s to make new slide at end of slides of d with properties {base layout:lay}
				set end of out to "LAYOUT" & tab & i & tab & my esc(name of lay) & tab & (title showing of s) & tab & (body showing of s) & tab & (count images of s)
			end repeat
			close d saving no
		end tell
	on error e number n
		closeQuietly(d)
		error e number n
	end try
	return joinLines(out)
end themeLayouts

-- ---------------------------------------------------------------- build

on buildDoc(args)
	set outPath to item 1 of args
	set d to newDoc(item 2 of args, outPath)
	set out to {}
	try
		tell application id "com.apple.Keynote"
			set W to width of d
			set H to height of d
		end tell
		set opts to {}
		set s to missing value
		set slideNo to 0
		set i to 3
		repeat while i ≤ (count args)
			set tg to item i of args
			if tg is "SL" then
				set layIdx to (item (i + 1) of args) as integer
				set slideNo to slideNo + 1
				tell application id "com.apple.Keynote"
					if slideNo = 1 then
						set s to slide 1 of d
						set base layout of s to slide layout layIdx of d
					else
						set s to make new slide at end of slides of d with properties {base layout:slide layout layIdx of d}
					end if
				end tell
				set i to i + 2
			else if tg is "TI" then
				tell application id "com.apple.Keynote"
					if not (title showing of s) then set title showing of s to true
					set object text of default title item of s to item (i + 1) of args
				end tell
				set i to i + 2
			else if tg is "BO" then
				tell application id "com.apple.Keynote"
					if not (body showing of s) then set body showing of s to true
					set object text of default body item of s to item (i + 1) of args
				end tell
				set i to i + 2
			else if tg is "NO" then
				tell application id "com.apple.Keynote" to set presenter notes of s to item (i + 1) of args
				set i to i + 2
			else if tg is "IM" then
				set end of out to placeImage(s, item (i + 1) of args, W, H, slideNo)
				set i to i + 2
			else if tg is "SK" then
				tell application id "com.apple.Keynote" to set skipped of s to true
				set i to i + 1
			else if tg is "O" then
				set end of opts to {item (i + 1) of args, item (i + 2) of args}
				set i to i + 3
			else if tg is "X" then
				tell application id "com.apple.Keynote" to save d
				set end of out to exportDoc(d, item (i + 1) of args, item (i + 2) of args, opts)
				set i to i + 3
			else
				error "bad build arg: " & tg number 2
			end if
		end repeat
		tell application id "com.apple.Keynote"
			save d
			set end of out to "SLIDES" & tab & (count slides of d)
			close d saving no
		end tell
	on error e number n
		closeQuietly(d)
		error e number n
	end try
	return joinLines(out)
end buildDoc

on placeImage(s, imgPath, W, H, slideNo)
	set f to POSIX file imgPath as alias
	tell application id "com.apple.Keynote"
		if (count images of s) > 0 then
			-- A photo placeholder: the new picture fills its frame (cropped by the
			-- placeholder mask), so the layout stays intact.
			set file name of image 1 of s to f
			return "IMAGE" & tab & slideNo & tab & "placeholder"
		end if
		tell s to set im to make new image with properties {file:f}
		-- No placeholder: fit into the right half, below the title band.
		set {bw, bh} to {W * 0.42, H * 0.62}
		set {iw, ih} to {width of im, height of im}
		if iw / ih > bw / bh then
			set width of im to bw
		else
			set height of im to bh
		end if
		set {iw, ih} to {width of im, height of im}
		set position of im to {round (W * 0.54 + (bw - iw) / 2), round (H * 0.26 + (bh - ih) / 2)}
	end tell
	return "IMAGE" & tab & slideNo & tab & "placed"
end placeImage

-- ---------------------------------------------------------------- text replace

-- Replace inside one rich-text object: delete the token's tail, then overwrite its
-- first character, so the value inherits the token's style. A range set
-- ("set characters i thru j to v") is broken in Keynote: it writes v into every
-- character of the range.
on replaceIn(rt, tok, val)
	set n to 0
	set L to length of tok
	tell application id "com.apple.Keynote"
		repeat
			set s to rt as text
			considering case
				set o to offset of tok in s
			end considering
			if o = 0 then exit repeat
			if val is "" then
				delete characters o thru (o + L - 1) of rt
			else
				if L > 1 then delete characters (o + 1) thru (o + L - 1) of rt
				set character o of rt to val
			end if
			set n to n + 1
			if n > 10000 then error "runaway replace for " & tok number 4
		end repeat
	end tell
	return n
end replaceIn

on replaceInTables(container, tok, val)
	set n to 0
	tell application id "com.apple.Keynote"
		repeat with tb in (every table of container)
			repeat with c in (every cell of tb)
				set v to value of c
				if class of v is text then
					considering case
						set hit to v contains tok
					end considering
					if hit then
						-- Pin the cell to text first: with "automatic" format Keynote parses
						-- "1 250 000 Ft" into the real 1250000, and a date-like value into a date.
						set format of c to text
						set value of c to my replaceText(v, tok, val)
						set n to n + 1
					end if
				end if
			end repeat
		end repeat
	end tell
	return n
end replaceInTables

on replaceInContainer(container, tok, val)
	set n to 0
	tell application id "com.apple.Keynote"
		-- A placeholder is listed more than once among the text items; after the first
		-- pass the others hold no token any more, so nothing is counted twice.
		repeat with tx in (every text item of container)
			try
				set n to n + (my replaceIn(a reference to (object text of tx), tok, val))
			end try
		end repeat
		repeat with sh in (every shape of container)
			try
				set n to n + (my replaceIn(a reference to (object text of sh), tok, val))
			end try
		end repeat
		set n to n + (my replaceInTables(container, tok, val))
	end tell
	return n
end replaceInContainer

on replaceAll(d, tok, val)
	set n to 0
	tell application id "com.apple.Keynote"
		repeat with s in (every slide of d)
			set n to n + (my replaceInContainer(s, tok, val))
			repeat with g in (every group of s)
				set n to n + (my replaceInContainer(g, tok, val))
			end repeat
			set n to n + (my replaceIn(a reference to (presenter notes of s), tok, val))
		end repeat
	end tell
	return n
end replaceAll

on replaceText(s, tok, val)
	set saved to AppleScript's text item delimiters
	considering case
		set AppleScript's text item delimiters to tok
		set parts to text items of s
		set AppleScript's text item delimiters to val
		set s to parts as text
	end considering
	set AppleScript's text item delimiters to saved
	return s
end replaceText

-- ---------------------------------------------------------------- export

on exportDoc(d, outPath, fmt, opts)
	-- Build the file object outside the tell block: inside it Keynote tries to
	-- resolve "POSIX file" itself.
	set dest to POSIX file outPath
	tell application id "com.apple.Keynote"
		-- {} is an empty *list*; concatenating records onto it yields a list.
		set props to {} as record
		repeat with kv in opts
			set {k, v} to {item 1 of kv, item 2 of kv}
			if k is "notes" then set props to props & {export style:SlideWithNotes}
			if k is "handouts" then set props to props & {export style:Handouts}
			if k is "include-skipped" then set props to props & {skipped slides:(v is "true")}
			if k is "all-stages" then set props to props & {all stages:(v is "true")}
			if k is "slide-numbers" then set props to props & {slide numbers:(v is "true")}
			if k is "comments" then set props to props & {include comments:(v is "true")}
			if k is "password" then set props to props & {password:v}
			if k is "password-hint" then set props to props & {password hint:v}
			if k is "pdf-quality" then
				if v is "good" then set props to props & {PDF image quality:Good}
				if v is "better" then set props to props & {PDF image quality:Better}
				if v is "best" then set props to props & {PDF image quality:Best}
			end if
			if k is "movie-format" then
				if v is "360p" then set props to props & {movie format:format360p}
				if v is "540p" then set props to props & {movie format:format540p}
				if v is "720p" then set props to props & {movie format:format720p}
				if v is "1080p" then set props to props & {movie format:format1080p}
				if v is "2160p" then set props to props & {movie format:format2160p}
				if v is "native" then set props to props & {movie format:native size}
			end if
			if k is "movie-codec" then
				if v is "h264" then set props to props & {movie codec:h264}
				if v is "hevc" then set props to props & {movie codec:HEVC}
				if v is "prores422" then set props to props & {movie codec:AppleProRes422}
				if v is "prores4444" then set props to props & {movie codec:AppleProRes4444}
			end if
		end repeat
		if fmt is "pdf" then
			set asFmt to PDF
		else if fmt is "pptx" then
			set asFmt to Microsoft PowerPoint
		else if fmt is "m4v" then
			set asFmt to QuickTime movie
		else if fmt is "png" or fmt is "jpeg" or fmt is "tiff" then
			set asFmt to slide images
			if fmt is "png" then set props to props & {image format:PNG}
			if fmt is "jpeg" then set props to props & {image format:JPEG}
			if fmt is "tiff" then set props to props & {image format:TIFF}
		else
			error "unknown format: " & fmt number 6
		end if
		-- An empty record is not accepted as export options.
		if (count props) = 0 then
			export d to dest as asFmt
		else
			export d to dest as asFmt with properties props
		end if
	end tell
	return "EXPORTED" & tab & outPath
end exportDoc

on exportMany(args)
	set fmt to item 1 of args
	set opts to {}
	set i to 2
	repeat while item i of args is not "--"
		if item i of args is "O" then
			set end of opts to {item (i + 1) of args, item (i + 2) of args}
			set i to i + 3
		else
			error "bad export arg: " & item i of args number 2
		end if
	end repeat
	set i to i + 1
	set out to {}
	repeat while i < (count args)
		set {src, dst} to {item i of args, item (i + 1) of args}
		set i to i + 2
		set d to missing value
		try
			set d to my openOwned(src)
			my exportDoc(d, dst, fmt, opts)
			tell application id "com.apple.Keynote"
				set sc to count slides of d
				set sk to count (slides of d whose skipped is true)
			end tell
			closeQuietly(d)
			set end of out to "OK" & tab & src & tab & dst & tab & sc & tab & sk
		on error e
			closeQuietly(d)
			set end of out to "ERR" & tab & src & tab & my esc(e)
		end try
	end repeat
	return joinLines(out)
end exportMany

-- ---------------------------------------------------------------- fill

on fillDoc(args)
	set p to item 1 of args
	set d to openOwned(p)
	set out to {}
	try
		set opts to {}
		set doSave to false
		set i to 2
		repeat while i ≤ (count args)
			set tg to item i of args
			if tg is "T" then
				set {tok, val} to {item (i + 1) of args, item (i + 2) of args}
				set end of out to "COUNT" & tab & my esc(tok) & tab & replaceAll(d, tok, val)
				set i to i + 3
			else if tg is "K" then
				tell application id "com.apple.Keynote" to set skipped of slide ((item (i + 1) of args) as integer) of d to ((item (i + 2) of args) is "true")
				set i to i + 3
			else if tg is "M" then
				set {a, b} to {(item (i + 1) of args) as integer, (item (i + 2) of args) as integer}
				tell application id "com.apple.Keynote"
					if b = 1 then
						move slide a of d to before slide 1 of d
					else if a < b then
						move slide a of d to after slide b of d
					else
						move slide a of d to before slide b of d
					end if
				end tell
				set i to i + 3
			else if tg is "D" then
				tell application id "com.apple.Keynote" to delete slide ((item (i + 1) of args) as integer) of d
				set i to i + 2
			else if tg is "O" then
				set end of opts to {item (i + 1) of args, item (i + 2) of args}
				set i to i + 3
			else if tg is "X" then
				set end of out to exportDoc(d, item (i + 1) of args, item (i + 2) of args, opts)
				set i to i + 3
			else if tg is "S" then
				set doSave to true
				set i to i + 1
			else if tg is "L" then
				set leftoverPrefix to item (i + 1) of args
				set i to i + 2
			else
				error "bad fill arg: " & tg number 2
			end if
		end repeat
		set end of out to "LEFTOVER" & tab & esc(leftovers(d))
		tell application id "com.apple.Keynote"
			set end of out to "SLIDES" & tab & (count slides of d)
			if doSave then save d
			close d saving no
		end tell
	on error e number n
		closeQuietly(d)
		error e number n
	end try
	return joinLines(out)
end fillDoc

-- ---------------------------------------------------------------- read

-- Every distinct text on a container. Placeholders show up more than once among the
-- text items, and hidden ones come back with a 0x0 frame, so both are filtered.
on containerTexts(container)
	set seen to {}
	set parts to {}
	tell application id "com.apple.Keynote"
		set objs to (every text item of container) & (every shape of container)
		repeat with o in objs
			try
				set t to (object text of o) as text
				set {w, h} to {width of o, height of o}
				set pos to position of o
				set k to t & "|" & (item 1 of pos) & "," & (item 2 of pos) & "," & w & "," & h
				if t is not "" and w > 0 and k is not in seen then
					set end of seen to k
					set end of parts to t
				end if
			end try
		end repeat
		-- formatted value: a numeric cell's value is a real ("120" reads back as 120.0,
		-- "120,0" under a comma-decimal locale); the formatted value is what is shown.
		repeat with tb in (every table of container)
			repeat with c in (every cell of tb)
				set v to formatted value of c
				if v is not missing value and v is not "" then set end of parts to v as text
			end repeat
		end repeat
	end tell
	return parts
end containerTexts

on slideTexts(s)
	set parts to containerTexts(s)
	tell application id "com.apple.Keynote"
		repeat with g in (every group of s)
			set parts to parts & my containerTexts(g)
		end repeat
	end tell
	return parts
end slideTexts

on allText(d)
	set parts to {}
	tell application id "com.apple.Keynote"
		repeat with s in (every slide of d)
			set parts to parts & my slideTexts(s)
			set end of parts to (presenter notes of s) as text
		end repeat
	end tell
	return joinLines(parts)
end allText

on leftovers(d)
	-- Report the first unreplaced token start; the caller decides if that is an error.
	set s to allText(d)
	set o to offset of leftoverPrefix in s
	if o = 0 then return ""
	set e to o + 40
	if e > (length of s) then set e to length of s
	return text o thru e of s
end leftovers

on docInfo(p)
	set d to openOwned(p)
	set out to {}
	try
		tell application id "com.apple.Keynote"
			set end of out to "DOC" & tab & my esc(id of document theme of d) & tab & my esc(name of document theme of d) & tab & (width of d) & tab & (height of d)
			set i to 0
			repeat with s in (every slide of d)
				set i to i + 1
				set ttl to ""
				if title showing of s then set ttl to (object text of default title item of s) as text
				set bdy to ""
				if body showing of s then set bdy to (object text of default body item of s) as text
				set end of out to "SLIDE" & tab & i & tab & (skipped of s) & tab & my esc(name of base layout of s) & tab & (count images of s) & tab & my esc(ttl) & tab & my esc(bdy) & tab & my esc((presenter notes of s) as text)
				repeat with t in my slideTexts(s)
					set end of out to "TEXT" & tab & i & tab & my esc(contents of t)
				end repeat
			end repeat
		end tell
	on error e number n
		closeQuietly(d)
		error e number n
	end try
	closeQuietly(d)
	return joinLines(out)
end docInfo

-- ---------------------------------------------------------------- util

on esc(s)
	set s to s as text
	set s to replaceText(s, "\\", "\\\\")
	set s to replaceText(s, tab, "\\t")
	set s to replaceText(s, return & linefeed, "\\n")
	set s to replaceText(s, return, "\\n")
	set s to replaceText(s, linefeed, "\\n")
	set s to replaceText(s, character id 8233, "\\n")
	set s to replaceText(s, character id 8232, "\\n")
	return s
end esc

on joinLines(xs)
	set saved to AppleScript's text item delimiters
	set AppleScript's text item delimiters to linefeed
	set s to xs as text
	set AppleScript's text item delimiters to saved
	return s
end joinLines
