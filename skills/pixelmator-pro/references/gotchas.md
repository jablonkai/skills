# Gotchas (Pixelmator Pro 3.8, macOS 27)

These were all found by running real scripts against the app, roughly in order of how
often they break a run.

## Alerts block everything

When an operation fails, Pixelmator Pro usually doesn't return an AppleScript error.
It shows an **app-modal alert** ("The document couldn't be opened…", "The operation
couldn't be completed (…InternalError…)"). Until someone clicks OK, every Apple Event
to the app, including `count documents` and `quit`, hangs until it times out. A batch
then fails on every later file. Alerts also queue up, so one bad run can leave
several behind.

`pxm.sh run` polls for these alerts through System Events. When it finds one, it
prints the alert's text, clicks OK and fails the run. All the bundled scripts use it.
If you call `osascript` directly and it hangs, clear the alerts by hand:

```bash
osascript -e 'tell application "System Events" to tell process "Pixelmator Pro" to get value of static texts of (windows whose subrole is "AXDialog")'
osascript -e 'tell application "System Events" to tell process "Pixelmator Pro" to click button "OK" of (first window whose subrole is "AXDialog")'
```

Reading and clicking needs Accessibility permission for the terminal. Without it, the
watchdog can't see alerts and the run ends at `--timeout`. When the watchdog fires or
the timeout hits, `pxm.sh` closes **every** open document without saving.

## Sandbox: how you pass a path matters

Pixelmator Pro is sandboxed (Mac App Store). A file passed in an Apple Event only
comes with a sandbox grant when the script coerces it to a file **locally**:

| form | result |
|---|---|
| `open POSIX file "/literal/path.jpg"` | works (compiled as a file literal) |
| `open (p as POSIX file)` | works |
| `set f to p as POSIX file` before the `tell`, then `open f` | works (the pattern the scripts use) |
| `open (POSIX file p)` **inside** `tell application "Pixelmator Pro"` | **fails** with "The document is damaged, or isn't compatible", but only for files the app has never opened, so it looks random |

Files in `~/Pictures` always open, because the app has that entitlement. Files the
app has opened once keep working. That is why a script that is wrong can pass its
first tests. The same rule applies to `file:` in `make new image layer`, to
`replace image … with`, to `export … to`, and to `save … in`.

## Apple Event timeout

AppleScript gives up on a reply after **120 s** (`-1712`, "AppleEvent timed out").
Super Resolution on a 4000-px image, or a long batch of ML calls, can take longer.
Wrap the work in `with timeout of 7200 seconds … end timeout`. The block is lexical,
so a handler called from inside it needs its own block. Use `pxm.sh run --timeout`
for the overall limit.

## Numbers and lists

- `width`, `height`, `position` and `bounds` are **reals**. Coercing them to text uses
  the locale's decimal separator (`1800,0` on a Hungarian system). Always use `as
  integer` before building strings or JSON.
- `item 1 of (position of L)` inside an expression errors (`-1700`). Read
  `set p to position of L` first, then `item 1 of p`.
- `position of L as text` joins the items with no separator (`0600`).
- Colours are **16-bit** RGB lists from 0 to 65535. Multiply 8-bit values by 257.

## Variable names that are dictionary terms

Inside `tell d` or `tell application "Pixelmator Pro"`, a variable whose name matches
a dictionary term is read as that property. One example is `headline`, which is a
`document info` field: `set text content of … to headline` fails with "cannot set
headline of document". Other such names include `width`, `height`, `name`, `size`,
`color`, `file`, `position`, `bounds`, `index`, `version` and `result`. Use names like
`newText`, `w`, `sz`.

## Documents and layers

- `make new document` already contains a white **`Image Layer`** at the bottom. Keep
  it (fill it with `set current layer of d to bg` then `fill d with color {…}`), or
  `delete` it for a transparent canvas.
- `layers of d` is ordered **top-first** (`index` 1 = top). `at beginning of layers` adds
  on top and `at end of layers` adds at the bottom.
- `make new image layer with properties {file:f}` places the image at its **native
  size, centred**. It doesn't fill the canvas. To scale it, keep `constrain
  proportions` true and set only `width` (the height follows), then set `position`.
  Or use `replace image L with f scale mode scale to fill` to cover an existing
  layer's frame.
- `replace image` **renames the layer** to the new file's name. Layer references are
  id-based, so a variable keeps working. Name-based lookups (`image layer "photo"`)
  fail after the replace until you rename the layer back.
- `remove background d` acts on the document's current layer. The canvas keeps its
  size and the removed area becomes transparent. Exporting as JPEG flattens that
  area, so use PNG, WebP, HEIC or TIFF.
- `super resolution` is fixed at ×3. To hit a target size, upscale and then
  `resize image … algorithm lanczos`.

## Text

- Font, size and colour are set on the rich text: `tell text content of t to set its
  font to "…"`. Without `its`, `set color to …` is read as a variable assignment and
  fails with `-10003`.
- Fonts take **PostScript names** (`Helvetica-Bold`, `Avenir-Heavy`,
  `SFProDisplay-Bold`). An unknown name silently falls back to Helvetica, so read
  `font of text content of t` back. `pxm-compose.py` reports it.
- `position` is the top-left of the text box. The box grows **downward** as lines are
  added. A `\n` in the text gives a new paragraph.
- To centre a line, set `horizontal alignment` to `center` and `width` to the canvas
  width, then `position {0, y}`. A fixed `width` wraps longer text. To place text at a
  corner, measure `width of t` after styling and compute the position from it.
- `set text content of t to "…"` keeps the existing style, which is what you want
  when filling a template.

## Export and quality

- `compression factor` uses the same 1–100 scale as `sips -s formatOptions`. ImageIO
  writes the same tables for neighbouring values (89–91 are identical), so
  `pxm-info.py` reports a range when the value is ambiguous. On the libjpeg/IJG scale,
  85 shows up as about 95.
- `export` leaves the open document as it was. `save as new document` re-points it at
  the new file.
- `save d in f` writes `.pxd`, which keeps the layers. Reopening a `.pxd` gives
  layers, text and fonts back exactly.

## Running headless-ish

- The app has to be running for scripts to work. `tell application` launches it, and
  the first launch takes a few seconds.
- macOS has no `timeout(1)`. `pxm.sh` keeps its own timer (`perl -e 'alarm N; exec …'`
  works for one-off commands).
- Automation permission denied shows up as `-1743`, and `pxm.sh` exits 3. Re-allow it
  in System Settings › Privacy & Security › Automation, or reset it with `tccutil
  reset AppleEvents`.
- Each `osascript` launch costs about 0.2 s. `pxm-batch.py` spends one launch per
  file, which keeps a failure isolated to that file.
