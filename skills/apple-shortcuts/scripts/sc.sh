#!/usr/bin/env bash
# Check the Shortcuts setup.
#
#   bash sc.sh --check   macOS and Shortcuts versions, the CLI, how many shortcuts and folders
#                        exist, and whether Automation access to Shortcuts Events works
#
# Exit 0 when the CLI works, 2 when the shortcuts CLI is missing (macOS < 12).
set -euo pipefail

if [[ "${1:-}" != "--check" ]]; then
  echo "usage: bash sc.sh --check" >&2
  exit 2
fi

echo "macOS: $(sw_vers -productVersion) ($(sw_vers -buildVersion))"
echo "Shortcuts.app: $(defaults read /System/Applications/Shortcuts.app/Contents/Info.plist CFBundleShortVersionString 2>/dev/null || echo missing)"

if ! command -v shortcuts >/dev/null 2>&1; then
  echo "shortcuts CLI: missing (needs macOS 12 Monterey or later)"
  exit 2
fi
echo "shortcuts CLI: $(command -v shortcuts)"
echo "shortcuts: $(shortcuts list | grep -c . || true), folders: $(shortcuts list --folders | grep -c . || true)"

if out=$(osascript -l JavaScript -e 'Application("Shortcuts Events").shortcuts.length' 2>&1); then
  echo "automation (Shortcuts Events): ok ($out shortcuts)"
else
  echo "automation (Shortcuts Events): denied or failed: $out"
  echo "  allow it in System Settings > Privacy & Security > Automation; only sc-list.py's accepts_input needs it"
fi

for tool in aea aa openssl; do
  command -v "$tool" >/dev/null 2>&1 || echo "warning: $tool missing; sc-decode.py cannot read signed files"
done
