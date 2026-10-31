# pdfcraft-cli 0.16.1 reference

Run every subcommand through `scripts/pf.sh` (same arguments) so OCR finds its
models. `pdfcraft-cli help <sub>` prints the same usage text as `--help`.

## Contents

- [Read-back](#read-back) — `info`, `text`, `render`, `check`, `audit`
- [Page operations](#page-operations) — `edit`, `combine`, `extract`, `split`
- [Batch](#batch) — `batch`
- [Tools](#tools) — `tools`, `run`
- [Servers and the app](#servers-and-the-app) — `mcp`, `ui`

## Read-back

| Command | Output | Notes |
|---|---|---|
| `info FILE [--password PW]` | JSON: `pages`, `title`, `author`, `producer`, `pdf_version`, `pdfa`, `pdfua`, `tagged`, `encrypted`, `fields`, `annotations`, `bookmarks`, `attachments`, `javascript`, `warnings` | No per-page rotation or size list. Use `doc_info` (via `run`, or `pf_verify.py`) for those |
| `text FILE [--page N]` | Plain text, pages separated by form feeds (`\f`) | No text from a scan until it is OCRed |
| `render FILE --page N [--dpi 96] --out X.png` | `.png`, `.jpg`, `.tif` or `.pam` | Inspect redactions, stamps and watermarks visually |
| `check FILES/DIRS… [--timeout 20] [--dpi 36] [--json out.json]` | `checked N files: {"ok": N}` | Opens and renders every page. Exit status 0 only if all files pass |
| `audit FILE [--password PW]` | JSON `{count, findings:[{kind, page, rect, covered_text}]}` | `kind` is `covered-text` (a box painted over live text) or `unapplied-mark`. Exit 1 when findings exist **or** the file is missing, so read `count` as well |

## Page operations

```sh
pf.sh edit IN.pdf --out OUT.pdf [--rotate 1,3:90] [--delete 2,4] [--move 5:1] \
                  [--insert-blank 1] [--title T] [--author A] [--full]
pf.sh combine a.pdf b.pdf c.pdf --out combined.pdf
pf.sh extract IN.pdf --pages 1,3,5-8 --out OUT.pdf
pf.sh split IN.pdf (--every N | --before 3,7) [--out-dir DIR]
```

- `edit` options run **in the order given**. Page numbers in each option refer to
  the document as left by the options before it. Example: `--delete 2 --rotate 8:90`
  on a 9-page file rotates the page that is last *after* the deletion.
- Page numbers are positive integers only. There is no `last`, `-1` or `end`, so
  read the count with `info` first.
- `--rotate PAGES:DEG` **adds** DEG clockwise to the current rotation. It does not
  set an absolute value. Rotating a page already at 90 by 90 gives 180.
- `--move 5:1` moves page 5 to position 1.
- Without `--full`, `edit` writes an incremental update (the old bytes plus the
  changes; the file grows). `--full` rewrites it compactly.
- `edit --out` onto its own input **overwrites it silently** (exit 0). Always
  write to a new path.
- `combine` adds one top-level bookmark per input, titled after the input's file
  name. Images and `.txt` files can be combined too.
- `extract` ranges must ascend (`3-1` is an error). Order comes from the list:
  `--pages 3,2,1` reverses.
- `split` names files `<stem>-p1-3.pdf`, `<stem>-p4-6.pdf`, … in `--out-dir`
  (default: next to the input). By bookmark or by size: use `doc_split` via `run`.

## Batch

```sh
pf.sh batch FILES/DIRS… --steps convert,ocr,optimize --out-dir DIR \
            [--recursive] [--root DIR] [--stop-on-error] \
            [--ppi 150] [--quality 60] [--dpi 300] [--language en] [--ocr-all-pages]
```

- Steps: any of `convert` (non-PDF inputs such as images to PDF; must come first),
  `ocr`, `optimize` (Reduce File Size; `--ppi`, `--quality`), each at most once.
- Prints a JSON report `{completed, failed, skipped, files:[{path, status, error?}], stopped}`.
  Exit 1 if any file failed. Read `files[].error` for the cause.
- Sources are never modified. **Existing outputs are never replaced**: a re-run
  into the same `--out-dir` writes `name (2).pdf`. Use an empty or new folder.
- `--recursive` mirrors subfolders under `--out-dir`. Without it, only files
  directly in the folder are processed.
- `--ocr-all-pages` re-OCRs pages that already have text. By default they are
  skipped, so text PDFs pass through unchanged.
- OCR needs the models: `pf.sh` sets `PDFCRAFT_MODELS`. Bare `pdfcraft-cli batch
  --steps ocr` fails every file with "the text recognition models are not installed".

## Tools

```sh
pf.sh tools                                  # every tool + JSON Schema (large; use pf_tool.py)
pf.sh run TOOL key=value … [--root DIR] [--out image.png]
pf.sh run --script steps.json [--root DIR] [--report]
```

- A single `run TOOL` has no open document, so it only suits document-free tools:
  `ocr_status`, `command_list`, `doc_combine`, `ocr_recognize_files`, `doc_batch`,
  and `printers`. Anything taking `doc` needs a script that opens the file first.
- `key=value` values are parsed as JSON when they look like it: `'paths=["a.pdf"]'`.
- `--script` stops at the first failing step. Later steps are reported
  `skipped`. `--report` prints `{ok, steps:[{step, tool, status, result|error}]}`
  on stdout. It exits 1 when a step fails. The failing step's `error` names the
  argument at fault (`missing argument doc`, `pages must be an array of integers`).
- `--root DIR` confines file access to DIR. Without it, any path is readable and
  writable, and missing parent folders are created.

## Servers and the app

- `pf.sh mcp [--compact] [--automation-read-root DIR] [--automation-write-root DIR]`
  is a stdio MCP server exposing the same tools. See [live-app.md](live-app.md).
- `pf.sh ui --control FILE METHOD [key=value…] [--out shot.png]` drives a running
  app. See [live-app.md](live-app.md).
