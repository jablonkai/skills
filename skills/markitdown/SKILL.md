---
name: markitdown
description: "Convert files and documents to Markdown for LLM consumption using Microsoft's markitdown tool. Use whenever the user wants to turn a PDF, Word/Excel/PowerPoint file (.docx/.xlsx/.pptx), HTML page, CSV/JSON/XML, EPUB, image, audio file, ZIP archive, or YouTube URL into Markdown or plain text — e.g. 'convert this PDF to markdown', 'extract the text from report.docx', 'turn this spreadsheet into markdown', 'pull the transcript from this audio', 'markdownify these files', 'alakítsd át markdownná'. Also use when batch-converting a folder of documents, feeding office/PDF content into a prompt, or building a doc-to-markdown step in a script. Trigger even if the user names a file type without saying 'markitdown'."
category: document-conversion
risk: safe
tags:
  - markdown
  - document-conversion
  - pdf
  - office
  - text-extraction
allowed-tools: Bash, Read, Write, Glob
argument-hint: "[file-or-url] [-o output.md]"
---

# markitdown

Convert almost any document into clean Markdown using Microsoft's [markitdown](https://github.com/microsoft/markitdown). The output preserves structure (headings, tables, lists, links) rather than scraping flat text, which is exactly what makes it good as LLM input.

## When to use this

Reach for markitdown whenever content lives in a non-Markdown format and someone wants it as Markdown or text: a PDF report, an Office file, a web page, a data file, an e-book, even an image or audio clip. It's the right tool both for one-off "what does this file say" tasks and for building a conversion step into a larger pipeline.

If the user just wants you to *read* a file you can already open directly (a `.txt`, `.md`, or source code), skip markitdown — it adds nothing there.

## Prerequisites

Check it's available before relying on it:

```bash
markitdown --version   # expect: markitdown 0.1.x
```

If missing, install with pip. The base package handles HTML, CSV/JSON/XML, and basic Office files; the `[all]` extra adds PDF, image OCR, audio transcription, and more:

```bash
pip install "markitdown[all]"        # full support (recommended)
pip install markitdown               # minimal
```

Heavy dependencies make a virtual environment worthwhile. Prefer `[all]` unless the user wants a lean install.

## Core CLI usage

The CLI takes one file and emits Markdown. With no filename it reads stdin.

```bash
markitdown report.pdf -o report.md      # convert to a file (-o)
markitdown report.pdf > report.md       # same, via redirect
markitdown report.pdf                    # print to stdout (good for piping into a prompt)
cat report.pdf | markitdown              # read from stdin
```

When reading from stdin, markitdown can't see a file extension, so give it a hint or it may misdetect the format:

```bash
cat data | markitdown -x pdf             # hint by extension
cat data | markitdown -m application/pdf # hint by MIME type
some_curl_command | markitdown -x html -c UTF-8
```

### All flags (v0.1.x)

| Flag | Purpose |
|------|---------|
| `-o, --output FILE` | Write Markdown to a file instead of stdout |
| `-x, --extension EXT` | Hint the file extension (essential for stdin) |
| `-m, --mime-type TYPE` | Hint the MIME type |
| `-c, --charset CS` | Hint the character set (e.g. `UTF-8`) |
| `-d, --use-docintel` | Use Azure Document Intelligence instead of offline conversion |
| `-e, --endpoint URL` | Azure Document Intelligence endpoint (required with `-d`) |
| `-p, --use-plugins` | Enable installed 3rd-party plugins |
| `--list-plugins` | List installed plugins (none ship by default) |
| `--keep-data-uris` | Keep base64 data URIs (e.g. inline images); truncated by default |

## Batch conversion

There's no built-in recursive mode, so loop in the shell. Convert every PDF in a tree to a sibling `.md`:

```bash
find . -name '*.pdf' -print0 | while IFS= read -r -d '' f; do
  markitdown "$f" -o "${f%.pdf}.md"
done
```

Swap the glob/extension for `*.docx`, `*.pptx`, etc. When the user hands you a folder of mixed documents, prefer this pattern over converting one file at a time.

## Supported formats

- **Office:** `.docx`, `.pptx`, `.xlsx`, `.xls`
- **Documents:** PDF, EPUB
- **Web & data:** HTML, CSV, JSON, XML, RSS/Atom, Wikipedia pages, YouTube URLs (pulls the transcript)
- **Media:** images (EXIF metadata + OCR), audio (metadata + speech transcription)
- **Archives:** ZIP (recurses into contents), plus Outlook `.msg`

Quality varies by source. Clean digital PDFs and Office files convert well; scanned PDFs and complex multi-column layouts are where Azure Document Intelligence (below) earns its keep.

## Python API

Use this when conversion is part of a larger Python program, or when you need the result in a variable rather than on disk.

```python
from markitdown import MarkItDown

md = MarkItDown()                 # enable_plugins=False by default
result = md.convert("report.pdf") # also accepts a URL or a file-like object
print(result.text_content)        # the Markdown string
# result.title may hold a detected document title
```

`convert()` returns a `DocumentConverterResult`; the Markdown is on `.text_content`. Pass `MarkItDown(enable_plugins=True)` to opt into installed plugins.

## Advanced options

### LLM image descriptions

For images, hand markitdown an OpenAI-compatible client and it will generate a description of the image content instead of just extracting EXIF/OCR text:

```python
from markitdown import MarkItDown
from openai import OpenAI

md = MarkItDown(llm_client=OpenAI(), llm_model="gpt-4o")
result = md.convert("diagram.png")
```

This calls a paid API and sends the image to that provider — only do it when the user has asked for image understanding and is fine with that. Needs `OPENAI_API_KEY` in the environment.

### Azure Document Intelligence (high-fidelity OCR)

For scanned or layout-heavy PDFs, route through Azure Document Intelligence for far better table/structure recovery:

```bash
markitdown scan.pdf -d -e "https://<resource>.cognitiveservices.azure.com/"
```

```python
md = MarkItDown(docintel_endpoint="https://<resource>.cognitiveservices.azure.com/")
```

Requires the `markitdown[az-doc-intel]` extra and Azure credentials in the environment.

### Plugins

Third-party plugins extend format support. None are installed by default; `markitdown --list-plugins` shows what's available, and `-p` (CLI) or `enable_plugins=True` (Python) turns them on. Find them via the `#markitdown-plugin` GitHub hashtag.

## Gotchas

- **stdin needs a format hint.** Without a real filename, pass `-x`/`-m` or detection may fail or pick the wrong converter.
- **`[all]` vs minimal.** A "no converter for this format" error usually means the base package is installed but the `[all]` extra (PDF, OCR, audio) is not.
- **Secrets live in env vars.** LLM and Azure features read `OPENAI_API_KEY` / Azure keys from the environment — never hardcode them, and don't send sensitive documents to those external services without the user's go-ahead.
- **Verify before trusting.** After converting, glance at the output (`head`, or read the file). Scanned PDFs and exotic layouts can yield garbled or empty Markdown — surface that to the user rather than passing it along silently.
