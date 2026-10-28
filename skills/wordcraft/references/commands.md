# Command ids by task (pinned to WordCraft 0.12.0)

These are the ids this skill uses, checked against the 0.12.0 registry. Look anything
else up rather than guessing. Names follow the ribbon, but not always the obvious way:
it is `format.bold`, not `font.bold`.

```sh
python3 $S/wc_commands.py comment            # id, label or ribbon location contains "comment"
python3 $S/wc_commands.py --prefix references.
python3 $S/wc_commands.py --id edit.replaceAll   # full params
```

In a session, `list_commands {"query": "…"}` does the same. In 0.12.0 the largest
namespaces are `para`, `table`, `insert`, `format`, `view`, `review`, `edit`, `file`,
`outline`, `references`, `text` and `mailings`.

## Text and caret

| Id | Params |
|---|---|
| `text.insert` | `{"text"}`. Types at the caret and replaces the selection |
| `text.newParagraph`, `text.lineBreak`, `text.pageBreak`, `text.tab` | none |
| `caret.docStart` / `caret.docEnd` / `caret.home` / `caret.end` / `caret.up` / `caret.down` | `{"extend"?}` |
| `caret.set` | `{"pos": Pos}`. Puts the caret anywhere, including header/footer parts |
| `select.text` | `{"text", "occurrence"?}`. Selects the n-th match (1-based) |
| `select.all`, `select.paragraph`, `select.range {"anchor", "focus"}` | |
| `document.setText` | `{"text"}`. Replaces the whole body |

## Find and replace

| Id | Params |
|---|---|
| `edit.replaceAll` | `{"text", "with", "matchCase"?, "wholeWord"?, "wildcards"?, "regex"?, "special"?}`. Acts on the caret's story only. `special` defaults to true, so `^p ^t ^&` in `with` are expanded. Pass `false` for literal values |
| `edit.find` / `edit.findNext` | same options; selects the match |

## Formatting and styles

| Id | Params |
|---|---|
| `format.bold`, `format.italic` | `{"value"?: bool}`. Omit to toggle |
| `para.style` | `{"style": "Heading 1"}`. Takes a name or id (`Heading1`) |
| `para.heading1..3` | none |
| `styles.apply` | `{"style"}` |
| `styles.modify` | `{"style", "chr"?: {"font", "size", …}, "para"?: {…}, "name"?, "next"?}`. Verified: `{"style": "Normal", "chr": {"font": "Georgia", "size": 12}}` |
| `styles.create` | `{"name", "basedOn"?, "fromSelection"?}` |
| `styles.list` | none |
| `styles.copyFrom` | `{"path", "styles": [names]}` |
| `insert.table` | `{"rows", "cols", "style"?}`. The caret lands in cell (0,0); `text.tab` moves to the next cell |

## Headers, footers and sections

| Id | Params |
|---|---|
| `insert.header` / `insert.footer` | `{"text"?, "preset"?}`. Replaces the header or footer content |
| `insert.editHeader` / `insert.editFooter` | `{"page"?}`. Moves into the header that page shows, **creating one if it has none** |
| `insert.closeHeader` | back to the body |
| `insert.pageField` | PAGE field at the caret |

## Review

| Id | Params |
|---|---|
| `review.trackChanges` | `{"value"?: bool}` |
| `file.setAuthor` | `{"name"}`. The same as `run --author` |
| `review.newComment` | `{"text"}`. Anchored on the current selection |
| `review.editComment` / `review.deleteComment` / `review.resolveComment` | `{"id", …}` |
| `review.comments` | none. Returns `[{id, author, date, text, anchor, resolved, parent}]` |
| `review.changes` | none. Returns `[{kind: insert\|delete\|…, author, date, text, start, end}]` |
| accept and reject | `wc_commands.py accept` / `reject` |
| `file.printMarkup` | `{"value"?: bool}`. Comments and revisions in the next pdf/png save |

## Fields and references

| Id | Params |
|---|---|
| `references.toc` | `{"levels"?, "title"?, "pageNumbers"?, "rightAlign"?, "tabLeader"?}` |
| `references.updateToc` | none |
| `references.updateFields` | `{"all"?: bool}`. `all` covers the body plus every header, footer, note and text box |
| `insert.field` | `{"instr", "result"?}`, e.g. `{"instr": "DATE \\@ \"d MMMM yyyy\""}` |
| `fields.lock` / `fields.unlock` / `fields.unlink` | none |

## Mail merge

| Id | Params |
|---|---|
| `mailings.start` | `{"kind": "letters"}` |
| `mailings.recipients` | `{"path": "list.csv"}`. Also takes .tsv, .xlsx and .ods |
| `mailings.insertField` | `{"field": "name"}` |
| `mailings.filterRecipients` / `mailings.sortRecipients` | |
| `mailings.finish` | `{"path", "records"?: "all\|current", "from"?, "to"?}`. Records are 1-based |

## File

| Id | Params |
|---|---|
| `file.new` | `{"template"?: "blank\|sample\|letter\|resume\|report"}` |
| `file.newFromTemplate` | `{"path"}` |
| `file.open` | `{"path"}` |
| `file.save` / `file.saveAs` | `{"path", "markup"?, "format"?}` |
| `file.inspect` | `{"remove"?: ["comments", "revisions", "properties", "hidden", "headers"]}`. Document Inspector |
