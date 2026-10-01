#!/usr/bin/env python3
"""kicad.py - KiCad 10 kicad-cli wrapper with real exit codes and English reports.

Subcommands:
  find     locate KiCad, print version, API-server switch and kipy availability
  drc      run DRC, write the JSON report, print a grouped summary
  erc      run ERC, write the JSON report, print a grouped summary
  fab      build a fabrication package (Gerbers, drill, CPL, BOM, STEP, zip) and check it
  render   3D-render the board to PNG and check the image is not blank

Exit status: 0 ok, 1 failed, 2 violations found (drc/erc), 3 setup error or timeout.

kicad-cli prints, and writes report descriptions, in the KiCad UI language. Unless
--keep-locale is given, every call runs against a temporary copy of the user's KiCad
config with the language set to English, so reports are stable and parseable.
Stdlib only; run it with the system python3.
"""
import argparse
import csv
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
import zipfile
import zlib
from collections import Counter, OrderedDict

DEFAULT_TIMEOUT = 600
NOISE_RE = re.compile(r"Fontconfig warning|regenerate the cache")

# Gerber layer sets per fab preset; inner copper layers are added from the board.
FAB_LAYERS = ["F.Cu", "B.Cu", "F.Paste", "B.Paste", "F.Silkscreen", "B.Silkscreen",
              "F.Mask", "B.Mask", "Edge.Cuts"]
REQUIRED_LAYERS = ["F.Cu", "B.Cu", "F.Mask", "B.Mask", "Edge.Cuts"]

JLC_CPL_HEADER = ["Designator", "Mid X", "Mid Y", "Layer", "Rotation"]
JLC_BOM_LABELS = ["Comment", "Designator", "Footprint", "LCSC Part #"]


class SetupError(Exception):
    pass


class ToolFailure(Exception):
    """kicad-cli ran but the request failed."""


# --------------------------------------------------------------------------- locate

def find_app():
    env = os.environ.get("KICAD_APP")
    cands = [env] if env else []
    cands += ["/Applications/KiCad/KiCad.app", os.path.expanduser("~/Applications/KiCad/KiCad.app"),
              "/Applications/KiCad.app"]
    cands += sorted(glob.glob("/Applications/KiCad*/KiCad.app"), reverse=True)
    for c in cands:
        if c and os.path.isfile(os.path.join(c, "Contents/MacOS/kicad-cli")):
            return c
    which = shutil.which("kicad-cli")
    if which:
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(which))))
    raise SetupError("KiCad not found. Install it (brew install --cask kicad, or the DMG from "
                     "https://www.kicad.org/download/macos/) or set KICAD_APP to KiCad.app.")


def cli_path():
    app = find_app()
    p = os.path.join(app, "Contents/MacOS/kicad-cli")
    return p if os.path.isfile(p) else shutil.which("kicad-cli")


def kicad_version():
    rc, out = run([cli_path(), "version"], 60, english=False)
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", out)
    if rc != 0 or not m:
        raise SetupError(f"kicad-cli version failed: {out.strip()}")
    return m.group(0)


def user_config_dir(version=None):
    version = version or kicad_version()
    base = os.environ.get("KICAD_CONFIG_HOME") or os.path.expanduser("~/Library/Preferences/kicad")
    return os.path.join(base, "%s.0" % version.split(".")[0])


# --------------------------------------------------------------------------- running

_EN_HOME = None


def english_config_home():
    """A temp KICAD_CONFIG_HOME cloned from the user's config, with language English."""
    global _EN_HOME
    if _EN_HOME:
        return _EN_HOME
    src = user_config_dir()
    if not os.path.isfile(os.path.join(src, "kicad_common.json")):
        return None  # fresh install: keep KiCad defaults rather than lose the lib tables
    home = tempfile.mkdtemp(prefix="kicad-en-")
    dst = os.path.join(home, os.path.basename(src))
    shutil.copytree(src, dst)
    p = os.path.join(dst, "kicad_common.json")
    with open(p) as f:
        cfg = json.load(f)
    cfg.setdefault("system", {})["language"] = "English"
    with open(p, "w") as f:
        json.dump(cfg, f, indent=2)
    _EN_HOME = home
    return home


def run(argv, timeout, english=True, cwd=None):
    """Run in its own process group; kill the group on timeout or Ctrl-C."""
    env = dict(os.environ)
    if english and not ARGS_KEEP_LOCALE:
        home = english_config_home()
        if home:
            env["KICAD_CONFIG_HOME"] = home
    proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, cwd=cwd, env=env,
                            start_new_session=True, text=True, errors="replace")
    try:
        out, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _killpg(proc)
        raise SetupError(f"timeout after {timeout}s: {' '.join(argv[1:3])} (process group killed)")
    except KeyboardInterrupt:
        _killpg(proc)
        raise
    out = "\n".join(l for l in out.splitlines() if not NOISE_RE.search(l))
    return proc.returncode, out


def _killpg(proc):
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    proc.wait()


def cli(args, timeout, what):
    rc, out = run([cli_path()] + args, timeout)
    bad = [l for l in out.splitlines() if re.search(r"(?i)invalid|failed|error:|not found|unknown", l)
           and not re.search(r"(?i)\bviolations?\b|unconnected", l)]
    return rc, out, bad


def need_file(path, exts):
    if not os.path.isfile(path):
        raise SetupError(f"file not found: {path}")
    if not path.endswith(exts):
        raise SetupError(f"expected {' or '.join(exts)}: {path}")
    return os.path.abspath(path)


ARGS_KEEP_LOCALE = False


# --------------------------------------------------------------------------- find

def cmd_find(args):
    app = find_app()
    ver = kicad_version()
    cfg_dir = user_config_dir(ver)
    api = None
    try:
        with open(os.path.join(cfg_dir, "kicad_common.json")) as f:
            api = json.load(f).get("api", {}).get("enable_server")
    except (OSError, ValueError):
        pass
    venv_py = os.path.expanduser("~/.venvs/kicad/bin/python")
    kipy = None
    if os.path.isfile(venv_py):
        rc, out = run([venv_py, "-c", "import kipy,importlib.metadata as m;print(m.version('kicad-python'))"],
                      60, english=False)
        kipy = out.strip() if rc == 0 else None
    sock = "/tmp/kicad/api.sock"
    info = OrderedDict([
        ("app", app), ("kicad_cli", cli_path()), ("version", ver),
        ("python", os.path.join(app, "Contents/Frameworks/Python.framework/Versions/Current/bin/python3")),
        ("config_dir", cfg_dir), ("api_server_enabled", api),
        ("api_socket", sock if os.path.exists(sock) else None),
        ("kipy_venv", venv_py if kipy else None), ("kipy_version", kipy),
    ])
    if args.json:
        print(json.dumps(info, indent=2))
    else:
        for k, v in info.items():
            print(f"{k:20} {v}")
        if not api:
            print("note: IPC API is off - enable it in KiCad > Preferences > Plugins to use kicad_ipc.py")
        if not kipy:
            print("note: kipy missing - python3 -m venv ~/.venvs/kicad && "
                  "~/.venvs/kicad/bin/pip install kicad-python")
    return 0


# --------------------------------------------------------------------------- drc / erc

def summarize(violations, top):
    groups = OrderedDict()
    for v in violations:
        key = (v.get("severity", "?"), v.get("type", "?"))
        groups.setdefault(key, []).append(v)
    order = {"error": 0, "warning": 1, "exclusion": 2}
    rows = sorted(groups.items(), key=lambda kv: (order.get(kv[0][0], 9), -len(kv[1]), kv[0][1]))
    out = []
    for (sev, typ), items in rows:
        out.append(OrderedDict([
            ("severity", sev), ("type", typ), ("count", len(items)),
            ("examples", [OrderedDict([
                ("description", v.get("description", "")),
                ("items", [OrderedDict([("item", i.get("description", "")),
                                        ("x", i.get("pos", {}).get("x")),
                                        ("y", i.get("pos", {}).get("y"))])
                           for i in v.get("items", [])])])
                for v in items[:top]]),
        ]))
    return out


def print_groups(title, groups, units):
    if not groups:
        print(f"{title}: none")
        return
    total = sum(g["count"] for g in groups)
    print(f"{title}: {total}")
    for g in groups:
        print(f"  [{g['severity']}] {g['type']} x{g['count']}")
        for ex in g["examples"]:
            print(f"      {ex['description']}")
            for it in ex["items"]:
                print(f"        - {it['item']} @ ({it['x']}, {it['y']}) {units}")


def report_path(args, src, kind):
    if args.output:
        return os.path.abspath(args.output)
    return os.path.splitext(src)[0] + f"-{kind}.json"


def cmd_drc(args):
    board = need_file(args.board, (".kicad_pcb",))
    out_json = report_path(args, board, "drc")
    cmd = ["pcb", "drc", "--format", "json", "--units", "mm", "-o", out_json]
    cmd += ["--severity-all"] if args.all else ["--severity-error", "--severity-warning"]
    if args.refill_zones:
        cmd.append("--refill-zones")
    if args.parity:
        cmd.append("--schematic-parity")
    before = _mtime(out_json)
    rc, out, _ = cli(cmd + [board], args.timeout, "drc")
    if rc not in (0, 5) or _mtime(out_json) == before:
        raise ToolFailure(f"kicad-cli pcb drc failed (exit {rc}):\n{out}")
    with open(out_json) as f:
        rep = json.load(f)
    viol = summarize(rep.get("violations", []), args.top)
    unconn = summarize(rep.get("unconnected_items", []), args.top)
    parity = summarize(rep.get("schematic_parity", []), args.top)
    n_err = sum(g["count"] for g in viol + unconn + parity if g["severity"] == "error")
    result = OrderedDict([("report", out_json), ("kicad_version", rep.get("kicad_version")),
                          ("errors", n_err), ("violations", viol),
                          ("unconnected_items", unconn), ("schematic_parity", parity)])
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"DRC {os.path.basename(board)}  (KiCad {rep.get('kicad_version')}, report: {out_json})")
        print_groups("violations", viol, "mm")
        print_groups("unconnected items", unconn, "mm")
        if args.parity:
            print_groups("schematic parity", parity, "mm")
        print(f"errors: {n_err}")
    return 2 if (n_err or (args.strict and (viol or unconn or parity))) else 0


def cmd_erc(args):
    sch = need_file(args.schematic, (".kicad_sch",))
    out_json = report_path(args, sch, "erc")
    cmd = ["sch", "erc", "--format", "json", "--units", "mm", "-o", out_json]
    cmd += ["--severity-all"] if args.all else ["--severity-error", "--severity-warning"]
    before = _mtime(out_json)
    rc, out, _ = cli(cmd + [sch], args.timeout, "erc")
    if rc not in (0, 5) or _mtime(out_json) == before:
        raise ToolFailure(f"kicad-cli sch erc failed (exit {rc}):\n{out}")
    with open(out_json) as f:
        rep = json.load(f)
    allv = []
    for sheet in rep.get("sheets", []):
        for v in sheet.get("violations", []):
            v = dict(v)
            v["description"] = f"{v.get('description', '')}  [sheet {sheet.get('path', '/')}]"
            allv.append(v)
    scale = erc_pos_scale(sch, allv, args.timeout)
    if scale != 1:  # allv shares the item dicts with rep, so scaling rep fixes both
        rep["pos_scale_applied"] = scale
        for sheet in rep.get("sheets", []):
            for v in sheet.get("violations", []):
                for i in v.get("items", []):
                    if "pos" in i:
                        i["pos"] = {k: round(c * scale, 4) for k, c in i["pos"].items()}
        with open(out_json, "w") as f:
            json.dump(rep, f, indent=2)
    viol = summarize(allv, args.top)
    n_err = sum(g["count"] for g in viol if g["severity"] == "error")
    if args.json:
        print(json.dumps(OrderedDict([("report", out_json), ("errors", n_err), ("violations", viol)]),
                         indent=2))
    else:
        print(f"ERC {os.path.basename(sch)}  (report: {out_json})")
        print_groups("violations", viol, "mm")
        print(f"errors: {n_err}")
    return 2 if (n_err or (args.strict and viol)) else 0


def erc_pos_scale(sch, violations, timeout):
    """KiCad 10.0.6 writes ERC JSON positions at 1/100 of the stated unit while the text
    report is right. Compare the first item against a text report to get the factor."""
    first = next((i["pos"] for v in violations for i in v.get("items", []) if "pos" in i), None)
    if not first or not first.get("y"):
        return 1
    fd, rpt = tempfile.mkstemp(suffix=".rpt")
    os.close(fd)
    try:
        run([cli_path(), "sch", "erc", "--format", "report", "--units", "mm", "--severity-all",
             "-o", rpt, sch], timeout)
        with open(rpt, errors="replace") as f:
            m = re.search(r"@\(\s*(-?[\d.]+) mm,\s*(-?[\d.]+) mm\)", f.read())
    finally:
        os.remove(rpt)
    if not m or float(m.group(2)) == 0:
        return 1
    ratio = float(m.group(2)) / first["y"]
    return 100 if 90 < ratio < 110 else 1


def _mtime(p):
    try:
        return os.path.getmtime(p)
    except OSError:
        return None


# --------------------------------------------------------------------------- fab

def board_copper_layers(board):
    with open(board, encoding="utf-8") as f:
        head = f.read(200000)
    m = re.search(r"\(layers\b(.*?)\n\t\)", head, re.S)
    names = re.findall(r'"((?:F|B|In\d+)\.Cu)"', m.group(1) if m else head)
    inner = sorted({n for n in names if n.startswith("In")}, key=lambda n: int(re.sub(r"\D", "", n)))
    return ["F.Cu"] + inner + ["B.Cu"]


def layer_file(files, layer):
    stem = "-" + layer.replace(".", "_") + "."
    hits = [f for f in files if stem in os.path.basename(f)]
    return hits[0] if hits else None


def gerber_has_draws(path):
    with open(path, errors="replace") as f:
        text = f.read()
    return bool(re.search(r"D0?[13]\*", text))


def detect_lcsc_field(sch):
    with open(sch, encoding="utf-8", errors="replace") as f:
        text = f.read()
    props = Counter(re.findall(r'\(property\s+"([^"]+)"', text))
    for name, _ in props.most_common():
        if re.search(r"(?i)lcsc|jlc", name):
            return name
    return None


def find_schematic(board):
    sch = os.path.splitext(board)[0] + ".kicad_sch"
    return sch if os.path.isfile(sch) else None


def cmd_fab(args):
    board = need_file(args.board, (".kicad_pcb",))
    name = os.path.splitext(os.path.basename(board))[0]
    out = os.path.abspath(args.output)
    gdir = os.path.join(out, "gerbers")
    if os.path.isdir(gdir):
        shutil.rmtree(gdir)
    os.makedirs(gdir)
    jlc = args.preset == "jlcpcb"
    copper = board_copper_layers(board)
    layers = copper + [l for l in FAB_LAYERS if not l.endswith(".Cu")]
    problems, made = [], OrderedDict()
    warnings = board_sanity(board)

    # Gerbers - explicit layer list; kicad-cli plots every layer without one.
    g = ["pcb", "export", "gerbers", "-o", gdir + "/", "-l", ",".join(layers), "--check-zones"]
    if jlc:
        g += ["--no-x2", "--no-netlist"]
    rc, log, bad = cli(g + [board], args.timeout, "gerbers")
    if rc != 0 or bad:
        raise ToolFailure(f"gerber export failed (exit {rc}):\n{log}")
    if jlc:  # JLCPCB's guide turns the Gerber job file off
        for f in glob.glob(os.path.join(gdir, "*.gbrjob")):
            os.remove(f)
    files = sorted(glob.glob(os.path.join(gdir, "*")))
    for l in layers:
        f = layer_file(files, l)
        if not f and l in REQUIRED_LAYERS + copper:
            problems.append(f"missing Gerber for {l}")
        made[l] = f
    edge = made.get("Edge.Cuts")
    if edge and not gerber_has_draws(edge):
        problems.append("Edge.Cuts Gerber has no outline - draw the board outline on Edge.Cuts")

    # Drill: Excellon, mm, absolute origin, separate PTH/NPTH files (accepted everywhere).
    d = ["pcb", "export", "drill", "-o", gdir + "/", "--format", "excellon", "--excellon-units", "mm",
         "--excellon-zeros-format", "decimal", "--drill-origin", "absolute", "--excellon-separate-th",
         "--generate-map", "--map-format", "gerberx2"]
    rc, log, bad = cli(d + [board], args.timeout, "drill")
    if rc != 0:
        raise ToolFailure(f"drill export failed (exit {rc}):\n{log}")
    drills = sorted(glob.glob(os.path.join(gdir, "*.drl")))
    if not drills:
        problems.append("no drill file written")

    # Pick-and-place.
    cpl_path = None
    if not args.no_cpl:
        raw = os.path.join(out, f"{name}-pos-kicad.csv")
        p = ["pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both", "-o", raw,
             "--exclude-dnp"]
        if not args.include_tht:
            p.append("--smd-only")
        rc, log, _ = cli(p + [board], args.timeout, "pos")
        if rc != 0 or not os.path.isfile(raw):
            raise ToolFailure(f"position export failed (exit {rc}):\n{log}")
        if jlc:
            cpl_path = os.path.join(out, f"{name}-CPL.csv")
            n = kicad_pos_to_jlc(raw, cpl_path)
            os.remove(raw)
        else:
            cpl_path = os.path.join(out, f"{name}-pos.csv")
            os.replace(raw, cpl_path)
            n = max(0, sum(1 for _ in open(cpl_path)) - 1)
        if n == 0:
            problems.append("CPL has no rows (no SMD footprints? use --include-tht)")

    # BOM from the schematic.
    bom_path = None
    sch = args.schematic or find_schematic(board)
    if args.no_bom:
        pass
    elif not sch:
        problems.append("no schematic next to the board - BOM skipped (pass --schematic)")
    else:
        bom_path = os.path.join(out, f"{name}-BOM.csv")
        lcsc = args.lcsc_field or detect_lcsc_field(sch)
        if jlc:
            fields = ["Value", "Reference", "${FOOTPRINT_NAME}", lcsc or "LCSC"]
            labels = JLC_BOM_LABELS
            group = ["Value", "${FOOTPRINT_NAME}", lcsc or "LCSC"]
        else:
            fields = ["Reference", "Value", "Footprint", "${QUANTITY}"] + ([lcsc] if lcsc else [])
            labels = ["Reference", "Value", "Footprint", "Qty"] + ([lcsc] if lcsc else [])
            group = ["Value", "Footprint"] + ([lcsc] if lcsc else [])
        b = ["sch", "export", "bom", "-o", bom_path, "--fields", ",".join(fields),
             "--labels", ",".join(labels), "--group-by", ",".join(group),
             "--ref-range-delimiter", "", "--exclude-dnp"]
        rc, log, _ = cli(b + [need_file(sch, (".kicad_sch",))], args.timeout, "bom")
        if rc != 0 or not os.path.isfile(bom_path):
            raise ToolFailure(f"BOM export failed (exit {rc}):\n{log}")
        if jlc and not lcsc:
            problems.append("no LCSC field found on the symbols - 'LCSC Part #' column is empty")

    # STEP.
    step_path = None
    if args.step:
        step_path = os.path.join(out, f"{name}.step")
        rc, log, _ = cli(["pcb", "export", "step", "-f", "-o", step_path, "--subst-models", board],
                         args.timeout, "step")
        if rc != 0 or not os.path.isfile(step_path) or os.path.getsize(step_path) < 1000:
            raise ToolFailure(f"STEP export failed (exit {rc}):\n{log}")

    # Zip: Gerbers + drill only, as fab houses expect.
    zip_path = None
    if args.zip:
        zip_path = os.path.join(out, f"{name}-gerbers.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(glob.glob(os.path.join(gdir, "*"))):
                z.write(f, os.path.basename(f))

    for l, f in made.items():
        if f and os.path.getsize(f) == 0:
            problems.append(f"empty Gerber for {l}")

    result = OrderedDict([
        ("preset", args.preset), ("copper_layers", len(copper)), ("gerber_dir", gdir),
        ("gerbers", {l: os.path.basename(f) for l, f in made.items() if f}),
        ("drill", [os.path.basename(f) for f in drills]),
        ("cpl", cpl_path), ("bom", bom_path), ("step", step_path), ("zip", zip_path),
        ("problems", problems), ("warnings", warnings)])
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"fab package ({args.preset}, {len(copper)} copper layers) -> {out}")
        for l, f in result["gerbers"].items():
            print(f"  {l:14} {f}")
        for f in result["drill"]:
            print(f"  {'drill':14} {f}")
        for k in ("cpl", "bom", "step", "zip"):
            if result[k]:
                print(f"  {k:14} {os.path.relpath(result[k], out)}")
        for wmsg in warnings:
            print(f"WARNING: {wmsg}")
        for pmsg in problems:
            print(f"PROBLEM: {pmsg}")
    return 1 if problems else 0


def board_sanity(board):
    """Cheap text checks for boards that export fine but would come back useless."""
    with open(board, encoding="utf-8", errors="replace") as f:
        text = f.read()
    out = []
    pads = len(re.findall(r"\n\t\t\(pad ", text))
    copper = len(re.findall(r"\n\t\((?:segment|arc|via|zone)\b", text))
    if pads and not copper:
        out.append(f"board has {pads} pads but no tracks, vias or zones - nothing is connected. "
                   "Route it (and update it from the schematic) before ordering.")
    nets = set(re.findall(r'\(pad "[^"]*"[^\n]*\n(?:\t{3}[^\n]*\n)*?\t{3}\(net (?:\d+ )?"([^"]+)"', text))
    if pads and not nets:
        out.append("no pad has a net - the board was never updated from its schematic (F8 in the PCB editor)")
    return out


def kicad_pos_to_jlc(src, dst):
    with open(src, newline="") as f:
        rows = list(csv.DictReader(f))
    with open(dst, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(JLC_CPL_HEADER)
        for r in rows:
            side = (r.get("Side") or "top").strip().lower()
            w.writerow([r["Ref"], f"{float(r['PosX']):.4f}mm", f"{float(r['PosY']):.4f}mm",
                        "Top" if side == "top" else "Bottom", f"{float(r['Rot']):g}"])
    return len(rows)


# --------------------------------------------------------------------------- render

def png_coverage(path):
    """Fraction of pixels that are not background (alpha>0 if RGBA, else != corner pixel)."""
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ToolFailure(f"not a PNG: {path}")
    i, idat, w, h, bd, ct = 8, b"", 0, 0, 0, 0
    while i < len(data):
        n, = struct.unpack(">I", data[i:i + 4])
        t, c = data[i + 4:i + 8], data[i + 8:i + 8 + n]
        i += 12 + n
        if t == b"IHDR":
            w, h, bd, ct = struct.unpack(">IIBB", c[:10])
        elif t == b"IDAT":
            idat += c
    if bd != 8 or ct not in (2, 6):
        return None
    bpp = 3 if ct == 2 else 4
    raw, stride, prev, o, rows = zlib.decompress(idat), w * bpp, bytearray(w * bpp), 0, []
    for _ in range(h):
        f = raw[o]
        line = bytearray(raw[o + 1:o + 1 + stride])
        o += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + b) & 255
            elif f == 3:
                line[x] = (line[x] + ((a + b) >> 1)) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(bytes(line))
        prev = line
    if bpp == 4:
        fg = sum(1 for r in rows for x in range(3, stride, 4) if r[x] > 0)
    else:
        bg = rows[0][:3]
        fg = sum(1 for r in rows for x in range(0, stride, 3) if r[x:x + 3] != bg)
    return fg / float(w * h)


def cmd_render(args):
    board = need_file(args.board, (".kicad_pcb",))
    out = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    cmd = ["pcb", "render", "-o", out, "--side", args.side, "-w", str(args.width),
           "-h", str(args.height), "--quality", args.quality]
    if args.rotate:
        cmd += ["--rotate", args.rotate]
    if args.background:
        cmd += ["--background", args.background]
    before = _mtime(out)
    rc, log, _ = cli(cmd + [board], args.timeout, "render")
    if rc != 0 or _mtime(out) == before:
        raise ToolFailure(f"render failed (exit {rc}):\n{log}")
    cov = png_coverage(out) if out.endswith(".png") else None
    print(f"rendered {out}" + (f"  coverage {cov:.1%}" if cov is not None else ""))
    if cov is not None and cov < args.min_coverage:
        print("PROBLEM: image is (nearly) blank - check the board outline and --side")
        return 1
    return 0


# --------------------------------------------------------------------------- main

def main(argv=None):
    global ARGS_KEEP_LOCALE
    p = argparse.ArgumentParser(prog="kicad.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                   help=f"seconds per kicad-cli call before its process group is killed (default {DEFAULT_TIMEOUT})")
    p.add_argument("--keep-locale", action="store_true",
                   help="run kicad-cli in the user's UI language instead of English")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("find", help="locate KiCad, version, API switch, kipy")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_find)

    for name, target, ext in (("drc", "board", ".kicad_pcb"), ("erc", "schematic", ".kicad_sch")):
        s = sub.add_parser(name, help=f"run {name.upper()} on a {ext}; exit 2 when errors exist")
        s.add_argument(target)
        s.add_argument("-o", "--output", help=f"JSON report path (default <name>-{name}.json)")
        s.add_argument("--all", action="store_true", help="include excluded violations too")
        s.add_argument("--top", type=int, default=3, help="examples printed per violation type")
        s.add_argument("--strict", action="store_true", help="exit 2 on warnings as well")
        s.add_argument("--json", action="store_true")
        if name == "drc":
            s.add_argument("--refill-zones", action="store_true", help="refill zones first (board not saved)")
            s.add_argument("--parity", action="store_true", help="also check schematic/PCB parity")
            s.set_defaults(func=cmd_drc)
        else:
            s.set_defaults(func=cmd_erc)

    s = sub.add_parser("fab", help="fabrication package: Gerbers, drill, CPL, BOM, STEP, zip")
    s.add_argument("board")
    s.add_argument("-o", "--output", required=True, help="output directory")
    s.add_argument("--preset", choices=["jlcpcb", "generic"], default="generic")
    s.add_argument("--schematic", help="schematic for the BOM (default: <board>.kicad_sch)")
    s.add_argument("--lcsc-field", help="symbol field holding LCSC numbers (default: auto-detect)")
    s.add_argument("--include-tht", action="store_true", help="put through-hole parts in the CPL too")
    s.add_argument("--step", action="store_true", help="also export a STEP model")
    s.add_argument("--zip", action="store_true", help="zip the Gerbers and drill files")
    s.add_argument("--no-bom", action="store_true")
    s.add_argument("--no-cpl", action="store_true")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_fab)

    s = sub.add_parser("render", help="3D render to PNG/JPEG with a blank-image check")
    s.add_argument("board")
    s.add_argument("-o", "--output", required=True)
    s.add_argument("--side", default="top", choices=["top", "bottom", "left", "right", "front", "back"])
    s.add_argument("--width", type=int, default=1600)
    s.add_argument("--height", type=int, default=900)
    s.add_argument("--quality", default="basic", choices=["basic", "high"])
    s.add_argument("--rotate", help="e.g. '-45,0,45' for an isometric view")
    s.add_argument("--background", choices=["default", "transparent", "opaque"])
    s.add_argument("--min-coverage", type=float, default=0.01)
    s.set_defaults(func=cmd_render)

    args = p.parse_args(argv)
    ARGS_KEEP_LOCALE = args.keep_locale
    try:
        return args.func(args)
    except SetupError as e:
        print(f"setup error: {e}", file=sys.stderr)
        return 3
    except ToolFailure as e:
        print(f"failed: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 3
    finally:
        if _EN_HOME:
            shutil.rmtree(_EN_HOME, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
