#!/usr/bin/env bash
# Locate HandBrakeCLI and run it. Same lookup order as hb_lib.find_cli().
#
#   bash hb.sh --check        print path, version and key encoders; exit 2 if missing
#   bash hb.sh [args...]      run HandBrakeCLI with the given arguments
#
# Override the lookup with HANDBRAKE_CLI=/path/to/HandBrakeCLI.
set -euo pipefail

find_cli() {
  local candidate
  for candidate in \
    "${HANDBRAKE_CLI:-}" \
    "$(command -v HandBrakeCLI 2>/dev/null || true)" \
    /opt/homebrew/bin/HandBrakeCLI \
    /usr/local/bin/HandBrakeCLI \
    /Applications/HandBrakeCLI; do
    if [[ -n "$candidate" && -x "$candidate" ]]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

if ! BIN=$(find_cli); then
  echo "HandBrakeCLI not found. The HandBrake.app GUI does not include it." >&2
  echo "Install: brew install handbrake   (or HandBrakeCLI-<version>.dmg from https://handbrake.fr/downloads2.php)" >&2
  echo "Or set HANDBRAKE_CLI=/path/to/HandBrakeCLI" >&2
  exit 2
fi

if [[ "${1:-}" == "--check" ]]; then
  version=$("$BIN" --version 2>/dev/null | grep -E '^HandBrake ' | head -n 1 || true)
  echo "cli: $BIN"
  echo "version: ${version:-unknown}"
  encoders=$("$BIN" --help 2>/dev/null |
    awk '/-e, --encoder/{on=1; next} on && /^ +--/{on=0} on {print $1}' | tr '\n' ' ' || true)
  echo "video encoders: $encoders"
  for tool in ffprobe ffmpeg; do
    if command -v "$tool" >/dev/null 2>&1; then echo "$tool: $(command -v "$tool")"; else echo "$tool: MISSING (brew install ffmpeg) — needed for hb-verify.py"; fi
  done
  exit 0
fi

exec "$BIN" "$@"
