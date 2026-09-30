#!/usr/bin/env bash
# Entry point for checks and housekeeping around headless LibreOffice.
#
#   bash lo.sh --check          soffice path and version, profile, helper tools, instances
#   bash lo.sh --stop           kill soffice processes running on the skill's profile
#   bash lo.sh --reset-profile  stop, then delete the skill profile (rebuilt on next run)
#
# Stop path: every call ends at its timeout (LO_TIMEOUT, default 300 s) and the driver
# kills the soffice it started; --stop clears leftovers. Only processes started with the
# skill's own profile are touched — never the user's LibreOffice window.
set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

profile() {
  python3 -c 'import sys; sys.path.insert(0, sys.argv[1]); import lo_run; print(lo_run.PROFILE)' "$HERE"
}

check() {
  local out soffice fw
  if ! out=$(python3 "$HERE/lo_run.py" --version 2>&1); then
    echo "$out" >&2
    exit 2
  fi
  echo "$out"
  soffice=$(sed -n 's/^soffice: //p' <<<"$out")
  if pgrep -f "$(dirname "$soffice")/soffice" >/dev/null 2>&1; then
    if pgrep -fl "$(dirname "$soffice")/soffice" | grep -qv UserInstallation; then
      echo "user instance: running (fine — the skill uses its own profile)"
    fi
    if pgrep -f "libreoffice-skill" >/dev/null 2>&1 || pgrep -f "UserInstallation=file://$(profile)" >/dev/null 2>&1; then
      echo "skill instance: RUNNING — a killed run left it; bash lo.sh --stop"
    fi
  fi
  for tool in pdfinfo pdffonts pdftotext pdftoppm pdfunite verapdf; do
    if command -v "$tool" >/dev/null 2>&1; then echo "$tool: yes"; else echo "$tool: no"; fi
  done
  # macOS: the bundled python breaks once it writes .pyc files into its signed
  # framework (it is then killed on start). The skill never uses it; report only.
  fw="${soffice%/MacOS/soffice}/Frameworks/LibreOfficePython.framework"
  if [[ -d "$fw" ]] && command -v codesign >/dev/null 2>&1; then
    if codesign --verify "$fw" >/dev/null 2>&1; then
      echo "bundled python: signature ok"
    else
      echo "bundled python: signature broken (not used by the skill; reinstall LibreOffice to fix)"
    fi
  fi
}

case "${1:-}" in
  --check) check ;;
  --stop) python3 "$HERE/lo_run.py" --stop ;;
  --reset-profile)
    python3 "$HERE/lo_run.py" --stop
    p=$(profile)
    case "$p" in
      */libreoffice-skill/profile|*/libreoffice-skill*) rm -rf "$p"; echo "removed $p" ;;
      *) echo "refusing to delete unexpected profile path $p (LO_PROFILE)" >&2; exit 2 ;;
    esac
    ;;
  *)
    sed -n '2,10p' "$0" >&2
    exit 2
    ;;
esac
