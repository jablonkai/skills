# Recipes (verified with WordCraft 0.12.0)

`S=<skill>/scripts`. Set `export WORDCRAFT_REGION=en-US` (or the user's region) so the
paper size doesn't depend on the machine.

## Fill a template

```sh
python3 $S/wc_fill.py invoice-template.docx data.json out/invoice.docx out/invoice.pdf
python3 $S/wc_verify.py doc out/invoice.docx --no-placeholders
wordcraft-cli render out/invoice.docx /tmp/p1.png --page 1     # then look at it
```

`data.json` is `{"client": "ACME Robotics Ltd.", "total": "€4,800.00", …}`. The script:
- refuses to start if the template has a placeholder the data lacks, unless `--allow-missing`;
- replaces in every story;
- keeps the run formatting: a bold `{{client}}` gives a bold value;
- exits 1 if anything is left.

The manual equivalent, per story:

```json
{"file": "/abs/template.docx",
 "commands": [
   "caret.docStart",
   {"command": "edit.replaceAll", "params": {"text": "{{client}}", "with": "ACME", "matchCase": true, "special": false}},
   {"command": "caret.set", "params": {"pos": {"story": {"part": 1}, "path": [0], "off": 0}}},
   {"command": "edit.replaceAll", "params": {"text": "{{client}}", "with": "ACME", "matchCase": true, "special": false}}],
 "save": ["/abs/out.docx", "/abs/out.pdf"]}
```

Part ids come from `wordcraft-cli inspect template.docx`, in `parts`, for headers,
footers and footnotes.

**One document per CSV row:** loop `wc_fill.py` with one JSON per row, or use mail merge
(below).

## Review pass: tracked changes and comments by a named author

```json
{"file": "contract.docx",
 "commands": [
   {"command": "review.trackChanges", "params": {"value": true}},
   {"command": "select.text", "params": {"text": "Payment terms"}},
   "caret.end", "text.newParagraph",
   {"command": "text.insert", "params": {"text": "Invoices are payable within 30 days of receipt."}},
   {"command": "select.text", "params": {"text": "late fee"}},
   {"command": "review.newComment", "params": {"text": "Is 30 days agreed with finance?"}}],
 "save": ["out/contract-review.docx"]}
```

```sh
wordcraft-cli run --script review.json --author "Claude"
wordcraft-cli convert out/contract-review.docx out/contract-review-markup.pdf --markup
python3 $S/wc_verify.py doc out/contract-review.docx --author Claude --style "Heading 2=Payment terms"
```

- `text.newParagraph` after a heading gives a paragraph in the heading's *next* style, Normal for built-in headings. Check it in the read-back.
- **Deleting as a tracked change:** select the text, then `text.delete`. **Replacing:** select it, then `text.insert`. With tracking on, both become `w:del` (+ `w:ins`) by the author.
- `select.text` picks the first match. Use `"occurrence": n` for a later one, and make the search text unique.

## Markdown to .docx with a filled TOC

```sh
python3 $S/wc_batch.py notes/ out/docx --to docx --glob '*.md' --toc
```

It runs one script per file:

```json
{"file": "/abs/notes/kickoff.md",
 "commands": ["caret.docStart", "text.newParagraph", "caret.up",
   {"command": "para.style", "params": {"style": "Normal"}},
   {"command": "references.toc", "params": {"levels": 3}},
   {"command": "references.updateFields", "params": {"all": true}}],
 "save": ["/abs/out/docx/kickoff.docx"]}
```

- The result is TOCHeading "Contents", then TOC1/TOC2 entries, then one empty Normal paragraph, then the first Heading1.
- The empty paragraph sits *between* the TOC and the content, which is harmless. Don't try to delete the paragraph *above* the TOC (see gotchas).
- `"title"` renames "Contents".

## Convert a folder

```sh
python3 $S/wc_batch.py old-docs/ converted/ --to docx,pdf --glob '*.doc'
python3 $S/wc_batch.py reviewed/ pdfs/ --to pdf --markup            # comments in the margin
python3 $S/wc_batch.py reports/ refreshed/ --to docx --update-fields
```

- A single file is `wordcraft-cli convert IN OUT`.
- `.doc` is read-only, so converting a .doc means a new .docx next to it.
- `wc_verify.py files converted --ext pdf --count N` confirms the outputs.

## Mail merge from CSV

```json
{"file": "letter.docx",
 "commands": [
   {"command": "mailings.start", "params": {"kind": "letters"}},
   {"command": "mailings.recipients", "params": {"path": "members.csv"}},
   {"command": "mailings.finish", "params": {"path": "out/merged.docx"}}],
 "save": []}
```

- When the letter has no merge fields yet, add them first: `select.text` on the placeholder text, then `mailings.insertField {"field": "name"}`.
- `finish` writes all records into one document. For one file per record, pass `{"path": "out/rec-N.docx", "from": N, "to": N}` in a loop of runs.
- Verified result: "Dear Ada from London / Dear Bob from Paris".

## Build a document from an outline

```json
{"commands": [
   {"command": "styles.modify", "params": {"style": "Normal", "chr": {"font": "Georgia", "size": 11}}},
   {"command": "para.style", "params": {"style": "Title"}},
   {"command": "text.insert", "params": {"text": "Project proposal"}}, "text.newParagraph",
   {"command": "para.style", "params": {"style": "Heading 1"}},
   {"command": "text.insert", "params": {"text": "Budget"}}, "text.newParagraph",
   {"command": "insert.table", "params": {"rows": 3, "cols": 2}},
   {"command": "text.insert", "params": {"text": "Item"}}, "text.tab",
   {"command": "text.insert", "params": {"text": "Cost"}}, "text.tab",
   {"command": "text.insert", "params": {"text": "Design"}}, "text.tab",
   {"command": "text.insert", "params": {"text": "€2,000"}},
   "caret.docEnd",
   {"command": "insert.footer", "params": {"preset": "pageNumber"}}],
 "save": ["proposal.docx", "proposal.pdf"]}
```

- For long text, writing Markdown and converting it is faster: `wordcraft-cli convert draft.md draft.docx`. Then run a styling script on the .docx.
- Set a paragraph's style **before** typing, or select the paragraph and set it after.

## Live app (the user watches the edits)

```sh
python3 $S/wc_live.py start report.docx          # new instance, control port, prints "connect"
echo '[{"select":"Q3"},{"cmd":"format.bold"},{"save":"/abs/report.docx"}]' \
  | python3 $S/wc_session.py - --connect 127.0.0.1:PORT --author "Claude"
python3 $S/wc_live.py stop                       # quits only that instance
```
