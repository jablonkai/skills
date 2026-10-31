"""Shared helpers for the effectcraft skill scripts (stdlib only, Python 3.9+).

`Session` drives `effectcraft-cli mcp` over stdio as a minimal JSON-RPC client, so a
stateful headless session needs no MCP client configuration.
"""
import json
import os
import shutil
import subprocess
import sys

PINNED_VERSION = "0.19.0"


def cli():
    """Path of effectcraft-cli, or exit with a hint."""
    path = shutil.which("effectcraft-cli") or os.path.expanduser("~/.local/bin/effectcraft-cli")
    if not os.path.isfile(path):
        sys.exit("effectcraft-cli not found (expected on PATH or in ~/.local/bin)")
    return path


def run_cli(args, check=True):
    """Run effectcraft-cli with args; return the CompletedProcess (text mode)."""
    proc = subprocess.run([cli()] + args, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError("effectcraft-cli %s failed: %s" % (
            " ".join(args[:2]), proc.stderr.strip() or proc.stdout.strip()))
    return proc


def info(project):
    """`effectcraft-cli info --project F --json` as a dict. Never call info without a
    project: the CLI then opens the bundled demo project."""
    return json.loads(run_cli(["info", "--project", project, "--json"]).stdout)


def ffprobe(path):
    """ffprobe streams + format of a media file as a dict."""
    exe = shutil.which("ffprobe")
    if not exe:
        raise RuntimeError("ffprobe not found (brew install ffmpeg)")
    proc = subprocess.run(
        [exe, "-v", "error", "-count_frames", "-show_streams", "-show_format",
         "-of", "json", path], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError("ffprobe %s: %s" % (path, proc.stderr.strip()))
    return json.loads(proc.stdout)


class ToolError(RuntimeError):
    pass


class Session:
    """A headless EffectCraft session. File access is confined to the given roots."""

    def __init__(self, read_roots, write_roots):
        self._id = 0
        args = [cli(), "mcp"]
        for root in read_roots:
            args += ["--automation-read-root", os.path.realpath(root)]
        for root in write_roots:
            args += ["--automation-write-root", os.path.realpath(root)]
        self.proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self._rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                 "clientInfo": {"name": "effectcraft-skill", "version": "1"}})
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
                raise ToolError("effectcraft-cli mcp exited unexpectedly")
            msg = json.loads(line)
            if msg.get("id") == self._id:
                if "error" in msg:
                    raise ToolError(json.dumps(msg["error"]))
                return msg["result"]

    def tool(self, name, args=None):
        """Call an MCP tool; return its parsed JSON text (or the text), raise on isError."""
        res = self._rpc("tools/call", {"name": name, "arguments": args or {}})
        content = res.get("content", [])
        text = "\n".join(c.get("text", "") for c in content if c.get("type") == "text")
        if res.get("isError"):
            raise ToolError("%s: %s" % (name, text))
        try:
            return json.loads(text) if text else None
        except ValueError:
            return text

    def cmd(self, command_id, params=None):
        return self.tool("execute_command", {"command": command_id, "params": params or {}})

    def batch(self, steps, label=None):
        """One undo step, rolled back on failure; "$N.key" in a param is step N's result."""
        args = {"steps": steps, "atomic": True}
        if label:
            args["label"] = label
        return self.tool("batch", args)

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
