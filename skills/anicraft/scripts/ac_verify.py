#!/usr/bin/env python3
"""Check an AniCraft document or its exports; print JSON, exit 1 on any failed check.

All frame numbers are 1-based (timeline frames).

  ac_verify.py doc F.anicraft [--size 1080x1080] [--fps 30] [--frames 30]
      [--layer NAME ...] [--text STR ...] [--symbol NAME[:graphic|movie_clip|button] ...]
      [--motion LAYER ...] [--motion-path LAYER ...] [--motion-key LAYER:PROP@FRAME=VALUE ...]
      [--shape-tween LAYER ...] [--hints LAYER:N ...] [--camera FRAME:zoom=140 ...]
      [--bones N] [--limited N] [--poses LAYER:N] [--action FRAME:OP ...]
      [--scripts-run] [--test-movie-ends FRAME] [--bitmap NAME ...]
  ac_verify.py media FILE [--frames N] [--size WxH] [--fps F] [--duration S] [--audio yes|no]
  ac_verify.py sheet SHEET.json [--frames N]
  ac_verify.py lottie FILE.json [--frames N] [--fps F] [--size WxH]
  ac_verify.py html FILE.html            self-contained: no external src/href/url()
  ac_verify.py seq DIR [--frames N] [--size WxH]
  ac_verify.py differ A.png B.png        decoded pixel data differs
  ac_verify.py edges F.anicraft --frames 1 15 30 [--color #e4572e]   renders them; fails
                                         when anything (or that colour) touches the frame
                                         edge, i.e. is cut off by the stage or the camera
"""
import argparse
import glob
import hashlib
import json
import os
import re
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aclib  # noqa: E402

CHECKS = []


def check(name, ok, got=None):
    CHECKS.append({"check": name, "ok": bool(ok), "got": got})


def size_arg(s):
    w, h = s.lower().split("x")
    return int(w), int(h)


def png_info(path):
    """(width, height, sha1 of the decompressed image data) from a PNG, stdlib only."""
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("%s is not a PNG" % path)
    pos, idat, w, h = 8, b"", 0, 0
    while pos < len(data):
        length, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        if ctype == b"IHDR":
            w, h = struct.unpack(">II", body[:8])
        elif ctype == b"IDAT":
            idat += body
        pos += 12 + length
    return w, h, hashlib.sha1(zlib.decompress(idat)).hexdigest()


def layers_by_name(doc):
    return {l["name"]: l for l in aclib.walk_layers(doc["scenes"][0]["timeline"])}


def layer_or_fail(layers, name, what):
    if name not in layers:
        check("%s %s" % (what, name), False, "no layer %r (have %s)" % (name, sorted(layers)))
        return None
    return layers[name]


def cmd_doc(a):
    data = aclib.load_document(a.file)
    doc = data["document"]
    layers = layers_by_name(doc)
    with aclib.Serve(a.file) as s:
        info = s.call("doc.info")
        stage = info["stage"]
        if a.size:
            check("size", (stage["width"], stage["height"]) == size_arg(a.size),
                  "%sx%s" % (stage["width"], stage["height"]))
        if a.fps:
            check("fps", abs(stage["fps"] - a.fps) < 1e-6, stage["fps"])
        if a.frames:
            check("frames", info["frames"] == a.frames, info["frames"])
        for name in a.layer:
            check("layer %s" % name, name in layers, sorted(layers))
        texts = []
        bitmaps = set()
        lib = s.call("library.items").get("items", [])
        names = {}
        for item in lib:
            for key in ("symbol", "bitmap", "sound"):
                if key in item:
                    names[item[key]] = item["name"]
        for layer in layers.values():
            for k in layer.get("keyframes", []):
                for el in k.get("elements", []):
                    kind, body = aclib.element_kind(el)
                    if kind == "Text":
                        texts.append(body.get("text"))
                    elif kind == "Shape" and isinstance(body.get("fill"), dict) \
                            and "Bitmap" in body["fill"]:
                        bitmaps.add(names.get(body["fill"]["Bitmap"]["bitmap"]))
        for t in a.text:
            check("text %r" % t, t in texts, texts)
        for b in a.bitmap:
            check("bitmap %s on stage" % b, b in bitmaps, sorted(x for x in bitmaps if x))
        kinds = {"Graphic": "graphic", "MovieClip": "movie_clip", "Button": "button"}
        lib_syms = {sym["name"]: kinds.get(sym.get("kind"), sym.get("kind"))
                    for sym in doc.get("library", [])}
        for spec in a.symbol:
            name, _, kind = spec.partition(":")
            got = lib_syms.get(name)
            check("symbol %s" % spec, got is not None and (not kind or got == kind), lib_syms)
        for name in a.motion:
            layer = layer_or_fail(layers, name, "motion tween on")
            if layer is not None:
                check("motion tween on %s" % name,
                      any(k.get("motion") for k in layer["keyframes"]))
        for name in a.motion_path:
            layer = layer_or_fail(layers, name, "motion path on")
            if layer is not None:
                check("motion path on %s" % name,
                      any((k.get("motion") or {}).get("path") for k in layer["keyframes"]))
        for spec in a.motion_key:
            m = re.match(r"(.+):(\w+)@(\d+)=(-?[\d.]+)$", spec)
            if not m:
                sys.exit("bad --motion-key %s (LAYER:PROP@FRAME=VALUE)" % spec)
            name, prop, frame, value = m.group(1), m.group(2), int(m.group(3)), float(m.group(4))
            layer = layer_or_fail(layers, name, "motion key")
            if layer is None:
                continue
            got = None
            for k in layer["keyframes"]:
                for t in (k.get("motion") or {}).get("tracks", []):
                    if t["property"] == prop:
                        for key in t["keys"]:
                            if key["frame"] == frame - 1:
                                got = key["value"]
            check("motion key %s" % spec, got is not None and abs(got - value) < 0.01, got)
        for name in a.shape_tween:
            layer = layer_or_fail(layers, name, "shape tween on")
            if layer is not None:
                check("shape tween on %s" % name,
                      any((k.get("tween") or {}).get("kind") == "Shape" for k in layer["keyframes"]))
        for spec in a.hints:
            name, _, n = spec.rpartition(":")
            layer = layer_or_fail(layers, name, "hints on")
            if layer is not None:
                got = max([len(k.get("hints") or []) for k in layer["keyframes"]] or [0])
                check("hints on %s >= %s" % (name, n), got >= int(n), got)
        for spec in a.camera:
            m = re.match(r"(\d+):(\w+)=(-?[\d.]+)$", spec)
            if not m:
                sys.exit("bad --camera %s (FRAME:PROP=VALUE)" % spec)
            cam = s.call("camera.info", {"frame": int(m.group(1)) - 1})
            got = cam.get(m.group(2))
            check("camera %s" % spec, cam.get("camera", True) and got is not None
                  and abs(float(got) - float(m.group(3))) < 0.05, got)
        if a.bones is not None or a.limited is not None:
            bones = [b for l in layers.values() for b in (l.get("armature") or {}).get("bones", [])]
            if a.bones is not None:
                check("bones >= %d" % a.bones, len(bones) >= a.bones, len(bones))
            if a.limited is not None:
                limited = sum(1 for b in bones if b.get("limits"))
                check("bones with limits >= %d" % a.limited, limited >= a.limited, limited)
        if a.poses:
            name, _, n = a.poses.rpartition(":")
            layer = layer_or_fail(layers, name, "poses on")
            if layer is not None:
                poses = [k for k in layer["keyframes"] if k.get("pose")]
                angles = {json.dumps(sorted((p["bone"], round(p["angle"], 3)) for p in k["pose"]))
                          for k in poses}
                # a looping cycle may end on its start pose: >= 2 distinct poses suffice
                check("pose keyframes on %s >= %s (>= 2 distinct)" % (name, n),
                      len(poses) >= int(n) and len(angles) >= min(2, len(poses)),
                      {"pose_keys": [k["start"] + 1 for k in poses], "distinct": len(angles)})
        acts = s.call("actions.list").get("frames", [])
        for spec in a.action:
            frame, _, op = spec.partition(":")
            hit = [x for x in acts if x["frame"] == int(frame) - 1
                   and any(y.get("op") == op for y in x.get("actions", []))]
            check("action %s" % spec, hit, [(x["frame"] + 1, x.get("summary")) for x in acts])
        if a.scripts_run:
            scripts = s.call("script.list", {"text": False}).get("frames", [])
            bad = [x for x in scripts if not x.get("runs") or x.get("problems")]
            check("frame scripts run", not bad, bad or len(scripts))
        if a.test_movie_ends:
            tm = s.call("control.test_movie", {"frames": max(10 * int(stage["fps"]), info["frames"] * 3)})
            st = tm["state"]
            check("test_movie ends on %d, stopped" % a.test_movie_ends,
                  st["frame"] == a.test_movie_ends - 1 and not st["playing"],
                  {"frame": st["frame"] + 1, "playing": st["playing"], "output": tm.get("output")})


def cmd_media(a):
    probe = aclib.ffprobe(a.file)
    video = [x for x in probe["streams"] if x.get("codec_type") == "video"]
    audio = [x for x in probe["streams"] if x.get("codec_type") == "audio"]
    check("video stream", video, [x.get("codec_name") for x in probe["streams"]])
    if not video:
        return
    v = video[0]
    if a.frames:
        got = int(v.get("nb_read_frames") or v.get("nb_frames") or 0)
        check("frames", got == a.frames, got)
    if a.size:
        check("size", (v["width"], v["height"]) == size_arg(a.size), "%sx%s" % (v["width"], v["height"]))
    if a.fps:
        num, den = (v.get("r_frame_rate") or "0/1").split("/")
        got = float(num) / float(den or 1)
        check("fps", abs(got - a.fps) < 0.01, got)
    if a.duration:
        got = float(probe["format"].get("duration", 0))
        check("duration", abs(got - a.duration) <= 1.0 / (a.fps or 24) + 0.05, got)
    if a.audio:
        check("audio %s" % a.audio, bool(audio) == (a.audio == "yes"), len(audio))


def cmd_sheet(a):
    with open(a.file, encoding="utf-8") as fh:
        m = json.load(fh)
    frames = m.get("frames", {})
    n = len(frames)
    if a.frames:
        check("sheet frames", n == a.frames, n)
    image = os.path.join(os.path.dirname(os.path.abspath(a.file)), m.get("meta", {}).get("image", ""))
    check("sheet image exists", os.path.isfile(image), image)
    if os.path.isfile(image):
        w, h, _ = png_info(image)
        size = m.get("meta", {}).get("size", {})
        check("sheet image size matches map", (w, h) == (size.get("w"), size.get("h")), "%dx%d" % (w, h))
        items = frames.values() if isinstance(frames, dict) else frames
        inside = all(f["frame"]["x"] + f["frame"]["w"] <= w and f["frame"]["y"] + f["frame"]["h"] <= h
                     for f in items)
        check("frame rects inside the image", inside)


def cmd_lottie(a):
    with open(a.file, encoding="utf-8") as fh:
        d = json.load(fh)
    got = int(round(d.get("op", 0) - d.get("ip", 0)))
    if a.frames:
        check("lottie frames (op-ip)", got == a.frames, got)
    if a.fps:
        check("lottie fps", abs(d.get("fr", 0) - a.fps) < 0.01, d.get("fr"))
    if a.size:
        check("lottie size", (d.get("w"), d.get("h")) == size_arg(a.size), "%sx%s" % (d.get("w"), d.get("h")))
    check("lottie has layers", d.get("layers"), len(d.get("layers", [])))


def cmd_html(a):
    with open(a.file, encoding="utf-8") as fh:
        text = fh.read()
    external = re.findall(r"""(?:src|href)\s*=\s*["']((?:https?:)?//[^"']+)""", text)
    external += re.findall(r"""url\(\s*["']?((?:https?:)?//[^)"']+)""", text)
    check("html self-contained (no external src/href/url)", not external,
          external[:5] or "%d bytes, no external references" % len(text))
    check("html has a canvas or svg", "<canvas" in text or "<svg" in text)


def cmd_seq(a):
    files = sorted(glob.glob(os.path.join(a.dir, "*.png")))
    if a.frames:
        check("png count", len(files) == a.frames, len(files))
    if files and a.size:
        w, h, _ = png_info(files[0])
        check("png size", (w, h) == size_arg(a.size), "%dx%d" % (w, h))
    if len(files) > 1:
        check("first and last frames differ", png_info(files[0])[2] != png_info(files[-1])[2])


def png_pixels(path):
    """(width, height, channels, rows) of an 8-bit RGB/RGBA PNG, unfiltered (stdlib only)."""
    with open(path, "rb") as fh:
        data = fh.read()
    pos, idat = 8, b""
    while pos < len(data):
        length, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        if ctype == b"IHDR":
            w, h, depth, color = struct.unpack(">IIBB", body[:10])
            if depth != 8 or color not in (2, 6):
                raise ValueError("%s: only 8-bit RGB/RGBA PNGs are supported" % path)
            ch = 3 if color == 2 else 4
        elif ctype == b"IDAT":
            idat += body
        pos += 12 + length
    raw, stride, rows, prev = zlib.decompress(idat), w * ch, [], bytearray(w * ch)
    for y in range(h):
        f, line = raw[y * (stride + 1)], bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            left = line[i - ch] if i >= ch else 0
            up, ul = prev[i], prev[i - ch] if i >= ch else 0
            if f == 1:
                line[i] = (line[i] + left) & 255
            elif f == 2:
                line[i] = (line[i] + up) & 255
            elif f == 3:
                line[i] = (line[i] + (left + up) // 2) & 255
            elif f == 4:
                p = left + up - ul
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - ul)
                line[i] = (line[i] + (left if pa <= pb and pa <= pc else up if pb <= pc else ul)) & 255
        rows.append(line)
        prev = line
    return w, h, ch, rows


def cmd_edges(a):
    """Render frames and check a border strip is one flat colour: nothing cut off."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="ac-edges-")
    for n in a.frames:
        png = os.path.join(tmp, "f%04d.png" % n)
        aclib.run_cli(["render", a.file, "--out", png, "--frame", str(n), "--scale", str(a.scale)])
        w, h, ch, rows = png_pixels(png)
        b = max(1, a.border)
        strip = [tuple(rows[y][x * ch:x * ch + 3]) for y in range(h) for x in range(w)
                 if y < b or y >= h - b or x < b or x >= w - b]
        if a.color:  # only this colour (an object's fill) must stay off the edge
            ref = tuple(int(a.color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
            off = sum(1 for p in strip if max(abs(p[i] - ref[i]) for i in range(3)) <= a.tolerance)
            check("frame %d: no %s on the frame edge" % (n, a.color), off <= a.max_pixels,
                  "%d of %d border pixels match it" % (off, len(strip)))
            continue
        bg = max(set(strip), key=strip.count)
        off = sum(1 for p in strip if max(abs(p[i] - bg[i]) for i in range(3)) > a.tolerance)
        check("frame %d: nothing touches the frame edge" % n, off <= a.max_pixels,
              "%d of %d border pixels differ from %s" % (off, len(strip), "#%02x%02x%02x" % bg))
    shutil_rm(tmp)


def shutil_rm(path):
    import shutil
    shutil.rmtree(path, ignore_errors=True)


def cmd_differ(a):
    ha, hb = png_info(a.a)[2], png_info(a.b)[2]
    check("%s differs from %s" % (os.path.basename(a.a), os.path.basename(a.b)), ha != hb)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("doc")
    d.add_argument("file")
    d.add_argument("--size")
    d.add_argument("--fps", type=float)
    d.add_argument("--frames", type=int)
    for name in ("layer", "text", "symbol", "motion", "motion-path", "motion-key", "shape-tween",
                 "hints", "camera", "action", "bitmap"):
        d.add_argument("--" + name, action="append", default=[])
    d.add_argument("--bones", type=int)
    d.add_argument("--limited", type=int)
    d.add_argument("--poses")
    d.add_argument("--scripts-run", action="store_true")
    d.add_argument("--test-movie-ends", type=int)
    m = sub.add_parser("media")
    m.add_argument("file")
    m.add_argument("--frames", type=int)
    m.add_argument("--size")
    m.add_argument("--fps", type=float)
    m.add_argument("--duration", type=float)
    m.add_argument("--audio", choices=["yes", "no"])
    sh = sub.add_parser("sheet")
    sh.add_argument("file")
    sh.add_argument("--frames", type=int)
    lo = sub.add_parser("lottie")
    lo.add_argument("file")
    lo.add_argument("--frames", type=int)
    lo.add_argument("--fps", type=float)
    lo.add_argument("--size")
    h = sub.add_parser("html")
    h.add_argument("file")
    sq = sub.add_parser("seq")
    sq.add_argument("dir")
    sq.add_argument("--frames", type=int)
    sq.add_argument("--size")
    ed = sub.add_parser("edges")
    ed.add_argument("file")
    ed.add_argument("--frames", type=int, nargs="+", default=[1])
    ed.add_argument("--scale", type=float, default=0.25)
    ed.add_argument("--border", type=int, default=2, help="strip width in rendered px")
    ed.add_argument("--tolerance", type=int, default=24, help="per-channel difference allowed")
    ed.add_argument("--color", help="#rrggbb: check only this colour (a full-bleed floor or "
                    "background touches the edge on purpose)")
    ed.add_argument("--max-pixels", type=int, default=0, help="off-colour border pixels allowed")
    df = sub.add_parser("differ")
    df.add_argument("a")
    df.add_argument("b")
    a = ap.parse_args()
    try:
        {"doc": cmd_doc, "media": cmd_media, "sheet": cmd_sheet, "lottie": cmd_lottie,
         "html": cmd_html, "seq": cmd_seq, "differ": cmd_differ,
         "edges": cmd_edges}[a.cmd](a)
    except (OSError, ValueError, RuntimeError) as exc:
        check("%s readable" % a.cmd, False, str(exc))
    ok = all(c["ok"] for c in CHECKS)
    print(json.dumps({"ok": ok, "checks": CHECKS}, indent=1, ensure_ascii=False, default=str))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
