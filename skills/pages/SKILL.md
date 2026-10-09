---
name: pages
description: 'Automate Apple Pages on macOS through its AppleScript/JXA dictionary (osascript) — create documents from Pages templates, replace {{placeholder}} tokens in body text, text boxes and tables without losing their formatting, swap or insert images, mail-merge a .pages template against CSV/JSON rows into one PDF/DOCX per row, and export or batch-convert .pages files to PDF, Word (DOCX), EPUB with title/author/language metadata, RTF or plain text — then verify the exports (PDF text and page count, EPUB metadata). Use whenever the user mentions Pages or a .pages file: "fill my Pages template", "export this .pages to PDF", "convert these Pages documents to Word", "make an EPUB from my Pages book", "mail merge this CSV into a Pages letter", or Hungarian "exportáld a .pages fájlt PDF-be", "töltsd ki a Pages sablont". Not for .docx files edited without Pages (use docx), generic PDF work (use pdf), converting files to Markdown (use markitdown), or Keynote and Numbers documents.'
summary: "automate Apple Pages via AppleScript/JXA — fill templates and {{placeholders}} without losing formatting, swap images, CSV mail merge, and PDF/DOCX/EPUB export or batch conversion of .pages files"
category: office
risk: low
tags:
    - pages
    - iwork
    - applescript
    - mail-merge
    - pdf
    - epub
---

# Pages Automation

Apple Pages is driven through its **AppleScript dictionary via `osascript`**: each
script call opens the documents it needs, works, and closes them again. There is no
bridge or listener; macOS Automation consent is the only gate. Verified against
**Pages Creator Studio 15.4** (bundle id `com.apple.Pages`) on macOS 27.

Everything goes through the scripts below. They encode workarounds for several
dictionary features that look usable but are broken (see Pitfalls), so reach for raw
AppleScript only for what they don't cover ([references/recipes.md](references/recipes.md)).

| Script | Does |
|---|---|
| `bash scripts/pages.sh --check` | app, version, Automation permission, open-document count. Run first. |
| `bash scripts/pages.sh --templates [RE]` | template **id** ⇥ localized name |
| `python3 scripts/pages-fill.py SRC ...` | copy a .pages (or `template:<id>`), replace tokens, swap/add images, export, optionally keep the filled `.pages` |
| `python3 scripts/pages-merge.py TPL DATA ...` | mail merge: one export per CSV/JSON row |
| `python3 scripts/pages-export.py SRC... --to FMT` | export one file or folders (`-r`) to pdf, docx, epub, rtf, txt; `--out FILE` names a single export |
| `python3 scripts/pages-verify.py FILE... ...` | assert on exports: PDF pages/text, EPUB metadata/text, DOCX text, .pages text |
| `bash scripts/pages.sh --dialog` | is a modal Pages alert blocking scripting? screenshots it |
| `bash scripts/pages.sh --close-leftovers` | close documents a killed run left open (stop path) |

All Python is standard library only and runs on the system `python3`. Every script
prints JSON lines and exits non-zero on failure. Read the JSON rather than assuming
success.

## Workflow

1. `bash scripts/pages.sh --check`. `automation: DENIED` → ask the user to allow
   the terminal in System Settings ▸ Privacy & Security ▸ Automation ▸ Pages.
2. Inspect the source when you did not write it: `python3 scripts/pages-verify.py
   doc.pages --show` prints all text Pages can reach (body, text boxes, shapes, tables).
   Tokens must appear there to be replaceable.
3. Run fill, merge or export.
4. **Verify the output independently** with `pages-verify.py`: `--contains` for every
   filled value, `--no-tokens`, `--pages N`, and for EPUB `--title/--author/--language`.
   A fixed-size text box silently clips a value that got longer, and verify is how you
   notice. For layout, render page 1 and look at it:
   `sips -s format png out.pdf --out /tmp/p1.png`, then Read the PNG.

## Fill and merge

```bash
S=scripts
# One document: tokens are {{key}} by default; the source is copied, never edited
python3 $S/pages-fill.py letter.pages --set name='Kovács Anna' --set 'amount=1 200 Ft' \
  --image logo=acme.png --export out/anna.pdf --export out/anna.docx --out out/anna.pages
python3 $S/pages-fill.py letter.pages --data values.json --export out/x.pdf   # JSON object
# From a built-in template, by id (names are localized: "Blank" is "Üres" in Hungarian)
python3 $S/pages-fill.py template:Application/Blank/ISO --out new.pages
# Mail merge: every column fills {{column}}; --name is a format string over the row
python3 $S/pages-merge.py letter.pages people.csv --out-dir out --name '{last}_{first}.pdf'
python3 $S/pages-merge.py letter.pages people.csv --out-dir out --dry-run   # plan only
```

- Replacement keeps each token's own character style (font, size, bold, colour).
  Style the `{{token}}` in the template the way the value should look.
- Matching is exact and case-sensitive. A value can be empty (the token is removed)
  or contain line breaks.
- An **unreplaced `{{` left in the document fails the run** (`"leftover"` in the
  JSON), so a misspelt column is caught. `not_found` lists keys that matched nothing,
  which is normal for extra CSV columns such as an email address. Pass
  `--allow-leftover` only when `{{` is meant to stay.
- Built-in template text such as the sample headline is replaceable as literal text:
  `--token '%s' --set 'Sample Headline=Our News'`.
- Images: `--image KEY=file` swaps every image whose **accessibility description**
  is KEY (Format ▸ Image ▸ Description, or set by script), fitted into the old frame
  with the aspect ratio kept. `--add-image '1,72,600,120=pic.png'` places a new one on
  page 1 at x=72, y=600 pt, 120 pt wide. Text-position anchoring is not scriptable.
- CSV: UTF-8 (BOM ok), with `,` `;` or tab detected. Quoted fields may contain commas.
  Duplicate output names get `-2`, `-3`. A row that fails is reported and the rest
  continue; the exit code is 1 if any row failed.

## Export and convert

```bash
python3 $S/pages-export.py report.pages --to pdf                       # next to source
python3 $S/pages-export.py ~/Docs --to docx --out-dir ~/Docs/docx -r   # mirrors subfolders
python3 $S/pages-export.py book.pages --out 'My Book.epub' --title 'My Book' --author 'Name' --language en
python3 $S/pages-export.py a.pages --to pdf --password s3cret --image-quality best
python3 $S/pages-verify.py ~/Docs/docx/*.docx --contains 'expected text'
```

- Formats: `pdf`, `docx` (Microsoft Word), `epub`, `rtf`, `txt`. `.pages` itself can't
  be converted *from* here. Opening `.docx` in Pages is an import and out of scope.
- Existing outputs are skipped unless `--force`. Sources are always closed without
  saving.
- EPUB options: `--title --author --genre --language --publisher --cover
  --fixed-layout`. Always pass `--title` and `--language`. Without them, the title is
  the file name and the language is the Mac's *system* language (it came out `hu`
  for an English book). Page-layout documents (newsletters, posters) come out
  reflowable unless you pass `--fixed-layout` (`rendition:layout` pre-paginated).
  Chapter splits and the TOC depend on paragraph *styles* in the source, which a
  script can't set (see gotchas).
- `--password` encrypts PDF and DOCX. `pages-verify` can't read an encrypted file.

## Pitfalls (all measured on 15.4)

- **A modal alert blocks all scripting.** Examples are "can't be opened", a password
  prompt, or a missing-fonts sheet. Every later call times out (error -1712). The
  scripts then report it and save a screenshot of the alert (`pages.sh --dialog`).
  Read the screenshot and ask the user to click it away. There is no scripted way to
  dismiss it without Accessibility access, so don't try.
- **Open files as an alias** in raw AppleScript: `open (POSIX file p as alias)`. A bare
  `POSIX file` gives an "operation not permitted" alert (sandbox), which then blocks
  Pages.
- **Never open a document the user has open.** Their unsaved edits and yours would
  collide. The scripts refuse: export errors with "already open". Fill copies the file
  on disk, so the user's *unsaved* changes aren't included; say so.
- **`make new document` leaves an "Untitled" file in iCloud Drive's Pages folder**,
  even after `close saving no`. The scripts save new documents to their target path
  at once. In raw AppleScript, do the same.
- **Headers and footers can't be filled.** Their text isn't in `body text`, shapes or
  tables. Put tokens in the body or a text box instead.
- **Fixed-size text boxes clip overflow silently.** A longer value disappears from the
  PDF. Verify with `--contains`, and keep token boxes roomy.

More pitfalls, and why the scripts do what they do: [references/gotchas.md](references/gotchas.md).
Dictionary reference (classes, export options, enumerations):
[references/dictionary.md](references/dictionary.md).

## Safety

- The scripts write new files only. Sources and templates are copied, never modified,
  and an existing output is replaced only with `--force`.
- Stop path: every call ends at `PAGES_TIMEOUT` (default 300 s). After an interrupted
  run, `pages.sh --close-leftovers` closes only the documents the scripts opened. The
  scripts never quit Pages, never close the user's own documents, and never click
  dialogs.
- PDF passwords passed with `--password` appear in the process list while the export
  runs. Mention this if the user cares.
