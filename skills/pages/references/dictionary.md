# Pages scripting dictionary (16.0)

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
| `window` → `two up` | boolean: pages shown side by side in that window |

## document

| Property | Type | Notes |
|---|---|---|
| `id` | text (r/o) | a UUID, stable while the document is open: `document id "…"` |
| `body text` | rich text | the main text flow. Setting it replaces everything as plain text. |
| `document template` | template | used with `make new document with properties {document template: template id "…"}` |
| `document body` | boolean | true = word processing, false = page layout |
| `facing pages` | boolean | |
| `current page` | page | |
| `password protected` | boolean | commands: `set password "pw" to d hint "h" [saving in keychain bool]`, `remove password` |
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
| `cell` | `value` (text or number), `formatted value` (r/o), `formula` (r/o, `missing value` without one), `row`, `column` |
| `row` / `column` | `address` (r/o, 1-based index), `height` / `width` |
| `range` | `name`, `font name`, `font size`, `text color`, `background color`, `alignment`, `vertical alignment`, `text wrap`, `format` (automatic, number, currency, percent, date and time, duration, text, checkbox, … numeral system) |
| `line`, `movie`, `audio clip`, `group` | `start/end point`; `file name`, `movie/clip volume`, `repetition method`; `rotation` |

## rich text (iWork Text Suite)

Properties `font` (PostScript name, e.g. `Helvetica-Bold`), `size`, `color`
({r, g, b} 0–65535). Elements `paragraphs`, `words`, `characters`,
`placeholder texts`. Each carries the same font/size/color properties.

- `delete characters i thru j of rt` works.
- `set character i of rt to "text"` inserts the text with character i's style.
- `set characters i thru j of rt to …` is broken (see gotchas).
- `word` elements drop punctuation, so they can't locate `{{tokens}}`.

`placeholder text`: a template's tap-to-replace text, in the body and in headers and
footers. `(placeholder text i of d) as text` is what it shows. Its `tag` is the
localized sample text, or a contact-field key for sender/recipient fields
(`TPMailMerge_FullNamePseudoProperty`, `postalAddresses`, `phoneNumbers`,
`emailAddresses`); Pages pre-fills the sender ones from the user's own contact card.
Since 16.0 `set placeholder text i of d to "…"` replaces it with plain text and the
change survives save, reopen and export (15.4 dropped it). The filled text stops being
a placeholder, so the indices shift: fill from the last one down. `set contents of …`
still fails (-10006).

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

JXA image creation: `P.Image({file: Path(p)}).make()` still fails, but since 16.0
`d.pages[0].images.push(P.Image({file: Path(p)}))` adds one. The scripts use
AppleScript for images.
