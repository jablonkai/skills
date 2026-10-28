# Gotchas (effectcraft-cli 0.18.0)

## Silent

- **The demo project.** Any subcommand without `--project F`, a positional `F.ecproj` or
  `--empty` opens the bundled demo project. `info` then describes a project you never
  made, and `render` renders it.
- **Edits without `--save` vanish.** `set`, `exec` and `run` print the new value or result
  and exit; the file is untouched. `--save` writes back to the opened file — use
  `--save-as copy.ecproj` on the first edit.
- **Render without `--comp`** renders the active comp: the last created or opened one,
  not necessarily the main one.
- **Point text is centred** horizontally on `position`, with the baseline at its y. A
  "left margin at x=160" needs `justify: "left"`. Shape layers are centred on `position`.
- **Defaults:** new text is white sans-serif; comps have a black background that is
  transparent in RGBA renders; new layers last the whole comp.
- **Footage shorter than the comp** ends: frames after its out point show nothing from it.
  Check `in`/`out` in `comp.info` before picking a preview time.
- **`--end` is exclusive** in `render`.

## Loud, but confusing

- **`run` has no step references.** `"$1.layer"` is read as a layer name: `no layer
  "$1.layer"`. MCP `batch` supports them, 1-based (`"$1"` is the first step).
- **`essential.exportTemplate` fails** with "the composition has no Essential Graphics
  controls" until `essential.addProperty` has added one.
- **Template values:** unknown control names and invalid values fail before rendering;
  `ec_template.py` checks names up front so a batch doesn't stop halfway.
- **Paths outside the automation roots** are refused in `mcp` sessions
  (`it is outside the automation roots`). `ec_build.py` sets roots to the spec's folder,
  footage folders and output folders.
- **Unknown command params** are rejected with the accepted list — read it, fix the key.
- **Expressions with a syntax error** are kept but disabled; `get --json` shows
  `expressionError`. `ec_build.py` fails on it.

## Time

- `set --time`, `prop.set` and `prop.addKey` take **layer** time by default; `get --time`,
  `render-frame --time` and scripts' `setValueAtTime` take **comp** time. They only differ
  for offset or stretched layers; pass `timeBase: "comp"` to the commands to be safe.
- Times snap to the nearest frame.

## Images and colour

- `render-frame` without `--transparent` composites over the comp background; with it the
  PNG keeps alpha (what an RGBA render writes).
- `get` returns colours as 0–1 floats `[r, g, b, a]`; commands accept `#hex` or
  `[r, g, b]`. `ec_verify.py --value` accepts `#hex` for colour properties.
- ProRes 4444 with alpha reads back as `yuva444p12le`; check with `ec_verify.py render --alpha`.
