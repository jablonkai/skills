# Command ids by task (pinned to DesignCraft 0.15.2)

The registry has 545 commands. These are the ones layout work needs; check the full
signature with `scripts/dc_commands.py --id ID` before a first use, since pre-1.0
releases can rename params. Coordinates are points in spread space; page numbers in
`file.exportPdf` and `layout.pageSize` are 1-based, `layout.pages.applyParent` indices 0-based; text offsets are UTF-8 bytes.

## Document and pages

| Id | Key params → result |
|---|---|
| `file.new` | `preset` (`A4`, `Letter`, …), `width`, `height` (points), `pages`, `facingPages`, `margins` (n or `{top,bottom,inside,outside}`), `bleed`, `columns`, `gutter`, `startPage`, `title`, `primaryTextFrame` |
| `file.open` / `file.openIdml` | `path` |
| `file.save` · `file.saveAs` · `file.saveACopy` | — · `path` · `path` |
| `document.inspect` | → pageCount, settings, spreads (pages with bounds, margins, side; items with id, kind, bounds, story), parents, stories (frames, overset, preview), styles, swatches, layers |
| `layout.pages.insert` / `.delete` / `.move` | pages; `layout.pages.applyParent {pages: [index], parent: "B" \| "A-Parent" \| null}` — **0-based** page indices here |
| `layout.parents.new` / `.options` | extra parents (B-Parent …) |
| `layout.marginsAndColumns`, `layout.documentSetup`, `layout.pageSize`, `layout.section` | margins/columns, size/bleed, per-page size, numbering (start, style, prefix) |
| `guide.add`, `layout.createGuides` | ruler guides, grids |

## Frames and objects

| Id | Key params → result |
|---|---|
| `frame.create` | `spread` (index or `{kind: "parent", index: 0}`), `rect [x0,y0,x1,y1]`, `content: text\|graphic\|unassigned`, `shape: rectangle\|ellipse\|polygon`, `text` → `{id, story}` |
| `line.create`, `path.create` | lines and paths |
| `object.fill` / `object.stroke` | `swatch` (`[Black]`, `[Paper]`, a swatch name), `tint`, `weight`, `ids` |
| `object.fit` | `mode: fillProportionally\|fitProportionally\|fitContentToFrame\|centerContent\|fitFrameToContent`, `ids` |
| `object.fittingOptions` | `autoFit`, `fitting`, `align`, `crop`, `ids` |
| `object.textFrameOptions` | columns, inset, vertical justification, auto-size |
| `transform.move` / `.resize` / `transform.set` | geometry of the selection or `ids` |
| `selection.set` | `ids`, `add`, `content` — many commands act on the selection |
| `object.setLayer`, `layer.new`, `layer.set` | layers |
| `object.label`, `object.findByLabel` | name items and find them again |

## Text

| Id | Key params → result |
|---|---|
| `story.get` | `story` or `frame` → text, frames, paragraphs, lines, `overset` (byte offset or null) |
| `story.setText` | `story`, `text` (`\n` = paragraph) |
| `story.replaceRange` | `story`, `start`, `end` (bytes), `text` |
| `text.thread` | `from` + `rect` + `spread` (new frame after `from`), or `from` + `to`; `autoflow: true` adds frames/pages until it fits → `{story, overset, pagesAdded}` |
| `text.unthread`, `text.removeFromThread` | break threads |
| `text.select` | `story`, `anchor`, `focus` (bytes) — the selection styles and `type.*` act on |
| `text.insert` | `text` at the insertion point (`raw` skips smart quotes) |
| `file.place` | `path`; text files (`.txt`, `.docx`, `.rtf`, `.md`) and `.xlsx` (as a table) flow into `frame` or a new frame on `page`/`rect`; `autoflow` threads a frame per column, adding pages |
| `find.find` / `find.change` | `find`, `grep`, `scope`, `story` → matches with byte offsets |
| `type.char` / `type.para` | `attrs` local overrides on the selection |
| `type.selectionAttrs` | → resolved attributes and `paragraphStyle` at the selection |
| `variables.list`, `variables.insert` | text variables (Last Page Number, Running Header …); the *current* page number is the `\ue000` character, not a variable |

## Styles and swatches

| Id | Key params |
|---|---|
| `style.paragraph.create` / `.edit` | `name`, `basedOn`, `nextStyle`, `chars {fontFamily, fontStyle, size, leading: {kind: "points", value} \| {kind: "auto"}, tracking, fill, …}`, `para {align, spaceBefore, spaceAfter, firstLineIndent, leftIndent, ruleAbove, …}`; `edit` changes only what it names, `rename` renames |
| `style.paragraph.apply` | `name`, `clearOverrides` — on the **selection** |
| `style.character.create` / `.edit` / `.apply` | same pattern |
| `style.object.create` / `.apply`, `style.table.*`, `style.cell.*` | object, table, cell styles |
| `style.list`, `style.load` | names; import styles from another document |
| `swatch.create` | `name`, `color: "#rrggbb" \| {c,m,y,k} (0–100) \| [r,g,b]`, `spot`; or a `gradient` (`swatch.new` only duplicates the selection's colour) |
| `font.list`, `font.replace` | fonts in use, missing ones, substitution |

## Images and links

| Id | Key params → result |
|---|---|
| `file.place` | `path`, `frame` (place into) or `spread` + `x`, `y`, `width`; `pdfPage`, `pdfCrop` for PDFs |
| `links.list` | → `[{asset, name, path, status: ok\|modified\|missing\|embedded, pixels, uses: [{id, page (1-based string), ppi}]}]` |
| `links.relink` | `asset`, `path` — every placement of that asset |
| `links.relinkFolder`, `links.update`, `links.embed` | bulk relink, refresh, embed |
| `object.altText` | alt text for tagged PDF / EPUB |

## Data merge

| Id | Key params → result |
|---|---|
| `data.source.select` | `path` (CSV/TSV/XLSX), `delimiter`, `sheet` → `{fields: [{name, kind}], records, warnings}` |
| `data.fields` | the source's fields |
| `data.placeholder.add` | `field`, `story`, `at` (byte offset; inserts `<<field>>`), `role: text\|image\|qr\|hyperlink`, `item` (image frame) → `{id}` |
| `data.preview {record}` / `data.preview.stop` | look at one record without merging |
| `data.merge` | `records: all\|one\|range`, `range "1-20"`, `perPage: single\|multiple`, `arrange: rows\|columns`, `rowSpacing`, `columnSpacing`, `insets`, `fitting`, `center`, `limit`; or inline `csv`/`rows`/`path` → `{records, pages, missingImages, oversetStories, warnings}` — a **new** document becomes active |

## Export and checks

| Id | Key params |
|---|---|
| `file.exportPdf` | see [cli.md › PDF options](cli.md#pdf-options) |
| `file.exportIdml`, `file.exportEpub`, `file.exportFixedEpub`, `file.exportHtml`, `file.exportPptx`, `file.exportText` | `path` |
| `file.package` | collect the document, links and fonts into a folder |
| `preflight.run` | `minPpi` → issues `[{severity, kind, message, item, page}]` |
| `book.*` | multi-document books, `book.exportPdf` |
| `toc.generate`, `index.generate`, `footnote.insert`, `xref.insert` | long-document features |
