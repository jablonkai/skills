#!/usr/bin/env python3
"""Static checks for Godot 4 projects and captured frames. No Godot needed.

    python3 gd-verify.py PROJECT_DIR            check project.godot and every .tscn/.tres
    python3 gd-verify.py scene.tscn other.tres  check just these files
    python3 gd-verify.py --png frame.png [--png-size WxH] [--min-colors N]

Scene checks: format=3 header, duplicate or dangling ExtResource/SubResource ids,
ext_resource paths that do not exist, node parent paths that do not resolve,
duplicate sibling names, [connection] from/to nodes that do not exist, and
connection methods missing from the target node's script. project.godot checks:
main scene and autoload paths exist.

PNG checks: prints size and distinct colour count; fails when the image is blank
(fewer than --min-colors colours, default 2) or not the --png-size.

Exit 0 when clean, 1 on any error. Warnings (load_steps mismatch (4.7 omits it), paths through
instanced scenes that cannot be checked) do not fail.
"""

import argparse
import re
import struct
import sys
import zlib
from pathlib import Path

HEADER_RE = re.compile(r"^\[(\w+)(.*)\]\s*$")
ATTR_RE = re.compile(r'(\w+)=("(?:[^"\\]|\\.)*"|\S+)')
REF_RE = re.compile(r'\b(ExtResource|SubResource)\(\s*"([^"]+)"\s*\)')


class Report:
    def __init__(self):
        self.errors = 0
        self.warnings = 0

    def error(self, where, msg):
        self.errors += 1
        print(f"ERROR {where}: {msg}")

    def warn(self, where, msg):
        self.warnings += 1
        print(f"WARN  {where}: {msg}")


def attrs(text):
    out = {}
    for key, value in ATTR_RE.findall(text):
        if value.startswith('"'):
            value = value[1:-1].encode().decode("unicode_escape")
        out[key] = value
    return out


def find_root(path):
    for parent in [path.parent if path.is_file() else path, *path.resolve().parents]:
        if (parent / "project.godot").is_file():
            return parent
    return None


def res_to_path(res, root):
    if root is None or not res.startswith("res://"):
        return None
    return root / res[len("res://"):]


def script_methods(script_path):
    """Methods defined in the script, and whether it extends another project script
    (then a missing method may be inherited, so it is only a warning)."""
    try:
        source = script_path.read_text(encoding="utf-8")
    except OSError:
        return None, False
    methods = set(re.findall(r"^\s*(?:static\s+)?func\s+(\w+)", source, re.M))
    base = re.search(r"^extends\s+(\S+)", source, re.M)
    inherits_script = bool(base) and (base.group(1).startswith('"') or base.group(1) in project_classes(script_path))
    return methods, inherits_script


_CLASSES = {}


def project_classes(script_path):
    root = find_root(script_path)
    if root not in _CLASSES:
        names = set()
        for gd in root.rglob("*.gd") if root else []:
            if ".godot" not in gd.parts:
                names.update(re.findall(r"^class_name\s+(\w+)", gd.read_text(encoding="utf-8", errors="replace"), re.M))
        _CLASSES[root] = names
    return _CLASSES[root]


def check_resource_file(path, root, report):
    errors_before = report.errors
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        report.error(path, "empty file")
        return
    head = HEADER_RE.match(lines[0])
    if not head or head.group(1) not in ("gd_scene", "gd_resource"):
        report.error(f"{path}:1", "first line must be [gd_scene …] or [gd_resource …]")
        return
    head_attrs = attrs(head.group(2))
    if head_attrs.get("format") != "3":
        report.error(f"{path}:1", f"format={head_attrs.get('format')} — Godot 4 writes format=3")

    ext, sub = {}, {}
    nodes = {}  # node path -> (lineno, script ext id or None, instanced)
    connections = []
    refs = []
    current = None
    for lineno, line in enumerate(lines, 1):
        m = HEADER_RE.match(line)
        if m:
            kind, a = m.group(1), attrs(m.group(2))
            current = None
            if kind == "ext_resource":
                rid = a.get("id")
                if rid in ext:
                    report.error(f"{path}:{lineno}", f'duplicate ext_resource id "{rid}"')
                ext[rid] = a
                target = res_to_path(a.get("path", ""), root)
                if target is not None and not target.exists():
                    report.error(f"{path}:{lineno}", f"ext_resource path does not exist: {a.get('path')}")
            elif kind == "sub_resource":
                rid = a.get("id")
                if rid in sub:
                    report.error(f"{path}:{lineno}", f'duplicate sub_resource id "{rid}"')
                sub[rid] = a
            elif kind == "node":
                name = a.get("name")
                parent = a.get("parent")
                if parent is None:
                    if nodes:
                        report.error(f"{path}:{lineno}", f'node "{name}" has no parent= but is not the first node')
                    node_path = "."
                else:
                    if parent not in nodes:
                        if any(nodes[p][2] and (parent == p or parent.startswith(p + "/")) for p in nodes if p != "."):
                            report.warn(f"{path}:{lineno}", f'parent "{parent}" is inside an instanced scene; not checked')
                        else:
                            report.error(f"{path}:{lineno}", f'parent "{parent}" of node "{name}" does not exist (earlier nodes: {", ".join(nodes) or "none"})')
                    node_path = name if parent == "." else f"{parent}/{name}"
                    if node_path in nodes:
                        report.error(f"{path}:{lineno}", f'duplicate node path "{node_path}"')
                instanced = "instance" in a
                nodes[node_path] = [lineno, None, instanced]
                current = node_path
            elif kind == "connection":
                connections.append((lineno, a))
            continue
        for kind, rid in REF_RE.findall(line):
            refs.append((lineno, kind, rid))
        if current is not None:
            sm = re.match(r'^script\s*=\s*ExtResource\(\s*"([^"]+)"\s*\)', line)
            if sm:
                nodes[current][1] = sm.group(1)
    for lineno, kind, rid in refs:
        table = ext if kind == "ExtResource" else sub
        if rid not in table:
            report.error(f"{path}:{lineno}", f'{kind}("{rid}") is not declared')

    steps = head_attrs.get("load_steps")
    if steps is not None and steps.isdigit() and int(steps) != len(ext) + len(sub) + 1:
        report.warn(f"{path}:1", f"load_steps={steps}, expected {len(ext) + len(sub) + 1} (Godot ignores it, but fix it)")

    for lineno, a in connections:
        where = f"{path}:{lineno}"
        for end in ("from", "to"):
            if a.get(end) not in nodes:
                report.error(where, f'connection {end}="{a.get(end)}" is not a node in this scene')
        target = nodes.get(a.get("to"))
        method = a.get("method")
        if target and target[1] and method:
            script_ref = ext.get(target[1], {}).get("path", "")
            script_path = res_to_path(script_ref, root)
            if script_path and script_path.suffix == ".gd":
                methods, inherits_script = script_methods(script_path)
                if methods is not None and method not in methods:
                    if inherits_script:
                        report.warn(where, f'method "{method}" not in {script_ref}; may be inherited')
                    else:
                        report.error(where, f'method "{method}" not found in {script_ref}')

    if report.errors == errors_before:
        print(f"OK    {path} ({len(nodes)} nodes, {len(ext)} ext, {len(sub)} sub, {len(connections)} connections)")


def check_project(root, report):
    cfg = (root / "project.godot").read_text(encoding="utf-8")
    main = re.search(r'^run/main_scene="([^"]+)"', cfg, re.M)
    if not main:
        report.warn(root / "project.godot", "no run/main_scene — running the project opens nothing")
    elif main.group(1).startswith("res://") and not res_to_path(main.group(1), root).exists():
        report.error(root / "project.godot", f"main scene does not exist: {main.group(1)}")
    autoload = re.search(r"^\[autoload\]\n(.*?)(?=^\[|\Z)", cfg, re.M | re.S)
    if autoload:
        for name, res in re.findall(r'^(\w+)="\*?(res://[^"]+)"', autoload.group(1), re.M):
            if not res_to_path(res, root).exists():
                report.error(root / "project.godot", f"autoload {name} path does not exist: {res}")


def read_png(path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    pos, idat, info = 8, b"", None
    while pos < len(data):
        length, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        chunk = data[pos + 8:pos + 8 + length]
        if ctype == b"IHDR":
            info = struct.unpack(">IIBBBBB", chunk)
        elif ctype == b"IDAT":
            idat += chunk
        pos += 12 + length
    width, height, depth, color, _, _, interlace = info
    channels = {0: 1, 2: 3, 4: 2, 6: 4}.get(color)
    if depth != 8 or channels is None or interlace:
        return width, height, None  # size only; colour count needs 8-bit non-interlaced
    raw = zlib.decompress(idat)
    stride = width * channels
    prev = bytearray(stride)
    colors = set()
    step = max(1, height // 64)
    for y in range(height):
        f = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for x in range(stride):
            a = line[x - channels] if x >= channels else 0
            b = prev[x]
            c = prev[x - channels] if x >= channels else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + b) & 255
            elif f == 3:
                line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        if y % step == 0:
            for x in range(0, stride, channels * max(1, width // 64)):
                colors.add(bytes(line[x:x + channels]))
        prev = line
    return width, height, len(colors)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", type=Path)
    ap.add_argument("--png", action="append", type=Path, default=[])
    ap.add_argument("--png-size")
    ap.add_argument("--min-colors", type=int, default=2)
    args = ap.parse_args()
    if not args.paths and not args.png:
        ap.error("give a project dir, scene/resource files, or --png")

    report = Report()
    for p in args.paths:
        if p.is_dir():
            if not (p / "project.godot").is_file():
                report.error(p, "no project.godot")
                continue
            check_project(p, report)
            for f in sorted(p.rglob("*")):
                rel = f.relative_to(p)
                if f.suffix in (".tscn", ".tres") and not any(part.startswith(".") for part in rel.parts):
                    if not any((p / Path(*rel.parts[:i]) / ".gdignore").exists() for i in range(1, len(rel.parts))):
                        check_resource_file(f, p, report)
        elif p.suffix in (".tscn", ".tres"):
            check_resource_file(p, find_root(p), report)
        else:
            report.error(p, "expected a project dir, .tscn or .tres")

    for png in args.png:
        try:
            width, height, colors = read_png(png)
        except (OSError, ValueError, zlib.error, TypeError) as exc:
            report.error(png, f"cannot read PNG: {exc}")
            continue
        size = f"{width}x{height}"
        note = f"{colors} sampled colours" if colors is not None else "colours not checked (non 8-bit)"
        print(f"PNG   {png}: {size}, {note}")
        if args.png_size and size != args.png_size:
            report.error(png, f"size {size}, expected {args.png_size}")
        if colors is not None and colors < args.min_colors:
            report.error(png, f"looks blank ({colors} colour(s))")

    print(f"--- {report.errors} error(s), {report.warnings} warning(s)")
    sys.exit(1 if report.errors else 0)


if __name__ == "__main__":
    main()
