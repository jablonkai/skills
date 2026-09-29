#!/usr/bin/env bash
# Import, parse-check and run a Godot 4 project headless, then judge the run from
# the log. Godot exits 0 even after script errors, so this script greps the log and
# exits non-zero when it finds any.
#
#   bash gd-run.sh PROJECT_DIR [options] [-- user args]
#
#   --scene RES      run this scene instead of the main scene (res://levels/one.tscn)
#   --test SCRIPT    run a SceneTree test script (--script); it must call quit(code),
#                    and that exit code is part of the verdict. Lines it prints that
#                    start with TEST, PASS or FAIL are echoed
#   --frames N       quit after N frames (default 120, at a fixed 60 fps: 2 s of game time)
#   --timeout SEC    kill Godot after SEC seconds per step (default 90)
#   --check          only import, verify scenes (gd-verify.py) and parse-check every
#                    .gd file; do not run
#   --no-import      skip the import step (faster when nothing new was added)
#   --no-check       skip the scene verification and the parse check
#   --log FILE       keep the combined log here (default: a temp file, path printed)
#   -- ARGS          passed to the game as user args (OS.get_cmdline_user_args())
#
# Exit codes: 0 clean, 1 errors in the log or the test script failed,
#             2 usage or install problem, 124 a step timed out.
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
GODOT=(bash "$here/godot.sh")

usage() { awk 'NR > 1 && !/^#/ { exit } NR > 1 { sub(/^# ?/, ""); print }' "${BASH_SOURCE[0]}"; exit 2; }

[[ $# -ge 1 ]] || usage
case "$1" in -h | --help) usage ;; esac
project=$1
shift
scene="" test="" frames=120 timeout=90 check_only=0 do_import=1 do_check=1 log=""
extra=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --scene) scene=$2; shift 2 ;;
    --test) test=$2; shift 2 ;;
    --frames) frames=$2; shift 2 ;;
    --timeout) timeout=$2; shift 2 ;;
    --check) check_only=1; shift ;;
    --no-import) do_import=0; shift ;;
    --no-check) do_check=0; shift ;;
    --log) log=$2; shift 2 ;;
    --) shift; extra=(-- "$@"); break ;;
    -h | --help) usage ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

if [[ ! -f "$project/project.godot" ]]; then
  echo "no project.godot in $project" >&2
  exit 2
fi
project=$(cd "$project" && pwd)
[[ -n "$log" ]] || log=$(mktemp -t gd-run).log
: >"$log"

# macOS ships no timeout(1); perl's alarm survives exec and SIGALRM ends Godot.
run_step() {
  local name=$1 rc=0
  shift
  echo "## $name" >>"$log"
  # The subshell swallows bash's "Alarm clock" notice when the alarm fires.
  (perl -e 'alarm shift; exec @ARGV' "$timeout" "${GODOT[@]}" "$@" >>"$log" 2>&1 || exit $?) 2>/dev/null || rc=$?
  # Strip ANSI colours so the log greps cleanly.
  perl -pi -e 's/\e\[[0-9;]*m//g' "$log"
  if [[ $rc -eq 142 ]]; then
    echo "TIMEOUT: $name did not finish in ${timeout}s" >>"$log"
    return 124
  fi
  return "$rc"
}

common=(--headless --path "$project" -l en)
status=0

if [[ $do_import -eq 1 ]]; then
  run_step import "${common[@]}" --import || status=$?
fi
if [[ $status -ne 124 && $do_check -eq 1 ]]; then
  # Static scene checks first: a [connection] to a missing method is silent at runtime.
  { echo "## verify"; python3 "$here/gd-verify.py" "$project" | grep -vE '^(OK|---)'; } >>"$log" || true
  run_step check "${common[@]}" --script "$here/gd-check.gd" || status=$?
fi
if [[ $status -ne 124 && $check_only -eq 0 ]]; then
  if [[ -n "$test" ]]; then
    run_step "test $test" "${common[@]}" --fixed-fps 60 --script "$test" ${extra[@]+"${extra[@]}"} || status=$?
  else
    args=("${common[@]}" --fixed-fps 60 --quit-after "$frames")
    [[ -n "$scene" ]] && args+=("$scene")
    run_step "run ${scene:-main scene}" "${args[@]}" ${extra[@]+"${extra[@]}"} || status=$?
  fi
fi

# Every engine and script error starts with one of these prefixes; the lines that
# follow (at:, GDScript backtrace) say where. A node whose parent path does not
# resolve is only a warning to Godot, but the node is gone, so count it as an error.
error_re='^(SCRIPT ERROR|USER SCRIPT ERROR|ERROR|USER ERROR|Parse Error|GD-CHECK FAIL|TIMEOUT|WARNING: Parent path .* has vanished)'
warning_re='^(WARNING|USER WARNING)'
errors=$(grep -cE "$error_re" "$log" || true)
warnings=$(grep -E "$warning_re" "$log" | grep -cvE "$error_re" || true)

# Step headers, the parse-check summary, and what a test script prints as TEST/PASS/FAIL.
grep -E '^(## |GD-CHECK [0-9]|TEST|PASS|FAIL)' "$log" || true
if [[ $errors -gt 0 ]]; then
  echo "--- errors ---"
  grep -A3 -E "$error_re" "$log" | grep -vE '^\s*$' | head -n 60
fi
if [[ $warnings -gt 0 ]]; then
  echo "--- warnings ---"
  grep -A1 -E "$warning_re" "$log" | grep -vE "$error_re" | grep -vE '^(--|\s*$)' | sort -u | head -n 20
fi
echo "--- $errors error(s), $warnings warning(s); godot status $status; log: $log"

if [[ $status -eq 124 ]]; then
  [[ -n "$test" ]] && echo "hint: a script error aborts the function, so quit() was never reached" >&2
  exit 124
fi
if [[ $errors -gt 0 || $status -ne 0 ]]; then
  exit 1
fi
exit 0
