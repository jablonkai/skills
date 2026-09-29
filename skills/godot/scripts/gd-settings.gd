extends SceneTree
# Read or change project.godot through ProjectSettings, so Godot itself writes the
# file in its canonical form (input events especially are too verbose to hand-write).
#   godot --headless --path PROJECT --script /abs/gd-settings.gd -- [ops...]
#
#   --set KEY=VALUE      VALUE is parsed with str_to_var (640, true, Vector2(1, 2),
#                        "quoted string"); anything that does not parse is a string
#   --action NAME=KEYS   (re)define an input action; KEYS are comma-separated key
#                        names (A, Left, Space, Enter, Escape, Shift…) or
#                        mouse:1 / mouse:2 for mouse buttons
#   --erase KEY          remove a setting
#   --get KEY            print KEY=value (no save unless something else changed)
# Exits 1 on an unknown key name, 2 on bad usage.

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var changed := false
	var i := 0
	while i < args.size():
		var op := args[i]
		if i + 1 >= args.size():
			printerr("GD-SETTINGS missing value after ", op)
			quit(2)
			return
		var arg := args[i + 1]
		i += 2
		match op:
			"--set":
				var eq := arg.find("=")
				if eq < 1:
					printerr("GD-SETTINGS expected KEY=VALUE, got ", arg)
					quit(2)
					return
				ProjectSettings.set_setting(arg.left(eq), _parse(arg.substr(eq + 1)))
				changed = true
			"--erase":
				ProjectSettings.set_setting(arg, null)
				changed = true
			"--get":
				print("%s=%s" % [arg, var_to_str(ProjectSettings.get_setting(arg))])
			"--action":
				var parts := arg.split("=", true, 1)
				if parts.size() != 2:
					printerr("GD-SETTINGS expected NAME=KEY[,KEY…], got ", arg)
					quit(2)
					return
				var events := []
				for key_name in parts[1].split(",", false):
					var event := _event(key_name.strip_edges())
					if event == null:
						printerr("GD-SETTINGS unknown key name: ", key_name)
						quit(1)
						return
					events.append(event)
				ProjectSettings.set_setting("input/" + parts[0], {"deadzone": 0.2, "events": events})
				changed = true
			_:
				printerr("GD-SETTINGS unknown option ", op)
				quit(2)
				return
	if changed:
		var err := ProjectSettings.save()
		if err != OK:
			printerr("GD-SETTINGS save failed: ", error_string(err))
			quit(1)
			return
		print("GD-SETTINGS saved project.godot")
	quit(0)


func _parse(text: String) -> Variant:
	var value = str_to_var(text)
	if value == null and text != "null":
		return text
	return value


func _event(key_name: String) -> InputEvent:
	if key_name.begins_with("mouse:"):
		var mouse := InputEventMouseButton.new()
		mouse.button_index = int(key_name.substr(6)) as MouseButton
		return mouse
	var code := OS.find_keycode_from_string(key_name)
	if code == KEY_NONE:
		return null
	var key := InputEventKey.new()
	key.physical_keycode = code
	return key
