-- Process one image in Pixelmator Pro: open, apply ops, resize, export, close.
-- usage: osascript pxm-process.applescript IN OUT FORMAT QUALITY OPS RESIZE
--   FORMAT  png|jpeg|heic|webp|tiff|psd|avif|pdf|gif|pxd
--   QUALITY 1-100 for jpeg/heic/webp/avif, 0 = app default
--   OPS     comma list run in order: remove-bg,super-res,enhance,denoise,
--           auto-light,auto-color,auto-white-balance,trim (or "" for none)
--   RESIZE  "" | WxH (exact) | wN (width, keep aspect) | hN | fitN (long edge)
-- Prints one JSON line. The input file is never saved; the document is always closed.

on run argv
	if (count of argv) < 6 then error "usage: IN OUT FORMAT QUALITY OPS RESIZE" number 64
	set {inPath, outPath, fmt, quality, ops, resizeSpec} to items 1 thru 6 of argv
	set quality to quality as integer
	set t0 to current date
	-- Coerce the path here, outside the tell block: "POSIX file inPath" inside it is
	-- resolved by the sandboxed app and arrives without a sandbox grant, so the open
	-- fails with "The document is damaged" for any file it has not opened before.
	set inFile to inPath as POSIX file
	-- ML operations on large images can outlast the default 120 s Apple Event timeout;
	-- the runner's own --timeout is the real limit.
	with timeout of 7200 seconds
	tell application "Pixelmator Pro"
		set d to open inFile
		try
			set w0 to (width of d) as integer
			set h0 to (height of d) as integer
			set AppleScript's text item delimiters to ","
			set opList to text items of ops
			set AppleScript's text item delimiters to ""
			repeat with op in opList
				set op to op as text
				if op is "remove-bg" then
					remove background d
				else if op is "super-res" then
					super resolution d
				else if op is "enhance" then
					enhance d
				else if op is "denoise" then
					denoise d
				else if op is "auto-light" then
					auto light d
				else if op is "auto-color" then
					auto color balance d
				else if op is "auto-white-balance" then
					auto white balance d
				else if op is "trim" then
					trim canvas d
				else if op is not "" then
					error "unknown op: " & op number 64
				end if
			end repeat
			my resizeDoc(d, resizeSpec)
			my exportDoc(d, outPath, fmt, quality)
			set w1 to (width of d) as integer
			set h1 to (height of d) as integer
			close d saving no
		on error msg number n
			close d saving no
			error msg number n
		end try
	end tell
	end timeout
	set secs to (current date) - t0
	return "{\"in\":" & my q(inPath) & ",\"out\":" & my q(outPath) & ",\"in_size\":[" & w0 & "," & h0 & "],\"out_size\":[" & w1 & "," & h1 & "],\"seconds\":" & secs & "}"
end run

on resizeDoc(d, spec)
	if spec is "" then return
	with timeout of 7200 seconds
	tell application "Pixelmator Pro"
		set w to (width of d) as integer
		set h to (height of d) as integer
		if spec starts with "fit" then
			set n to (text 4 thru -1 of spec) as integer
			if w ≥ h then
				set nw to n
				set nh to round (h * n / w) rounding as taught in school
			else
				set nh to n
				set nw to round (w * n / h) rounding as taught in school
			end if
		else if spec starts with "w" then
			set nw to (text 2 thru -1 of spec) as integer
			set nh to round (h * nw / w) rounding as taught in school
		else if spec starts with "h" then
			set nh to (text 2 thru -1 of spec) as integer
			set nw to round (w * nh / h) rounding as taught in school
		else if spec contains "x" then
			set AppleScript's text item delimiters to "x"
			set nw to (text item 1 of spec) as integer
			set nh to (text item 2 of spec) as integer
			set AppleScript's text item delimiters to ""
		else
			error "bad resize spec: " & spec number 64
		end if
		if nw is not w or nh is not h then resize image d width nw height nh algorithm lanczos
	end tell
	end timeout
end resizeDoc

on exportDoc(d, outPath, fmt, quality)
	set f to outPath as POSIX file
	with timeout of 7200 seconds
	tell application "Pixelmator Pro"
		if fmt is "pxd" then
			save d in f
			return
		end if
		if quality > 0 then
			set opts to {compression factor:quality}
		else
			set opts to {}
		end if
		if fmt is "png" then
			export d to f as PNG
		else if fmt is "jpeg" or fmt is "jpg" then
			export d to f as JPEG with properties opts
		else if fmt is "heic" then
			export d to f as HEIC with properties opts
		else if fmt is "webp" then
			export d to f as WebP with properties opts
		else if fmt is "avif" then
			export d to f as AVIF with properties opts
		else if fmt is "tiff" or fmt is "tif" then
			export d to f as TIFF
		else if fmt is "psd" then
			export d to f as PSD
		else if fmt is "pdf" then
			export d to f as PDF
		else if fmt is "gif" then
			export d to f as GIF
		else
			error "unknown format: " & fmt number 64
		end if
	end tell
	end timeout
end exportDoc

on q(s)
	set AppleScript's text item delimiters to "\\"
	set parts to text items of s
	set AppleScript's text item delimiters to "\\\\"
	set s to parts as text
	set AppleScript's text item delimiters to "\""
	set parts to text items of s
	set AppleScript's text item delimiters to "\\\""
	set s to parts as text
	set AppleScript's text item delimiters to ""
	return "\"" & s & "\""
end q
