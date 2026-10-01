# Gotchas

All of these were reproduced on Shortcuts 10.0 / macOS 27.0.1.

## Running

- **Hangs instead of failing.** A shortcut that needs interaction blocks `shortcuts run`
  with no window, no output and no error. Causes include Ask for Input, Choose from
  Menu, an unset required parameter, and a first-run privacy prompt. Always use a
  timeout. `sc-run.py` kills the process group on timeout.
- **macOS has no `timeout` command.** `timeout 60 shortcuts run …` fails with
  "command not found". Use `sc-run.py`, or Python's `subprocess.run(timeout=…)`.
- **Exit 0 with no output.** Text output to an `-o` path with an unknown extension
  (`.out`) writes nothing. Use `.txt` or `--output-type public.plain-text`.
- **Exit 0 with junk output.** Input of a type the shortcut doesn't accept (a text file
  given to an image shortcut) doesn't fail. The output is a UUID string or an empty file, written under
  whatever name `-o` gave it. Filter batches with `--glob` and use `--expect`.
- **Error messages are localized.** On a Hungarian system: `Error: A megadott index
  kívül esik…`. Branch on exit codes, never on message text.
- **Several outputs make `-o` a folder.** Two `-i` files with `-o result.png` create a
  *directory* called `result.png` holding `img.png` and `img2.png`.
- **The `-o` extension converts images**: `-o x.jpg` re-encodes as JPEG. PNG results are RGBA.

## Inspecting

- **`action count` / `subtitle` from AppleScript are wrong for imported shortcuts**: 0 and
  "No actions" (*Nincsenek műveletek*), even though the actions run.
- **`~/Library/Shortcuts` is TCC-protected** ("Operation not permitted"). Don't try to
  read the database. Ask for an exported file instead.
- **Exported files come in two signature formats** (see file-format.md). A decoder that
  only handles `SigningCertificateChain` fails on the default `people-who-know-me` files.

## Building and importing

- **Import always needs a click.** `open X.shortcut` shows a preview with "Add Shortcut".
  Automating that click depends on the UI language and on Accessibility permission.
  Don't do it; ask the user.
- **The import name comes from the file name**, not from anything in the plist.
- **A generated action with a wrong parameter key imports fine and then hangs at run
  time** (seen with `text.changecase`). Only generate verified actions, and smoke-test
  every generated shortcut with a short timeout before using it.
- The CLI cannot delete shortcuts. Test shortcuts the agent created must be removed by
  the user in the app (select, then ⌫).
