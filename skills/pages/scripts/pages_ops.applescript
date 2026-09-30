-- Apple Pages operations driven by argv, so no value is ever spliced into script
-- source. Called by the Python helpers through pages_osa.py; usable directly:
--
--   osascript pages_ops.applescript fill DOC.pages [T token value]... [I key image]...
--             [A page x y width image]... [O key value]... [X out.pdf format]... [S] [L prefix]
--   osascript pages_ops.applescript export format [O key value]... -- SRC DST [SRC DST]...
--   osascript pages_ops.applescript text DOC.pages
--   osascript pages_ops.applescript new TEMPLATE_ID OUT.pages
--   osascript pages_ops.applescript close PATH...
--
-- fill: T replaces every occurrence of token (case-sensitive) in body text, text
--   boxes, shapes and table cells, keeping the token's character style. I swaps the
--   image whose accessibility description is key for a new file at the same frame.
--   A adds an image on a page. O sets an export option, X exports, S saves, L sets
--   the token prefix the LEFTOVER check looks for (default "{{").
--   Output lines: "COUNT<TAB>token<TAB>n", "EXPORTED<TAB>path", "LEFTOVER<TAB>text".
-- Documents this script opens are closed again, even on error; documents the user
-- already had open are refused rather than touched.

property leftoverPrefix : "{{"

on run argv
	set timeoutSecs to 300
	try
		set timeoutSecs to (system attribute "PAGES_TIMEOUT") as integer
	end try
	set op to item 1 of argv
	set opArgs to {}
	if (count argv) > 1 then set opArgs to items 2 thru -1 of argv
	with timeout of timeoutSecs seconds
		if op is "fill" then return fillDoc(opArgs)
		if op is "export" then return exportMany(opArgs)
		if op is "text" then return docText(item 1 of opArgs)
		if op is "new" then return newDoc(item 1 of opArgs, item 2 of opArgs)
		if op is "close" then return closePaths(opArgs)
	end timeout
	error "unknown op: " & op number 2
end run

-- ---------------------------------------------------------------- open / close

on findOpenDoc(p)
	tell application id "com.apple.Pages"
		repeat with d in documents
			try
				if POSIX path of ((file of d) as alias) is p then return contents of d
			end try
		end repeat
	end tell
	return missing value
end findOpenDoc

on openOwned(p)
	if findOpenDoc(p) is not missing value then error "already open in Pages (close it first, unsaved edits would conflict): " & p number 3
	tell application id "com.apple.Pages" to return open (POSIX file p as alias)
end openOwned

on closePaths(paths)
	set n to 0
	repeat with p in paths
		set d to findOpenDoc(contents of p)
		if d is not missing value then
			tell application id "com.apple.Pages" to close d saving no
			set n to n + 1
		end if
	end repeat
	return "CLOSED" & tab & n
end closePaths

on newDoc(templateId, outPath)
	tell application id "com.apple.Pages"
		set d to make new document with properties {document template:template id templateId}
		-- Save at once: an unsaved new document is autosaved as "Untitled" into the
		-- iCloud Pages folder and stays there even after close saving no.
		try
			save d in POSIX file outPath
		on error e number n
			close d saving no
			error e number n
		end try
		close d saving no
	end tell
	return "CREATED" & tab & outPath
end newDoc

-- ---------------------------------------------------------------- text replace

-- Replace inside one rich-text object: delete the token's tail, then overwrite its
-- first character, so the value inherits the token's style. A range set
-- ("set characters i thru j to v") is broken in Pages: it writes v into every
-- character of the range.
on replaceIn(rt, tok, val)
	set n to 0
	set L to length of tok
	tell application id "com.apple.Pages"
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

on replaceAll(d, tok, val)
	set n to 0
	tell application id "com.apple.Pages"
		set n to n + (my replaceIn(a reference to (body text of d), tok, val))
		-- Text boxes are shapes too; a second pass over the same text finds nothing.
		repeat with sh in (every shape of d)
			try
				set n to n + (my replaceIn(a reference to (object text of sh), tok, val))
			end try
		end repeat
		repeat with tb in (every table of d)
			repeat with c in (every cell of tb)
				set v to value of c
				if class of v is text then
					considering case
						set hit to v contains tok
					end considering
					if hit then
						set value of c to my replaceText(v, tok, val)
						set n to n + 1
					end if
				end if
			end repeat
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

-- ---------------------------------------------------------------- images

on swapImage(d, key, imgPath)
	set f to POSIX file imgPath as alias
	set n to 0
	tell application id "com.apple.Pages"
		-- "whose description is" is refused by Pages (-1723), so walk the pages.
		-- Images are elements of a page too, which gives the page to recreate on.
		repeat with pg in pages of d
			set targets to {}
			repeat with im in (every image of pg)
				if description of im is key then set end of targets to contents of im
			end repeat
			repeat with im in targets
				set {pos, w, h} to {position of im, width of im, height of im}
				-- "file" of an image is read-only, so replace the image object. New
				-- images can only be made on a page, not on the document.
				delete im
				tell pg to set nim to make new image with properties {file:f, position:pos}
				-- Fit inside the old frame, keeping the new picture's aspect ratio.
				set {nw, nh} to {width of nim, height of nim}
				if nw / nh > w / h then
					set width of nim to w
				else
					set height of nim to h
				end if
				set description of nim to key
				set n to n + 1
			end repeat
		end repeat
	end tell
	if n = 0 then error "no image with description '" & key & "' (set it in Format > Image > Description)" number 5
	return n
end swapImage

on addImage(d, pageNo, x, y, w, imgPath)
	set f to POSIX file imgPath as alias
	tell application id "com.apple.Pages"
		tell page pageNo of d to set nim to make new image with properties {file:f, position:{x, y}}
		if w > 0 then set width of nim to w
	end tell
end addImage

-- ---------------------------------------------------------------- export

on exportDoc(d, outPath, fmt, opts)
	-- Build the file object outside the tell block: inside it Pages tries to resolve
	-- "POSIX file" itself and fails with -1728.
	set dest to POSIX file outPath
	tell application id "com.apple.Pages"
		-- {} is an empty *list*; concatenating records onto it yields a list.
		set props to {} as record
		repeat with kv in opts
			set {k, v} to {item 1 of kv, item 2 of kv}
			if k is "title" then set props to props & {title:v}
			if k is "author" then set props to props & {author:v}
			if k is "genre" then set props to props & {genre:v}
			if k is "language" then set props to props & {language:v}
			if k is "publisher" then set props to props & {publisher:v}
			if k is "cover" then set props to props & {cover:(v is "true")}
			if k is "fixed-layout" then set props to props & {fixed layout:(v is "true")}
			if k is "password" then set props to props & {password:v}
			if k is "password-hint" then set props to props & {password hint:v}
			if k is "comments" then set props to props & {include comments:(v is "true")}
			if k is "annotations" then set props to props & {include annotations:(v is "true")}
			if k is "image-quality" then
				if v is "good" then set props to props & {image quality:Good}
				if v is "better" then set props to props & {image quality:Better}
				if v is "best" then set props to props & {image quality:Best}
			end if
		end repeat
		if fmt is "pdf" then
			set asFmt to PDF
		else if fmt is "docx" then
			set asFmt to Microsoft Word
		else if fmt is "epub" then
			set asFmt to EPUB
		else if fmt is "rtf" then
			set asFmt to formatted text
		else if fmt is "txt" then
			set asFmt to unformatted text
		else
			error "unknown format: " & fmt number 6
		end if
		-- An empty record is not accepted as export options.
		if (count opts) = 0 then
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
			tell application id "com.apple.Pages" to close d saving no
			set end of out to "OK" & tab & src & tab & dst
		on error e
			if d is not missing value then
				try
					tell application id "com.apple.Pages" to close d saving no
				end try
			end if
			set end of out to "ERR" & tab & src & tab & e
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
			set tag to item i of args
			if tag is "T" then
				set {tok, val} to {item (i + 1) of args, item (i + 2) of args}
				set end of out to "COUNT" & tab & tok & tab & replaceAll(d, tok, val)
				set i to i + 3
			else if tag is "I" then
				set end of out to "IMAGE" & tab & (item (i + 1) of args) & tab & swapImage(d, item (i + 1) of args, item (i + 2) of args)
				set i to i + 3
			else if tag is "A" then
				addImage(d, (item (i + 1) of args) as integer, (item (i + 2) of args) as real, (item (i + 3) of args) as real, (item (i + 4) of args) as real, item (i + 5) of args)
				set end of out to "ADDED" & tab & (item (i + 5) of args)
				set i to i + 6
			else if tag is "O" then
				set end of opts to {item (i + 1) of args, item (i + 2) of args}
				set i to i + 3
			else if tag is "X" then
				set end of out to exportDoc(d, item (i + 1) of args, item (i + 2) of args, opts)
				set i to i + 3
			else if tag is "S" then
				set doSave to true
				set i to i + 1
			else if tag is "L" then
				set leftoverPrefix to item (i + 1) of args
				set i to i + 2
			else
				error "bad fill arg: " & tag number 2
			end if
		end repeat
		set end of out to "LEFTOVER" & tab & leftovers(d)
		tell application id "com.apple.Pages"
			if doSave then save d
			close d saving no
		end tell
	on error e number n
		tell application id "com.apple.Pages" to close d saving no
		error e number n
	end try
	return joinLines(out)
end fillDoc

-- ---------------------------------------------------------------- read

on allText(d)
	set parts to {}
	tell application id "com.apple.Pages"
		set end of parts to (body text of d) as text
		repeat with sh in (every shape of d)
			try
				set end of parts to (object text of sh) as text
			end try
		end repeat
		repeat with tb in (every table of d)
			repeat with c in (every cell of tb)
				set v to value of c
				if class of v is text then set end of parts to v
			end repeat
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

on docText(p)
	set d to openOwned(p)
	try
		set s to allText(d)
	on error e number n
		tell application id "com.apple.Pages" to close d saving no
		error e number n
	end try
	tell application id "com.apple.Pages" to close d saving no
	return s
end docText

on joinLines(xs)
	set saved to AppleScript's text item delimiters
	set AppleScript's text item delimiters to linefeed
	set s to xs as text
	set AppleScript's text item delimiters to saved
	return s
end joinLines
