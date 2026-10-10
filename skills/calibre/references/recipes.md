# Recipes

`C=scripts/calibre.sh` (relative to the skill directory). Each recipe ends with a
check; run it.

## Kindle: EPUB → AZW3, a whole folder
```bash
mkdir -p kindle
for f in books/*.epub; do
  bash $C ebook-convert "$f" "kindle/$(basename "${f%.epub}").azw3" >/dev/null || echo "FAILED: $f"
done
for f in kindle/*.azw3; do bash $C ebook-meta "$f" | grep -E '^(Title|Author)'; done
```
Send-to-Kindle (email or app) takes EPUB directly and converts it, so AZW3 is only
needed for a USB sideload. For Kobo, use `.kepub` output.

## Markdown book with metadata from front matter
`md_to_epub.py` reads a chapter's own `title:` from YAML front matter, but the book's
metadata comes from flags. With a `book.yaml`/`metadata.yaml` (pandoc style), read
the values from it and pass `--title/--authors/--language/--series/--cover`.

## One Markdown file → EPUB
```bash
bash $C ebook-convert book.md book.epub --formatting-type markdown --paragraph-type off \
  --title "T" --authors "A" --language en --level1-toc '//h:h1' --level2-toc '//h:h2'
```
Images are resolved relative to the `.md`. For several files use `md_to_epub.py`,
because concatenating them breaks footnote numbering and relative image paths.

## DOCX manuscript → EPUB
```bash
bash $C ebook-convert manuscript.docx book.epub --language en --cover cover.jpg \
  --level1-toc '//h:h1' --docx-no-cover
bash $C py scripts/ebook_check.py book.epub --expect-toc <chapters> --expect-cover
```
Chapter titles must use Word's Heading 1 style. Bold "normal" paragraphs do not
become headings; for those, add `--chapter "//h:p[re:test(., '^Chapter\s')]"` instead.

## EPUB → Markdown
```bash
bash $C ebook-convert book.epub book.txt --txt-output-formatting markdown --keep-links \
  --keep-image-references --max-line-length 0
mv book.txt book.md
```
Use `.txtz` instead of `.txt` to keep the images in a zip. For a quick read of the
text only, markitdown is the lighter tool.

## Add a folder of books to the library
```bash
bash $C lock                                       # must say "free" (or route via server)
bash $C calibredb add -r ~/Downloads/new-books --languages eng
bash $C calibredb list --for-machine -f title,authors,formats --sort-by timestamp --limit 20
```
Duplicates (same title and author) are skipped and listed unless `-d` is given.

## Books without a cover / without an EPUB
```bash
bash $C calibredb list --for-machine -f title,authors --search 'cover:false'
bash $C calibredb list --for-machine -f title,formats --search 'not formats:epub'
```

## Convert library books and attach the result as a new format
```bash
ids=$(bash $C calibredb search 'formats:mobi and not formats:epub')
mkdir -p /tmp/cal-conv
for id in ${ids//,/ }; do
  src=$(bash $C calibredb list --for-machine -f formats --search "id:=$id" |
        python3 -c 'import json,sys; print([f for f in json.load(sys.stdin)[0]["formats"] if f.endswith(".mobi")][0])')
  bash $C ebook-convert "$src" "/tmp/cal-conv/$id.epub" --language eng >/dev/null &&
    bash $C calibredb add_format "$id" "/tmp/cal-conv/$id.epub"
done
```
Never convert in place inside the library folder. Write to a temporary file and use
`add_format`.

## Export a series in reading order
```bash
bash $C calibredb export --to-dir out --formats epub --single-dir \
  --template '{series_index:0>2.0f} - {title}' $(bash $C calibredb search 'series:"=Harbor Lights"')
```

## Catalogue as CSV
```bash
bash $C calibredb catalog library.csv --fields title,authors,series,series_index,tags,pubdate,formats
```
`.xml`, `.bib`, `.epub` and `.azw3` work the same way.

## Fix one file's metadata
```bash
bash $C ebook-meta book.epub -t "Title" -a "Jane Doe" --author-sort "Doe, Jane" \
  -s "Harbor Lights" -i 2 -l en --cover cover.jpg
bash $C py scripts/ebook_check.py book.epub --expect-authors "Jane Doe" --expect-series "Harbor Lights"
```
Inside the library, change the record with `bulk_metadata.py` or `set_metadata`, then
`calibredb embed_metadata ID` to write it into the files.

## Look up metadata online
```bash
bash $C fetch-ebook-metadata -t "Gale Warning" -a "Jane Doe" -o > found.opf
```
This uses the network. Treat the result as a suggestion, and show it to the user
before writing it anywhere.

## Polish an existing EPUB
```bash
bash $C ebook-polish -p -u -i book.epub book.polished.epub   # punctuation, unused CSS, images
bash $C ebook-polish -c newcover.jpg book.epub                # → book_polished.epub
bash $C ebook-polish -U book.epub book.epub3.epub             # EPUB 2 → 3
```

## Through a running Content server (library open in the GUI)
```bash
bash $C lock                       # "locked" plus http://127.0.0.1:8080
curl -s http://127.0.0.1:8080/ajax/library-info      # {"library_map": {"Calibre_Library": …}}
bash $C calibredb --with-library 'http://127.0.0.1:8080/#Calibre_Library' list -f title --limit 5
```
Writes answer `Forbidden` unless the user enabled *Preferences → Sharing over the net →
Advanced → Allow un-authenticated local connections to make changes*, or gives
`--username/--password` for a user with write access.
