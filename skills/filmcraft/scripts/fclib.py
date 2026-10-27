"""Shared helpers for the filmcraft scripts: locate filmcraft-cli, talk to its MCP session, time units."""
import json
import os
import shutil
import subprocess
import sys

TICKS = 254016000000  # ticks per second


def cli_path():
    """Return the filmcraft-cli executable, or exit with a hint."""
    found = shutil.which("filmcraft-cli")
    if found:
        return found
    local = os.path.expanduser("~/.local/bin/filmcraft-cli")
    if os.access(local, os.X_OK):
        return local
    sys.exit("filmcraft-cli not found on PATH or in ~/.local/bin")


def cli(*args, check=False):
    """Run filmcraft-cli with args; return the CompletedProcess (text mode)."""
    proc = subprocess.run([cli_path(), *args], capture_output=True, text=True)
    if check and proc.returncode != 0:
        sys.exit(f"filmcraft-cli {' '.join(args[:3])} failed (exit {proc.returncode}): "
                 f"{(proc.stderr or proc.stdout).strip()}")
    return proc


def inspect(project, what="sequence"):
    """Return `filmcraft-cli --project P inspect WHAT` as a dict."""
    proc = cli("--project", project, "inspect", what, "--compact", check=True)
    return json.loads(proc.stdout)


class Session:
    """One headless engine kept alive over `filmcraft-cli mcp`, so commands share state in memory."""

    def __init__(self, project=None):
        args = [cli_path()]
        if project:
            args += ["--project", project]
        self.proc = subprocess.Popen(args + ["mcp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True, bufsize=1)
        self.next_id = 0
        self._call("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                  "clientInfo": {"name": "filmcraft-skill", "version": "1"}})
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def _send(self, msg):
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()

    def _call(self, method, params):
        self.next_id += 1
        self._send({"jsonrpc": "2.0", "id": self.next_id, "method": method, "params": params})
        while True:
            line = self.proc.stdout.readline()
            if not line:
                err = self.proc.stderr.read()
                sys.exit(f"filmcraft-cli mcp exited: {err.strip()}")
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if msg.get("id") == self.next_id:
                if "error" in msg:
                    raise RuntimeError(msg["error"].get("message", str(msg["error"])))
                return msg["result"]

    def tool(self, name, args=None):
        """Call an MCP tool; return its parsed JSON payload. Raises RuntimeError on a tool error."""
        res = self._call("tools/call", {"name": name, "arguments": args or {}})
        text = "".join(c.get("text", "") for c in res.get("content", []) if c.get("type") == "text")
        if res.get("isError"):
            raise RuntimeError(text or "tool error")
        try:
            return json.loads(text) if text else None
        except json.JSONDecodeError:
            return text

    def run(self, cmd_id, params=None):
        return self.tool("command_run", {"id": cmd_id, "params": params or {}})

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


def fr(ticks, fps):
    return round(ticks * fps / TICKS)


def summary(seq):
    if not seq:
        print("no active sequence")
        return
    rate = seq["settings"]["frame_rate"]
    fps = rate["num"] / rate["den"]
    s = seq["settings"]
    print(f"sequence {seq['name']} (id {seq['id']}): {s['width']}x{s['height']} @ {fps:g} fps, "
          f"{seq['durationFrames']} frames ({seq['durationFrames'] / fps:.3f} s)")
    for kind in ("video", "audio"):
        for t in seq[kind]:
            items = [f"{i.get('name')}[clip {i['clip']}] {i['startFrame']}-{i['endFrame']}" for i in t["items"]]
            trs = [f"{x['effect']} {fr(x['start'], fps)}+{fr(x['duration'], fps)}f" for x in t.get("transitions", [])]
            if items or trs:
                print(f"  {t['name']}: " + "; ".join(items) + (f" | transitions: {', '.join(trs)}" if trs else ""))
    for m in seq.get("markers", []):
        print(f"  marker {m['name']!r} @ frame {fr(m['start'], fps)} ({m['color']})")
    if seq.get("in") is not None or seq.get("out") is not None:
        i = fr(seq["in"], fps) if seq.get("in") is not None else None
        o = fr(seq["out"], fps) if seq.get("out") is not None else None
        print(f"  in/out: {i} - {o} (frames, out inclusive) -> exports with no --range use only this span")


def fps_of(seq):
    fr = seq["settings"]["frame_rate"]
    return fr["num"] / fr["den"]


def tc_to_frame(tc, fps, drop=None):
    """HH:MM:SS:FF (or HH:MM:SS;FF drop-frame) -> frame number; plain numbers are seconds."""
    tc = str(tc).strip()
    if ":" not in tc and ";" not in tc:
        return round(float(tc) * fps)
    drop = drop if drop is not None else ";" in tc
    parts = [int(p) for p in tc.replace(";", ":").split(":")]
    if len(parts) != 4:
        raise ValueError(f"not a timecode: {tc}")
    h, m, s, f = parts
    base = round(fps)
    frames = ((h * 60 + m) * 60 + s) * base + f
    if drop:
        dropped = 2 if base == 30 else 4
        total_min = h * 60 + m
        frames -= dropped * (total_min - total_min // 10)
    return frames


def ffprobe(path):
    """Return {codec, width, height, duration, frames} for the first video stream (or audio only)."""
    if not shutil.which("ffprobe"):
        sys.exit("ffprobe not found (brew install ffmpeg)")
    proc = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                           "format=duration:stream=codec_type,codec_name,width,height,nb_frames",
                           "-of", "json", path], capture_output=True, text=True)
    if proc.returncode != 0:
        return {"error": proc.stderr.strip()}
    d = json.loads(proc.stdout)
    streams = d.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    out = {"duration": float(d.get("format", {}).get("duration", 0) or 0),
           "audio": a.get("codec_name") if a else None}
    if v:
        out.update(codec=v.get("codec_name"), width=v.get("width"), height=v.get("height"),
                   frames=int(v["nb_frames"]) if str(v.get("nb_frames", "")).isdigit() else None)
    else:
        out["codec"] = a.get("codec_name") if a else None
    return out
