"""Shared helpers for the materialcraft skill scripts (Python 3.9+, standard library only)."""
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import zlib

CANDIDATES = [
    os.path.expanduser("~/.local/bin/materialcraft-cli"),
    "/Applications/MaterialCraft.app/Contents/MacOS/materialcraft-cli",
]

USAGES = ["Base color", "Normal", "Roughness", "Metallic", "Height", "Ambient occlusion",
          "Emissive", "Opacity", "Specular", "Any"]


class McError(Exception):
    pass


def cli():
    """The materialcraft-cli to use: $MATERIALCRAFT_CLI, then PATH, then known install spots."""
    env = os.environ.get("MATERIALCRAFT_CLI")
    if env:
        return env
    found = shutil.which("materialcraft-cli")
    if found:
        return found
    for c in CANDIDATES:
        if os.access(c, os.X_OK):
            return c
    raise McError("materialcraft-cli not found; set MATERIALCRAFT_CLI or install it to ~/.local/bin")


def run(args, timeout=900):
    """Run materialcraft-cli ARGS; return stdout. Raise McError (with the CLI's message) on failure."""
    p = subprocess.run([cli()] + list(args), capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        msg = [l for l in (p.stderr or "").strip().splitlines() if l.strip()]
        detail = ""
        try:  # a failed batch prints its JSON (with `failed`) on stdout
            j = json.loads(p.stdout)
            if isinstance(j, dict) and j.get("failed"):
                f = j["failed"]
                detail = "step %s `%s`: %s" % (f.get("index"), f.get("id"), f.get("error"))
        except ValueError:
            pass
        raise McError(detail or (msg[0] if msg else "materialcraft-cli %s failed (%d)" % (args[0], p.returncode)))
    return p.stdout


def run_json(args, timeout=900):
    out = run(args, timeout)
    text = "\n".join(l for l in out.splitlines() if not l.startswith("saved "))
    return json.loads(text) if text.strip() else None


def command(inp, cid, params=None, save=None):
    args = ["run", inp, cid, json.dumps(params or {})]
    if save:
        args += ["-o", save]
    return run_json(args)


def info(path):
    return run_json(["info", path])


def graph_of(path, graph=None):
    """The full graph record (nodes, connections, exposed, presets, size) of graph index GRAPH."""
    if graph is None:
        return info(path)["graph"]
    return command(path, "session.inspect", {"graph": graph})["graph"]


def version():
    return run(["--version"]).strip()


# ---- registries ---------------------------------------------------------------

_CMDS = None
_NODES = None


def commands():
    """{id: {"label", "params" (signature text), "keys"}} from `materialcraft-cli commands`."""
    global _CMDS
    if _CMDS is None:
        _CMDS = {}
        for c in run_json(["commands"]):
            sig = c.get("params") or "{}"
            _CMDS[c["id"]] = {"label": c.get("label", ""), "params": sig, "keys": _sig_keys(_first_braces(sig))}
    return _CMDS


def nodes():
    """{def id: node definition} from `materialcraft-cli nodes`."""
    global _NODES
    if _NODES is None:
        d = run_json(["nodes"])
        d = d if isinstance(d, list) else d.get("nodes", [])
        _NODES = {n["id"]: n for n in d}
    return _NODES


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
    """Top-level keys of a signature such as `{def (see …), at? [x, y], params? {id: value}}`."""
    inner = sig.strip()[1:-1] if sig.strip().startswith("{") else sig
    keys, depth, start = set(), 0, 0
    parts = []
    for i, ch in enumerate(inner):
        if ch in "{[(":
            depth += 1
        elif ch in "}])":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append(inner[start:i])
            start = i + 1
    parts.append(inner[start:])
    for p in parts:
        m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)", p)
        if m:
            keys.add(m.group(1))
    return keys


def check_step(cid, params):
    """Problems with one command step: an unknown id, or keys the command would silently ignore."""
    reg = commands()
    if cid not in reg:
        close = [k for k in reg if k.split(".")[0] == cid.split(".")[0]][:8]
        return ["unknown command `%s`%s" % (cid, " (same group: %s)" % ", ".join(close) if close else "")]
    keys = reg[cid]["keys"]
    bad = [k for k in (params or {}) if k not in keys]
    if bad and keys:
        return ["`%s` ignores %s silently; it takes %s" % (cid, ", ".join(bad), reg[cid]["params"][:300])]
    return []


def typed(value):
    """A value for graph.exposed.add `default`: "#rrggbb" becomes a typed colour (the command rejects
    hex). Hex is sRGB and typed colours are linear, so convert the way the engine does for
    graph.exposed.set / --set "#rrggbb"."""
    if isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?", value):
        h = value[1:]
        rgba = [int(h[i:i + 2], 16) / 255 for i in range(0, len(h), 2)]
        rgba[:3] = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgba[:3]]
        if len(rgba) == 3:
            rgba.append(1.0)
        return {"t": "color", "v": [round(c, 4) for c in rgba]}
    if isinstance(value, bool):
        return {"t": "bool", "v": value}
    return value


def usage_index(u):
    if isinstance(u, int):
        return u
    for i, name in enumerate(USAGES):
        if name.lower().replace(" ", "") == str(u).lower().replace(" ", "").replace("_", ""):
            return i
    alias = {"basecolor": 0, "albedo": 0, "ao": 5, "ambientocclusion": 5, "emission": 6}
    k = str(u).lower().replace(" ", "").replace("_", "")
    if k in alias:
        return alias[k]
    raise McError("unknown output usage `%s`; one of %s" % (u, ", ".join(USAGES)))


def outputs(graph):
    """[{node, identifier, usage, source, value}] for every output node of a graph record."""
    feed = {c["to"]: c["from"] for c in graph.get("connections", []) if c["toPort"] == "input"}
    res = []
    for n in graph.get("nodes", []):
        if n["def"] == "output":
            u = n["params"].get("usage", {}).get("v", 0)
            res.append({"node": n["id"], "identifier": n["params"].get("identifier", {}).get("v", "output"),
                        "usage": USAGES[u] if isinstance(u, int) and u < len(USAGES) else u,
                        "source": feed.get(n["id"]),
                        # a value output (fed by a value_processor, 0.4.0 atomics) cooks to a number: no image
                        "value": (n.get("cooked") or {}).get("value") is not None})
    return res


def cook_errors(cook):
    return [{"node": n["id"], "def": n.get("def"), "error": n["error"]}
            for n in (cook or {}).get("nodes", []) if n.get("error")]


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
            return _tiff_header(path, "<" if head[:2] == b"II" else ">")
    if path.lower().endswith(".tga"):
        idlen, cmap, itype = head[0], head[1], head[2]
        w, h = struct.unpack("<HH", head[12:16])
        bpp = head[16]
        return {"format": "tga", "width": w, "height": h, "bit_depth": 8, "channels": bpp // 8}
    raise McError("unrecognised image: %s" % path)


def _tiff_header(path, e):
    """Width, height, samples and bits per sample from the first IFD (uncompressed writers put it last)."""
    with open(path, "rb") as f:
        f.seek(4)
        f.seek(struct.unpack(e + "I", f.read(4))[0])
        n = struct.unpack(e + "H", f.read(2))[0]
        entries = [struct.unpack(e + "HHI4s", f.read(12)) for _ in range(n)]
        tags = {}
        for tag, typ, cnt, raw in entries:
            if typ == 3 and cnt <= 2:
                tags[tag] = struct.unpack(e + "H", raw[:2])[0]
            elif typ == 3:  # a list of shorts stored elsewhere (BitsPerSample per channel)
                f.seek(struct.unpack(e + "I", raw)[0])
                tags[tag] = struct.unpack(e + "H", f.read(2))[0]
            else:
                tags[tag] = struct.unpack(e + "I", raw)[0]
    return {"format": "tif", "width": tags.get(256), "height": tags.get(257),
            "channels": tags.get(277, 1), "bit_depth": tags.get(258)}


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
    raise McError("no JPEG frame header: %s" % path)


def _exr_header(path):
    with open(path, "rb") as f:
        data = f.read(65536)
    i, chans, dw, depths = 8, 0, None, set()
    while i < len(data) and data[i] != 0:
        name_end = data.index(b"\x00", i)
        name = data[i:name_end].decode()
        type_end = data.index(b"\x00", name_end + 1)
        size = struct.unpack("<I", data[type_end + 1:type_end + 5])[0]
        val = data[type_end + 5:type_end + 5 + size]
        if name == "channels":
            j = 0
            while j < len(val) and val[j] != 0:
                j = val.index(b"\x00", j) + 1
                depths.add({0: 32, 1: 16, 2: 32}.get(struct.unpack("<i", val[j:j + 4])[0]))
                j += 16  # pixel type, pLinear+reserved, x/y sampling
                chans += 1
        if name == "dataWindow":
            x0, y0, x1, y1 = struct.unpack("<iiii", val)
            dw = (x1 - x0 + 1, y1 - y0 + 1)
        i = type_end + 5 + size
    return {"format": "exr", "width": dw[0] if dw else None, "height": dw[1] if dw else None,
            "channels": chans or None, "bit_depth": depths.pop() if len(depths) == 1 else None}


def png_pixels(path, max_side=256):
    """Decode a non-interlaced 8/16-bit PNG; return (w, h, channels, rows) subsampled to about max_side."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise McError("not a PNG: %s" % path)
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
        raise McError("interlaced or palette PNG not supported: %s" % path)
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


def write_png(path, rows, channels):
    """Write 8-bit rows (lists of pixel tuples) as a PNG."""
    ct = {1: 0, 2: 4, 3: 2, 4: 6}[channels]
    h, w = len(rows), len(rows[0])
    raw = b"".join(b"\x00" + bytes(v for p in r for v in p) for r in rows)

    def chunk(t, body):
        return struct.pack(">I", len(body)) + t + body + struct.pack(">I", zlib.crc32(t + body) & 0xFFFFFFFF)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, ct, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def tile_png(src, dst, n):
    """An n x n repeat of a PNG (the CLI's `render --view 2d --tiling` does not repeat in 0.4.0)."""
    w, h, ch, rows = png_pixels(src, max_side=1 << 16)
    write_png(dst, [r * n for r in rows] * n, ch)
    return {"width": w * n, "height": h * n}


def png_stats(path):
    """Per-channel mean and stddev on a subsample, plus the share of distinct colours."""
    w, h, ch, rows = png_pixels(path)
    px = [p for r in rows for p in r]
    n = len(px)
    means = [sum(p[c] for p in px) / n for c in range(ch)]
    stds = [(sum((p[c] - means[c]) ** 2 for p in px) / n) ** 0.5 for c in range(ch)]
    return {"width": w, "height": h, "channels": ch, "mean": [round(m, 1) for m in means],
            "std": [round(s, 2) for s in stds], "distinct": len(set(px))}


def seam(path):
    """Wrap-around seam score per axis for a tile (PNG). The mean jump between the last and the first
    column (x) or row (y) is divided by what the image's own interior allows: the larger of three
    times the mean neighbour jump and the 99th percentile jump (so pattern edges such as brick gaps
    don't count). Up to 1.5 tiles (noise in a seamless tile stays below it); real seams score 4+."""
    w, h, ch, rows = png_pixels(path, max_side=4096)
    if len(rows) != h or len(rows[0]) != w:
        raise McError("seam check needs a full-resolution decode (image too large)")
    gray = [[sum(p[:3]) / 3 if ch >= 3 else p[0] for p in r] for r in rows]

    def axis(lines):
        n = len(lines[0])
        jumps = sorted(abs(l[x + 1] - l[x]) for l in lines for x in range(n - 1))
        inner = sum(jumps) / len(jumps)
        limit = max(3 * inner, jumps[int(len(jumps) * 0.99)], 1.0)
        wrap = sum(abs(l[0] - l[-1]) for l in lines) / len(lines)
        return round(wrap / limit, 2)

    cols = [[gray[y][x] for y in range(h)] for x in range(w)]
    sx, sy = axis(gray), axis(cols)
    return {"x": sx, "y": sy, "tiles": sx <= 1.5 and sy <= 1.5}


# ---- misc --------------------------------------------------------------------

def refuse_overwrite(path, overwrite, what="output"):
    if os.path.exists(path) and not overwrite:
        if os.path.isdir(path) and not os.listdir(path):
            return
        raise McError("%s %s exists; pass --overwrite or pick a new path" % (what, path))


def sbs_path(path):
    """The path the CLI really writes: `.sbs` and `.mcraft` (a zip holding package.sbs, back since 0.3.0)
    are kept, any other save path gets `.sbs` appended."""
    return path if path.lower().endswith((".sbs", ".mcraft")) else path + ".sbs"


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
    except McError as e:
        emit({"ok": False, "error": str(e)}, ok=False)
    except subprocess.TimeoutExpired as e:
        emit({"ok": False, "error": "timed out: %s" % e}, ok=False)
