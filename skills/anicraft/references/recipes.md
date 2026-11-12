# Recipes (ac_build.py specs)

All specs are run as `python3 $S/ac_build.py spec.json` and use **1-based frames**.
Every recipe here was run on AniCraft 0.2.1; ids in results (`$name.key`) are what the
engine returned.

## Contents
- [Bouncing ball on a motion path, squash, camera zoom](#bouncing-ball)
- [Bone rig with limits and a posed wave](#bone-rig)
- [Shape tween with hints](#shape-tween-with-hints)
- [Edit a supplied file: text, bitmap, stop action](#edit-a-supplied-file)
- [Classic tween, labels, layers, sounds](#more-building-blocks)

## Bouncing ball

```json
{"new": {"width": 1080, "height": 1080, "fps": 30, "background": "#f4f1ea"},
 "out": "ball.anicraft",
 "steps": [
  {"cmd": "layer.rename", "params": {"name": "Ball", "layer": "$layer:Layer 1"}},
  {"cmd": "draw.ellipse", "on": {"layer": "$layer:Ball", "frame": 1},
   "params": {"x": 160, "y": 240, "w": 120, "h": 120, "fill": "#e4572e", "stroke": null}},
  {"cmd": "modify.convert_to_symbol", "params": {"name": "Ball", "kind": "graphic"}, "as": "ball"},
  {"cmd": "timeline.insert_frame", "params": {"layer": "$ball.layer", "frame": 30}},
  {"cmd": "timeline.create_motion_tween", "params": {"layer": "$ball.layer", "frame": 1}},
  {"cmd": "motion.set_path", "params": {"layer": "$ball.layer", "frame": 1,
                                        "d": "M220 300 Q540 1500 860 300"}},
  {"cmd": "motion.set_ease", "params": {"layer": "$ball.layer", "frame": 1, "easing": "ease-in-out"}},
  {"cmd": "motion.set_key", "params": {"layer": "$ball.layer", "property": "scale_y", "value": 100, "frame": 14}},
  {"cmd": "motion.set_key", "params": {"layer": "$ball.layer", "property": "scale_y", "value": 70, "frame": 16}},
  {"cmd": "motion.set_key", "params": {"layer": "$ball.layer", "property": "scale_x", "value": 125, "frame": 16}},
  {"cmd": "motion.set_key", "params": {"layer": "$ball.layer", "property": "scale_y", "value": 100, "frame": 18}},
  {"cmd": "motion.set_key", "params": {"layer": "$ball.layer", "property": "scale_x", "value": 100, "frame": 18}},
  {"cmd": "camera.add"},
  {"cmd": "timeline.insert_keyframe", "params": {"layer": "$layer:Camera", "frame": 30}},
  {"cmd": "camera.set", "params": {"zoom": 130, "frame": 30}},
  {"cmd": "timeline.create_tween", "params": {"layer": "$layer:Camera", "frame": 1, "easing": "ease-in-out"}},
  {"cmd": "file.export_video", "params": {"path": "out/ball.mp4"}},
  {"cmd": "file.export_gif", "params": {"path": "out/ball.gif", "scale": 0.5}}
 ],
 "renders": {"dir": "out/frames", "frames": [1, 15, 30]}}
```

- A drawn shape is selected, so `convert_to_symbol` right after it converts just that
  shape. It returns `{symbol, instance, layer}`.
- `create_motion_tween` makes a motion object on the span (`info` shows `motion`, not
  `tween`). `motion.set_path` takes SVG path data in stage px; its ends become the start
  and end positions. `motion.orient {"orient": true}` turns the object along the path.
- Squash = `scale_x`/`scale_y` keys (percent) around the impact frame; hold keys either
  side keep the squash short. Other properties: `x y rotation skew alpha tint`.
- Easing (motion, classic and shape tweens): `Linear QuadIn QuadOut QuadInOut CubicIn
  CubicOut CubicInOut Smooth`; `linear`, `ease-in`, `ease-out`, `ease-in-out` are aliases
  for the quad ones. No bounce/elastic presets — build a bounce from keys instead.
- **Framing under a camera zoom**: at zoom Z the camera sees stage/Z around its centre —
  at 130 % on 1080², x and y 125…955. The path above starts and ends at x 220/860, y 300 so
  the 120 px ball (radius 60) stays inside at frame 30; the quadratic's lowest point is
  y = (300 + 2·1500 + 300)/4 = 900, so the ball's bottom touches a floor at 960. Check
  with `ac_verify.py edges ball.anicraft --frames 1 15 30 --color #e4572e`.
- The camera layer has one element; keyframe it like any layer. Check:
  `ac_verify.py doc ball.anicraft --camera 1:zoom=100 --camera 30:zoom=130`.

## Bone rig

Parts are separate movie-clip (or graphic) instances; bones join them parent → child.

```json
{"new": {"width": 800, "height": 800, "fps": 30}, "out": "rig.anicraft",
 "steps": [
  {"cmd": "draw.rect", "on": {"layer": "$layer:Layer 1", "frame": 1},
   "params": {"x": 300, "y": 300, "w": 120, "h": 220, "fill": "#3d5a80"}},
  {"cmd": "modify.convert_to_symbol", "params": {"name": "Torso", "kind": "movie_clip"}, "as": "torso"},
  {"cmd": "edit.deselect"},
  {"cmd": "draw.rect", "params": {"x": 420, "y": 310, "w": 120, "h": 34, "fill": "#98c1d9"}},
  {"cmd": "modify.convert_to_symbol", "params": {"name": "UpperArm", "kind": "movie_clip"}, "as": "upper"},
  {"cmd": "edit.deselect"},
  {"cmd": "draw.rect", "params": {"x": 540, "y": 312, "w": 100, "h": 30, "fill": "#98c1d9"}},
  {"cmd": "modify.convert_to_symbol", "params": {"name": "LowerArm", "kind": "movie_clip"}, "as": "lower"},
  {"cmd": "edit.deselect"},
  {"cmd": "draw.ellipse", "params": {"x": 640, "y": 305, "w": 44, "h": 44, "fill": "#ee6c4d"}},
  {"cmd": "modify.convert_to_symbol", "params": {"name": "Hand", "kind": "movie_clip"}, "as": "hand"},
  {"cmd": "bone.add", "params": {"from": "$torso.instance", "to": "$upper.instance", "head": [420, 327], "name": "shoulder"}, "as": "shoulder"},
  {"cmd": "bone.add", "params": {"from": "$upper.instance", "to": "$lower.instance", "head": [540, 327], "name": "elbow"}, "as": "elbow"},
  {"cmd": "bone.add", "params": {"from": "$lower.instance", "to": "$hand.instance", "head": [640, 327], "name": "wrist"}, "as": "wrist"},
  {"cmd": "bone.set_limits", "params": {"bone": "$shoulder.bone", "constrain": true, "min": -150, "max": 20}},
  {"cmd": "bone.set_limits", "params": {"bone": "$elbow.bone", "constrain": true, "min": -120, "max": 0}},
  {"cmd": "bone.set_limits", "params": {"bone": "$wrist.bone", "constrain": true, "min": -45, "max": 45}},
  {"cmd": "timeline.insert_frame", "params": {"layer": "$shoulder.layer", "frame": 60}},
  {"cmd": "bone.pose", "params": {"bone": "$shoulder.bone", "angle": -110, "frame": 1}},
  {"cmd": "bone.pose", "params": {"bone": "$elbow.bone", "angle": -40, "frame": 1}},
  {"cmd": "bone.pose", "params": {"bone": "$elbow.bone", "angle": -90, "frame": 30}},
  {"cmd": "bone.pose", "params": {"bone": "$wrist.bone", "angle": 30, "frame": 30}},
  {"cmd": "bone.pose", "params": {"bone": "$elbow.bone", "angle": -30, "frame": 60}},
  {"cmd": "bone.pose", "params": {"bone": "$wrist.bone", "angle": -30, "frame": 60}},
  {"cmd": "file.export_png_sequence", "params": {"dir": "out/seq"}},
  {"cmd": "file.export_sprite_sheet", "params": {"path": "out/sheet.png", "scale": 0.25}}
 ],
 "renders": {"dir": "out/check", "frames": [1, 30, 60], "scale": 0.5}}
```

- Without `edit.deselect` between parts, the next `convert_to_symbol` would also grab the
  previous selection. A freshly drawn shape is selected on its own after a deselect.
- `bone.add` → `{bone, layer, created}`; every instance moves to one armature layer
  (`Armature_1`), and the original layer is left empty. `head` is the joint in stage px.
- Angles are degrees from the drawn pose; negative turns counter-clockwise on screen
  (y down). Limits clamp poses silently (`-200` with `min -120` becomes `-120`), so read
  back with `ac_inspect.py rig.anicraft --at 1 30 60`.
- Each `bone.pose {frame}` keys a pose keyframe; the armature tweens between them.
  `bone.solve {bone, x, y, frame}` does IK instead (limits and pins respected).
- Check: `ac_verify.py doc rig.anicraft --frames 60 --bones 3 --limited 3 --poses Armature_1:3`.

## Shape tween with hints

```json
  {"cmd": "layer.new", "params": {"name": "Morph"}, "as": "morph"},
  {"cmd": "draw.rect", "on": {"layer": "$morph.layer", "frame": 1}, "params": {"x": 100, "y": 200, "w": 120, "h": 120, "fill": "#3366cc"}},
  {"cmd": "timeline.insert_blank_keyframe", "params": {"layer": "$morph.layer", "frame": 24}},
  {"cmd": "draw.ellipse", "on": {"layer": "$morph.layer", "frame": 24}, "params": {"x": 300, "y": 200, "w": 140, "h": 140, "fill": "#cc6633"}},
  {"cmd": "timeline.create_shape_tween", "params": {"layer": "$morph.layer", "frame": 1, "easing": "ease-in-out"}},
  {"cmd": "tween.add_hint", "params": {"layer": "$morph.layer", "frame": 1}},
  {"cmd": "tween.move_hint", "params": {"hint": "a", "x": 100, "y": 200, "side": "start", "layer": "$morph.layer", "frame": 1}},
  {"cmd": "tween.move_hint", "params": {"hint": "a", "x": 370, "y": 200, "side": "end", "layer": "$morph.layer", "frame": 1}}
```

- Shape tweens need raw shapes (not symbols) on both keyframes.
- Hints are letters `a`…`z` in creation order; each needs a `start` and an `end` placement
  (they snap to the nearest shape edge). A hint is `active` only once both ends are placed:
  `tween.hints` shows `start_placed`/`end_placed`.
- Check: `ac_verify.py doc F --shape-tween Morph --hints Morph:2`.

## Edit a supplied file

Inspect first: `ac_inspect.py in.anicraft` lists element ids, text content, bitmap names.

```json
{"source": "in.anicraft", "out": "edited.anicraft",
 "steps": [
  {"cmd": "element.select", "params": {"ids": [2]}},
  {"cmd": "text.edit", "params": {"text": "Goodbye"}},
  {"cmd": "file.import_to_library", "params": {"path": "new.png"}, "as": "img"},
  {"cmd": "layer.select", "params": {"layer": "$layer:Photo", "select": true}},
  {"cmd": "element.swap_bitmap", "params": {"bitmap": "$img.bitmap"}},
  {"cmd": "layer.new", "params": {"name": "Actions"}, "as": "act"},
  {"cmd": "timeline.insert_keyframe", "params": {"layer": "$act.layer", "frame": 24}},
  {"cmd": "actions.set", "params": {"layer": "$act.layer", "frame": 24, "actions": [{"op": "stop"}]}},
  {"cmd": "script.check", "params": {"text": "stop();"}, "as": "check"},
  {"cmd": "control.test_movie", "params": {"frames": 72}, "as": "tm"},
  {"cmd": "file.export_lottie", "params": {"path": "out/edited.lottie.json"}},
  {"cmd": "file.export_html", "params": {"path": "out/edited.html"}}
 ]}
```

- `element.select` works on visible, unlocked layers at the playhead; `layer.select
  {"select": true}` selects everything on a layer.
- `text.edit` and `element.swap_bitmap` act on the selection. An imported image is a
  bitmap-filled shape; `swap_bitmap` keeps its position and takes the new image's size.
- Frame actions (`actions.set`: `stop play goto_and_play goto_and_stop next_frame
  prev_frame trace set_property …`) and scripts (`script.set {text}` — the ActionScript 3
  subset) both live on a keyframe. A separate `Actions` layer keeps them off artwork keys.
- `script.check {text}` → `runs`, `problems` (line/col), `steps`. `control.test_movie`
  → `state.frame` (0-based) and `playing`; stopped on the last frame means `frame ==
  frames-1, playing false`, plus `output` from `trace`.
- Check: `ac_verify.py doc edited.anicraft --text Goodbye --bitmap new.png --action 24:stop --scripts-run --test-movie-ends 24`.

## More building blocks

- **Classic tween** between two keyframes of a symbol (tested):
  ```json
  {"cmd": "timeline.insert_keyframe", "params": {"layer": "$box.layer", "frame": 24}},
  {"cmd": "element.select", "on": {"layer": "$box.layer", "frame": 24}, "params": {"ids": ["$box.instance"]}},
  {"cmd": "element.set_transform", "params": {"x": 300, "y": 300, "rotation": 90}},
  {"cmd": "timeline.create_tween", "params": {"layer": "$box.layer", "frame": 1, "easing": "ease-out"}}
  ```
  `element.set_transform` x/y place the registration point (the shape's centre after
  `convert_to_symbol`).
- **Labels**: `timeline.set_label {label, layer, frame}`; goto actions can target them.
- **Layer types**: `layer.set_type {type: mask|masked|guide|guided}`, `layer.new_folder`,
  `layer.add_motion_guide`, `layer.set_depth` (parallax against the camera).
- **Sound**: `file.import_to_library {path: x.wav}` → `{sound}`; `sound.place {sound, layer,
  frame, sync: stream, extend: true}`. MP4/WebM exports include it unless `audio: false`.
- **Multi-frame edits**: `frames.*` (edit_multiple, transform, align) for onion-skin style
  batch changes.
- **Scenes**: `scene.new`, `scene.select {scene: index}`; exports with `from`/`to` run
  through every scene in order. `ac_inspect.py` shows the first scene's layers only.
