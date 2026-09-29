# Godot 4 text formats

Everything below is how Godot **4.7.2** reads and writes these files. Text scenes and
resources are the source of truth. The `.godot/` folder is a cache that `--import`
rebuilds, so never edit it and don't commit it.

## Contents

- [project.godot](#projectgodot)
- [.tscn scenes](#tscn-scenes)
- [.tres resources](#tres-resources)
- [Scripts and .uid files](#scripts-and-uid-files)
- [export_presets.cfg](#export_presetscfg)

## project.godot

An INI-like file of `[section]` and `key=value` lines, where each value is a Godot
Variant literal. Keys inside a section are relative, so `[display]` +
`window/size/viewport_width=640` is the setting `display/window/size/viewport_width`.

```ini
config_version=5

[application]

config/name="Coin Hunt"
run/main_scene="res://main.tscn"
config/features=PackedStringArray("4.7")
config/icon="res://icon.svg"

[autoload]

GameState="*res://autoload/game_state.gd"   ; * = instantiate as a singleton node

[display]

window/size/viewport_width=640
window/size/viewport_height=360
window/stretch/mode="canvas_items"

[rendering]

renderer/rendering_method="gl_compatibility"
textures/vram_compression/import_etc2_astc=true
```

- Change settings with `scripts/gd-settings.gd` (`--set KEY=VALUE`, `--action`). It
  goes through `ProjectSettings.save()`, so the file stays canonical. Small hand edits
  such as the name, main scene or window size are fine too.
- **Input actions** are serialized as full `Object(InputEventKey, …)` blobs about 300
  characters long. Don't hand-write them. Use
  `--action move_left=A,Left`. Key names follow `OS.find_keycode_from_string`: `A`–`Z`,
  `0`–`9`, `Left`, `Right`, `Up`, `Down`, `Space`, `Enter`, `Escape`, `Tab`, `Shift`,
  `Ctrl`, `Alt`, `F1`… Use `mouse:1` for the left mouse button. The built-in `ui_*`
  actions (`ui_left`, `ui_accept`, …) always exist. You can also add actions at
  runtime with `InputMap.add_action()` + `InputMap.action_add_event()`.
- `gl_compatibility` is the only renderer the **Web** export supports, and it is the
  fastest one for Movie Maker captures. Use `forward_plus` only for desktop 3D that
  needs it.

## .tscn scenes

```ini
[gd_scene format=3]

[ext_resource type="Script" path="res://coin.gd" id="1_coin"]
[ext_resource type="PackedScene" path="res://player.tscn" id="2_player"]
[ext_resource type="Texture2D" path="res://art/coin.png" id="3_tex"]

[sub_resource type="CircleShape2D" id="CircleShape2D_coin"]
radius = 12.0

[node name="Main" type="Node2D"]

[node name="Player" parent="." instance=ExtResource("2_player")]
position = Vector2(100, 180)

[node name="Coin" type="Area2D" parent="." groups=["coins"]]
position = Vector2(200, 180)
script = ExtResource("1_coin")

[node name="Shape" type="CollisionShape2D" parent="Coin"]
shape = SubResource("CircleShape2D_coin")

[node name="Sprite" type="Sprite2D" parent="Coin"]
texture = ExtResource("3_tex")

[node name="Score" type="Label" parent="."]
unique_name_in_owner = true
text = "Score: 0"

[connection signal="body_entered" from="Coin" to="Coin" method="_on_body_entered"]
```

Rules:
- **Order**: the header, then all `ext_resource` entries, then all `sub_resource`
  entries, then nodes in tree order, then connections. A sub-resource must come before
  anything that references it.
- **Header**: `[gd_scene format=3]`. Godot writes `[gd_scene format=3 uid="uid://…"]`
  on save. `load_steps` was deprecated in 4.6, and Godot ignores it if present.
  `format=2` is Godot 3.
- **ids** are arbitrary strings, unique per file. Godot generates `1_ab3cd` and
  `CircleShape2D_x7k2p`, but readable ids work the same. Reference them with
  `ExtResource("id")` and `SubResource("id")`.
- **ext_resource** takes `type` and `path`. Godot adds `uid="uid://…"` when it saves.
  Omitting the uid is fine: Godot resolves by path and fills the uid in on the next
  editor save.
- **Nodes**: the first node is the root and has no `parent`. Scenes saved by 4.6+
  also carry `unique_id=<int>` in each node header. Leave it out when you write a
  scene; Godot assigns ids on the next save. Every other node's
  `parent` is its path relative to the root: `"."` for the root's children,
  `"Coins/Coin1"` for deeper ones. A parent must appear **before** its children, and
  sibling names must be unique.
- **Instanced scenes** use `instance=ExtResource("id")` and take no `type`. Properties
  under an instance node override the instanced scene's values. Nodes *inside* an
  instance can't be declared again, but can be given overrides with
  `[node name="Child" parent="Player"]` and no type.
- **Properties** are `name = value` in Variant syntax: `Vector2(1, 2)`,
  `Color(1, 0, 0, 1)`, `"string"`, `&"StringName"`, `NodePath("../Target")`,
  `[1, 2]`, `{ "k": 1 }`, `PackedVector2Array(0, 0, 10, 0)`. Default values are
  omitted: Godot drops `radius = 10.0` on a `CircleShape2D` because 10 is its default.
- **Theme overrides** are `theme_override_font_sizes/font_size = 24`,
  `theme_override_colors/font_color = Color(…)` and
  `theme_override_constants/separation = 12`.
- **Control layout**: Godot writes both `layout_mode` and the anchors.
  `layout_mode = 3` + `anchors_preset = 15` + `anchor_right = 1.0` +
  `anchor_bottom = 1.0` is Full Rect on the root Control. Children of containers use
  `layout_mode = 2`, and free children of a Control use `layout_mode = 1`.
- **Groups**: `groups=["coins", "pickups"]` goes in the node header.
- **Unique names**: `unique_name_in_owner = true` makes `%Score` resolve from any
  script in the same scene.
- **Connections**:
  `[connection signal="pressed" from="VBox/Start" to="." method="_on_start_pressed"]`.
  `from` and `to` are node paths relative to the root, and the method must exist on
  the `to` node's script. Optional: `flags=3` (deferred + persist), and
  `binds=[1, "a"]` for extra arguments. Connecting in code
  (`button.pressed.connect(_on_start)`) is equally valid and easier to diff; use one
  style per project.

`python3 scripts/gd-verify.py PROJECT` checks ids, parents, connections and handler
methods without starting Godot.

## .tres resources

```ini
[gd_resource type="StyleBoxFlat" format=3]

[resource]
bg_color = Color(0.12, 0.14, 0.2, 1)
corner_radius_top_left = 8
```

A resource with sub-resources lists `[ext_resource]` / `[sub_resource]` entries
before `[resource]`, exactly as a scene does. For a custom `Resource` script, set
`script_class="ItemData"` in the header, add an `ext_resource` for the script, and put
`script = ExtResource("1")` under `[resource]`.

## Scripts and .uid files

- A `.gd` file starts with `extends <Class>` (plus an optional `class_name Foo`). Use
  tabs for indentation; the editor default and generated code use tabs.
- Since 4.4, the import step writes a `foo.gd.uid` file next to every script. Commit
  them, and move or rename them together with the script. A missing `.uid` file is
  regenerated.
- The `.import` sidecars (`icon.svg.import`) are generated too, and are committed by
  convention.

## export_presets.cfg

`scripts/gd-preset.sh DIR web|macos|windows|linux` writes this for you. A
hand-written preset needs **every key below** in the `[preset.N]` section. With keys
missing, Godot logs `Couldn't find the given section … include_filter`, and an empty
`[preset.N.options]` section counts as nonexistent. Unlisted options take their
defaults. Put build output in a folder with a `.gdignore` file (the scaffold's
`build/`), or the next import will pick it up and pack it into the export.

```ini
[preset.0]

name="Web"
platform="Web"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="build/web/index.html"

[preset.0.options]

variant/thread_support=false

[preset.1]

name="macOS"
platform="macOS"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="build/mac/CoinHunt.zip"

[preset.1.options]

application/bundle_identifier="com.example.coinhunt"
```

- Numbering is `preset.0`, `preset.1`, … with no gaps. `name` is what
  `--export-release "Web"` matches, case-sensitively.
- **Web** writes `index.html`, `.js`, `.wasm` (about 40 MB), `.pck`, the icons and two
  audio worklets. `variant/thread_support=false` (the default since 4.3) runs without
  cross-origin isolation headers, so any static server works. With threads on, the
  server has to send `Cross-Origin-Opener-Policy: same-origin` and
  `Cross-Origin-Embedder-Policy: require-corp`.
- **macOS** `OUT` can be `.zip`, `.app` or `.dmg` (`.dmg` needs `hdiutil`, which ships
  with macOS). The universal and arm64 builds refuse to export unless
  `rendering/textures/vram_compression/import_etc2_astc=true`. The build is ad-hoc
  signed, and notarization is out of scope.
- Other platforms (`Windows Desktop`, `Linux`, `Android`, `iOS`) use the same
  structure. Android needs the SDK, and iOS needs Xcode plus a team ID. Check the
  error text Godot prints for the missing option.
- Once the user saves a preset in the editor, Godot rewrites the file with every
  option spelled out. Edit that version in place rather than replacing it.
