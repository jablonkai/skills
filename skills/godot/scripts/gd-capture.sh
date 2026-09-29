#!/usr/bin/env bash
# Render frames of a Godot 4 project with Movie Maker mode and keep them as PNGs,
# for a visual check. Needs a real display driver: under --headless, --write-movie
# writes only the audio track. Godot opens a minimized window for a few seconds.
#
#   bash gd-capture.sh PROJECT_DIR OUT.png [options] [-- user args]
#
#   --frame N        keep frame N, counted from 0 (default 60, one second in)
#   --every K        also keep every K-th frame before N as OUT-0000.png… (contact sheet)
#   --scene RES      render this scene instead of the main scene
#   --fps F          movie frame rate (default 60)
#   --timeout SEC    kill Godot after SEC seconds (default 120)
#   -- ARGS          passed to the game as user args (OS.get_cmdline_user_args()),
#                    e.g. -- --demo for a self-playing capture
#
# The frame size is the project's viewport size (display/window/size/*). Do not pass
# --resolution: it resizes the window and the content is scaled up into the frame.
# Exit codes: 0 frame written, 1 no frame or errors in the log, 2 usage, 124 timeout.
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

usage() { awk 'NR > 1 && !/^#/ { exit } NR > 1 { sub(/^# ?/, ""); print }' "${BASH_SOURCE[0]}"; exit 2; }

[[ $# -ge 2 ]] || usage
project=$1 out=$2
shift 2
frame=60 every=0 scene="" fps=60 timeout=120
extra=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --frame) frame=$2; shift 2 ;;
    --every) every=$2; shift 2 ;;
    --scene) scene=$2; shift 2 ;;
    --fps) fps=$2; shift 2 ;;
    --timeout) timeout=$2; shift 2 ;;
    --) shift; extra=(-- "$@"); break ;;
    -h | --help) usage ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done
if [[ ! -f "$project/project.godot" ]]; then
  echo "no project.godot in $project" >&2
  exit 2
fi
if [[ "$out" != *.png ]]; then
  echo "OUT must end in .png" >&2
  exit 2
fi

tmp=$(mktemp -d -t gd-capture)
trap 'rm -rf "$tmp"' EXIT
log="$tmp/godot.log"

args=(--path "$project" -l en --minimized --write-movie "$tmp/f.png"
  --fixed-fps "$fps" --quit-after $((frame + 1)))
[[ -n "$scene" ]] && args+=("$scene")
rc=0
(perl -e 'alarm shift; exec @ARGV' "$timeout" bash "$here/godot.sh" "${args[@]}" \
  ${extra[@]+"${extra[@]}"} >"$log" 2>&1 || exit $?) 2>/dev/null || rc=$?
perl -pi -e 's/\e\[[0-9;]*m//g' "$log"
if [[ $rc -eq 142 ]]; then
  echo "timed out after ${timeout}s" >&2
  exit 124
fi

# Movie Maker numbers frames f00000000.png, f00000001.png, …
src=$(printf '%s/f%08d.png' "$tmp" "$frame")
if [[ ! -f "$src" ]]; then
  echo "frame $frame was not written (godot status $rc)" >&2
  tail -n 20 "$log" >&2
  exit 1
fi
mkdir -p "$(dirname "$out")"
cp "$src" "$out"
if [[ $every -gt 0 ]]; then
  for ((i = 0; i < frame; i += every)); do
    cp "$(printf '%s/f%08d.png' "$tmp" "$i")" "${out%.png}-$(printf '%04d' "$i").png"
  done
fi

size=$(python3 -c 'import struct,sys; d=open(sys.argv[1],"rb").read(24); print("%dx%d" % struct.unpack(">II", d[16:24]))' "$out")
echo "wrote $out ($size, frame $frame at ${fps} fps)"
if grep -qE '^(SCRIPT ERROR|USER SCRIPT ERROR|ERROR|USER ERROR)' "$log"; then
  echo "--- errors while rendering ---"
  grep -A3 -E '^(SCRIPT ERROR|USER SCRIPT ERROR|ERROR|USER ERROR)' "$log" | head -n 40
  exit 1
fi
