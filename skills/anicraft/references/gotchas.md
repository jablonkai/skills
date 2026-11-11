# Gotchas (AniCraft 0.2.0)

Each of these was hit while building the skill.

## Frames
- **CLI 1-based, engine 0-based.** `render --frame 30` renders index 29;
  `exec … '{"frame":30}'` targets timeline frame 31. Export `from`/`to` are 0-based and
  inclusive (`to: 10` → 11 frames). In `ac_build.py` specs everything is 1-based.
- `insert_frame {frame}` on a layer **shorter** than the frame extends it to that frame;
  on a layer that already covers it, it **inserts** a frame there (30 → 31). Set the movie
  length once, on the first layer, then check `frames`. New layers (`layer.new`,
  `camera.add`, `file.import`) already span the whole movie.
- Frames nested in action lists (`goto_and_play {frame}`) are passed through unchanged by
  `ac_build.py`; prefer labels for goto targets.

## Where commands land
- **Playhead**: `draw.*`, `text.create`, `file.import`, `library.place`, paste draw into the
  active layer at the playhead. `insert_blank_keyframe {frame}` / `insert_keyframe` do
  **not** move it, so a following `draw.ellipse` silently lands on the old keyframe. Use
  `"on": {"layer", "frame"}` (= `layer.select` + `timeline.goto`).
- **Active layer**: `camera.add`, `layer.new`, `file.import`, `bone.add` change it. A later
  command without `layer` hits the new one: `actions.set {frame: 30}` after `camera.add`
  went onto the camera layer.
- **Keyframe that contains the frame**: `actions.set`, `script.set`, `set_easing`,
  `set_label` act on the keyframe whose span holds the frame. On a one-key layer that is
  frame 1 — `stop` there halts the movie at once. Insert a keyframe first.
- **Selection**: a drawn shape stays selected; `convert_to_symbol`, `text.edit`,
  `swap_bitmap`, `set_transform` act on the selection. `edit.deselect` between parts.
  `element.select` needs `ids` (no `all`); use `edit.select_all` or
  `layer.select {layer, select: true}`.

## Tweens
- A motion tween is a `motion` object (`info`: `"motion": ["x","y"]`, `"tween": null`).
  Ease it with `motion.set_ease`; `timeline.set_easing` errors "this span has no tween".
- `create_motion_tween` on several objects groups them into one graphic symbol; on a
  one-frame span it grows the span to one second.
- Shape tweens need raw shapes on both ends; hints are inactive until both ends are
  placed, and `move_hint` fails if the side's keyframe has no shape ("no shape on that
  keyframe") — usually because the end shape was drawn on the wrong keyframe.
- No bounce/elastic easing — eight presets only (see recipes).

## Camera and bones
- `camera.set {frame}` without a camera keyframe at that frame changes the whole span
  (zoom 140 everywhere). Key it, then `create_tween` on the camera layer.
- A camera zoom crops the stage edges: at zoom Z only stage/Z around the camera centre
  is seen. Objects near the edges at the zoomed end are cut off — move them inward and
  run `ac_verify.py edges … --color <fill>`.
- `camera.add` is a no-op if a camera exists (`added: false`).
- Bone ids are integers from `bone.add`; names are labels only. Limits clamp poses
  silently. `bone.remove` with more than one pose asks for confirmation.
- After rigging, the parts live on `Armature_1`; the original layer is left empty
  (harmless, but `ac_verify.py doc --layer` sees it).

## Files and params
- `draw.*` shapes get a default 2 px dark (`#1b2a4a`) stroke; pass `"stroke": null` for a
  fill-only shape (matters for clean shape tweens and flat-colour art).
- Colours: `#rrggbb` only (`#e33` → "must be a colour like #ff8800").
- Overwrite needs `"confirm": true` (`file.save_as`, exports); serve returns an error
  instead of prompting.
- `serve` keeps going after an error. `ac_build.py` stops and saves nothing.
- `info` counts elements; element detail (text content, bitmaps, transforms) is only in
  the saved JSON — `ac_inspect.py` reads it.
- Unknown param names are ignored, not rejected: `camera.set {"zooom": 50}` succeeds and
  changes nothing. Check the result values, not just `ok`.
- Drawing while the camera layer is active fails ("'Camera' is the camera layer") — pass
  `on.layer` after `camera.add`.
- No `.fla`/XFL import. Import is SVG, PNG/JPG and WAV/OGG/MP3 only.
- Video export needs ffmpeg; set `ANICRAFT_FFMPEG` or pass `ffmpeg` when it isn't on PATH.
