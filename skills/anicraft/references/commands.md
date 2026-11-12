# Commands pinned for 0.2.1

240 commands: `file` 24, `timeline` 21, `layer` 16, `element` 15, `draw` 14, `motion` 13,
`raw` 11, `edit` 10, `library` 10, `scene` 9, `frames` 9, `modify` 8, `align` 8, `bone` 7,
`tween` 5, `path` 5, `stroke` 5, `plugin` 5, `sound` 5, `script` 5, `camera` 4, `paint` 4,
`arrange` 4, `symbol` 4, `text` 3, `actions` 3, `find` 3, `prefs` 3, `doc` 2, `publish` 2,
`control` 1, `instance` 1, `explorer` 1.
Look anything else up: `ac_commands.py WORD…`, `--prefix GROUP.`, `--id ID`.
`frame` below is 0-based for the engine (1-based in `ac_build.py` specs).

| Task | Command | Key params |
|---|---|---|
| Stage | `doc.set_stage` | `width height fps background` |
| Read state | `doc.info` | = `info` |
| Shapes | `draw.rect` `ellipse` `star` `line` `path` `freehand` `brush` | `x y w h fill stroke stroke_width radius` (path: `d`, SVG) |
| Text | `text.create` / `text.edit` (selection) | `text x y font size bold italic color align width` |
| Symbol | `modify.convert_to_symbol` | `name kind: graphic\|movie_clip\|button` |
| Place from library | `library.place` | `symbol\|bitmap\|sound x y` |
| Library | `library.items`, `library.rename`, `library.delete_unused` | |
| Import | `file.import` (stage, new layer) / `file.import_to_library` | `path x y` / `path name` |
| Select | `element.select`, `edit.select_all`, `edit.deselect`, `layer.select` | `ids` / `layer select` |
| Transform | `element.set_transform`, `element.translate` | `x y sx sy rotation` / `dx dy` |
| Look | `element.set_fill` `set_stroke` `set_alpha` `set_filters` `set_blend` | |
| Swap | `element.swap_bitmap`, `element.swap_symbol` | `bitmap` / `symbol` |
| Layers | `layer.new` `rename` `delete` `set_type` `new_folder` `add_motion_guide` `set_depth` | `name layer type` |
| Frames | `timeline.insert_frame` `remove_frame` | `layer(s) frame count` |
| Keys | `timeline.insert_keyframe` `insert_blank_keyframe` `clear_keyframe` `move_keyframes` | `layer(s) frame` |
| Playhead | `timeline.goto` | `frame` |
| Classic / shape tween | `timeline.create_tween` / `create_shape_tween`, `set_easing`, `remove_tween` | `layer frame easing` |
| Motion tween | `timeline.create_motion_tween` | `layer frame` |
| Motion keys | `motion.set_key` `remove_key` `set_ease` `info` | `property value frame layer` |
| Motion path | `motion.set_path` `clear_path` `orient` `add_point` `pin_point` `move_path` | `d` (SVG, stage px) |
| Shape hints | `tween.add_hint` `move_hint` `remove_hint` `clear_hints` `hints` | `hint x y side layer frame` |
| Labels | `timeline.set_label` | `label layer frame` |
| Camera | `camera.add` `set` `info` `remove` | `x y dx dy zoom zoom_by rotation tint tint_amount frame` |
| Bones | `bone.add` `set_limits` `pin` `pose` `solve` `info` `remove` | `from to head tail name` / `bone min max` / `bone angle frame` |
| Sound | `sound.place` `set` `remove`; `layer.set_volume` | `sound layer frame sync extend` |
| Actions | `actions.set` `clear` `list` | `actions:[{op,…}] layer frame` or `element event` |
| Scripts | `script.check` `set` `list` `clear` `set_class` | `text language layer frame` |
| Instance name | `instance.set_name` | for script targets |
| Play | `control.test_movie` | `frames events` |
| Scenes | `scene.new` `select` `rename` `duplicate` `delete` | |
| Save | `file.save_as` | `path confirm` |
| Export | `file.export_*` | see [export.md](export.md) |
