#!/usr/bin/env python3
"""Verify exported images without Pixelmator Pro: format, pixel size, alpha, JPEG quality.

usage: pxm-info.py FILE_OR_DIR... [--layers]

One JSON line per image:
  format, width, height, bytes, has_alpha,
  alpha {tl,tr,bl,br,c}   alpha (0-255) of the four corners and the centre pixel,
                          so a cut-out reads as transparent corners + opaque centre
  transparent_ratio       share of nearly transparent pixels (alpha images only); a
                          good cut-out is well between 0 and 1
  jpeg_quality            the macOS/ImageIO quality (1-100) whose quant table matches;
                          this is the scale Pixelmator Pro's "compression factor" and
                          sips formatOptions use. A range [lo, hi] when several match.
  jpeg_ijg_quality        the same table on the libjpeg/IJG scale (ImageIO 85 = IJG 95)
.pxd files are opened in Pixelmator Pro (read-only, closed without saving) and listed
with their layers (bottom -> top); --layers does the same for PSD.
"""
import json
import os
import platform
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
EXTS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".tif", ".tiff", ".webp", ".gif",
        ".bmp", ".psd", ".avif", ".pxd", ".jp2"}

# IJG (libjpeg) standard luminance quantisation table, natural order is irrelevant
# here because both tables are compared element-wise in the same (zig-zag) order.
STD_LUMA = [16, 11, 12, 14, 12, 10, 16, 14, 13, 14, 18, 17, 16, 19, 24, 40, 26, 24, 22, 22,
            24, 49, 35, 37, 29, 40, 58, 51, 61, 60, 57, 51, 56, 55, 64, 72, 92, 78, 64, 68,
            87, 69, 55, 56, 80, 109, 81, 87, 95, 98, 103, 104, 103, 62, 77, 113, 121, 112,
            100, 120, 92, 101, 103, 99]
ZIGZAG = [0, 1, 8, 16, 9, 2, 3, 10, 17, 24, 32, 25, 18, 11, 4, 5, 12, 19, 26, 33, 40, 48,
          41, 34, 27, 20, 13, 6, 7, 14, 21, 28, 35, 42, 49, 56, 57, 50, 43, 36, 29, 22, 15,
          23, 30, 37, 44, 51, 58, 59, 52, 45, 38, 31, 39, 46, 53, 60, 61, 54, 47, 55, 62, 63]

PIXELS_JXA = r'''
ObjC.import('AppKit');
function run(argv) {
  const rep = $.NSBitmapImageRep.imageRepWithContentsOfFile(argv[0]);
  if (!rep || rep.isNil()) return "{}";
  const w = rep.pixelsWide, h = rep.pixelsHigh;
  const pts = {tl:[0,0], tr:[w-1,0], bl:[0,h-1], br:[w-1,h-1], c:[Math.floor(w/2), Math.floor(h/2)]};
  const o = {has_alpha: rep.hasAlpha, alpha: {}};
  for (const k in pts) {
    const c = rep.colorAtXY(pts[k][0], pts[k][1]);
    o.alpha[k] = c.isNil() ? null : Math.round(c.alphaComponent * 255);
  }
  if (rep.hasAlpha) {  // share of (nearly) transparent pixels on a 64x64 sample grid
    let clear = 0, n = 0;
    for (let i = 0; i < 64; i++) for (let j = 0; j < 64; j++) {
      const c = rep.colorAtXY(Math.floor((i + 0.5) * w / 64), Math.floor((j + 0.5) * h / 64));
      n++; if (!c.isNil() && c.alphaComponent < 0.06) clear++;
    }
    o.transparent_ratio = Math.round(clear / n * 1000) / 1000;
  }
  return JSON.stringify(o);
}
'''

LAYERS_AS = r'''
on run argv
	set f to (item 1 of argv) as POSIX file -- coerce outside the tell (sandbox grant)
	tell application "Pixelmator Pro"
		set d to open f
		try
			set rows to {}
			repeat with L in (reverse of (layers of d as list))
				set row to "{\"class\":\"" & (class of L as text) & "\",\"name\":" & my q(name of L) & ",\"visible\":" & (visible of L)
				if class of L is text layer then set row to row & ",\"text\":" & my q((text content of L) as text) & ",\"font\":" & my q(font of text content of L) & ",\"size\":" & (size of text content of L)
				set end of rows to row & "}"
			end repeat
			set AppleScript's text item delimiters to ","
			set out to "{\"width\":" & ((width of d) as integer) & ",\"height\":" & ((height of d) as integer) & ",\"layers\":[" & (rows as text) & "]}"
			set AppleScript's text item delimiters to ""
		on error msg number n
			close d saving no
			error msg number n
		end try
		close d saving no
	end tell
	return out
end run
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


def sips(path):
    out = subprocess.run(["sips", "-g", "format", "-g", "pixelWidth", "-g", "pixelHeight", path],
                         capture_output=True, text=True).stdout
    info = {}
    for line in out.splitlines()[1:]:
        if ":" in line:
            k, v = line.strip().split(":", 1)
            info[k.strip()] = v.strip()
    return info


def luma_table(path):
    """First 8-bit luminance DQT table (zig-zag order) of a JPEG, or None."""
    with open(path, "rb") as f:
        data = f.read()
    i = 2
    while i + 4 <= len(data) and data[i] == 0xFF:
        marker, length = data[i + 1], struct.unpack(">H", data[i + 2:i + 4])[0]
        if marker == 0xDB:
            seg = data[i + 4:i + 2 + length]
            if seg and seg[0] == 0:
                return list(seg[1:65])
        if marker == 0xDA:
            break
        i += 2 + length
    return None


def ijg_quality(table):
    std = [STD_LUMA[z] for z in ZIGZAG]
    return min(range(1, 101), key=lambda q: sum(
        abs(max(1, min(255, (v * (5000 // q if q < 50 else 200 - 2 * q) + 50) // 100)) - t)
        for v, t in zip(std, table)))


def imageio_tables():
    """Quant tables ImageIO writes at quality 1-100, built once per macOS version with sips."""
    cache = os.path.expanduser("~/Library/Caches/pxm-jpeg-tables-%s.json" % platform.mac_ver()[0])
    try:
        with open(cache) as f:
            return {int(k): v for k, v in json.load(f).items()}
    except (OSError, ValueError):
        pass
    tables = {}
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "src.bmp")  # 8x8 grey 24-bit BMP
        row = bytes([128, 128, 128] * 8)
        pix = row * 8
        hdr = struct.pack("<2sIHHI", b"BM", 54 + len(pix), 0, 0, 54)
        dib = struct.pack("<IiiHHIIiiII", 40, 8, 8, 1, 24, 0, len(pix), 2835, 2835, 0, 0)
        with open(src, "wb") as f:
            f.write(hdr + dib + pix)
        for q in range(1, 101):
            out = os.path.join(tmp, "q%d.jpg" % q)
            subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", str(q), src,
                            "--out", out], capture_output=True)
            t = luma_table(out) if os.path.isfile(out) else None
            if t:
                tables[q] = t
    try:
        with open(cache, "w") as f:
            json.dump(tables, f)
    except OSError:
        pass
    return tables


def apple_quality(table):
    hits = [q for q, t in sorted(imageio_tables().items()) if t == table]
    if not hits:
        return None
    return hits[0] if len(hits) == 1 else [hits[0], hits[-1]]


def image_info(path):
    s = sips(path)
    r = {"file": path, "format": s.get("format"), "bytes": os.path.getsize(path)}
    try:
        r["width"], r["height"] = int(s["pixelWidth"]), int(s["pixelHeight"])
    except (KeyError, ValueError):
        r["error"] = "not an image sips can read"
        return r
    px = subprocess.run(["osascript", "-l", "JavaScript", "-e", PIXELS_JXA, path],
                        capture_output=True, text=True)
    if px.returncode == 0 and px.stdout.strip():
        r.update(json.loads(px.stdout))
    if r["format"] == "jpeg":
        table = luma_table(path)
        if table:
            r["jpeg_quality"] = apple_quality(table)
            r["jpeg_ijg_quality"] = ijg_quality(table)
    return r


def doc_info(path):
    p = subprocess.run(["bash", os.path.join(HERE, "pxm.sh"), "run", "-", "--timeout", "120", path],
                       input=LAYERS_AS, capture_output=True, text=True)
    r = {"file": path, "bytes": os.path.getsize(path)}
    if p.returncode == 0:
        r.update(json.loads(p.stdout))
    else:
        r["error"] = p.stderr.strip()
    return r


def main():
    args = [x for x in sys.argv[1:] if x != "--layers"]
    layers = "--layers" in sys.argv
    if not args or "-h" in args or "--help" in args:
        print(__doc__)
        return 64
    files = []
    for a in args:
        if os.path.isdir(a):
            for root, dirs, names in os.walk(a):
                dirs.sort()
                files += [os.path.join(root, n) for n in sorted(names)
                          if os.path.splitext(n)[1].lower() in EXTS and not n.startswith(".")]
        else:
            files.append(a)
    rc = 0
    for f in files:
        if not os.path.isfile(f):
            print(json.dumps({"file": f, "error": "missing"}))
            rc = 1
            continue
        ext = os.path.splitext(f)[1].lower()
        f = os.path.abspath(f)
        r = doc_info(f) if ext == ".pxd" or (layers and ext == ".psd") else image_info(f)
        rc |= 1 if "error" in r else 0
        print(json.dumps(r, ensure_ascii=False))
    return rc


if __name__ == "__main__":
    sys.exit(main())
