#!/usr/bin/env bash
# Run MuseScore Studio 4's CLI headless with a timeout, judging success by the
# output file rather than the exit code.
#
#   mscore-run.sh [--timeout S] [mscore options] -o OUT INPUT   convert; checks OUT exists
#   mscore-run.sh [--timeout S] --score-meta INPUT               any stdout mode, passed through
#   mscore-run.sh --which                                        print the binary in use
#
# mscore 4.x may abort (rc 134) at shutdown after writing its output, and some
# modes write nothing at all; this wrapper exits 0 only when every -o target
# (PNG/SVG: OUT-1.png, OUT-2.png ...) exists, is non-empty and is newer than the
# run's start. Exit 1 on a missing output or timeout, 2 on usage errors.
# Binary lookup: $MSCORE_BIN, /Applications/MuseScore*.app, mscore4/mscore on PATH.
set -euo pipefail

timeout_s=300
if [[ "${1:-}" == "--timeout" ]]; then timeout_s="$2"; shift 2; fi
case "${1:-}" in
  ""|-h|--help) sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
esac

find_mscore() {
  if [[ -n "${MSCORE_BIN:-}" ]]; then
    [[ -x "$MSCORE_BIN" ]] && { echo "$MSCORE_BIN"; return; }
    echo "MSCORE_BIN=$MSCORE_BIN is not executable" >&2; return 1
  fi
  local app
  for app in "/Applications/MuseScore 4.app" "/Applications/MuseScore Studio 4.app" \
             /Applications/MuseScore*.app "$HOME"/Applications/MuseScore*.app; do
    if [[ -x "$app/Contents/MacOS/mscore" ]]; then echo "$app/Contents/MacOS/mscore"; return; fi
  done
  local n
  for n in mscore4portable mscore4 musescore4 mscore musescore; do
    command -v "$n" 2>/dev/null && return
  done
  echo "MuseScore Studio 4 not found: install it (Muse Hub / musescore.org) or set MSCORE_BIN" >&2
  return 1
}
mscore=$(find_mscore) || exit 2
if [[ "$1" == "--which" ]]; then echo "$mscore"; exit 0; fi

outs=()
prev=""
for arg in "$@"; do
  if [[ "$prev" == "-o" || "$prev" == "--export-to" ]]; then outs+=("$arg"); fi
  prev="$arg"
done

stamp=$(mktemp "${TMPDIR:-/tmp}/mscore-run.XXXXXX")
trap 'rm -f "$stamp"' EXIT
# back-date the stamp: bash 3.2's -nt compares whole seconds, so an output written
# within the same second as the stamp would otherwise count as stale
perl -e '$t = time - 2; utime $t, $t, shift' "$stamp"
for o in "${outs[@]+"${outs[@]}"}"; do
  case "$o" in
    *.png|*.svg|*.PNG|*.SVG) rm -f "${o%.*}"-[0-9]*."${o##*.}" ;;  # stale pages would pass the check
  esac
done

set +e
# perl supervisor: a portable timeout (macOS has no timeout(1)), and it reports a
# signal death as a plain exit code so bash prints no "Abort trap: 6" job notice.
perl -e '
  my $t = shift; my $pid = fork // die "fork: $!";
  if (!$pid) { exec @ARGV or die "exec: $!\n" }
  $SIG{ALRM} = sub { kill "KILL", $pid; waitpid $pid, 0; exit 124 };
  alarm $t; waitpid $pid, 0; my $s = $?;
  exit($s & 127 ? 128 + ($s & 127) : $s >> 8);
' "$timeout_s" "$mscore" "$@" 2> >(grep -v -E '^(\[[0-9]+:[0-9]+:|qt\.|QML|Debug|Warning: QT_|libc\+\+abi: terminating)' >&2)
rc=$?
set -e
if [[ $rc -eq 124 ]]; then echo "mscore timed out after ${timeout_s}s" >&2; exit 1; fi
[[ ${#outs[@]} -eq 0 ]] && exit "$rc"

status=0
for o in "${outs[@]}"; do
  case "$o" in
    *.png|*.svg|*.PNG|*.SVG) pages=( "${o%.*}"-[0-9]*."${o##*.}" ) ;;
    *) pages=( "$o" ) ;;
  esac
  good=0
  for p in "${pages[@]}"; do
    if [[ -s "$p" && "$p" -nt "$stamp" ]]; then good=1; echo "wrote $p"; fi
  done
  if [[ $good -eq 0 ]]; then echo "FAIL no output for $o (mscore rc=$rc)" >&2; status=1; fi
done
[[ $status -eq 0 && $rc -ne 0 ]] && echo "note: mscore exited $rc after writing its output (known 4.x shutdown abort)" >&2
exit "$status"
