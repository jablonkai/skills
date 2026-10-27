#!/bin/bash
# pf.sh — run pdfcraft-cli with the OCR models found.
#
#   pf.sh <subcommand> [args…]   same as pdfcraft-cli, with PDFCRAFT_MODELS set
#   pf.sh --doctor               version, CLI path, OCR availability
#
# ~/.local/bin/pdfcraft-cli is a symlink and looks for its OCR models next to the
# link, so OCR (ocr_*, batch --steps ocr) fails unless PDFCRAFT_MODELS points at
# the app bundle. An exported PDFCRAFT_MODELS is left alone.
set -euo pipefail

APP_MODELS=/Applications/PdfCraft.app/Contents/Resources/models

CLI=$(command -v pdfcraft-cli || true)
if [[ -z $CLI && -x $HOME/.local/bin/pdfcraft-cli ]]; then
  CLI=$HOME/.local/bin/pdfcraft-cli
fi
if [[ -z $CLI ]]; then
  echo "error: pdfcraft-cli not found (expected on PATH or at ~/.local/bin/pdfcraft-cli)" >&2
  exit 2
fi

if [[ -z ${PDFCRAFT_MODELS:-} && -d $APP_MODELS ]]; then
  export PDFCRAFT_MODELS=$APP_MODELS
fi

if [[ ${1:-} == --doctor ]]; then
  echo "cli:     $CLI"
  echo "version: $("$CLI" --version | head -n 1)"
  echo "models:  ${PDFCRAFT_MODELS:-<unset>}"
  status=$("$CLI" run ocr_status)
  if [[ $status == *'"available": true'* ]]; then
    echo "ocr:     available"
  else
    echo "ocr:     NOT available (install PdfCraft.app or set PDFCRAFT_MODELS)"
    exit 1
  fi
  exit 0
fi

exec "$CLI" "$@"
