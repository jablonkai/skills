#!/usr/bin/env python3
"""BRL-CAD helper: build, inspect, render, check and export .g databases headless.

Every BRL-CAD tool this wraps exits 0 on most failures (unknown command, missing
object, overlaps found, 0 triangles written), so each subcommand reads the tool's
log and turns it into a real exit status:

    0  ok
    1  the tool failed (bad command, missing object, blank render, empty export)
    2  overlaps found (overlaps subcommand only)
    3  usage or setup error (BRL-CAD not found, timeout, bad arguments)

Stdlib only, Python 3.9+. Run with the system python3.
"""

import argparse
import glob
import json
import os
import re
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import zlib

DEFAULT_TIMEOUT = 600
GRID_SKEW = 0.9871  # keeps gqa grid rays off round-number faces

VIEWS = {
    # name: (azimuth, elevation, what the image shows)
    "front": (270, 0, "looking along +Y: X right, Z up"),
    "back": (90, 0, "looking along -Y: -X right, Z up"),
    "right": (0, 0, "looking along -X: Y right, Z up"),
    "left": (180, 0, "looking along +X: -Y right, Z up"),
    "top": (270, 90, "looking down -Z: X right, Y up"),
    "bottom": (270, -90, "looking up +Z: X right, -Y up"),
    "iso": (35, 25, "MGED default 35/25 view from the +X+Y side"),
    "iso2": (305, 25, "from the +X-Y side, front-right-top"),
}

# Text that means a command failed even though mged/converters returned 0.
FAIL_PATTERNS = [
    r"does not exist",
    r"skip(ping| member)",
    r"not found",
    r"FAILED",
    r"\bERROR\b",
    r"is not a known primitive",
    r"invalid command name",
    r"more arguments needed",
    r"\bUsage:",
]
FAIL_RE = re.compile("|".join(FAIL_PATTERNS))
KILL_CMDS = {"kill", "killall", "killtree", "killrefs"}


class SetupError(Exception):
    pass


class ToolFailure(Exception):
    """BRL-CAD ran but the request failed (missing object, unparsable output)."""


# --------------------------------------------------------------------------- tools

def find_bin():
    """Locate the BRL-CAD bin directory."""
    env = os.environ.get("BRLCAD_BIN") or os.environ.get("BRLCAD_ROOT")
    if env:
        cand = env if os.path.isfile(os.path.join(env, "mged")) else os.path.join(env, "bin")
        if os.path.isfile(os.path.join(cand, "mged")):
            return cand
        raise SetupError(f"BRLCAD_BIN/BRLCAD_ROOT={env} has no mged")

    def ver_key(path):
        m = re.search(r"(\d+)\.(\d+)\.(\d+)", path)
        return tuple(int(x) for x in m.groups()) if m else (0, 0, 0)

    apps = glob.glob("/Applications/BRL-CAD*.app/Contents/Resources/brlcad/bin")
    apps += glob.glob(os.path.expanduser("~/Applications/BRL-CAD*.app/Contents/Resources/brlcad/bin"))
    apps += glob.glob("/usr/brlcad/rel-*/bin") + glob.glob("/usr/brlcad/bin")
    apps = [a for a in apps if os.path.isfile(os.path.join(a, "mged"))]
    if apps:
        return sorted(apps, key=ver_key)[-1]
    which = shutil.which("mged")
    if which:
        return os.path.dirname(os.path.realpath(which))
    raise SetupError(
        "BRL-CAD not found. Install the official DMG from "
        "https://github.com/BRL-CAD/brlcad/releases to /Applications, "
        "or set BRLCAD_BIN to the directory containing mged.")


def tool(name):
    path = os.path.join(find_bin(), name)
    if not os.path.isfile(path):
        raise SetupError(f"{name} not found in {find_bin()}")
    return path


def run(argv, timeout, stdin_text=None, cwd=None):
    """Run a tool in its own process group; kill the whole group on timeout or Ctrl-C."""
    proc = subprocess.Popen(
        argv, stdin=subprocess.PIPE if stdin_text is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd,
        start_new_session=True, text=True, errors="replace")
    try:
        out, _ = proc.communicate(stdin_text, timeout=timeout)
    except subprocess.TimeoutExpired:
        _killpg(proc)
        raise SetupError(f"timeout after {timeout}s: {os.path.basename(argv[0])} (process group killed)")
    except KeyboardInterrupt:
        _killpg(proc)
        raise
    return proc.returncode, out


def _killpg(proc):
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    proc.wait()


def need_db(db):
    if not os.path.isfile(db):
        raise SetupError(f"database not found: {db}")
    return os.path.abspath(db)


def tcl_path(path):
    if any(c in path for c in "{}\\"):
        raise SetupError(f"path may not contain braces or backslashes: {path}")
    return "{" + path + "}"


def mged_tcl(db, tcl, timeout):
    """Run a Tcl snippet in mged via `source`, which (unlike stdin) keeps [..] substitution."""
    with tempfile.NamedTemporaryFile("w", suffix=".tcl", delete=False) as f:
        f.write(tcl)
        path = f.name
    try:
        return run([tool("mged"), "-c", db, "source", path], timeout)
    finally:
        os.unlink(path)


def emit(args, data, text):
    if getattr(args, "json", False):
        print(json.dumps(data, indent=2))
    else:
        print(text.rstrip("\n"))


# --------------------------------------------------------------------------- find

def cmd_find(args):
    b = find_bin()
    _, out = run([os.path.join(b, "mged"), "-v"], 30)
    m = re.search(r"Release (\S+)", out)
    data = {"bin": b, "version": m.group(1) if m else None,
            "man": os.path.normpath(os.path.join(b, "..", "share", "man"))}
    emit(args, data, f"BRL-CAD {data['version']}\nbin: {b}\nman: man -M {data['man']} <tool>")
    return 0


# --------------------------------------------------------------------------- build

BUILD_DRIVER = r"""
set __f [open %(script)s r]
set __n 0
set __buf ""
set __start 0
while {[gets $__f __line] >= 0} {
    incr __n
    if {$__buf eq ""} {set __start $__n}
    append __buf $__line "\n"
    if {![info complete $__buf]} continue
    set __cmd [string trim $__buf]
    set __buf ""
    if {$__cmd eq "" || [string index $__cmd 0] eq "#"} continue
    puts "@@BEGIN $__start"
    flush stdout
    if {[catch {uplevel #0 $__cmd} __m]} {
        puts "@@ERR $__start"
        puts $__m
    } else {
        puts "@@OK $__start"
        if {$__m ne ""} {puts $__m}
    }
    flush stdout
}
close $__f
if {$__buf ne ""} {puts "@@INCOMPLETE $__start"}
puts "@@END"
"""


def list_objects(db, timeout):
    _, out = mged_tcl(db, "puts [join [ls -s] \\n]\nputs [join [ls -c] \\n]\n", timeout)
    return {re.sub(r"[/\s].*$", "", line) for line in out.splitlines() if line.strip()}


def cmd_build(args):
    script = os.path.abspath(args.script)
    if not os.path.isfile(script):
        raise SetupError(f"script not found: {args.script}")
    db = os.path.abspath(args.output)
    lines = open(script, encoding="utf-8", errors="replace").read().splitlines()
    notes = []

    if os.path.exists(db) and args.fresh:
        bak = db + ".bak"
        os.replace(db, bak)
        notes.append(f"moved existing {os.path.basename(db)} to {os.path.basename(bak)}")
    elif os.path.exists(db):
        # r/comb/g on an existing combination APPEND members; warn before that happens.
        existing = list_objects(db, args.timeout)
        killed = set()
        for i, line in enumerate(lines, 1):
            tok = line.split()
            if len(tok) >= 2 and tok[0] in KILL_CMDS:
                killed.update(t for t in tok[1:] if not t.startswith("-"))
            if len(tok) >= 3 and tok[0] in ("r", "comb", "g") and tok[1] in existing and tok[1] not in killed:
                notes.append(f"line {i}: '{tok[1]}' already exists, so `{tok[0]}` APPENDS to it "
                             f"(kill it first, or rebuild with --fresh)")

    rc, out = mged_tcl(db, BUILD_DRIVER % {"script": tcl_path(script)}, args.timeout)

    results, cur = [], None
    for line in out.splitlines():
        m = re.match(r"@@(BEGIN|OK|ERR|INCOMPLETE) (\d+)$", line)
        if m:
            kind, n = m.group(1), int(m.group(2))
            if kind == "BEGIN":
                cur = {"line": n, "cmd": lines[n - 1].strip(), "status": "ok", "out": [], "done": False}
                results.append(cur)
            elif kind in ("OK", "ERR") and cur:
                cur["done"] = True
                if kind == "ERR":
                    cur["status"] = "error"
            elif kind == "INCOMPLETE":
                results.append({"line": n, "cmd": lines[n - 1].strip(), "status": "error",
                                "out": ["unbalanced braces or quotes: command never completed"]})
                cur = None
            continue
        if line == "@@END":
            cur = None
        elif cur is not None:
            cur["out"].append(line)
        elif line.strip():
            notes.append(line.strip())

    errors, warns = [], []
    for r in results:
        verb = r["cmd"].split()[0] if r["cmd"] else ""
        text = "\n".join(r["out"])
        if r["status"] == "error":
            errors.append(r)
        elif FAIL_RE.search(text):
            (warns if verb in KILL_CMDS else errors).append(r)
    if "@@END" not in out:
        crashed = [r for r in results if not r.get("done", True)]
        why = f"mged died (exit {rc}{', segfault' if rc in (-11, 139) else ''}) while running this line; " \
              "nothing after it ran. Check its arguments (malformed primitive input can crash mged)."
        if crashed:
            crashed[-1]["out"].append(why)
            if crashed[-1] not in errors:
                errors.append(crashed[-1])
        else:
            errors.append({"line": 0, "cmd": "(mged)", "out": [why] + out.splitlines()[-3:]})

    tops = []
    if os.path.exists(db):
        _, tout = mged_tcl(db, "puts [tops -n]\n", args.timeout)
        tops = tout.split()
    data = {"db": db, "commands": len(results), "errors": len(errors), "warnings": len(warns),
            "tops": tops, "notes": notes,
            "problems": [{"line": r["line"], "cmd": r["cmd"], "level": lvl,
                          "message": " | ".join(x.strip() for x in r["out"] if x.strip())}
                         for lvl, group in (("error", errors), ("warning", warns)) for r in group]}

    if args.verbose and not args.json:
        for r in results:
            print(f"{r['line']:4d} {r['status']:5s} {r['cmd']}")
            for x in r["out"]:
                print("          " + x)
    txt = [f"build {os.path.basename(db)}: {len(results)} commands, {len(errors)} errors, {len(warns)} warnings"]
    txt += [f"  note: {n}" for n in notes]
    txt += [f"  {p['level'].upper()} line {p['line']}: {p['cmd']}\n      -> {p['message']}" for p in data["problems"]]
    txt.append("tops: " + (" ".join(tops) or "(empty)"))
    emit(args, data, "\n".join(txt))
    return 1 if errors else 0


# --------------------------------------------------------------------------- tree

def cmd_tree(args):
    db = need_db(args.db)
    tcl = "puts \"title: [title]\"\nputs \"units: [units]\"\nputs \"tops: [tops -n]\"\n"
    for o in args.objects:
        tcl += f"if {{[catch {{tree {o}}} m]}} {{puts \"ERROR: $m\"}} else {{puts $m}}\n"
    _, out = mged_tcl(db, tcl, args.timeout)
    print(out.rstrip())
    return 1 if FAIL_RE.search(out) else 0


# --------------------------------------------------------------------------- bbox

def bbox(db, objects, timeout):
    """Bounding box lengths and units from mged `bb`."""
    _, out = mged_tcl(db, f"puts [bb -q {' '.join(objects)}]\n", timeout)
    dims = {}
    unit = "mm"
    for ax, val, u in re.findall(r"([XYZ]) Length: ([-\d.eE+]+) (\S+)", out):
        dims[ax] = float(val)
        unit = u
    if len(dims) != 3 or FAIL_RE.search(out):
        raise ToolFailure(f"cannot get bounding box of {' '.join(objects)}: {out.strip()[:300]}")
    return dims, unit


def auto_grid(db, objects, timeout, lower_div=200.0, skew=GRID_SKEW):
    """Grid 'upper,lower' from the bbox: upper ~ L/50, lower ~ L/lower_div (1-2-5, skewed)."""
    dims, unit = bbox(db, objects, timeout)
    big = max(dims.values()) or 1.0
    # For overlaps, scale off the round 1-2-5 values: a grid whose rays land exactly on a
    # shared face (round spacing, round coordinates) reports parts sitting flush as
    # overlapping. Volumes of a single object came out more accurate on the round grid.
    upper = round(_nice(big / 50.0) * skew, 6)
    lower = round(min(_nice(big / lower_div), _nice(big / 50.0)) * skew, 6)
    return f"{upper:g}{unit},{lower:g}{unit}"


def _nice(x):
    import math
    e = math.floor(math.log10(x))
    for m in (1, 2, 5, 10):
        if m * 10 ** e >= x * 0.999:
            return round(m * 10 ** e, 10)
    return x


# --------------------------------------------------------------------------- render

def png_coverage(path):
    """Fraction of pixels differing from the corner (background) pixel."""
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    i, idat = 8, b""
    w = h = ct = bd = 0
    while i < len(data):
        n, = struct.unpack(">I", data[i:i + 4])
        t = data[i + 4:i + 8]
        c = data[i + 8:i + 8 + n]
        i += 12 + n
        if t == b"IHDR":
            w, h, bd, ct = struct.unpack(">IIBB", c[:10])
        elif t == b"IDAT":
            idat += c
    if bd != 8 or ct not in (2, 6):
        return w, h, None
    bpp = 3 if ct == 2 else 4
    raw = zlib.decompress(idat)
    stride = w * bpp
    prev = bytearray(stride)
    rows = []
    o = 0
    for _ in range(h):
        f = raw[o]
        o += 1
        line = bytearray(raw[o:o + stride])
        o += stride
        if f == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x - bpp]) & 255
        elif f == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 255
        elif f == 3:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 255
        elif f == 4:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        rows.append(bytes(line))
        prev = line
    bg = rows[0][:3]
    fg = sum(1 for row in rows for x in range(0, stride, bpp) if row[x:x + 3] != bg)
    return w, h, fg / float(w * h)


def cmd_render(args):
    db = need_db(args.db)
    os.makedirs(args.output, exist_ok=True)
    views = []
    for v in args.views.split(","):
        v = v.strip()
        if v in VIEWS:
            views.append((v, VIEWS[v][0], VIEWS[v][1]))
        elif re.match(r"^-?\d+(\.\d+)?/-?\d+(\.\d+)?$", v):
            az, el = (float(x) for x in v.split("/"))
            views.append((f"az{az:g}_el{el:g}", az, el))
        else:
            raise SetupError(f"unknown view '{v}' (use {', '.join(VIEWS)} or AZ/EL like 30/20)")
    prefix = args.prefix if args.prefix is not None else "_".join(o.replace("/", "_") for o in args.objects)
    size = ["-w", str(args.width), "-n", str(args.height)] if args.width else ["-s", str(args.size)]
    bg = ["-C", args.bg] if args.bg else ["-W"]
    results, failed = [], 0
    for name, az, el in views:
        out_png = os.path.join(args.output, f"{prefix}_{name}.png" if prefix else f"{name}.png")
        if os.path.exists(out_png):
            os.unlink(out_png)
        argv = [tool("rt")] + size + bg + ["-a", f"{az:g}", "-e", f"{el:g}"]
        if args.perspective:
            argv += ["-p", str(args.perspective)]
        argv += sum((["-c", c] for c in args.set), []) + list(args.rt_arg) + ["-o", out_png, db] + args.objects
        rc, out = run(argv, args.timeout)
        r = {"view": name, "az": az, "el": el, "png": out_png, "ok": True,
             "overlap_reports": len(re.findall(r"^OVERLAP1:", out, re.M))}
        if rc != 0 or "No primitives remaining" in out or not os.path.isfile(out_png):
            r.update(ok=False, error=_tail(out))
        else:
            w, h, cov = png_coverage(out_png)
            r.update(width=w, height=h, coverage=None if cov is None else round(cov, 4))
            if cov is not None and cov < args.min_coverage:
                r.update(ok=False, error=f"render looks blank: {cov:.2%} of pixels differ from the background")
        failed += not r["ok"]
        results.append(r)
    txt = []
    for r in results:
        if r["ok"]:
            cov = "" if r.get("coverage") is None else f", object covers {r['coverage']:.1%}"
            txt.append(f"ok    {r['view']:<8} az {r['az']:g} el {r['el']:g} -> {r['png']} "
                       f"({r['width']}x{r['height']}{cov})")
        else:
            txt.append(f"FAIL  {r['view']:<8} {r['error']}")
    ov = max((r["overlap_reports"] for r in results), default=0)
    if ov:
        txt.append(f"warning: rt reported {ov} overlap rays; run `brl.py overlaps` before trusting volumes or exports")
    emit(args, {"views": results, "failed": failed}, "\n".join(txt))
    return 1 if failed else 0


def _tail(out, n=4):
    lines = [x for x in out.splitlines() if x.strip() and "Release" not in x and "Compilation" not in x
             and not x.startswith("    @")]
    return " | ".join(lines[-n:])


# --------------------------------------------------------------------------- overlaps

OVL_RE = re.compile(r"^(/\S+) (/\S+) count:(\d+) dist:([-\d.eE+]+)(\S*) @ \(([^)]*)\)")


def cmd_overlaps(args):
    db = need_db(args.db)
    grid = args.grid or auto_grid(db, args.objects, args.timeout)
    argv = [tool("gqa"), "-Ao", "-g", grid]
    if args.tol:
        argv += ["-t", args.tol]
    rc, out = run(argv + [db] + args.objects, args.timeout)
    if FAIL_RE.search(out) and "Overlaps" not in out:
        emit(args, {"ok": False, "error": _tail(out)}, f"gqa failed: {_tail(out)}")
        return 1
    pairs = []
    for line in out.splitlines():
        m = OVL_RE.match(line.strip())
        if m:
            pairs.append({"a": m.group(1), "b": m.group(2), "count": int(m.group(3)),
                          "dist": float(m.group(4)), "units": m.group(5) or None,
                          "at": [float(x) for x in m.group(6).split()]})
    if not pairs and "No Overlaps" not in out:
        emit(args, {"ok": False, "error": _tail(out)}, f"could not parse gqa output: {_tail(out)}")
        return 1
    data = {"grid": grid, "overlaps": pairs}
    if pairs:
        txt = [f"{len(pairs)} overlapping pair(s) (grid {grid}):"]
        txt += [f"  {p['a']}  x  {p['b']}  rays:{p['count']}  longest overlap along a ray:{p['dist']:g}{p['units'] or ''}"
                f"  first at ({' '.join(f'{v:g}' for v in p['at'])})" for p in pairs]
    else:
        txt = [f"No overlaps (grid {grid})"]
    emit(args, data, "\n".join(txt))
    return 2 if pairs else 0


# --------------------------------------------------------------------------- mass

def _parse_section(out, title):
    """gqa prints `Volume:` / `Weight:` followed by tab-indented `name value units` lines."""
    vals, units, inside = {}, None, False
    for line in out.splitlines():
        if line.strip() == f"{title}:":
            inside, vals = True, {}
            continue
        if inside:
            m = re.match(r"^\t\s*(\S+) ([-\d.eE+]+) (.+)$", line)
            if m:
                vals[m.group(1)] = float(m.group(2))
                units = m.group(3).strip()
            else:
                inside = False
    total = re.findall(rf"Average total {title.lower()}: ([-\d.eE+]+)", out)
    return vals, (float(total[-1]) if total else None), units


def cmd_mass(args):
    db = need_db(args.db)
    # One gqa run per object, each on a grid from its own bbox: listing several objects in
    # one run put a plate on the combined grid and read it 1% high. A tiny -V/-W makes
    # gqa refine to the lower grid limit; its default tolerance stopped early, 4% off.
    vols, wts, grids, warn = {}, {}, {}, False
    vu = wu = None
    for obj in args.objects:
        grid = args.grid or auto_grid(db, [obj], args.timeout, lower_div=1000.0, skew=1.0)
        argv = [tool("gqa"), "-A" + ("vw" if args.density else "v"), "-g", grid,
                "-u", args.units, "-V", "1e-6", "-W", "1e-6"]
        if args.density:
            argv += ["-f", os.path.abspath(args.density)]
        rc, out = run(argv + [db, obj], args.timeout)
        if FAIL_RE.search(out) or "density information" in out:
            emit(args, {"ok": False, "object": obj, "error": _tail(out)}, f"gqa failed on {obj}: {_tail(out)}")
            return 1
        v, vt, vu = _parse_section(out, "Volume")
        if vt is None:
            emit(args, {"ok": False, "object": obj, "error": _tail(out)}, f"could not parse gqa output: {_tail(out)}")
            return 1
        vols[obj], grids[obj] = vt, grid
        if args.density:
            w, wt, wu = _parse_section(out, "Weight")
            wts[obj] = wt
        warn = warn or "overlap" in out.lower()
    data = {"grid": grids, "volume": vols, "volume_total": sum(vols.values()), "volume_units": vu}
    txt = ["Volume:"] + [f"  {k}: {v:g} {vu}   (grid {grids[k]})" for k, v in vols.items()]
    if len(vols) > 1:
        txt.append(f"  total: {data['volume_total']:g} {vu}")
    if args.density:
        data.update(weight=wts, weight_total=sum(wts.values()), weight_units=wu)
        txt += ["Weight:"] + [f"  {k}: {v:g} {wu}" for k, v in wts.items()]
        if len(wts) > 1:
            txt.append(f"  total: {data['weight_total']:g} {wu}")
    if warn:
        data["warning"] = "overlaps present: volumes and weights are not trustworthy until they are fixed"
        txt.append("WARNING: " + data["warning"])
    emit(args, data, "\n".join(txt))
    return 0


# --------------------------------------------------------------------------- export

def stl_stats(path):
    data = open(path, "rb").read()
    tris = []
    is_ascii = data[:5].lower() == b"solid" and b"facet" in data[:1000]
    if is_ascii:
        verts = [tuple(float(x) for x in m.split())
                 for m in re.findall(rb"vertex\s+(\S+\s+\S+\s+\S+)", data)]
        tris = [verts[i:i + 3] for i in range(0, len(verts) - 2, 3)]
    else:
        n, = struct.unpack("<I", data[80:84])
        for k in range(n):
            o = 84 + 50 * k + 12
            v = struct.unpack("<9f", data[o:o + 36])
            tris.append([v[0:3], v[3:6], v[6:9]])
    if not tris:
        return {"triangles": 0}
    xs = [p[0] for t in tris for p in t]
    ys = [p[1] for t in tris for p in t]
    zs = [p[2] for t in tris for p in t]
    edges = {}
    for t in tris:
        key = [tuple(round(c, 4) for c in p) for p in t]
        for a, b in ((0, 1), (1, 2), (2, 0)):
            e = tuple(sorted((key[a], key[b])))
            edges[e] = edges.get(e, 0) + 1
    boundary = sum(1 for c in edges.values() if c == 1)
    nonmanifold = sum(1 for c in edges.values() if c > 2)
    return {"triangles": len(tris), "format": "ascii" if is_ascii else "binary",
            "bbox_min": [min(xs), min(ys), min(zs)], "bbox_max": [max(xs), max(ys), max(zs)],
            "size": [max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)],
            "boundary_edges": boundary, "nonmanifold_edges": nonmanifold,
            "watertight": boundary == 0 and nonmanifold == 0}


def cmd_export(args):
    db = need_db(args.db)
    fmt = args.format or ("stl" if args.per_region else os.path.splitext(args.output)[1].lstrip(".").lower())
    fmt = {"stp": "step"}.get(fmt, fmt)
    if fmt not in ("stl", "obj", "step"):
        raise SetupError("format must be stl, obj or step (or give -o with that extension)")
    conv = {"stl": "g-stl", "obj": "g-obj", "step": "g-step"}[fmt]
    argv = [tool(conv)]
    if fmt == "stl" and args.binary:
        argv.append("-b")
    if fmt in ("stl", "obj"):
        for flag, val in (("-a", args.abs_tol), ("-r", args.rel_tol), ("-n", args.norm_tol)):
            if val is not None:
                argv += [flag, str(val)]
    per_dir = None
    if args.per_region:
        if fmt != "stl":
            raise SetupError("--per-region is only supported for STL (g-stl -m)")
        per_dir = os.path.abspath(args.output)
        os.makedirs(per_dir, exist_ok=True)
        argv += ["-m", per_dir]
    else:
        out_path = os.path.abspath(args.output)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        if os.path.exists(out_path):
            os.unlink(out_path)
        argv += ["-o", out_path]
    tmpdir = None
    src_db, objects = db, args.objects
    if args.merge and args.per_region:
        raise SetupError("--merge and --per-region are mutually exclusive")
    if args.merge or (fmt == "step" and not args.csg_step):
        # Evaluate the CSG into one BoT inside a scratch copy and export that:
        # --merge gives a single shell instead of one shell per touching region, and
        # g-step 7.44 segfaults on any boolean subtraction (a `brep` conversion gives
        # wrong geometry), so STEP always goes this way unless --csg-step.
        tmpdir = tempfile.mkdtemp(prefix="brl-facet-")
        src_db = os.path.join(tmpdir, "facet.g")
        shutil.copyfile(db, src_db)
        tol = args.abs_tol if args.abs_tol is not None else 0.05
        _, fout = mged_tcl(src_db, f"tol abs {tol}\nif {{[catch {{facetize __merged.bot {' '.join(args.objects)}}} m]}} "
                                   f"{{puts \"@@ERR $m\"}}\n", args.timeout)
        if "@@ERR" in fout or FAIL_RE.search(fout):
            shutil.rmtree(tmpdir, ignore_errors=True)
            emit(args, {"ok": False, "error": _tail(fout)}, f"FAIL: facetize failed: {_tail(fout)}")
            return 1
        objects = ["__merged.bot"]
    try:
        rc, out = run(argv + [src_db] + objects, args.timeout)
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)
    problems = []
    if rc != 0:
        problems.append(f"{conv} exited {rc}" + (" (crashed)" if rc < 0 else ""))
    if FAIL_RE.search(out):
        problems.append(_tail(out))
    if re.search(r"^0 triangles written", out, re.M):
        problems.append("0 triangles written")
    files = sorted(glob.glob(os.path.join(per_dir, "*.stl"))) if per_dir else [os.path.abspath(args.output)]
    data = {"format": fmt, "files": []}
    for f in files:
        info = {"path": f, "bytes": os.path.getsize(f) if os.path.exists(f) else 0}
        if info["bytes"] == 0:
            problems.append(f"{f}: missing or empty")
        elif fmt == "stl":
            info.update(stl_stats(f))
            if info["triangles"] == 0:
                problems.append(f"{f}: no triangles")
        elif fmt == "obj":
            txt = open(f, errors="replace").read()
            info.update(vertices=len(re.findall(r"^v ", txt, re.M)), faces=len(re.findall(r"^f ", txt, re.M)))
            if info["faces"] == 0:
                problems.append(f"{f}: no faces")
        else:
            txt = open(f, errors="replace").read()
            if "ISO-10303-21" not in txt[:200]:
                problems.append(f"{f}: not a STEP file")
            elif "END-ISO-10303-21;" not in txt[-200:]:
                problems.append(f"{f}: truncated STEP (converter died mid-write)")
            info["faces"] = txt.count("ADVANCED_FACE")
        data["files"].append(info)
    data["problems"] = problems
    txt = []
    for i in data["files"]:
        line = f"{i['path']} ({i['bytes']} bytes"
        if "triangles" in i and i["triangles"]:
            s = i["size"]
            line += (f", {i['triangles']} triangles, {i['format']}, size {s[0]:.3f} x {s[1]:.3f} x {s[2]:.3f} mm, "
                     f"{'watertight' if i['watertight'] else 'NOT watertight: %d open / %d non-manifold edges' % (i['boundary_edges'], i['nonmanifold_edges'])}")
        if "vertices" in i:
            line += f", {i['vertices']} vertices, {i['faces']} faces"
        elif "faces" in i:
            line += f", {i['faces']} faces" + ("" if args.csg_step else ", facetized")
        if args.merge:
            line += ", merged into one shell"
        txt.append(line + ")")
    txt += [f"FAIL: {p}" for p in problems]
    emit(args, data, "\n".join(txt))
    return 1 if problems else 0


# --------------------------------------------------------------------------- main

def main(argv=None):
    p = argparse.ArgumentParser(prog="brl.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                   help=f"seconds per BRL-CAD process before its process group is killed (default {DEFAULT_TIMEOUT})")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("find", help="locate BRL-CAD and print its version")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_find)

    s = sub.add_parser("build", help="run an mged command script into a .g, reporting errors by line")
    s.add_argument("script")
    s.add_argument("-o", "--output", required=True, help="target .g database (created if missing)")
    s.add_argument("--fresh", action="store_true", help="move an existing .g to .g.bak and build from empty")
    s.add_argument("-v", "--verbose", action="store_true", help="print every command with its output")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_build)

    s = sub.add_parser("tree", help="title, units, top-level objects and the tree of OBJECTS")
    s.add_argument("db")
    s.add_argument("objects", nargs="*")
    s.set_defaults(func=cmd_tree)

    s = sub.add_parser("render", help="raytrace PNG views with rt")
    s.add_argument("db")
    s.add_argument("objects", nargs="+")
    s.add_argument("-o", "--output", default=".", help="output directory")
    s.add_argument("--views", default="front,right,top,iso",
                   help=f"comma list of {', '.join(VIEWS)} or AZ/EL pairs (default front,right,top,iso)")
    s.add_argument("-s", "--size", type=int, default=512)
    s.add_argument("--width", type=int)
    s.add_argument("--height", type=int)
    s.add_argument("--bg", help="background R/G/B (default white)")
    s.add_argument("--perspective", type=float, help="perspective field of view in degrees")
    s.add_argument("--prefix", help="file name prefix (default: object names; '' gives front.png, top.png, ...)")
    s.add_argument("--set", action="append", default=[], help="extra rt -c command, e.g. 'set ambient=0.6'")
    s.add_argument("--rt-arg", action="append", default=[], help="extra raw rt argument (repeatable)")
    s.add_argument("--min-coverage", type=float, default=0.005, help="fail below this object pixel fraction")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_render)

    s = sub.add_parser("overlaps", help="gqa overlap check; exit 2 when overlaps exist")
    s.add_argument("db")
    s.add_argument("objects", nargs="+")
    s.add_argument("-g", "--grid", help="gqa grid 'upper,lower' e.g. 1mm,0.25mm (default: from bbox)")
    s.add_argument("-t", "--tol", help="ignore overlaps thinner than this, e.g. 0.01mm")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_overlaps)

    s = sub.add_parser("mass", help="gqa volume, and weight when a density file is given")
    s.add_argument("db")
    s.add_argument("objects", nargs="+")
    s.add_argument("--density", help="density file: 'id g/cm3 name' per line; id = region material_id")
    s.add_argument("-g", "--grid", help="gqa grid 'upper,lower' (default: L/50,L/1000 from the bbox)")
    s.add_argument("-u", "--units", default="mm,cu mm,grams", help="gqa -u 'length,volume,weight'")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_mass)

    s = sub.add_parser("export", help="g-stl / g-obj / g-step with output checks")
    s.add_argument("db")
    s.add_argument("objects", nargs="+")
    s.add_argument("-o", "--output", required=True, help="output file (or directory with --per-region)")
    s.add_argument("-f", "--format", choices=["stl", "obj", "step"], help="default: from -o extension")
    s.add_argument("-b", "--binary", action="store_true", help="binary STL")
    s.add_argument("--per-region", action="store_true", help="one STL per region into the -o directory")
    s.add_argument("--merge", action="store_true",
                   help="union all regions into one shell (facetize) before export; use for 3D printing")
    s.add_argument("--abs-tol", type=float, help="tessellation absolute tolerance in mm (default 0.05 with --merge/STEP)")
    s.add_argument("--rel-tol", type=float, help="tessellation relative tolerance (0-1)")
    s.add_argument("--norm-tol", type=float, help="tessellation normal tolerance (degrees)")
    s.add_argument("--csg-step", action="store_true",
                   help="STEP straight from CSG (exact surfaces; crashes on any subtraction in 7.44)")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_export)

    args = p.parse_args(argv)
    try:
        return args.func(args)
    except ToolFailure as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1
    except SetupError as e:
        print(f"error: {e}", file=sys.stderr)
        return 3
    except KeyboardInterrupt:
        print("interrupted; BRL-CAD process killed", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
