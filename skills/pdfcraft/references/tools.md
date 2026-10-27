# PdfCraft 0.14.0 tools used by the recipes

Pinned for 0.14.0 (179 tools in all). For anything not listed, or when a call
here fails after an upgrade, look it up instead of guessing:

```sh
python3 $S/pf_tool.py --search redact        # find tools by word
python3 $S/pf_tool.py redact_mark            # one tool's arguments (* = required)
python3 $S/pf_tool.py --commands rotate      # menu commands → the tool behind each
```

Conventions shared by every tool:

- `doc` is the session id from `doc_open` / `doc_create` (1, 2, … in order).
  `doc_combine` and `page_extract` with `open: true` take the next id too.
- Page numbers are 1-based. `pages` is always a JSON **array of integers**: no
  strings, ranges or `"all"`. Omit it to mean every page.
- Geometry (`rect`, `at`) is in points from the **top-left** of the displayed
  page, y down: the same frame as `page_render` at 72 dpi and `text_find` rects.
  `[x0, y0, x1, y1]`.
- Edits are in memory until `doc_save`. Save to a new `path` (a full rewrite) and
  keep the source.

## Documents

| Tool | Key args | Notes |
|---|---|---|
| `doc_open` | `path`*, `password` | Returns `{doc, pages, editable}` |
| `doc_create` | `from`*: `blank` (`pages`, `width`, `height`) · `images` (`paths`) · `text` (`path` or `text`) | `text` splits pages on form feeds. `images` makes a scan-like, text-free PDF |
| `doc_save` | `doc`*, `path`, `full`, `flatten_fill_sign` | Creates parent folders. Atomic |
| `doc_info` | `doc`* | Per-page `rotation`, `width`, `height`, `label`; `outline`, `fields`, `annotations`, `security` |
| `doc_set_info` | `doc`*, `key`* (`Title`, `Author`, `Subject`, `Keywords`, or custom), `value`* | |
| `doc_combine` | `paths`*, `pages` (per file, e.g. `"1-3, 6"`), `out`, `open` | Document-free: works with a single `run` |

## Pages

| Tool | Key args |
|---|---|
| `page_rotate` | `doc`*, `degrees`* (multiple of 90, added clockwise), `pages`, `subset` (all/even/odd), `orientation` |
| `page_delete` | `doc`*, `pages`* |
| `page_move` | `doc`*, `pages`*, `to`* (position counted before the move) |
| `page_insert_blank` / `page_insert_file` / `page_replace` / `page_duplicate` / `page_reverse` | see `pf_tool.py` |
| `page_extract` | `doc`*, `pages`*, `out` or `out_dir` + `separate`, `delete` |
| `doc_split` | `doc`*, `out_dir`*, one of `every`, `before`, `bookmarks: true`, `max_mb` |
| `page_number` | `doc`*, `from`*, `to`*, `style`, `prefix`, `start` (page labels, not stamped numbers) |

## Text, OCR, size

| Tool | Key args | Notes |
|---|---|---|
| `text_extract` | `doc`*, `pages`, `rect` | |
| `text_find` | `doc`*, `query`*, `limit` | Case-insensitive. Returns page + rects, which you can feed to `redact_mark rect` or `comment_add` |
| `ocr_status` | — | `available: false` means PDFCRAFT_MODELS is missing (use `pf.sh`) |
| `ocr_recognize` | `doc`*, `pages`, `language` (`en`), `dpi`, `skip_text_pages` | Adds invisible text over the image. The image is unchanged |
| `ocr_recognize_files` | `paths`*, `folder`* | Document-free multi-file OCR |
| `doc_reduce` | `doc`*, `path`* | Reduce File Size (150 ppi JPEG) |
| `doc_optimize` | `doc`*, `path`*, `preset` (standard/mobile), many discard options | |

## Redaction and sanitizing

| Tool | Key args | Notes |
|---|---|---|
| `redact_mark` | `doc`*, one of: `find` (phrase) · `words` (list) · `pattern` (phone/email/credit-card/ssn/date) · `rect`+`page` · `whole_pages: true`; plus `pages` or `page`, `case_sensitive`, `whole_words`, `overlay`, `code_set`+`codes`, `fill` | Case-insensitive by default. `find` **fails the step when nothing matches**. `words` reports `matched_words` per entry and fails only if none match |
| `redact_apply` | `doc`*, `pages` | Removes text, images, vectors, comments and fields under the marks. Fails if anything readable remains |
| `redact_clear` | `doc`* | Drop pending marks |
| `doc_audit_redactions` | `doc`* | Same as the `audit` subcommand |
| `doc_hidden_info` / `doc_remove_hidden` | `doc`*, `categories` | Metadata, attachments, scripts, hidden layers, comments… Remove all when no categories are given |

## Forms

| Tool | Key args | Notes |
|---|---|---|
| `form_fields` | `doc`* | `name`, `type`, `value`, `options`, `page`, `rect`, flags |
| `form_fill` | `doc`*, `values`* `{name: value}` | Strings for text/combo/radio (the option), `true`/`false` for check boxes, string arrays for multi-select lists |
| `form_add_field` | `doc`*, `page`*, `type`*, `rect`*, `name`, … | |
| `form_merge_data` / `doc_import_data` / `doc_export_data` | see `pf_tool.py` | Data-file merges (FDF/XFDF/CSV) |
| `doc_flatten` | `doc`*, `fields`, `comments` | Bake appearances into the page content. They can no longer be edited |

## Comments, stamps, marks

| Tool | Key args |
|---|---|
| `comment_add` | `doc`*, `page`*, `type`* (`note`, `highlight`, `underline`, `strikeout`, `squiggly`, `rectangle`, `oval`, `line`, `arrow`, `ink`, `textbox`, `stamp`, `polygon`, `cloud`, `polyline`, `callout`, `caret`, `attachment`, `replace`); `contents`, `author`, `color`, `fill`; geometry by type: `at`, `rect`, `from`/`to`, `find` (+`all`) for text markup; `stamp` names such as `approved`, `confidential`, `draft` |
| `comment_list` / `comment_edit` / `comment_delete` / `comment_reply` / `comment_set_status` | see `pf_tool.py` |
| `doc_watermark` | `doc`*, `text` or `file`, `opacity`, `rotation`, `scale`, `behind`, `pages`, `replace` |
| `doc_header_footer` | `doc`*, `header_left/center/right`, `footer_*`; tokens such as `<<1 of n>>`, `<<yyyy-mm-dd>>`, Bates |
| `stamp_custom` | `doc`*, `page`*, `path`* (image or PDF page), `at` or `rect` |
| `bookmark_add` | `doc`*, `title`*, `page`*, `parent`, `position` |

## Security and standards

| Tool | Key args |
|---|---|
| `doc_protect` / `doc_unprotect` | `open_password`, `permissions_password`, `printing`, `changes`, `copy` (applied by the next save) |
| `pdfa_convert` / `pdfa_verify` | `level` (e.g. `2b`, `3b`) |
| `accessibility_check` / `accessibility_autotag_apply` | see `pf_tool.py` |
| `doc_export_office` | `doc`*, `path`* (`.docx`, `.pptx`, `.html`, `.rtf` by extension) |
