# Keynote scripting gotchas

Each item was reproduced against Keynote Creator Studio 15.4 on macOS 27, with the UI
in Hungarian, while this skill was being built. The scripts handle every one of them.
The notes explain why the scripts work the way they do, and what to watch for in raw
AppleScript.

## Blocking and state

| Symptom | Cause | What to do |
|---|---|---|
| Every call times out (-1712), even `count documents` | A modal alert is up: "can't be opened", a password prompt, missing fonts | `keynote.sh --dialog` finds it through CoreGraphics and screenshots it without Accessibility access. Show the user and ask them to click it away. |
| `open POSIX file p` returns `missing value`, then an error alert appears | Sandboxed Keynote gets no read permission from a bare file URL for a file it didn't create | Open with an **alias**: `open (POSIX file p as alias)`. An alias carries the sandbox grant. `openOwned` does this. |
| `Untitled.key` (localized, e.g. `Névtelen.key`) piles up in `~/Library/Mobile Documents/com~apple~Keynote/Documents/` | `make new document` autosaves to iCloud until the document is saved somewhere, and `close … saving no` doesn't remove it | Save the new document to its real path **immediately** after `make` (`save d in POSIX file p`). Saving at once leaves nothing in iCloud; saving at the end doesn't help. Leftovers are the user's to delete. |
| A deck stays open after a script error | The error skipped the `close` | `keynote_ops` closes in its error handlers. After a *killed* run, `keynote.sh --close-leftovers` closes what the scripts had recorded as opened. |
| Editing a deck the user has open | Their unsaved edits and yours collide | `openOwned` refuses any path already open. `keynote-fill` copies the file on disk instead, so the user's unsaved changes aren't in the copy. |
| `/tmp/x.key` isn't detected as open | Keynote reports `/private/tmp/x.key` | Paths go through `realpath` before comparing. |

## Themes and layouts

| Symptom | Cause | What to do |
|---|---|---|
| `theme "Basic White"` not found | Theme **names are localized** ("Egyszerű fehér") | Use the id: `first theme whose id is "Application/21_BasicWhite/Standard"`. `keynote.sh --themes` lists id ⇥ name. |
| `slide layout "Title & Bullets"` not found | Layout names are localized too, have no id, and some carry soft hyphens ("Fel­so­ro­lás­je­lek") | `keynote.sh --layouts THEME` maps each index to its English name through the app's own `TSATemplateLocalizable.strings`. Pass an index to raw AppleScript. |
| Layout 4 is "Title & Bullets" in one theme and "Photo - Vertical" in another | Themes have different layout sets and orders: Basic White has 17 with a "Section", Gradient 14 without | Resolve per theme. `keynote-build` picks by *role* with fallbacks (section → Section, then Title - Center, then Title). |
| The role `bullets` must not mean the layout named "Bullets" | "Bullets" has no title placeholder | Roles win over same-named layouts; the index still reaches that layout. |

## Text

| Symptom | Cause | What to do |
|---|---|---|
| `set characters 2 thru 4 of object text of t to "x"` turns `ABCDEF` into `AxxxEF` | A range set is broken, as in Pages | Delete the tail (`delete characters (o+1) thru (o+L-1)`), then `set character o to value`. The value inherits character o's style (bold stays bold). This is `replaceIn`. |
| `set object text of t to "…"` loses mixed styling | It replaces the whole run with text in the first character's style | Fine for building; use `replaceIn` to edit. |
| Nested bullets come out flat, with a gap after the bullet | A leading tab or spaces is literal text; the indent level isn't in the dictionary | `keynote-build` flattens nested items and warns. Indent in the Keynote UI (Tab) if the hierarchy matters. |
| Slide text read twice | `every text item of s` lists each placeholder more than once, plus a hidden one with a 0×0 frame | Deduplicate by text and frame, skip 0-sized items. `containerTexts` does this. |
| A numeric table cell reads back as `120,0` | `value` is a real, coerced with the locale's decimal comma | Read `formatted value` for what the slide shows. |
| Filling `{{amount}}` in a cell with "1 250 000 Ft" leaves the real `1.25E+6` behind (it *displays* right) | Cells default to the `automatic` format, which parses numbers, currency and dates out of text | `set format of c to text` before `set value of c`. `replaceInTables` does this, so a filled cell stays the text you wrote. |
| `transition effect of (transition properties of s)` fails (-1700) | Nested property access on a record property | Read the record into a variable first. |
| `if tg is "n"` also matches `"N"` | AppleScript string comparison ignores case by default | Use tags that differ by more than case, or wrap in `considering case`. |
| A variable named `th` or `it` is a syntax error | `th` is an ordinal suffix; `it` is the implicit target | Rename it. |

## Objects and export

| Symptom | Cause | What to do |
|---|---|---|
| `make image slides d files {a, b}` makes 4 slides | Broken: each picture is added twice (AppleScript and JXA alike) | Make the slides yourself: `make new slide` and set the placeholder's `file name`, as `keynote-build` does. |
| A picture in a layout's photo placeholder | `file name` of the placeholder image is **settable** | `set file name of image 1 of s to (POSIX file p as alias)`: the frame and mask stay. |
| `export … as slide images` makes a folder | The target path is a directory holding `NAME.001.png`, … | `keynote-export` reports the image count; point `--out` at a folder. |
| Image export leaves skipped slides out even with `skipped slides:true` | That option only affects PDF | Unskip first (`keynote-fill --unskip`) when the images must include them. |
| PPTX slide count differs from PDF page count | PPTX keeps skipped slides (hidden), PDF drops them by default | Compare against `slides` and `skipped_slides` in `keynote-export` output, or pass `--include-skipped` for PDF. |
| `export … with properties {}` fails | `{}` is an empty *list* | Start from `{} as record`, and leave out `with properties` when there are no options. |
