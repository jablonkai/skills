#!/usr/bin/env python3
"""Start, check and stop a WordCraft app instance with its control port (live mode).

    wc_live.py start [--port N] [FILE]   launch a new WordCraft with --control on 127.0.0.1
    wc_live.py status                    is the instance started here still listening?
    wc_live.py stop                      quit only the instance started here

The control port is authenticated: the app writes a per-port key (mode 0600) to
~/Library/Application Support/WordCraft/control-key.local-PORT, and `wordcraft-cli mcp
--connect` presents it. Requests without the key get "unauthorized", and the port speaks
JSON lines only, so a web page cannot talk to it. `stop` never touches a WordCraft the
user opened themselves; unsaved changes in the stopped instance are lost, so save first.
State lives in $TMPDIR/wordcraft-skill-live.json.
"""
import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time

APP = "/Applications/WordCraft.app"
KEY_DIR = os.path.expanduser("~/Library/Application Support/WordCraft")
STATE = os.path.join(tempfile.gettempdir(), "wordcraft-skill-live.json")


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def listening(port):
    try:
        socket.create_connection(("127.0.0.1", port), timeout=1).close()
        return True
    except OSError:
        return False


def listener_pid(port):
    out = subprocess.run(["lsof", "-nP", "-t", "-iTCP:%d" % port, "-sTCP:LISTEN"],
                         capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else None


def load_state():
    try:
        return json.load(open(STATE))
    except (OSError, ValueError):
        return None


def start(a):
    st = load_state()
    if st and listening(st["port"]):
        print(json.dumps(dict(st, note="already running"), indent=1))
        return 0
    port = a.port or free_port()
    if listening(port):
        sys.exit("port %d is already in use" % port)
    args = ["open", "-n", "-a", APP]
    if a.file:
        args.append(os.path.abspath(a.file))
    subprocess.run(args + ["--args", "--control", str(port)], check=True)
    key = os.path.join(KEY_DIR, "control-key.local-%d" % port)
    for _ in range(60):
        if listening(port) and os.path.exists(key):
            break
        time.sleep(0.5)
    else:
        sys.exit("WordCraft did not open the control port %d within 30 s" % port)
    st = {"port": port, "pid": listener_pid(port), "connect": "127.0.0.1:%d" % port, "key_file": key}
    json.dump(st, open(STATE, "w"))
    print(json.dumps(st, indent=1))
    return 0


def status(_):
    st = load_state()
    if not st:
        print(json.dumps({"running": False}))
        return 1
    up = listening(st["port"]) and listener_pid(st["port"]) == st["pid"]
    print(json.dumps(dict(st, running=up), indent=1))
    return 0 if up else 1


def stop(_):
    st = load_state()
    if not st:
        print(json.dumps({"stopped": False, "note": "no instance was started by wc_live.py"}))
        return 0
    pid = listener_pid(st["port"])
    if pid and pid == st["pid"]:
        os.kill(pid, signal.SIGTERM)
        for _ in range(20):
            if not listening(st["port"]):
                break
            time.sleep(0.5)
    os.remove(STATE)
    print(json.dumps({"stopped": True, "pid": st["pid"], "port": st["port"]}))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("start")
    p.add_argument("--port", type=int)
    p.add_argument("file", nargs="?")
    sub.add_parser("status")
    sub.add_parser("stop")
    a = ap.parse_args()
    return {"start": start, "status": status, "stop": stop}[a.mode](a)


if __name__ == "__main__":
    sys.exit(main())
