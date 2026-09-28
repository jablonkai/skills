#!/usr/bin/env bash
# Run a Python script against the running DaVinci Resolve and print its output.
#
# Usage:
#   resolve-run.sh /abs/path/job.py            run a .py file with resolve, project, ... injected
#   resolve-run.sh -c 'print(project.GetName())'   run inline code
#   resolve-run.sh --ping                      check Resolve is reachable (version, Studio, page)
#   resolve-run.sh --state                     project / timelines / tracks / render queue as JSON
#   resolve-run.sh job.py --arg tl=Main --arg dry=1
#                                              KEY=VALUE strings, read back as ARGS["tl"]
#
# Resolve has its own scripting server, so unlike the app bridges in this repo there is
# nothing to install inside the app: the script runs in a local Python process that talks
# to Resolve through fusionscript. Resolve 21.1+ ships ResolvePython, which imports
# DaVinciResolveScript without any environment setup — it is preferred when present;
# otherwise python3 is used with RESOLVE_SCRIPT_API / RESOLVE_SCRIPT_LIB / PYTHONPATH set.
#
# Env: RESOLVE_PYTHON (force an interpreter), RESOLVE_CONNECT_TIMEOUT seconds (default 20),
# RESOLVE_JOB_TIMEOUT seconds for the whole job (default: none), OUT (output directory,
# injected as OUT).
set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

case "$(uname -s)" in
    Darwin)
        builtin_py="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Applications/ResolvePython"
        api="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
        lib="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
        sep=":"
        ;;
    Linux)
        builtin_py="/opt/resolve/bin/ResolvePython"
        api="/opt/resolve/Developer/Scripting"
        lib="/opt/resolve/libs/Fusion/fusionscript.so"
        sep=":"
        ;;
    MINGW* | MSYS* | CYGWIN*)
        builtin_py="C:/Program Files/Blackmagic Design/DaVinci Resolve/ResolvePython/ResolvePython.exe"
        api="${PROGRAMDATA:-C:/ProgramData}/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting"
        lib="C:/Program Files/Blackmagic Design/DaVinci Resolve/fusionscript.dll"
        sep=";"  # a native Windows python3 splits PYTHONPATH on ';'
        ;;
    *)
        echo "ERROR: unsupported platform $(uname -s)" >&2
        exit 2
        ;;
esac

if [ -n "${RESOLVE_PYTHON:-}" ]; then
    py="$RESOLVE_PYTHON"
elif [ -x "$builtin_py" ]; then
    py="$builtin_py"
else
    # Pre-21.1 install or no bundled interpreter: point a system Python at the SDK module.
    py=$(command -v python3 || true)
    [ -n "$py" ] || { echo "ERROR: neither ResolvePython nor python3 found" >&2; exit 2; }
    export RESOLVE_SCRIPT_API="${RESOLVE_SCRIPT_API:-$api}"
    export RESOLVE_SCRIPT_LIB="${RESOLVE_SCRIPT_LIB:-$lib}"
    export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH$sep}$RESOLVE_SCRIPT_API/Modules/"
fi

rc=0
"$py" "$HERE/resolve_run.py" "$@" || rc=$?
if [ "$rc" -eq 142 ]; then
    cat >&2 <<EOF
ERROR: timed out (connect limit ${RESOLVE_CONNECT_TIMEOUT:-20}s, job limit ${RESOLVE_JOB_TIMEOUT:-none}s).
       If Resolve stopped answering: a menu, context menu or dialog may be open in its
       window (that stalls every script call — ask the user to close it), Resolve may be
       starting, quitting or frozen, or Preferences > System > General > External scripting
       using is not Local. Run --ping to tell a slow job from a stuck Resolve.
EOF
fi
exit "$rc"
