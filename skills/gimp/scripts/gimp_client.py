#!/usr/bin/env python3
"""Talk to a running GIMP through its built-in Script-Fu server.

The Script-Fu server (Filters > Script-Fu > Start Server, default 127.0.0.1:10008)
is GIMP's own remote-control endpoint: it evaluates Script-Fu (TinyScheme) sent
over a TCP socket, inside the LIVE GIMP session, so the images the user sees are
the images the script touches.

Wire protocol (plug-ins/script-fu/server/script-fu-server.c):
    request   'G' + uint16be(len) + utf8(command)
    response  'G' + uint8(error) + uint16be(len) + utf8(message)
A command therefore cannot exceed 65535 bytes -- which is why this module never
sends a build script inline. It writes the script to disk and sends a short,
fixed Scheme call that makes GIMP's own `python-fu-eval` read it back.

Used as a library by gimp-send.sh; runnable on its own for raw Scheme:

    python3 gimp_client.py --ping
    python3 gimp_client.py --scheme '(gimp-version)'
"""

import argparse
import json
import os
import socket
import struct
import sys
import tempfile

MAGIC = b"G"
DEFAULT_HOST = os.environ.get("GIMP_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.environ.get("GIMP_PORT", "10008"))
MAX_COMMAND = 0xFFFF


class GimpNotReachable(RuntimeError):
    """The Script-Fu server did not answer -- GIMP is down or the server is off."""


def _recv_exactly(sock, count):
    chunks = []
    got = 0
    while got < count:
        chunk = sock.recv(count - got)
        if not chunk:
            raise GimpNotReachable(
                "connection closed after %d of %d bytes" % (got, count))
        chunks.append(chunk)
        got += len(chunk)
    return b"".join(chunks)


def send_scheme(command, host=DEFAULT_HOST, port=DEFAULT_PORT, timeout=120.0):
    """Evaluate one Script-Fu expression in the running GIMP.

    Returns (error, message): `error` is the server's error flag, `message` the
    printed return value or the error text. Raises GimpNotReachable if nothing
    is listening -- that is the "start the server" case, worth distinguishing
    from a script that ran and failed.
    """
    data = command.encode("utf-8")
    if len(data) > MAX_COMMAND:
        raise ValueError("command is %d bytes; the Script-Fu server accepts at "
                         "most %d -- send a file instead" % (len(data), MAX_COMMAND))
    try:
        sock = socket.create_connection((host, port), timeout=min(timeout, 10.0))
    except OSError as exc:
        raise GimpNotReachable("cannot connect to %s:%d (%s)" % (host, port, exc))
    sock.settimeout(timeout)
    try:
        sock.sendall(MAGIC + struct.pack(">H", len(data)) + data)
        head = _recv_exactly(sock, 4)
        if head[0:1] != MAGIC:
            raise GimpNotReachable(
                "not a Script-Fu server: expected magic %r, got %r" % (MAGIC, head[0:1]))
        error = bool(head[1])
        length = struct.unpack(">H", head[2:4])[0]
        body = _recv_exactly(sock, length).decode("utf-8", "replace") if length else ""
        return error, body
    finally:
        sock.close()


def _scheme_string(text):
    """Quote a Python string as a TinyScheme string literal."""
    return '"%s"' % text.replace("\\", "\\\\").replace('"', '\\"')


# Runs inside GIMP's python-fu-eval process. It execs the build script with
# stdout/stderr captured and writes the outcome as JSON, because the Script-Fu
# server can only hand back a short Scheme return value -- print() output and
# tracebacks would otherwise be lost in GIMP's own error console.
_BOOTSTRAP = '''\
import io, json, os, sys, traceback
_script, _out, _result = {script}, {out}, {result}
if _out:
    os.environ["OUT"] = _out
_buf = io.StringIO()
_saved = (sys.stdout, sys.stderr)
_res = {{"ok": True, "output": "", "error": None}}
try:
    sys.stdout = sys.stderr = _buf
    with open(_script) as _fh:
        _code = _fh.read()
    exec(compile(_code, _script, "exec"),
         {{"__name__": "__main__", "__file__": _script, "OUT": _out}})
except BaseException:
    _res["ok"] = False
    _res["error"] = traceback.format_exc()
finally:
    sys.stdout, sys.stderr = _saved
    _res["output"] = _buf.getvalue()
    with open(_result, "w") as _fh:
        json.dump(_res, _fh)
'''


def run_python(script_path, out="", host=DEFAULT_HOST, port=DEFAULT_PORT,
               timeout=120.0):
    """Run a Python build script inside the live GIMP.

    Returns {"ok", "output", "error"}. `out` is exposed to the script both as an
    OUT global and as os.environ["OUT"], which is where exports and metrics
    should go so they can be read back afterwards.
    """
    script_path = os.path.abspath(script_path)
    workdir = tempfile.mkdtemp(prefix="gimp-send-")
    boot_path = os.path.join(workdir, "bootstrap.py")
    result_path = os.path.join(workdir, "result.json")
    with open(boot_path, "w") as fh:
        fh.write(_BOOTSTRAP.format(script=repr(script_path), out=repr(out),
                                   result=repr(result_path)))

    command = "(python-fu-eval RUN-NONINTERACTIVE %s)" % _scheme_string(
        "exec(open(%r).read())" % boot_path)
    error, message = send_scheme(command, host=host, port=port, timeout=timeout)

    if os.path.exists(result_path):
        with open(result_path) as fh:
            return json.load(fh)
    # No result file: the failure happened before the bootstrap could write one
    # (bad Scheme call, python-fu-eval missing, GIMP killed mid-run), so the
    # server's own message is all the diagnosis there is.
    return {"ok": not error, "output": "",
            "error": message or "python-fu-eval produced no result file"}


def ping(host=DEFAULT_HOST, port=DEFAULT_PORT):
    """Return {"ok", "version", "images"} for the GIMP on the other end."""
    # Script-Fu in GIMP 3 returns a PDB call's values as a plain list, so
    # (car (gimp-version)) is the version string and (car (gimp-get-images))
    # the image vector -- no leading status element as in GIMP 2.
    error, message = send_scheme(
        '(string-append (car (gimp-version)) " | open images: "'
        '  (number->string (vector-length (car (gimp-get-images)))))',
        host=host, port=port, timeout=10.0)
    return {"ok": not error, "bridge": "gimp", "host": host, "port": port,
            "reply": message.strip().strip('"')}


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float,
                        default=float(os.environ.get("GIMP_SEND_TIMEOUT", "120")))
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--ping", action="store_true")
    group.add_argument("--scheme", metavar="EXPR", help="evaluate raw Script-Fu")
    group.add_argument("--python", metavar="FILE", help="run a Python file in GIMP")
    group.add_argument("--code", metavar="SRC", help="run inline Python in GIMP")
    parser.add_argument("--out", default=os.environ.get("OUT", ""))
    args = parser.parse_args()

    try:
        if args.ping:
            print(json.dumps(ping(args.host, args.port)))
            return 0
        if args.scheme:
            error, message = send_scheme(args.scheme, args.host, args.port, args.timeout)
            stream = sys.stderr if error else sys.stdout
            stream.write(message.rstrip() + "\n")
            return 1 if error else 0
        script = args.python
        if args.code is not None:
            handle, script = tempfile.mkstemp(prefix="gimp-inline-", suffix=".py")
            with os.fdopen(handle, "w") as fh:
                fh.write(args.code)
        result = run_python(script, args.out, args.host, args.port, args.timeout)
    except GimpNotReachable as exc:
        sys.stderr.write("ERROR: %s\n" % exc)
        sys.stderr.write("       Run scripts/gimp-start.sh, or in a GIMP that is already "
                         "open:\n       Filters > Development > Script-Fu > Start Server..."
                         " (127.0.0.1, port %d)\n" % args.port)
        return 1
    if result.get("output"):
        sys.stdout.write(result["output"].rstrip() + "\n")
    if not result.get("ok"):
        sys.stderr.write((result.get("error") or "script failed").rstrip() + "\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
