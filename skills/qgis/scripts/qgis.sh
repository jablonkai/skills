#!/usr/bin/env bash
# Entry point for headless QGIS: finds the app bundle, sets the environment its
# bundled tools need outside the GUI, and runs one short process with a timeout.
#
#   bash qgis.sh check                     app path, versions, PROJ db, Python, profile
#   bash qgis.sh python SCRIPT [ARGS...]   run a PyQGIS script on the bundled Python 3
#   bash qgis.sh process ARGS...           qgis_process (e.g. run native:buffer -- ...)
#   bash qgis.sh env                       print the exports (eval "$(bash qgis.sh env)")
#   bash qgis.sh open FILE                 open a .qgz/.gpkg/... in the QGIS GUI
#
# QGIS_APP     override the bundle (default: newest /Applications/QGIS*.app)
# QGIS_TIMEOUT seconds before the process is killed (default 300)
# QGIS_PROFILE_DIR  config dir for the headless runs (default: a skill-owned dir, so
#              the user's plugins and settings are never loaded or modified)
# QGIS_VERBOSE=1 keeps the known-harmless stderr noise instead of filtering it
set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

find_app() {
  if [[ -n "${QGIS_APP:-}" ]]; then
    [[ -x "$QGIS_APP/Contents/MacOS/qgis_process" ]] || {
      echo "QGIS_APP=$QGIS_APP has no Contents/MacOS/qgis_process" >&2
      exit 2
    }
    printf '%s' "${QGIS_APP%/}"
    return
  fi
  local app
  app=$(find /Applications "$HOME/Applications" -maxdepth 1 -name 'QGIS*.app' 2>/dev/null | sort -V | tail -n 1)
  if [[ -z "$app" ]]; then
    echo "QGIS not found in /Applications. Install it (brew install --cask qgis, or the" >&2
    echo "installer from qgis.org) or set QGIS_APP=/path/to/QGIS.app" >&2
    exit 2
  fi
  printf '%s' "$app"
}

APP=$(find_app)
C="$APP/Contents"
PROFILE_DIR=${QGIS_PROFILE_DIR:-"$HOME/Library/Caches/qgis-skill/profile"}
TIMEOUT=${QGIS_TIMEOUT:-300}

setup_env() {
  # Without PROJ_DATA qgis_process prints "Cannot find proj.db" and every EPSG lookup
  # silently fails; without PYTHONHOME=Contents/Frameworks the bundled python3.12 dies
  # on "No module named 'encodings'" (the bundle's own MacOS/python wrapper sets the
  # same). QGIS_PREFIX_PATH must be the .app itself, not Contents/MacOS, or
  # pkgDataPath (SVG markers, north arrows, styles) points nowhere.
  export PROJ_DATA="$C/Resources/qgis/proj"
  export PROJ_LIB="$PROJ_DATA"
  export GDAL_DATA="$C/Resources/qgis/gdal"
  export PYTHONHOME="$C/Frameworks"
  export PYTHONPATH="$C/Resources/qgis/python/plugins:$HERE"
  export QGIS_PREFIX_PATH="$APP"
  export QGIS_CUSTOM_CONFIG_PATH="$PROFILE_DIR"
  export QT_QPA_PLATFORM=offscreen
  export PYTHONDONTWRITEBYTECODE=1
  mkdir -p "$PROFILE_DIR"
}

python_bin() {
  local p
  p=$(find "$C/MacOS" -maxdepth 1 -name 'python3*' -type f | sort -V | tail -n 1)
  [[ -n "$p" ]] || { echo "no bundled python in $C/MacOS" >&2; exit 2; }
  printf '%s' "$p"
}

# Lines every headless run prints that mean nothing; QGIS_VERBOSE=1 keeps them.
NOISE='^(Could not find platform (in)?dependent libraries|qt\.qpa\.fonts:|ERROR 6: The PNG driver does not support update access|Application path not initialized|QStandardPaths:)'

run_limited() {
  # Runs "$@" with a wall-clock limit and the noise filter on stderr; returns its
  # exit status (124 on timeout, like coreutils timeout). perl's alarm survives the
  # exec, so no watcher process is left holding the output pipe open.
  local status=0
  if [[ "${QGIS_VERBOSE:-0}" == 1 ]]; then
    perl -e 'alarm shift; exec @ARGV or die "exec $ARGV[0]: $!\n"' "$TIMEOUT" "$@" || status=$?
  else
    { perl -e 'alarm shift; exec @ARGV or die "exec $ARGV[0]: $!\n"' "$TIMEOUT" "$@" 2>&1 1>&3 3>&- |
        { grep -Ev "$NOISE" || true; } >&2; } 3>&1 || status=$?
  fi
  if [[ $status -eq 142 ]]; then
    echo "qgis.sh: killed after ${TIMEOUT}s (QGIS_TIMEOUT)" >&2
    return 124
  fi
  return "$status"
}

cmd=${1:-}
[[ $# -gt 0 ]] && shift
case "$cmd" in
  check)
    setup_env
    echo "app: $APP"
    echo "version: $(defaults read "$C/Info.plist" CFBundleShortVersionString 2>/dev/null || echo unknown)"
    echo "qgis_process: $C/MacOS/qgis_process"
    echo "python: $(python_bin)"
    echo "profile: $PROFILE_DIR"
    run_limited "$C/MacOS/qgis_process" --version 2>/dev/null | grep -E '^(QGIS |Qt |Python |GDAL|PROJ|EPSG)' || true
    if [[ -f "$PROJ_DATA/proj.db" ]]; then echo "proj.db: ok"; else echo "proj.db: MISSING ($PROJ_DATA)"; exit 2; fi
    run_limited "$(python_bin)" -c 'from qgis.core import Qgis; print("pyqgis:", Qgis.version())'
    ;;
  python)
    [[ $# -ge 1 ]] || { echo "usage: qgis.sh python SCRIPT [ARGS...]" >&2; exit 2; }
    setup_env
    run_limited "$(python_bin)" "$@"
    ;;
  process)
    setup_env
    # No --skip-loading-plugins: it also drops the core "processing" plugin, which
    # provides every gdal:* algorithm. The skill-owned profile already keeps the
    # user's own plugins out.
    run_limited "$C/MacOS/qgis_process" "$@"
    ;;
  env)
    setup_env
    for v in PROJ_DATA PROJ_LIB GDAL_DATA PYTHONHOME PYTHONPATH QGIS_PREFIX_PATH QGIS_CUSTOM_CONFIG_PATH QT_QPA_PLATFORM PYTHONDONTWRITEBYTECODE; do
      printf 'export %s=%q\n' "$v" "${!v}"
    done
    printf 'export QGIS_PYTHON=%q QGIS_PROCESS=%q\n' "$(python_bin)" "$C/MacOS/qgis_process"
    ;;
  open)
    [[ $# -ge 1 ]] || { echo "usage: qgis.sh open FILE" >&2; exit 2; }
    open -a "$APP" "$@"
    ;;
  *)
    sed -n '2,15p' "$0" >&2
    exit 2
    ;;
esac
