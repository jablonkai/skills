# Gotchas (FilmCraft 0.13.0)

Everything here was hit while building the skill. Most of these fail **silently**: exit 0,
a plausible result, wrong output.

## Saving

- **`run`, `exec` and `import` without `--save` or `--save-as` discard everything** and
  still exit 0 with `"ok": true` on every line.
- **A failing `run` line stops the run, and nothing is saved**, including the successful
  lines before it. `--keep-going` skips the bad line and saves the rest, which you rarely
  want for an edit.
- **`export` and `render` ignore `--save`/`--save-as`.** They exit 0 and write no project.
  Save the edit with `run`, or with `fc_run.py`, first.
- `--save` writes over `--project`. Save to a new file unless the user asked for an
  in-place edit. `fc_run.py` refuses to overwrite.
- `file.saveAs` inside the session works (`fc_run.py` uses it) and returns
  `{path, bytes}`.

## Active sequence

- **Every `file.newSequence` (and `fromItem`) makes the new sequence active.** `export`,
  `render`, `inspect sequence`, `markers.*` and `markIn`/`markOut` all act on the active
  sequence. Create the delivery sequence last, or `sequence.open {item}` before the steps
  that need it.
- **An empty sequence exports a valid 1-frame file** (0.04 s) with exit 0.
  `fc_export.py` refuses when the sequence has no clips.
- `file.newSequence` defaults to **23.976 fps**. With 25 fps footage that gives a
  mismatched timeline. Pass `fps` (and the size), or use `fromItem`.

## Export

- **With in/out set, the default range is in/out**, for `--preset` and `--format` alike.
  Always pass `--range entire` or `inOut` explicitly.
- **In/out is inclusive of the out frame.** In 1 s → out 9 s gives 201 frames at 25 fps.
  `range: "custom"` with `startSeconds`/`endSeconds` is end-exclusive (2–4 s → 50 frames).
- **`--scale` is ignored by fixed-size presets** (YouTube, Vimeo, High Quality, Social
  Vertical, GIF). The file comes out at the preset size with no warning. Use
  `width`/`height` in `file.exportMedia`, which `fc_export.py` does for `@SCALE`, or a
  Match Source preset or `--format`. `--settings` keys are not `width`/`height`
  (`unknown key`). See `export.presets.get` for its schema.
- **The output file is overwritten and missing folders are created** without a prompt.
- **Offline media renders as placeholder frames.** The CLI exits 1 and lists the items
  in `offlineMedia` with `status: missing`. Relink (`file.import` with `replace`) or fix
  the paths. Use `--allow-offline` only when the user accepts placeholders.
- Container durations from ffprobe run slightly long (12.010 s for 300 frames) because of
  audio priming. Compare **frame counts**, not seconds.
- Rendering a sequence with titles or transitions creates a **`FilmCraft Previews/`**
  folder next to the `.fcproj` (preview render cache). It is FilmCraft's, not an export.
  Leave it, or tell the user it is there if they asked for a clean output folder.
- In `filmcraft-cli run`, `file.exportMedia` waits for the file. Through MCP
  (`fc_run.py`), the job is
  asynchronous: without `"wait": true` the session ends and **the file is never
  written**. `fc_run.py` adds `wait: true` unless you set it.

## Ids and parameters

- **Ids come from results.** `file.import` → `items`, `file.newSequence` → `sequence`,
  `timeline.place` → `placed: [[video, audio], …]`, `graphics.newText` → `clip`. A wrong
  clip id gives confusing errors (`no edit point at the playhead on targeted tracks`), not
  "no such clip". Use `"as"` / `$ref` in `fc_run.py`.
- Ids are allocated in order and **change with every edit**, so never hard-code an id seen
  in a different project or before a razor.
- **`markers.add` without `time` adds the marker at the playhead** (frame 0 headless).
  It succeeds, so a list of markers piles up at 0. Its documented time param is `time`
  (ticks).
- **Marker colours are label names**: Violet, Iris, Caribbean, Lavender, Cerulean,
  Forest, Rose, Mango, Purple, Blue, Teal, Magenta, Tan, Green, Brown, Yellow. `Red` and
  `Orange` fail the step (`unknown marker color`).
- `timeline.razor` with a time outside the clips, or a non-number, returns `{cuts: 0}`
  and succeeds.
- An unknown transition or effect name fails (`unknown transition`). List them with
  `exec effects.list kind=VideoTransition`.

## Titles

- `graphics.newText` goes on **the lowest video track free over its whole span**: V2 on
  an empty V2, V3 when B-roll occupies V2 at that time. Pass `track` when the track
  matters. It is a **0-based index (1 = V2, 2 = V3)**. An occupied track fails
  (`V2 is not free here`). An index past the last track, or a name such as `"V2"`, is
  **ignored**, and the title is auto-placed.
- New text is point text whose **left baseline sits at the frame centre**, so it looks
  off-centre. Centre it with `graphics.align` `hcenter` and then `vcenter`, or pass
  `position`. Check with `render` and look at the PNG.
- A title clip's `name` in `inspect` is its text, and it has a `Graphic` project item.

## Live app and bridge

- `--bridge 127.0.0.1:PORT` talks to an app the user started with `filmcraft --control
  PORT`. `filmcraft-cli help` documents no authentication for that channel, so any local
  process can drive the app while it listens. This skill never starts it. If the user
  wants a live session, they start it, and they stop it by quitting the app or relaunching
  it without `--control`.
- With the project open in the app, a headless `--save` to the same file races the app's
  own save. Save headless to a new file, or ask the user to close the project.
