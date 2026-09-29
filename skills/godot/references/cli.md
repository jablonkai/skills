# Godot 4 command line

Verified on Godot **4.7.2.stable** (macOS). Run `bash scripts/godot.sh --help` to see the
flags for other versions. Flags marked *editor* start the editor code path (import,
export), and the others run the project.

## Flags this skill uses

| Flag | What it does | Notes |
|---|---|---|
| `--path DIR` | project to use (contains `project.godot`) | always pass it; do not rely on the cwd |
| `--headless` | dummy display, renderer and audio | for runs, checks and exports; renders **no pixels** |
| `-l en` | locale for engine and editor messages | the editor language can be localized (e.g. Hungarian); force `en` so logs grep reliably |
| `--import` *editor* | scan and import all resources, then quit | first run of a new project; after adding assets |
| `--quit` / `--quit-after N` | quit after 1 / N main-loop iterations | without one, a run never ends |
| `--fixed-fps F` | fixed step, no real-time sync | makes `--quit-after N` = N/F seconds of game time, and runs faster than real time headless |
| `--script PATH` | run a script as the main loop (`extends SceneTree` or `MainLoop`) | `res://…` or an absolute path outside the project |
| `--check-only` | parse only, with `--script` | exit code is **0 even on a parse error**; without `--script` it just runs the game |
| `SCENE` (positional) | run this scene instead of `run/main_scene` | `godot --path P res://levels/two.tscn` |
| `--write-movie OUT` | Movie Maker: `.png` sequence (`OUT00000000.png…`), `.avi` (MJPEG), or `.ogv` (Theora, the docs' recommended format; editor builds only) | needs a real display driver; implies `--fixed-fps 60`; the PNG sequence gets a `.wav` alongside |
| `--minimized` | start the window minimized | Movie Maker still renders frames |
| `--export-release PRESET OUT` *editor* | export with a preset from `export_presets.cfg` | needs export templates; exit 1 on failure; `OUT` is relative to the **project folder**, not the cwd, and its directory must exist |
| `--export-debug PRESET OUT` *editor* | debug export | same; like `--export-pack`, implies `--import` |
| `--export-pack PRESET OUT` *editor* | data only, `.pck` or `.zip` | no templates needed |
| `--log-file FILE` | write the log here too | the skill redirects stdout/stderr instead |
| `--quiet` / `--no-header` | less stdout | errors are still printed |
| `-- ARGS…` | user arguments, read with `OS.get_cmdline_user_args()` | everything after a bare `--` |
| `--version` | `4.7.2.stable.official.ed1daf0bf` | `.mono.` in the string = .NET build |

## Exit codes and logs

Godot's exit code is **not** a verdict on the project:

| Situation | Exit code | What shows in the log |
|---|---|---|
| Runtime script error (null call, missing node) | 0 | `SCRIPT ERROR:` or `ERROR:` + `at:` + GDScript backtrace |
| Parse error in a script the scene uses | 0 | `SCRIPT ERROR: Parse Error: …` + `ERROR: Failed to load script` |
| `--check-only --script bad.gd` | 0 | `SCRIPT ERROR: Parse Error: …` |
| `--script t.gd` that calls `quit(3)` | 3 | whatever it printed |
| `--script t.gd` that errors before `quit()` | never exits | the error, then it hangs; a timeout or watchdog is required |
| `--script bad.gd` with a parse error | 1 | `Failed to load script` |
| `--export-*` success | 0 | progress lines |
| `--export-*` failure (unknown preset, config error, no templates) | 1 | `ERROR: Cannot export project with preset …` + the reason |

**Unknown command-line arguments are ignored silently**, so a misspelled flag just
does nothing. `--headless` is required on machines without GPU access, such as CI
runners. On a desktop it only keeps the window from opening.

So:
- grep the log for `^(SCRIPT ERROR|USER SCRIPT ERROR|ERROR|USER ERROR)`, and treat any
  match as a failure;
- use `quit(code)` in test scripts to get a real verdict;
- always run with a timeout.

`scripts/gd-run.sh` does all three. macOS has no `timeout(1)`, so the scripts use
`perl -e 'alarm N; exec @ARGV' …`. A process killed that way exits with 142.

Warnings (`WARNING:`, e.g. unused variables, integer division) do not fail a run.
Read them anyway: they often point at the bug.

## Language server and debugger (optional)

The editor serves the GDScript LSP on port **6005** and DAP on **6006** while it is
open (`--lsp-port` / `--dap-port` override them). They belong to the user's running
editor and IDE, and this skill does not depend on them. `gd-check.gd` gives the same
parse diagnostics headless, without an editor. Use the LSP only when the user already
has the editor open and asks for symbol-level help.

## Other useful commands

```bash
G="bash scripts/godot.sh"
$G --headless --doctool /tmp/godot-api --no-docbase   # dump the class reference as XML (large)
$G --headless --path P --script res://tools/bake.gd -- --level 3   # tool script with user args
$G --path P --debug-collisions --quit-after 120       # visible run with collision shapes drawn
```
