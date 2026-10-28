---
name: wordcraft
description: 'Automate WordCraft, the Word-style word processor, with wordcraft-cli (headless or live): fill .docx templates and {{placeholders}} (headers and footers too) without losing formatting, build documents from Markdown or an outline with heading styles, tables and an updated table of contents, add tracked changes and comments by a named author, export markup PDFs, refresh fields, mail-merge from CSV, and convert docx/doc/odt/rtf/html/md to docx/pdf one file or a folder at a time, checked by inspect read-back and a page render. Use when the user mentions WordCraft or wordcraft-cli, or wants a Word document filled, reviewed, built or converted with it: "fill this docx template with WordCraft", "add my edits as tracked changes by Legal", "turn these markdown notes into docx with a TOC", "refresh the TOC". Not for Apple Pages (pages), headless LibreOffice/soffice (libreoffice), python-docx/OOXML code without WordCraft (docx), extracting documents to Markdown (markitdown), e-books (calibre) or PDF merge/split (pdf).'
summary: "automate WordCraft with wordcraft-cli — docx template fill with formatting kept (headers and footers too), documents from Markdown with heading styles, tables and an updated TOC, tracked changes and comments by a named author, markup PDFs, docx/odt/rtf/html/md/pdf conversion and folder batches, inspect read-back verified"
category: office
compatibility: "Built for WordCraft 0.12.0 and wordcraft-cli 0.12.0 on macOS 27; helper scripts need Python 3.9+. Pre-1.0, so command ids may change."
risk: medium
tags: [wordcraft, word, docx, templates, tracked-changes, comments, toc, markdown, conversion, headless]
metadata:
  version: "1.1.0"
---

# WordCraft via wordcraft-cli

WordCraft is a Word-style word processor. Every ribbon button, dialog and keystroke is a
command in one registry: 648 of them in 0.12.0. The same commands run headless from
`wordcraft-cli`, in a headless MCP session, and in the desktop app. This skill works
**headless by default**, so no window opens, and checks every result by reading the
document back. It is verified against **WordCraft 0.12.0 / wordcraft-cli 0.12.0**. The
software is pre-1.0: when a pinned id fails, look it up rather than guess.

```sh
command -v wordcraft-cli || ls ~/.local/bin/wordcraft-cli
wordcraft-cli --version
export WORDCRAFT_REGION=en-US   # paper size otherwise follows the locale (A4 vs Letter)
```

`wordcraft-cli <subcommand> --help` only prints the global help, and there is no
`describe`: look commands up with `wc_commands.py`.

## Pick the route

| Task | Route |
|---|---|
| Fill `{{placeholders}}` in a .docx from JSON, save docx/pdf | `scripts/wc_fill.py TEMPLATE DATA.json OUT.docx OUT.pdf` |
| Convert a folder (md/docx/odt/rtf/html → docx/pdf/…), optional TOC | `scripts/wc_batch.py IN OUT --to docx,pdf [--toc]` |
| Convert one file, refresh fields, print markup | `wordcraft-cli convert IN OUT [--update-fields] [--markup]` |
| Edit a document: tracked changes, comments, styles, tables, TOC | `wordcraft-cli run --script steps.json --author NAME` |
| Steps that need a read mid-way (comment ids, positions) | `scripts/wc_session.py steps.json` |
| Work in the open app the user is looking at | `scripts/wc_live.py start` + `wc_session.py --connect` |
| Check the result | `scripts/wc_verify.py doc OUT.docx`, `wordcraft-cli render OUT.docx p1.png --page 1` |

## Scripts

`S=<this skill>/scripts`; run as `python3 $S/<script>`. Standard library only; each has
a full `--help`. All refuse to overwrite without `--overwrite` and never write an input.

- **`wc_commands.py WORD…`** (`--prefix review.`, `--id edit.replaceAll`): filtered
  registry lookup with params. Never dump `wordcraft-cli commands` into context.
- **`wc_fill.py`**: replaces every placeholder in the body, tables, **headers, footers**,
  footnotes and text boxes, literally (`^p`/`^&` in values are not expanded), keeps the
  run formatting, saves all outputs in one run and exits 1 if any `{{…}}` is left or
  the data misses one.
- **`wc_batch.py`**: one run per file, every format at once; `--toc` puts a filled TOC
  at the top with no stray paragraph, `--update-fields`, `--markup`.
- **`wc_session.py`**: one stateful session over `wordcraft-cli mcp` (headless, file
  access confined to `--root`), or the live app with `--connect`.
- **`wc_live.py start|status|stop`**: launches a separate app instance with its
  authenticated control port, and quits only that instance.
- **`wc_verify.py`**: `doc` (blocks, styles, tables, headers and footers, placeholders
  left, revisions and comments **with their authors**, TOC entries; `--author`,
  `--style`, `--no-placeholders` turn it into a check), `files`, `hash`.

## Workflow

1. **Look first.** `wordcraft-cli inspect IN | head -c 3000` or `wc_verify.py doc IN`:
   styles, tables, `parts` (headers, footers, comments), sections. Note what must stay.
2. **Never touch originals.** Write to a new path; hash inputs if the user cares
   (`wc_verify.py hash DIR > before.sha256`).
3. **Do it** with the route above. For `run`, write a `--script` JSON (below); look up
   any id you are not sure of with `wc_commands.py`.
4. **Read back** with `wc_verify.py doc` (and `--author`/`--style`/`--no-placeholders`).
   `inspect` alone shows revisions and comments but **not who made them**
   (`run --file OUT --cmd review.changes --cmd review.comments --print` also lists them).
5. **Look** at one page: `wordcraft-cli render OUT.docx /tmp/p1.png --page 1`, then
   view the PNG. Layout problems (overflowing tables, wrong page size) only show here.
   `render` takes documents, not PDFs; to see comments and revision marks, use
   `wordcraft-cli convert OUT.docx /tmp/markup.png --markup` (page 1 with the margin).
6. **Report** paths, page counts and what the read-back confirmed.

## `run --script`: the main edit tool

```json
{"file": "in.docx",
 "commands": [
   {"command": "review.trackChanges", "params": {"value": true}},
   {"command": "select.text", "params": {"text": "Payment terms"}},
   "caret.end", "text.newParagraph",
   {"command": "text.insert", "params": {"text": "Invoices are payable within 30 days."}},
   {"command": "select.text", "params": {"text": "late fee"}},
   {"command": "review.newComment", "params": {"text": "Agreed with finance?"}}],
 "save": ["out.docx", "out.pdf"]}
```

`wordcraft-cli run --script steps.json --author "Claude"`. Relative paths resolve against
**the script's folder**, not the shell's cwd (`--script -` reads stdin; then use absolute
paths). More recipes: [recipes.md](references/recipes.md).

## Traps that fail silently

- **Two `--save` flags write only the first file.** Save several formats with the
  script's `"save": [...]` list.
- **`edit.replaceAll` covers one story**, the one the caret is in: headers and footers
  keep their placeholders. Move in with `caret.set {"pos": {"story": {"part": ID},
  "path": [0], "off": 0}}` (part ids from `inspect`), or use `wc_fill.py`.
- **`^` codes in replacement text are live** by default: `^p` breaks the paragraph,
  `^&` re-inserts the match. Pass `"special": false` for literal values.
- **TOC at `caret.docStart`** leaves an empty heading-styled paragraph above it, and
  deleting that paragraph destroys the TOC. Open a Normal paragraph first (see recipes).
- **A TOC or other field is empty until updated**: `references.updateFields {"all": true}`
  in the script, or `convert --update-fields`.
- **Markup PDFs**: `convert IN out.pdf --markup` (or `file.printMarkup` before saving);
  a plain export shows neither comments nor revision marks.
- **Comment and revision authors** come from `--author` (or `file.setAuthor`); without
  it they are "WordCraft User".

More, with fixes: [gotchas.md](references/gotchas.md).

## References

- [cli.md](references/cli.md): subcommands, flags, the script schema, formats, `inspect`
  JSON, MCP tools.
- [commands.md](references/commands.md): pinned 0.12.0 command ids by task.
- [recipes.md](references/recipes.md): template fill, review pass, Markdown with TOC,
  folder conversion, mail merge, styles, tables, headers and footers.
- [gotchas.md](references/gotchas.md): every trap found while building this skill.
- [security.md](references/security.md): automation roots, the live control port and
  its key, the stop path.
