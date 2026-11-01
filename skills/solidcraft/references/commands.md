# Command ids by task (pinned to 0.29.0)

These ids were checked against `solidcraft-cli commands` from SolidCraft 0.29.0, which
has 555 commands. The parameter shapes are long and change between releases, so look
them up instead of copying them from here:
- `sc_commands.py WORD…` for one-line signatures;
- `sc_commands.py --id ID` for the full text and the typed schema, where there is one;
- `sc_commands.py --doc solidcraft-modeling/reference.md` for worked shapes and traps.

In the parameter shapes, `expr` means a number in mm, or text such as `"thickness"`,
`"w/2 - 6"` or `"5 mm"`. Text follows parameter changes.

| Task | Ids | Key params |
|---|---|---|
| Parameters | `parameters.add`, `parameters.change`, `parameters.list`, `parameters.rename`, `parameters.delete`, `parameters.export`, `parameters.import` | `add {name, expression, unit?}`. `change {changes: {name: expr}}` takes existing names only and applies all or none. `list {filter: all\|user\|sketch\|feature}` |
| Sketch | `sketch.create`, `sketch.finish`, `sketch.edit`, `sketch.solve`, `sketch.inspect` | `create {plane: XY\|XZ\|YZ\|{origin,x_dir,y_dir}\|{face:[x,y,z]}, offset?, name?}` |
| Sketch geometry | `sketch.line`, `sketch.rectangle.two_point`, `sketch.rectangle.center`, `sketch.rectangle.rounded`, `sketch.circle.center`, `sketch.arc.center_point`, `sketch.polygon.inscribed`, `sketch.slot.overall`, `sketch.point`, `sketch.draw.dimensioned` | `rectangle.two_point {p0, p1}`, `circle.center {center, radius\|diameter}`. The reply lists the new ids in `created` (`l1`, `c1`, `c1.center`) |
| Constraints and dimensions | `sketch.dimension`, `sketch.constraint.{horizontal_vertical,coincident,tangent,equal,parallel,perpendicular,fix,midpoint,concentric,collinear,symmetry}` | `dimension {entities, type?, value}`. `value: "w = 40"` adds the parameter `w` and drives the dimension with it |
| Primitives | `solid.box`, `solid.cylinder`, `solid.sphere`, `solid.torus`, `solid.cone` | `box {length, width, height, corner?\|center?, operation?, body_name?}` |
| Sketch features | `solid.extrude`, `solid.revolve`, `solid.sweep`, `solid.loft`, `solid.rib`, `solid.web`, `solid.emboss`, `solid.coil`, `solid.pipe` | `extrude {distance\|through_all, operation?: new\|join\|cut\|intersect, direction?: positive\|negative\|symmetric, profiles?, body_name?, name?}` |
| Holes | `solid.hole`, `solid.thread` | `hole {position:[x,y,z] on a face \| sketch (+points), diameter \| clearance:"M3", type?: simple\|counterbore\|countersink, depth?}` (through all by default) |
| Edges and faces | `solid.fillet`, `solid.chamfer`, `solid.shell`, `solid.draft`, `solid.offset_face`, `solid.press_pull`, `solid.replace_face` | `fillet {edges:[[x,y,z] on the edge], radius}`; `shell {faces:[[x,y,z]], thickness}` |
| Repeats | `solid.pattern.rectangular`, `solid.pattern.circular`, `solid.pattern.path`, `solid.mirror` | `rectangular {features\|bodies, dir1, count1, spacing1, dir2?, count2?, spacing2?}`. `circular {features, axis, count, angle?}` |
| Booleans and bodies | `solid.combine`, `solid.split_body`, `solid.move`, `solid.scale`, `solid.remove`, `body.rename` | `combine {target, tools:[…], operation?: join\|cut\|intersect, keep_tools?}` |
| Timeline | `timeline.inspect`, `timeline.edit`, `timeline.roll_to`, `timeline.suppress`, `timeline.delete`, `timeline.dependents`, `timeline.compute_all`, `timeline.export_script` | `edit {feature, set:{…}}`, using the field shapes `timeline.inspect` shows |
| Undo and safety | `edit.undo`, `edit.redo`, `edit.checkpoint`, `edit.restore_checkpoint` | |
| Measure and check | `inspect.measure`, `inspect.section`, `inspect.interference`, `inspect.clearance`, `inspect.center_of_mass`, `inspect.compare`, `inspect.parameter_sweep`, `inspect.minimum_radius`, `document.inspect` | `measure {bodies?}` or `{items:[1-2 selections]}`; `section {plane, at?\|offset?, flip?}` |
| Materials | `material.assign`, `material.inspect`, `appearance.assign` | Mass uses the assigned material. The default density is 1.29 g/cm³ |
| Files | `file.new`, `file.save`, `file.save_as`, `file.export`, `file.save_mesh`, `file.insert_step`, `file.insert_mesh`, `sketch.export_dxf`, `file.send_to_slicer` | `export {path, format?, bodies?, quality?}` |
| Views | `view.save`, `view.fit`, `view.home` | A view saved in the design can be passed to `snapshot --view NAME` |
| Components | `component.create`, `component.activate`, `component.move_bodies`, `joint.*`, `motion.*` | Assemblies and mechanisms: `sc_commands.py --doc solidcraft-mechanisms` |

**Added in 0.25.0** (missing from the 0.22.1 CLI):
- solids and sketches: `solid.cone`, `sketch.arc3d`, `sketch.transform`, `sketch.toggle_diameter`, `sketch.spline.insert_point`, `canvas.to_sketch`;
- files: `file.send_to_slicer`, `file.open_in_easyprint`;
- rendering: `render.batch`, `render.compare`;
- views: `view.fit`, `view.home`, `view.perspective`;
- other: `edit.repeat`, `document.revision`, `component.copy_bodies`, `occurrence.reparent`, and a few `appearance.*` commands.
