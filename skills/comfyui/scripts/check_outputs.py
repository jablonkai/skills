#!/usr/bin/env python3
"""Verify ComfyUI outputs on disk — standard library only (Python 3.9+).

  check_outputs.py DIR_OR_FILES... [--count N] [--width W --height H]
                   [--require-workflow] [--seeds 101-104] [--history]

Checks each PNG/JPEG/WebP for dimensions and, for PNG, the `prompt` (API graph) and
`workflow` (editor graph) text chunks ComfyUI embeds. --seeds checks that every listed
seed appears in some file's embedded prompt. --history re-reads /history for each
prompt_id found in the .params.json sidecars and checks status `success`.
Prints a JSON report; exits 1 when any check fails.
"""
import argparse
import json
import os
import struct
import sys
import urllib.request
import zlib

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}


def png_info(data):
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    pos, size, text = 8, None, {}
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            size = struct.unpack(">II", body[:8])
        elif kind == b"tEXt":
            k, _, v = body.partition(b"\0")
            text[k.decode("latin-1")] = v.decode("latin-1")
        elif kind == b"zTXt":
            k, _, rest = body.partition(b"\0")
            text[k.decode("latin-1")] = zlib.decompress(rest[1:]).decode("latin-1")
        elif kind == b"iTXt":
            k, _, rest = body.partition(b"\0")
            flag = rest[0]
            rest = rest[2:].split(b"\0", 2)[2]
            text[k.decode("utf-8")] = (zlib.decompress(rest) if flag else rest).decode("utf-8")
        elif kind == b"IEND":
            break
        pos += 12 + length
    return size, text


def jpeg_size(data):
    pos = 2
    while pos < len(data):
        marker, length = data[pos + 1], struct.unpack(">H", data[pos + 2:pos + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            h, w = struct.unpack(">HH", data[pos + 5:pos + 9])
            return w, h
        pos += 2 + length
    raise ValueError("no JPEG frame header")


def webp_size(data):
    kind = data[12:16]
    if kind == b"VP8X":
        return 1 + int.from_bytes(data[24:27], "little"), 1 + int.from_bytes(data[27:30], "little")
    if kind == b"VP8 ":
        w, h = struct.unpack("<HH", data[26:30])
        return w & 0x3FFF, h & 0x3FFF
    if kind == b"VP8L":
        b = int.from_bytes(data[21:25], "little")
        return (b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1
    raise ValueError("unknown WebP chunk")


def parse_seeds(spec):
    seeds = []
    for part in spec.split(","):
        if "-" in part.strip()[1:]:
            a, b = part.split("-", 1)
            seeds += list(range(int(a), int(b) + 1))
        else:
            seeds.append(int(part))
    return seeds


def embedded_seeds(prompt_json):
    try:
        graph = json.loads(prompt_json)
    except ValueError:
        return set()
    return {v for node in graph.values() if isinstance(node, dict)
            for k, v in (node.get("inputs") or {}).items() if k in ("seed", "noise_seed") and isinstance(v, int)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--count", type=int)
    ap.add_argument("--width", type=int)
    ap.add_argument("--height", type=int)
    ap.add_argument("--require-workflow", action="store_true", help="PNG must carry the editor `workflow` chunk too")
    ap.add_argument("--seeds")
    ap.add_argument("--history", action="store_true")
    ap.add_argument("--url", default=os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188"))
    args = ap.parse_args()

    files = []
    for p in args.paths:
        if os.path.isdir(p):
            files += sorted(os.path.join(p, f) for f in os.listdir(p) if os.path.splitext(f)[1].lower() in IMAGE_EXT)
        else:
            files.append(p)
    report, failures, seen_seeds = {"files": []}, [], set()
    for path in files:
        with open(path, "rb") as f:
            data = f.read()
        ext = os.path.splitext(path)[1].lower()
        row = {"file": path}
        try:
            if ext == ".png":
                size, text = png_info(data)
                row["has_prompt"] = "prompt" in text
                row["has_workflow"] = "workflow" in text
                if not row["has_prompt"]:
                    failures.append("%s: no embedded prompt" % path)
                if args.require_workflow and not row["has_workflow"]:
                    failures.append("%s: no embedded editor workflow" % path)
                seeds = embedded_seeds(text.get("prompt", "{}"))
                row["seeds"] = sorted(seeds)
                seen_seeds |= seeds
            elif ext in (".jpg", ".jpeg"):
                size = jpeg_size(data)
            else:
                size = webp_size(data)
        except (ValueError, struct.error, IndexError, zlib.error) as e:
            failures.append("%s: unreadable (%s)" % (path, e))
            report["files"].append(row)
            continue
        row["width"], row["height"] = size
        if args.width and size[0] != args.width:
            failures.append("%s: width %d != %d" % (path, size[0], args.width))
        if args.height and size[1] != args.height:
            failures.append("%s: height %d != %d" % (path, size[1], args.height))
        sidecar = os.path.splitext(path)[0] + ".params.json"
        if os.path.exists(sidecar):
            with open(sidecar) as f:
                row["prompt_id"] = json.load(f).get("prompt_id")
        report["files"].append(row)
    if args.count is not None and len(files) != args.count:
        failures.append("expected %d files, found %d" % (args.count, len(files)))
    if args.seeds:
        missing = [s for s in parse_seeds(args.seeds) if s not in seen_seeds]
        if missing:
            failures.append("seeds not found in any embedded prompt: %s" % missing)
    if args.history:
        for row in report["files"]:
            pid = row.get("prompt_id")
            if not pid:
                failures.append("%s: no .params.json sidecar with a prompt_id" % row["file"])
                continue
            with urllib.request.urlopen("%s/history/%s" % (args.url.rstrip("/"), pid), timeout=30) as r:
                entry = json.loads(r.read()).get(pid) or {}
            row["history_status"] = (entry.get("status") or {}).get("status_str")
            if row["history_status"] != "success":
                failures.append("%s: /history status %s" % (row["file"], row["history_status"]))
    report["count"] = len(files)
    report["ok"] = not failures
    report["failures"] = failures
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
