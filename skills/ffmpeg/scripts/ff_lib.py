"""Shared helpers for the ffmpeg skill scripts (stdlib only, Python 3.9+).

- find_ffmpeg(filters): the first ffmpeg build that has every named filter
  (plain Homebrew ffmpeg lacks libass/freetype; ffmpeg-full is keg-only beside it)
- probe(): ffprobe JSON, keyframes(): keyframe timestamps of the first video stream
- run_ffmpeg(): runs a command with -progress, prints 10% steps, writes atomically
"""
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile

FULL_CANDIDATES = [
    "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg",
    "/usr/local/opt/ffmpeg-full/bin/ffmpeg",
]
_filter_cache = {}


def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def _candidates():
    seen = []
    for c in [os.environ.get("FFMPEG"), shutil.which("ffmpeg"), "/opt/homebrew/bin/ffmpeg",
              "/usr/local/bin/ffmpeg"] + FULL_CANDIDATES:
        if c and os.access(c, os.X_OK) and os.path.realpath(c) not in [os.path.realpath(s) for s in seen]:
            seen.append(c)
    return seen


def filters_of(binary):
    if binary not in _filter_cache:
        out = subprocess.run([binary, "-hide_banner", "-filters"], capture_output=True, text=True).stdout
        names = set()
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 3 and "->" in parts[2]:
                names.add(parts[1])
        _filter_cache[binary] = names
    return _filter_cache[binary]


def find_ffmpeg(filters=()):
    """Return the first ffmpeg that has all `filters`; exit 2 with an install hint otherwise."""
    cands = _candidates()
    if not cands:
        die("ffmpeg not found. Install: brew install ffmpeg", 2)
    for c in cands:
        if all(f in filters_of(c) for f in filters):
            return c
    die(f"no installed ffmpeg has the filter(s) {', '.join(filters)}. "
        "The Homebrew 'ffmpeg' formula is built without libass/freetype; "
        "install the keg-only full build beside it: brew install ffmpeg-full", 2)


def ffprobe_for(ffmpeg):
    side = os.path.join(os.path.dirname(ffmpeg), "ffprobe")
    return side if os.access(side, os.X_OK) else (shutil.which("ffprobe") or die("ffprobe not found", 2))


def probe(path, ffprobe=None):
    ffprobe = ffprobe or ffprobe_for(find_ffmpeg())
    r = subprocess.run([ffprobe, "-v", "error", "-of", "json", "-show_streams", "-show_format", path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        die(f"ffprobe cannot read {path}: {r.stderr.strip()[:300]}")
    return json.loads(r.stdout)


def duration(info):
    d = info.get("format", {}).get("duration")
    if d:
        return float(d)
    return max([float(s.get("duration", 0)) for s in info.get("streams", [])] or [0])


def streams(info, kind):
    return [s for s in info.get("streams", []) if s.get("codec_type") == kind]


def keyframes(path, ffprobe=None):
    """Presentation times of the keyframes of the first video stream (packet scan, fast)."""
    ffprobe = ffprobe or ffprobe_for(find_ffmpeg())
    r = subprocess.run([ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "packet=pts_time,flags", "-of", "csv=p=0", path], capture_output=True, text=True)
    out = []
    for line in r.stdout.splitlines():
        parts = line.split(",")
        if len(parts) >= 2 and "K" in parts[1] and parts[0] not in ("", "N/A"):
            out.append(float(parts[0]))
    return sorted(out)


def parse_time(s):
    """'90', '1:30', '00:01:30.5' -> seconds."""
    s = str(s).strip()
    sec = 0.0
    for part in s.split(":"):
        sec = sec * 60 + float(part)
    return sec


def fps(stream):
    num, _, den = stream.get("avg_frame_rate", "0/1").partition("/")
    try:
        return float(num) / float(den or 1)
    except (ValueError, ZeroDivisionError):
        return 0.0


def quote(cmd):
    return " ".join(shlex.quote(c) for c in cmd)


def run_ffmpeg(cmd, out, total=None, dry_run=False, label=None):
    """Run ffmpeg `cmd` whose output path is `out` (last argument).

    The command writes to a hidden temp file next to `out`, which is renamed only on
    success, so an interrupted job never leaves a plausible-looking broken output.
    """
    if dry_run:
        print(quote(cmd))
        return 0
    d = os.path.dirname(os.path.abspath(out)) or "."
    os.makedirs(d, exist_ok=True)
    base, ext = os.path.splitext(os.path.basename(out))
    fd, part = tempfile.mkstemp(prefix=f".{base}.", suffix=f".part{ext}", dir=d)
    os.close(fd)
    real = [c if c != out else part for c in cmd]
    real = real[:1] + ["-hide_banner", "-nostdin", "-y", "-loglevel", "error", "-progress", "pipe:1", "-nostats"] + real[1:]
    proc = subprocess.Popen(real, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    step = 10
    try:
        for line in proc.stdout:
            if total and line.startswith("out_time_us="):
                try:
                    pct = int(line.split("=")[1]) / 1e6 / total * 100
                except ValueError:
                    continue
                while pct >= step and step < 100:
                    print(f"  {label or os.path.basename(out)}: {step}%", file=sys.stderr)
                    step += 10
        err = proc.stderr.read()
        rc = proc.wait()
    except KeyboardInterrupt:
        proc.send_signal(signal.SIGINT)
        proc.wait()
        os.path.exists(part) and os.remove(part)
        die("interrupted; partial output removed", 130)
    if rc != 0:
        os.path.exists(part) and os.remove(part)
        print(err.strip()[-2000:], file=sys.stderr)
        die(f"ffmpeg failed (exit {rc}) for {out}\ncommand: {quote(cmd)}")
    os.replace(part, out)
    return 0
