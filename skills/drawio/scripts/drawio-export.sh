#!/usr/bin/env bash
# Headless export and conversion through the draw.io desktop CLI. Works whether
# or not the draw.io GUI is running, and needs no control port.
#
#   bash drawio-export.sh INPUT OUTPUT [extra draw.io CLI flags...]
#
# The output extension picks the format: .png .jpg .svg .pdf .html, or
# .drawio to convert a Mermaid (.mmd), CSV or Visio (.vsdx) input into an
# editable, uncompressed diagram. Useful extras: --layout verticalFlow,
# -b 10 (border), -s 2 (scale), -t (transparent), -a (all pages, pdf),
# -p 2 (page 2, images), -e (embed the diagram in png/svg/pdf).
set -euo pipefail

APP="${DRAWIO_APP:-/Applications/draw.io.app}"
BIN="$APP/Contents/MacOS/draw.io"

if [[ $# -lt 2 ]]; then
  echo "usage: drawio-export.sh INPUT OUTPUT [draw.io flags...]" >&2
  exit 2
fi
if [[ ! -x "$BIN" ]]; then
  echo "draw.io not found at $APP — install it (brew install --cask drawio) or set DRAWIO_APP" >&2
  exit 2
fi

in="$1" out="$2"
shift 2
ext="${out##*.}"
case "$ext" in
  drawio) fmt=(-f xml -u) ;;
  png|jpg|svg|pdf|html) fmt=(-f "$ext") ;;
  *) echo "unsupported output extension: .$ext" >&2; exit 2 ;;
esac

mkdir -p "$(dirname "$out")"
# The CLI prints Electron sandbox noise on stderr; keep only real messages.
"$BIN" -x "${fmt[@]}" "$@" -o "$out" "$in" 2>&1 | grep -v -e sandbox_extension -e '^$' || true

if [[ ! -s "$out" ]]; then
  echo "export failed: $out was not written" >&2
  exit 1
fi
echo "$out"
