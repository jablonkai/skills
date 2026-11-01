"""Shared helpers for the cadcraft skill scripts (stdlib only, Python 3.9+).

`Session` drives `cadcraft-cli mcp` (headless backend, stdio) as a minimal JSON-RPC
client, so a stateful session needs no MCP client configuration. It never passes
`--connect`/`--launch`: the app's control port is unauthenticated (see
references/security.md).
"""
import json
import os
import shutil
import subprocess
import sys

PINNED_VERSION = "0.16.0"
IMAGE_EXTS = (".png", ".svg", ".pdf")
DRAWING_EXTS = (".dxf", ".dwg")


def cli():
    """Path of cadcraft-cli, or exit with a hint."""
    path = shutil.which("cadcraft-cli") or os.path.expanduser("~/.local/bin/cadcraft-cli")
    if not os.path.isfile(path):
        sys.exit("cadcraft-cli not found (expected on PATH or in ~/.local/bin)")
    return path


def run_cli(args):
    """Run cadcraft-cli with args; return (returncode, [parsed JSON lines], stderr)."""
    proc = subprocess.run([cli()] + args, capture_output=True, text=True)
    out = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            out.append({"text": line})
    return proc.returncode, out, proc.stderr.strip()


def info(path):
    """`cadcraft-cli info FILE` as a dict."""
    proc = subprocess.run([cli(), "info", path], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError("info %s failed: %s" % (path, (proc.stderr or proc.stdout).strip()))
    return json.loads(proc.stdout)


def framing_args(view=None, window=None):
    """CLI framing flags. Always explicit: `run --export` and `convert` default differently."""
    if window:
        if isinstance(window, (list, tuple)):
            window = ",".join(str(v) for v in window)
        return ["--window=" + window]  # `=` form: a negative x0 is parsed as a flag otherwise
    return ["--view", view or "extents"]


def convert(src, dst, view=None, window=None):
    """`cadcraft-cli convert`; framing flags only for image outputs."""
    args = ["convert", src, dst]
    if dst.lower().endswith(IMAGE_EXTS):
        args += framing_args(view, window)
    rc, _, err = run_cli(args)
    if rc != 0:
        raise RuntimeError("convert %s -> %s failed: %s" % (src, dst, err))


def same_file(a, b):
    return os.path.realpath(a) == os.path.realpath(b)


def inside(path, root):
    path, root = os.path.realpath(path), os.path.realpath(root)
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


class ToolError(RuntimeError):
    pass


class Session:
    """A headless CADCraft session over `cadcraft-cli mcp` on stdio (no network port)."""

    def __init__(self):
        self._id = 0
        self.proc = subprocess.Popen(
            [cli(), "mcp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, bufsize=1)
        init = self._rpc("initialize", {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "cadcraft-skill", "version": "1"}})
        backend = init.get("instructions", "")
        if "headless" not in backend.lower():
            self.close()
            raise ToolError("cadcraft-cli mcp did not start a headless backend: %s" % backend[-120:])
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
                raise ToolError("cadcraft-cli mcp exited unexpectedly")
            msg = json.loads(line)
            if msg.get("id") != self._id:
                continue
            if "error" in msg:
                raise ToolError(msg["error"].get("message", json.dumps(msg["error"])))
            return msg["result"]

    def tool(self, name, args=None):
        """Call an MCP tool; return its parsed JSON text (or {"image": bytes} for render)."""
        res = self._rpc("tools/call", {"name": name, "arguments": args or {}})
        parts = res.get("content", [])
        text = "\n".join(p.get("text", "") for p in parts if p.get("type") == "text")
        if res.get("isError"):
            raise ToolError("%s: %s" % (name, text))
        if not text:
            return {"image": True} if parts else None
        try:
            return json.loads(text)
        except ValueError:
            return text

    def cmd(self, command, params=None):
        """Run an engine command by id with JSON params (`execute`)."""
        return self.tool("execute", {"command": command, "params": params or {}})

    def layer_names(self):
        return [l["name"] for l in self.tool("inspect_drawing", {"entities": False}).get("layers", [])]

    def ensure_layer(self, layer, current=False):
        """Create a layer, or update it if it exists (`layer.new` fails on an existing name)."""
        layer = dict(layer)
        if layer["name"] in self.layer_names():
            props = {k: v for k, v in layer.items() if k in ("name", "color", "linetype", "lineweight")}
            if len(props) > 1:
                self.cmd("layer.set", props)
            if current:
                self.cmd("layer.current", {"name": layer["name"]})
        else:
            if current:
                layer["current"] = True
            self.cmd("layer.new", layer)

    def title_block(self, tb, default_height):
        """Draw a frame + attribute definitions, turn them into block `tb.name` and insert
        it with the field values. Uses the handles it created, never a window selection,
        so nothing already in the drawing is swallowed into the block.

        tb = {"name": "TB", "at": [x, y], "size": [w, h], "layer": "TITLE",
              "fields": [{"tag": "TITLE", "value": "…", "at": [dx, dy], "height": 5}]}
        Field positions are relative to the frame's lower-left corner.
        """
        x, y = tb["at"]
        w, h = tb["size"]
        self.ensure_layer({"name": tb.get("layer", "TITLE")}, current=True)
        handles = [self.cmd("rectang", {"p1": [x, y], "p2": [x + w, y + h]})["handle"]]
        values = {}
        for f in tb["fields"]:
            dx, dy = f["at"]
            handles.append(self.cmd("attdef", {
                "tag": f["tag"], "prompt": f.get("prompt", f["tag"].title()),
                "default": f.get("default", "-"), "at": [x + dx, y + dy],
                "height": f.get("height", default_height)})["handle"])
            values[f["tag"]] = f.get("value", f.get("default", "-"))
        self.cmd("select", {"handles": handles})
        self.cmd("block", {"name": tb.get("name", "TB"), "base": [x, y], "keep": "delete"})
        return self.cmd("insert", {"name": tb.get("name", "TB"), "at": [x, y], "attribs": values})

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)
        except Exception:  # noqa: BLE001 - best effort shutdown
            self.proc.kill()
