"""Shared helpers for the soundcraft skill scripts (Python 3.9+, standard library only)."""

import json
import os
import shutil
import struct
import subprocess
import sys


class ScError(Exception):
    pass


def die(msg, code=1):
    print("error: " + str(msg), file=sys.stderr)
    sys.exit(code)


def cli_path():
    """Locate soundcraft-cli: $SOUNDCRAFT_CLI, PATH, then ~/.local/bin."""
    env = os.environ.get("SOUNDCRAFT_CLI")
    if env:
        return env
    found = shutil.which("soundcraft-cli")
    if found:
        return found
    local = os.path.expanduser("~/.local/bin/soundcraft-cli")
    if os.path.exists(local):
        return local
    raise ScError("soundcraft-cli not found (set SOUNDCRAFT_CLI or put it on PATH)")


def cli(*args):
    """Run soundcraft-cli; return stdout. Raise ScError with stderr on failure."""
    proc = subprocess.run([cli_path()] + [str(a) for a in args],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          universal_newlines=True)
    if proc.returncode != 0:
        msg = (proc.stderr.strip() or proc.stdout.strip() or "exit %d" % proc.returncode)
        raise ScError(msg)
    return proc.stdout


def result_lines(out):
    """Parse `ID: {json}` lines printed by `run`/`script` into [(id, value)]."""
    results = []
    for line in out.splitlines():
        head, sep, body = line.partition(": ")
        if sep and "." in head and " " not in head:
            try:
                results.append((head, json.loads(body)))
            except ValueError:
                pass
    return results


def inspect(session):
    """Full session.inspect dict of a .scraft file."""
    out = cli("run", "--in", session, "--cmd", 'session.inspect={"detail":"full"}')
    for cid, value in result_lines(out):
        if cid == "session.inspect":
            return value
    raise ScError("no session.inspect result for " + session)


def info(path):
    """`soundcraft-cli info` of an audio file as a dict."""
    return json.loads(cli("info", path))


def find_track(doc, name):
    for t in doc.get("tracks", []):
        if t.get("name") == name or str(t.get("id")) == str(name):
            return t
    raise ScError("no track named %r (have: %s)"
                  % (name, ", ".join(t.get("name", "?") for t in doc.get("tracks", []))))


def to_samples(value, rate):
    """Seconds (number), 'm:ss.fff' / 'h:mm:ss.fff' or '<n>smp' -> samples."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(round(float(value) * rate))
    text = str(value).strip()
    if text.endswith("smp"):
        return int(text[:-3])
    if ":" in text:
        secs = 0.0
        for part in text.split(":"):
            secs = secs * 60 + float(part)
        return int(round(secs * rate))
    return int(round(float(text) * rate))


def fmt_time(samples, rate):
    secs = samples / float(rate)
    return "%d:%06.3f" % (int(secs // 60), secs % 60)


# --- minimal WAV reader for peak / RMS checks -------------------------------

def _wav_layout(path):
    with open(path, "rb") as fh:
        head = fh.read(12)
        if head[:4] not in (b"RIFF", b"RF64") or head[8:12] != b"WAVE":
            raise ScError("%s is not a WAV file" % path)
        fmt = None
        while True:
            hdr = fh.read(8)
            if len(hdr) < 8:
                break
            cid, size = hdr[:4], struct.unpack("<I", hdr[4:])[0]
            if cid == b"fmt ":
                raw = fh.read(size)
                tag, ch, rate, _, _, bits = struct.unpack("<HHIIHH", raw[:16])
                if tag == 0xFFFE and len(raw) >= 26:
                    tag = struct.unpack("<H", raw[24:26])[0]
                fmt = (tag, ch, rate, bits)
            elif cid == b"data":
                if fmt is None:
                    raise ScError("%s: data chunk before fmt" % path)
                return fmt, fh.tell(), size
            else:
                fh.seek(size + (size & 1), 1)
    raise ScError("%s: no data chunk" % path)


def wav_levels(path, start=None, end=None):
    """Peak and RMS (dBFS) of a PCM/float WAV, optionally over [start, end) seconds."""
    import math
    (tag, ch, rate, bits), offset, size = _wav_layout(path)
    width = bits // 8
    frame = width * ch
    total = size // frame
    first = 0 if start is None else max(0, int(start * rate))
    last = total if end is None else min(total, int(end * rate))
    if tag == 3 and bits == 32:
        dec = lambda b: struct.unpack("<%df" % (len(b) // 4), b)  # noqa: E731
    elif tag == 1 and bits in (16, 32):
        scale = float(1 << (bits - 1))
        code = "h" if bits == 16 else "i"
        dec = lambda b: [v / scale for v in struct.unpack("<%d%s" % (len(b) // width, code), b)]  # noqa: E731
    elif tag == 1 and bits == 24:
        def dec(b):
            return [int.from_bytes(b[i:i + 3], "little", signed=True) / 8388608.0
                    for i in range(0, len(b), 3)]
    else:
        raise ScError("%s: unsupported WAV format tag %d / %d bit" % (path, tag, bits))
    peak, sq, n = 0.0, 0.0, 0
    with open(path, "rb") as fh:
        fh.seek(offset + first * frame)
        remaining = max(0, last - first) * frame
        while remaining > 0:
            chunk = fh.read(min(remaining, frame * 65536))
            if not chunk:
                break
            remaining -= len(chunk)
            for v in dec(chunk):
                a = abs(v)
                if a > peak:
                    peak = a
                sq += v * v
                n += 1

    def db(x):
        return round(20 * math.log10(x), 2) if x > 0 else -math.inf
    return {"peak_db": db(peak), "rms_db": db(math.sqrt(sq / n)) if n else -math.inf,
            "frames": max(0, last - first), "rate": rate, "channels": ch}
