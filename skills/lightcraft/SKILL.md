---
name: lightcraft
description: 'Automate LightCraft, the Lightroom-style photo library and raw developer, headless with lightcraft-cli: import folders into a library, rate, flag, label and keyword photos, query the library by rating, keyword, date or camera, develop raw and JPEG files (exposure, white balance, auto tone, presets, B&W), copy or sync develop settings across photos, merge HDR/panoramas, and export JPEG/TIFF/WebP/AVIF/DNG at a set size, quality and colour space, verified by read-back, export sizes and unchanged originals. Use when the user mentions LightCraft or lightcraft-cli, or wants a LightCraft library culled, keyworded or queried, or raws developed and exported with LightCraft: "import this shoot into LightCraft and export 2048 px JPEGs", "sync these develop settings to the rest", "list my 5-star photos in LightCraft". Not for the Apple Photos library (apple-photos), layered PSD or composite editing (photocraft), Pixelmator Pro (pixelmator-pro), GIMP/Krita, or plain resizing with no LightCraft (sips/ImageMagick).'
summary: "automate LightCraft headless with lightcraft-cli — folder import into libraries, rating, flags and keywords, library queries, raw and JPEG develop with auto tone, white balance and presets, settings sync, sized JPEG/TIFF/AVIF/DNG export, read-back verified with originals untouched"
category: design-automation
compatibility: "Built for lightcraft-cli 0.17.0 and LightCraft.app 0.17.0 on macOS; pre-1.0, so command ids may change."
risk: medium
tags: [lightcraft, lightroom, raw, photo-library, develop, keywords, export, headless]
license: GPL-3.0-only
metadata:
  version: "1.0.5"
  author: "Tamás Jablonkai"
---

# LightCraft via lightcraft-cli

LightCraft is a Lightroom-style photo library and raw developer. Every feature is a
command in one engine registry (380 in 0.17.0): import, rate, keyword, develop, export.
`lightcraft-cli run` executes those commands headless against a library folder, with no
window or GPU, and answers each one with a JSON line. This skill drives that route and
checks every result by reading the library back. Verified against **lightcraft-cli
0.17.0** and **LightCraft.app 0.17.0** on macOS. The software is pre-1.0, so when a
pinned command id fails, look it up rather than guessing.

```sh
command -v lightcraft-cli || ls ~/.local/bin/lightcraft-cli
lightcraft-cli --version
```

## Pick the route

| Task | Route |
|---|---|
| Library work: import, cull, keyword, query, develop many photos, export | `scripts/lc_run.py` (one `run` process per job) |
| One quick command or read | `lightcraft-cli run --library DIR COMMAND key=value …` |
| Develop one or two files, no catalogue, no auto tone | `lightcraft-cli render IN -o OUT --set … --size N` |
| HDR / panorama merge | `lightcraft-cli merge hdr\|panorama …` (writes next to the first input) |
| Try a command safely | `lightcraft-cli run --demo …` (in-memory 24-photo library) |

The live app port (`LightCraft --control`, `run --connect`) has **no authentication** in
0.16.0 (not re-checked in 0.17.0). This skill doesn't start it or connect to it ([gotchas](references/gotchas.md#live-app-port)).

## Scripts

They need Python 3.9+ and the standard library only. Call them as
`python3 $S/<script>` with `S=<this skill>/scripts`.

- **`lc_run.py (--library DIR | --demo) [--import PATH]… STEPS.json|-`** runs a JSON
  list of `{"command", "params"}` steps in **one** process. That matters because the
  develop clipboard does not survive between processes. It prints `ok`/`FAIL` per
  command and a summary, and exits 1 on any failure. It adds two things:
  - `{"forEach": "all" | [ids] | {filter}, "do": [steps]}` selects each photo in turn
    and runs `do` on it. This is required for commands that act on the active photo only.
  - `"@all"` anywhere in params becomes every photo id (resolved after `--import`).
- **`lc_query.py`**
  - `photos --library DIR [--rating N --op exactly] [--keyword K] [--flag pick] [--from D --to D] [--filter JSON] [--json]`:
    every match (paged), with id, file, rating, flag, label, keywords and capture date.
    It refuses filter keys LightCraft would ignore.
  - `develop --library DIR --ids 1,2|all [--keys light,wb] [--diff]`: develop values side by side.
  - `commands WORD…`: registry ids and full params. There is no `describe` command.
- **`lc_verify.py`** prints JSON and exits 1 when a check fails.
  - `hash DIR > m.json` then `hash DIR --compare m.json`: the originals are untouched.
  - `files DIR --count N --ext jpg --long-edge 2048`: export count, format and size, via `sips`.
  - `same --library DIR --ids 1,2,3`: develop settings are identical, crop, masks and spots excepted.

## Workflow

1. **Snapshot the originals.** Run `lc_verify.py hash IN > manifest.json` before
   importing. Import with the default `mode=add` (files referenced in place). Never use
   `move`, `photo.deletePermanently` or `library.emptyRecentlyDeleted` unless the user
   asked for it.
2. **Import and count.** After `--import`, check `lc_query.py photos`: byte-identical
   files are skipped as duplicates without an error. Work with the ids it prints.
3. **Look up what you haven't used** with `lc_query.py commands <words>`. Note whether
   the params list `ids?`. If they don't, the command works on the **active photo
   only**, so wrap it in `forEach`.
4. **Do the job as one `lc_run.py` step list.** Use absolute paths, and create the
   export folder first.
5. **Read back.** Use `lc_query.py develop` for values, `lc_query.py photos` for
   ratings, keywords and flags, `lc_verify.py files` for exports, `lc_verify.py same`
   after a sync, and `hash --compare` for the originals.
6. **Look at it.** Open one or two exported files (Read the image) to confirm the look
   matches the request: not black, not blown out, the preset is visible.
7. **Report** the output paths, the counts, the real sizes from the export reply, what
   was verified, and anything skipped (duplicates, clamped values).

## The traps that cost the most (details in [gotchas.md](references/gotchas.md))

- **Active-photo commands ignore `ids` and the selection.** This covers `develop.auto`,
  `develop.adjust`, `develop.wb`, `develop.profile` and `develop.treatment`.
  `selectAll` then `develop.auto` tones **one** photo and still says `ok`. Use `forEach`.
- **`develop.autoSync` + `develop.auto` copies one photo's auto values to all of
  them.** It does not auto-tone each photo. Real per-photo auto tone is `forEach` →
  `develop.auto`.
- **`develop.set` is absolute.** "Auto, then +0.5 EV" is
  `develop.quickAdjust {control: "light.exposure", delta: 0.5, ids}`, which works from
  each photo's own value. `set value=0.5` would wipe the auto exposure.
- **Copy and paste must happen in one process.** `develop.paste` in a later `run` fails
  with "no settings copied". Use `select → develop.copy → develop.paste {ids}`, or
  `select {ids, active} → develop.sync`, in one step list.
- **`app.export` takes `dir=` for a folder.** `path=/some/folder` is taken as a file stem
  and writes PNGs into the **current directory**. Always pass `format`. `longEdge`
  defaults to 3000, and exports are never upscaled.
- **Re-exporting into the same folder adds `-2`, `-3` copies** (`conflict=unique`).
  Use a fresh folder, or `conflict=overwrite` in your own output folder.
- **Unknown filter keys match everything**, and `rating` means "at least". `lc_query.py`
  guards both (`--op exactly`).
- **Out-of-range values are clamped silently** (exposure 9 → 5), so read them back.
- **One process per library.** A second `run` on an open library fails ("already
  open"). Run jobs for one library one after another, and ask the user to close it in
  the app if needed.

## Common jobs

- **Import → auto tone → nudge → export**, **copy a look to the rest**, **cull and
  list**, **raw white balance/profile/preset**, **web export with watermark**, **HDR
  merge**: all are worked out in [recipes.md](references/recipes.md).
- **Library questions** ("how many picks from June?", "which photos have the keyword
  X?"): run `lc_query.py photos` with filters, or `lightcraft-cli run --library DIR
  catalog.stats`. Report the total and the filter used.

## References

- [references/cli.md](references/cli.md): `run`, `render`, `merge`, `snapshot`, libraries
  and locks, exit status.
- [references/commands.md](references/commands.md): the pinned command ids by task, with
  params, filter keys, settings groups and control ids.
- [references/recipes.md](references/recipes.md): step lists for each common job.
- [references/gotchas.md](references/gotchas.md): everything that fails silently, and
  the live-port security note.
