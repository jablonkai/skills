# The `shortcuts` CLI and the scripting dictionary

Checked with `--help` on Shortcuts 10.0 / macOS 27.0.1. The CLI exists since macOS 12.

## Subcommands

| Command | Notes |
|---|---|
| `shortcuts list [-f NAME\|ID\|none] [--folders] [--show-identifiers]` | One name per line, `Name (UUID)` with `--show-identifiers`. `-f none` lists shortcuts outside folders |
| `shortcuts run NAME\|ID [-i PATH ...] [-o PATH] [--output-type UTI]` | `-i` repeats. stdin is also passed as input when piped. Without `-o`, text results print to stdout |
| `shortcuts view NAME` | Opens the shortcut in the editor (GUI) |
| `shortcuts sign [-m anyone\|people-who-know-me] -i IN -o OUT` | Signs a plain plist or an old-format file. The default mode is `people-who-know-me` and works offline |

There is no `create`, `delete`, `rename`, `export` or `import` subcommand.

## Input and output, as observed

- **Text result, no `-o`**: printed to stdout without a trailing newline. A word count
  of a 4-word file prints `4`.
- **`-o file.txt`**: text is written to the file. **`-o file.out` (unknown extension)
  writes nothing and still exits 0.** `--output-type public.plain-text` fixes that, or
  use `.txt`.
- **Image result**: the `-o` extension picks the format. A PNG input with `-o x.jpg`
  gives a JPEG. Resized PNGs come back RGBA.
- **Several results** (several `-i`, or a list result): `-o PATH` is created as a
  **folder**, and items keep their input file names. `-o dir/` into an existing folder
  does the same.
- **Wrong input type** (a `.txt` given to an image-only shortcut): exit 0, and the
  output is a UUID string or an empty file. Filter inputs first and check output types.
- **Errors**: exit 1, `Error: <message>` on stderr, **in the system UI language** (for
  example Hungarian). Don't match on the wording.
- **Needs interaction** (an Ask/Choose action, an unset required parameter, a
  first-time permission prompt): the CLI blocks forever and shows nothing. Always use a
  timeout.
- Typical runtime for a trivial shortcut is about 0.2–0.6 s per call.

## Scripting dictionary (Shortcuts Events)

```
shortcut: name, subtitle, id, folder (rw), color, icon, accepts input, action count
folder:   name (rw), id, shortcuts
run shortcut <s> [with input <any>]
```

- `Shortcuts.app` exposes the same dictionary. `Shortcuts Events` runs headless.
- **`action count` is 0 and `subtitle` is "No actions" for imported shortcuts that do
  have actions.** Don't use them.
- Moving a shortcut into a folder (`set folder of`) and renaming a folder are the only
  writes. Neither is needed by this skill.
- It needs Automation permission for the calling app (error -1743 when denied).

```javascript
// osascript -l JavaScript
const s = Application("Shortcuts Events").shortcuts;
JSON.stringify(s.name().map((n, i) => [n, s.acceptsInput()[i]]));
```
