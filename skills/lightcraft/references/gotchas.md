# LightCraft gotchas (verified on lightcraft-cli 0.17.0)

Everything here was reproduced against the real CLI. Most of these fail **silently**:
the command replies `"ok": true` and exits 0, and the result is still wrong. That is
why the workflow reads every result back.

## Contents

- [Active photo vs ids](#active-photo-vs-ids)
- [Auto tone](#auto-tone)
- [Absolute vs relative values](#absolute-vs-relative-values)
- [One process per dependent sequence](#one-process-per-dependent-sequence)
- [Export paths, formats and re-runs](#export-paths-formats-and-re-runs)
- [Import](#import)
- [Queries and filters](#queries-and-filters)
- [Originals and sidecars](#originals-and-sidecars)
- [Exit status](#exit-status)
- [Live app port](#live-app-port)

## Active photo vs ids

Some commands take `ids` (`develop.set`, `develop.quickAdjust`, `develop.paste`,
`develop.reset`, `preset.apply`, `photo.rate`, `photo.flag`, `photo.label`,
`photo.setMeta`, `app.export`). Others act on the **active photo only**: `develop.auto`,
`develop.adjust`, `develop.wb`, `develop.profile`, `develop.treatment`, `develop.curve`
and most `crop.*`, `mask.*` and `spot.*` commands.

- An `ids` param passed to an active-photo command is **ignored without an error**.
  `develop.wb mode=daylight ids=[2]` changed photo 1, the active one.
- A multi-selection does not help either. `library.selectAll develop.auto` tones only
  the active photo and leaves the other four at zero.
- Fix: one `library.select {ids:[n], active:n}` per photo, followed by the command.
  `lc_run.py`'s `forEach` writes that loop for you.
- Check the signature in the registry (`lc_query.py commands <id>`). If `ids?` isn't
  listed, the command works on the active photo.

## Auto tone

- `develop.auto` computes the values from **the photo's own content**. On 5 different
  images it gave exposures of −1.04, −1.09, −0.84, −1.16 and +0.53.
- `develop.autoSync on=true` followed by `develop.auto` does **not** auto-tone each
  photo. It copies the active photo's auto result to every selected photo, so all five
  get −0.54. Use it only when the user wants the same values everywhere.
- `develop.autoSync` is a mode switch (`{on}`, toggles when omitted), not an action.
  Leave it off.
- The auto result is in the reply (`exposure`, `contrast`, `highlights`, `shadows`,
  `whites`, `blacks`, `vibrance`, `saturation`). Keep it if the task asks for "auto +
  something".

## Absolute vs relative values

- `develop.set control=light.exposure value=0.5` sets the value **to** 0.5. After an
  auto tone of −1.04, the result is +0.5, not −0.54.
- "Auto tone and +0.5 EV" means relative to the auto result. Use
  `develop.quickAdjust {control, delta, ids}`, which adds to each photo's own value, or
  `develop.adjust {control, delta}` on the active photo.
- `develop.quickAdjust` is the only relative command that takes `ids`.

## One process per dependent sequence

- Each `lightcraft-cli run` is a new process. The develop **clipboard is lost** at the end
  of a run: `develop.paste` in a second `run` fails with "no settings copied".
- The selection **is persisted** (`view.json` in the library). A later run that relies on
  "the active photo" may hit a photo picked several runs ago. Select explicitly in every
  run.
- Filters (`library.filter`) are **not** persisted.
- Put `select → copy → select → paste` (or `select → develop.sync`) in one `run` or one
  `--script`. `lc_run.py` always uses one process.

## Export paths, formats and re-runs

- **`app.export path=<folder>` treats the folder as a file stem.** With `path=/x/out`,
  LightCraft wrote `p0.png`, `p1.png`… into the **current directory**, as PNG, with
  `ok: true`. For a folder use `dir=<folder>`, and always pass `format`.
  Re-checked on 0.17.0: with one id the file is written as a PNG named exactly the stem
  (no extension); with several ids it still writes `p1.png`, `p2.png` into the cwd.
- Create the `dir` first. Use absolute paths.
- `conflict` defaults to `unique`. Exporting again into the same folder adds
  `IMG_0001-2.jpg`, `-3`… silently. That doubles the file count on a retry. Export into
  a fresh folder, or pass `conflict=overwrite` when re-running into a folder you own.
- `longEdge` defaults to **3000**, not full size (`longEdge=0` is full size). Exports
  are not upscaled: `longEdge=5000` on a 3000 px source gave 3000 px, with or without
  `dontEnlarge`. The reply's `width`/`height` show the real size, so report them, not
  the requested one.
- `quality` is 1..100 (default 92).
- `metadata` defaults to `all`. Pass `metadata=allExceptCamera` or `removeLocation=true`
  for public sharing.

## Import

- **Byte-identical files are skipped as duplicates without an error**: 5 copies of
  one JPEG imported as `total: 1`. Check `catalog.query` totals after every import.
- The default `mode=add` references files in place, which is what you want for "leave the
  originals alone". `copy` and `move` relocate files into
  `<library>/Originals/YYYY/YYYY-MM-DD/`, and `move` deletes the sources after
  verification. Use `move` only when the user asked for it.
- `--import PATH` is repeatable and recursive for folders. Re-running with the same
  `--import` re-checks and finds duplicates, so it is harmless but slow on big folders.
- `captured` comes from EXIF. With no EXIF date, LightCraft uses the file date.

## Queries and filters

- **Unknown filter keys are ignored**, so the query matches everything. `{"keywords":
  "x"}` (plural) returned all 5 photos. `lc_query.py` refuses unknown keys.
- `rating` means **at least** by default (`ratingOp: atLeast`). "Photos rated 3" needs
  `ratingOp: exactly`. For 5 it makes no difference.
- Dates: `date: "YYYY-MM-DD"` (or `"YYYY"`, `"YYYY-MM"` prefixes), or `dateFrom`/`dateTo`.
  An object such as `{"year": 2024}` is an error.
- `catalog.query` takes `offset`/`limit`, and `total` is always the full match count.
  Compare `len(photos)` with `total`, or page with `offset` (`lc_query.py photos` does),
  so a long list can't be cut off silently.
- `keyword` matches the keyword name **case-insensitively** (`beach` finds `Beach`).
  Keywords are stored as typed.
- `catalog.stats` gives totals per date, picks, rejects and edited counts. It's quicker
  than paging when only numbers are needed.

## Originals and sidecars

- Develop edits live in the library (`catalog.snap`/`catalog.log`). The image files are
  never rewritten, and with default settings no XMP sidecar appears next to them.
- `library.toggleAutoWriteXmp` and `photo.saveMetadataToFile` **do** write next to the
  originals (XMP, or into DNG/JPEG metadata). Use them only on request.
- `photo.delete` moves photos to the library's *Recently Deleted*.
  `photo.deletePermanently` and `library.emptyRecentlyDeleted` remove files from disk.
  Never call them without an explicit request.

## Exit status

- `run` exits **1** when any command fails, and stops at the failed command unless
  `--keep-going` is set. The failing reply is `{"ok": false, "error": "..."}`.
- An unknown control id fails (`unknown control 'light.nope'`). An unknown photo id fails
  (`no such photo PhotoId(99)`). An unknown **param** on a command that does not take it
  is often **ignored** (see `ids` above), while `app.export` rejects unknown params.
- Piping `run` into `grep`/`head` hides the exit status. Keep the replies, or use
  `lc_run.py`, which reports `failed` and exits 1.

## Live app port

- `LightCraft --control PORT` (and `lightcraft-cli run --connect`) is a JSON-lines
  channel on 127.0.0.1 **with no authentication** in 0.16.0 (not re-checked in 0.17.0: that needs the GUI app). Any local process can
  drive the app and read the library through it.
- This skill does not start it or connect to it. If the user insists on watching the
  edits live, say this plainly, let them start the app with `--control` themselves, and
  have them close it afterwards.
