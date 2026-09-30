# Pages scripting dictionary (15.4)

Taken from `sdef "/Applications/Pages Creator Studio.app"`; the behaviour notes come from live calls.
The notes say what works in practice. Regenerate the dictionary after an update:

```bash
sdef "$(mdfind "kMDItemCFBundleIdentifier == 'com.apple.Pages'" | head -1)" > pages.sdef
```

Suites: Pages Suite, iWork Suite, iWork Text Suite, plus the Cocoa Standard Suite
(open, save, close, count, delete, make, exists).

## Application

| Element / property | Notes |
|---|---|
| `templates` (r/o) | `id` (stable, e.g. `Application/Blank/ISO`) and `name` (localized) |
| `documents` | the open documents |

## document

| Property | Type | Notes |
|---|---|---|
| `body text` | rich text | the main text flow. Setting it replaces everything as plain text. |
| `document template` | template | used with `make new document with properties {document template: template id "…"}` |
| `document body` | boolean | true = word processing, false = page layout |
| `facing pages` | boolean | |
| `current page` | page | |
| `password protected` | boolean | commands: `set password "pw" to d hint "h"`, `remove password` |
| `selection` | | the GUI selection. Avoid it. |

Elements: `pages`, `sections`, `images`, `shapes`, `text items`, `tables`, `charts`,
`groups`, `lines`, `movies`, `audio clips`, `iWork items`, `placeholder texts`.

`page` and `section` have `body text` and hold the same drawable elements. **New
drawables must be made on a page**: `tell page 1 of d to make new image …`.

## iWork item (base of all drawables)

`position` (point {x, y}, in points from the page's top-left), `width`, `height`,
`locked`, `parent`.

| Class | Extra properties |
|---|---|
| `image` | `file` (read-only in practice), `file name`, `description` (accessibility text, read/write, the key `--image` swaps by), `opacity`, `rotation`, `reflection showing/value` |
| `shape` | `object text` (rich text), `background fill type`, `opacity`, `rotation` |
| `text item` | `object text`, `background fill type`, `opacity`, `rotation`. Text items are also returned by `shapes`. |
| `table` | `name`, `row count`, `column count`, `header row/column count`, `footer row count`, `cell range`, `selection range`. Elements: `cells`, `rows`, `columns`, `ranges`. Commands: `sort`, `merge`, `unmerge`, `clear`. |
| `cell` | `value` (text or number), `formatted value` (r/o), `formula` (r/o), `row`, `column` |
| `range` | `font name`, `font size`, `text color`, `background color`, `alignment`, `vertical alignment`, `text wrap`, `format` |

## rich text (iWork Text Suite)

Properties `font` (PostScript name, e.g. `Helvetica-Bold`), `size`, `color`
({r, g, b} 0–65535). Elements `paragraphs`, `words`, `characters`,
`placeholder texts`. Each carries the same font/size/color properties.

- `delete characters i thru j of rt` works.
- `set character i of rt to "text"` inserts the text with character i's style.
- `set characters i thru j of rt to …` is broken (see gotchas).
- `word` elements drop punctuation, so they can't locate `{{tokens}}`.

`placeholder text`: its `tag` is the localized sample text. It can be read and
deleted, but writing to it isn't kept.

## export

```applescript
export theDoc to (POSIX file "/abs/out.pdf") as PDF with properties {image quality:Best}
```

| `as` | Extension | Options that apply |
|---|---|---|
| `PDF` | pdf | `password`, `password hint`, `image quality` (Good/Better/Best), `include comments`, `include annotations` |
| `Microsoft Word` | docx | `password`, `password hint` |
| `EPUB` | epub | `title`, `author`, `genre`, `language`, `publisher`, `cover` (bool: the first page is the cover), `fixed layout` (bool) |
| `formatted text` | rtf | |
| `unformatted text` | txt | CR line endings |
| `Pages 09` | pages | a legacy format. Avoid it. |

Build `POSIX file` outside the `tell` block. Leave out `with properties` when there
are no options.

## JXA equivalents

```javascript
const P = Application("com.apple.Pages");
const t = P.templates.byId("Application/Blank/ISO");
const d = P.Document({documentTemplate: t}).make();
d.save({in: Path("/abs/new.pages")});          // save at once (iCloud Untitled pitfall)
d.bodyText = "Title\nBody";
d.bodyText.paragraphs[0].font = "Helvetica-Bold";
P.export(d, {to: Path("/abs/out.epub"), as: "EPUB",
             withProperties: {title: "T", author: "A", language: "en"}});
d.close({saving: "no"});
```

JXA can't create images (`P.Image(...)` fails). Use AppleScript for them.
