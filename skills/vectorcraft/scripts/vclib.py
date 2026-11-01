"""Shared helpers for the vectorcraft skill scripts (stdlib only, Python 3.9+).

`Session` drives `vectorcraft-cli mcp --headless` over stdio as a minimal JSON-RPC
client, so a stateful headless session needs no MCP client configuration.
"""
import json
import os
import shutil
import subprocess
import sys

PINNED_VERSION = "0.20.0"


def cli():
    """Path of vectorcraft-cli, or exit with a hint."""
    path = shutil.which("vectorcraft-cli") or os.path.expanduser("~/.local/bin/vectorcraft-cli")
    if not os.path.isfile(path):
        sys.exit("vectorcraft-cli not found (expected on PATH or in ~/.local/bin)")
    return path


def run_json_lines(args):
    """Run vectorcraft-cli with args; return (returncode, [parsed JSON lines], stderr)."""
    proc = subprocess.run([cli()] + args, capture_output=True, text=True)
    out = []
    buf = ""
    for line in proc.stdout.splitlines():
        buf += line
        try:
            out.append(json.loads(buf))
            buf = ""
        except ValueError:
            buf += "\n"
    if buf.strip():
        out.append({"raw": buf})
    return proc.returncode, out, proc.stderr.strip()


def info(path):
    """`vectorcraft-cli info FILE` as a dict."""
    proc = subprocess.run([cli(), "info", path], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError("info %s failed: %s" % (path, proc.stderr.strip() or proc.stdout.strip()))
    return json.loads(proc.stdout)


class ToolError(RuntimeError):
    pass


class Session:
    """A headless VectorCraft session. File access is confined to the given roots."""

    def __init__(self, read_root, write_root=None):
        self.read_root = os.path.realpath(read_root)
        self.write_root = os.path.realpath(write_root or read_root)
        self._id = 0
        self.proc = subprocess.Popen(
            [cli(), "mcp", "--headless",
             "--automation-read-root", self.read_root,
             "--automation-write-root", self.write_root],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, bufsize=1)
        self._rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                 "clientInfo": {"name": "vectorcraft-skill", "version": "1"}})
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
                raise ToolError("vectorcraft-cli mcp exited unexpectedly")
            msg = json.loads(line)
            if msg.get("id") == self._id:
                if "error" in msg:
                    raise ToolError(json.dumps(msg["error"]))
                return msg["result"]

    def tool(self, name, args=None):
        """Call an MCP tool; return its parsed JSON text (or the text), raise on isError."""
        res = self._rpc("tools/call", {"name": name, "arguments": args or {}})
        texts = [c.get("text", "") for c in res.get("content", []) if c.get("type") == "text"]
        images = [c for c in res.get("content", []) if c.get("type") == "image"]
        text = "\n".join(texts)
        if res.get("isError"):
            raise ToolError("%s: %s" % (name, text))
        try:
            value = json.loads(text) if text else None
        except ValueError:
            value = text
        if images and not texts:
            return {"images": images}
        return value

    def cmd(self, command_id, params=None):
        return self.tool("command_run", {"id": command_id, "params": params or {}})

    def batch(self, steps, atomic=False):
        """command_batch; raise if any step failed."""
        res = self.tool("command_batch", {"steps": steps, "atomic": atomic})
        if res.get("failed"):
            bad = [r for r in res.get("results", []) if not r.get("ok")]
            raise ToolError("batch step failed: %s" % json.dumps(bad)[:2000])
        return res

    def find(self, name=None, text=None, kind=None):
        """document.find; exact-name matches first."""
        params = {k: v for k, v in (("name", name), ("text", text), ("kind", kind)) if v}
        matches = self.cmd("document.find", params).get("matches", [])
        if name:
            exact = [m for m in matches if m.get("name") == name]
            if exact:
                return exact
        return matches

    def resolve(self, ref):
        """'@name:Headline' / '@text:Spring' / '@kind:Type' -> the single matching id."""
        key, _, value = ref[1:].partition(":")
        matches = self.find(**{key: value})
        if len(matches) != 1:
            raise ToolError("%s matched %d objects: %s" % (
                ref, len(matches), [(m["id"], m.get("name")) for m in matches][:10]))
        return matches[0]["id"]

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)
        except Exception:  # noqa: BLE001 - best effort shutdown
            self.proc.kill()


REF_PREFIXES = ("@name:", "@text:", "@kind:")


def resolve_refs(session, value):
    """Replace '@name:…' style strings (also inside lists/dicts) with object ids."""
    if isinstance(value, str) and value.startswith(REF_PREFIXES):
        return session.resolve(value)
    if isinstance(value, list):
        return [resolve_refs(session, v) for v in value]
    if isinstance(value, dict):
        return {k: resolve_refs(session, v) for k, v in value.items()}
    return value


def absolutize(value, keys=("path", "folder")):
    """Make the values of path-like keys absolute (the session rejects relative paths)."""
    if isinstance(value, list):
        return [absolutize(v, keys) for v in value]
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if k in keys and isinstance(v, str) and not v.startswith("/"):
                v = os.path.abspath(os.path.expanduser(v))
            out[k] = absolutize(v, keys)
        return out
    return value


def refuse_existing(paths, overwrite):
    if overwrite:
        return
    existing = [p for p in paths if os.path.exists(p)]
    if existing:
        sys.exit("refusing to overwrite (pass --overwrite): " + ", ".join(existing))
