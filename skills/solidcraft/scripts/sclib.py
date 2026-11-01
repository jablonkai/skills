"""Shared helpers for the solidcraft skill scripts (stdlib only, Python 3.9+).

`cli()` finds solidcraft-cli (SOLIDCRAFT_CLI, then the app bundle, then PATH) and warns
when the copy on PATH is older than the app's. `Session` drives `solidcraft-cli mcp
--headless --param-check strict` over stdio, so a misspelled parameter key is an error
instead of being silently dropped, and file access stays inside the given folders.
"""
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib

PINNED_VERSION = "0.29.0"
APP_CLI = "/Applications/SolidCraft.app/Contents/MacOS/solidcraft-cli"
_CLI = None


def _version(path):
    try:
        out = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.TimeoutExpired):
        return None
    parts = out.strip().split()
    return parts[-1] if parts else None


def _vtuple(v):
    try:
        return tuple(int(x) for x in (v or "").split("."))
    except ValueError:
        return ()


def cli():
    """Path of solidcraft-cli, or exit with a hint. Cached after the first call."""
    global _CLI
    if _CLI:
        return _CLI
    env = os.environ.get("SOLIDCRAFT_CLI")
    on_path = shutil.which("solidcraft-cli") or os.path.expanduser("~/.local/bin/solidcraft-cli")
    if env:
        path = env
    elif os.path.isfile(APP_CLI):
        path = APP_CLI
        if os.path.isfile(on_path) and os.path.realpath(on_path) != os.path.realpath(APP_CLI):
            pv, av = _version(on_path), _version(APP_CLI)
            if _vtuple(pv) < _vtuple(av):
                print("note: solidcraft-cli on PATH is %s, the app's is %s; using the app's" % (pv, av),
                      file=sys.stderr)
    else:
        path = on_path
    if not os.path.isfile(path):
        sys.exit("solidcraft-cli not found (set SOLIDCRAFT_CLI, install SolidCraft.app, or put it on PATH)")
    _CLI = path
    return path


def run_cli(args, check=True):
    """Run solidcraft-cli with args; return the CompletedProcess (text mode)."""
    proc = subprocess.run([cli()] + args, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError("solidcraft-cli %s failed: %s" % (
            " ".join(args[:2]), (proc.stderr.strip() or proc.stdout.strip())[-1500:]))
    return proc


def evaluate(path, script=None):
    """`solidcraft-cli eval` of a design, part or script (on `path` when script is given) as a dict."""
    fd, out = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        args = ["eval", script, "--in", path] if script else ["eval", path]
        run_cli(args + ["--json-out", out])
        with open(out, encoding="utf-8") as f:
            return json.load(f)
    finally:
        os.unlink(out)


def summary(ev):
    """The parts of an eval that matter for a report: bodies, totals, params, feature errors."""
    def r(x, n=3):
        return round(x, n) if isinstance(x, (int, float)) else x

    bodies = []
    for b in ev.get("bodies", []):
        lo, hi = b["bbox"]["min"], b["bbox"]["max"]
        bodies.append({
            "name": b["name"], "closed": b.get("closed"),
            "volume_mm3": r(b.get("volume_mm3")), "mass_g": r(b.get("mass_g")),
            "bbox_min": [r(v) for v in lo], "bbox_max": [r(v) for v in hi],
            "size": [r(h - l) for l, h in zip(lo, hi)],
            "faces": b.get("faces"), "face_types": b.get("face_types"),
        })
    tot = ev.get("total", {})
    return {
        "body_count": ev.get("body_count", len(bodies)),
        "volume_mm3": r(tot.get("volume_mm3")), "mass_g": r(tot.get("mass_g")),
        "open_bodies_skipped": tot.get("open_bodies_skipped"),
        "bodies": bodies,
        "params": {p["name"]: p["expression"] for p in ev.get("params", [])},
        "features": [f["name"] for f in ev.get("timeline", [])],
        "feature_errors": [{"feature": f["name"], "error": f.get("error"), "warning": f.get("warning")}
                           for f in ev.get("timeline", []) if f.get("error") or f.get("warning")],
    }


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def refuse_existing(paths, overwrite):
    if overwrite:
        return
    existing = [p for p in paths if p and os.path.exists(p)]
    if existing:
        sys.exit("refusing to overwrite (pass --overwrite): " + ", ".join(existing))


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def png_pixels(path):
    """(width, height, channels, rows) of an 8-bit non-interlaced PNG; rows are bytes."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG: " + path)
    pos, idat, w = 8, [], None
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
            if depth != 8 or interlace:
                raise ValueError("only 8-bit non-interlaced PNGs are supported")
            ch = {0: 1, 2: 3, 4: 2, 6: 4}.get(ctype)
            if ch is None:
                raise ValueError("palette PNGs are not supported")
        elif kind == b"IDAT":
            idat.append(body)
        elif kind == b"IEND":
            break
        pos += 12 + length
    raw = zlib.decompress(b"".join(idat))
    stride = w * ch
    rows, prev = [], bytearray(stride)
    for y in range(h):
        ftype = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        if ftype == 1:
            for i in range(ch, stride):
                line[i] = (line[i] + line[i - ch]) & 255
        elif ftype == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif ftype == 3:
            for i in range(stride):
                left = line[i - ch] if i >= ch else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 255
        elif ftype == 4:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                b = prev[i]
                c = prev[i - ch] if i >= ch else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[i] = (line[i] + pred) & 255
        rows.append(bytes(line))
        prev = line
    return w, h, ch, rows


def png_stats(path, step=4):
    """Distinct sampled colours and the share of samples that differ from the corner pixel."""
    w, h, ch, rows = png_pixels(path)
    corner = rows[0][:min(ch, 3)]
    colours, differ, n = set(), 0, 0
    for y in range(0, h, step):
        row = rows[y]
        for x in range(0, w, step):
            px = row[x * ch:x * ch + min(ch, 3)]
            colours.add(px)
            n += 1
            if sum(abs(a - b) for a, b in zip(px, corner)) > 24:
                differ += 1
    return {"width": w, "height": h, "colours": len(colours), "content_share": round(differ / max(n, 1), 4)}


def png_diff(a, b, step=4):
    """Mean absolute channel difference (0-255) between two same-size PNGs, sampled."""
    wa, ha, ca, ra = png_pixels(a)
    wb, hb, cb, rb = png_pixels(b)
    if (wa, ha) != (wb, hb):
        return 255.0
    k, total, n = min(ca, cb, 3), 0, 0
    for y in range(0, ha, step):
        for x in range(0, wa, step):
            pa, pb = ra[y][x * ca:x * ca + k], rb[y][x * cb:x * cb + k]
            total += sum(abs(p - q) for p, q in zip(pa, pb))
            n += k
    return round(total / max(n, 1), 3)


class ToolError(RuntimeError):
    data = None


class Session:
    """A headless SolidCraft MCP session with strict parameter checks.

    File access is limited to `allow` folders (plus the open design's folder and a temp
    folder, which the server always allows)."""

    def __init__(self, allow=()):
        self._id = 0
        args = [cli(), "mcp", "--headless", "--param-check", "strict"]
        for d in sorted(set(os.path.realpath(d) for d in allow)):
            args += ["--allow-path", d]
        self._err = tempfile.TemporaryFile(mode="w+")
        self.proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=self._err, text=True, bufsize=1)
        self._rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                 "clientInfo": {"name": "solidcraft-skill", "version": "1"}})
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
                raise ToolError("solidcraft-cli mcp exited: " + self._err.read().strip()[-500:])
            msg = json.loads(line)
            if msg.get("id") == self._id:
                if "error" in msg:
                    raise ToolError(json.dumps(msg["error"]))
                return msg["result"]

    def tool(self, name, args=None):
        """Call an MCP tool; return its parsed JSON text (or the text), raise on isError."""
        res = self._rpc("tools/call", {"name": name, "arguments": args or {}})
        text = "\n".join(c.get("text", "") for c in res.get("content", []) if c.get("type") == "text")
        try:
            data = json.loads(text) if text else None
        except ValueError:
            data = text
        if res.get("isError"):
            err = ToolError("%s: %s" % (name, text))
            err.data = data
            raise err
        return data

    def batch(self, commands):
        """Run steps all-or-nothing; raise ToolError naming the failed step (1-based)."""
        try:
            return self.tool("batch", {"commands": commands, "verbose": False})
        except ToolError as e:
            failed = isinstance(getattr(e, "data", None), dict) and e.data.get("failed")
            if not failed:
                raise
            i = failed.get("index")
            raise ToolError("step %s (%s) failed: %s; nothing was applied" % (
                i + 1 if isinstance(i, int) else "?", failed.get("command"), failed.get("error")))

    def cmd(self, command_id, params=None):
        return self.tool("execute", {"command": command_id, "params": params or {}, "verbose": False})

    def open(self, path):
        return self.tool("open", {"path": os.path.realpath(path)})

    def save(self, path):
        return self.tool("save", {"path": os.path.realpath(path)})

    def export(self, path):
        return self.tool("export", {"path": os.path.realpath(path)})

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)
        except Exception:  # noqa: BLE001 - best effort shutdown
            self.proc.kill()


def load_script(arg):
    """A command script from a file or inline JSON: {"commands": [...]} or a bare list."""
    text = arg
    if not arg.lstrip().startswith(("{", "[")):
        with open(arg, encoding="utf-8") as f:
            text = f.read()
    data = json.loads(text)
    steps = data.get("commands") if isinstance(data, dict) else data
    if not isinstance(steps, list) or not all(isinstance(s, dict) and "command" in s for s in steps):
        sys.exit('a script is {"commands": [{"command": ID, "params": {...}}, ...]}')
    return [{"command": s["command"], "params": s.get("params", {})} for s in steps]
