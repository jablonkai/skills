#!/usr/bin/env python3
"""Dependency-free WebSocket client for Rebelle's WebSocket Control (Rebelle Pro).

Rebelle speaks plain RFC 6455 text frames, one JSON object per message, so a
~90-line client beats adding a dependency the user's Python may not have.

Library use:

    from rebelle_ws import Rebelle
    with Rebelle() as r:
        r.event({"event_type": "SET_BRUSH", "tool": "PENCIL",
                 "preset": "Charcoal/Charcoal", "size": 30,
                 "color": {"r": 200, "g": 20, "b": 20}})
        r.stroke([(100, 100), (400, 300), (700, 500)], pressure=0.9)
        r.sync()                      # BOOKMARK round-trip: everything above is done
        r.export("/tmp/check.png")    # then Read the PNG to see what happened

CLI use:

    rebelle_ws.py --ping                       # is Rebelle listening?
    rebelle_ws.py --send events.json           # a Motion IO frames/events file
    rebelle_ws.py --export /tmp/check.png
    rebelle_ws.py --cmd list_tools
    rebelle_ws.py --cmd list_tool_presets --arg tool=Watercolors
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import socket
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rebelle_events import stroke_events  # noqa: E402  (sibling module, same directory)

DEFAULT_PORT = int(os.environ.get("REBELLE_WS_PORT", "8265"))


class WSError(RuntimeError):
    pass


class Rebelle:
    """One WebSocket connection to a running Rebelle."""

    def __init__(self, host: str = "127.0.0.1", port: int = DEFAULT_PORT, timeout: float = 10.0):
        try:
            self.sock = socket.create_connection((host, port), timeout=timeout)
        except OSError as exc:
            raise WSError(
                f"no WebSocket server on {host}:{port} — start Rebelle with "
                "-websocket-server-enable (see SKILL.md)"
            ) from exc
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall(
            (
                "GET / HTTP/1.1\r\n"
                f"Host: {host}:{port}\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {key}\r\n"
                "Sec-WebSocket-Version: 13\r\n\r\n"
            ).encode()
        )
        self.buf = b""
        while b"\r\n\r\n" not in self.buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise WSError("handshake failed: server closed the connection")
            self.buf += chunk
        head, self.buf = self.buf.split(b"\r\n\r\n", 1)
        if b"101" not in head.split(b"\r\n")[0]:
            raise WSError("handshake failed: " + head.decode(errors="replace")[:200])
        # Rebelle greets with e.g. "Rebelle 8 Pro here" — proof it is the right app.
        self.greeting = self.recv(timeout=5) or ""

    # --- framing ---------------------------------------------------------
    def send_text(self, text: str) -> None:
        payload = text.encode()
        mask = os.urandom(4)
        n = len(payload)
        if n < 126:
            header = struct.pack("!BB", 0x81, 0x80 | n)
        elif n < 65536:
            header = struct.pack("!BBH", 0x81, 0x80 | 126, n)
        else:
            header = struct.pack("!BBQ", 0x81, 0x80 | 127, n)
        self.sock.sendall(header + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))

    def _exact(self, n: int) -> bytes:
        while len(self.buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise WSError("connection closed by Rebelle")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def recv(self, timeout: float = 2.0):
        """Next text message, or None on timeout. Rebelle stays silent for most events."""
        self.sock.settimeout(timeout)
        try:
            b0, b1 = self._exact(2)
        except (socket.timeout, TimeoutError):
            return None
        opcode, n = b0 & 0x0F, b1 & 0x7F
        if n == 126:
            n = struct.unpack("!H", self._exact(2))[0]
        elif n == 127:
            n = struct.unpack("!Q", self._exact(8))[0]
        data = self._exact(n)
        if opcode == 8:
            raise WSError("Rebelle closed the connection")
        return data.decode(errors="replace")

    # --- Rebelle API -----------------------------------------------------
    def event(self, ev: dict, wait: float = 0.0):
        """Send one Motion IO JSON event (NEW_ARTWORK, SET_BRUSH, POINTER_*, ...)."""
        self.send_text(json.dumps(ev))
        return self.recv(timeout=wait) if wait else None

    def cmd(self, name: str, wait: float = 3.0, **params):
        """Send one live-control command ({"cmd": ...}); returns the reply text."""
        self.send_text(json.dumps({"cmd": name, **params}))
        return self.recv(timeout=wait)

    def sync(self, tag: str = "sync", timeout: float = 30.0) -> bool:
        """Block until Rebelle has processed everything sent so far.

        BOOKMARK is echoed back, and Rebelle processes messages in order, so its
        reply is the only reliable "done" signal — most events answer nothing.
        """
        self.send_text(json.dumps({"event_type": "BOOKMARK", "id": tag}))
        deadline = time.time() + timeout
        while time.time() < deadline:
            reply = self.recv(timeout=min(2.0, deadline - time.time()))
            if reply and tag in reply:
                return True
        return False

    def stroke(self, points, **kw):
        """Paint one stroke through `points` (canvas pixels, y down from top-left).

        Same signature as `rebelle_events.stroke_events`, which builds the events —
        the press/move/release rules live there so both paths obey one copy of them.
        """
        for ev in stroke_events(list(points), **kw):
            self.event(ev)

    def export(self, filename: str, timeout: float = 30.0) -> str:
        """Write the composited canvas (paper + layers) to a PNG/JPG and wait for it.

        SAVE/LOAD events are rejected over WebSockets in Rebelle 8.3, so this
        undocumented command is the only way to get pixels back out live.
        """
        path = os.path.abspath(filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        before = os.path.getmtime(path) if os.path.exists(path) else 0
        self.sync("pre_export")
        self.cmd("export_canvas", wait=0.5, filename=path)
        deadline = time.time() + timeout
        while time.time() < deadline:
            if os.path.exists(path) and os.path.getmtime(path) > before and os.path.getsize(path):
                return path
            time.sleep(0.3)
        raise WSError(f"export_canvas produced no file at {path}")

    def close(self):
        try:
            self.sock.sendall(struct.pack("!BB", 0x88, 0x80) + os.urandom(4))
        except OSError:
            pass
        self.sock.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def _send_file(r: Rebelle, path: str) -> None:
    """Replay a Motion IO events file ({"frames":[{"events":[...]}]}) live."""
    doc = json.load(open(path))
    frames = doc["frames"] if isinstance(doc, dict) and "frames" in doc else doc
    for i, frame in enumerate(frames):
        for ev in frame.get("events", []):
            r.event(ev)
        r.sync(f"frame_{i}")
        print(f"frame {i + 1}/{len(frames)} done", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--ping", action="store_true", help="check the server and print its greeting")
    ap.add_argument("--send", metavar="EVENTS.json", help="replay an events file live")
    ap.add_argument("--event", metavar="JSON", action="append", default=[], help="send one raw JSON event")
    ap.add_argument("--cmd", metavar="NAME", help="send a live-control command")
    ap.add_argument("--arg", metavar="K=V", action="append", default=[], help="parameter for --cmd")
    ap.add_argument("--export", metavar="PNG", help="export the canvas and print the path")
    args = ap.parse_args()

    try:
        with Rebelle(port=args.port) as r:
            if args.ping:
                print(r.greeting or "(connected, no greeting)")
            for raw in args.event:
                r.event(json.loads(raw))
            if args.send:
                _send_file(r, args.send)
            if args.cmd:
                params = {}
                for kv in args.arg:
                    k, _, v = kv.partition("=")
                    try:
                        params[k] = json.loads(v)
                    except json.JSONDecodeError:
                        params[k] = v
                print(r.cmd(args.cmd, **params))
            if args.event or args.send:
                r.sync("cli_done")
            if args.export:
                print(r.export(args.export))
    except WSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
