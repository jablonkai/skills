#!/usr/bin/env python3
"""Drive Sonic Pi 5 over OSC: a headless session the skill owns, or an open GUI.

    sp.py check                         app path, version, bundled ruby, ffmpeg
    sp.py start [--timeout S]           boot a headless session in the background
    sp.py attach                        target the running Sonic Pi GUI instead
    sp.py status                        mode, liveness, ping round-trip
    sp.py run (-f FILE | -e CODE | -)   evaluate code; prints errors, exit 2 on error
    sp.py stop                          stop all running jobs (session stays up)
    sp.py record-start                  start the built-in recorder
    sp.py record-stop OUT.wav           stop it and save the take to OUT.wav
    sp.py record -o OUT.wav (--seconds S | --bars N --bpm B) (-f FILE | -e CODE | -)
                                        one-shot: record, run, wait, save, stop jobs
    sp.py logs [--errors] [--last-run] [-n N]
    sp.py shutdown                      stop jobs and end the owned session

The token and ports live in a 0600 state file under $TMPDIR/sonic-pi-skill/ and are
never printed. Everything listens and sends on 127.0.0.1 only. If this helper's
background process dies, Sonic Pi's daemon stops getting keep-alives and reaps its
engine and server after about 90 s; `sp.py shutdown` (or the next `start`) reaps such
an orphan at once.
"""

import argparse
import json
import os
import re
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time

APP_CANDIDATES = [
    os.environ.get("SONIC_PI_APP", ""),
    "/Applications/Sonic Pi.app",
    os.path.expanduser("~/Applications/Sonic Pi.app"),
]
STATE_DIR = os.path.join(tempfile.gettempdir(), "sonic-pi-skill")
STATE_FILE = os.path.join(STATE_DIR, "state.json")
SESSION_LOG = os.path.join(STATE_DIR, "session.jsonl")
SERVE_LOG = os.path.join(STATE_DIR, "serve.log")
HOST = "127.0.0.1"
KEEP_ALIVE_EVERY = 2.0  # the daemon's kill switch fires after ~90 s without one
SCHED_AHEAD = 0.48  # measured: first note lands ~0.48 s after /run-code on 5.0.0
DRAIN = 1.0  # stop-all-jobs does not cancel notes already sent to the engine

# Messages the daemon forwards to the GUI that only matter to a GUI.
NOISY = {"/supersonic/statechange", "/scope/amp", "/supersonic/device-table",
         "/supersonic/devices", "/supersonic/input-devices", "/buffer/replace",
         "/flash", "/live_loop/scope", "/live_loop/scope-ended", "/incoming/osc",
         "/runs/all-completed", "/midi/out-ports", "/midi/in-ports",
         "/link/num-peers", "/link/tempo-change", "/link/start", "/link/stop",
         "/link-bpm", "/link-num-peers", "/cue", "/version"}


# ---------------------------------------------------------------- OSC codec

def _pad(data):
    return data + b"\0" * (4 - len(data) % 4)


def osc_message(address, *args):
    tags, payload = ",", b""
    for arg in args:
        if isinstance(arg, bool):
            tags += "T" if arg else "F"
        elif isinstance(arg, int):
            tags += "i"
            payload += struct.pack(">i", arg)
        elif isinstance(arg, float):
            tags += "f"
            payload += struct.pack(">f", arg)
        elif isinstance(arg, bytes):
            tags += "b"
            payload += struct.pack(">i", len(arg)) + arg + b"\0" * (-len(arg) % 4)
        else:
            tags += "s"
            payload += _pad(str(arg).encode("utf-8"))
    return _pad(address.encode()) + _pad(tags.encode()) + payload


def _read_str(data, pos):
    end = data.index(b"\0", pos)
    text = data[pos:end].decode("utf-8", "replace")
    return text, (end // 4 + 1) * 4


def osc_decode(data):
    """Return a list of (address, args); bundles are flattened."""
    if data.startswith(b"#bundle\0"):
        out, pos = [], 16
        while pos + 4 <= len(data):
            (size,) = struct.unpack(">i", data[pos:pos + 4])
            out.extend(osc_decode(data[pos + 4:pos + 4 + size]))
            pos += 4 + size
        return out
    address, pos = _read_str(data, 0)
    if pos >= len(data):
        return [(address, [])]
    tags, pos = _read_str(data, pos)
    args = []
    for tag in tags[1:]:
        if tag == "i":
            args.append(struct.unpack(">i", data[pos:pos + 4])[0])
            pos += 4
        elif tag == "f":
            args.append(struct.unpack(">f", data[pos:pos + 4])[0])
            pos += 4
        elif tag == "h":
            args.append(struct.unpack(">q", data[pos:pos + 8])[0])
            pos += 8
        elif tag == "d":
            args.append(struct.unpack(">d", data[pos:pos + 8])[0])
            pos += 8
        elif tag == "s":
            text, pos = _read_str(data, pos)
            args.append(text)
        elif tag == "b":
            (size,) = struct.unpack(">i", data[pos:pos + 4])
            args.append(data[pos + 4:pos + 4 + size].hex())
            pos += 4 + ((size + 3) // 4) * 4
        elif tag in "TF":
            args.append(tag == "T")
        elif tag == "N":
            args.append(None)
    return [(address, args)]


def send(port, address, *args):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(osc_message(address, *args), (HOST, port))


# ---------------------------------------------------------------- app + state

def find_app():
    for path in APP_CANDIDATES:
        if path and os.path.isdir(path):
            return path
    return None


def app_paths(app):
    res = os.path.join(app, "Contents", "Resources", "app", "server")
    return {
        "ruby": os.path.join(res, "native", "ruby", "bin", "ruby"),
        "daemon": os.path.join(res, "ruby", "bin", "daemon.rb"),
        "version": os.path.join(app, "Contents", "Resources", "VERSION"),
    }


def die(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def write_state(state):
    os.makedirs(STATE_DIR, mode=0o700, exist_ok=True)
    tmp = STATE_FILE + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        json.dump(state, fh)
    os.replace(tmp, STATE_FILE)


def read_state():
    try:
        with open(STATE_FILE) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except (OSError, TypeError):
        return False


def live_state():
    """The current state if its session is still usable, else None."""
    state = read_state()
    if not state:
        return None
    if state["mode"] == "owned" and not pid_alive(state.get("pid")):
        return None
    if state["mode"] == "attach" and not pid_alive(state.get("spider_pid")):
        return None
    return state


def require_state():
    state = live_state()
    if not state:
        die("No Sonic Pi session. Run `sp.py start` (headless) or `sp.py attach` (open GUI).")
    if state["mode"] == "owned" and not state.get("ready"):
        die("Session is still booting; wait for `sp.py start` to finish.")
    return state


def log_size():
    try:
        return os.path.getsize(SESSION_LOG)
    except OSError:
        return 0


def read_log(offset=0):
    entries = []
    try:
        with open(SESSION_LOG, "rb") as fh:
            fh.seek(offset)
            for line in fh:
                try:
                    entries.append(json.loads(line))
                except ValueError:
                    pass
    except OSError:
        pass
    return entries


# ---------------------------------------------------------------- background session

def serve(boot_timeout):
    """Own a headless Sonic Pi: spawn its daemon, keep it alive, log its output."""
    app = find_app()
    paths = app_paths(app)
    os.makedirs(STATE_DIR, mode=0o700, exist_ok=True)
    open(SESSION_LOG, "w").close()

    daemon = subprocess.Popen([paths["ruby"], paths["daemon"]], stdin=subprocess.DEVNULL,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    first = daemon.stdout.readline().decode().split()
    if len(first) < 6:
        print(f"daemon did not report ports: {first!r}", flush=True)
        daemon.kill()
        sys.exit(1)
    daemon_port, gui_listen, gui_send, engine, cues, token = (int(x) for x in first[:6])

    def drain():
        for _ in daemon.stdout:
            pass
    threading.Thread(target=drain, daemon=True).start()

    stopping = threading.Event()
    ready = {"ack": threading.Event(), "engine": threading.Event()}

    def shutdown(*_):
        if stopping.is_set():
            return
        stopping.set()
        try:
            send(daemon_port, "/daemon/exit", token)
        except OSError:
            pass
        try:
            daemon.wait(timeout=10)
        except subprocess.TimeoutExpired:
            daemon.kill()
        state = read_state()
        if state and state.get("pid") == os.getpid():
            os.unlink(STATE_FILE)
        os._exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    def keep_alive():
        while not stopping.is_set():
            try:
                send(daemon_port, "/daemon/keep-alive", token)
            except OSError:
                pass
            if daemon.poll() is not None:
                print("daemon exited", flush=True)
                shutdown()
            time.sleep(KEEP_ALIVE_EVERY)
    threading.Thread(target=keep_alive, daemon=True).start()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, gui_listen))

    def listen():
        with open(SESSION_LOG, "a", buffering=1) as log:
            while not stopping.is_set():
                try:
                    data, _ = sock.recvfrom(65536)
                    messages = osc_decode(data)
                except (OSError, ValueError, struct.error, IndexError):
                    continue
                for address, args in messages:
                    if address == "/ack":
                        ready["ack"].set()
                    elif address == "/supersonic/info" or (
                            address == "/log/info" and "Live Coding begin" in str(args[1:2])):
                        ready["engine"].set()
                    if address in NOISY:
                        continue
                    log.write(json.dumps({"t": round(time.time(), 3), "path": address,
                                          "args": args}) + "\n")
    threading.Thread(target=listen, daemon=True).start()

    state = {"mode": "owned", "pid": os.getpid(), "daemon_pid": daemon.pid,
             "app": app, "token": token, "daemon_port": daemon_port,
             "gui_send": gui_send, "gui_listen": gui_listen, "engine": engine,
             "cues": cues, "ready": False}
    write_state(state)

    deadline = time.time() + boot_timeout
    while not ready["ack"].is_set() and time.time() < deadline:
        try:
            send(gui_send, "/ping", token, "boot")
        except OSError:
            pass
        time.sleep(0.5)
    ready["engine"].wait(max(0.0, deadline - time.time()))
    if not (ready["ack"].is_set() and ready["engine"].is_set()):
        print("boot timed out", flush=True)
        shutdown()
    state["ready"] = True
    write_state(state)
    print("ready", flush=True)
    while True:
        time.sleep(3600)


# ---------------------------------------------------------------- commands

def reap_orphan():
    """End a daemon whose helper died (kill -9, crash) using the saved token."""
    state = read_state()
    if not state or state.get("mode") != "owned" or pid_alive(state.get("pid")):
        return False
    if pid_alive(state.get("daemon_pid")):
        send(state["daemon_port"], "/daemon/exit", state["token"])
        deadline = time.time() + 10
        while pid_alive(state["daemon_pid"]) and time.time() < deadline:
            time.sleep(0.2)
    os.unlink(STATE_FILE)
    return True


def cmd_check(_args):
    app = find_app()
    if not app:
        die("Sonic Pi.app not found. Install: brew install --cask sonic-pi "
            "(or https://sonic-pi.net), or set SONIC_PI_APP=/path/to/Sonic Pi.app", 2)
    paths = app_paths(app)
    version = open(paths["version"]).read().strip() if os.path.exists(paths["version"]) else "unknown"
    print(f"app: {app}\nversion: {version}")
    print(f"bundled ruby: {'ok' if os.access(paths['ruby'], os.X_OK) else 'MISSING'}")
    for tool in ("ffmpeg", "ffprobe"):
        found = any(os.access(os.path.join(d, tool), os.X_OK)
                    for d in os.environ.get("PATH", "").split(os.pathsep))
        print(f"{tool}: {'ok' if found else 'missing (brew install ffmpeg) — needed by wav_check.py'}")
    state = live_state()
    print(f"session: {state['mode'] if state else 'none'}")
    if not version.startswith("5"):
        print("warning: this skill is verified against Sonic Pi 5.x", file=sys.stderr)


def cmd_start(args):
    state = live_state()
    if state and state["mode"] == "owned":
        print(f"already running (pid {state['pid']}, ready={state.get('ready')})")
        return
    if not find_app():
        die("Sonic Pi.app not found — run `sp.py check`.", 2)
    os.makedirs(STATE_DIR, mode=0o700, exist_ok=True)
    reap_orphan()
    if os.path.exists(STATE_FILE):
        os.unlink(STATE_FILE)  # stale attach or dead session
    with open(SERVE_LOG, "w") as out:
        proc = subprocess.Popen([sys.executable, os.path.abspath(__file__), "_serve",
                                 "--timeout", str(args.timeout)],
                                stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT,
                                start_new_session=True)
    deadline = time.time() + args.timeout + 5
    while time.time() < deadline:
        state = read_state()
        if state and state.get("ready"):
            version = open(app_paths(state["app"])["version"]).read().strip()
            print(f"Sonic Pi {version} headless session ready (pid {proc.pid}); "
                  f"OSC cues port {state['cues']}")
            return
        if proc.poll() is not None:
            break
        time.sleep(0.25)
    if proc.poll() is None:
        proc.terminate()
    tail = open(SERVE_LOG).read()[-800:]
    die(f"Session failed to boot.\n{tail}")


def cmd_attach(_args):
    out = subprocess.run(["ps", "-axww", "-o", "pid=,command="], capture_output=True,
                         text=True).stdout
    for line in out.splitlines():
        if "spider-server.rb" not in line:
            continue
        match = re.search(r"spider-server\.rb\s+-u\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(-?\d+)", line)
        if not match:
            continue
        pid = int(line.split()[0])
        own = read_state()
        if own and own.get("mode") == "owned" and pid_alive(own.get("pid")):
            die("A headless session owned by this skill is running; `sp.py shutdown` it first.")
        gui_send, gui_listen, engine, _engine_send, cues, token = (int(x) for x in match.groups())
        write_state({"mode": "attach", "spider_pid": pid, "token": token, "gui_send": gui_send,
                     "gui_listen": gui_listen, "engine": engine, "cues": cues, "ready": True})
        print("Attached to the running Sonic Pi GUI. Errors and puts output appear in the "
              "GUI's log pane, not here.")
        return
    die("No running Sonic Pi found. Open Sonic Pi.app, or use `sp.py start` for a headless session.")


def cmd_status(_args):
    state = live_state()
    if not state:
        print("session: none")
        return
    print(f"session: {state['mode']}  ready: {state.get('ready')}")
    if state["mode"] == "owned" and state.get("ready"):
        offset = log_size()
        send(state["gui_send"], "/ping", state["token"], "status")
        deadline = time.time() + 2
        while time.time() < deadline:
            if any(e["path"] == "/ack" for e in read_log(offset)):
                print("ping: ok")
                return
            time.sleep(0.05)
        print("ping: no answer")


def read_code(args):
    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            return fh.read()
    if args.code is not None:
        return args.code
    return sys.stdin.read()


def format_entry(entry):
    path, a = entry["path"], entry["args"]
    if path == "/error":
        # a[2] is the backtrace; its first lines name the exception, the rest is internals
        detail = [ln.strip() for ln in str(a[2]).splitlines()
                  if ln.strip() and "/Contents/Resources/app/server/" not in ln
                  and not ln.strip().startswith("eval:") and ln.strip() not in a[1]][:2]
        message = " ".join(ln.strip() for ln in str(a[1]).splitlines()
                           if ln.strip() and not ln.startswith(("Example:", "Docs:")))
        return "\n  ".join([f"ERROR (run {a[0]}, line {a[3]}): {message}"] + detail)
    if path == "/syntax_error":
        return f"SYNTAX ERROR (run {a[0]}, line {a[3]}): {a[1]}  | {a[2]}"
    if path == "/log/multi_message":
        # [run, thread, time, count, kind, text, kind, text, ...]; kind 1 is a puts
        thread = "" if a[1] in ("", '""') else f" {a[1]}"
        return f"[run {a[0]}{thread} t={a[2]}] " + " | ".join(str(t) for t in a[5::2])
    if path in ("/log/info", "/info"):
        return f"info: {a[1] if len(a) > 1 else a}"
    return f"{path} {a}"


def is_error(entry):
    return entry["path"] in ("/error", "/syntax_error")


def warnings(entries):
    """Things Sonic Pi only logs, e.g. an unknown sample name is skipped silently."""
    found = []
    for entry in entries:
        if entry["path"] == "/log/multi_message" and "no match found" in json.dumps(entry["args"]):
            line = format_entry(entry).replace("\n", " ")
            if line not in found:
                found.append(line)
    return found


def run_code(state, code, wait):
    """Send code; return (new log entries, errors) observed within `wait` seconds."""
    offset = log_size()
    send(state["gui_send"], "/run-code", state["token"], code)
    if state["mode"] != "owned":
        return [], []
    time.sleep(wait)
    entries = read_log(offset)
    return entries, [e for e in entries if is_error(e)]


def cmd_run(args):
    state = require_state()
    entries, errors = run_code(state, read_code(args), args.wait)
    if state["mode"] != "owned":
        print("sent (attached: check the GUI log pane for errors)")
        return
    for entry in entries:
        if entry["path"] in ("/log/multi_message", "/error", "/syntax_error"):
            print(format_entry(entry))
    for line in warnings(entries):
        print(f"WARNING (skipped, not an error): {line}")
    if errors:
        sys.exit(2)
    print(f"ok — no errors within {args.wait}s (a live_loop can fail on a later "
          "iteration: check `sp.py logs --errors` before calling it done)")


def cmd_stop(_args):
    state = require_state()
    send(state["gui_send"], "/stop-all-jobs", state["token"])
    print("stopped all jobs")


def cmd_record_start(_args):
    state = require_state()
    send(state["gui_send"], "/start-recording", state["token"])
    print("recording")


def save_recording(state, out):
    out = os.path.abspath(out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.exists(out):
        os.unlink(out)
    send(state["gui_send"], "/stop-recording", state["token"])
    time.sleep(0.5)
    send(state["gui_send"], "/save-recording", state["token"], out)
    deadline, last = time.time() + 15, -1
    while time.time() < deadline:
        size = os.path.getsize(out) if os.path.exists(out) else -1
        if size > 0 and size == last:
            return out
        last = size
        time.sleep(0.4)
    die(f"recording was not saved to {out}")


def cmd_record_stop(args):
    state = require_state()
    print(f"saved {save_recording(state, args.out)}")


def cmd_record(args):
    state = require_state()
    if args.seconds:
        seconds = args.seconds
    elif args.bars and args.bpm:
        seconds = args.bars * args.beats_per_bar * 60.0 / args.bpm
    else:
        die("give --seconds, or --bars with --bpm")
    code = read_code(args)
    send(state["gui_send"], "/stop-all-jobs", state["token"])
    time.sleep(DRAIN)  # let already-scheduled notes of the old jobs play out
    offset = log_size()
    started = time.time()
    send(state["gui_send"], "/run-code", state["token"], code)
    # Sonic Pi schedules sound SCHED_AHEAD after evaluation; start the take there.
    time.sleep(SCHED_AHEAD)
    send(state["gui_send"], "/start-recording", state["token"])
    time.sleep(min(1.0, seconds))
    errors = [e for e in read_log(offset) if is_error(e)]
    if errors:
        send(state["gui_send"], "/stop-all-jobs", state["token"])
        send(state["gui_send"], "/stop-recording", state["token"])
        for entry in errors:
            print(format_entry(entry))
        sys.exit(2)
    remaining = started + SCHED_AHEAD + seconds + args.tail - time.time()
    time.sleep(max(0.0, remaining))
    out = save_recording(state, args.out)
    send(state["gui_send"], "/stop-all-jobs", state["token"])
    entries = read_log(offset)
    late = [e for e in entries if is_error(e)]
    for entry in late:
        print(format_entry(entry))
    for line in warnings(entries):
        print(f"WARNING (skipped, not an error): {line}")
    print(f"saved {out} ({seconds:.2f}s of music + {args.tail}s tail requested)")
    if late:
        sys.exit(2)


def cmd_logs(args):
    state = read_state()
    if state and state.get("mode") == "attach":
        die("Attached to the GUI: its log pane has the output.")
    entries = read_log(0)
    if args.last_run:
        runs = [e for e in entries if e["path"] in ("/log/multi_message", "/error", "/syntax_error")]
        if runs:
            last = max(e["args"][0] for e in runs if isinstance(e["args"][0], int))
            entries = [e for e in entries if e["args"] and e["args"][0] == last]
    if args.errors:
        flagged = set(warnings(entries))
        entries = [e for e in entries if is_error(e)
                   or format_entry(e).replace("\n", " ") in flagged]
    for entry in entries[-args.n:]:
        print(format_entry(entry))
    if not entries:
        print("(no matching log entries)")


def cmd_shutdown(_args):
    state = live_state()
    if not state:
        print("reaped an orphaned session" if reap_orphan() else "no session")
        if os.path.exists(STATE_FILE):
            os.unlink(STATE_FILE)
        return
    send(state["gui_send"], "/stop-all-jobs", state["token"])
    if state["mode"] == "attach":
        os.unlink(STATE_FILE)
        print("stopped jobs and detached (the GUI keeps running)")
        return
    os.kill(state["pid"], signal.SIGTERM)
    deadline = time.time() + 15
    while pid_alive(state["pid"]) and time.time() < deadline:
        time.sleep(0.2)
    print("session ended" if not pid_alive(state["pid"]) else "session did not exit in 15s")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    p = sub.add_parser("start")
    p.add_argument("--timeout", type=float, default=60)
    p = sub.add_parser("_serve")
    p.add_argument("--timeout", type=float, default=60)
    sub.add_parser("attach")
    sub.add_parser("status")

    def code_args(p):
        group = p.add_mutually_exclusive_group()
        group.add_argument("-f", "--file")
        group.add_argument("-e", "--code")

    p = sub.add_parser("run")
    code_args(p)
    p.add_argument("--wait", type=float, default=1.5,
                   help="seconds to collect errors and output (default 1.5)")
    sub.add_parser("stop")
    sub.add_parser("record-start")
    p = sub.add_parser("record-stop")
    p.add_argument("out")
    p = sub.add_parser("record")
    code_args(p)
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--seconds", type=float)
    p.add_argument("--bars", type=float)
    p.add_argument("--bpm", type=float)
    p.add_argument("--beats-per-bar", type=float, default=4)
    p.add_argument("--tail", type=float, default=0.0,
                   help="extra seconds after the last bar, e.g. for reverb tails")
    p = sub.add_parser("logs")
    p.add_argument("--errors", action="store_true")
    p.add_argument("--last-run", action="store_true")
    p.add_argument("-n", type=int, default=40)
    sub.add_parser("shutdown")
    args = parser.parse_args()

    if args.cmd == "_serve":
        serve(args.timeout)
    else:
        globals()["cmd_" + args.cmd.replace("-", "_")](args)


if __name__ == "__main__":
    main()
