# calibre CLI reference (checked against 9.16)

Run every tool as `bash scripts/calibre.sh <tool> …`. Full option lists:
`bash scripts/calibre.sh ebook-convert in.<ext> out.<ext> -h` (the list depends on the
two extensions), `bash scripts/calibre.sh calibredb <command> -h`.

## Contents
- [ebook-convert](#ebook-convert): common, structure and TOC, input formats, output formats
- [ebook-meta](#ebook-meta)
- [ebook-polish](#ebook-polish)
- [calibredb](#calibredb): commands, search syntax, field formats
- [Other tools](#other-tools)

## ebook-convert

`ebook-convert INPUT OUTPUT [options]`. The formats come from the extensions.
- **Input:** epub, azw3, azw/azw4, mobi, kepub, pdf, docx, odt, rtf, txt/md
  (`.md` and `.markdown` are TXT input), html/htm/xhtml, htmlz, txtz, fb2, lit, pdb,
  cbz/cbr/cb7, opf (a package file with a spine), recipe.
- **Output:** epub, kepub, azw3, mobi, pdf, docx, txt, txtz, htmlz, fb2, rtf, snb, pml,
  lrf, oeb (a folder), zip.

### Common options (any pair)
| Option | Effect |
|---|---|
| `--title`, `--authors "A & B"`, `--author-sort`, `--title-sort` | Metadata. A comma does not separate authors. |
| `--series`, `--series-index`, `--tags "a,b"`, `--publisher`, `--pubdate`, `--isbn`, `--comments`, `--rating` | Metadata |
| `--language en` | Book language. **Always pass it**, because the default is the UI locale. |
| `--cover FILE`, `--preserve-cover-aspect-ratio` | Cover image |
| `--read-metadata-from-opf FILE` | Take all metadata from an OPF |
| `--extra-css FILE/CSS`, `--filter-css font-family,color` | Styling |
| `--base-font-size`, `--line-height`, `--margin-*`, `--embed-all-fonts`, `--subset-embedded-fonts` | Look & feel |
| `--smarten-punctuation`, `--remove-paragraph-spacing`, `--insert-blank-line` | Text tidy |
| `--enable-heuristics` (+ `--disable-*` sub-options, `--html-unwrap-factor 0.4`) | Unwrap lines, fix indents, mark up chapter headings. Use it for PDF and TXT input. |
| `--sr1-search REGEX --sr1-replace TEXT` (… `sr3`), `--search-replace FILE` | Regex fixes on the HTML before structure detection |
| `-v`, `-vv` | Verbose log |

### Structure and TOC (XPath, `h:` = XHTML namespace)
| Option | Default | Notes |
|---|---|---|
| `--chapter XPATH` | `<h1>`/`<h2>` containing chapter, book, section, part, prologue or epilogue, plus `class="chapter"` | Chapter starts (page breaks, auto TOC) |
| `--chapter-mark pagebreak|rule|both|none` | pagebreak | |
| `--page-breaks-before XPATH` | `//*[name()='h1' or name()='h2']` | |
| `--level1-toc` / `--level2-toc` / `--level3-toc XPATH` | none | e.g. `//h:h1`, `//h:h2`. Overrides the auto TOC. |
| `--use-auto-toc` | off | Ignore the input's TOC and build one |
| `--max-toc-links N` | 50 | Extra link entries added when fewer than `--toc-threshold` chapters are found; `0` disables them |
| `--toc-threshold N` | 6 | |
| `--no-chapters-in-toc`, `--toc-filter REGEX` | | Drop entries |
| `--epub-inline-toc`, `--toc-title` | | A printed contents page (EPUB/AZW3) |

### Input-specific
- **PDF:**
  - `--pdf-engine calibre|pdftohtml` (default `calibre`; it removes headers and footers itself)
  - `--pdf-header-skip N`, `--pdf-footer-skip N` (pixels; `-1` = auto), `--pdf-header-regex`, `--pdf-footer-regex`
  - `--unwrap-factor 0.45`, `--no-images`
  - Scanned PDFs (no text layer) give empty books, so run OCR first.
- **TXT / Markdown:**
  - `--formatting-type auto|plain|heuristic|textile|markdown`
  - `--paragraph-type auto|block|single|print|unformatted|off`
  - `--markdown-extensions footnotes,tables,toc` (the default), `--txt-in-remove-indents`, `--preserve-spaces`
  - One file only. For a folder of chapters use `md_to_epub.py`.
- **DOCX:** `--docx-no-cover`, `--docx-no-pagebreaks-between-notes`, `--docx-inline-subsup`. Word headings map to h1–h6, and Word's TOC field is dropped and rebuilt.
- **HTML:** follows local links (`--max-levels 5`), `--breadth-first`, `--dont-package`.

### Output-specific
- **EPUB:**
  - `--epub-version 2|3` (default 2, the most compatible)
  - `--no-default-epub-cover` (otherwise calibre draws one when there is no cover)
  - `--epub-flatten`, `--dont-split-on-page-breaks`, `--flow-size KB`, `--epub-toc-at-end`
- **KEPUB (Kobo):** `--kepub-max-image-size`, hyphenation flags.
- **AZW3 (Kindle):**
  - `--no-inline-toc`, `--prefer-author-sort`, `--share-not-sync`
  - For Send-to-Kindle, upload EPUB directly; Amazon converts it.
- **MOBI:** `--mobi-file-type old|both|new` (legacy devices only).
- **PDF:**
  - page setup: `--paper-size a4|a5|letter…`, `--custom-size WxH`, `--pdf-page-margin-*` (pt)
  - fonts: `--pdf-default-font-size`, `--pdf-serif-family`
  - extras: `--pdf-add-toc`, `--pdf-page-numbers`, `--pdf-hyphenate`, `--pdf-no-cover`, `--pdf-mark-links`
  - header/footer: `--pdf-header-template HTML` / `--pdf-footer-template HTML` (with `_PAGENUM_`, `_TITLE_`, `_AUTHOR_`, `_SECTION_`)
- **DOCX:** `--docx-page-size a4|letter…`, `--docx-page-margin-*`, `--docx-no-toc`, `--docx-no-cover`.
- **TXT (incl. Markdown):** `--txt-output-formatting plain|markdown|textile`, `--keep-links`, `--keep-image-references`, `--max-line-length 0`, `--txt-output-encoding utf-8`. Use `.txtz` to keep the images.

## ebook-meta

`ebook-meta FILE` prints the metadata. With options it writes into the file, in place:
- `-t TITLE`, `-a "A & B"`, `--author-sort`, `--title-sort`
- `-s SERIES`, `-i INDEX`, `--tags "a,b"`, `-p PUBLISHER`, `-l LANG`, `-d DATE`, `--isbn`, `--identifier type:value`, `-c COMMENTS`, `-r RATING`
- `--cover FILE`, `--get-cover OUT.jpg`, `--to-opf OUT.opf`, `--from-opf IN.opf`

It works for EPUB, AZW3, MOBI, PDF, DOCX, ODT, RTF, FB2, CBZ and others.

## ebook-polish

`ebook-polish [options] IN.epub|IN.azw3 [OUT]`. Without OUT it writes `IN_polished.epub`.
- `-c COVER` replaces the cover; `-o OPF` replaces the metadata.
- `-j` / `--remove-jacket` adds or removes a book jacket.
- `-e` embeds the referenced fonts; `-f` subsets the embedded fonts.
- `-p` smartens punctuation; `-u` removes unused CSS.
- `-i` compresses images losslessly.
- `-H` / `--remove-soft-hyphens` adds or removes soft hyphens.
- `-U` upgrades EPUB 2 → 3; `-d` downloads external resources.

## calibredb

`calibredb [--with-library PATH|URL] COMMAND …`. A URL looks like
`http://127.0.0.1:8080/#Library_id` (the id is the folder name with spaces → `_`). It
takes `--username/--password` when the server requires them.

| Command | Use |
|---|---|
| `list [-f fields\|all] [--search Q] [--sort-by F --ascending] [--limit N] [--for-machine]` | Rows; `--for-machine` = JSON |
| `search Q` | Matching ids, comma separated |
| `show_metadata ID [--as-opf]` | One book |
| `add FILES… [-a A -t T -s S -S IDX -T tags -l lang -c cover -I id:val] [-d] [-r] [-1]` | Add books; `-d` allows duplicates; `-e` adds an empty record |
| `add_format ID FILE`, `remove_format ID FMT` | Formats of a book |
| `set_metadata ID -f field:value [-f …]` or `set_metadata ID file.opf` | Edit (prefer `bulk_metadata.py`) |
| `set_custom COLUMN ID VALUE`, `custom_columns`, `add_custom_column LABEL NAME TYPE` | Custom columns |
| `export IDS\|--all --to-dir D [--formats epub,pdf] [--single-dir] [--template '{author_sort}/{title}']` | Copy books out |
| `catalog OUT.csv\|.xml\|.bib\|.epub\|.azw3 [--fields …] [--search Q] [--ids …]` | Catalogue of the library |
| `list_categories [-r authors,series,tags]` | Every author/series/tag with counts |
| `remove IDS [--permanent]` | **Destructive**, so ask first. Without `--permanent` the books go to calibre's trash. |
| `check_library`, `backup_metadata`, `embed_metadata IDS\|all`, `restore_database` | Maintenance |
| `fts_index enable`, `fts_search "text"` | Full-text search, once it is indexed |

### Search syntax (same as the GUI search bar)
- `title:salt`: contains, case-insensitive. `title:"=Salt Road"`: exact. `title:"~^The\s"`: regex.
- `authors:"=Jane Doe"`, `series:"=Harbor Lights"`, `tags:"=to read"`, `publisher:`, `languages:eng`
- `series:false`: no series. `cover:false`: no cover. `formats:pdf`, `formats:false`.
- `pubdate:<2000`, `pubdate:>=1995-01-01`, `date:` (= added), `rating:>3`, `size:>5M`
- `identifiers:isbn:978…`, `#mycol:value`, `id:=12`
- Combine with `and`, `or`, `not`, `( )`. Quote values with spaces. In the shell, wrap the
  whole expression in single quotes.

### Field formats for `set_metadata -f` / `bulk_metadata.py --set`
| Field | Format |
|---|---|
| `authors` | `A & B`. It does **not** update `author_sort`, so set that too. |
| `author_sort` | `Doe, Jane & Li, Bo` |
| `tags`, `languages` | comma separated (`languages:eng,hun`, ISO 639-2 or -1) |
| `identifiers` | `isbn:978…,goodreads:123` (replaces them all) |
| `series` / `series_index` | `Harbor Lights` / `2` (empty `series:` clears it; don't send an empty index) |
| `pubdate`, `timestamp` | `1995-03-01T12:00:00+00:00`. A bare date can shift a day. |
| `rating` | 0–10 (stars × 2) |
| `comments` | HTML or plain text |
| `#custom` | depends on the column type |

## Other tools

| Tool | Use |
|---|---|
| `fetch-ebook-metadata -t T -a A [-i ISBN] [-c cover.jpg] [-o]` | Look metadata up online (Google, Amazon …). It uses the network; `-o` prints an OPF. |
| `calibre-server [--port 8080 --listen-on 127.0.0.1 --enable-local-write] LIBRARY` | Content server. Start it only when the user asks, and stop it afterwards. |
| `calibre-smtp` | Email a book, e.g. to a Kindle address. It needs SMTP details from the user. |
| `pdfinfo`, `pdftotext`, `pdftoppm` (in `calibre.sh`, from the bundle) | Inspect a PDF: pages, whether it has a text layer, page renders |
