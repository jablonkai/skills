"""Shared helpers for the designcraft skill scripts (stdlib only, Python 3.9+).

`Session` drives `designcraft-cli mcp` over stdio as a minimal JSON-RPC client, so a
stateful headless session needs no MCP client configuration and keeps file access
inside the given roots.
"""
import json
import os
import shutil
import subprocess
import sys
import zipfile

PINNED_VERSION = "0.13.0"
PAGE_MARKER = "\ue000"  # Current Page Number marker inside story text


def cli():
    """Path of designcraft-cli, or exit with a hint."""
    path = shutil.which("designcraft-cli") or os.path.expanduser("~/.local/bin/designcraft-cli")
    if not os.path.isfile(path):
        sys.exit("designcraft-cli not found (expected on PATH or in ~/.local/bin)")
    return path


def run_cli(args, check=True):
    """Run designcraft-cli with args; return the CompletedProcess (text mode)."""
    proc = subprocess.run([cli()] + args, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError("designcraft-cli %s failed: %s" % (
            " ".join(args[:2]), proc.stderr.strip() or proc.stdout.strip()))
    return proc


def run_cmds(doc, *cmds):
    """`designcraft-cli run --in DOC --cmd …`; the last command's JSON result."""
    args = ["run", "--in", doc]
    for c in cmds:
        args += ["--cmd", c if isinstance(c, str) else "%s=%s" % (c[0], json.dumps(c[1]))]
    lines = [l for l in run_cli(args).stdout.splitlines() if l.strip()]
    return json.loads(lines[-1]) if lines else None


def inspect(doc):
    return run_cmds(doc, "document.inspect")


def links(doc):
    return run_cmds(doc, "links.list") or []


def doc_json(doc):
    """The document model stored in a .designcraft zip (styles with attributes, stories
    with per-paragraph styles, parents, assets, dataMerge)."""
    with zipfile.ZipFile(doc) as z:
        return json.loads(z.read("document.json"))


def validate_pdf(pdf):
    proc = run_cli(["validate-pdf", pdf], check=False)
    try:
        return json.loads(proc.stdout)
    except ValueError:
        return {"valid": False, "error": (proc.stderr or proc.stdout).strip()}


class ToolError(RuntimeError):
    pass


class Session:
    """A headless DesignCraft session. File access is confined to the given roots."""

    def __init__(self, read_roots, write_roots):
        self._id = 0
        args = [cli(), "mcp"]
        for root in sorted(set(map(os.path.realpath, read_roots))):
            args += ["--automation-read-root", root]
        for root in sorted(set(map(os.path.realpath, write_roots))):
            args += ["--automation-write-root", root]
        self.proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self._rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                 "clientInfo": {"name": "designcraft-skill", "version": "1"}})
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
                raise ToolError("designcraft-cli mcp exited unexpectedly")
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
        return self.tool("execute", {"command": command_id, "params": params or {}})

    def batch(self, steps):
        """Run [(command, params)…] in order; "$N.path" in a param is step N's result
        (0-based). Every step's params are checked before the first runs."""
        res = self.tool("batch", {"commands": [{"command": c, "params": p} for c, p in steps]})
        return res.get("results", []) if isinstance(res, dict) else res

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)
        except Exception:  # noqa: BLE001 - best effort shutdown
            self.proc.kill()


def refuse_existing(paths, overwrite):
    if overwrite:
        return
    existing = [p for p in paths if os.path.exists(p)]
    if existing:
        sys.exit("refusing to overwrite (pass --overwrite): " + ", ".join(existing))


def field_names(source):
    """Column names from a data.source.select result ({fields: [{name, kind}]})."""
    return [f["name"] if isinstance(f, dict) else f for f in source.get("fields", [])]


def mm(v):
    """Millimetres to points (every DesignCraft size and coordinate is in points)."""
    return v * 72.0 / 25.4
