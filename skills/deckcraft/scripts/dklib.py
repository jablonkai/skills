"""Shared helpers for the deckcraft skill scripts (stdlib only, Python 3.9+).

`Session` drives `deckcraft-cli mcp` over stdio as a minimal JSON-RPC client, so one
headless presentation stays open across many commands (shape ids from `slide.inspect`
stay valid) and file access stays inside the given roots.
"""
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile

PINNED_VERSION = "0.14.1"
SLIDE_W, SLIDE_H = 960.0, 540.0  # default 16:9 slide, in points


def cli():
    """Path of deckcraft-cli, or exit with a hint."""
    path = shutil.which("deckcraft-cli") or os.path.expanduser("~/.local/bin/deckcraft-cli")
    if not os.path.isfile(path):
        sys.exit("deckcraft-cli not found (expected on PATH or in ~/.local/bin)")
    return path


def run_cli(args, check=True):
    """Run deckcraft-cli with args; return the CompletedProcess (text mode)."""
    proc = subprocess.run([cli()] + args, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError("deckcraft-cli %s failed: %s" % (
            " ".join(args[:2]), proc.stderr.strip() or proc.stdout.strip()))
    return proc


def info(path):
    """`deckcraft-cli info PATH` as a dict (slides with title, layout, notes; theme; media)."""
    return json.loads(run_cli(["info", path]).stdout)


def inspect(path, index):
    """slide.inspect of one slide (0-based) of a file: shapes with ids, kinds, boxes, text."""
    out = run_cli(["run", "--in", path, "--print", "--cmd", 'slide.inspect={"index":%d}' % index]).stdout
    for line in out.splitlines():
        if line.startswith("slide.inspect"):
            return json.loads(line.split(" → ", 1)[1])
    raise RuntimeError("no slide.inspect answer for slide %d of %s" % (index, path))


def slide_text(slide):
    """All shape text of an inspected slide, one shape per line."""
    return "\n".join(s.get("text") or "" for s in slide.get("shapes", []))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def image_size(path):
    """(width, height) of a PNG, JPEG or GIF from its header, or None."""
    with open(path, "rb") as f:
        head = f.read(32)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", head[16:24])
        if head[:6] in (b"GIF87a", b"GIF89a"):
            return struct.unpack("<HH", head[6:10])
        if head[:2] != b"\xff\xd8":
            return None
        f.seek(2)
        while True:
            marker = f.read(2)
            if len(marker) < 2 or marker[0] != 0xFF:
                return None
            if marker[1] in (0xD8, 0x01) or 0xD0 <= marker[1] <= 0xD7:
                continue
            length = struct.unpack(">H", f.read(2))[0]
            if 0xC0 <= marker[1] <= 0xCF and marker[1] not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">xHH", f.read(5))
                return w, h
            f.seek(length - 2, 1)


def fit(img_wh, box):
    """The largest rect with the image's aspect ratio centred in box [x, y, w, h]."""
    x, y, w, h = box
    if not img_wh:
        return box
    iw, ih = img_wh
    scale = min(w / iw, h / ih)
    fw, fh = iw * scale, ih * scale
    return [round(x + (w - fw) / 2, 1), round(y + (h - fh) / 2, 1), round(fw, 1), round(fh, 1)]


def refuse_existing(paths, overwrite):
    if overwrite:
        return
    existing = [p for p in paths if p and os.path.exists(p)]
    if existing:
        sys.exit("refusing to overwrite (pass --overwrite): " + ", ".join(existing))


class ToolError(RuntimeError):
    pass


def common_root(dirs, what):
    """The one folder holding all dirs: `mcp` takes a single read root and a single write
    root. Refuses a root as wide as / or a home's parent, which would confine nothing."""
    root = os.path.commonpath(sorted(set(map(os.path.realpath, dirs))))
    if len(root.strip(os.sep).split(os.sep)) < 2:
        sys.exit("the %s folders %s share only %s; put them under one project folder"
                 % (what, sorted(set(dirs)), root))
    return root


class Session:
    """A headless DeckCraft session. File access is confined to one read and one write root."""

    def __init__(self, read_dirs, write_dirs):
        self._id = 0
        self.read_root = common_root(read_dirs, "input")
        self.write_root = common_root(write_dirs, "output")
        args = [cli(), "mcp", "--automation-read-root", self.read_root,
                "--automation-write-root", self.write_root]
        self._err = tempfile.TemporaryFile(mode="w+")
        self.proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=self._err, text=True, bufsize=1)
        self._rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                 "clientInfo": {"name": "deckcraft-skill", "version": "1"}})
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def _send(self, msg):
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()

    def _rpc(self, method, params):
        self._id += 1
        self._send({"jsonrpc": "2.0", "id": self._id, "method": method, "params": params})
        while True:
            line = self.proc.stdout.readline()
            if not line:
                self._err.seek(0)
                raise ToolError("deckcraft-cli mcp exited: " + self._err.read().strip()[-500:])
            msg = json.loads(line)
            if msg.get("id") == self._id:
                if "error" in msg:
                    raise ToolError(json.dumps(msg["error"]))
                return msg["result"]

    def tool(self, name, args=None):
        """Call an MCP tool; return its parsed JSON text (or the text), raise on isError."""
        res = self._rpc("tools/call", {"name": name, "arguments": args or {}})
        text = "\n".join(c.get("text", "") for c in res.get("content", []) if c.get("type") == "text")
        if res.get("isError"):
            raise ToolError("%s: %s" % (name, text))
        try:
            return json.loads(text) if text else None
        except ValueError:
            return text

    def cmd(self, command_id, params=None):
        return self.tool("run_command", {"command": command_id, "params": params or {}})

    def open(self, path):
        return self.tool("open_presentation", {"path": os.path.realpath(path)})

    def deck(self):
        """inspect_document: slides (index, id, title, layout, notes…), theme, media."""
        return self.tool("inspect_document")

    def slide(self, index):
        return self.cmd("slide.inspect", {"index": index})

    def themes(self):
        return [t["name"] for t in (self.cmd("design.themes") or {}).get("themes", [])]

    def save_as(self, path):
        return self.cmd("file.saveAs", {"path": os.path.realpath(path)})

    def export(self, path, **params):
        params["path"] = os.path.realpath(path)
        return self.cmd("file.export", params)

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)
        except Exception:  # noqa: BLE001 - best effort shutdown
            self.proc.kill()
