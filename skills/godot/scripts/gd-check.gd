extends SceneTree
# Parse-check every .gd file in the project in one Godot process.
#   godot --headless --path PROJECT --script /abs/path/gd-check.gd
# Prints "GD-CHECK OK|FAIL res://path.gd" per file; the parse error itself goes to
# stderr as "SCRIPT ERROR: Parse Error: … (res://path.gd:LINE)". Exits 1 on any failure.
# Skips hidden folders (.godot, .git) and folders that contain a .gdignore file.

func _initialize() -> void:
	var failed := 0
	var files := _walk("res://")
	for path in files:
		var script := GDScript.new()
		script.source_code = FileAccess.get_file_as_string(path)
		script.resource_path = path
		if script.reload() != OK:
			printerr("GD-CHECK FAIL ", path)
			failed += 1
		else:
			print("GD-CHECK OK ", path)
	print("GD-CHECK %d file(s), %d failed" % [files.size(), failed])
	quit(1 if failed > 0 else 0)


func _walk(dir: String) -> Array[String]:
	var out: Array[String] = []
	for file in DirAccess.get_files_at(dir):
		if file.ends_with(".gd"):
			out.append(dir.path_join(file))
	for sub in DirAccess.get_directories_at(dir):
		var sub_path := dir.path_join(sub)
		if sub.begins_with(".") or FileAccess.file_exists(sub_path.path_join(".gdignore")):
			continue
		out.append_array(_walk(sub_path))
	return out
