#!/usr/bin/env bash
# Locate yt-dlp and report what it needs to work.
#
#   bash ytdl.sh --check      path, version, install method and its update command,
#                             ffmpeg/ffprobe and the JavaScript runtime; exit 2 if yt-dlp is missing
#   bash ytdl.sh [args...]    run yt-dlp with the given arguments
#
# Override the binary with YTDLP=/path/to/yt-dlp.
set -euo pipefail

BIN=""
for c in "${YTDLP:-}" "$(command -v yt-dlp 2>/dev/null || true)" /opt/homebrew/bin/yt-dlp /usr/local/bin/yt-dlp; do
  if [[ -n "$c" && -x "$c" ]]; then BIN=$c; break; fi
done
if [[ -z "$BIN" ]]; then
  echo "yt-dlp not found. Install: brew install yt-dlp   (or: python3 -m pip install -U 'yt-dlp[default]')" >&2
  exit 2
fi

if [[ "${1:-}" != "--check" ]]; then
  exec "$BIN" "$@"
fi

real=$(python3 -c 'import os,sys;print(os.path.realpath(sys.argv[1]))' "$BIN")
if [[ "$real" == */Cellar/* ]]; then
  method=brew; update="brew update && brew upgrade yt-dlp"
elif [[ "$real" == */pipx/* ]]; then
  method=pipx; update="pipx upgrade yt-dlp"
elif head -c 200 "$real" 2>/dev/null | head -n 1 | grep -q python; then
  method=pip; update="python3 -m pip install -U 'yt-dlp[default]'"
else
  method=binary; update="$BIN -U"
fi

echo "yt-dlp:  $BIN  (version $("$BIN" --version))"
echo "install: $method  → update with: $update"
[[ $method == brew ]] && echo "         (yt-dlp -U does not work on a Homebrew install)"

for tool in ffmpeg ffprobe; do
  p=$(command -v "$tool" || true)
  if [[ -n "$p" ]]; then
    echo "$tool: $p  ($("$p" -hide_banner -version | head -n 1 | awk '{print $3}'))"
  else
    echo "$tool: MISSING — merging, sections, -x and --convert-subs need it: brew install ffmpeg"
  fi
done

js=""
for r in deno node bun quickjs; do
  p=$(command -v "$r" || true)
  [[ -n "$p" ]] && js="$js $r($p)"
done
if [[ -n "$js" ]]; then
  echo "js runtimes:$js  (yt-dlp uses deno by default; others via --js-runtimes NAME)"
else
  echo "js runtimes: NONE — YouTube downloads will lack formats or fail: brew install deno"
fi
