# Recipes

Every recipe is a complete script that takes its paths as arguments. Save it as
`x.applescript` and run it through the runner, which dismisses alerts and enforces
the timeout:

```bash
bash scripts/pxm.sh run x.applescript --timeout 900 ARG1 ARG2 ...
```

All of them were run against Pixelmator Pro 3.8. Paths must be absolute. Each script
coerces them **before** the `tell` block (see gotchas). For the jobs the bundled
scripts already cover (cut-outs, upscales, batch convert, new layered designs), use
`pxm-batch.py` and `pxm-compose.py` rather than these recipes.

## Contents
- [Fill a .pxd template](#fill-a-pxd-template)
- [Colour grade and vignette](#colour-grade-and-vignette)
- [Upscale to an exact size](#upscale-to-an-exact-size)
- [Cut-out on a new background](#cut-out-on-a-new-background)
- [Styled headline with shadow and a highlighted word](#styled-headline-with-shadow-and-a-highlighted-word)
- [Watermark every image in a folder](#watermark-every-image-in-a-folder)
- [Web export](#web-export)

## Fill a .pxd template

Change a named text layer, swap the photo while keeping its adjustments and effects,
and export. Run it once per row of a data file.

```applescript
on run argv
	set {tplPath, photoPath, newText, outPath} to argv
	set tplFile to tplPath as POSIX file
	set photoFile to photoPath as POSIX file
	set outFile to outPath as POSIX file
	with timeout of 600 seconds
		tell application "Pixelmator Pro"
			set d to open tplFile
			try
				tell d
					set text content of text layer "headline" to newText -- keeps font/size/colour
					set L to image layer "photo" -- id-based reference
					replace image L with photoFile scale mode scale to fill
					set name of L to "photo" -- replace image renamed it after the file
				end tell
				export d to outFile as PNG
			on error msg number n
				close d saving no
				error msg number n
			end try
			close d saving no -- the template stays untouched
		end tell
	end timeout
	return outPath
end run
```

To change a phrase wherever it appears in the document, use
`replace d text "{{name}}" with "Ada"`.

## Colour grade and vignette

```applescript
on run argv
	set {inPath, outPath} to argv
	set inFile to inPath as POSIX file
	set outFile to outPath as POSIX file
	tell application "Pixelmator Pro"
		set d to open inFile
		try
			set L to current layer of d
			tell color adjustments of L
				set its exposure to 10
				set its contrast to 15
				set its vibrance to 25
				set its temperature to 12
				set its vignette to true
				set its vignette exposure to -40
			end tell
			export d to outFile as JPEG with properties {compression factor:90}
		on error msg number n
			close d saving no
			error msg number n
		end try
		close d saving no
	end tell
end run
```

To apply a look saved in the app, use `apply color adjustments preset L name "<preset
name>"`. The name must match a preset in Pixelmator's Adjustments presets exactly.

## Upscale to an exact size

`super resolution` is always ×3. Upscale once, or twice for ×9, then resize down to
the exact target with Lanczos.

```applescript
on run argv
	set {inPath, outPath, targetW} to argv
	set targetW to targetW as integer
	set inFile to inPath as POSIX file
	set outFile to outPath as POSIX file
	with timeout of 3600 seconds
		tell application "Pixelmator Pro"
			set d to open inFile
			try
				repeat while ((width of d) as integer) < targetW
					super resolution d
				end repeat
				resize image d width targetW algorithm lanczos -- height follows the aspect ratio
				set sz to {(width of d) as integer, (height of d) as integer}
				export d to outFile as PNG
			on error msg number n
				close d saving no
				error msg number n
			end try
			close d saving no
		end tell
	end timeout
	return sz
end run
```

## Cut-out on a new background

Remove the background from the photo layer, then put a solid colour behind it. This
is the usual "product on white" or brand-colour shot.

```applescript
on run argv
	set {inPath, outPath} to argv
	set inFile to inPath as POSIX file
	set outFile to outPath as POSIX file
	with timeout of 600 seconds
		tell application "Pixelmator Pro"
			set d to open inFile
			try
				set photo to current layer of d
				remove background photo
				decontaminate colors photo -- clean colour fringes on the edge
				tell d
					set bg to make new rectangle shape layer at end of layers with properties {width:(width of d), height:(height of d), position:{0, 0}, name:"background"}
				end tell
				set fill color of styles of bg to {62965, 62965, 63479} -- #f5f5f7
			on error msg number n
				close d saving no
				error msg number n
			end try
			export d to outFile as JPEG with properties {compression factor:90}
			close d saving no
		end tell
	end timeout
end run
```

## Styled headline with shadow and a highlighted word

```applescript
on run argv
	set {outPath} to argv
	set outFile to outPath as POSIX file
	tell application "Pixelmator Pro"
		set d to make new document with properties {width:1200, height:628}
		try
			tell d
				set fill color of styles of (make new rectangle shape layer at beginning of layers with properties {width:1200, height:628, position:{0, 0}}) to {6425, 6425, 11565}
				set t to make new text layer at beginning of layers with properties {text content:"Launch day is here"}
				tell text content of t
					set its font to "Avenir-Heavy"
					set its size to 96
					set its color to {65535, 65535, 65535}
				end tell
				tell word 4 of text content of t to set its color to {65535, 45232, 0}
				set horizontal alignment of t to center
				set width of t to 1200
				set position of t to {0, 250}
				tell styles of t
					set its shadow color to {0, 0, 0}
					set its shadow opacity to 60
					set its shadow blur to 12
					set its shadow distance to 6
				end tell
				set fnt to font of text content of t
			end tell
			export d to outFile as PNG
		on error msg number n
			close d saving no
			error msg number n
		end try
		close d saving no
	end tell
	return fnt -- confirm the font really applied
end run
```

## Watermark every image in a folder

This is an AppleScript loop for a one-off overlay that `pxm-batch.py` doesn't cover.
It writes to another folder, one document at a time.

```applescript
on run argv
	set {inDir, outDir, mark} to argv
	set names to paragraphs of (do shell script "cd " & quoted form of inDir & " && ls | grep -iE '\\.(jpe?g|png|heic|tiff?)$' || true")
	set done to {}
	with timeout of 600 seconds
		repeat with nm in names
			set inFile to (inDir & "/" & nm) as POSIX file
			set base to do shell script "n=" & quoted form of (nm as text) & "; echo \"${n%.*}\""
			set outFile to (outDir & "/" & base & ".jpg") as POSIX file
			tell application "Pixelmator Pro"
				set d to open inFile
				try
					set w to (width of d) as integer
					set h to (height of d) as integer
					tell d
						set t to make new text layer at beginning of layers with properties {text content:mark}
						tell text content of t
							set its size to (round (h / 25))
							set its color to {65535, 65535, 65535}
						end tell
						set opacity of t to 70
						-- place by the measured box: a fixed-width box would wrap long marks
						set m to round (h / 40)
						set position of t to {w - ((width of t) as integer) - m, h - ((height of t) as integer) - m}
					end tell
					export d to outFile as JPEG with properties {compression factor:88}
				on error msg number n
					close d saving no
					error msg number n
				end try
				close d saving no
			end tell
			set end of done to base
		end repeat
	end timeout
	return (count of done) as text
end run
```

## Web export

`export for web` adds size-oriented options: transparency, sRGB conversion and a
scale percentage.

```applescript
on run argv
	set {inPath, outPath} to argv
	set inFile to inPath as POSIX file
	set outFile to outPath as POSIX file
	tell application "Pixelmator Pro"
		set d to open inFile
		try
			export for web d to outFile as WebP with properties {compression factor:75, keep transparency:true, convert to sRGB:true, scale:50}
		on error msg number n
			close d saving no
			error msg number n
		end try
		close d saving no
	end tell
end run
```
