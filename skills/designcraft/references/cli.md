# designcraft-cli reference (0.14.0)

`designcraft-cli` (`~/.local/bin/designcraft-cli`) runs the DesignCraft engine headless.
Vendor docs: `docs/agents.md`, `docs/mcp.md`, `docs/control-protocol.md` in
<https://github.com/storytold/designcraft>.

## Contents

- [run](#run) · [script](#script) · [Exports](#exports) · [PDF options](#pdf-options)
- [Registry lookup](#registry-lookup) · [validate-pdf](#validate-pdf) · [mcp](#mcp) · [Other subcommands](#other-subcommands)

## run

```sh
designcraft-cli run [--in FILE | --sample] [--cmd ID[=JSON]]… [--page N] [--scale S] \
    [--pdf-options JSON] [--export OUT]… [--all-pages DIR]
```

- Arguments run **in order**. `--page` (0-based), `--scale` (pixels per point, default 1)
  and `--pdf-options` apply to the `--export`s that follow them:
  `run --in F --scale 0.5 --export small.png --scale 2 --export large.png`.
  An option with no `--export` after it is an error.
- `--in` opens `.designcraft` or `.idml`; without it the engine starts from an empty
  Letter document (`--sample`: the sample magazine).
- Each `--cmd` prints its JSON result on its own line; the `wrote …` lines of the exports
  may come first (output order is not run order).
- `--cmd 'file.save={}'` writes back to `--in` — run it on a copy. `file.saveAs {path}`
  adds `.designcraft` when the extension is missing.
- `--all-pages DIR` writes every page as PNG, named from 1: `page-001.png` is `--page 0`.
- Unknown params are rejected with the list of valid ones ("did you mean …"); the help
  text saying they are ignored is out of date.

## script

```sh
designcraft-cli script [FILE|-] [--in FILE | --sample] [--save OUT] [--export OUT]… [--keep-going]
```

One step per line: `command.id {"param": 1}`, `command.id={json}`, `command.id` alone,
`{"command": …, "params": …}` JSON lines, or one JSON array of those. `#` and `//` lines
are comments. Results feed later steps:

- `"$N.path"` — the value at `path` in step N's result, **0-based**, comments and blank
  lines not counted: `"$1.story"`, `"$3.ids.0"`; `$last` is the previous step.
- `"${N.path}"` inside a longer string; `"$$"` is a literal `$`.
- Text params: `\n` new paragraph, `\u2028` forced line break, `\t` tab, `\ue000` page number.

`--save` writes `.designcraft` after the script succeeds; `--export` writes plain exports
(`.pdf`, `.idml`, `.epub`, `.pptx`, `.png`, `.jpg`, page 0 for images) — for PDF/X-4 or a
page other than the first, end the script with `file.exportPdf {…}` instead. A failing
step stops the script (`step N (id) failed: …`); `--keep-going` records `{"error": …}`
and continues. `script.run {text}` runs a script as one command (e.g. from `run --cmd`).

## Exports

| `--export` extension | Result |
|---|---|
| `.pdf` | all pages, plain PDF (no bleed, no marks) unless `--pdf-options` came first |
| `.png` / `.jpg` | one page: `--page N` (0-based, default 0) at `--scale S`; the bleed is included in the image |
| `.designcraft` | the document |
| `.idml` | InDesign interchange (re-opens with styles and pages) |
| `.epub` | reflowable EPUB (`file.exportFixedEpub` for fixed layout) |
| `.pptx` | one slide per page |

Command equivalents: `file.exportPdf`, `file.exportIdml`, `file.exportEpub`,
`file.exportHtml`, `file.exportPptx`, `file.exportText`, `file.package` (collect fonts and links).

## PDF options

`file.exportPdf` / `--pdf-options` keys (`dc_commands.py --id file.exportPdf`):

| Key | Values |
|---|---|
| `path` | output (command only; without it the result is base64) |
| `standard` | `"none"` (default), `"x4"` (PDF/X-4), `"a2b"` (PDF/A-2b), `"x1a"` (PDF/X-1a:2003, new in 0.14.0: the X-4 file flattened to CMYK/gray/spot, no transparency; `validate-pdf` reports `PDF/X-1a:2003`) |
| `bleed` | `true`: include the document bleed (set by `file.new {bleed}` / `layout.documentSetup`) |
| `marks` | `true` or `{crop, bleed, pageInfo, weight, offset}` |
| `pages` | `"1-3,5"` or `[1, 3]` — **1-based** |
| `spreads`, `tagged`, `compressImages`, `flatten`, `title`, `author`, `created` | as named; `created` (Unix seconds) makes the file reproducible |

Result: `{path, bytes, pages, warnings}`. A PDF/X-4 export reports problems as `warnings`;
it does not embed or outline fonts that can't be embedded.

## Registry lookup

```sh
designcraft-cli commands [FILTER]    # JSON array: id, label, menu, shortcut, params, enabled
designcraft-cli describe ID          # one command; an unknown id lists similar ones
```

Prefer `scripts/dc_commands.py WORD…`. `enabled: false` with `disabled_reason` reflects
the empty start document (e.g. "needs a selection"), not the command's availability.

## validate-pdf

`designcraft-cli validate-pdf F.pdf` → `{path, standard, valid, issues: [...]}`, exit 1
when invalid. Checks PDF/X-4 identification, output intent, trim/bleed boxes, encryption,
image interpolation, Type 3 fonts, device RGB under a CMYK intent and unembedded fonts
that draw visible text. Not a complete preflight; `preflight.run` checks the document side
(missing links, overset, low-res images).

## mcp

```sh
designcraft-cli mcp [--sample] --automation-read-root DIR… --automation-write-root DIR…
```

A JSON-RPC MCP server over stdio with an in-process engine (starts with an empty Letter
document). Tools: `execute {command, params}`, `batch {commands: [{command, params}]}`
(every step's params checked before the first runs; `$N.path` refs, 0-based),
`inspect_document`, `get_story`, `set_story_text`, `new_document`, `open_document`,
`save_document {path}`, `place_image`, `render_page`, `export_png {page (0-based), path,
scale (default 2)}`. Window tools (`screenshot`, `click`, `dialog_*`) need `--connect`,
which this skill doesn't use ([security.md](security.md)). `scripts/dclib.py` has a
minimal client (`Session`).

## Other subcommands

`perf`, `bench FILE` (layout/render timing), `links` (community URLs), `app` (sends a
command to an app started with `--control PORT` — not used here), `--version`.
