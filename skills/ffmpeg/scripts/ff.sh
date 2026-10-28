#!/usr/bin/env bash
# Locate ffmpeg builds and report what each can do.
#
#   bash ff.sh --check        paths, versions, key encoders and filters; exit 2 if ffmpeg is missing
#   bash ff.sh [args...]      run the default ffmpeg with the given arguments
#
# Override the default with FFMPEG=/path/to/ffmpeg.
set -euo pipefail

candidates() {
  local c seen=""
  for c in "${FFMPEG:-}" "$(command -v ffmpeg 2>/dev/null || true)" /opt/homebrew/bin/ffmpeg /usr/local/bin/ffmpeg \
    /opt/homebrew/opt/ffmpeg-full/bin/ffmpeg /usr/local/opt/ffmpeg-full/bin/ffmpeg; do
    [[ -n "$c" && -x "$c" ]] || continue
    local real
    real=$(cd "$(dirname "$c")" && pwd -P)/$(basename "$c")
    [[ " $seen " == *" $real "* ]] && continue
    seen="$seen $real"
    printf '%s\n' "$c"
  done
}

BINS=$(candidates)
if [[ -z "$BINS" ]]; then
  echo "ffmpeg not found. Install: brew install ffmpeg   (add ffmpeg-full for subtitles burn-in/drawtext)" >&2
  exit 2
fi
DEFAULT=$(printf '%s\n' "$BINS" | head -n 1)

if [[ "${1:-}" != "--check" ]]; then
  exec "$DEFAULT" "$@"
fi

full_seen=0
while IFS= read -r bin; do
  version=$("$bin" -hide_banner -version | head -n 1 | awk '{print $3}')
  filters=$("$bin" -hide_banner -filters 2>/dev/null | awk '{print $2}')
  encoders=$("$bin" -hide_banner -encoders 2>/dev/null | awk '{print $2}')
  have() { printf '%s\n' "$2" | grep -qx "$1" && printf '%s ' "$1" || true; }
  echo "ffmpeg: $bin  (version $version)"
  printf '  encoders: '
  for e in libx264 libx265 libsvtav1 libvpx-vp9 h264_videotoolbox hevc_videotoolbox prores_videotoolbox prores_ks libopus libmp3lame aac_at; do
    have "$e" "$encoders"
  done
  echo
  printf '  text filters: '
  t=$(for f in subtitles ass drawtext; do have "$f" "$filters"; done)
  echo "${t:-none (no libass/freetype)}"
  [[ "$bin" == *ffmpeg-full* ]] && full_seen=1
done <<<"$BINS"

probe=$(dirname "$DEFAULT")/ffprobe
[[ -x "$probe" ]] || probe=$(command -v ffprobe || true)
echo "ffprobe: ${probe:-MISSING}"
echo "default: $DEFAULT"
if ! "$DEFAULT" -hide_banner -filters 2>/dev/null | awk '{print $2}' | grep -qx subtitles && [[ $full_seen == 0 ]]; then
  echo "note: no build with libass — subtitle burn-in and drawtext need: brew install ffmpeg-full (keg-only, no conflict)"
fi
