"""Shared helpers for the photocraft skill scripts (Python 3.9+, stdlib only).

Finds photocraft-cli, runs `info`, and drives one headless `serve` session over
stdio, one JSON-lines request at a time so the caller can stop at the first error.
"""

import json
import os
import shutil
import subprocess
import sys


class PcError(Exception):
    """A PhotoCraft request or CLI call failed."""


def cli_path():
    """Locate photocraft-cli: $PHOTOCRAFT_CLI, then PATH, then ~/.local/bin."""
    env = os.environ.get("PHOTOCRAFT_CLI")
    if env:
        return env
    found = shutil.which("photocraft-cli")
    if found:
        return found
    fallback = os.path.expanduser("~/.local/bin/photocraft-cli")
    if os.path.exists(fallback):
        return fallback
    raise PcError("photocraft-cli not found: install it or set PHOTOCRAFT_CLI")


def info(path):
    """Return `photocraft-cli info <path>` as a dict."""
    proc = subprocess.run(
        [cli_path(), "info", path, "--compact"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
    )
    if proc.returncode != 0:
        raise PcError("info %s: %s" % (path, (proc.stderr or proc.stdout).strip()))
    return json.loads(proc.stdout)


def walk(layers, depth=0):
    """Yield (depth, layer) over a layer tree, top of the stack first."""
    for layer in layers:
        yield depth, layer
        for item in walk(layer.get("children") or [], depth + 1):
            yield item


def find_layer(doc, name):
    """First layer whose name equals `name` (case-sensitive), or None."""
    for _, layer in walk(doc.get("layers") or []):
        if layer.get("name") == name:
            return layer
    return None


LAYER_REF = "@layer:"


def layer_ids(doc, names):
    """Map layer names to numeric ids; raise on a missing or duplicated name.

    Pass ids, not names, to engine commands: some (type.edit, layer.translate)
    silently ignore a name they cannot resolve and edit the active layer instead.
    """
    found = {}
    for _, layer in walk(doc.get("layers") or []):
        found.setdefault(layer.get("name"), []).append(layer.get("id"))
    out = {}
    for name in names:
        ids = found.get(name) or []
        if not ids:
            raise PcError("no layer named %r (layers: %s)" % (name, ", ".join(sorted(map(str, found)))))
        if len(ids) > 1:
            raise PcError("%d layers are named %r (ids %s); pick an id" % (len(ids), name, ids))
        out[name] = ids[0]
    return out


def layer_refs(params):
    """Names referenced as "@layer:<name>" anywhere in params."""
    if isinstance(params, str):
        return [params[len(LAYER_REF):]] if params.startswith(LAYER_REF) else []
    if isinstance(params, dict):
        return [n for v in params.values() for n in layer_refs(v)]
    if isinstance(params, list):
        return [n for v in params for n in layer_refs(v)]
    return []


def substitute_refs(params, ids):
    if isinstance(params, str) and params.startswith(LAYER_REF):
        return ids[params[len(LAYER_REF):]]
    if isinstance(params, dict):
        return {k: substitute_refs(v, ids) for k, v in params.items()}
    if isinstance(params, list):
        return [substitute_refs(v, ids) for v in params]
    return params


def normalize_paths(params):
    """Collapse `..`/`~` in absolute path/dir params: serve rejects parent traversal."""
    if isinstance(params, dict):
        out = {}
        for key, value in params.items():
            if key in ("path", "dir") and isinstance(value, str):
                expanded = os.path.expanduser(value)
                out[key] = os.path.normpath(expanded) if os.path.isabs(expanded) else value
            else:
                out[key] = normalize_paths(value)
        return out
    if isinstance(params, list):
        return [normalize_paths(v) for v in params]
    return params


def to_step(step):
    """Normalise a step to (method, params).

    {"cmd": id, "params": {...}, "wait": bool} -> engine.execute
    {"method": name, "params": {...}}          -> that method
    """
    if "cmd" in step:
        params = {"command": step["cmd"]}
        if step.get("params") is not None:
            params["params"] = normalize_paths(step["params"])
        if "wait" in step:
            params["wait"] = step["wait"]
        return "engine.execute", params
    if "method" in step:
        return step["method"], normalize_paths(step.get("params") or {})
    raise PcError("step needs `cmd` or `method`: %s" % json.dumps(step))


class Session(object):
    """One `photocraft-cli serve` process on stdio.

    File access in serve fails closed: every path must lie beneath the read root
    (open, place, CSV import) or the write root (save, render, export).
    """

    def __init__(self, read_root, write_root):
        self.read_root = os.path.abspath(read_root)
        self.write_root = os.path.abspath(write_root)
        self._next = 0
        self.proc = subprocess.Popen(
            [cli_path(), "serve",
             "--automation-read-root", self.read_root,
             "--automation-write-root", self.write_root],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, bufsize=1,
        )

    def request(self, method, params=None):
        """Send one request; return the full reply dict ({id, ok, result|error})."""
        self._next += 1
        line = json.dumps({"id": self._next, "method": method, "params": params or {}})
        try:
            self.proc.stdin.write(line + "\n")
            self.proc.stdin.flush()
        except BrokenPipeError:
            raise PcError("serve exited: %s" % self.proc.stderr.read().strip())
        while True:
            reply = self.proc.stdout.readline()
            if not reply:
                raise PcError("serve exited: %s" % self.proc.stderr.read().strip())
            data = json.loads(reply)
            if data.get("id") in (self._next, None):
                return data

    def call(self, method, params=None):
        """Send one request; return its result or raise PcError."""
        data = self.request(method, params)
        if not data.get("ok"):
            raise PcError("%s: %s" % (method, data.get("error")))
        return data.get("result")

    def execute(self, command, params=None):
        body = {"command": command}
        if params is not None:
            body["params"] = params
        return self.call("engine.execute", body)

    def close(self):
        if self.proc.poll() is None:
            try:
                self.proc.stdin.close()
            except OSError:
                pass
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def load_json_arg(text):
    """Parse a JSON argument, or read it from a file when it starts with '@'."""
    if text.startswith("@"):
        with open(text[1:]) as handle:
            return json.load(handle)
    return json.loads(text)


def die(message, code=1):
    sys.stderr.write("error: %s\n" % message)
    sys.exit(code)
