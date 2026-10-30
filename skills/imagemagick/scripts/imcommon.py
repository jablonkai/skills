"""Shared helpers for the imagemagick skill scripts (stdlib only, Python 3.9+).

Every call goes through `run()` with an argument list, never a shell, so geometry such
as `1600x1600>` needs no quoting. Outputs always go to a separate folder: `out_dir()`
refuses the input folder, and `Originals` checksums the inputs before and after a job.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".heic", ".heif", ".tif", ".tiff",
             ".gif", ".bmp", ".jxl", ".jp2", ".psd", ".dng", ".cr2", ".nef", ".arw"}
FORMAT_EXT = {"jpeg": "jpg", "jpg": "jpg", "png": "png", "webp": "webp", "avif": "avif",
              "heic": "heic", "tiff": "tif", "tif": "tif", "gif": "gif", "jxl": "jxl"}
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
]
SRGB_PROFILES = [
    "/System/Library/ColorSync/Profiles/sRGB Profile.icc",
    "/usr/share/color/icc/colord/sRGB.icc",
    "/usr/share/color/icc/sRGB.icc",
]
INSTALL = "brew install imagemagick  (Debian/Ubuntu: apt install imagemagick; needs ImageMagick 7)"


def die(msg, code=2):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def magick_path():
    path = shutil.which("magick")
    if not path:
        die(f"magick (ImageMagick 7) not found. Install: {INSTALL}", 3)
    return path


def run(args, ok=(0,)):
    """Run `magick ARGS`; returns CompletedProcess. Exits with its stderr unless rc is in ok."""
    proc = subprocess.run([magick_path()] + [str(a) for a in args], capture_output=True,
                          text=True, errors="replace")
    if proc.returncode not in ok:
        die(f"magick {' '.join(str(a) for a in args[:3])}… exited {proc.returncode}: "
            f"{(proc.stderr or proc.stdout).strip()[:800]}")
    return proc


def emit(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


# --- fonts and profiles --------------------------------------------------------

def resolve_font(font=None):
    """A font *file*: Homebrew's ImageMagick has no fontconfig, so names like 'Arial' fail."""
    if font:
        if os.path.isfile(font):
            return font
        die(f"font file not found: {font} (pass a .ttf/.otf/.ttc path, not a font name)")
    env = os.environ.get("IM_FONT")
    if env and os.path.isfile(env):
        return env
    for f in FONT_CANDIDATES:
        if os.path.isfile(f):
            return f
    die("no font file found; pass --font /path/to/font.ttf or set IM_FONT")


def srgb_profile():
    for p in SRGB_PROFILES:
        if os.path.isfile(p):
            return p
    return None


def to_srgb_args(info):
    """Colour-managed sRGB conversion for one image, based on its identify() info.

    An embedded ICC profile (Adobe RGB, Display P3, CMYK) is converted through lcms by
    assigning the sRGB profile. `-colorspace sRGB` alone ignores the embedded profile and
    shifts CMYK colours badly, so it is only the fallback when no profile is available.
    """
    prof = srgb_profile()
    if info.get("icc") and prof:
        return ["-profile", prof]
    if info.get("colorspace") not in ("sRGB", "Gray", "Grey") or info.get("icc"):
        return ["-colorspace", "sRGB"]
    return []


# --- read-back -------------------------------------------------------------------

LOSSY = {"JPEG", "WEBP", "AVIF", "HEIC", "JXL", "JP2"}  # %Q on PNG is the zlib level, not a quality
FMT = "\t".join(["%m", "%w", "%h", "%[colorspace]", "%z", "%A", "%Q", "%[orientation]",
                 "%[profiles]", "%[icc:description]", "%n", "%[EXIF:GPS*]|", "%[EXIF:Make]"]) + "\n"


def identify(path):
    """First-frame facts for one image. Unknown properties come back empty, not as errors."""
    proc = subprocess.run([magick_path(), "identify", "-quiet", "-format", FMT, f"{path}[0]"],
                          capture_output=True, text=True, errors="replace")
    line = proc.stdout.splitlines()[0] if proc.stdout.strip() else ""
    if proc.returncode != 0 or not line:
        return {"file": str(path), "error": (proc.stderr or "unreadable").strip()[:300]}
    f = line.split("\t")
    f += [""] * (13 - len(f))
    profiles = [p for p in f[8].split(",") if p]
    return {
        "file": str(path), "format": f[0], "width": int(f[1]), "height": int(f[2]),
        "colorspace": f[3], "depth": int(f[4] or 0), "alpha": f[5] not in ("False", "Undefined", ""),
        "quality": int(f[6]) if f[6].isdigit() and f[6] != "0" and f[0] in LOSSY else None,
        "orientation": f[7] if f[7] not in ("Undefined", "TopLeft") else None,
        "profiles": profiles, "icc": f[9] or None, "frames": int(f[10] or 1),
        "exif": "exif" in profiles, "gps": bool(f[11].strip("|")),
        "size_bytes": os.path.getsize(path),
    }


def display_size(info):
    """Width x height as a viewer shows it (EXIF orientations 5-8 swap the axes)."""
    if info.get("orientation") in ("LeftTop", "RightTop", "RightBottom", "LeftBottom"):
        return info["height"], info["width"]
    return info["width"], info["height"]


# --- inputs and outputs ------------------------------------------------------------

def list_images(inputs, recursive=False):
    """Expand files and folders to image files by extension; hidden files are skipped."""
    found, skipped = [], []
    for item in inputs:
        if os.path.isdir(item):
            walker = os.walk(item) if recursive else [(item, [], os.listdir(item))]
            for root, dirs, files in walker:
                dirs[:] = [x for x in dirs if not x.startswith(".")]
                for f in sorted(files):
                    if f.startswith("."):
                        continue
                    p = os.path.join(root, f)
                    (found if os.path.splitext(f)[1].lower() in IMAGE_EXT else skipped).append(p)
        elif os.path.isfile(item):
            found.append(item)
        else:
            die(f"no such file or folder: {item}")
    if not found:
        die("no images found in the given inputs")
    return sorted(dict.fromkeys(found)), skipped


def out_dir(path, inputs):
    """Create the output folder; refuse one that holds any input (no in-place writes)."""
    real = os.path.realpath(path)
    for src in inputs:
        if os.path.dirname(os.path.realpath(src)) == real:
            die(f"output folder {path} contains the input {src}; pick a new folder "
                "(this skill never overwrites originals)")
    os.makedirs(path, exist_ok=True)
    return path


def out_name(src, outdir, ext=None, suffix="", inputs_root=None, create=True):
    stem, old = os.path.splitext(os.path.basename(src))
    rel = ""
    if inputs_root:
        rel = os.path.relpath(os.path.dirname(src), inputs_root)
        rel = "" if rel == "." else rel
    target_dir = os.path.join(outdir, rel)
    if create:
        os.makedirs(target_dir, exist_ok=True)
    return os.path.join(target_dir, f"{stem}{suffix}.{ext or old.lstrip('.')}")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Originals:
    """Checksums of the inputs taken before a job; `changed()` lists any that moved."""

    def __init__(self, files):
        self.sums = {f: sha256(f) for f in files}

    def changed(self):
        return [f for f, s in self.sums.items() if not os.path.exists(f) or sha256(f) != s]


def parse_size(text):
    m = re.fullmatch(r"(\d+)[xX](\d+)", text.strip())
    if not m:
        die(f"size must be WxH, got {text!r}")
    return int(m.group(1)), int(m.group(2))


def quality_args(fmt, quality, lossless=False):
    """Encoder options. -quality is on each encoder's own scale; WebP lossless is a define."""
    args = []
    if fmt == "webp" and lossless:
        args += ["-define", "webp:lossless=true"]
    elif quality is not None:
        args += ["-quality", str(quality)]
    if fmt == "webp":
        args += ["-define", "webp:method=6"]
    if fmt == "jpg":
        args += ["-sampling-factor", "4:2:0", "-interlace", "JPEG"]
    return args
