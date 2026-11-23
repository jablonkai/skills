# Pages scripting gotchas

Each item was reproduced against Pages Creator Studio 15.4 while this
skill was being built, and re-checked against 16.0. Rows marked
**16.0** changed in that release; the opening-by-bare-`POSIX file` alert, the EPUB
chapter/TOC notes and text-box clipping were not re-triggered on 16.0. The scripts already handle every one of them. The notes explain
why the scripts work the way they do, and what to watch for in raw AppleScript.

## Blocking and state

| Symptom | Cause | What to do |
|---|---|---|
| Every call times out (-1712), even `count documents` | A modal alert is up: "…can't be opened / invalid file format", a password prompt, missing fonts | `pages.sh --dialog` finds it through CoreGraphics and screenshots it without Accessibility access. Show the user and ask them to click it away. |
| Alert "…can't be opened right now: operation not permitted" for a file you can read (the DOCX baseline hit it on all 4 files and left the alerts stacked) | `open (POSIX file p)` sends a bare file URL, and sandboxed Pages gets no permission to read it | Open with an **alias**: `open (POSIX file p as alias)`. An alias carries the sandbox grant. `openOwned` does this. |
| An alert appeared after opening a half-written `.pages` | Pages opened a package that was still being written, or one that isn't a Pages file | `check_pages_file` rejects anything that isn't a zip or a package with `Index/`. Never open a path while another process is writing it. |
| "Untitled 2.pages" files pile up in `~/Library/Mobile Documents/com~apple~Pages/Documents/` | `make new document` autosaves to iCloud as soon as it is edited (still so on 16.0), and `close … saving no` doesn't remove the file | Save the new document to its real path immediately (`save d in POSIX file p`), as `pages_ops new` does. Leftovers are the user's to delete. |
| A document stays open after a script error | The error skipped the `close` | `pages_ops` closes in its error handlers. After a *killed* run, `pages.sh --close-leftovers` closes what the scripts had recorded as opened. |
| Editing a document the user has open | Their unsaved edits and yours collide | `openOwned` refuses any path already open. `pages-fill` copies the file on disk instead, so the user's unsaved changes aren't in the copy. |
| `/tmp/x.pages` isn't detected as open | Pages reports `/private/tmp/x.pages` | Paths go through `realpath` before comparing. |

## Text

| Symptom | Cause | What to do |
|---|---|---|
| `set characters 5 thru 9 of body text of d to "Győr"` writes "Győr" into **each** of the five characters | A range set is broken | Delete the tail (`delete characters 6 thru 9`), then `set character 5 to "Győr"`. The new text inherits character 5's style. This is `replaceIn`. |
| `set body text of d to "…"` loses all styling | It replaces the whole storage with plain text | Use it only to build new content, then style the paragraphs. |
| Tokens like `{{name}}` or `FIELD_NAME` can't be found as words | `word` elements drop punctuation, so `{{city}}` becomes the word `city` and `_` splits words | Search the text with `offset of`, then edit by character index. The indices of AppleScript `offset` and Pages `character` agree, including accents and emoji. |
| `offset of "Name" in s` matches "name" | AppleScript ignores case by default | Wrap it in `considering case`. |
| Passing `body text of d` to a handler, then `delete characters … of rt` fails with "can't make {…} into specifier" | The argument was evaluated to plain text | Pass `a reference to (body text of d)`. |
| A value longer than the token vanishes from the PDF | A fixed-size text box clips overflow without warning. In a newsletter title, "NAPI HÍREK" → "EMU HÍRADÓ" wrapped, and the second line was cut. | Verify with `pages-verify --contains`, render page 1 and look, or keep token boxes roomy. |
| Header/footer text can't be filled | It's outside `body text`, shapes and tables, so the scripts never see it. **16.0:** a template's header/footer `placeholder text` elements can now be set (15.4 dropped the set); plain header text stays unreachable, including a placeholder once it has been filled. | Keep tokens in the body, text boxes or table cells. For template placeholders in headers and footers, use the placeholder recipe in recipes.md. |
| Built-in template placeholders ("Heading 1", lorem ipsum) | `placeholder text` elements, whose `tag` is the localized sample text (or a contact-field key such as `postalAddresses`). **16.0:** `set placeholder text i of d to "…"` works and persists; `set contents of …` fails (-10006). | Body ones: `pages-fill --token '%s' --set 'Heading 1=…'`. Header/footer ones: the placeholder recipe. |
| Paragraphs come back joined in terminal output | Pages separates paragraphs with CR (`\r`), and TXT export uses CR too | `norm_text` maps CR and U+2029 to `\n`. |
| Table cell text lost its partial formatting after a fill | Cells are replaced through `value`, which is plain text | It's fine for tokens that fill a whole cell. For styled runs inside a cell, use a text box instead. |

## Objects

| Symptom | Cause | What to do |
|---|---|---|
| `make new image with properties {file:…}` on the document fails: 15.4 said "can't make TMAScriptImageInfoProxy", 16.0 says -10024 "can't be created or put in that container" (or -10000 with `at d`). JXA `Image().make` fails too | Images can only be made on a page (JXA: `d.pages[0].images.push(...)` works on 16.0) | `tell page 1 of d to make new image with properties {file:(POSIX file p as alias), position:{x, y}}` |
| `set file of image 1 of d to …` fails | `file` is read-only | Record the position, width and height, delete the image, make a new one there and fit it. This is `swapImage`. |
| `every image of d whose description is "logo"` fails with -1723 | **16.0:** fixed, the filter works on the document and on a page. 15.4 refused it. | `swapImage` still loops over `every image of pg`, which works on both. |
| `export d to POSIX file p …` inside `tell application "Pages"` fails with -1728 | **16.0:** fixed, it exports. 15.4 tried to resolve `POSIX file` itself. | Building `set dest to POSIX file p` before the `tell` block works on both; the scripts keep doing that. |
| `export … with properties {}` fails: "can't make {} into export options" | `{}` is an empty *list*, and `{} & {title:x}` is a list too | Start from `{} as record`, and leave out `with properties` when there are no options. |

## Templates and export

- Template **names are localized** ("Blank" is "Üres" in Hungarian), and ids aren't
  (`Application/Blank/ISO`). Always look them up with `pages.sh --templates`.
- The dictionary has no `open`/`save`/`close` of its own. They come from the Cocoa
  Standard Suite (`xi:include` in the sdef) and work normally.
- EPUB: the title defaults to the file name and the language to the system language,
  so pass both. Page-layout documents need `--fixed-layout` to keep their layout.
- EPUB chapters: Pages starts a new EPUB chapter file only at paragraphs that use a
  heading/chapter *paragraph style*. Bold, large text isn't enough: the three-chapter
  test book came out as one `chapter-1.xhtml`. Paragraph styles aren't in the
  dictionary, so the source has to use them already (a book template, or styles set in
  the Pages UI).
- The EPUB's table of contents labels ("Tartalomjegyzék", "1. fejezet") are in the
  Mac's UI language, whatever `--language` says.
- `--password` produces an encrypted PDF or DOCX that the verifier can't open. That is
  expected.
