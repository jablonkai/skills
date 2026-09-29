# Gotchas (Inkscape 1.4 CLI)

Each item below was hit or confirmed on Inkscape 1.4.4.

## Silent failures

- **The exit code is 0 even when an action fails.** An unknown ID, a boolean with
  fewer than two paths, and wrong `object-trace` arguments all just print a message.
  After every raw call, check stderr **and** that the output exists and changed. The
  skill's scripts do both.
- `--export-id=missing` prints `Object with id="…" was not found … Skipping.` and
  writes no file.
- An `org.inkscape.*` extension called through `--actions` that fails to start (for
  example when its Python is killed) leaves the document unchanged and prints nothing.

## Selection state

- The selection carries through the whole chain. After `object-trace`, the new trace
  group is selected. After `path-union`, the union result is selected. Insert
  `select-clear` before selecting anything new, otherwise the next action also hits
  the previous result.
- `select-all` selects top-level non-group objects by default. Use `select-all:all`
  or `select-by-element:X` to reach objects inside groups and layers.
- An imported bitmap (`inkscape photo.png`) sits inside a group, so
  `select-all;object-trace` fails with *Select an image to trace*.

## Styles

- Path operations (union, difference, intersection, exclusion) keep the **bottom**
  object's `id` and `style` and drop presentation attributes (`fill=`, `stroke=`),
  so a shape styled `fill="red"` comes out black. Use `style="fill:…"`.
- `path-combine` keeps the **top** object's id and style instead.
- `transform-scale` also scales `stroke-width`.

## Units, DPI and sizes

- 96 DPI means 1 px per user unit **when `width` equals the viewBox width in px**. A
  document declared `width="2in"` with `viewBox="0 0 192 96"` exports at 192 px wide
  at 96 DPI and 600 px at 300 DPI (2 in × 300).
- For an exact pixel size, use `--export-width`/`--export-height` or a DPI computed from the physical width:
  `px = inches × dpi`.
- `--export-area-page` and `--export-area-drawing` **persist within a run** and the
  last one wins, with a warning. Use one area type per invocation.
- `--query-*` returns the visual bounding box, stroke included, in user units.

## Text and fonts

- A missing font is substituted silently. Name fallbacks
  (`font-family:Helvetica, Arial, sans-serif`), and outline text
  (`--export-text-to-path` or `object-to-path`) for anything sent to print or to
  another machine.
- Text outlined with `object-to-path` becomes a single `<path>` with the same `id`
  and an `aria-label` holding the original string.

## Files

- Action argument lists are split on `,` and chains on `;`, so file paths or values
  containing either break a chain (for example `object-set-attribute:style,fill:red;stroke:…`).
  Spaces are fine. Set styles one property at a time with `object-set-property`.
- `export-overwrite` rewrites the whole file: comments and formatting are lost, and
  Inkscape adds a `sodipodi:namedview`. Keep a hand-written source separate from the
  processed file.
- Plain SVG export (`-l`) drops `inkscape:groupmode`, so layers become plain groups.
  Keep the Inkscape SVG as the editable source.

## Versions

- 0.92 syntax (`-e out.png`, `-z`, `--verb=…`, `--without-gui`) is gone in 1.4.
  `scripts/inkscape.sh` refuses anything that is not 1.x.
- Action names were reworked across 1.0 → 1.2 → 1.4. Everything in this skill is
  verified on 1.4.4 only. On an older 1.x, check every action with `--actions-grep`
  before use. If `path-*` or `object-trace` are missing, ask the user to upgrade to
  1.4 (`brew upgrade --cask inkscape`) instead of improvising.
- Always check with `--action-list` (`inkscape.sh --actions-grep`) instead of relying
  on memory.

## Python extensions

- Extensions live in `Inkscape.app/Contents/Resources/share/inkscape/extensions/`
  and run under the bundled Python 3.10 (`Contents/Resources/bin/python3`). The
  system `python3` lacks `lxml`, so it cannot import `inkex`.
- On the verification Mac, macOS killed the bundled Python at launch (SIGKILL, exit
  137). It happened in the user's own Terminal too, so it is the install, not the
  agent environment. Extension actions then silently do nothing.
  `inkscape.sh --check` reports `extensions: UNAVAILABLE` in that case. Reinstalling
  Inkscape (`brew reinstall --cask inkscape`) may help, but that is unverified.
