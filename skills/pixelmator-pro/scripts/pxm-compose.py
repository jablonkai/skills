#!/usr/bin/env python3
"""Build a layered Pixelmator Pro document from a JSON spec, export it, report the layers.

usage: pxm-compose.py SPEC.json [--dry-run] [--keep-open] [--timeout SECS]

The spec (paths are relative to the spec file):
{
  "width": 1080, "height": 1350,
  "background": "#ffffff" | "transparent",          # default: white
  "layers": [                                         # bottom -> top
    {"type": "image", "file": "photo.jpg", "fit": "cover",   # cover|contain|none
     "x": 0, "y": 0, "width": 1080, "height": 1350,          # frame, default canvas
     "remove_background": false},
    {"type": "rounded-rect", "x": 90, "y": 950, "width": 900, "height": 300,
     "radius": 40, "fill": "#000000", "fill_opacity": 60,
     "stroke": "#ffffff", "stroke_width": 4},                 # also rect|ellipse|polygon|star
    {"type": "text", "text": "Summer Sale", "font": "Helvetica-Bold", "size": 120,
     "color": "#ffffff", "x": 0, "y": 1010, "width": 1080, "align": "center"}
  ],
  "export": [{"path": "post.png"}, {"path": "post.jpg", "quality": 85}, {"path": "post.pxd"}]
}
Every layer also takes "name", "opacity" (0-100) and "rotation" (degrees).
Prints a JSON report: the exported files plus every layer (bottom -> top) with its class,
name, bounds and, for text, the text, font and size Pixelmator actually applied.
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHAPES = {
    "rect": "rectangle shape layer",
    "rounded-rect": "rounded rectangle shape layer",
    "ellipse": "ellipse shape layer",
    "polygon": "polygon shape layer",
    "star": "star shape layer",
}
EXPORT_FORMATS = {
    "png": "PNG", "jpg": "JPEG", "jpeg": "JPEG", "heic": "HEIC", "webp": "WebP",
    "avif": "AVIF", "tif": "TIFF", "tiff": "TIFF", "psd": "PSD", "pdf": "PDF", "gif": "GIF",
}
QUALITY_FORMATS = {"JPEG", "HEIC", "WebP", "AVIF"}


def die(msg):
    sys.exit("pxm-compose: " + msg)


def s(text):
    """AppleScript string literal."""
    text = str(text).replace("\\", "\\\\").replace('"', '\\"')
    parts = re.split(r"\r\n|\r|\n", text)
    return " & linefeed & ".join('"%s"' % p for p in parts)


def color(value):
    m = re.fullmatch(r"#?([0-9a-fA-F]{6})", str(value))
    if not m:
        die("colour must be #rrggbb: %r" % value)
    h = m.group(1)
    return "{%s}" % ", ".join(str(int(h[i:i + 2], 16) * 257) for i in (0, 2, 4))


def num(layer, key, default=None):
    v = layer.get(key, default)
    if v is None:
        die("layer %r needs %r" % (layer.get("name", layer.get("type")), key))
    if not isinstance(v, (int, float)):
        die("%r must be a number" % key)
    return v


def common(layer, var):
    out = []
    if "name" in layer:
        out.append("set name of %s to %s" % (var, s(layer["name"])))
    if "opacity" in layer:
        out.append("set opacity of %s to %d" % (var, num(layer, "opacity")))
    if "rotation" in layer:
        out.append("set rotation of %s to %s" % (var, num(layer, "rotation")))
    return out


def image_layer(layer, i, base, W, H):
    path = os.path.join(base, layer.get("file") or die("image layer needs 'file'"))
    if not os.path.isfile(path):
        die("image not found: " + path)
    v = "L%d" % i
    fx, fy = num(layer, "x", 0), num(layer, "y", 0)
    fw, fh = num(layer, "width", W), num(layer, "height", H)
    fit = layer.get("fit", "cover")
    if fit not in ("cover", "contain", "none"):
        die("fit must be cover, contain or none")
    out = [
        "set %s to make new image layer at beginning of layers with properties {file:(%s as POSIX file)}"
        % (v, s(os.path.abspath(path))),
    ]
    if layer.get("remove_background"):
        out.append("remove background %s" % v)
    if fit == "none":
        out.append("set position of %s to {%s, %s}" % (v, fx, fy))
    else:
        pick = "max" if fit == "cover" else "min"
        out += [
            "set constrain proportions of %s to true" % v,
            "set w0 to (width of %s)" % v,
            "set h0 to (height of %s)" % v,
            "set k to my %s(%s / w0, %s / h0)" % (pick, fw, fh),
            "set width of %s to (w0 * k)" % v,
            "set position of %s to {round (%s + (%s - w0 * k) / 2), round (%s + (%s - h0 * k) / 2)}"
            % (v, fx, fw, fy, fh),
        ]
    return out + common(layer, v)


def shape_layer(layer, i):
    v = "L%d" % i
    cls = SHAPES[layer["type"]]
    props = "width:%s, height:%s, position:{%s, %s}" % (
        num(layer, "width"), num(layer, "height"), num(layer, "x", 0), num(layer, "y", 0))
    if layer["type"] == "rounded-rect":
        props += ", corner radius:%s" % num(layer, "radius", 20)
    if layer["type"] in ("polygon", "star") and "sides" in layer:
        props += ", sides:%d" % num(layer, "sides")
    out = ["set %s to make new %s at beginning of layers with properties {%s}" % (v, cls, props)]
    st = "styles of %s" % v
    if "fill" in layer:
        out.append("set fill color of %s to %s" % (st, color(layer["fill"])))
    if "fill_opacity" in layer:
        out.append("set fill opacity of %s to %d" % (st, num(layer, "fill_opacity")))
    if "stroke" in layer:
        out.append("set stroke color of %s to %s" % (st, color(layer["stroke"])))
        out.append("set stroke width of %s to %s" % (st, num(layer, "stroke_width", 2)))
    return out + common(layer, v)


def text_layer(layer, i, W):
    v = "L%d" % i
    if "text" not in layer:
        die("text layer needs 'text'")
    out = ["set %s to make new text layer at beginning of layers with properties {text content:%s}"
           % (v, s(layer["text"]))]
    tc = []
    if "font" in layer:
        tc.append("set its font to %s" % s(layer["font"]))
    if "size" in layer:
        tc.append("set its size to %d" % num(layer, "size"))
    tc.append("set its color to %s" % color(layer.get("color", "#000000")))
    out.append("tell text content of %s\n%s\nend tell" % (v, "\n".join(tc)))
    align = layer.get("align")
    if align:
        if align not in ("left", "center", "right"):
            die("align must be left, center or right")
        out.append("set horizontal alignment of %s to %s" % (v, align))
    if align or "width" in layer:
        out.append("set width of %s to %s" % (v, num(layer, "width", W)))
    if "x" in layer or "y" in layer:
        out.append("set position of %s to {%s, %s}" % (v, num(layer, "x", 0), num(layer, "y", 0)))
    return out + common(layer, v)


def export_lines(spec, base):
    out = []
    files = []
    for e in spec.get("export") or die("spec needs an 'export' list"):
        path = os.path.abspath(os.path.join(base, e["path"]))
        ext = os.path.splitext(path)[1].lower().lstrip(".")
        files.append(path)
        if ext == "pxd":
            out.append("save d in (%s as POSIX file)" % s(path))
            continue
        fmt = EXPORT_FORMATS.get(e.get("format", ext).lower())
        if not fmt:
            die("cannot export %r (use png, jpg, heic, webp, avif, tiff, psd, pdf, gif, pxd)" % path)
        opts = ""
        if "quality" in e and fmt in QUALITY_FORMATS:
            opts = " with properties {compression factor:%d}" % num(e, "quality")
        out.append("export d to (%s as POSIX file) as %s%s" % (s(path), fmt, opts))
    return out, files


REPORT = r'''
set rows to {}
repeat with L in (reverse of (layers of d as list))
	set p to position of L
	set row to "{\"class\":\"" & (class of L as text) & "\",\"name\":" & my q(name of L) & ¬
		",\"x\":" & ((item 1 of p) as integer) & ",\"y\":" & ((item 2 of p) as integer) & ¬
		",\"width\":" & ((width of L) as integer) & ",\"height\":" & ((height of L) as integer)
	if class of L is text layer then
		set row to row & ",\"text\":" & my q((text content of L) as text) & ",\"font\":" & my q(font of text content of L) & ",\"size\":" & (size of text content of L)
	end if
	set end of rows to row & "}"
end repeat
set AppleScript's text item delimiters to ","
set report to "{\"width\":" & ((width of d) as integer) & ",\"height\":" & ((height of d) as integer) & ",\"layers\":[" & (rows as text) & "]}"
set AppleScript's text item delimiters to ""
'''

HELPERS = r'''
on max(a, b)
	if a > b then return a
	return b
end max
on min(a, b)
	if a < b then return a
	return b
end min
on q(t)
	set AppleScript's text item delimiters to "\\"
	set parts to text items of t
	set AppleScript's text item delimiters to "\\\\"
	set t to parts as text
	set AppleScript's text item delimiters to "\""
	set parts to text items of t
	set AppleScript's text item delimiters to "\\\""
	set t to parts as text
	set AppleScript's text item delimiters to linefeed
	set parts to text items of t
	set AppleScript's text item delimiters to "\\n"
	set t to parts as text
	set AppleScript's text item delimiters to ""
	return "\"" & t & "\""
end q
'''


def build(spec, base, keep_open):
    W, H = int(num(spec, "width")), int(num(spec, "height"))
    body = []
    bg = spec.get("background", "#ffffff")
    body.append("set bg to last layer")
    if bg == "transparent":
        transparent = True
    else:
        transparent = False
        if str(bg).lower() not in ("#ffffff", "white"):
            body += ["set current layer to bg", "fill d with color %s" % color(bg)]
    for i, layer in enumerate(spec.get("layers", [])):
        t = layer.get("type")
        if t == "image":
            body += image_layer(layer, i, base, W, H)
        elif t in SHAPES:
            body += shape_layer(layer, i)
        elif t == "text":
            body += text_layer(layer, i, W)
        else:
            die("unknown layer type %r (image, text, %s)" % (t, ", ".join(SHAPES)))
    if transparent:
        body.append("delete bg")
    exports, files = export_lines(spec, base)
    script = [
        "with timeout of 7200 seconds",
        'tell application "Pixelmator Pro"',
        "set d to make new document with properties {width:%d, height:%d}" % (W, H),
        "try",
        "tell d",
        *body,
        "end tell",
        *exports,
        REPORT,
        "on error msg number n",
        "close d saving no" if not keep_open else "",
        "error msg number n",
        "end try",
        "close d saving no" if not keep_open else "",
        "end tell",
        "end timeout",
        "return report",
    ]
    return "\n".join(script) + "\n" + HELPERS, files


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--dry-run", action="store_true", help="print the generated AppleScript")
    ap.add_argument("--keep-open", action="store_true", help="leave the document open in Pixelmator Pro")
    ap.add_argument("--timeout", type=int, default=600)
    a = ap.parse_args()
    with open(a.spec) as f:
        spec = json.load(f)
    script, files = build(spec, os.path.dirname(os.path.abspath(a.spec)), a.keep_open)
    if a.dry_run:
        print(script)
        return 0
    for path in files:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    r = subprocess.run(["bash", os.path.join(HERE, "pxm.sh"), "run", "-", "--timeout", str(a.timeout)],
                       input=script, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        return r.returncode
    report = json.loads(r.stdout)
    report["files"] = [{"path": p, "exists": os.path.isfile(p)} for p in files]
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if all(f["exists"] for f in report["files"]) else 1


if __name__ == "__main__":
    sys.exit(main())
