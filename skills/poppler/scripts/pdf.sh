#!/usr/bin/env bash
# Environment check for the poppler skill: tool paths and versions.
#   bash pdf.sh --check
set -u

if [[ "${1:-}" != "--check" ]]; then
  echo "usage: bash pdf.sh --check" >&2
  exit 2
fi

missing=0
for t in pdfinfo pdffonts pdftotext pdfimages pdftoppm pdftocairo pdfseparate pdfunite; do
  if ! command -v "$t" >/dev/null 2>&1; then
    echo "MISSING $t  -> brew install poppler  (Debian/Ubuntu: apt install poppler-utils)"
    missing=1
  fi
done
if command -v pdfinfo >/dev/null 2>&1; then
  echo "poppler: $(pdfinfo -v 2>&1 | head -1 | awk '{print $3}')  ($(command -v pdfinfo))"
fi
if command -v qpdf >/dev/null 2>&1; then
  echo "qpdf:    $(qpdf --version | head -1 | awk '{print $3}')  ($(command -v qpdf))"
else
  echo "MISSING qpdf  -> brew install qpdf  (Debian/Ubuntu: apt install qpdf)"
  missing=1
fi
if command -v python3 >/dev/null 2>&1; then
  echo "python3: $(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
else
  echo "MISSING python3 (3.9+) for the helper scripts"
  missing=1
fi
if command -v verapdf >/dev/null 2>&1; then
  echo "verapdf: available (optional PDF/A validation)"
fi
exit "$missing"
