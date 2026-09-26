---
name: markitdown
description: "Convert files and documents to Markdown for LLM consumption using Microsoft's markitdown tool. Use whenever the user wants to turn a PDF, Word/Excel/PowerPoint file (.docx/.xlsx/.pptx), HTML page, CSV/JSON/XML, Jupyter notebook, EPUB, Outlook .msg, ZIP archive, audio file, or YouTube URL into Markdown or plain text — e.g. 'convert this PDF to markdown', 'extract the text from report.docx', 'turn this spreadsheet into markdown', 'markdownify this folder of documents', 'pull the transcript from this audio', 'alakítsd át markdownná'. Also use when batch-converting a directory of documents, feeding office/PDF content into a prompt or RAG pipeline, or building a doc-to-markdown step in a Python script. Trigger even if the user names a file type without saying 'markitdown'. Not for plain .txt/.md/source files, which can be read directly."
summary: "convert PDF, Office, HTML, data, notebook, e-book, audio, and ZIP files (or YouTube URLs) to clean Markdown using Microsoft's markitdown tool, via CLI, batch script or Python API"
category: document-conversion
risk: low
tags:
  - markdown
  - document-conversion
  - pdf
  - office
  - text-extraction
allowed-tools: Bash, Read, Write, Glob
argument-hint: "[file-or-dir-or-url] [-o output.md]"
---

# markitdown

Convert documents into clean Markdown with Microsoft's [markitdown](https://github.com/microsoft/markitdown).
It keeps structure — headings, tables, lists, links, slide notes, sheet names — instead of
scraping flat text, which is what makes it good LLM input.

It extracts text that is *already in the file*. It does **not** OCR: scanned PDFs and
photos come back empty (see "Image-only content" below).

## Setup

```bash
markitdown --version   # expect 0.1.x or later
```

If it's missing, install it as an isolated tool. It needs **Python 3.10+**:

```bash
uv tool install "markitdown[all]"      # preferred
pipx install "markitdown[all]"         # alternative
```

Avoid bare `pip install` with the macOS system Python (3.9): pip silently resolves the
ancient `markitdown 0.0.1a1`, which has no `[all]` extra and no working CLI. If an install
reports `0.0.1a1` or "does not provide the extra 'all'", the interpreter is too old — use
`uv tool install` or `uv venv -p 3.12`.

`[all]` pulls every optional converter. Lean installs can pick extras: `pdf`, `docx`,
`pptx`, `xlsx`, `xls`, `outlook`, `audio-transcription`, `youtube-transcription`,
`az-doc-intel`, `az-content-understanding`. A `MissingDependencyException` names the
extra that's missing.

If the environment forbids global installs, use a throwaway venv and call
`<venv>/bin/markitdown` directly.

## Single file

```bash
markitdown report.pdf -o report.md      # write to a file
markitdown report.pdf                    # stdout — good for piping into a prompt
curl -sL "$URL" | markitdown -x html     # stdin: add -x/-m hints for reliable detection
```

Useful flags (full list: `markitdown --help`):

| Flag | Purpose |
|------|---------|
| `-o FILE` | Output file instead of stdout |
| `-x EXT` / `-m MIME` / `-c CHARSET` | Format hints — mainly for stdin |
| `--keep-data-uris` | Keep inline base64 images (truncated by default) |
| `-p` / `--list-plugins` | Use / list installed 3rd-party plugins |
| `-d -e URL` | Azure Document Intelligence (cloud OCR) — see references |
| `--use-cu --cu-endpoint URL` | Azure Content Understanding — see references |

Exit status is non-zero for missing files and unsupported formats, but **0 with empty
output** for image-only content — so always check the result isn't blank.

## Batch conversion

For a directory, use the bundled script instead of hand-rolling a loop:

```bash
bash <skill-dir>/scripts/batch_convert.sh SRC_DIR [OUT_DIR]
# MARKITDOWN=/path/to/markitdown   if it isn't on PATH
# EXTENSIONS="pdf docx"             to narrow the file types
```

It recurses, mirrors the tree into `OUT_DIR` (or writes beside each source), names
outputs `<file>.<ext>.md` so `report.pdf` and `report.docx` can't collide, skips
up-to-date outputs on reruns, and ends with a summary that flags **EMPTY** (needs OCR),
**FAILED** (with the error), and **LEGACY** (`.doc`/`.ppt`) files. Relay those flagged
files to the user — they are the ones that need a decision. If the user wants a different
naming scheme (e.g. `report.md`), adapt the script's `dest=` line rather than rewriting it.

## What converts well

| Input | Result |
|-------|--------|
| `.docx` | Headings, lists, tables, links — a table whose first row isn't marked as a Word header row gets an empty `\|  \|  \|` header, with the real headers as the first data row; fix it up if the table matters |
| `.pptx` | One section per slide (`<!-- Slide number: N -->`), speaker notes under `### Notes:` |
| `.xlsx` / `.xls` | One `## SheetName` section with a table per sheet |
| PDF (digital) | Text plus tables recovered via pdfplumber; complex multi-column layouts can scramble |
| HTML, RSS/Atom, Wikipedia, Bing results | Main content as Markdown |
| CSV / JSON / XML / `.ipynb` | Tables / text / notebook cells |
| EPUB, Outlook `.msg` | Chapters / headers + body |
| ZIP | Every supported member, each under `## File: name` |
| Audio (`.wav .mp3 .m4a .mp4`) | Metadata plus a transcript via Google's free Web Speech API — **uploads the audio**, needs network |
| YouTube URL | Title, description and transcript when available |
| Images (`.jpg .png`) | Only EXIF metadata (needs `exiftool`) and an optional LLM caption — no OCR |

**Legacy `.doc` / `.ppt` are unsupported** (`UnsupportedFormatException`). Convert first:
`textutil -convert docx memo.doc` on macOS, or
`soffice --headless --convert-to docx memo.doc` with LibreOffice, then run markitdown.

## Image-only content (scans, photos)

When a PDF or image yields empty or near-empty output, the text is pixels, not
characters. Tell the user plainly, then choose a route:

1. **Read it yourself.** If you can view images and PDFs (e.g. the Read tool), open the
   file and transcribe it — often the quickest path for a few pages. Say that this is
   your transcription, not markitdown output.
2. **Local OCR**, if installed: `ocrmypdf scan.pdf out.pdf` then markitdown `out.pdf`,
   or `tesseract scan.png - ` for images.
3. **Cloud OCR**: Azure Document Intelligence (`-d -e ...`) — sends the document to
   Azure; only with the user's consent.

Never hand back an empty `.md` as if the conversion worked.

## Python API

```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("report.pdf")   # path, URL, or binary file-like object
text = result.markdown              # the Markdown string (alias: .text_content)
title = result.title                # may be None
```

For streams, error handling, LLM image captions, Azure and plugins, read
[references/python-api.md](references/python-api.md).

## Before handing results over

- **Look at the output.** `head` it or read it. Check that tables came through and the
  text isn't garbled or blank; say so when it is.
- **Privacy.** Offline conversion stays local; audio transcription, YouTube, LLM captions
  and Azure send content out. Ask before routing sensitive files through them, and keep
  keys (`OPENAI_API_KEY`, Azure credentials) in the environment, never in code.
- **Large outputs.** A long PDF can produce megabytes of Markdown. Write to a file and
  read or grep the parts you need rather than dumping it all into the conversation.
