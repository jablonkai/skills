# Gotchas (DesignCraft 0.14.0)

Each was hit while building or testing the skill.

## Pages and numbers

- **Three numbering schemes.** 0-based: `run --page`, MCP `export_png`/`render_page`
  `page`, `layout.pages.applyParent` `pages`, `document.inspect` page `index`.
  1-based: `file.exportPdf {pages}`, `layout.pageSize {pages}`, `links.list` `uses.page`,
  page `name` in `document.inspect`, `--all-pages` file names (`page-001.png`), and
  everything the user says. Convert at the boundary; `dc_build.py` and `dc_verify.py` take
  1-based pages throughout.
- **A wrong `--page` exports silently.** `--page 1` on a 4-page brochure renders page 2;
  past the end it fails with `no such page`. The `wrote … (N glyphs)` line is a cheap
  hint: 0 glyphs on a text page means the wrong page.
- **PNG renders include the bleed.** At `--scale 2` an A4 page with 3 mm bleed is
  1225 × 1718 px, not 1191 × 1684. Pages without bleed render at exactly page × scale.

## Units and geometry

- **Points only.** `width`, `height`, `margins`, `bleed`, `gutter`, `rect`, `x`, `y` are
  points no matter what `units` says (`units` sets the UI display). 1 mm = 2.8346 pt;
  A4 = 595.276 × 841.89 pt; 3 mm bleed = 8.504 pt.
- **Spread coordinates.** On a facing spread the right page's x runs from page width to
  twice page width; page 1 of a facing document is alone on spread 0 (a right page).
  `document.inspect` lists each page's `bounds`.
- **Defaults:** `file.new` margins are 36 pt, facing pages on, one column, no bleed, Letter
  when no preset/size is given.

## Text

- **Byte offsets.** `text.select`, `story.replaceRange`, `data.placeholder.add {at}`,
  `find.find` matches and story `length` count UTF-8 bytes (é = 2, — = 3).
- **Styles act on the selection.** `style.paragraph.apply` and `type.char`/`type.para`
  have no story param; `text.select` first. A `focus` past the end selects to the end.
- **Overset is silent.** Text that doesn't fit stops at the last frame; exports succeed
  without it. `document.inspect` → `stories[].overset`, `story.get` → `overset` (the byte
  offset where hidden text starts, or null).
- **Auto page number** = `\ue000` in the text (Type › Insert Special Character › Current
  Page Number in the app; no registry command). `variables.insert` only has Last Page
  Number, Chapter Number, dates, File Name and Running Header.
- **Default font** is a bundled serif. Name `fontFamily`/`fontStyle` in styles; a family
  that isn't installed shows up in `font.list` as `missing` (`dc_verify.py doc` lists it
  under `missingFonts`) and renders in Source Sans 3 instead.

## Data merge

- `data.merge` **opens a new document**; the template is unchanged. Save or export after
  the merge to get the records.
- `perPage: "multiple"` needs exactly one page with facing pages off
  ("multiple records on a page need one page with facing pages off").
- `data.placeholder.add {at}` inserts `<<field>>` at `at`; `end` does not turn existing
  text into a field. Insert from the last offset to the first so earlier offsets hold.
- Unresolved fields come out as literal `<<field>>` text: check the PDF text.

## PDF

- `--export x.pdf` without `--pdf-options` (and `script --export`) writes a plain PDF:
  no bleed, no marks, not PDF/X. `validate-pdf` then exits 1.
- `validate-pdf` exits 1 on invalid files; it reports issues, it doesn't fix them. The
  export doesn't embed or outline fonts it can't embed.

## CLI behaviour

- `run` without `--in`/`--sample` works on an empty Letter document — easy to miss when a
  path variable is empty.
- `--cmd 'file.save={}'` writes back to the `--in` file: copy first.
- The `wrote …` lines and command results may print out of order.
- Unknown params are errors (with the valid list), despite `script --help` saying
  otherwise; unknown *values* of enum params are usually errors too
  (`unknown perPage value`).
- `/Applications/DesignCraft.app/Contents/MacOS/DesignCraft --help` opens the GUI —
  don't probe the app binary.
