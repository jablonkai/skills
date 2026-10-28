# Gotchas (WordCraft 0.12.0)

Each of these was hit while building or testing this skill. Most fail **silently**: the
command succeeds and the document is wrong.

## Saving
- **`run --save A --save B` writes only A.** No error, and the second file is simply
  missing. Use a script: `"save": ["out.docx", "out.pdf"]`. The extension picks the
  format.
- **Relative paths in a `--script` file resolve against the script's folder**, not the
  shell's cwd. A script in `/tmp` saving `out.docx` writes `/tmp/out.docx`. Use absolute
  paths, or keep the script next to the files.
- `.doc` and PDF cannot be written back as `.doc` or opened for editing. They convert
  to something else.

## Find and replace
- **`edit.replaceAll` acts on one story**: the body by default, or the one the caret
  is in. Header and footer placeholders survive a body replace and show on every
  printed page. Put the caret in each part
  (`caret.set {"pos": {"story": {"part": ID}, "path": [0], "off": 0}}`), or use
  `wc_fill.py`. `insert.editHeader {"page": n}` also works, but **creates** a header
  when that page has none.
- **Special codes are on by default** in `with`:
  - `^p` becomes a paragraph break;
  - `^&` re-inserts the found text (so `{{item}}` comes back);
  - `^^` becomes `^`.

  Literal data needs `"special": false`.
- Placeholders split across differently formatted runs (`{{na` plain + `me}}` italic)
  **are** found. The replacement takes the formatting of the match's first character.
- Use `"matchCase": true`. Replace longer keys first when one key is a prefix of another
  inside the braces. `wc_fill.py` sorts by length.

## Table of contents and fields
- **`references.toc` at `caret.docStart` leaves an empty Heading1-styled paragraph
  above the TOC.** A Heading1 with no text can still show in navigation.
- **Deleting that paragraph (`caret.docStart` + `text.delete`) destroys the TOC.** The
  TOC heading merges into Heading1, the field disappears, and "Contents" lists itself.
  Instead, open a Normal paragraph first: `caret.docStart`, `text.newParagraph`,
  `caret.up`, `para.style Normal`, then `references.toc`.
- A new TOC, or one after edits, needs `references.updateFields {"all": true}` (or
  `convert --update-fields`). Otherwise it shows stale or no entries. `updateFields`
  without `all` updates only the caret's story.

## Review
- **`inspect` shows revisions and comments without their authors**: runs carry
  `ins: n`/`del: n` and comments are `parts` of kind `comment`. Verify authors with
  `wc_verify.py doc FILE --author NAME`, which reads `w:author` from the package, or ask
  the engine: `wordcraft-cli run --file F --cmd review.changes --cmd review.comments --print`
  lists every revision and comment with author, date, text and position.
- Without `--author` (or `file.setAuthor`) every mark is by "WordCraft User".
- Track changes must be **on before** the edit. Turning it on afterwards marks nothing.
- `text.newParagraph` under tracking adds an empty `w:ins` for the paragraph mark, plus
  one with the text. Both are by the author, as Word does it.
- A plain PDF export drops comments and revision marks. Use `--markup` or
  `file.printMarkup {"value": true}`.
- `render` rejects a `.pdf` input, so you can't look at the markup PDF directly. Preview
  the same markup with `convert OUT.docx markup.png --markup`. The page comes out wider
  to make room for the comment margin.

## Commands
- Ids are not always the obvious ones: `format.bold` (not `font.bold`),
  `para.style {"style": "Heading 1"}`. An unknown id stops `run` with
  ``unknown command `x` ``. Check with `wc_commands.py`.
- `wordcraft-cli <sub> --help` prints the global help only. Command params are in the
  registry (`wc_commands.py --id ID`), not in the CLI help.
- Run offsets in `inspect` are UTF-8 **bytes**: `€` counts as 3.

## Environment
- Paper size follows the locale (A4 vs Letter), and so do page counts. Set
  `WORDCRAFT_REGION=en-US` (or the user's region) for reproducible output.
- `/Applications/WordCraft.app/Contents/MacOS/WordCraft --help` is safe (it prints
  usage), but running the binary with anything else opens a window. Headless work needs
  only `wordcraft-cli`.
