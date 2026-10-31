---
name: deckcraft
description: 'Automate DeckCraft, the Keynote/PowerPoint-style presentation app, headless with deckcraft-cli: build decks from a Markdown outline (theme, title slide, bullet slides, image slides, presenter notes); edit existing .deckcraft or .pptx files (titles, body text, find and replace, delete, move, duplicate or hide slides, swap pictures, change layouts or theme); export PDF (slides or notes pages), PPTX, PNG/JPG and animated GIF; batch-convert folders of decks; render slides for a visual check, with every result read back. Use when the user mentions DeckCraft, deckcraft-cli or a .deckcraft file, or wants slides made or changed with DeckCraft: "turn this outline into a DeckCraft deck", "delete slide 4 and move the last slide to 2 in this pptx with DeckCraft", "convert these decks to PDF with DeckCraft", "render slide 3 as PNG". Not for Apple Keynote (keynote), LibreOffice Impress (libreoffice), Word documents (wordcraft), page layout (designcraft), or editing PDFs (pdfcraft).'
summary: "automate DeckCraft headless with deckcraft-cli — decks from a Markdown outline with theme, layouts, images and presenter notes, title, text, picture and slide-order edits in .deckcraft or .pptx, PDF/PPTX/PNG/GIF export and folder conversion, info read-back and rendered slides verified"
category: office
compatibility: "Built for DeckCraft 0.13.1 and deckcraft-cli 0.13.1 on macOS, Python 3.9+; poppler (pdfinfo, pdftotext) and ImageMagick for export checks; pre-1.0, so command ids may change."
risk: medium
tags: [deckcraft, presentations, slides, pptx, keynote-style, powerpoint-style, headless]
license: GPL-3.0-only
metadata:
  version: "1.0.4"
  author: "Tamás Jablonkai"
---

# DeckCraft via deckcraft-cli

DeckCraft is a Keynote/PowerPoint-style presentation app. A presentation (`.deckcraft`,
or `.pptx` read and written natively) has slides on layouts from a slide master, a theme
(colours and fonts), placeholders, pictures, notes, sections and transitions. Every menu
item is a command in one registry (330 in 0.13.1); the same commands run from
`deckcraft-cli run`, from a headless MCP session (`deckcraft-cli mcp`) and in the app.
This skill drives them **headless** — no window opens — and checks every result by
reading the file or the export back. Verified against **DeckCraft 0.13.1** and
**deckcraft-cli 0.13.1** on macOS; the software is pre-1.0, so if a pinned id fails,
look it up rather than guessing.

```sh
command -v deckcraft-cli || ls ~/.local/bin/deckcraft-cli
deckcraft-cli --version
```

## Pick the route

| Task | Route |
|---|---|
| New deck from a Markdown outline (title slide, bullets, images, notes, theme) | `scripts/dk_build.py outline.md --out deck.deckcraft [--pptx …] [--pdf …]` |
| Edit a copy: titles, text, replace, delete/move/duplicate/hide slides, pictures, layout, theme | `scripts/dk_edit.py IN OUT edits.json [--pdf …]` |
| One file or a folder → PDF, PPTX, PNG/JPG thumbnails, GIF, outline | `scripts/dk_convert.py IN OUT_DIR --to pdf,png [--thumb-width 480]` |
| What a deck holds: titles, layouts, notes, pictures, text per slide | `scripts/dk_verify.py deck F` (no flags = summary) |
| A slide as PNG | `deckcraft-cli render F --slide N-1 [--scale S] out.png` (`--all DIR` for every slide) |
| Notes pages or handouts PDF | `run --in F --export out.pdf --export-params '{"layout":"notes"}'` |
| Anything else (tables, charts, shapes, transitions, sections…) | `run --in F --cmd ID=JSON … --save OUT` or `dk_edit.py` with `{"op":"cmd"}` ([recipes](references/recipes.md)) |
| Find a command and its params | `scripts/dk_commands.py WORD…` / `--id ID` |

## Scripts

`S=<this skill>/scripts`; call as `python3 $S/<script>`. Python 3.9+, standard library
only, each with a full `--help`. They refuse to overwrite outputs without `--overwrite`.

- **`dk_build.py OUTLINE --out F [--theme T] [--pptx P] [--pdf P] [--notes-pdf P] [--png-dir D]`**:
  the first `#` is the title slide (the line under it is the subtitle), each `##` a slide,
  later `#` section headers; `-`/`*`/`1.` bullets with two-space nesting; Markdown
  image lines (`![alt]` + path in parentheses, relative to the outline) become pictures
  fitted under the title (Two Content when the slide also has bullets);
  `Notes: …` or `> …` lines are presenter notes. Removes the starter slide, rejects an
  unknown theme, saves, exports, then reads every output back against the outline and
  exits 1 on any mismatch. `--dry-run` shows the parsed slides.
- **`dk_edit.py IN OUT EDITS`**: JSON edit list (file or inline). Slide numbers are
  **1-based and sequential** — each edit sees the deck as the previous one left it, so
  "delete slide 4, then move the last slide to 2" is `[{"op":"delete","slide":4},
  {"op":"move","slide":"last","to":2}]`. Ops: `title`, `subtitle`, `body`, `replace`,
  `delete`, `move`, `duplicate`, `new`, `notes`, `picture` (swap in place), `add-picture`,
  `layout`, `hide`, `theme`, `cmd` (any command). Shape ids are resolved by
  `slide.inspect` in the same session. Positions named together against the *original*
  deck ("delete 3 and 5") go in one list: `{"op":"delete","slide":[3,5]}`. OUT must
  differ from IN; `--expect-titles` fails the run if the saved order is wrong;
  `--pdf P --include-hidden` keeps hidden slides in the PDF.
- **`dk_convert.py IN OUT_DIR --to pdf,pptx,png,jpg,gif,md`**: per deck `NAME.<ext>`;
  `png` is slide 1 (`--all-slides` → `NAME/slide-01.png …`), sized by `--thumb-width` or
  `--scale`. Checks PDF pages against the slide count, hashes inputs before and after.
- **`dk_verify.py`** prints JSON and exits 1 on any failed check:
  - `deck F --slides 6 --titles A B … --layout 1="Title Slide" --notes 2="…" --only-notes 2 4 --text 3="Fuel" --pictures 5=1 --theme Harbor --no-empty`
  - `pdf F.pdf --pages 5 --size 960x540 --order "Q3 2026 Update" Questions … --text 2="…"`
  - `png F.png --width 480 --not-blank` · `hash PATH… --save m.json` / `--compare m.json`
- **`dk_commands.py WORD…`** (`--prefix slide.`, `--id file.export`): filtered registry lookup.

## Workflow

1. **Inspect first.** `dk_verify.py deck F` shows every slide's title, layout, notes and
   text. Map what the user says ("slide 4", "the last slide") onto that list before
   editing. Look up any command you haven't used this session with `dk_commands.py`.
2. **Never touch the originals.** Write to a new path (`dk_edit.py IN OUT`, `run --in IN
   --save OUT`); snapshot inputs with `dk_verify.py hash … --save` when nothing else does.
3. **Do the work** with the route from the table.
4. **Read back** with `dk_verify.py deck` (count, order, titles, notes, layouts, theme)
   and `dk_verify.py pdf` (pages and order). The scripts do this for you and say so.
5. **Look at it.** Render the slides that matter (`render F --all DIR`, or `--png-dir`)
   and view them: overflowing bullets, a picture over the title, or the wrong theme only
   show up there.
6. **Report** outputs, the checks that passed, and anything you could not verify.

## The traps that cost the most (details in [gotchas.md](references/gotchas.md))

- **A new presentation already has one empty title slide**, and `slide.fromOutline`
  inserts after it, so a hand-built deck ends up one slide too long. Delete index 0
  first (`slide.delete {"index":0}` on the only slide is fine) or fill it.
- **`slide.fromOutline {markdown:true}` makes every heading a Title and Content slide**
  — no title slide, no notes, no pictures. `dk_build.py` does what it doesn't.
- **Typos fail silently.** Unknown parameters are ignored (`"titel"` → an untitled
  slide) and an unknown theme name falls back to the default. Check names with
  `describe` / `design.themes` and read back.
- **Indices are 0-based in commands and `render --slide`; people count from 1.**
  `file.export {"slides": [1,2]}` is 0-based, but the range string `"slides": "1-2"` is
  1-based. `slide.new`/`slide.fromOutline` insert after the *current* slide, which they
  don't always move — pass `at`.
- **Shape ids exist only on the current slide.** `text.set {id}` needs `slide.go` first,
  and ids must come from `slide.inspect`, never be guessed.
- **`pictureWithCaption`'s `body` lands in the picture placeholder**, and
  `insert.picture` never fills a placeholder — it adds a free picture. Use Title Only
  plus `insert.picture {rect}` (what `dk_build.py` does).
- **Hidden slides are left out of PDFs** unless `includeHidden: true`.
- **`mcp` takes one read root and one write root** (a second `--automation-read-root`
  is an error); the scripts use the folders' common parent.
- **One failing `--cmd` aborts the whole `run`** and nothing is saved — good for safety,
  but check the message, fix the one command, and rerun the batch.

## References

- [references/cli.md](references/cli.md): subcommands, `run` ordering and `--print`, export params, render, MCP tools.
- [references/commands.md](references/commands.md): pinned 0.13.1 ids by task, with key params.
- [references/recipes.md](references/recipes.md): outline deck, open-edit-export, folder conversion, notes PDF, GIF, tables and charts.
- [references/gotchas.md](references/gotchas.md): silent failures and surprises.
- [references/security.md](references/security.md): file roots, and why there is no live-app bridge.
