---
name: effectcraft
description: 'Automate EffectCraft, the After Effects-style motion-graphics compositor, headless with effectcraft-cli: build comps with text, shape and footage layers, eased keyframes, expressions and effects from a spec; change text, values and keyframes in .ecproj projects; make and fill .ectemplate templates from JSON or CSV (lower thirds, name titles); render PNG stills and H.264, ProRes 4444 alpha, WebM or GIF, verified by read-back and ffprobe. Use when the user mentions EffectCraft, effectcraft-cli, an .ecproj or .ectemplate file, or wants an After Effects-style comp or .jsx script made or rendered with EffectCraft: "make a lower third in EffectCraft and render ProRes 4444 with alpha", "fill this .ectemplate with these names and render MP4s", "change the title text in this .ecproj and render frame 2 s". Not for Cavalry scenes (cavalry), Apple Motion/Final Cut titles (apple-motion), Nuke comps (nuke), editing timelines (filmcraft, davinci-resolve), or plain transcodes (handbrake, compressor).'
summary: "automate EffectCraft headless with effectcraft-cli — comps with text, shape and footage layers, keyframes, expressions and effects from a spec, .ecproj edits, Essential Graphics templates filled from JSON or CSV, PNG stills and H.264/ProRes 4444 alpha renders, info, get and ffprobe read-back verified"
category: motion-design
compatibility: "Built for EffectCraft 0.20.0 and effectcraft-cli 0.20.0 on macOS, Python 3.9+, ffprobe (FFmpeg) for render checks; pre-1.0, so command ids may change."
risk: medium
tags: [effectcraft, after-effects, motion-graphics, compositing, lower-third, essential-graphics, prores, headless]
license: GPL-3.0-only
metadata:
  version: "1.2.0"
  author: "Tamás Jablonkai"
---

# EffectCraft via effectcraft-cli

EffectCraft is an After Effects-style compositor: projects (`.ecproj`) hold compositions,
compositions hold layers, layers hold a property tree you can keyframe, drive with
expressions and stack effects on. Every menu item and panel action is a command in one
engine registry (743 in 0.20.0, plus 308 effects). The same commands run from
`effectcraft-cli`, from a headless MCP session (`effectcraft-cli mcp`) and in the app. This
skill drives them **headless**, so no window opens, and checks every result by reading the
project or the render back. It is verified against **EffectCraft 0.20.0** and
**effectcraft-cli 0.20.0** on macOS. The software is pre-1.0, so if a pinned id fails, look
it up rather than guessing.

```sh
command -v effectcraft-cli || ls ~/.local/bin/effectcraft-cli
effectcraft-cli --version
```

## Pick the route

| Task | Route |
|---|---|
| New comp with layers, keys, expressions, effects → save, preview, render | `scripts/ec_build.py spec.json` |
| Same, plus an Essential Graphics template to fill later | `ec_build.py` with `"essential"` + `"template"` |
| Fill a template with N value sets → N movies or stills | `scripts/ec_template.py T.ectemplate values.csv OUTDIR` |
| What a project holds: comps, layers, items | `effectcraft-cli info --project F --json`, `ec_verify.py project` |
| A layer's property paths and values | `effectcraft-cli props COMP LAYER --flat --project F` |
| Change text, a value, a keyframe, add an effect in an existing project | `--save-as` a copy, then `set` / `run` on the copy ([recipes](references/recipes.md#open-edit-render)) |
| One still to look at | `effectcraft-cli render-frame --project F --comp C --time S --out f.png [--transparent]` |
| A deliverable | `effectcraft-cli render --project F --comp C --out X --format h264\|prores\|webm\|png… ` |
| Logic the registry doesn't cover (loops, AE scripts) | `effectcraft-cli script build.jsx F.ecproj --save` ([cli.md](references/cli.md#script)) |
| Find a command and its params | `scripts/ec_commands.py WORD…` / `--id ID` |

## Scripts

`S=<this skill>/scripts`; call as `python3 $S/<script>`. Python 3.9+, standard library
only, each with a full `--help`.

- **`ec_build.py SPEC.json [--overwrite]`**: a new project from a spec — comp, layers (top
  of the stack first: `text`, `shape`, `solid`, `null`, `adjustment`, `footage`), `props`,
  `keys` (comp seconds, `ease`: easyEase by default), `expressions` (fails on an expression
  error), `effects` with values, `timing`, Essential Graphics controls, then save, template
  export, a preview PNG and renders. Layers are created in one atomic batch; nothing is
  saved when any step fails. Runs `mcp` confined to the spec's folder and the output
  folders. Spec: [recipes.md](references/recipes.md#lower-third-from-a-spec).
- **`ec_template.py T VALUES OUTDIR`**: one render per JSON object / CSV row; keys are
  control names (case-insensitive), `out` names the file. Checks every key against the
  template **before** rendering — EffectCraft would otherwise fail mid-batch.
  `--format`, `--prores 4444 --channels rgba`, `--still 2.0` for PNGs, `--dry-run`.
- **`ec_verify.py`** prints JSON and exits 1 on any failed check:
  - `project F --comp LT --size 1920x1080 --duration 5 --fps 25 --layer Name:Text Bar:Shape --text "Name=Jane Doe" --value Bar:transform/opacity=90 --animated Name:transform/position --key 'Name:transform/position@0.6=[160,900]' --effect "Bar=Gaussian Blur" --expression Bar:transform/rotation`
  - `render FILE… --codec prores --profile 4444 --alpha --duration 5 --size 1920x1080 --count 3`
  - `template T.ectemplate --controls Name Title`
  - `hash PATH… [--compare manifest.json]` · `differ A.png B.png`
- **`ec_commands.py WORD…`** (`--prefix keys.`, `--id prop.addKey --schema`): filtered
  registry lookup with params. Never dump `effectcraft-cli commands`.

## Workflow

1. **Inspect first.** `info --project F --json` (active comp, its layers, project items);
   `exec comp.info --params '{"comp":"X"}'` for any other comp; `props` for property paths.
   Look up any command you haven't used this session with `ec_commands.py`.
2. **Never touch the originals.** Edit a copy: the first command gets `--save-as copy.ecproj`,
   later ones `--project copy.ecproj --save`. Snapshot inputs with `ec_verify.py hash`.
3. **Do the work** with the route from the table.
4. **Read back** with `ec_verify.py project` (text, values, keys, effects) and
   `ec_verify.py render` (codec, profile, alpha, duration, size).
5. **Look at it.** Render a still (`render-frame`, `--transparent` for alpha work) and view
   it: text running off-frame, a layer hidden behind another, footage that already ended,
   wrong colours only show up there.
6. **Report** outputs, the checks that passed, and anything you could not verify.

## The traps that cost the most (details in [gotchas.md](references/gotchas.md))

- **No `--project` means the demo project.** `info`, `render`, `render-frame`, `set`… without
  `--project F` / a positional `F.ecproj` / `--empty` silently work on the bundled demo.
- **No `--save` means nothing was saved** — yet `set` still prints the new value. Every
  editing call needs `--save` or `--save-as`; `--save` writes in place, so copy first.
- **Point text is centred on `position`** (horizontal centre, baseline) and shape layers are
  centred on theirs. For a left-aligned lower third pass `"justify": "left"`.
- **Keyframe times are layer time.** CLI `set --time`, `prop.set` and `prop.addKey` take
  *layer* seconds; `get --time`, renders and the timeline the user reads are *comp*
  seconds. On a layer that starts at 2 s, `set … --time 2.5` adds a key at comp 4.5 s and
  leaves the real one alone. Check the layer's `start` (`comp.info`), and key by comp time
  with `run prop.set '{"layer":…,"path":…,"value":…,"time":2.5,"timeBase":"comp"}'`
  (`ec_build.py` always does). Times snap to frames: 2.5 s at 25 fps lands on 2.48 s.
- **`run` steps can't reference earlier results** (`"$1.layer"` is taken as a layer name).
  Name layers when you create them and refer to them by name, or use `ec_build.py`, whose
  MCP `batch` does resolve `"$N.key"` (1-based).
- **A template needs controls.** `essential.exportTemplate` fails until
  `essential.addProperty` has added at least one; `--values` keys must be control names.
- **Render `--comp` explicitly.** Without it the active comp renders, which after opening a
  project with several comps is whichever was last active.
- **Effect parameter paths are positional**: `effects/#2/blurriness` is the *second* effect.
  `effect.apply` returns the path; read it rather than counting.

## References

- [references/cli.md](references/cli.md): subcommands, global options, render formats and flags, `script`, `mcp`.
- [references/commands.md](references/commands.md): pinned 0.20.0 ids by task, with key params.
- [references/recipes.md](references/recipes.md): lower third spec, template batch, open-edit-render, effects + still, image sequences.
- [references/gotchas.md](references/gotchas.md): silent failures and surprises.
- [references/security.md](references/security.md): file roots, scripts, and why there is no live-app bridge.
