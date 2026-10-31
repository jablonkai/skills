---
name: pdfcraft
description: 'Automate PdfCraft, the Acrobat-style PDF editor, headless with pdfcraft-cli: merge, split, extract, rotate, reorder and delete pages, set title/author metadata, OCR folders of scanned PDFs into searchable text and optimize their size, redact phrases or patterns for good and prove it with an audit for faux redactions, fill and flatten forms, add comments, stamps, watermarks and headers/footers, and run any of its 182 tools from a JSON script, all verified by an info, text and render read-back. Use when the user mentions PdfCraft or pdfcraft-cli, or wants PDFs edited with it: "merge these PDFs, drop page 2 and rotate the last page", "OCR this folder of scans", "redact every mention of the client and prove it is gone", "check this PDF for fake redactions", "fill this PDF form". Not for converting PDFs to Markdown (markitdown), Office documents to PDF or PDF/A from documents (libreoffice), Python PDF scripting with pypdf/reportlab and no PdfCraft (pdf), or Word documents (wordcraft).'
summary: "automate PdfCraft headless with pdfcraft-cli — merge, split, extract, rotate and reorder pages, metadata, batch OCR and optimize, redaction proven by audit, form fill, comments and watermarks, JSON tool scripts, info, text and render read-back verified"
category: office
compatibility: "Built for PdfCraft 0.16.1 and pdfcraft-cli 0.16.1 on macOS 27; Python 3.9+ for the helper scripts. Pre-1.0, so tool names and arguments may change."
risk: medium
tags: [pdfcraft, pdf, ocr, redaction, forms, merge, split, headless]
license: GPL-3.0-only
metadata:
  version: "1.0.4"
  author: "Tamás Jablonkai"
---

# PdfCraft via pdfcraft-cli

PdfCraft is an Acrobat-style PDF editor. Its features are exposed as 182 automation
tools (open, edit pages, OCR, redact, forms, comments, standards…). `pdfcraft-cli`
runs them headless, with no window, through quick subcommands for common page jobs
and through JSON tool scripts for everything else. Verified against **PdfCraft
0.16.1** and **pdfcraft-cli 0.16.1** on macOS. It is pre-1.0, so when a tool name
or argument pinned in `references/` fails, look it up with `pf_tool.py` rather
than guessing.

## Start here

```sh
S=<this skill>/scripts
bash $S/pf.sh --doctor          # CLI path, version, and "ocr: available"
```

**Run the CLI through `bash $S/pf.sh …`, not bare `pdfcraft-cli`.** The installed
CLI is a symlink that can't find its own OCR models, so every OCR job fails until
`PDFCRAFT_MODELS` points at the app bundle. `pf.sh` sets it and otherwise passes
arguments through unchanged. Shell exports don't survive between separate
commands, so set it per call this way. The Python scripts set it themselves.

## Pick the route

| Task | Route |
|---|---|
| Merge, extract, split; rotate, delete, move pages; title/author | `pf.sh combine` / `extract` / `split` / `edit` |
| OCR and/or shrink many files | `pf.sh batch DIR --steps ocr,optimize --out-dir NEW` |
| Redact phrases/patterns/pages and prove it | `scripts/pf_redact.py` |
| Anything else (forms, comments, stamps, watermark, bookmarks, security, PDF/A, export) | JSON steps → `scripts/pf_run.py` |
| Check any result | `scripts/pf_verify.py` (plus `pf.sh render` for a visual) |
| The user wants to watch it happen in the app, or wants an MCP server | [live-app.md](references/live-app.md) |

## Scripts

Python 3.9+, standard library only.

- **`pf.sh`**: `pdfcraft-cli` with OCR models found. `--doctor` checks the setup.
- **`pf_run.py STEPS.json|-`** runs a tool script and prints one line per step.
  It exits 1 if any step failed or was skipped. It fills a missing `"doc"` with the
  latest opened/created document, and `"@1"`, `"@2"` name one explicitly. It makes
  relative paths absolute. `--dry-run` shows the resolved steps; `--full` prints
  the raw report.
- **`pf_tool.py NAME…`** gives a tool's arguments (`*` = required);
  `--search WORD…` finds tools; `--commands WORD` maps menu commands to tools.
  Use it instead of `pdfcraft-cli tools`, which dumps every schema at once.
- **`pf_redact.py IN --out OUT --find PHRASE… [--pattern email phone…] [--page N…]`**
  audits the input, marks, applies, saves to a new path, then proves each phrase is
  gone (page text, title, subject, keywords, bookmarks) and `audit` is clean.
  `--whole-words`, `--case-sensitive`, `--overlay TEXT`, `--sanitize` (also strips
  hidden data), `--fix-faux` (also truly redacts what existing fake boxes hide).
- **`pf_verify.py PATH… [checks]`** takes files or folders and prints JSON, exit 1
  on any failure. Checks: `--pages N`, `--rotation "1-7=0,last=90"`, `--title`,
  `--author`, `--contains S`, `--absent S`, `--page-order S1,S2,…` (page i
  contains S_i), `--searchable`, `--audit-clean`, `--valid`, `--count N`.

## Tool scripts

A script is a JSON array of `{"tool": NAME, "args": {...}}`, run in order in one
session, stopping at the first error:

```json
[{"tool": "doc_open", "args": {"path": "in.pdf"}},
 {"tool": "page_rotate", "args": {"degrees": 90, "pages": [3]}},
 {"tool": "doc_set_info", "args": {"key": "Title", "value": "Q3 Report"}},
 {"tool": "doc_save", "args": {"path": "out/q3.pdf"}}]
```

Rules that cause most failures:

- **Pages are JSON arrays of integers** (`[1, 3]`), never `"all"` or `"1-3"`.
  Omit `pages` to mean every page.
- Coordinates are points from the **top-left** of the displayed page, y down.
  `text_find` returns rects in the same frame, ready for `redact_mark` or
  `comment_add`.
- Nothing is written until `doc_save`. Save to a new path.
- Argument names are strict (a typo is an `unknown argument` error). Check with
  `pf_tool.py NAME`.

Pinned tool table: [tools.md](references/tools.md). Worked scripts:
[recipes.md](references/recipes.md).

## Things that silently go wrong

These are the traps that produce a plausible-looking but wrong result. The full
list is in [gotchas.md](references/gotchas.md).

- **`edit` options apply in order, and page numbers shift.** `--delete 2
  --rotate 9:90` on a 9-page file fails: after the delete, the last page is 8.
  There's no `last` keyword. Read the count from `info` and compute it.
- **Rotation adds to the current angle.** A page already at 90 becomes 180 with
  another 90. `info` doesn't show rotation, but `pf_verify.py --rotation` does.
- **`edit --out` onto its input overwrites it** with no warning.
- **`batch` never replaces outputs.** A re-run into the same folder adds
  `name (2).pdf`. Use a fresh, empty `--out-dir` and check `--count`.
- **A black box is not a redaction.** Shapes drawn over text hide it on screen,
  but `text` still extracts it. `audit` reports these as `covered-text`, and
  inputs may already contain them. `pf_redact.py` lists them in
  `input_faux_redactions`. A box means someone meant to hide that text, and a
  document going out will fail its audit while the box is fake. So by default,
  pass `--fix-faux` and tell the user what was under each box. Only leave a box
  (and flag it) if the user said to touch nothing else.
- **`covered_text` is the whole line the box touches**, not just the hidden
  words. Redacting that string also removes visible text. Redact by the box's
  `rect` (`--fix-faux` does), or by the specific words.
- **Marks without `redact_apply` remove nothing.** `audit` reports
  `unapplied-mark`.
- **Scans have no text** until OCR, so redaction and `--contains` find nothing.
  OCR first.

## Verify before reporting

Read every result back from the saved file. A successful step only means the call
ran. Match the check to the request:

| Request | Proof |
|---|---|
| Page edits | `pf_verify.py OUT --pages N --rotation … --page-order …` |
| Metadata | `--title` / `--author` |
| OCR | `--searchable` on the outputs, plus `--contains` with a word you can see in a render |
| Redaction | `pf_redact.py` result `ok: true`, or `pf_verify.py --absent … --audit-clean`, plus a render of a redacted page |
| Forms | a closing `form_fields` step and a comparison of the values |
| Folder jobs | `--count N` on the output folder and the batch report's `failed: 0` |

Keep the sources untouched. Report the output paths and what the checks showed.
If a check fails, say so; don't describe the job as done.
