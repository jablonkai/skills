---
name: godot
description: 'Build, run, test and export Godot 4 projects headless from the CLI — scaffold a project, author .tscn scenes, .gd scripts and project.godot as text, import, parse-check and run with errors read from the log, test gameplay and UI signals with headless test scripts, capture frames with Movie Maker, and export Web or macOS builds from export presets. Use whenever the user wants a small 2D or 3D game or prototype made in Godot, a Godot project run or debugged ("why does my scene error", "Node not found"), a Godot UI or signals wired up, a headless test, a screenshot of a scene, or an export to Web/HTML5 or macOS, or mentions Godot, GDScript, .tscn or project.godot. Hungarian: "csinálj egy Godot játékot", "futtasd headless", "exportáld webre". Not for Unity, Unreal or GameMaker; 3D modeling or rendering (use blender); 2D motion graphics (use cavalry); plain JavaScript/canvas or Phaser web games; Godot C#/.NET projects; sprite painting (use krita or gimp).'
summary: "build, run, test and export Godot 4 projects headless from the CLI — author scenes, GDScript and project settings as text, catch script errors from the log, test gameplay and UI signals with headless test scripts, capture Movie Maker frames, export Web and macOS builds"
category: game-dev
risk: low
tags:
    - godot
    - gdscript
    - game
    - headless
    - export
metadata:
  version: "1.0.0"
---

# Godot Control

Drive Godot 4 **headless from the command line**:
- Write the project as text (`project.godot`, `.tscn`, `.gd`).
- Run one short-lived Godot process per step. There is no live bridge, and nothing is
  left running.
- Verified on **Godot 4.7.2**, macOS. This file covers the usual tasks; the references
  are for the cases listed at the end.

`B=<this skill>/scripts`. Call each script as `bash "$B/<script>" …`; run any of them
with `-h` to list its options.

| Script | Does |
|---|---|
| `godot.sh --check` | Godot path and version, .NET or not, export templates. Any other arguments go straight to Godot. |
| `gd-new.sh DIR --wasd --size 640x360` | New project with the Compatibility renderer, WASD+arrow actions, `build/.gdignore`, and the macOS texture setting. Then imports. |
| `gd-run.sh DIR` | import → scene lint → parse-check every `.gd` → run 120 frames. Exits non-zero on **any** error in the log. |
| `gd-run.sh DIR --no-import --test res://tests/t.gd` | Runs a headless test script; its `quit(code)` is the verdict. |
| `gd-capture.sh DIR out.png --frame 90 [-- --demo]` | Renders frame N to PNG with Movie Maker (a minimized window). Args after `--` go to the game. |
| `gd-preset.sh DIR web\|macos\|windows\|linux` | Appends a complete export preset. `macos` also enables the texture setting macOS needs. |
| `gd-export.sh DIR PRESET build/web/index.html` | Checks the preset and templates, exports, then checks the artifacts. |
| `gd-verify.py DIR` / `--png f.png --png-size WxH` | Scene lint without Godot, and a PNG size/blankness check. |
| `godot.sh --headless --path DIR --script "$B/gd-settings.gd" -- --action jump=Space,W --set KEY=VALUE` | Edits `project.godot` through Godot. Use it for input actions, whose serialized form is too long to write by hand. |

## Workflow

1. Run `godot.sh --check`. Exit 2 means Godot is missing or older than 4.x: suggest
   `brew install --cask godot`. C# projects are out of scope.
2. For a new project, run `gd-new.sh`. For an existing one, read `project.godot`, the
   main scene and its scripts first.
3. Write the scenes, scripts and resources as text, following the rules below.
4. `gd-run.sh DIR`: fix everything it reports. It prints `file:line` and a GDScript
   backtrace for each error.
5. Prove the requested behaviour with a test script (template below). A clean run
   doesn't show that the player can collect a coin.
6. `gd-capture.sh`, then open the PNG with the Read tool. A game with no input stays
   still, so gate a self-playing mode behind a user argument:
   `if "--demo" in OS.get_cmdline_user_args(): Input.action_press("move_right")`,
   then capture with `-- --demo`.
7. Export when asked: `gd-preset.sh` if no preset exists yet, then `gd-export.sh`.
   Missing templates give exit 2 plus install steps. Never download them (~1 GB)
   without asking.
   - **Web:** serve the build over HTTP (`python3 -m http.server -d build/web`);
     `file://` does not work. Single-threaded builds need no special headers.
   - **macOS:** the `.zip` holds `<config/name>.app`. It is ad-hoc signed, so the
     first launch needs right-click ▸ Open.

## What Godot won't tell you

The scripts handle all of these. Keep them in mind on raw `godot` calls.
- **The exit code is 0 after script errors, parse errors included.** Read the log, and
  pass `-l en`, because the editor language can be localized.
- **A runtime error aborts the function, not the process.** A test that fails before
  `quit()` hangs, so use a timeout and a watchdog.
- **Two scene faults produce no error:**
  - A `[connection]` to a misspelled method logs nothing at all.
  - A wrong `parent=` path is only a `WARNING`, and the node is dropped.
- **Other silent pitfalls:**
  - `--check-only` without `--script` runs the game forever.
  - Unknown flags are silently ignored.
  - `--headless` renders no frames.
  - `--resolution` on a capture scales the content; set the viewport size in the
    project instead.
- **Build output inside the project gets imported and packed.** Keep it in a folder
  with a `.gdignore`.
- **Export paths are relative to the project folder, not the cwd.**

## Scene rules (.tscn)

```ini
[gd_scene format=3]

[ext_resource type="Script" path="res://coin.gd" id="1_coin"]

[sub_resource type="CircleShape2D" id="CircleShape2D_coin"]
radius = 12.0

[node name="Coin" type="Area2D" groups=["coins"]]
script = ExtResource("1_coin")

[node name="Shape" type="CollisionShape2D" parent="."]
shape = SubResource("CircleShape2D_coin")

[connection signal="body_entered" from="." to="." method="_on_body_entered"]
```

- **Order:** header, `ext_resource`, `sub_resource`, nodes, connections. Each parent
  comes before its children. Leave out `load_steps` (deprecated since 4.6), and
  `uid`/`unique_id`, which Godot adds when it saves.
- **Nodes:** the root has no `parent`. The others use a path from the root that leaves
  out the root's name: `"."`, `"HUD"`, `"Coins/Coin1"`.
- **ids** are any unique strings.
- **Instances:** `[node name="Player" parent="." instance=ExtResource("2")]` takes no
  type.
- **Properties** use Variant syntax: `Vector2(1, 2)`, `Color(1, 0, 0, 1)`,
  `theme_override_font_sizes/font_size = 24`.
- **Full-rect root Control:** `layout_mode = 3`, `anchors_preset = 15`,
  `anchor_right = 1.0`, `anchor_bottom = 1.0`. Children of containers use
  `layout_mode = 2`.
- **`unique_name_in_owner = true`** lets scripts find the node as `%Name`.

## GDScript (4.x)

- Use 4.x syntax: `@export`, `@onready`, `await`, `signal hit(damage: int)`,
  `hit.emit(3)`, `button.pressed.connect(_on_pressed)`, and `CharacterBody2D` with
  `velocity` plus `move_and_slide()` with no arguments. `yield`, `export var` and
  `KinematicBody2D` are 3.x.
- Indent with tabs.
- `var ok := node.prop == 2` is a **parse error** when `prop` is untyped, for example a
  script property reached through a `Control`-typed variable. Write
  `var ok: bool = …`.
- Read input through actions (`Input.get_vector("move_left", "move_right", "move_up",
  "move_down")`), so that tests can press them.
- Web export needs the `gl_compatibility` renderer, which `gd-new.sh` sets.

## Test script template

```gdscript
extends SceneTree
# tests/test_collect.gd — gd-run.sh DIR --no-import --test res://tests/test_collect.gd
# quit(0) pass, 1 fail, 2 watchdog (a script error aborted the test).

func _initialize() -> void:
	create_timer(10.0).timeout.connect(func(): printerr("FAIL watchdog"); quit(2))
	var main: Node = load("res://main.tscn").instantiate()
	root.add_child(main)            # _ready() runs; physics and signals are live
	await process_frame
	Input.action_press("move_right") # UI: button.pressed.emit(); LineEdit: set .text
	for i in 120:                    # 2 s of game time at the fixed 60 fps
		await physics_frame
		if main.score == 3:
			break
	Input.action_release("move_right")
	var ok: bool = main.score == 3 and main.get_node("HUD/Score").text == "Score: 3"
	print("%s score=%d" % ["PASS" if ok else "FAIL", main.score])  # gd-run.sh echoes PASS/FAIL/TEST lines
	quit(0 if ok else 1)
```

To test a custom signal, connect a lambda that appends to an array, fire the trigger,
and assert on the array.

## Before you report success

- `gd-run.sh` exits 0, and you have read any warnings.
- The behaviour test exits 0.
- You have looked at the capture yourself, when the task is visual.
- For an export, `gd-export.sh` exits 0.

Report the Godot version, which checks ran, and what stayed unverified (for example,
the build was never opened in a browser). Work only on local files, and never
overwrite a project the user has open with unsaved editor changes.

## References (read only the part you need)

- [formats.md](references/formats.md) — full `.tscn`/`.tres`/`project.godot` grammar
  and hand-edited `export_presets.cfg` keys. Read it for unusual syntax: editable
  instance children, custom Resource scripts, `binds`.
- [recipes.md](references/recipes.md) — complete tested projects: a 2D collect game
  and a UI with signals and a test. Read it when you want a whole working example to
  adapt.
- [cli.md](references/cli.md) — every flag, with an exit-code table. Read it before
  calling `godot` directly instead of through the scripts.
- [gotchas.md](references/gotchas.md) — the longer explanation of the list above.
  Read it only when something behaves unexpectedly.
