# Gotchas

## Locale leaks into output and into books
- calibre prints its messages in the system language (Hungarian on this machine). That
  breaks every `grep` on them. `calibre.sh` sets `CALIBRE_OVERRIDE_LANG=en`. If you
  call the binaries directly, set it yourself.
- **New books get the UI language** when the source has none. Markdown, TXT and HTML
  input on a Hungarian Mac produce `language: hun` for an English text. Always pass
  `--language`.

## The library lock
- While the GUI or `calibre-server` has a library open, `calibredb` on that path
  prints *"Another calibre program such as calibre-server or the main calibre program is
  running…"*. **Writes exit 1, but reads exit 0 with no data**, so a script that only
  checks the exit code sees an empty library. `cal_common.calibredb()` turns both into
  exit 6.
- **The lock is machine-wide.** While *any* calibre GUI or `calibre-server` runs,
  `calibredb` refuses every local library, including ones calibre doesn't have open, and
  a second `calibre-server` will not start. `ebook-convert`, `ebook-meta` and
  `ebook-polish` are not affected.
- The fix is to go through the program's Content server:
  `--with-library http://127.0.0.1:PORT/#Library_id`. The id is the folder name with
  spaces turned into `_`, and `/ajax/library-info` lists it. Without "allow local
  writes" (or a user/password), writes answer `Forbidden`.
- Never kill, quit or restart the user's calibre to get the lock. They may have unsaved
  edits open in the editor or viewer, or a running conversion queue. Ask.
- Killing `calibre-server` and immediately running `calibredb` still sees the lock for
  a second or two. Wait before retrying.

## Metadata traps
- `set_metadata -f authors:…` **does not change `author_sort`**. The book keeps sorting
  under the old name ("Doe, J."). Set both; `bulk_metadata.py` does.
- Author and series names are **case-insensitive shared records**: adding "jane doe"
  when "Jane Doe" exists links the book to "Jane Doe". The per-book `author_sort` can
  still be wrong ("doe, jane"), so check it.
- A comma never separates authors: `--authors "Doe, Jane"` makes one author literally
  called "Doe, Jane". Use `&` between authors.
- `pubdate:1995-03-01` is stored as **1995-03-02** (local midnight → UTC). Pass
  `1995-03-01T12:00:00+00:00`.
- An empty `series_index:` raises `could not convert string to float`. To clear a
  series, send only `series:`.
- `ebook-convert` leaves the EPUB's author file-as empty, so `ebook-meta` and calibre
  read the author sort back as **"Unknown"**. Pass `--author-sort` (the scripts do).
- Unset dates read back as `0101-01-01`. Treat them as empty.
- `identifiers:` replaces **all** identifiers. Read them first and send the full set.
- `calibredb set_metadata` changes the database only. The files keep their old
  embedded metadata until `calibredb embed_metadata IDS` (or an export).

## Conversion traps
- `.md` is TXT input (`--formatting-type markdown`). `.md` is not an output
  extension: use `.txt` with `--txt-output-formatting markdown`.
- calibre's frozen Python has no Markdown extension entry points. `markdown.Markdown(
  extensions=["extra"])` fails with `No module named 'fenced_code'`. Use dotted names
  (`markdown.extensions.footnotes` …) in custom scripts.
- PDF input:
  - With `--enable-heuristics` the lines are unwrapped, but words split by a hyphen
    stay split ("con-tinued"). calibre only rejoins words it also finds unhyphenated
    in the book.
  - The TOC comes out as a single "Start" entry even when the chapter headings were
    detected (as `<h2>`).
  - Document titles are the PDF's file path.
  - `pdf_to_epub.py` fixes all of these.
- PDF input with the default engine strips running headers and page numbers in most
  layouts, but not all. Look for them (`ebook_check.py` reports them).
- A scanned PDF converts "successfully" into an empty or image-only book. Check for a
  text layer first (`bash $C pdftotext -l 3 f.pdf - | wc -c`).
- `--max-toc-links 0` *disables* the extra link entries; it does not mean unlimited.
- calibre draws a generated cover when none is given. Pass `--cover`, or
  `--no-default-epub-cover` for none.
- Converting a file inside the library folder and writing the output next to it does
  not add it to the library. Use `calibredb add_format`.

## Paths
- Library paths can contain spaces and accents ("Calibre könyvtár"). Always quote them.
- `calibredb list` truncates columns to the terminal width. Use `--for-machine` for
  JSON, or `-w 200`.

## Security posture
- **Nothing listens.** The skill starts no server and no daemon, so cross-origin
  requests (#17) and token auth (#32) don't apply. `calibre-server` is started only
  when the user asks. Then it binds to `--listen-on 127.0.0.1` and is stopped
  afterwards.
- **Library writes** go only through `calibredb`, never through SQL on `metadata.db`.
  Bulk edits run as a dry run first and save a JSON backup of the old values before
  writing, and `--restore` undoes them. `remove` is used only on explicit request, and
  without `--permanent`, so the books go to calibre's trash.
- The scripts read only the inputs they are given. They write only the requested output
  and a temporary staging folder, which is deleted afterwards.
- **Stop path (#35):** every call runs under `CALIBRE_TIMEOUT` (default 600 s) and is
  killed on expiry. There is nothing else to stop.
- `fetch-ebook-metadata` and `--cover URL` go to the network. Use them only when the
  user wants an online lookup.
