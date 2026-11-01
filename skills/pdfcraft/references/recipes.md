# Recipes

`S=<skill>/scripts`. Every recipe writes to new paths and ends with a read-back.
Each one was run against pdfcraft-cli 0.17.0.

## Contents

- [Merge, then edit pages and metadata](#merge-then-edit-pages-and-metadata)
- [Split and extract](#split-and-extract)
- [OCR and optimize a folder of scans](#ocr-and-optimize-a-folder-of-scans)
- [Redact and prove it](#redact-and-prove-it)
- [Fill a form](#fill-a-form)
- [Comments, stamps, watermark, header/footer](#comments-stamps-watermark-headerfooter)
- [Edits that need ids from earlier steps](#edits-that-need-ids-from-earlier-steps)

## Merge, then edit pages and metadata

"Merge q1.pdf, q2.pdf, q3.pdf, drop page 2, turn the last page to landscape, title it 2026 Report."

```sh
bash $S/pf.sh combine q1.pdf q2.pdf q3.pdf --out work/merged.pdf
N=$(bash $S/pf.sh info work/merged.pdf | python3 -c 'import sys,json;print(json.load(sys.stdin)["pages"])')
# --delete runs first, so the last page is now N-1.
bash $S/pf.sh edit work/merged.pdf --out report.pdf --delete 2 --rotate $((N-1)):90 \
     --title "2026 Report" --full
python3 $S/pf_verify.py report.pdf --pages $((N-1)) --rotation "last=90" --title "2026 Report"
```

- `edit` options apply in order, and each option's page numbers refer to the
  result of the options before it. Compute "last" after the deletions.
- Rotation is added to what the page already has. If the source page is already
  rotated, `pf_verify.py --rotation` shows the real value. Pick the delta that
  reaches the target.
- To check the order, use `--page-order` with one marker string per page (a
  heading or page footer you can see in `text`).

## Split and extract

```sh
bash $S/pf.sh split big.pdf --every 10 --out-dir parts/          # parts/big-p1-10.pdf …
bash $S/pf.sh split big.pdf --before 5,12 --out-dir parts/       # 1-4, 5-11, 12-end
bash $S/pf.sh extract big.pdf --pages 1,3,5-8 --out picked.pdf   # in the order given
python3 $S/pf_verify.py parts/ --count 3 --valid
```

Split at top-level bookmarks (files named after them) or by size:

```json
[{"tool": "doc_open", "args": {"path": "big.pdf"}},
 {"tool": "doc_split", "args": {"out_dir": "chapters", "bookmarks": true}}]
```

## OCR and optimize a folder of scans

```sh
bash $S/pf.sh --doctor                                  # must print "ocr: available"
mkdir -p ocr-out && test -z "$(ls -A ocr-out)"          # empty folder: re-runs add "name (2).pdf"
bash $S/pf.sh batch scans/ --steps ocr,optimize --out-dir ocr-out > batch.json
python3 -c 'import json;d=json.load(open("batch.json"));print(d["completed"],d["failed"]);[print(f) for f in d["files"] if f["status"]!="ok"]'
python3 $S/pf_verify.py ocr-out/ --count 3 --searchable --valid --contains "<a word you can see on a page>"
```

- `--searchable` proves every page has a text layer. `--contains` with a word
  visible in a render proves the OCR read it correctly.
- Image files (JPEG/PNG/TIFF) instead of PDFs: add `convert` as the first step.
- Pages that already have text are skipped. `--ocr-all-pages` redoes them.
- One file in a script: `ocr_recognize`, then `doc_save` (or `doc_reduce` to a
  new path for a smaller copy).

## Redact and prove it

```sh
python3 $S/pf_redact.py contract.pdf --out contract-redacted.pdf \
        --find "Project Falcon" "Jane Q. Doe" --pattern email phone
```

It audits the input first. **Read `input_faux_redactions`**: a black box
someone drew over live text is listed there, with the line it sits on. Add
`--fix-faux` to redact exactly what each box hides (by its rectangle) and name
those words to the user. Leave it off only when told not to change anything
else, and then report that the output's audit will still flag the box. Then it
marks, applies and saves to a new path, and proves
the result: every phrase absent from page text, title, subject, keywords and
bookmarks (any case), and `audit` clean. `ok: false` or a `warning` about zero
matches needs attention. A `hint` means page text is clean, but the title or a
bookmark still holds the phrase. A scan without a text layer has nothing to
match, so OCR it first.

- Default matching is case-insensitive and substring-based. Add `--whole-words`
  so "Doe" doesn't hit "Doerr". `--case-sensitive` keeps other casings on purpose.
- `--sanitize` also removes hidden data: metadata, attachments, comments,
  bookmarks, scripts, hidden layers, form fields (flattened). That is right for
  documents leaving the organisation, but tell the user what it drops.
- Visual check:
  `bash $S/pf.sh render contract-redacted.pdf --page 1 --dpi 72 --out p1.png`.
- Manual equivalent: `redact_mark` (`words: [...]`) → `redact_apply` → `doc_save`.
  Without `redact_apply` the marks are only annotations. The text stays, and
  `audit` reports `unapplied-mark`.

## Fill a form

```json
[{"tool": "doc_open", "args": {"path": "application.pdf"}},
 {"tool": "form_fields", "args": {}}]
```

```sh
python3 $S/pf_run.py fields.json --full | python3 -c 'import sys,json;r=json.load(sys.stdin)["steps"][1]["result"][0];[print(f["name"],f["type"],f.get("options",""),repr(f["value"])) for f in r["fields"]]'
```

Fill with the exact names and option values it printed:

```json
[{"tool": "doc_open", "args": {"path": "application.pdf"}},
 {"tool": "form_fill", "args": {"values": {"FullName": "Ada Lovelace", "Agree": true, "Country": "Hungary"}}},
 {"tool": "doc_save", "args": {"path": "application-filled.pdf"}},
 {"tool": "form_fields", "args": {}}]
```

The final `form_fields` is the read-back. Compare each `value`. Add
`{"tool": "doc_flatten", "args": {"fields": true}}` before the save only if the
user wants a non-editable copy.

## Comments, stamps, watermark, header/footer

```json
[{"tool": "doc_open", "args": {"path": "draft.pdf"}},
 {"tool": "comment_add", "args": {"page": 1, "type": "highlight", "find": "deadline", "all": true, "contents": "Confirm date"}},
 {"tool": "comment_add", "args": {"page": 1, "type": "stamp", "stamp": "draft", "at": [500, 60]}},
 {"tool": "doc_watermark", "args": {"text": "CONFIDENTIAL", "opacity": 0.2}},
 {"tool": "doc_header_footer", "args": {"footer_center": "<<Page 1 of n>>", "header_right": "<<yyyy-mm-dd>>"}},
 {"tool": "doc_save", "args": {"path": "draft-marked.pdf"}}]
```

Read back with `info` (`annotations` count) and a render. `text` shows watermark
and header/footer text, because they are page content.

## Edits that need ids from earlier steps

Several documents in one script: `pf_run.py` fills a missing `doc` with the
latest opened one. `"@1"`, `"@2"` pick a specific one.

```json
[{"tool": "doc_open", "args": {"path": "main.pdf"}},
 {"tool": "doc_open", "args": {"path": "appendix.pdf"}},
 {"tool": "page_extract", "args": {"doc": "@2", "pages": [1, 2], "out": "tmp/app-1-2.pdf"}},
 {"tool": "page_insert_file", "args": {"doc": "@1", "path": "tmp/app-1-2.pdf", "at": 4}},
 {"tool": "doc_save", "args": {"doc": "@1", "path": "main-with-appendix.pdf"}}]
```

Check argument names with `pf_tool.py page_insert_file` before running:
`--dry-run` shows the resolved steps without touching anything.
