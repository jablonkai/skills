"""Shared helpers for the figcraft skill scripts (stdlib only, Python 3.9+).

`Session` drives `figcraft-cli mcp` over stdio as a minimal JSON-RPC client, so a
stateful headless session needs no MCP client configuration.
"""
import json
import os
import shutil
import subprocess
import sys

PINNED_VERSION = "0.13.1"


def cli():
    """Path of figcraft-cli, or exit with a hint."""
    path = shutil.which("figcraft-cli") or os.path.expanduser("~/.local/bin/figcraft-cli")
    if not os.path.isfile(path):
        sys.exit("figcraft-cli not found (expected on PATH or in ~/.local/bin)")
    return path


def run_cli(args, check=True):
    """Run figcraft-cli with args; return the CompletedProcess (text mode)."""
    proc = subprocess.run([cli()] + args, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError("figcraft-cli %s failed: %s" % (
            " ".join(args[:2]), proc.stderr.strip() or proc.stdout.strip()))
    return proc


def info(path):
    """`figcraft-cli info FILE --json` as a dict."""
    return json.loads(run_cli(["info", path, "--json"]).stdout)


class ToolError(RuntimeError):
    pass


class Session:
    """A headless FigCraft session. File access is confined to the given roots."""

    def __init__(self, read_root, write_root=None):
        self.read_root = os.path.realpath(read_root)
        self.write_root = os.path.realpath(write_root or read_root)
        self._id = 0
        self.proc = subprocess.Popen(
            [cli(), "mcp",
             "--automation-read-root", self.read_root,
             "--automation-write-root", self.write_root],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, bufsize=1)
        self._rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                 "clientInfo": {"name": "figcraft-skill", "version": "1"}})
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
                raise ToolError("figcraft-cli mcp exited unexpectedly")
            msg = json.loads(line)
            if msg.get("id") == self._id:
                if "error" in msg:
                    raise ToolError(json.dumps(msg["error"]))
                return msg["result"]

    def tool(self, name, args=None):
        """Call an MCP tool; return its parsed JSON text (or the text), raise on isError."""
        res = self._rpc("tools/call", {"name": name, "arguments": args or {}})
        content = res.get("content", [])
        texts = [c.get("text", "") for c in content if c.get("type") == "text"]
        images = [c for c in content if c.get("type") == "image"]
        text = "\n".join(texts)
        if res.get("isError"):
            raise ToolError("%s: %s" % (name, text))
        try:
            value = json.loads(text) if text else None
        except ValueError:
            value = text
        if images:
            return {"result": value, "images": images}
        return value

    def cmd(self, command_id, params=None):
        return self.tool("run_command", {"command": command_id, "params": params or {}})

    def batch(self, commands, label=None):
        """One undo step; {"$step": n} in params refers to step n's result id."""
        args = {"commands": commands}
        if label:
            args["label"] = label
        return self.tool("batch", args)

    def tree(self, depth=50):
        """Every layer of every page, flattened: [{id, name, type, page, parent, node}]."""
        doc = self.tool("inspect_document", {"depth": depth, "allPages": True})
        return flatten(doc)

    def find(self, name=None, text=None, type=None):  # noqa: A002 - mirrors the ref key
        """Layers matching all given keys. "Home/Headline" also matches a layer named
        Headline under the top-level frame Home when no layer has the literal name."""
        layers = self.tree()
        top = None
        if name is not None and "/" in name and not any(n["name"] == name for n in layers):
            top, _, name = name.partition("/")
        hits = []
        for n in layers:
            if name is not None and n["name"] != name:
                continue
            if top is not None and n["top"] != top:
                continue
            if text is not None and text not in (n["node"].get("characters") or ""):
                continue
            if type is not None and n["type"].lower() != type.lower():
                continue
            hits.append(n)
        return hits

    def resolve(self, ref):
        """'@name:Title' / '@text:Sign in' / '@type:COMPONENT' -> the single matching id."""
        key, _, value = ref[1:].partition(":")
        matches = self.find(**{key: value})
        if len(matches) != 1:
            raise ToolError("%s matched %d layers: %s" % (
                ref, len(matches), [(m["id"], m["name"]) for m in matches][:10]))
        return matches[0]["id"]

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)
        except Exception:  # noqa: BLE001 - best effort shutdown
            self.proc.kill()


def flatten(doc):
    """inspect_document JSON -> flat list of layers with page, parent id and top-level frame name."""
    out = []

    def walk(node, page, parent, top):
        out.append({"id": node.get("id"), "name": node.get("name"), "type": node.get("type", ""),
                    "page": page, "parent": parent, "top": top, "node": node})
        for child in node.get("children") or []:
            walk(child, page, node.get("id"), top)

    document = doc.get("document", doc)
    for page in document.get("pages", []):
        for child in page.get("children") or []:
            walk(child, page.get("name"), None, child.get("name"))
    return out


REF_PREFIXES = ("@name:", "@text:", "@type:")


def resolve_refs(session, value):
    """Replace '@name:…' style strings (also inside lists/dicts) with layer ids."""
    if isinstance(value, str) and value.startswith(REF_PREFIXES):
        return session.resolve(value)
    if isinstance(value, list):
        return [resolve_refs(session, v) for v in value]
    if isinstance(value, dict):
        return {k: resolve_refs(session, v) for k, v in value.items()}
    return value


def absolutize(value, keys=("path", "dir")):
    """Make the values of path-like keys absolute (roots are checked on real paths)."""
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
