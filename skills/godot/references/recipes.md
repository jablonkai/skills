# Recipes

Each recipe below was run end to end on Godot 4.7.2 with the skill's scripts. `B` is
the skill's `scripts/` folder.

## Contents

- [Headless test script template](#headless-test-script-template)
- [2D collect game](#2d-collect-game)
- [UI scene with signals](#ui-scene-with-signals)
- [Capture frames with scripted input](#capture-frames-with-scripted-input)
- [Web export and local preview](#web-export-and-local-preview)
- [macOS export](#macos-export)
- [Diagnose a broken project](#diagnose-a-broken-project)

## Headless test script template

The exit code is the verdict, and the watchdog catches script errors that abort the
test before it reaches `quit()`:

```gdscript
extends SceneTree
# tests/test_<feature>.gd — run: bash $B/gd-run.sh . --test res://tests/test_<feature>.gd
# quit(0) pass, 1 fail, 2 watchdog (a script error aborted the test).


func _initialize() -> void:
	create_timer(10.0).timeout.connect(func(): printerr("FAIL watchdog"); quit(2))
	var scene: Node = load("res://main.tscn").instantiate()
	root.add_child(scene)
	await process_frame           # _ready() has run
	# … drive it: Input.action_press("move_right"), button.pressed.emit(), set properties …
	for i in 120:                 # 2 s of game time at the fixed 60 fps
		await physics_frame
	var ok: bool = scene.score == 3   # typed: `:=` on an untyped property is a parse error
	print("%s score=%d" % ["PASS" if ok else "FAIL", scene.score])
	quit(0 if ok else 1)
```

- `root` is the SceneTree's root Window. Adding the scene there runs `_ready()`,
  `_process()` and physics, just as in the game.
- `Input.action_press()` works headless, and `Input.get_vector()` and
  `is_action_pressed()` see it. Release the action afterwards.
- Timers and `await` run on the fixed step, so 120 physics frames take well under a
  second of wall time.
- `gd-run.sh` echoes lines that start with `PASS`, `FAIL` or `TEST`.
- Keep tests in `tests/`. Add a `tests/.gdignore` only if you want them left out of
  exports. That also hides them from `res://`, so `--test` needs an absolute path then.

## 2D collect game

`bash $B/gd-new.sh coin-hunt --wasd --size 640x360` sets up the project, then:

`player.gd`
```gdscript
extends CharacterBody2D

@export var speed := 240.0


func _physics_process(_delta: float) -> void:
	velocity = Input.get_vector("move_left", "move_right", "move_up", "move_down") * speed
	move_and_slide()


func _draw() -> void:
	draw_circle(Vector2.ZERO, 16, Color("#4fc3f7"))
```

`coin.gd`
```gdscript
extends Area2D

signal collected


func _on_body_entered(body: Node2D) -> void:
	if body is CharacterBody2D:
		collected.emit()
		queue_free()


func _draw() -> void:
	draw_circle(Vector2.ZERO, 10, Color.GOLD)
```

`main.gd`
```gdscript
extends Node2D

var score := 0


func _ready() -> void:
	for coin in $Coins.get_children():
		coin.collected.connect(_on_coin_collected)
	_update_label()


func _on_coin_collected() -> void:
	score += 1
	_update_label()


func _update_label() -> void:
	$HUD/Score.text = "Score: %d" % score
```

`main.tscn`: repeat the Coin block for Coin2 and Coin3 at x = 300 and 400.
```ini
[gd_scene format=3]

[ext_resource type="Script" path="res://main.gd" id="1_main"]
[ext_resource type="Script" path="res://player.gd" id="2_player"]
[ext_resource type="Script" path="res://coin.gd" id="3_coin"]

[sub_resource type="CircleShape2D" id="CircleShape2D_player"]
radius = 16.0

[sub_resource type="CircleShape2D" id="CircleShape2D_coin"]
radius = 10.0

[node name="Main" type="Node2D"]
script = ExtResource("1_main")

[node name="Player" type="CharacterBody2D" parent="."]
position = Vector2(100, 180)
motion_mode = 1
script = ExtResource("2_player")

[node name="Shape" type="CollisionShape2D" parent="Player"]
shape = SubResource("CircleShape2D_player")

[node name="Coins" type="Node2D" parent="."]

[node name="Coin1" type="Area2D" parent="Coins"]
position = Vector2(200, 180)
script = ExtResource("3_coin")

[node name="Shape" type="CollisionShape2D" parent="Coins/Coin1"]
shape = SubResource("CircleShape2D_coin")

[node name="HUD" type="CanvasLayer" parent="."]

[node name="Score" type="Label" parent="HUD"]
offset_left = 16.0
offset_top = 12.0
theme_override_font_sizes/font_size = 24
text = "Score: 0"

[connection signal="body_entered" from="Coins/Coin1" to="Coins/Coin1" method="_on_body_entered"]
```

- `motion_mode = 1` is floating, for a top-down game. Use the default (grounded) for a
  platformer with gravity.
- Collision layers default to layer 1 and mask 1, so bodies and areas see each other.
  Set `collision_layer` / `collision_mask` when you add enemies or walls.
- Drawing with `_draw()` needs no art assets. For sprites, add a `Sprite2D` with
  `texture = ExtResource("…")` and run `--import` after adding the PNG.

Verify: `gd-verify.py .`, then a test that holds `move_right` until
`score == $Coins.get_child_count()`, then `gd-capture.sh . shot.png --frame 30`.

## UI scene with signals

`ui/counter.tscn`: a full-rect Control containing a centred VBox with a label and two
buttons.
```ini
[gd_scene format=3]

[ext_resource type="Script" path="res://ui/counter.gd" id="1_counter"]

[node name="Counter" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
script = ExtResource("1_counter")

[node name="Center" type="CenterContainer" parent="."]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0

[node name="VBox" type="VBoxContainer" parent="Center"]
layout_mode = 2
theme_override_constants/separation = 12

[node name="CountLabel" type="Label" parent="Center/VBox"]
unique_name_in_owner = true
layout_mode = 2
theme_override_font_sizes/font_size = 32
text = "Count: 0"
horizontal_alignment = 1

[node name="Increment" type="Button" parent="Center/VBox"]
layout_mode = 2
text = "Add one"

[node name="Reset" type="Button" parent="Center/VBox"]
layout_mode = 2
text = "Reset"

[connection signal="pressed" from="Center/VBox/Increment" to="." method="_on_increment_pressed"]
[connection signal="pressed" from="Center/VBox/Reset" to="." method="_on_reset_pressed"]
```

`ui/counter.gd`
```gdscript
extends Control

signal count_changed(value: int)

var count := 0


func _on_increment_pressed() -> void:
	count += 1
	%CountLabel.text = "Count: %d" % count
	count_changed.emit(count)


func _on_reset_pressed() -> void:
	count = 0
	%CountLabel.text = "Count: 0"
	count_changed.emit(count)
```

In the test, `button.pressed.emit()` fires the connected handler, just as a click
would. Also connect to the custom signal and assert on what it carried:

```gdscript
	var seen: Array[int] = []
	ui.count_changed.connect(func(v: int): seen.append(v))
	ui.get_node("Center/VBox/Increment").pressed.emit()
	ui.get_node("Center/VBox/Increment").pressed.emit()
	var ok: bool = ui.get_node("%CountLabel").text == "Count: 2" and seen == [1, 2]
```

To make a UI scene the entry point, set `run/main_scene` to it, or instance it under a
`CanvasLayer` in the game scene.

## Capture frames with scripted input

`gd-capture.sh` renders the game as it runs, so with no player input nothing moves.
For a frame that shows gameplay, let the game read a user argument and drive itself:

```gdscript
# main.gd
func _ready() -> void:
	if "--demo" in OS.get_cmdline_user_args():
		Input.action_press("move_right")
```

```bash
bash $B/gd-capture.sh . shots/collect.png --frame 90 --every 30 -- --demo
python3 $B/gd-verify.py --png shots/collect.png --png-size 640x360
```

Then open the PNG with the Read tool. Overlapping nodes, off-screen UI and wrong
colours only show up visually.

## Web export and local preview

```bash
bash $B/godot.sh --check                                   # templates installed?
bash $B/gd-preset.sh . web                                 # only if no Web preset exists yet
bash $B/gd-export.sh . Web build/web/index.html            # preset "Web" in export_presets.cfg
python3 -m http.server 8000 --directory build/web          # then open http://localhost:8000
```

A single-threaded export (`variant/thread_support=false`) runs from any static
server. `file://` does not work, because browsers block loading the `.wasm` from it.

## macOS export

```bash
bash $B/gd-preset.sh . macos                               # preset + import_etc2_astc=true
bash $B/gd-export.sh . macOS build/mac/CoinHunt.zip        # or .app / .dmg
unzip -q build/mac/CoinHunt.zip -d build/mac && build/mac/*.app/Contents/MacOS/* --headless --quit-after 30
```

The `.app` inside is named after `config/name`, not after the zip. The exported binary
accepts the same runtime flags, so a headless smoke run of the build itself is cheap.

## Diagnose a broken project

1. `python3 $B/gd-verify.py .` finds broken resource ids, missing files, bad parent
   paths, and connections to methods that don't exist. None of these needs Godot.
2. `bash $B/gd-run.sh . --check` imports and parse-checks every script, and reports
   `file:line` for each parse error.
3. `bash $B/gd-run.sh . --frames 120` runs the game and shows runtime errors
   (`Node not found`, calls on null) with a GDScript backtrace.
4. Fix, then rerun steps 1–3 until all three are clean. Report what was wrong at
   `file:line`, not only that it now passes.
