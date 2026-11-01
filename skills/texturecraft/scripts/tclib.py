"""Shared helpers for the texturecraft skill scripts (Python 3.9+, standard library only)."""
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import zlib

CANDIDATES = [
    os.path.expanduser("~/.local/bin/texturecraft-cli"),
    "/Applications/TextureCraft.app/Contents/MacOS/texturecraft-cli",
]


class TcError(Exception):
    pass


def cli():
    """The texturecraft-cli to use: $TEXTURECRAFT_CLI, then PATH, then known install spots."""
    env = os.environ.get("TEXTURECRAFT_CLI")
    if env:
        return env
    found = shutil.which("texturecraft-cli")
    if found:
        return found
    for c in CANDIDATES:
        if os.access(c, os.X_OK):
            return c
    raise TcError("texturecraft-cli not found; set TEXTURECRAFT_CLI or install it to ~/.local/bin")


def run(args, timeout=900, stderr=False):
    """Run texturecraft-cli ARGS; return stdout (plus stderr when asked). Raise TcError on failure."""
    p = subprocess.run([cli()] + list(args), capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        msg = (p.stderr or p.stdout).strip().splitlines()
        raise TcError(msg[0] if msg else "texturecraft-cli %s failed (%d)" % (args[0], p.returncode))
    return p.stdout + p.stderr if stderr else p.stdout


def run_json(args, timeout=900):
    out = run(args, timeout)
    # `run -o` / `batch` print the JSON result and then "saved X" on its own line.
    text = "\n".join(l for l in out.splitlines() if not l.startswith("saved "))
    return json.loads(text) if text.strip() else None


def command(inp, cid, params=None, save=None):
    args = ["run", inp, cid, json.dumps(params or {})]
    if save:
        args += ["-o", save]
    return run_json(args)


def info(path):
    if path.startswith("builtin:"):
        raise TcError("`info` cannot read builtin:<id>; create a project with `new` first")
    return run_json(["info", path])


def version():
    return run(["--version"]).strip()


# ---- command registry -------------------------------------------------------

_REG = None


def registry():
    """{id: {"label", "sig", "keys"}} parsed from `texturecraft-cli commands`."""
    global _REG
    if _REG is None:
        _REG = {}
        for line in run(["commands"]).splitlines():
            m = re.match(r"^(\S+)\s{2,}(.+?)\s{2,}(\{.*)$", line)
            if not m:
                m2 = re.match(r"^(\S+)\s{2,}(.+?)\s*$", line)
                if m2:
                    _REG[m2.group(1)] = {"label": m2.group(2), "sig": "{}", "keys": set()}
                continue
            cid, label, rest = m.groups()
            sig = _first_braces(rest)
            _REG[cid] = {"label": label, "sig": rest, "keys": _sig_keys(sig)}
        # "...any bake.settings parameter": the command also takes the other one's keys
        for cid, r in _REG.items():
            for other in re.findall(r"any ([a-zA-Z]+\.[a-zA-Z.]+) param", r["sig"]):
                if other in _REG:
                    r["keys"] |= _REG[other]["keys"]
    return _REG


def _first_braces(s):
    depth = 0
    for i, ch in enumerate(s):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return s[: i + 1]
    return s


def _sig_keys(sig):
    """Every word in the signature that is written like a key (`name?`, `path:`, `ts,`)."""
    return set(re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\??(?=\s*[:,}|?])", sig))


def check_step(cid, params):
    """Return a list of problems with one step: unknown id or param keys the registry does not name."""
    reg = registry()
    if cid not in reg:
        close = [k for k in reg if k.split(".")[0] == cid.split(".")[0]][:8]
        return ["unknown command `%s`%s" % (cid, " (same group: %s)" % ", ".join(close) if close else "")]
    keys = reg[cid]["keys"]
    bad = [k for k in (params or {}) if k not in keys]
    if bad and keys:
        return ["`%s` does not take %s; it takes %s" % (cid, ", ".join(bad), reg[cid]["sig"][:300])]
    return []


# ---- image headers and pixels (PNG fully, others header only) ---------------

def image_header(path):
    """{format, width, height, channels, bit_depth} for PNG, JPEG, TGA, TIFF, EXR."""
    with open(path, "rb") as f:
        head = f.read(64)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            w, h, bd, ct = struct.unpack(">IIBB", head[16:26])
            return {"format": "png", "width": w, "height": h, "bit_depth": bd,
                    "channels": {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(ct, 0)}
        if head[:4] == b"\x76\x2f\x31\x01":
            return _exr_header(path)
        if head[:2] == b"\xff\xd8":
            return _jpeg_header(path)
        if head[:4] in (b"II*\x00", b"MM\x00*"):
            return {"format": "tif", "width": None, "height": None, "channels": None, "bit_depth": None}
    if path.lower().endswith(".tga"):
        idlen, cmap, itype = head[0], head[1], head[2]
        w, h = struct.unpack("<HH", head[12:16])
        bpp = head[16]
        return {"format": "tga", "width": w, "height": h, "bit_depth": 8, "channels": bpp // 8}
    raise TcError("unrecognised image: %s" % path)


def _jpeg_header(path):
    with open(path, "rb") as f:
        data = f.read()
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return {"format": "jpg", "width": w, "height": h, "bit_depth": 8, "channels": data[i + 9]}
        seg = struct.unpack(">H", data[i + 2:i + 4])[0]
        i += 2 + seg
    raise TcError("no JPEG frame header: %s" % path)


def _exr_header(path):
    with open(path, "rb") as f:
        data = f.read(65536)
    i, chans, dw = 8, 0, None
    while i < len(data) and data[i] != 0:
        name_end = data.index(b"\x00", i)
        name = data[i:name_end].decode()
        type_end = data.index(b"\x00", name_end + 1)
        size = struct.unpack("<I", data[type_end + 1:type_end + 5])[0]
        val = data[type_end + 5:type_end + 5 + size]
        if name == "channels":
            j = 0
            while j < len(val) and val[j] != 0:
                j = val.index(b"\x00", j) + 1 + 16  # name, then type, pLinear+reserved, x/y sampling
                chans += 1
        if name == "dataWindow":
            x0, y0, x1, y1 = struct.unpack("<iiii", val)
            dw = (x1 - x0 + 1, y1 - y0 + 1)
        i = type_end + 5 + size
    return {"format": "exr", "width": dw[0] if dw else None, "height": dw[1] if dw else None,
            "channels": chans or None, "bit_depth": None}


def png_pixels(path, max_side=256):
    """Decode a non-interlaced 8/16-bit PNG; return (w, h, channels, rows) subsampled to about max_side."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise TcError("not a PNG: %s" % path)
    pos, idat, hdr = 8, [], None
    while pos < len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            hdr = struct.unpack(">IIBBBBB", body)
        elif typ == b"IDAT":
            idat.append(body)
        pos += 12 + ln
    w, h, bd, ct, _, _, interlace = hdr
    if interlace or ct == 3:
        raise TcError("interlaced or palette PNG not supported: %s" % path)
    ch = {0: 1, 2: 3, 4: 2, 6: 4}[ct]
    bpp = ch * bd // 8
    raw = zlib.decompress(b"".join(idat))
    stride = w * bpp
    step = max(1, max(w, h) // max_side)
    rows, prev = [], bytearray(stride)
    i = 0
    for y in range(h):
        ft = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        _unfilter(ft, line, prev, bpp)
        prev = line
        if y % step == 0:
            if bd == 16:
                vals = struct.unpack(">%dH" % (w * ch), bytes(line))
                vals = [v >> 8 for v in vals]
            else:
                vals = line
            rows.append([tuple(vals[x * ch:(x + 1) * ch]) for x in range(0, w, step)])
    return w, h, ch, rows


def _unfilter(ft, line, prev, bpp):
    n = len(line)
    if ft == 1:
        for x in range(bpp, n):
            line[x] = (line[x] + line[x - bpp]) & 255
    elif ft == 2:
        for x in range(n):
            line[x] = (line[x] + prev[x]) & 255
    elif ft == 3:
        for x in range(n):
            left = line[x - bpp] if x >= bpp else 0
            line[x] = (line[x] + ((left + prev[x]) >> 1)) & 255
    elif ft == 4:
        for x in range(n):
            a = line[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            p = a + b - c
            pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
            pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
            line[x] = (line[x] + pr) & 255


def png_stats(path):
    """Per-channel mean and stddev on a subsample, plus the share of distinct colours."""
    w, h, ch, rows = png_pixels(path)
    px = [p for r in rows for p in r]
    n = len(px)
    means = [sum(p[c] for p in px) / n for c in range(ch)]
    stds = [(sum((p[c] - means[c]) ** 2 for p in px) / n) ** 0.5 for c in range(ch)]
    return {"width": w, "height": h, "channels": ch, "mean": [round(m, 1) for m in means],
            "std": [round(s, 2) for s in stds], "distinct": len(set(px))}


def glb_summary(path):
    """Materials, images and texture links of a .glb, read from its JSON chunk."""
    with open(path, "rb") as f:
        head = f.read(20)
        magic, _, _, jlen, jtype = struct.unpack("<IIIII", head)
        if magic != 0x46546C67 or jtype != 0x4E4F534A:
            raise TcError("not a binary glTF: %s" % path)
        j = json.loads(f.read(jlen))
    mats = []
    for m in j.get("materials", []):
        pbr = m.get("pbrMetallicRoughness", {})
        mats.append({"name": m.get("name"),
                     "baseColorTexture": "baseColorTexture" in pbr,
                     "metallicRoughnessTexture": "metallicRoughnessTexture" in pbr,
                     "normalTexture": "normalTexture" in m,
                     "occlusionTexture": "occlusionTexture" in m})
    return {"materials": mats, "images": len(j.get("images", [])), "meshes": len(j.get("meshes", []))}


# ---- misc --------------------------------------------------------------------

def refuse_overwrite(path, overwrite, what="output"):
    if os.path.exists(path) and not overwrite:
        raise TcError("%s %s exists; pass --overwrite or pick a new path" % (what, path))


def same_file(a, b):
    try:
        return os.path.samefile(a, b)
    except OSError:
        return os.path.abspath(a) == os.path.abspath(b)


def emit(obj, ok=True):
    print(json.dumps(obj, indent=2, default=str))
    sys.exit(0 if ok else 1)


def main_guard(fn):
    try:
        fn()
    except TcError as e:
        emit({"ok": False, "error": str(e)}, ok=False)
    except subprocess.TimeoutExpired as e:
        emit({"ok": False, "error": "timed out: %s" % e}, ok=False)
