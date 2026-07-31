# Rebelle JSON event reference

The event vocabulary is shared by both control paths: Motion IO reads it from a file,
the WebSocket server accepts the same objects one per message. Condensed from the
official [JSON Events Reference](https://www.escapemotions.com/products/rebelle/motionio_doc/reference/json_events_reference)
(Rebelle 8.3), with behaviour notes verified against the installed build.

## Contents

- [File structure](#file-structure)
- [Canvas: NEW_ARTWORK, SET_PAPER](#canvas)
- [Brush: SET_BRUSH and friends](#brush)
- [Painting: POINTER_PRESS / MOVE / RELEASE](#painting)
- [Simulation and drying](#simulation-and-drying)
- [Masks and layers](#masks-and-layers)
- [Data in and out: LOAD, SAVE](#data-in-and-out)
- [Engine and housekeeping](#engine-and-housekeeping)
- [Tool ↔ paint type matrix](#tool--paint-type-matrix)

## File structure

```json
{"frames": [
  {"events": [ {"event_type": "..."}, ... ]},   // frame 0
  {"events": [ ... ]}                            // frame 1
]}
```

One frame = one rendered image + one implicit fluid-simulation step. Unknown keys are
ignored, so `"comment"` fields anywhere are free documentation. Over the WebSocket there
are no frames — you send the event objects themselves and the app runs continuously.

## Canvas

### NEW_ARTWORK

```json
{"event_type": "NEW_ARTWORK", "width": 1200, "height": 800,
 "units": "px",                                    // px | in | cm, default px
 "dpi": 200,
 "paper": {"preset": "Handmade/HM01 Handmade",     // "<Category>/<Name>" or absolute path
           "color": {"r": 255, "g": 255, "b": 255},
           "deckled_edges": true, "paper_scale": 100, "visible": true}}
```

In batch this event is fragile — see the placement rules in SKILL.md. Over the
WebSocket it just works, and it replaces the artwork the user has open.

### SET_PAPER

Same parameters as the `paper` block above, as a top-level event. Changes the paper of
the existing artwork.

## Brush

### SET_BRUSH

Sets tool, preset and parameters in one go. `preset` is required — without it Rebelle
logs `ERROR: Preset for brush was not set` and the following strokes do nothing.
Anything not named keeps its previous value, but loading a preset can itself change
size/water/opacity/paint type.

```json
{"event_type": "SET_BRUSH", "tool": "WATERCOLOR", "preset": "Watercolor/Round",
 "size": 40, "size_px": 40,        // use one or the other
 "water": 55, "opacity": 60, "pressure": 100,
 "paint_type": "PAINT",            // BLEND | PAINT | PAINT_BLEND | PAINT_MIX | ERASE
 "glaze_mode": "TRANSPARENT",      // WATERCOLOR only: TRANSPARENT | SEMI-OPAQUE | OPAQUE
 "color": {"r": 255, "g": 128, "b": 0},
 "dirty_brush": false,             // OIL_AND_ACRYLIC only
 "smudge_only_wet": false,         // SMUDGE
 "keep_layer_wet": false, "keep_water": true,   // tools with ERASE paint type
 "only_water": false,              // WATERCOLOR/INK_PEN: paint water only
 "multi_color_brush": false, "rotate_multi_color_brush": false,
 "smudge": true, "spacing": 50, "opacity_multiplier": 2}   // override preset (needs "preset")
```

Tools: `WATERCOLOR`, `OIL_AND_ACRYLIC`, `EXPRESS_OIL`, `INK_PEN`, `PENCIL`, `PASTEL`,
`MARKER`, `AIRBRUSH`, `BLEND`, `SMUDGE`, `CLONE`, `ERASER`, `WATER`, `DRY`, `BLOW`.

Preset paths are `"<Subfolder>/<Name>"` **inside the tool's own folder** — they are not
prefixed with the tool. See [assets.md](assets.md) for how to list what is installed.

### Narrower setters

`SET_TOOL` `{tool}` · `SET_BRUSH_PRESET` `{preset}` · `SET_BRUSH_PARAMS`
`{size|size_px, water, opacity, pressure, dirty_brush}` · `SET_PAINT_TYPE` `{paint_type}` ·
`SET_GLAZE_MODE` `{glaze_mode}` · `SET_CLONE_PICK_POS` `{pos}` (clone source, set before
the first clone stroke).

None of these are recommended mid-stroke; switching tools also drops the previous tool's
parameters.

### SET_BRUSH_COLOR

```json
{"event_type": "SET_BRUSH_COLOR", "color": {"r": 255, "g": 0, "b": 0}}
```

Colours are 8-bit even though the engine mixes in 16-bit internally. Setting a colour
turns off an active `reveal_mask`.

With `multicolor` it also loads a multi-colour brush texture (Rebelle 5+): `seed`,
`threshold` (0–1), `scale_with_brush`, `scale`/`offset` (either `x`/`y` or `x_range`/
`y_range` `{min,max}` for random values), and `multi_color_list` — a list of
`{color, threshold, scale, offset, scale_with_brush}` entries that override the
top-level values per colour. Sending it without `color` adds colours on top of the
existing texture instead of refilling it.

### EDIT_BRUSH_PRESET

Edits a preset file on disk (8.1.3+); it does not load it — follow with `SET_BRUSH`.

```json
{"event_type": "EDIT_BRUSH_PRESET",
 "preset_path_in": "preset.rebelle-brush.png",
 "preset_path_out": "out.rebelle-brush.png",   // optional, defaults to overwriting
 "shape": "shape.png", "shape_1": "", "grain": "grain.jpg",
 "params": { }}                                 // omitted params reset to defaults
```

Editable slots: `params`, `shape`, `shape_1..3`, `grain`, `grain_1..3`,
`background_texture`, `background_texture_1`, `dual_brush`, `shape_border`. An empty
path removes a texture. Shape and grain counts must match.

## Painting

```json
{"event_type": "POINTER_PRESS",  "pos": {"x": 400, "y": 0}, "pressure": 0.6,
 "pen_tilt": {"x": 60, "y": -45}, "rotation": 45.0, "stroke_id": 25}
{"event_type": "POINTER_MOVE",   "pos": {"x": 450, "y": 50}, "pressure": 0.8,
 "dissipation": 0.5, "paint_ratio": 1.0, "mix_ratio": 0.2}
{"event_type": "POINTER_RELEASE","pos": {"x": 450, "y": 50}, "pressure": 0.0}
```

- Coordinates are canvas pixels, origin top-left, and may fall outside the canvas.
- **A move draws the previous segment.** The release must repeat the last move's
  position or the final segment never appears.
- Keep the same optional fields on every event of a stroke — mixing e.g. tilt in and out
  mid-stroke makes the brush behave erratically.
- `stroke_id` ties split sub-strokes together so they share the preset's random start.
- `dissipation`/`paint_ratio`/`mix_ratio` (Rebelle 5+) override the preset's paint curves
  per event. The resulting brush colour is
  `C_final = C_bottom*mix_ratio + C_dis*paint_ratio + C_prev*brush_ratio`, where
  `C_dis` blends the multicolor texture with the palette colour by `dissipation` and
  `brush_ratio` is whatever is left of 1.

## Simulation and drying

- `{"event_type": "SIMULATION", "repeats": 10}` — extra fluid steps inside a frame
  (each frame already ends with one). Only wet media care.
- `{"event_type": "FAST_DRY"}` — remove water, canvas stays wet.
- `{"event_type": "DRY"}` — remove water, canvas ends dry.
- `{"event_type": "WET_LAYER"}` — the Layers panel "wet the layer" action.

## Masks and layers

- `CLEAR_LAYER` — clears everything by default; set any of `rgba_dry`, `rgba_wet`,
  `wetness`, `water`, `bump_dry`, `bump_wet`, `velocity`, `reveal_mask`,
  `selection_mask`, `stencil_mask` to `false` to preserve it. With `selection_mask`
  true (the default) it behaves like pressing Del and the other flags are ignored.
- `CLEAR_MASK` — `{"stencil_mask": true}` by default; also `selection_mask`,
  `reveal_mask`.
- `LOAD_MASK` — removed in Rebelle 5; use `LOAD` with `selection_mask`/`stencil_mask`.

Use only one of `selection_mask`/`stencil_mask` at a time: a selection mask is copied
into the stencil mask internally, so setting both leaves undefined behaviour.

## Data in and out

`LOAD` and `SAVE` take one object per data layer. **Rejected over the WebSocket in
8.3** ("SAVE and LOAD events aren't supported via Websockets yet") — batch only.

```json
{"event_type": "LOAD",
 "rgba_dry": {"filename": "in/bg.exr", "blending": "NORMAL"},
 "water":    {"filename": "in/water.exr", "function": "add",
              "multiplier": 1.2, "scaling": 2.3,
              "wait_for_file_timeout_seconds": 10}}

{"event_type": "SAVE",
 "rgba_canvas": {"filename": "out/frame.png", "scaling": 1.0},
 "velocity":    {"filename": "out/vel.exr", "options": "tiled_mipmapped"}}
```

Layers, functions and options are listed in [batch.md](batch.md#data-layers).

## Engine and housekeeping

```json
{"event_type": "SET_ENGINE_PARAMS",
 "absorbency": 5, "re_wet": 5, "texture_influence": 5, "edge_darkening": 5,
 "create_drips": true, "drip_size": 5, "drip_length": 5,
 "impasto_depth": 5, "gloss": 5, "paper_texture": 5, "paint_texture": 5,
 "gran_enabled": true, "gran_strength": 5, "gran_contrast": 5, "gran_texture": 1,
 "paused": false, "show_wet": false, "realshader": true, "nanopixel": true}
```

Ranges are 0–10 (`drip_*` 1–10, `gran_texture` 0–4). These are the Visual Settings
panel. `realshader`/`nanopixel` (8.3+) affect `rgba_canvas` exports.

- `SET_CANVAS_TILT` `{"tilt": {"x": 0.75, "y": 0.0}, "enabled": 1}` — direction of fluid
  flow, changeable at any time, `x`/`y` in −1…1.
- `SET_PIGMENTS` `{"enabled": true}` — real pigment mixing.
- `SET_RANDOM_SEED` `{"seed": 12345}` — makes a render reproducible. Rebelle logs the
  seed it picked when you don't set one.
- `GROUP` `{"events": [...]}` — purely for folding a long file in an editor.
- `BOOKMARK` `{"id": "...", ...}` — echoed to stdout (batch) or back over the socket
  (live) when reached. The only way to know where processing actually is.
