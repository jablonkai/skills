# Krita Bridge — a pykrita plugin that starts a tiny HTTP server on
# 127.0.0.1:8737 and executes whatever Python is POSTed to it, inside the LIVE
# Krita session, on the GUI (main) thread — so the canvas updates, the layer
# stack is the one the user sees, and Krita's own API (which is main-thread
# only) is safe to call.
#
# It is integrated with Qt's event loop via QTcpServer, so it never blocks the
# UI. Each request runs synchronously and the HTTP response carries the
# script's captured stdout/stderr plus any traceback, so the sender gets real
# feedback.
#
#   GET  /ping         -> {"ok": true, "bridge": "krita", "version": "5.3.3", ...}
#   POST /run  {code}  -> exec inline code   ; {path} -> exec a .py file
#                         optional {out} sets the OUT dir (env + a global var)
#
# Two ways to run it:
#   * as a plugin (recommended) — installed into <resources>/pykrita and enabled
#     in Settings ▸ Configure Krita ▸ Python Plugin Manager, it starts itself
#     every time Krita launches;
#   * pasted into Tools ▸ Scripts ▸ Scripter and run once, for a session where
#     the plugin isn't installed.
#
# Env overrides (only inherited when Krita is launched from a terminal):
# KRITA_BRIDGE_PORT (8737).
import io
import json
import os
import sys
import traceback

from krita import Krita, Extension
from PyQt5 import QtCore, QtNetwork

_PORT = int(os.environ.get("KRITA_BRIDGE_PORT", "8737"))


def _cross_origin(headers):
    """True when the request came from a browsing context on another origin.

    The bridge execs arbitrary Python, so a page on any site the user visits
    could otherwise drive it with a CORS *simple* request (no preflight, and
    the opaque response is irrelevant — the code has already run). curl and
    krita-send.sh send neither header, so this costs them nothing.

    `headers` maps lowercased bytes names to bytes values.
    """
    if headers.get(b"origin"):
        return True
    site = headers.get(b"sec-fetch-site", b"").decode("latin1", "replace").lower()
    return site not in ("", "same-origin", "none")


def _run(code, filename, out):
    """Exec code in a fresh namespace; capture stdout/stderr and any error."""
    instance = Krita.instance()
    ns = {"__name__": "__main__", "__file__": filename,
          "Krita": Krita, "krita_instance": instance, "OUT": out}
    if out:
        os.environ["OUT"] = out
    buf = io.StringIO()
    saved_out, saved_err = sys.stdout, sys.stderr
    result = {"ok": True, "output": "", "error": None}
    try:
        sys.stdout = sys.stderr = buf
        exec(compile(code, filename, "exec"), ns)
    except BaseException:
        result["ok"] = False
        result["error"] = traceback.format_exc()
    finally:
        sys.stdout, sys.stderr = saved_out, saved_err
        result["output"] = buf.getvalue()
    return result


class _Bridge(QtCore.QObject):
    def __init__(self, port=_PORT):
        super().__init__()
        self.port = port
        self.bufs = {}
        self.server = QtNetwork.QTcpServer(self)
        if not self.server.listen(QtNetwork.QHostAddress("127.0.0.1"), port):
            sys.stderr.write("Krita Bridge: cannot bind 127.0.0.1:%d (%s)\n"
                             % (port, self.server.errorString()))
            return
        self.server.newConnection.connect(self._accept)
        sys.stderr.write("Krita Bridge listening on 127.0.0.1:%d\n" % port)

    def close(self):
        try:
            self.server.close()
        except Exception:
            pass

    def _accept(self):
        sock = self.server.nextPendingConnection()
        self.bufs[id(sock)] = b""
        sock.readyRead.connect(lambda s=sock: self._read(s))
        sock.disconnected.connect(lambda s=sock: self.bufs.pop(id(s), None))

    def _read(self, sock):
        self.bufs[id(sock)] += bytes(sock.readAll())
        data = self.bufs[id(sock)]
        if b"\r\n\r\n" not in data:
            return                                   # headers not complete yet
        head, _, body = data.partition(b"\r\n\r\n")
        lines = head.split(b"\r\n")
        request = lines[0].decode("latin1", "replace")
        path = (request.split(" ") + ["", "/"])[1]
        headers = {}
        clen = 0
        for ln in lines[1:]:
            name, sep, value = ln.partition(b":")
            if not sep:
                continue
            key = name.strip().lower()
            headers[key] = value.strip()
            if key == b"content-length":
                try:
                    clen = int(value.strip())
                except ValueError:
                    clen = 0
        if len(body) < clen:
            return                                   # wait for the rest of the body

        # The request is complete: consume it, so a second pipelined request on
        # the same connection cannot re-dispatch this one. Every path below
        # returns, so this is the single place it has to happen.
        self.bufs[id(sock)] = b""

        if _cross_origin(headers):
            self._respond(sock, {"ok": False, "output": "",
                                 "error": "cross-origin request rejected"}, "403 Forbidden")
            return

        if path.startswith("/ping"):
            instance = Krita.instance()
            docs = [d.fileName() or d.name() for d in instance.documents()]
            self._respond(sock, {"ok": True, "bridge": "krita",
                                 "version": instance.version(),
                                 "documents": docs})
            return
        if not path.startswith("/run"):
            # Anything else — a stray GET /favicon.ico, a probe — must not reach
            # the exec branch, where it would run empty code.
            self._respond(sock, {"ok": False, "output": "",
                                 "error": "unknown endpoint"}, "404 Not Found")
            return

        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except Exception as e:
            self._respond(sock, {"ok": False, "output": "",
                                 "error": "bad JSON payload: %s" % e}, "400 Bad Request")
            return
        out = payload.get("out") or ""
        if payload.get("path"):
            try:
                with open(payload["path"]) as f:
                    code = f.read()
                filename = payload["path"]
            except Exception as e:
                self._respond(sock, {"ok": False, "output": "",
                                     "error": "cannot read %s: %s" % (payload["path"], e)})
                return
        else:
            code, filename = payload.get("code", ""), "<bridge>"
        self._respond(sock, _run(code, filename, out))

    def _respond(self, sock, obj, status="200 OK"):
        body = json.dumps(obj).encode("utf-8")
        sock.write(b"HTTP/1.1 " + status.encode("latin1") + b"\r\n"
                   b"Content-Type: application/json\r\n"
                   b"Content-Length: " + str(len(body)).encode() + b"\r\n"
                   b"Connection: close\r\n\r\n" + body)
        sock.flush()
        sock.disconnectFromHost()


def start_bridge(port=_PORT):
    """Start (or restart) the bridge, keeping the only reference to it on the
    long-lived `krita` module — a local would be garbage-collected the moment
    the Scripter's namespace goes away, and the server would stop listening."""
    module = sys.modules.get("krita")
    previous = getattr(module, "__krita_bridge__", None)
    if previous is not None:
        previous.close()
    bridge = _Bridge(port)
    setattr(module, "__krita_bridge__", bridge)
    return bridge


class KritaBridgeExtension(Extension):
    """Starts the bridge when Krita launches (plugin path)."""

    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        start_bridge()

    def createActions(self, window):
        pass


if globals().get("__package__"):
    # `__package__` is set when Krita's plugin loader imports this as part of the
    # krita_bridge package, and simply absent from the Scripter's exec namespace —
    # hence globals().get() rather than a bare name, which would raise NameError.
    # Imported by Krita's plugin loader: register, and let setup() start it.
    Krita.instance().addExtension(KritaBridgeExtension(Krita.instance()))
else:
    # Pasted into the Scripter and run by hand: start it right now.
    start_bridge()
