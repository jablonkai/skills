#!/usr/bin/env bash
# Scaffold a minimal Godot 4 project that imports, runs and exports cleanly.
#
#   bash gd-new.sh DIR [options]
#
#   --name NAME          application name (default: the directory name)
#   --3d                 3D main scene (Node3D + camera + light) instead of 2D (Node2D)
#   --size WxH           viewport size (default 1152x648)
#   --renderer R         gl_compatibility (default; required for Web export),
#                        mobile or forward_plus
#   --wasd               add move_left/right/up/down actions on WASD + arrow keys
#
# Writes project.godot, main.tscn, main.gd, icon.svg, .gitignore and build/.gdignore,
# then imports once. Refuses to touch a directory that already holds project.godot.
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

usage() { awk 'NR > 1 && !/^#/ { exit } NR > 1 { sub(/^# ?/, ""); print }' "${BASH_SOURCE[0]}"; exit 2; }

[[ $# -ge 1 ]] || usage
case "$1" in -h | --help) usage ;; esac
dir=$1
shift
name="" three_d=0 size=1152x648 renderer=gl_compatibility wasd=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) name=$2; shift 2 ;;
    --3d) three_d=1; shift ;;
    --size) size=$2; shift 2 ;;
    --renderer) renderer=$2; shift 2 ;;
    --wasd) wasd=1; shift ;;
    -h | --help) usage ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

case "$renderer" in
  gl_compatibility | mobile | forward_plus) ;;
  *) echo "--renderer must be gl_compatibility, mobile or forward_plus" >&2; exit 2 ;;
esac
if [[ ! "$size" =~ ^([0-9]+)x([0-9]+)$ ]]; then
  echo "--size must look like 1280x720" >&2
  exit 2
fi
width=${BASH_REMATCH[1]} height=${BASH_REMATCH[2]}

if [[ -f "$dir/project.godot" ]]; then
  echo "$dir already contains project.godot — not overwriting" >&2
  exit 2
fi
mkdir -p "$dir/build"
dir=$(cd "$dir" && pwd)
[[ -n "$name" ]] || name=$(basename "$dir")
# project.godot strings are double-quoted; escape backslashes and quotes.
name_escaped=${name//\\/\\\\}
name_escaped=${name_escaped//\"/\\\"}

cat >"$dir/project.godot" <<EOF
config_version=5

[application]

config/name="$name_escaped"
run/main_scene="res://main.tscn"
config/icon="res://icon.svg"
EOF

if [[ $three_d -eq 1 ]]; then
  root_type=Node3D
  cat >"$dir/main.tscn" <<'EOF'
[gd_scene format=3]

[ext_resource type="Script" path="res://main.gd" id="1_main"]

[node name="Main" type="Node3D"]
script = ExtResource("1_main")

[node name="Camera3D" type="Camera3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 0.939693, 0.34202, 0, -0.34202, 0.939693, 0, 3, 8)

[node name="Sun" type="DirectionalLight3D" parent="."]
transform = Transform3D(0.866025, -0.353553, 0.353553, 0, 0.707107, 0.707107, -0.5, -0.612372, 0.612372, 0, 5, 0)
EOF
else
  root_type=Node2D
  cat >"$dir/main.tscn" <<'EOF'
[gd_scene format=3]

[ext_resource type="Script" path="res://main.gd" id="1_main"]

[node name="Main" type="Node2D"]
script = ExtResource("1_main")
EOF
fi

printf 'extends %s\n\n\nfunc _ready() -> void:\n\tpass\n' "$root_type" >"$dir/main.gd"

cat >"$dir/icon.svg" <<'EOF'
<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128"><rect x="4" y="4" width="120" height="120" rx="24" fill="#478cbf"/><circle cx="44" cy="60" r="14" fill="#fff"/><circle cx="84" cy="60" r="14" fill="#fff"/><circle cx="44" cy="62" r="6" fill="#414042"/><circle cx="84" cy="62" r="6" fill="#414042"/><rect x="40" y="88" width="48" height="10" rx="5" fill="#fff"/></svg>
EOF

cat >"$dir/.gitignore" <<'EOF'
# Godot 4 import cache and editor state — regenerated on import
.godot/
# Export output
build/
EOF
# .gdignore keeps export output out of the import scan and the exported pack.
touch "$dir/build/.gdignore"

settings=(
  --set "rendering/renderer/rendering_method=\"$renderer\""
  --set "rendering/renderer/rendering_method.mobile=\"$renderer\""
  --set "display/window/size/viewport_width=$width"
  --set "display/window/size/viewport_height=$height"
  --set 'display/window/stretch/mode="canvas_items"'
  # macOS arm64/universal export refuses to run without ETC2/ASTC textures.
  --set "rendering/textures/vram_compression/import_etc2_astc=true"
)
if [[ $wasd -eq 1 ]]; then
  settings+=(
    --action "move_left=A,Left" --action "move_right=D,Right"
    --action "move_up=W,Up" --action "move_down=S,Down"
  )
fi

log=$(mktemp -t gd-new)
if ! (perl -e 'alarm 60; exec @ARGV' bash "$here/godot.sh" --headless --path "$dir" -l en \
  --script "$here/gd-settings.gd" -- "${settings[@]}" >"$log" 2>&1 || exit $?) 2>/dev/null; then
  cat "$log" >&2
  exit 1
fi
if ! (perl -e 'alarm 120; exec @ARGV' bash "$here/godot.sh" --headless --path "$dir" -l en \
  --import >>"$log" 2>&1 || exit $?) 2>/dev/null; then
  cat "$log" >&2
  exit 1
fi
if grep -qE '^(SCRIPT ERROR|ERROR)' "$log"; then
  grep -A2 -E '^(SCRIPT ERROR|ERROR)' "$log" >&2
  exit 1
fi
rm -f "$log"

echo "created $dir ($root_type, $renderer, ${width}x${height}$([[ $wasd -eq 1 ]] && echo ', WASD actions'))"
ls -A "$dir"
