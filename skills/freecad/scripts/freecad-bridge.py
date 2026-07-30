# FreeCAD Bridge — run this INSIDE a running FreeCAD GUI (Macro ▸ Execute, or paste
# into the Python console). It starts a tiny HTTP server on 127.0.0.1:8735 that
# executes whatever build script is POSTed to it, in the LIVE FreeCAD session, on
# the GUI (main) thread — so the viewport updates and Gui.*/saveImage work.
#
# It is integrated with Qt's event loop via QTcpServer, so it never blocks the UI.
# Each request runs synchronously and the HTTP response carries the script's
# captured stdout plus any traceback, so the sender gets real feedback.
#
#   GET  /ping         -> {"ok": true, "bridge": "freecad", "version": "1.1.1"}
#   POST /run  {code}  -> exec inline code   ; {path} -> exec a .py file
#                         optional {out} sets the OUT dir (env + a global var)
#
# Env overrides (read when the macro starts): FREECAD_BRIDGE_PORT (8735),
# FREECAD_BRIDGE_STATUS (/tmp/freecad-bridge-status.json).
import os
import sys
import io
import json
import traceback

import FreeCAD as App
try:
    import FreeCADGui as Gui
except Exception:
    Gui = None
# FreeCAD 1.1 ships PySide6 (Qt6); older builds PySide2. Try both.
try:
    from PySide6 import QtCore, QtNetwork
except ImportError:
    from PySide2 import QtCore, QtNetwork

_PORT = int(os.environ.get("FREECAD_BRIDGE_PORT", "8735"))
_STATUS = os.environ.get("FREECAD_BRIDGE_STATUS", "/tmp/freecad-bridge-status.json")


def _run(code, filename, out):
    """Exec code in a fresh namespace; capture stdout and any error."""
    ns = {"__name__": "__main__", "__file__": filename,
          "App": App, "FreeCAD": App, "Gui": Gui, "OUT": out}
    if out:
        os.environ["OUT"] = out
    buf = io.StringIO()
    saved = sys.stdout
    result = {"ok": True, "output": "", "error": None}
    try:
        sys.stdout = buf
        exec(compile(code, filename, "exec"), ns)
    except BaseException:
        result["ok"] = False
        result["error"] = traceback.format_exc()
    finally:
        sys.stdout = saved
        result["output"] = buf.getvalue()
    return result


class _Bridge(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self.seq = 0
        self.bufs = {}
        self.server = QtNetwork.QTcpServer(self)
        if not self.server.listen(QtNetwork.QHostAddress("127.0.0.1"), _PORT):
            App.Console.PrintError("FreeCAD Bridge: cannot bind 127.0.0.1:%d (%s)\n"
                                   % (_PORT, self.server.errorString()))
            return
        self.server.newConnection.connect(self._accept)
        App.Console.PrintMessage("FreeCAD Bridge listening on 127.0.0.1:%d\n" % _PORT)

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
        clen = 0
        for ln in lines[1:]:
            if ln.lower().startswith(b"content-length:"):
                try:
                    clen = int(ln.split(b":", 1)[1].strip())
                except ValueError:
                    clen = 0
        if len(body) < clen:
            return                                   # wait for the rest of the body

        if path.startswith("/ping"):
            resp = {"ok": True, "bridge": "freecad",
                    "version": ".".join(App.Version()[0:3])}
        else:
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except Exception as e:
                payload = {}
                App.Console.PrintError("Bridge: bad JSON (%s)\n" % e)
            out = payload.get("out") or ""
            if payload.get("path"):
                try:
                    with open(payload["path"]) as f:
                        code = f.read()
                    fn = payload["path"]
                except Exception as e:
                    self._respond(sock, {"ok": False, "output": "",
                                         "error": "cannot read %s: %s" % (payload.get("path"), e)})
                    return
            else:
                code, fn = payload.get("code", ""), "<bridge>"
            resp = _run(code, fn, out)
            self.seq += 1
            resp["seq"] = self.seq
            try:
                with open(_STATUS, "w") as f:
                    json.dump({"seq": self.seq, "ok": resp["ok"]}, f)
            except Exception:
                pass
        self._respond(sock, resp)

    def _respond(self, sock, obj):
        body = json.dumps(obj).encode("utf-8")
        sock.write(b"HTTP/1.1 200 OK\r\n"
                   b"Content-Type: application/json\r\n"
                   b"Content-Length: " + str(len(body)).encode() + b"\r\n"
                   b"Connection: close\r\n\r\n" + body)
        sock.flush()
        sock.disconnectFromHost()


# Keep a reference on the FreeCAD module so the server survives past this macro's
# scope (otherwise it would be garbage-collected and stop listening).
if getattr(App, "__freecad_bridge__", None) is not None:
    try:
        App.__freecad_bridge__.server.close()
    except Exception:
        pass
App.__freecad_bridge__ = _Bridge()
