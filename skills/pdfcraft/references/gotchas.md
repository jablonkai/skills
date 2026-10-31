# Gotchas (pdfcraft-cli 0.16.1)

Each was found by running the CLI. Where the fix is mechanical, the scripts
already apply it.

## Environment

- **OCR is unavailable through the symlinked CLI.** `~/.local/bin/pdfcraft-cli`
  looks for its models next to the link, so `ocr_status` says
  `available: false`, and `batch --steps ocr` fails every file with "the text
  recognition models are not installed". Set
  `PDFCRAFT_MODELS=/Applications/PdfCraft.app/Contents/Resources/models`. `pf.sh`
  and the Python scripts do this. Shell exports don't carry across separate tool
  calls, so use `pf.sh` rather than a one-off `export`.
- Don't run `/Applications/PdfCraft.app/Contents/MacOS/PdfCraft --help` to read
  help. It opens the GUI. Use `pdfcraft-cli help <sub>`.

## Tool scripts (`run --script`)

- **Every document tool needs an explicit `"doc"`.** There is no current
  document: `doc_save: missing argument doc`. Ids are 1, 2, … in the order
  documents are opened or created. `pf_run.py` fills them in.
- A single `run TOOL key=value` call has no open document. `run form_fields
  path=x.pdf` fails with `unknown argument "path"`. Open the file in a script.
- `pages` must be a JSON array of integers: `"pages": "all"` and `"pages": "1-3"`
  are rejected. Omit `pages` for every page. Only `doc_combine`'s per-file
  `pages` takes range strings.
- Unknown tool argument names are errors (`unknown argument`), so a typo fails
  loudly rather than being ignored.
- The script stops at the first error and marks the rest `skipped`. Nothing is
  saved unless a `doc_save` step ran before the error.

## Page edits

- `edit --out` onto its own input overwrites it with exit 0. Write elsewhere.
- No `last`/`-1` page keyword. Read `pages` from `info`.
- `edit` options run in order, and each sees the result of the previous one.
  After `--delete 2`, the old page 9 is page 8.
- Rotation is relative: `--rotate N:90` and `page_rotate degrees: 90` add to the
  existing `/Rotate`. To get an absolute value, read the current one
  (`pf_verify.py --rotation`, or `doc_info`) first.
- `info` has no per-page rotation. Use `doc_info` via `pf_verify.py`.
- `combine` adds a top-level bookmark per input file, titled with the file name.
  It is visible in `doc_info.outline`, and it leaks file names. Remove it with
  `bookmark_delete` or `doc_remove_hidden categories=["bookmarks"]` if that
  matters.

## Batch

- Existing outputs are never replaced. A second run into the same `--out-dir`
  adds `name (2).pdf`, so counts double. Start from an empty folder.
- Exit 1 if any file failed, and the JSON report on stdout names each file's
  error. Only files directly in a folder are processed unless `--recursive` is
  given.
- Output files are written mode 600.

## Redaction

- `redact_mark find` **fails the step when nothing matches** (`nothing matched,
  so nothing was marked`), which aborts the rest of the script. `words: [...]`
  tolerates misses per entry and reports `matched_words`. `pf_redact.py` uses it.
- Matching is case-insensitive by default, and substring-based unless
  `whole_words: true`.
- Marks alone remove nothing. Saving after `redact_mark` without
  `redact_apply` leaves the text extractable, and `audit` reports
  `unapplied-mark` (exit 1).
- A black rectangle drawn over text (a comment flattened into the page, or a
  shape) hides it visually, but `text` still extracts it. `audit` reports
  `covered-text`. Inputs can already contain these: audit the input as well as
  the output.
- A `covered-text` finding's `covered_text` is the **whole text line** the box
  overlaps ("Contact: Dana Whitfield, programme office." for a box over the
  name). Redacting that string with `find` wipes the visible words too. Redact
  the finding's `rect` on its `page` (`redact_mark rect`, or
  `pf_redact.py --fix-faux`) to remove exactly what the box hides.
- `audit` also exits 1 when the file doesn't exist. Read `count` in its JSON,
  not only the exit status.
- Page text is not the only place a phrase lives. Title/subject/keywords,
  bookmarks (including the ones `combine` adds), comments, attachments and form
  values can hold it too. `pf_verify.py --absent` checks text, info and
  bookmarks. `doc_remove_hidden` (`pf_redact.py --sanitize`) clears the rest.
- Scans have no text layer, so there is nothing to match. OCR first, then redact
  (the OCR text and the image under the box are both removed).
