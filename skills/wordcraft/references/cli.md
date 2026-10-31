# wordcraft-cli reference (0.13.2)

All behaviour below was verified against wordcraft-cli 0.13.2 on macOS. `-h` on any
subcommand prints this same global help; there is no per-command help and no `describe`.

## Subcommands

| Command | What it does |
|---|---|
| `convert IN OUT [--markup] [--update-fields] [--format wordml2003\|flatopc]` | Format conversion by extension. `--update-fields` refreshes unlocked fields first. `--markup` adds comments beside each page and revision marks in pdf/png, or a comment list in html/md/txt |
| `info FILE` | JSON: pages, words, paragraphs, sections, comments, trackChanges, properties |
| `text FILE` | Plain body text. Tracked deletions are left out; headers and footers are not included |
| `inspect FILE` | Structure JSON (below) |
| `render FILE OUT.png [--page N] [--scale S]` | One page to PNG. Pages are 1-based; scale is px per pt (default 2) |
| `run [--file F \| --template T] [--script FILE\|-] --cmd 'id={json}' … [--save OUT] [--print] [--author NAME]` | Runs commands headless, then saves. `--print` prints each command's result |
| `commands [--json]` | The registry (648 ids). Filter it with `scripts/wc_commands.py` |
| `parity [--markdown]` | Feature-catalogue coverage |
| `mcp [--connect HOST:PORT \| --author NAME] [--automation-read-root DIR] [--automation-write-root DIR]` | MCP server on stdio, headless or bridged to the app |
| `zotero <command> FILE …` | Zotero citation commands (needs Zotero running) |

Password-protected files take `--password-file PATH` or `WORDCRAFT_PASSWORD`. A
`--password` given on the command line is visible to other processes.

## Formats

- **Read:** docx, doc, odt, rtf, html, md, tex, txt, json, xml (Flat OPC / Word 2003 XML).
- **Write:** docx, pdf, odt, rtf, html, md, tex, txt, json, png, xml.
- **Not supported:** `.doc` output and reading PDF.
- **Markdown in:** `#`→Heading1, `##`→Heading2, `###`→Heading3, pipe tables → `TableGrid`, lists, `**bold**` and `*italic*` as run props.

## `run`

- `--cmd 'id={json}'` can repeat. An id with no params is written `--cmd caret.docEnd`.
- `--save` can be given **once**. With two flags, only the first file is written. Use a script to save several formats.
- `--script FILE` runs first, then any `--cmd`:

```json
{"file": "in.docx",            // or "template": "t.dotx" (new untitled doc from it); neither = blank
 "commands": [{"command": "id", "params": {}}, "id-without-params"],
 "save": ["out.docx", "out.pdf"]}
```

- Relative paths in the script resolve against the script file's folder. With `--script -` (stdin), use absolute paths.
- `--author NAME` sets the author of new tracked changes and comments. Without it they are "WordCraft User". The `file.setAuthor` command does the same.
- `file.new` and `file.open` open another document and make it the active one; later commands and the `save` list act on the active document. `view.switchWindows` lists the open documents and, with `{"id": N}`, activates one.
- An unknown id stops the run: `unknown command `font.bold``. The error names the id.

## `inspect` JSON

```text
blocks[]      {index, type: paragraph|table, style, text, len,
               runs[] {start, end (UTF-8 byte offsets), props {bold, italic, ins: n, del: n, …}},
               objects[] {type: field (instr, result, locked) | commentStart/End (id) | bookmarkStart/End (name) | …},
               table: rows, cols, cells [[text]]}
parts[]       {id, kind: header|footer|comment|footnote|…, text}
sections[]    {endBlock, props {pageW, pageH, margins…, headers {default, even, first: part id}, footers {…}}}
comments, pages, words, trackChanges, properties, selection
```

- Run offsets are bytes. Convert with `len(text[:i].encode())`.
- Revisions and comments carry **no author** here. Read the authors with `scripts/wc_verify.py doc`, which parses the package XML, or with `run --file F --cmd review.changes --cmd review.comments --print`.

## Story positions

`Pos = {"story": "body" | {"part": ID}, "path": [block, (row, cell, block)…], "off": byte}`.
Part ids come from `inspect.parts` or `sections[].props.headers`. For example,
`caret.set {"pos": {"story": {"part": 1}, "path": [0], "off": 0}}` puts the caret in
header part 1. Story-scoped commands (`edit.replaceAll`, `references.updateFields`
without `all`) then act on that story.

## MCP server (`wordcraft-cli mcp`)

| Tool | Arguments |
|---|---|
| `list_commands` | `query` filter |
| `execute` | `command`, `params` |
| `batch` | `commands: [{command, params}]`, `keepGoing` |
| `new_document` | `template: blank\|sample\|letter\|resume\|report` |
| `open_document` | `path`, `password` |
| `save_document` | `path` |
| `type_text` | `text` |
| `select_text` | `text`, `occurrence` (1-based) |
| `get_text` | none |
| `inspect_document` | none |
| `render_page` | `page`, `scale` |
| `screenshot`, `click`, `key`, `ui_inspect` | desktop app only (`--connect`) |

- Headless, file access is confined to `--automation-read-root` / `--automation-write-root`. A root left out grants no access, and a path outside a root is refused with `automation path rejected`.
- `scripts/wc_session.py` is a ready client.
- With `--connect`, the roots flags are an error. The app's own file access applies.
