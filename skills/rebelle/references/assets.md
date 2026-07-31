# Finding brush presets, papers and other assets

`SET_BRUSH` fails loudly on a bad preset (`ERROR: Preset for brush was not set`) but
`NEW_ARTWORK` fails *silently* on a bad paper — you get the default paper and no
warning. So resolve names against the filesystem before using them; it is faster than
a render round-trip and works without the app running.

## Where the libraries live

| Kind | Path |
|---|---|
| User brushes/papers/etc. (what the app actually offers) | `~/Library/Application Support/Escape Motions/Rebelle 8/` |
| Factory papers shipped in the app | `/Applications/Rebelle 8.app/Contents/Resources/Data/PaperShop/` |
| Factory brushes shipped in the app | `/Applications/Rebelle 8.app/Contents/Resources/Brushes/` |

On Windows the user folder is `%USERPROFILE%\Documents\Escape Motions\Rebelle 8\`.

## Brush presets

A preset path is `"<Subfolder>/<Preset name>"` **relative to the tool's own folder** —
the tool is named separately in `SET_BRUSH`, never in the path.

```bash
B=~/Library/Application\ Support/Escape\ Motions/Rebelle\ 8/Brushes
ls "$B"                                   # tool folders
ls "$B/Watercolor"                        # subfolders: Bristle, Gouache, Sumi-e, ...
ls "$B/Watercolor/Watercolor" | sed 's/\.rebelle-brush\.png$//'   # preset names
```

Tool folders map to the `tool` values like this:

| `tool` | folder | | `tool` | folder |
|---|---|---|---|---|
| `WATERCOLOR` | `Watercolor` | | `SMUDGE` | `Smudge` |
| `OIL_AND_ACRYLIC` | `Oil` (also `Acrylic`) | | `BLEND` | `Blend` |
| `EXPRESS_OIL` | `ExpressOil` | | `CLONE` | `Clone` |
| `INK_PEN` | `Ink` | | `ERASER` | `Eraser` |
| `PENCIL` | `Pencil` | | `WATER` | `Wet` |
| `PASTEL` | `Pastel` | | `DRY` | `Dry` |
| `MARKER` | `Marker` | | `BLOW` | *(no presets — Rebelle logs "Tool BLOW doesn't have presets, skipping")* |
| `AIRBRUSH` | `Airbrush` | | | |

`Favorite`, `1. Shapes` and `2. Grains` are cross-tool folders, not tools. Verified
working examples: `WATERCOLOR` + `"Watercolor/Round"`, `PENCIL` + `"Charcoal/Charcoal"`,
`PENCIL` + `"Graphite Pencil/HB"`, `WATERCOLOR` + `"Gouache/Gouache Filbert"`.

An absolute path to a `.rebelle-brush.png` also works, which is how you use a preset
that was just written by `EDIT_BRUSH_PRESET`.

## Papers

`"<Category>/<Name>"`, e.g. `"Handmade/HM01 Handmade"`, `"Default/RH00 Aquarelle"`
(the default), `"Hot Pressed/HP01 Hot Pressed"`. Categories: `Canvas`, `Cold Pressed`,
`Default`, `Exotic`, `Felt`, `Gesso`, `Handmade`, `Hot Pressed`, `Lokta`, `Machinemade`,
`Rough`, `Stone`, `Washi`, `Wood`.

```bash
ls /Applications/Rebelle\ 8.app/Contents/Resources/Data/PaperShop/*/    # every paper
```

Note the official quickstart's `"Default/HM01 Handmade"` is wrong for Rebelle 8 — HM01
lives under `Handmade`. That is exactly the silent-failure case: the render succeeds and
you simply get the wrong paper.

## Live discovery

With Rebelle running with its WebSocket server, `{"cmd":"list_tool_presets"}` returns
the preset paths of the tool **currently selected in the UI** (the `tool` parameter is
ignored), and `{"cmd":"list_tools"}` returns the tool names in UI order. Useful to see
what the user has selected right now; the filesystem is better for everything else.

## Other libraries

Same folder, same idea: `Papers`, `Stencils`, `Structures`, `Patterns`, `Gradients`,
`Granulations`, `Reflection Maps`, `Colors`, `Mixing Palettes`, `Paths`,
`Reference Images`. Most are referenced from the UI rather than from JSON events, but
they show what the user has installed.
