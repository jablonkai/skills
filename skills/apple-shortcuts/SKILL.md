---
name: apple-shortcuts
description: 'Run, inspect and build Apple Shortcuts on macOS from the command line: list shortcuts and folders with whether each accepts input, run a shortcut on files or text and capture its output, batch it over a folder, wrap it as a reusable agent or script step with a timeout, exit codes and output checks, decode an exported .shortcut file to read its actions, and generate simple shortcuts as signed files the user adds with one click. Use for "run my Resize shortcut on every image in this folder", "what shortcuts do I have and what do they do", "turn this shortcut into a script step with error handling", "chain these two shortcuts", "what does this .shortcut file do", "make me a shortcut that counts words", "shortcuts run". Not for editing Photos libraries (apple-photos), Keynote/Numbers/Pages documents (keynote, numbers, pages), video transcoding (handbrake), or image edits GIMP, Inkscape or sips can do directly — unless the user wants them done through a shortcut.'
summary: "list, inspect and run Apple Shortcuts from the CLI — file and text input and output, folder batches, timeout-guarded agent steps, decoding exported .shortcut files, and generating signed shortcuts for one-click import"
category: mac-automation
risk: medium
tags:
    - shortcuts
    - macos
    - automation
    - cli
---

# Apple Shortcuts from the command line

Three surfaces, all local:

- **`/usr/bin/shortcuts`**: `list`, `run`, `view`, `sign`. It does all the running.
- **The `Shortcuts Events` scripting dictionary**, used read-only. It adds `accepts input` per
  shortcut. It has no create, delete or export verb.
- **`.shortcut` files.** They are plists of `WFWorkflowActions`, signed as an Apple Encrypted
  Archive. `sc-decode.py` reads them and `sc-build.py` writes and signs simple ones.

Verified on **Shortcuts 10.0 / macOS 27.0.1**. Nothing listens on a port.

## Rules

- **A shortcut can do anything its actions do**: send messages, delete files, call the
  network. Run only shortcuts the user named or approved. When you have the file, run
  `sc-decode.py` first and say what it will do. Never run unknown shortcuts to "see what
  they do".
- **Always run through `sc-run.py`**, or with your own timeout. **A shortcut that wants
  interaction hangs `shortcuts run` forever, with no window and no error.** Interaction
  means an Ask/Choose action, an empty required parameter, or a first-run permission
  prompt. macOS has no `timeout` command.
- **Exit 0 does not mean it worked.** Check the output:
  - text written to `-o x.out` (an extension Shortcuts doesn't know) is silently dropped;
  - input of a type the shortcut doesn't accept still exits 0 and writes junk (a UUID string or an empty file);
  - `sc-run.py` turns both into exit 3. Use `--expect image|pdf|text`.
- The library cannot be changed from the CLI: no create, edit, delete or rename. Adding
  a shortcut always takes the user's click.

## Setup

```bash
S=scripts                      # relative to this skill's directory
bash $S/sc.sh --check          # versions, CLI, counts, Automation access to Shortcuts Events
```

If Automation is denied, allow it under System Settings › Privacy & Security ›
Automation. Only `sc-list.py`'s `accepts_input` needs it.

## Discover and inspect

```bash
python3 $S/sc-list.py                   # JSON: name, id, folder, accepts_input
python3 $S/sc-list.py --folder Work     # one folder ("none" = not in a folder)
python3 $S/sc-decode.py "Thing.shortcut"   # input types + one line per action, variables resolved
shortcuts view "Thing"                  # opens it in the editor for the user to look at
```

- **Ignore `action count` and `subtitle` from the dictionary**: they report 0 / "No actions"
  for imported shortcuts that do have actions.
- The library database is TCC-protected, so a library shortcut's actions are only
  readable from a file. Ask the user to export it: right-click › Share › Export File, or
  drag it to Finder. Then decode the file.
- When describing shortcuts without files, say what is known (name, folder, whether it
  takes input) and what would need the file. Don't guess from the name.

## Run

```bash
python3 $S/sc-run.py "Word Count" -i notes.txt              # text result -> "stdout" in the JSON
python3 $S/sc-run.py "Word Count" --stdin "some text"       # stdin is passed as input
python3 $S/sc-run.py "Resize" -i a.png -o small.png --expect image
python3 $S/sc-run.py "Resize" -i a.png -o small.jpg         # the -o extension converts (JPEG here)
python3 $S/sc-run.py "Resize" -i a.png -i b.png -o outdir   # several results -> a folder, input names kept
python3 $S/sc-run.py "Resize" --batch in/ --out out/ --glob '*.png' --glob '*.jpg' --expect image
```

- Exit codes: 0 ok, 1 the shortcut failed (its message, in the user's UI language, is in
  `error`), 2 bad arguments, 3 no output or the wrong type, 4 shortcut not found, 124
  timeout, 130 interrupted.
- `--batch` runs once per file, so one bad file doesn't sink the rest. It names outputs
  `out/<stem><ext>` (`--ext` changes the extension). A re-run skips outputs that already
  exist (`--overwrite` redoes them). `--fail-fast` stops at the first failure. An
  output rejected by `--expect` is deleted, so a re-run retries it instead of skipping it.
- **Filter batches with `--glob`** to the types the shortcut accepts (see
  `accepts_input` / decode). Use `--timeout` (default 60 s) for long jobs.

## Wrap as an agent step / chain

Call `sc-run.py` and branch on its exit code and JSON. Don't parse the raw CLI. To chain,
feed one step's output file or `stdout` into the next as input; see
[references/recipes.md](references/recipes.md) for a bash and a Python wrapper and for
launchd/cron use.

## Build a new shortcut

Generation is limited to actions verified to import with their parameters intact
(`VERIFIED` in `sc-build.py`: resize image, count, get item from list, stop and output).
Anything else may import with a parameter left empty, and that makes runs hang. For
other actions, either:

1. **generate, then have the user check it in the editor** (`shortcuts view NAME`); or
2. **give hand-build steps**: the editor's action names, in order, with the settings to set.
   See [references/recipes.md](references/recipes.md#building-by-hand).

```bash
python3 $S/sc-build.py spec.json --import   # signs '<name>.shortcut' and opens the import preview
shortcuts list | grep -x "<name>"           # after the user clicks "Add Shortcut"
python3 $S/sc-run.py "<name>" ...           # smoke-test it before relying on it
```

The spec format and tokens (`$input`, `$prev`, `$N`, `:text`) are in the script header
and in [references/file-format.md](references/file-format.md). The default signing mode
(`people-who-know-me`) is fine for this Mac. Use `--mode anyone` only for a file meant
for other people. Pick a name that isn't in the library yet, and check the
result with `shortcuts list`.

## Stopping

`sc-run.py` runs the CLI in its own process group:

- a timeout kills it (exit 124);
- Ctrl-C kills it (exit 130);
- re-running a batch resumes.

If a raw `shortcuts run` is stuck, `pkill -f "shortcuts run"` ends it.

## References

- [references/cli.md](references/cli.md): CLI flags, input/output and UTI behaviour, the
  scripting dictionary.
- [references/file-format.md](references/file-format.md): plist schema, variables, signing
  and decoding, action identifiers.
- [references/recipes.md](references/recipes.md): wrappers, chaining, scheduling, building
  by hand.
- [references/gotchas.md](references/gotchas.md): **read before running raw commands.**
