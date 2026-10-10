---
name: calibre
description: 'Manage e-books and calibre libraries from the CLI on macOS: convert between EPUB, AZW3, KEPUB, MOBI, PDF, DOCX, Markdown and HTML with cover, TOC and metadata; build an EPUB from a folder of Markdown or HTML chapters; turn a text PDF into a clean EPUB and report what the conversion broke; read and write e-book metadata; query, add, export and bulk-edit calibre library records (authors, series, tags) with a dry run, backup and read-back, even while the calibre GUI is open; validate EPUBs. Use for "turn these Markdown chapters into an EPUB with a cover", "convert this PDF to EPUB and tell me what is wrong with it", "fix the author spelling across this series in my calibre library", "convert my EPUBs to AZW3 for Kindle", "which books have no cover", "ebook-convert", "calibredb", Hungarian "készíts EPUB-ot a fejezetekből". Not for pulling text out of a document to read or summarise (markitdown), typeset print PDFs (scribus, libreoffice), Pages export (pages), or reference libraries and citations (zotero).'
summary: "manage e-books and calibre libraries from the CLI — EPUB/AZW3/KEPUB/PDF/DOCX/Markdown conversion with cover, TOC and metadata, EPUB builds from Markdown chapters, PDF-to-EPUB repair with a quality report, and bulk library metadata edits with dry run, backup and read-back"
category: publishing
risk: medium
tags:
  - calibre
  - ebook
  - epub
  - azw3
  - kindle
  - ebook-convert
  - calibredb
  - metadata
metadata:
  version: "1.0.0"
---

# calibre

Every call is **one short process** on calibre's own CLI tools (`ebook-convert`,
`calibredb`, `ebook-meta`, `ebook-polish`). The helper scripts run on calibre's
bundled Python, so they need nothing else installed. The skill never starts a server
and never edits `metadata.db` directly; library writes go through `calibredb`.
Verified against **calibre 9.16** on macOS 27.

Always go through `scripts/calibre.sh`. It finds the app, applies a timeout
(`CALIBRE_TIMEOUT`, default 600 s) and forces English output. calibre localizes its
messages to the system language, and it also **tags a new book with the UI language**:
on a Hungarian Mac an English novel comes out as `hun` unless `--language` is passed.

- [references/cli-reference.md](references/cli-reference.md): `ebook-convert` options
  by input and output format, TOC/chapter XPaths, `calibredb` subcommands, search
  syntax and field formats, `ebook-meta`, `ebook-polish`. Read it before any
  conversion or library command not shown below.
- [references/recipes.md](references/recipes.md): Kindle/Kobo conversion, folder
  batches, DOCX → EPUB, EPUB → Markdown, adding books, export, catalogs, covers,
  fetching metadata.
- [references/gotchas.md](references/gotchas.md): **read it when a write is refused,
  metadata reads back wrong, or a conversion looks broken.** It also covers the
  security posture.

## 1. Check first

```bash
C=scripts/calibre.sh            # paths are relative to this skill's directory
bash $C check [LIBRARY]         # app, version, library (default: calibre's), lock state, epubcheck
```

If calibre is missing, ask before installing (`brew install --cask calibre`).
`epubcheck` is optional (`brew install epubcheck`); the scripts use it when present.

## 2. Pick the tool

| Task | Use |
|---|---|
| Folder of Markdown/HTML chapters → EPUB (or AZW3/DOCX/PDF) | `md_to_epub.py` (§3) |
| Text PDF → EPUB, plus what is still wrong | `pdf_to_epub.py` (§4) |
| Any other format → format | `bash $C ebook-convert in out [options]` (§5) |
| Read or set metadata on one file | `bash $C ebook-meta` (§5) |
| Query, add, export the library | `bash $C calibredb …` (§6) |
| Change metadata on several library books | `bulk_metadata.py` (§7) |
| Is this e-book OK? metadata, TOC, cover, smells, epubcheck | `ebook_check.py` (§8) |

Scripts run as `bash $C py scripts/<name>.py …`, print JSON on stdout, and take `--help`.
Exit codes: **2** usage, **3** missing or unreadable input, **4** verification
failed, **5** calibre error, **6** library locked (§7).

## 3. EPUB from Markdown or HTML chapters

```bash
bash $C py scripts/md_to_epub.py chapters/ -o book.epub --title "The Salt Road" \
   --authors "Mara Lind" --language en --cover cover.jpg \
   [--series "Coastline" --series-index 2] [--publisher P --tags "a,b" --pubdate 2026-05-01] \
   [--toc-levels 2] [--css extra.css] [--order a.md b.md …] [--inline-toc]
```

- Chapters are the folder's `.md`/`.html` files in natural order (`2` before `10`).
  `README*`, `NOTES*` and `_*` are skipped, and the JSON lists every skipped file, so
  check that list against what the user meant. Use `--order` when filenames don't sort.
- Each chapter becomes its own spine document. The first `#` heading is its TOC entry;
  `##` become level-2 entries. A chapter with no heading gets one from front matter
  `title:` or the filename, and a warning says so.
- Markdown gets footnotes, tables, fenced code, smart quotes. Local images are copied
  in, and links between chapter files are rewritten.
- **`--language` is required.** Set it from the text, not from the user's locale.
- Output type follows the extension. The script reads the book back and exits 4 if
  title, authors, series, cover or the chapter list differ from what was asked.

## 4. PDF → EPUB, with a quality report

```bash
bash $C py scripts/pdf_to_epub.py book.pdf -o book.epub --language en [--title T --authors A] [--cover c.jpg]
```

- It refuses scanned PDFs (no text layer, exit 3), because they need OCR first.
- It runs `ebook-convert` with heuristics, then repairs the result:
  - rejoins words split at line ends (`con-tinued` → `continued`; real compounds like
    `well-known` stay)
  - merges paragraphs broken mid-sentence
  - drops bare page numbers and running headers
  - rebuilds an empty TOC from the chapter headings
- **Report** `fixes` (what changed) and `remaining_issues` (what didn't) to the user.
  A PDF → EPUB is never lossless, so name the issues instead of calling the result
  clean. Then look at a few chapters with `ebook_check.py` or by unzipping them.
- Tables, footnotes, multi-column layouts and figures with captions usually survive
  badly. Say so when the source has them.

## 5. Other conversions and single-file metadata

```bash
bash $C ebook-convert in.epub out.azw3 [--cover c.jpg --title T --authors "A & B" --language en]
bash $C ebook-meta book.epub                          # read
bash $C ebook-meta book.epub -a "Jane Doe" --author-sort "Doe, Jane" -s "Series" -i 2 -l en
```

- Formats come from the extensions. KEPUB, AZW3, MOBI, PDF, DOCX, TXT and HTMLZ are
  all outputs. **Markdown output is `.txt` with `--txt-output-formatting markdown`**,
  because `.md` is not an output extension.
- Metadata options (`--title`, `--authors`, `--series`, `--cover`, `--language` …)
  work on every conversion. `--authors` takes `&` between names. A comma does not
  separate authors, so "Doe, Jane" is one author.
- Folders of files: loop in the shell. Each file is its own process, and you can check
  each exit code.

## 6. Library: query, add, export

```bash
bash $C calibredb list --for-machine -f title,authors,series,series_index,tags --search 'series:"=Harbor Lights"'
bash $C calibredb search 'cover:false'                # ids of books without a cover
bash $C calibredb add --authors "A" --title "T" --languages eng book.epub
bash $C calibredb export --to-dir out/ --formats epub 12,13
```

- The default library is the one calibre has configured. Pass `--with-library PATH`
  for another one.
- Search language: `field:value` (contains), `field:"=exact"`, `field:"~regex"`,
  `and`/`or`/`not`, `cover:false`, `formats:pdf`, `#custom:`. See
  [references/cli-reference.md](references/cli-reference.md).

## 7. Bulk metadata edits

Never loop `calibredb set_metadata` by hand over many books. Use the script, which
plans, backs up, writes and reads back:

```bash
B=scripts/bulk_metadata.py
bash $C py $B --variants "Jane Doe"                          # every spelling of the name, with titles
bash $C py $B --ids 1,2,3,4,5 --set authors="Jane Doe" --set series="Harbor Lights" --series-order pubdate
bash $C py $B … same … --apply --backup before.json          # writes, then verifies every field
bash $C py $B --restore before.json --apply                  # undo
```

- **Find the books first.** `--variants` lists each author spelling with its books,
  including `Doe, Jane` and `J. Doe`. Initials-only matches and look-alikes such as
  `John Doe` or `Jane Doe-Smith` are flagged rather than merged. Decide with the
  titles and series, and ask the user when a book's identity is unclear.
- Then dry-run and read every `old → new` pair, then `--apply`. Setting `authors` also
  sets `author_sort` (calibredb alone keeps the stale one). `--series-order pubdate`
  numbers the selection 1…n. Dates are stored at noon UTC, because a bare
  `1995-03-01` lands on March 2.
- **Report the applied changes and the backup path**, so the user can undo.
- **Library open in calibre:** while the GUI or `calibre-server` runs, `calibredb`
  refuses writes and even reads on *every* local library. The script then writes through that program's
  Content server on this machine when one is running with local writes allowed. If
  none is, it exits 6 and says how to enable one. **Never kill or quit the user's
  calibre** to get around the lock. Ask them to close it, or to turn on the Content
  server. `bash $C lock` shows the state.

## 8. Verify every output

```bash
bash $C py scripts/ebook_check.py book.epub --expect-title "T" --expect-authors "A" --expect-language en \
   --expect-toc 6 --expect-cover [--expect-series S --expect-series-index 2] [--max-epubcheck-errors 0]
```

- The JSON holds the metadata, the TOC with levels, the cover, the images, epubcheck
  results, and `issues`: running headers, page numbers, split words, mid-sentence
  breaks, image-only pages, a missing TOC, Unknown author, no language. `--strict`
  exits 4 on any issue.
- A file that converted with exit 0 is not done. Check what the user asked for (title,
  author, language, chapters, cover) and tell them what you checked.
