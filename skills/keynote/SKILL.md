---
name: keynote
description: 'Automate Apple Keynote on macOS via its AppleScript dictionary (osascript) — build a deck from a Markdown/JSON outline with a theme, layouts, bullets, images and presenter notes; edit a copy of a .key deck (replace {{placeholder}} text in titles, bodies, text boxes, tables and notes without losing formatting; skip, delete or reorder slides); export or batch-convert .key files to PDF (with or without notes), PPTX, slide images or movie; verify by reading slides back. Use whenever the user mentions Keynote or a .key file: "turn this outline into a Keynote deck", "export deck.key to PDF with speaker notes", "convert these Keynote files to PowerPoint", "fill the {{client}} placeholders in my Keynote template", "skip the appendix slides", or Hungarian "exportáld a Keynote prezentációt PDF-be". Not for .pptx decks made or edited without Keynote (use pptx), generic PDF work (use pdf), slides to Markdown (use markitdown), or Pages and Numbers documents.'
summary: "automate Apple Keynote via AppleScript/JXA — build decks from an outline with themes, layouts and presenter notes, edit .key text without losing formatting, skip or reorder slides, and PDF/PPTX/image export or batch conversion"
category: office
risk: low
tags:
    - keynote
    - iwork
    - applescript
    - presentation
    - pptx
    - pdf
metadata:
  version: "1.0.0"
---

# Keynote Automation

Apple Keynote is driven through its **AppleScript dictionary via `osascript`**: each
script call opens the decks it needs, works, and closes them again. There is no
bridge or listener; macOS Automation consent is the only gate. Verified against
**Keynote Creator Studio 15.4** (bundle id `com.apple.Keynote`) on macOS 27.

Everything goes through the scripts below. They encode workarounds for dictionary
features that look usable but are broken or localized (see Pitfalls), so reach for
raw AppleScript only for what they don't cover
([references/recipes.md](references/recipes.md)).

| Script | Does |
|---|---|
| `bash scripts/keynote.sh --check` | app, version, Automation permission, open-deck count. Run first. |
| `bash scripts/keynote.sh --themes [RE]` | theme **id** ⇥ localized name |
| `bash scripts/keynote.sh --layouts THEME` | layout index ⇥ English name ⇥ localized name ⇥ placeholders |
| `python3 scripts/keynote-build.py OUTLINE --out D.key ...` | new deck from a Markdown/JSON outline, optional exports |
| `python3 scripts/keynote-fill.py SRC.key --out D.key ...` | copy a deck, replace tokens, skip/delete/reorder slides, export |
| `python3 scripts/keynote-export.py SRC... --to FMT` | one file or folders (`-r`) to pdf, pptx, png, jpeg, tiff, m4v |
| `python3 scripts/keynote-verify.py FILE... ...` | read back .key / .pptx / .pdf / image folder and assert |
| `bash scripts/keynote.sh --dialog` | is a modal Keynote alert blocking scripting? screenshots it |
| `bash scripts/keynote.sh --close-leftovers` | close decks a killed run left open (stop path) |

All Python is standard library only and runs on the system `python3`. Every script
prints JSON lines and exits non-zero on failure. Read the JSON rather than assuming
success.

## Workflow

1. `bash scripts/keynote.sh --check`. `automation: DENIED` → ask the user to allow the
   terminal in System Settings ▸ Privacy & Security ▸ Automation ▸ Keynote.
2. Inspect a deck you did not write: `python3 scripts/keynote-verify.py deck.key --show`
   prints per slide the layout (English name), title, body, notes, skipped flag, image
   count and all other text Keynote can reach. Tokens must appear there to be replaceable.
3. Build, fill or export.
4. **Verify independently** with `keynote-verify.py`: `--slides N`, `--title N=TEXT`,
   `--notes N=TEXT`, `--contains`, `--no-tokens`, `--skipped 3,7` on the `.key` and on
   each export. For looks, export PNGs (`keynote-export.py deck.key --to png --out
   /tmp/look`) and Read one or two of them.

## Build a deck from an outline

```bash
S=scripts
python3 $S/keynote-build.py talk.md --out talk.key --export talk.pdf --export talk.pptx
python3 $S/keynote-build.py talk.md --out talk.key --theme Application/20_BasicBlack/Standard
python3 $S/keynote-build.py talk.md --out talk.key --dry-run   # layouts chosen, warnings
python3 $S/keynote-build.py talk.md --out talk.key --export talk-notes.pdf --notes
```

Markdown outline, one slide per heading:

```markdown
# Deck title              ← first H1: title slide; plain lines below = subtitle
Subtitle line
Notes: Presenter notes run from here to the next heading,
over several lines.

## Slide title            ← content slide (## or deeper)
- Bullet one              ← -, *, + or 1. ; nested bullets are flattened (warning)
- Bullet two
![](images/chart.png)     ← relative to the outline; fills the photo placeholder
<!-- skip -->             ← mark skipped
<!-- layout: quote -->    ← override: role, English/localized name, or index

# Part two                ← a later H1: section slide
```

JSON works too: `{"theme": "...", "slides": [{"title", "body": str|[str], "notes",
"image", "layout", "skip", "section": true}]}`.

- Layouts are chosen by **role** and resolved per theme, in any UI language: `title`,
  `section`, `bullets`, `bullets-photo`, `title-photo`, `photo`, `title-only`,
  `statement`, `quote`, `agenda`, `blank`. Themes differ (Gradient has no Section;
  the builder falls back to Title - Center), so check `--dry-run` or `--layouts`.
- Default theme: Basic White (`Application/21_BasicWhite/Standard`). `--theme` takes an
  id or a (localized) name. Never pass English theme names to raw AppleScript.
- A slide with a picture gets a layout with a photo placeholder; the picture fills its
  frame (cropped to it). An explicit layout without one gets the picture in the right half.
- Nested bullets can't be indented by script. They are flattened and reported. Tell
  the user if the hierarchy matters (Tab in the Keynote UI).
- Existing outputs are refused unless `--force`.

## Edit a deck: placeholders and slides

```bash
python3 $S/keynote-fill.py template.key --out acme.key \
  --set client='Kovács és Társa' --set date='2026. október 1.' --export acme.pdf
python3 $S/keynote-fill.py template.key --out acme.key --data values.json
python3 $S/keynote-fill.py talk.key --out short.key --skip title:Appendix --delete 12,13 \
  --move 9=2 --allow-leftover
python3 $S/keynote-fill.py talk.key --out reordered.key --order 1,3,2,4,5 --allow-leftover
```

- Tokens (`{{key}}` by default, `--token '%s'` for literal text) are replaced in
  titles, bodies, text boxes, shapes, table cells, grouped objects **and presenter
  notes**, keeping each token's own character style (a bold `{{client}}` gives a bold
  name). Matching is exact and case-sensitive.
- An **unreplaced `{{` anywhere fails the run** (`"leftover"`), so a misspelt key is
  caught. `not_found` lists keys that matched nothing. Pass `--allow-leftover` when
  `{{` is meant to stay (or no tokens are being filled).
- Slide numbers in `--skip/--unskip/--delete/--order/--move` always mean the slide's
  number **in the source deck**; `title:TEXT` picks by exact title. `--order` lists
  every remaining slide.
- The source is copied, never edited. The user's *unsaved* changes in an open copy
  aren't included, and a deck open in Keynote is refused by verify/export; say so.
- Long values can overflow a fixed text box. Verify with `--contains` and look at a
  PNG of the slide.

## Export and convert

```bash
python3 $S/keynote-export.py talk.key --to pdf                        # next to source
python3 $S/keynote-export.py talk.key --out 'Talk (notes).pdf' --notes
python3 $S/keynote-export.py ~/Decks --to pptx --out-dir ~/Decks/pptx -r   # mirrors subfolders
python3 $S/keynote-export.py talk.key --to png --out /tmp/talk-png         # folder of PNGs
python3 $S/keynote-export.py talk.key --to m4v --movie-format 1080p
python3 $S/keynote-verify.py ~/Decks/pptx/*.pptx --contains 'expected text'
```

- Formats: `pdf`, `pptx`, `png`/`jpeg`/`tiff` (a folder of `NAME.001.png` …), `m4v`.
- **Skipped slides:** PDF leaves them out unless `--include-skipped`; images always
  leave them out; PPTX always keeps them, hidden. Each result line carries the deck's
  `slides` and `skipped_slides`, so check the output against them and tell the user
  which rule applied.
- PDF options: `--notes` (slide + notes per page), `--handouts`, `--slide-numbers`,
  `--all-stages`, `--pdf-quality`, `--password` (PDF/PPTX; verify can't read an
  encrypted PDF).
- Existing outputs are skipped unless `--force`. Sources are closed without saving.

## Pitfalls (all measured on 15.4)

- **A modal alert blocks all scripting.** Examples are "can't be opened", a password
  prompt, or missing fonts. Every later call times out (-1712). The scripts then report
  it and save a screenshot of the alert (`keynote.sh --dialog`). Read the screenshot and
  ask the user to click it away. There is no scripted way to dismiss it without
  Accessibility access, so don't try.
- **Open files as an alias** in raw AppleScript: `open (POSIX file p as alias)`. A bare
  `POSIX file` on a file Keynote didn't create returns `missing value` and raises an
  alert (sandbox), which then blocks Keynote.
- **`make new document` leaves an "Untitled" deck in iCloud Drive's Keynote folder**
  unless you `save d in POSIX file p` right after `make`. Saving later is too late.
- **Themes and layouts are addressed by id and index**, never by English name: both
  names are localized, and layout sets differ between themes.
- **`set characters i thru j to v` is broken** (writes v into every character). Edit
  text with `keynote-fill`, or see `replaceIn` in `scripts/keynote_ops.applescript`.
- **`make image slides` adds every picture twice.** Use the outline builder, or the
  recipe in references.
- **Never open a deck the user has open.** Their unsaved edits and yours would
  collide; the scripts refuse.

More pitfalls, and why the scripts do what they do:
[references/gotchas.md](references/gotchas.md). Dictionary reference (classes, export
options, enumerations): [references/dictionary.md](references/dictionary.md).

## Safety

- The scripts write new files only. Sources and templates are copied, never modified,
  and an existing output is replaced only with `--force`.
- Values reach Keynote as `osascript` arguments, never spliced into script source.
- Stop path: every call ends at `KEYNOTE_TIMEOUT` (default 300 s). After an interrupted
  run, `keynote.sh --close-leftovers` closes only the decks the scripts opened. The
  scripts never quit Keynote, never close the user's own decks, and never click dialogs.
- Passwords passed with `--password` appear in the process list while the export
  runs. Mention this if the user cares.
