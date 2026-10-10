#!/usr/bin/env bash
# Entry point for the calibre CLIs: finds the app bundle, forces English output and
# runs one short process with a timeout.
#
#   bash calibre.sh check [LIBRARY]        app path, version, library, lock state, epubcheck
#   bash calibre.sh TOOL [ARGS...]         calibredb | ebook-convert | ebook-meta |
#                                          ebook-polish | fetch-ebook-metadata | calibre-server
#   bash calibre.sh py SCRIPT [ARGS...]    run a script on calibre's own Python
#   bash calibre.sh lock [LIBRARY]         is the library held by the GUI or calibre-server?
#   bash calibre.sh env                    print the exports (eval "$(bash calibre.sh env)")
#
# CALIBRE_APP      override the bundle (default /Applications/calibre.app)
# CALIBRE_TIMEOUT  seconds before the process is killed (default 600)
# CALIBRE_LIBRARY  library path or Content server URL used by `lock` and the scripts
set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

find_app() {
  local app=${CALIBRE_APP:-}
  if [[ -z "$app" ]]; then
    for c in /Applications/calibre.app "$HOME/Applications/calibre.app"; do
      [[ -x "$c/Contents/MacOS/calibredb" ]] && { app=$c; break; }
    done
  fi
  if [[ -z "$app" || ! -x "$app/Contents/MacOS/calibredb" ]]; then
    echo "calibre not found. Install it (brew install --cask calibre, or calibre-ebook.com)" >&2
    echo "or set CALIBRE_APP=/path/to/calibre.app" >&2
    exit 2
  fi
  printf '%s' "${app%/}"
}

APP=$(find_app)
BIN="$APP/Contents/MacOS"
UTILS="$APP/Contents/utils.app/Contents/MacOS"
TIMEOUT=${CALIBRE_TIMEOUT:-600}

# calibre localizes every message and, worse, defaults a new book's language to the
# UI locale (a Hungarian Mac tags English books "hun"). Force English for parseable
# output; the scripts always pass --language explicitly.
export CALIBRE_OVERRIDE_LANG=en
export LANG=${LANG:-en_US.UTF-8}
export PYTHONDONTWRITEBYTECODE=1

run_limited() {
  # Runs "$@" with a wall-clock limit; 124 on timeout, like coreutils timeout. perl's
  # alarm survives the exec, so no watcher process is left behind.
  local status=0
  perl -e 'alarm shift; exec @ARGV or die "exec $ARGV[0]: $!\n"' "$TIMEOUT" "$@" || status=$?
  if [[ $status -eq 142 ]]; then
    echo "calibre.sh: killed after ${TIMEOUT}s (CALIBRE_TIMEOUT)" >&2
    return 124
  fi
  return "$status"
}

default_library() {
  "$BIN/calibre-debug" -c 'from calibre.utils.config import prefs; print(prefs["library_path"] or "")' 2>/dev/null
}

lock_state() {
  # calibredb refuses to touch a library another calibre program has open, but for
  # reads it still exits 0 after printing the warning, so look at the message.
  local lib=$1 out
  if [[ "$lib" == http* ]]; then echo "server"; return; fi
  out=$("$BIN/calibredb" --with-library "$lib" list --limit 1 -f title 2>&1 || true)
  if grep -q 'Another calibre program' <<<"$out"; then echo "locked"; else echo "free"; fi
}

server_urls() {
  # Ports calibre (GUI Content server) or calibre-server listen on, as URLs.
  lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null |
    awk '$1 ~ /^calibre/ {n=split($9,a,":"); print "http://127.0.0.1:" a[n]}' | sort -u
}

cmd=${1:-}
[[ $# -gt 0 ]] && shift
case "$cmd" in
  check)
    echo "app: $APP"
    echo "version: $(defaults read "$APP/Contents/Info" CFBundleShortVersionString 2>/dev/null || echo unknown)"
    lib=${1:-${CALIBRE_LIBRARY:-$(default_library)}}
    echo "library: ${lib:-<none configured>}"
    if [[ -n "$lib" ]]; then
      state=$(lock_state "$lib")
      echo "library state: $state"
      if [[ "$state" == locked ]]; then
        urls=$(server_urls | tr '\n' ' ')
        echo "content servers: ${urls:-none listening — close calibre or start its Content server}"
      fi
    fi
    if command -v epubcheck >/dev/null; then echo "epubcheck: $(command -v epubcheck)"
    elif [[ -n "${EPUBCHECK_JAR:-}" ]]; then echo "epubcheck: $EPUBCHECK_JAR"
    else echo "epubcheck: not installed (optional: brew install epubcheck)"; fi
    ;;
  lock)
    lib=${1:-${CALIBRE_LIBRARY:-$(default_library)}}
    state=$(lock_state "$lib")
    echo "$state"
    [[ "$state" == locked ]] && server_urls
    ;;
  py)
    [[ $# -ge 1 ]] || { echo "usage: calibre.sh py SCRIPT [ARGS...]" >&2; exit 2; }
    script=$1; shift
    export CALIBRE_SH="$HERE/calibre.sh" CALIBRE_BIN="$BIN" CALIBRE_UTILS="$UTILS"
    run_limited "$BIN/calibre-debug" -e "$script" -- "$@"
    ;;
  env)
    printf 'export CALIBRE_BIN=%q CALIBRE_UTILS=%q CALIBRE_OVERRIDE_LANG=en\n' "$BIN" "$UTILS"
    # shellcheck disable=SC2016  # $PATH is meant literally, for the eval'ing shell
    printf 'export PATH=%q:"$PATH"\n' "$BIN"
    ;;
  calibredb|ebook-convert|ebook-meta|ebook-polish|fetch-ebook-metadata|calibre-server|calibre-debug|calibre-smtp)
    run_limited "$BIN/$cmd" "$@"
    ;;
  pdfinfo|pdftotext|pdftoppm)
    run_limited "$UTILS/$cmd" "$@"
    ;;
  *)
    sed -n '2,15p' "$0" >&2
    exit 2
    ;;
esac
