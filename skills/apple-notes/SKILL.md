---
name: apple-notes
description: 'Search, export and write Apple Notes on macOS through its AppleScript/JXA dictionary: find notes by text, folder or date and list their titles and folders, export a note or a whole folder to Markdown files with their images and attachments, and create a note or append to one from Markdown (headings, lists, checklists, tables, links, images), with read-back verification. Read-only by default; never deletes notes; skips locked notes. Use for "export my Recipes folder in Notes to Markdown", "find every note that mentions the invoice number", "turn this Markdown file into an Apple Note", "append today''s log to my Journal note", "back up my notes as Markdown files", "which notes did I edit last week". Not for Obsidian vaults or plain Markdown files on disk (obsidian-*), converting PDFs or Office files to Markdown (markitdown), Pages documents (pages), Reminders or Calendar items, or Evernote/OneNote.'
summary: "search, export and write Apple Notes via JXA — text, folder and date searches, folder export to Markdown with attachments, notes created or appended from Markdown with checklists and tables, read-back verified"
category: mac-automation
compatibility: "Built for Notes 4.13 on macOS 27.0.1 (JXA)."
risk: medium
tags:
    - notes
    - apple-notes
    - applescript
    - jxa
    - macos
    - markdown
metadata:
  version: "1.0.2"
  author: "Tamás Jablonkai"
---

# Apple Notes via JXA

Everything goes through Notes' scripting dictionary (`osascript -l JavaScript`), wrapped
in stdlib-only Python helpers. Notes doesn't need to be in front, there's nothing to
install, and Full Disk Access isn't needed. The helpers solve the parts that are easy to
get wrong by hand: Notes' HTML dialect, attachments that the HTML body doesn't show, and
body rewrites that silently delete attachments.

Verified against **Notes 4.13 on macOS 27.0.1**.

## Privacy and safety rules (read first)

Notes hold private text, so treat it like mail.

- **Read-only by default.** Search and export never change a note. Write only when the
  user asks for a note to be created or added to.
- **Never delete** notes, folders or attachments. `replace` (overwrite a note's whole
  body) only on an explicit request.
- **Stay local.** Don't send note contents to web services or delegate agents. Quote
  only what the user needs; for searches, titles, folders and short snippets are enough.
- **Locked notes** can't be read by scripts. They're skipped and listed, never unlocked.

## Setup

```bash
S=scripts   # relative to this skill's directory
bash $S/notes.sh check   # versions, Automation permission, accounts/folders with note counts
```

If `automation: DENIED` appears (or error -1743), allow the terminal/IDE to control
Notes under System Settings › Privacy & Security › Automation. macOS asks for this
on the first run. AppleScript error **messages are localized**, so match the number in
parentheses, not the text.

Folders are addressed as paths, `Account/Folder/Sub` (for example
`iCloud/Recipes/Soups`). A bare `Recipes` works when it's unique. Notes are addressed by
id (`x-coredata://…`, from search output) or `Account/Folder/Title`.

## Tasks

| The user wants | Run |
|---|---|
| find notes mentioning X | `python3 $S/nt-search.py --text X` (all terms must match; add `--any` for any term, `--folder`, `--json`) |
| notes edited or created in a period | `nt-search.py --since 2026-10-04 --until 2026-10-11 [--date created]` (inclusive local dates) |
| a folder as Markdown, with images | `nt-export.py --folder "iCloud/Recipes" --out DIR` (subfolders included; `--no-recursive`) |
| one note, or the search hits | `nt-export.py --note ID --out DIR`, or `nt-export.py --ids-from hits.json --out DIR` |
| a new note from Markdown | `nt-write.py create --folder "iCloud/Projects" --md plan.md [--make-folder] [--title T]` |
| add to an existing note | `nt-write.py append --note "iCloud/Journal/Log" --md today.md` (add `--reattach` if it has attachments; see below) |
| check a note or an export | `nt-verify.py note --note ID --md FILE` / `nt-verify.py export --dir DIR --folder PATH` |

Every write accepts `--dry-run`, which prints the HTML and the target without touching
Notes. All commands print JSON (search prints text unless `--json`).

## Workflow

1. **Locate before acting.** Search or list first and tell the user what matched: count,
   titles, folders. That matters most before an export of many notes or an append.
2. **Run the helper.** Don't hand-build HTML with `osascript`, for the reasons below.
3. **Verify by read-back.** `nt-write.py` re-reads the note and diffs it against the
   Markdown (`readback.ok`, `missing`, `extra`; exit 4 on mismatch). After an export,
   run `nt-verify.py export`. Report the outcome, including anything in `warnings`,
   `locked_skipped` or `attachments_not_exportable`.

## What Notes keeps, and what it loses

- **Headings** come back as sized bold text (24/18 px). The converter maps them back to
  `#`/`##`/`###`. A note's title is simply its first line.
- **Checklists aren't scriptable.** Notes' real checkboxes can't be created or read
  through AppleScript. `- [ ]` / `- [x]` are written as `☐` / `☑` bullets and read back
  as task items, so the checklist round-trips in Markdown. In Notes they look like
  checkboxes but don't toggle on tap. Say so when you create a checklist.
- **Tables** survive both ways. Their text is missing from Notes' `plaintext`, but the
  search helper adds it.
- **Images**: `create` adds local images from the Markdown as real attachments **at the
  end of the note**, because scripting can't place them mid-text. Remote image URLs
  become links. **Only images can be attached by script.** Notes silently ignores PDFs
  and other files, so the helper warns and the user has to drag them in.
- **Notes can only append by rewriting the whole body**, and a rewrite deletes or
  degrades attachments: images, PDFs and scans either vanish or turn into copies that
  can't be exported. So `append`/`replace` stop with exit 3 on a note that has file
  attachments. The way through is `--reattach`, which saves the files first and re-adds
  them as real attachments **at the end of the note**. Tell the user that their images
  moved. If you can ask, offer that or a new note. When working unattended, `--reattach`
  is the choice that loses nothing. A note whose attachments can't be saved at all is
  always refused: offer a new note.
- Blockquotes and horizontal rules turn into plain text. Underline and colours are
  dropped on export.

Details are in [references/notes-html.md](references/notes-html.md). Read
[references/gotchas.md](references/gotchas.md) before writing raw JXA, and see
[references/jxa-reference.md](references/jxa-reference.md) for the dictionary.
[references/recipes.md](references/recipes.md) has more worked jobs: backups, daily
logs, a search into an export, and a Markdown folder imported as notes.

## Export layout

```
OUT/Note title.md                     # YAML front matter: title, id, folder, created, modified
OUT/Sub/Other note.md                 # subfolders mirror Notes
OUT/attachments/Note title/photo.jpg  # images and files, linked relatively from the .md
```

Inline images stay where they appear. Attachments that the body doesn't show are linked
under `## Attachments` at the end of the note. Existing `.md` files are kept unless
`--force` is passed, so re-running an export skips notes it has already written.

## Stopping

Every call is a one-shot `osascript` with a timeout (`--timeout SEC`, default 300).
Nothing keeps running and nothing listens on a port. If Notes shows a dialog (an iCloud
sign-in or a locked-note prompt), calls stall until the timeout and exit 124 with a hint.
Dismiss the dialog and re-run.
