"""Connect to the running DaVinci Resolve and run a job script in a prepared namespace.

Invoked by resolve-run.sh, which picks the interpreter. See that file for usage.

Injected into the job script: resolve, fusion, pm (ProjectManager), project, mp (MediaPool),
timeline (current, may be None), OUT, ARGS, need, ResolveError, H (the Helpers object), and
every helper in resolve_helpers.EXPORTED as a bare function.
"""

import json
import os
import signal
import sys
import threading
import traceback

sys.dont_write_bytecode = True  # keep __pycache__ out of the installed skill directory
# Stream prints as they happen: when a call blocks (an open dialog in Resolve stalls its
# script server), the output so far shows which step it stuck on.
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import resolve_helpers  # noqa: E402

USAGE = "usage: resolve-run.sh <job.py> | -c '<code>' | --ping | --state  [--arg KEY=VALUE ...]"


def connect(timeout):
    # scriptapp() — and any call after it — blocks while Resolve is starting or quitting,
    # refuses external connections, or has a menu or dialog open. The blocked call is inside
    # fusionscript holding the GIL, so a Python thread can't interrupt it: SIGALRM with its
    # default action lets the kernel end the process, and resolve-run.sh explains exit 142.
    # Windows has no SIGALRM; the timer thread there is best effort.
    use_alarm = hasattr(signal, "alarm")
    if use_alarm:
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
        signal.alarm(max(1, int(timeout)))
    else:
        timer = threading.Timer(timeout, lambda: os._exit(142))
        timer.daemon = True
        timer.start()
    try:
        import DaVinciResolveScript as dvr
    except ImportError as e:
        sys.exit(f"ERROR: cannot import DaVinciResolveScript ({e}). Is DaVinci Resolve installed?")
    resolve = dvr.scriptapp("Resolve")
    if resolve is not None:
        # scriptapp can succeed while the app itself is stalled; one real call proves it isn't.
        resolve.GetVersionString()
    if use_alarm:
        signal.alarm(0)
    else:
        timer.cancel()
    if resolve is None:
        sys.exit("ERROR: no Resolve to connect to. Either DaVinci Resolve is not running (start it\n"
                 "       and open a project), or it refuses external scripts: set Preferences >\n"
                 "       System > General > External scripting using: Local, then restart it. On\n"
                 "       the free edition, run the script from Workspace > Scripts (see SKILL.md).")
    return resolve


def main(argv):
    if not argv:
        sys.exit(USAGE)
    mode, target, rest = None, None, []
    if argv[0] in ("--ping", "--state"):
        mode, rest = argv[0], argv[1:]
    elif argv[0] == "-c":
        if len(argv) < 2:
            sys.exit(USAGE)
        mode, target, rest = "code", argv[1], argv[2:]
    else:
        if not os.path.isfile(argv[0]):
            sys.exit(f"ERROR: script not found: {argv[0]}")
        mode, target, rest = "file", os.path.abspath(argv[0]), argv[1:]

    args = {}
    while rest:
        if rest[0] == "--arg" and len(rest) >= 2 and "=" in rest[1]:
            k, v = rest[1].split("=", 1)
            args[k] = v
            rest = rest[2:]
        else:
            sys.exit(f"ERROR: unexpected argument {rest[0]!r}\n{USAGE}")

    resolve = connect(float(os.environ.get("RESOLVE_CONNECT_TIMEOUT", "20")))
    H = resolve_helpers.bind(resolve)

    if mode == "--ping":
        pm = resolve.GetProjectManager()
        p = pm.GetCurrentProject()
        print(json.dumps({
            "ok": True, "product": resolve.GetProductName(), "version": resolve.GetVersionString(),
            "studio": resolve.IsStudio(), "page": resolve.GetCurrentPage(),
            "project": p.GetName() if p else None,
            "interpreter": f"{sys.executable} ({sys.version.split()[0]})",
        }))
        return 0
    if mode == "--state":
        print(json.dumps(H.state(), indent=2, default=repr, ensure_ascii=False))
        return 0

    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject()
    ns = {
        "__name__": "__main__",
        "__file__": target if mode == "file" else "<inline>",
        "resolve": resolve, "fusion": resolve.Fusion(), "pm": pm, "project": project,
        "mp": project.GetMediaPool() if project else None,
        "timeline": project.GetCurrentTimeline() if project else None,
        "OUT": os.environ.get("OUT", os.getcwd()), "ARGS": args,
        "need": resolve_helpers.need, "ResolveError": resolve_helpers.ResolveError, "H": H,
    }
    for name in resolve_helpers.EXPORTED:
        ns[name] = getattr(H, name)
    code = open(target, encoding="utf-8").read() if mode == "file" else target
    job_timeout = int(os.environ.get("RESOLVE_JOB_TIMEOUT", "0") or 0)
    if job_timeout and hasattr(signal, "alarm"):
        # Same reasoning as connect(): a frozen Resolve blocks inside fusionscript, so only
        # the kernel can end the wait. resolve-run.sh reports exit 142.
        signal.alarm(job_timeout)
    try:
        exec(compile(code, ns["__file__"], "exec"), ns)
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    except Exception:
        sys.stdout.flush()
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
