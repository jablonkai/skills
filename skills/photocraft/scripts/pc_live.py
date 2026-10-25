#!/usr/bin/env python3
"""Drive the running PhotoCraft desktop app over its authenticated loopback control port.

Use only when the user wants to watch edits happen in the app; headless work goes
through photocraft-cli (run/batch/serve).

Usage:
  pc_live.py [--port 7878] start --root DIR [--read-root DIR] [--write-root DIR]
  pc_live.py [--port 7878] status
  pc_live.py [--port 7878] call METHOD [PARAMS_JSON|@file.json]
  pc_live.py [--port 7878] steps STEPS.json|-     # same step format as pc_session.py
  pc_live.py [--port 7878] stop                   # app.quit: DISCARDS unsaved edits, save first

Security posture: the app listens on 127.0.0.1 only, every connection must send the
256-bit token first (token file mode 0600, never on the command line), file access is
limited to the read/write roots given at start, and `stop` quits the app (app.quit).
app.open / app.save take paths RELATIVE to those roots.
"""

import argparse
import json
import os
import socket
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pclib import PcError, die, layer_ids, layer_refs, load_json_arg, substitute_refs, to_step  # noqa: E402

BUNDLE_ID = "ai.storyteller.photocraft"
DEFAULT_TOKEN = os.path.expanduser("~/.config/photocraft-skill/control.token")


class Link(object):
    def __init__(self, port, token_file, timeout=65):
        with open(token_file) as handle:
            token = handle.read().strip()
        self.sock = socket.create_connection(("127.0.0.1", port), timeout=timeout)
        self.reader = self.sock.makefile("r", encoding="utf-8")
        self._id = 0
        reply = self.request("auth", {"token": token})
        if not reply.get("ok"):
            raise RuntimeError("auth failed: %s" % reply.get("error"))

    def request(self, method, params=None):
        self._id += 1
        line = json.dumps({"id": self._id, "method": method, "params": params or {}}) + "\n"
        self.sock.sendall(line.encode("utf-8"))
        while True:
            reply = self.reader.readline()
            if not reply:
                raise RuntimeError("connection closed by PhotoCraft")
            data = json.loads(reply)
            if data.get("id") in (self._id, None):
                return data

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


def port_open(port):
    try:
        socket.create_connection(("127.0.0.1", port), timeout=1).close()
        return True
    except OSError:
        return False


def connect(args):
    if not os.path.exists(args.token_file):
        die("no token file at %s; run `pc_live.py start` first" % args.token_file)
    try:
        return Link(args.port, args.token_file)
    except (OSError, RuntimeError) as exc:
        die("cannot reach PhotoCraft on 127.0.0.1:%d: %s" % (args.port, exc))


def cmd_start(args):
    if port_open(args.port):
        link = connect(args)
        link.close()
        print(json.dumps({"running": True, "port": args.port, "note": "already listening; reused"}))
        return
    read_root = os.path.abspath(args.read_root or args.root)
    write_root = os.path.abspath(args.write_root or args.root)
    token_dir = os.path.dirname(args.token_file)
    os.makedirs(token_dir, exist_ok=True)
    os.chmod(token_dir, 0o700)
    subprocess.check_call([
        "open", "-n", "-b", BUNDLE_ID, "--args",
        "--control", str(args.port), "--control-token-file", args.token_file,
        "--automation-read-root", read_root, "--automation-write-root", write_root,
    ])
    deadline = time.time() + args.wait
    while time.time() < deadline:
        if port_open(args.port) and os.path.exists(args.token_file):
            try:
                link = Link(args.port, args.token_file)
                link.close()
                print(json.dumps({"running": True, "port": args.port,
                                  "readRoot": read_root, "writeRoot": write_root}))
                return
            except (OSError, RuntimeError):
                pass
        time.sleep(0.5)
    die("PhotoCraft did not open control port %d within %ds" % (args.port, args.wait))


def cmd_status(args):
    if not port_open(args.port):
        print(json.dumps({"running": False, "port": args.port}))
        return
    link = connect(args)
    reply = link.request("ui.inspect", {})
    link.close()
    result = reply.get("result") or {}
    print(json.dumps({"running": True, "port": args.port,
                      "session": result.get("session"),
                      "dialogs": result.get("dialogs")}, ensure_ascii=False)[:4000])


def cmd_call(args):
    link = connect(args)
    params = load_json_arg(args.params) if args.params else {}
    reply = link.request(args.method, params)
    link.close()
    print(json.dumps(reply, ensure_ascii=False))
    sys.exit(0 if reply.get("ok") else 1)


def cmd_steps(args):
    text = sys.stdin.read() if args.steps == "-" else open(args.steps).read()
    text = text.strip()
    steps = json.loads(text) if text.startswith("[") else [json.loads(l) for l in text.splitlines() if l.strip()]
    link = connect(args)
    for index, step in enumerate(steps, 1):
        method, params = to_step(step)
        refs = layer_refs(params)
        if refs:
            doc = link.request("engine.execute", {"command": "document.inspect"})
            try:
                if not doc.get("ok"):
                    raise PcError("document.inspect: %s" % doc.get("error"))
                params = substitute_refs(params, layer_ids(doc.get("result") or {}, refs))
            except PcError as exc:
                link.close()
                die("step %d: %s" % (index, exc))
        reply = link.request(method, params)
        print(json.dumps({"step": index, "method": step.get("cmd", method), "ok": bool(reply.get("ok")),
                          "result" if reply.get("ok") else "error":
                          reply.get("result") if reply.get("ok") else reply.get("error")}, ensure_ascii=False))
        if not reply.get("ok"):
            link.close()
            sys.exit(1)
    link.close()


def cmd_stop(args):
    if not port_open(args.port):
        print(json.dumps({"running": False}))
        return
    link = connect(args)
    try:
        link.request("app.quit", {})
    except (OSError, RuntimeError):
        pass
    link.close()
    for _ in range(20):
        if not port_open(args.port):
            print(json.dumps({"running": False, "stopped": True}))
            return
        time.sleep(0.5)
    link = connect(args)
    dialogs = (link.request("ui.inspect", {}).get("result") or {}).get("dialogs")
    link.close()
    die("PhotoCraft is still running; open dialogs (an unsaved-changes prompt?): %s"
        % json.dumps(dialogs)[:1500])


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=7878)
    parser.add_argument("--token-file", default=DEFAULT_TOKEN)
    sub = parser.add_subparsers(dest="action")
    p = sub.add_parser("start")
    p.add_argument("--root", default=os.getcwd())
    p.add_argument("--read-root")
    p.add_argument("--write-root")
    p.add_argument("--wait", type=int, default=45)
    sub.add_parser("status")
    p = sub.add_parser("call")
    p.add_argument("method")
    p.add_argument("params", nargs="?")
    p = sub.add_parser("steps")
    p.add_argument("steps")
    sub.add_parser("stop")
    args = parser.parse_args()
    handlers = {"start": cmd_start, "status": cmd_status, "call": cmd_call,
                "steps": cmd_steps, "stop": cmd_stop}
    if args.action not in handlers:
        parser.print_help()
        sys.exit(2)
    handlers[args.action](args)


if __name__ == "__main__":
    main()
