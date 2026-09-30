# Keynote scripting dictionary (Creator Studio 15.4)

Confirmed with `sdef "/Applications/Keynote Creator Studio.app"` on macOS 27. Suites:
Keynote Suite, iWork Suite, iWork Text Suite, Compatibility Suite, plus `open`,
`save`, `close` and `count` from the Cocoa Standard Suite (`xi:include`). Nothing the
older Keynote dictionary documents is missing from this edition.

Address the app by bundle id, `application id "com.apple.Keynote"`, because the app
name ("Keynote Creator Studio") differs between editions.

## Application and document

| Class / property | Notes |
|---|---|
| `theme` (application element) | `id` (stable, e.g. `Application/21_BasicWhite/Standard`), `name` (**localized**) |
| `document` → `document theme` | settable, so you can re-theme a deck |
| `document` → `slide layout` elements | per document, `name` only (**localized**, may contain soft hyphens U+00AD), no id |
| `document` → `width`, `height` | points, 1024×768 for Basic White |
| `document` → `slide numbers showing`, `auto play`, `auto loop`, `auto restart`, `maximum idle duration`, `current slide` | |
| `document` → `password protected` (r/o); `set password … to … hint …`, `remove password … from …` | |

## Slide

| Property | Notes |
|---|---|
| `base layout` | a `slide layout` of the same document; settable on an existing slide |
| `default title item`, `default body item` | text items; write `object text` |
| `title showing`, `body showing` | set true to reveal a placeholder the layout hides |
| `presenter notes` | rich text; supports `characters`, `words`, `paragraphs` |
| `skipped` | skipped slides are left out of PDF/image exports by default |
| `slide number` (r/o) | |
| `transition properties` | record: `transition effect`, `transition duration`, `transition delay`, `automatic transition` |

Elements of a slide (iWork container): `text item`, `shape`, `image`, `table`, `chart`,
`group`, `line`, `movie`, `audio clip`, `iWork item`.

- `image`: `file name` (**settable**: replaces the picture, keeps the frame), `file`
  (r/o), `description`, `opacity`, `rotation`, `position`, `width`, `height`.
- `text item` / `shape`: `object text` (rich text), `position`, `width`, `height`,
  `rotation`, `opacity`.
- `table`: `row count`, `column count`, `header row count`, …; `cell` → `value`,
  `formatted value` (r/o), `formula` (r/o); `range` → `font name`, `font size`,
  `text color`, `background color`, `alignment`, `format`.
- Rich text (`object text`, `presenter notes`): `color` (16-bit RGB list), `font`
  (PostScript name), `size`; elements `character`, `word`, `paragraph`.

## Commands

| Command | Notes |
|---|---|
| `make new slide at end of slides of d with properties {base layout: …}` | |
| `make new image / text item / table with properties {…}` | `tell` the **slide**: `tell s to make new image with properties {file: alias}` |
| `move slide a of d to before/after slide b of d` | reorder |
| `delete slide n of d` | |
| `duplicate slide n of d to after slide m of d` | |
| `make image slides d files {alias, …} [set titles bool] [slide layout …]` | **broken in 15.4**: every picture is added twice |
| `add chart` (Compatibility) | `row names`, `column names`, `data`, `type` (legacy chart type), `group by` |
| `start d from slide n`, `show next`, `show previous`, `stop d` | live slideshow; takes over the screen |
| `export d to file as FMT [with properties {…}]` | see below |

## Export

`as`: `PDF`, `Microsoft PowerPoint`, `slide images`, `QuickTime movie`, `HTML`,
`Keynote 09`.

`export options` record keys:

| Key | Values | Applies to |
|---|---|---|
| `export style` | `IndividualSlides`, `SlideWithNotes`, `Handouts` | PDF |
| `skipped slides` | bool | PDF (images ignore it: skipped slides are never exported as images) |
| `all stages` | bool, one page per build stage | PDF, images |
| `borders`, `slide numbers`, `date` | bool | PDF |
| `include comments` | bool | PDF |
| `PDF image quality` | `Good`, `Better`, `Best` | PDF |
| `password`, `password hint` | text | PDF, PPTX |
| `image format` | `JPEG`, `PNG`, `TIFF` | slide images |
| `compression factor` | real 0–1 | JPEG |
| `movie format` | `format360p` … `format2160p`, `native size` | movie |
| `movie codec` | `h264`, `HEVC`, `AppleProRes422`, `AppleProRes4444`, … | movie |
| `movie framerate` | `FPS12` … `FPS60` | movie |

- **Slide images** go into a *folder*: exporting to `…/deck` creates `deck/` holding
  `deck.001.png`, `deck.002.png`, ….
- **PPTX** keeps skipped slides, marked hidden (`show="0"`), and carries presenter
  notes into the notes pages.
- Movie export of a deck with no timings gives a short slideshow at the default
  pacing. A 1-slide deck at 360p took about 1 s.
