#!/usr/bin/env bash
# Convert every audio file in a folder with soundcraft-cli convert, into another folder.
#
# Usage: sc_convert.sh IN_DIR OUT_DIR [--ext wav|aiff|flac] [--overwrite] [convert flags...]
#   convert flags pass through: --bit-depth 16|24|32f --rate HZ --normalize --dither|--no-dither
#
# Not recursive. Refuses OUT_DIR == IN_DIR (convert writes in place without asking) and
# existing outputs unless --overwrite. Each output is read back with `soundcraft-cli info`;
# the last line is a JSON summary. Exit 1 if any file failed.
set -euo pipefail

if [ $# -lt 2 ]; then
  sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'
  exit 2
fi
in_dir=$1
out_dir=$2
shift 2

ext=""
overwrite=0
flags=()
while [ $# -gt 0 ]; do
  case $1 in
    --ext) ext=$2; shift 2 ;;
    --overwrite) overwrite=1; shift ;;
    *) flags+=("$1"); shift ;;
  esac
done

cli=${SOUNDCRAFT_CLI:-$(command -v soundcraft-cli || echo "$HOME/.local/bin/soundcraft-cli")}
[ -x "$cli" ] || { echo "error: soundcraft-cli not found" >&2; exit 1; }
[ -d "$in_dir" ] || { echo "error: $in_dir is not a folder" >&2; exit 1; }
mkdir -p "$out_dir"
in_abs=$(cd "$in_dir" && pwd -P)
out_abs=$(cd "$out_dir" && pwd -P)
if [ "$in_abs" = "$out_abs" ]; then
  echo "error: output folder is the input folder; convert would overwrite the sources" >&2
  exit 1
fi

ok=0
failed=0
for src in "$in_abs"/*; do
  [ -f "$src" ] || continue
  name=$(basename "$src")
  case $(printf '%s' "${name##*.}" | tr '[:upper:]' '[:lower:]') in
    wav|wave|aif|aiff|flac) ;;
    *) continue ;;
  esac
  dst="$out_abs/${name%.*}.${ext:-${name##*.}}"
  if [ -e "$dst" ] && [ "$overwrite" -eq 0 ]; then
    echo "skip $name: $dst exists (use --overwrite)" >&2
    failed=$((failed + 1))
    continue
  fi
  if "$cli" convert "$src" "$dst" ${flags[@]+"${flags[@]}"} >/dev/null \
      && meta=$("$cli" info "$dst"); then
    printf '%s -> %s %s\n' "$name" "$(basename "$dst")" \
      "$(printf '%s' "$meta" | tr -d ' \n' | sed 's/"bwf":null,//')"
    ok=$((ok + 1))
  else
    echo "FAILED $name" >&2
    failed=$((failed + 1))
  fi
done

printf '{"converted": %d, "failed": %d, "out_dir": "%s"}\n' "$ok" "$failed" "$out_abs"
[ "$failed" -eq 0 ]
