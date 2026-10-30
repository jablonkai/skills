#!/usr/bin/env bash
# Environment check for the imagemagick skill: magick 7, format support, font file, Python.
#   bash im.sh --check
set -u

if [[ "${1:-}" != "--check" ]]; then
  echo "usage: bash im.sh --check" >&2
  exit 2
fi

missing=0
if ! command -v magick >/dev/null 2>&1; then
  if command -v convert >/dev/null 2>&1; then
    echo "MISSING magick: only ImageMagick 6 'convert' found -> brew install imagemagick (needs IM 7)"
  else
    echo "MISSING magick -> brew install imagemagick  (Debian/Ubuntu: apt install imagemagick, needs 7.x)"
  fi
  exit 1
fi

echo "magick:  $(magick -version | head -1 | sed 's/^Version: ImageMagick //; s/ https.*//')  ($(command -v magick))"
formats=$(magick -list format 2>/dev/null)
for f in JPEG PNG WEBP AVIF HEIC TIFF JXL; do
  mode=$(printf '%s\n' "$formats" | awk -v f="$f" '{sub(/\*$/, "", $1)} $1 == f {print $3; exit}')
  case "$mode" in
    *w*) printf '  %-5s write ok\n' "$f" ;;
    "")  printf '  %-5s not available\n' "$f" ;;
    *)   printf '  %-5s read only\n' "$f" ;;
  esac
done

fonts=$(magick -list font 2>/dev/null | grep -c 'Font:')
font=""
for f in "${IM_FONT:-}" /System/Library/Fonts/Supplemental/Arial.ttf /System/Library/Fonts/Helvetica.ttc \
         /Library/Fonts/Arial.ttf /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf /usr/share/fonts/TTF/DejaVuSans.ttf; do
  if [[ -n "$f" && -f "$f" ]]; then font=$f; break; fi
done
if [[ "$fonts" -eq 0 ]]; then
  echo "fonts:   none registered (no fontconfig) -> always pass -font /path/to/file.ttf"
else
  echo "fonts:   $fonts registered"
fi
if [[ -n "$font" ]]; then
  echo "font file: $font"
else
  echo "MISSING font file for text and labels -> set IM_FONT=/path/to/font.ttf"
  missing=1
fi

if command -v python3 >/dev/null 2>&1; then
  echo "python3: $(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
else
  echo "MISSING python3 (3.9+) for the helper scripts"
  missing=1
fi
exit "$missing"
