#!/usr/bin/env python3
"""Shared plumbing for the Keynote scripts: run keynote_ops.applescript, diagnose a
blocked Keynote, map localized layout names to English ones, and track the
documents a run opened so they can be closed.

Also a small CLI:
  python3 keynote_osa.py --layouts THEME_ID  index, English name, localized name, shape
  python3 keynote_osa.py --dialog            detect a modal Keynote alert, screenshot it
  python3 keynote_osa.py --close-leftovers   close documents a killed run left open

Standard library only; runs on the macOS system python3 (3.9).
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
OPS = os.path.join(HERE, "keynote_ops.applescript")
BUNDLE_ID = "com.apple.Keynote"
FORMATS = ("pdf", "pptx", "png", "jpeg", "tiff", "m4v")
IMAGE_FORMATS = ("png", "jpeg", "tiff")
DEFAULT_THEME = "Application/21_BasicWhite/Standard"
STATE = os.path.join(tempfile.gettempdir(), "keynote-skill-open.txt")
TIMEOUT = int(os.environ.get("KEYNOTE_TIMEOUT", "300"))


class KeynoteError(Exception):
    pass


def unesc(s):
    """Undo keynote_ops esc(): \\n, \\t and \\\\ back to characters."""
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            nxt = s[i + 1]
            out.append({"n": "\n", "t": "\t", "\\": "\\"}.get(nxt, "\\" + nxt))
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def norm_text(s):
    """Keynote separates paragraphs with CR (and U+2029 / U+2028 in some exports)."""
    for a in ("\r\n", "\r", " ", " "):
        s = s.replace(a, "\n")
    return s


def check_key_file(path):
    """A .key is a zip or a package directory. Opening anything else makes Keynote
    show a modal "can't be opened" alert that blocks every later Apple Event."""
    if not os.path.exists(path):
        raise KeynoteError("not found: %s" % path)
    if os.path.isdir(path):
        if not os.path.exists(os.path.join(path, "Index.zip")) and not os.path.isdir(
            os.path.join(path, "Index")
        ):
            raise KeynoteError("not a Keynote package (no Index): %s" % path)
    elif not zipfile.is_zipfile(path):
        raise KeynoteError("not a Keynote file (not a zip or package): %s" % path)


def copy_key(src, dst):
    if os.path.isdir(src):
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)


def remove_path(path):
    if os.path.isdir(path) and not os.path.islink(path):
        shutil.rmtree(path)
    elif os.path.exists(path):
        os.remove(path)


def real(path):
    """Keynote reports /private/tmp for /tmp; realpath keeps open-document checks exact.
    The file itself may not exist yet, so resolve its folder."""
    path = os.path.abspath(path)
    return os.path.join(os.path.realpath(os.path.dirname(path)), os.path.basename(path))


def _track(paths, opened):
    try:
        existing = set()
        if os.path.exists(STATE):
            with open(STATE, encoding="utf-8") as fh:
                existing = {line.rstrip("\n") for line in fh if line.strip()}
        existing = existing | set(paths) if opened else existing - set(paths)
        with open(STATE, "w", encoding="utf-8") as fh:
            fh.write("".join(p + "\n" for p in sorted(existing)))
    except OSError:
        pass


def run_ops(op, args, docs=()):
    """Run one keynote_ops op. docs = paths the op will open (tracked for cleanup)."""
    docs = [real(d) for d in docs]
    _track(docs, True)
    env = dict(os.environ, KEYNOTE_TIMEOUT=str(TIMEOUT))
    try:
        proc = subprocess.run(
            ["osascript", OPS, op] + [str(a) for a in args],
            capture_output=True,
            text=True,
            env=env,
            timeout=TIMEOUT + 30,
        )
    except subprocess.TimeoutExpired:
        raise KeynoteError("osascript did not return in %ss. %s" % (TIMEOUT + 30, dialog_hint()))
    err = proc.stderr.strip()
    if proc.returncode != 0:
        if "-1712" in err:  # AppleEvent timed out: almost always a modal dialog
            raise KeynoteError("Keynote did not answer (timeout). %s" % dialog_hint())
        if "-1743" in err:
            raise KeynoteError(
                "not allowed to control Keynote: grant it in System Settings > "
                "Privacy & Security > Automation, then retry"
            )
        raise KeynoteError(err or "osascript failed with code %d" % proc.returncode)
    _track(docs, False)
    return proc.stdout.rstrip("\n")


def rows(out):
    """ops output -> list of [tag, field, ...] with text fields unescaped."""
    return [[unesc(f) for f in line.split("\t")] for line in out.split("\n") if line]


# ------------------------------------------------------------------ layouts

def _strings_tables():
    """{lproj: {English: localized}} from the app's template strings, cached per run."""
    if hasattr(_strings_tables, "cache"):
        return _strings_tables.cache
    app = find_app()
    tables = {}
    if app:
        for f in glob.glob(os.path.join(app, "Contents/Resources/*.lproj/TSATemplateLocalizable.strings")):
            lang = os.path.basename(os.path.dirname(f))[:-6]
            proc = subprocess.run(["plutil", "-convert", "json", "-o", "-", f],
                                  capture_output=True, text=True)
            if proc.returncode == 0:
                try:
                    tables[lang] = json.loads(proc.stdout)
                except ValueError:
                    pass
    _strings_tables.cache = tables
    return tables


def _clean(name):
    # Localized names carry soft hyphens (U+00AD) and stray trailing spaces.
    return name.replace("­", "").strip()


def english_names(localized):
    """Localized layout names (one theme) -> English names, or the name itself when
    no translation table matches (an English UI, or a custom theme)."""
    best, best_hits = {}, 0
    for lang, table in _strings_tables().items():
        rev = {}
        for en, loc in table.items():
            rev.setdefault(_clean(loc), []).append(_clean(en))
        hits = sum(1 for n in localized if _clean(n) in rev)
        if hits > best_hits:
            best, best_hits = rev, hits
    out = []
    for n in localized:
        cands = best.get(_clean(n))
        # Several English keys can share one translation ("Statement", "Statement ");
        # after cleaning they are usually identical, else take the shortest.
        out.append(min(cands, key=len) if cands else _clean(n))
    return out


def theme_layouts(theme_id):
    """-> {"width", "height", "layouts": [{index, name, localized, title, body, images}]}
    Probing takes a scratch document and several seconds, so the result is cached per
    theme and Keynote version (the UI language is part of the key via the names)."""
    app = find_app() or ""
    version = ""
    if app:
        version = subprocess.run(
            ["defaults", "read", os.path.join(app, "Contents/Info"), "CFBundleShortVersionString"],
            capture_output=True, text=True).stdout.strip()
    cache = os.path.join(tempfile.gettempdir(), "keynote-layouts-%s-%s.json" % (
        "".join(c if c.isalnum() else "_" for c in theme_id), version))
    lang = subprocess.run(["defaults", "read", "-g", "AppleLanguages"],
                          capture_output=True, text=True).stdout
    try:
        with open(cache, encoding="utf-8") as fh:
            res = json.load(fh)
        if res.get("languages") == lang:
            return res
    except (OSError, ValueError):
        pass
    res = _probe_layouts(theme_id)
    res["languages"] = lang
    try:
        with open(cache, "w", encoding="utf-8") as fh:
            json.dump(res, fh, ensure_ascii=False)
    except OSError:
        pass
    return res


def _probe_layouts(theme_id):
    tmp = tempfile.mkdtemp(prefix="keynote-layouts-")
    scratch = os.path.join(os.path.realpath(tmp), "layouts.key")
    try:
        out = run_ops("layouts", [theme_id, scratch], docs=[scratch])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    res = {"theme": theme_id, "layouts": []}
    locs = []
    for r in rows(out):
        if r[0] == "SIZE":
            res["width"], res["height"] = int(float(r[1])), int(float(r[2]))
        elif r[0] == "LAYOUT":
            locs.append(r[2])
            res["layouts"].append({
                "index": int(r[1]), "localized": _clean(r[2]),
                "title": r[3] == "true", "body": r[4] == "true", "images": int(r[5]),
            })
    for lay, en in zip(res["layouts"], english_names(locs)):
        lay["name"] = en
    return res


# Roles the outline builder asks for -> English layout names, first match wins.
# Themes differ: Basic White has "Section", Gradient has "Title - Center" instead.
ROLE_CHAIN = {
    "title": ["Title", "Title - Center"],
    "bullets": ["Title & Bullets", "Title, Text & Bullets", "Title & Text", "Bullets"],
    "bullets-photo": ["Title, Bullets & Photo", "Title, Bullets & Image", "Title & Photo",
                      "Title & Photo Alt", "Title & Bullets"],
    "photo": ["Photo", "Photo - Horizontal", "Photo - 1 Up", "Title & Photo"],
    "title-photo": ["Title & Photo", "Title & Photo Alt", "Title, Bullets & Photo", "Photo"],
    "section": ["Section", "Title - Center", "Title"],
    "title-only": ["Title Only", "Title - Top", "Title"],
    "statement": ["Statement", "Big Fact", "Title - Center", "Title"],
    "quote": ["Quote", "Statement", "Title - Center"],
    "agenda": ["Agenda", "Title & Bullets", "Bullets"],
    "blank": ["Blank"],
}


def resolve_layout(layouts, want):
    """want = role, English name, localized name or 1-based index -> layout dict."""
    ls = layouts["layouts"]
    w = str(want).strip()
    if w.isdigit():
        i = int(w)
        if 1 <= i <= len(ls):
            return ls[i - 1]
        raise KeynoteError("layout index %s out of range 1..%d" % (w, len(ls)))
    low = _clean(w).lower()
    # Roles win over same-named layouts: the role "bullets" means Title & Bullets, while
    # the layout called "Bullets" has no title. Use its index to get that one.
    if low not in ROLE_CHAIN:
        for lay in ls:
            if low in (lay["name"].lower(), lay["localized"].lower()):
                return lay
    if low in ROLE_CHAIN:
        for name in ROLE_CHAIN[low]:
            for lay in ls:
                if lay["name"].lower() == name.lower():
                    return lay
        # Fall back on the placeholder shape, which every theme has in some form.
        shape = {"title": (True, True, 0), "section": (True, False, 0),
                 "title-only": (True, False, 0), "blank": (False, False, 0)}.get(low)
        for lay in ls:
            if shape and (lay["title"], lay["body"], lay["images"]) == shape:
                return lay
        for lay in ls:
            if lay["title"] and lay["body"] and (lay["images"] > 0) == ("photo" in low):
                return lay
        return ls[0]
    raise KeynoteError("no layout %r; see keynote.sh --layouts %s" % (want, layouts["theme"]))


def themes():
    out = subprocess.run(
        ["osascript", "-l", "JavaScript", "-e",
         "const K = Application('%s'); K.themes().map(t => t.id() + '\\t' + t.name()).join('\\n');"
         % BUNDLE_ID],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        raise KeynoteError(out.stderr.strip())
    return [line.split("\t", 1) for line in out.stdout.strip().split("\n") if "\t" in line]


def resolve_theme(want):
    """Theme id, or a (localized) theme name -> theme id."""
    if not want:
        return DEFAULT_THEME
    ts = themes()
    for tid, name in ts:
        if want in (tid, name) or want.lower() == name.lower():
            return tid
    for tid, name in ts:  # "BasicWhite" / "Basic White" against the id
        key = want.replace(" ", "").lower()
        if key in tid.replace("_", "").lower():
            return tid
    raise KeynoteError("no theme %r; list them with keynote.sh --themes" % want)


def find_app():
    proc = subprocess.run(["mdfind", "kMDItemCFBundleIdentifier == '%s'" % BUNDLE_ID],
                          capture_output=True, text=True)
    for line in proc.stdout.splitlines():
        if line.endswith(".app") and os.path.isdir(line):
            return line
    for app in sorted(glob.glob("/Applications/Keynote*.app")):
        return app
    return None


# ------------------------------------------------------------------ dialogs

_WINDOWS_JXA = r"""
ObjC.import("CoreGraphics");
const l = ObjC.deepUnwrap(ObjC.castRefToObject($.CGWindowListCopyWindowInfo(1, 0)));
// Alerts can sit on the normal layer (0) or the modal-panel layer (8); both count.
l.filter(w => w.kCGWindowOwnerName && /^Keynote/.test(w.kCGWindowOwnerName) && [0, 8].includes(w.kCGWindowLayer))
 .map(w => [w.kCGWindowNumber, w.kCGWindowBounds.Width, w.kCGWindowBounds.Height, w.kCGWindowName || ""].join("\t"))
 .join("\n");
"""


def find_dialogs():
    """On-screen, untitled, alert-sized Keynote windows. Needs no Accessibility access."""
    proc = subprocess.run(
        ["osascript", "-l", "JavaScript", "-e", _WINDOWS_JXA], capture_output=True, text=True
    )
    hits = []
    for line in proc.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        wid, w, h, name = parts[0], float(parts[1]), float(parts[2]), parts[3]
        if not name and 150 < w < 700 and 100 < h < 600:
            hits.append(wid)
    return hits


def dialog_hint():
    hits = find_dialogs()
    if not hits:
        return "No Keynote dialog is visible; the deck may be very large, or Keynote is busy."
    shots = []
    for wid in hits:
        shot = os.path.join(tempfile.gettempdir(), "keynote-dialog-%s.png" % wid)
        if subprocess.run(["screencapture", "-x", "-o", "-l", wid, shot]).returncode == 0:
            shots.append(shot)
    return (
        "Keynote is showing a modal dialog, which blocks all scripting until someone "
        "clicks it away. Screenshot: %s - read it and ask the user to dismiss it."
        % (", ".join(shots) or "unavailable")
    )


def close_leftovers():
    if not os.path.exists(STATE):
        return "CLOSED\t0"
    with open(STATE, encoding="utf-8") as fh:
        paths = [line.rstrip("\n") for line in fh if line.strip()]
    out = run_ops("close", paths) if paths else "CLOSED\t0"
    os.remove(STATE)
    return out


# ------------------------------------------------------------------ export options


def add_export_args(parser):
    g = parser.add_argument_group("export options")
    g.add_argument("--notes", action="store_true", help="PDF: each slide with its presenter notes")
    g.add_argument("--handouts", action="store_true", help="PDF: handout layout")
    g.add_argument("--include-skipped", action="store_true",
                   help="PDF/images: include skipped slides (PPTX always keeps them, hidden)")
    g.add_argument("--all-stages", action="store_true", help="PDF/images: one page per build stage")
    g.add_argument("--slide-numbers", action="store_true", help="PDF: print slide numbers")
    g.add_argument("--comments", action="store_true", help="PDF: include comments")
    g.add_argument("--password", help="PDF/PPTX open password")
    g.add_argument("--password-hint")
    g.add_argument("--pdf-quality", choices=("good", "better", "best"))
    g.add_argument("--movie-format", choices=("360p", "540p", "720p", "1080p", "2160p", "native"))
    g.add_argument("--movie-codec", choices=("h264", "hevc", "prores422", "prores4444"))


def export_opt_args(ns):
    """Argument namespace -> ["O", key, value, ...] for keynote_ops."""
    out = []
    for key in ("password", "password_hint", "pdf_quality", "movie_format", "movie_codec"):
        val = getattr(ns, key)
        if val:
            out += ["O", key.replace("_", "-"), val]
    for key in ("notes", "handouts", "include_skipped", "all_stages", "slide_numbers", "comments"):
        if getattr(ns, key):
            out += ["O", key.replace("_", "-"), "true"]
    return out


def format_of(path):
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    ext = {"jpg": "jpeg", "tif": "tiff", "mov": "m4v", "mp4": "m4v"}.get(ext, ext)
    if ext not in FORMATS:
        raise KeynoteError("unsupported export extension .%s (use %s)" % (ext, ", ".join(FORMATS)))
    return ext


def image_files(dst):
    """Slide-image export writes a folder DST holding DST-stem.001.png, ... ."""
    return sorted(glob.glob(os.path.join(dst, "*.*")))


def main(argv):
    try:
        if len(argv) == 2 and argv[0] == "--layouts":
            res = theme_layouts(resolve_theme(argv[1]))
            print("# %s  %sx%s" % (res["theme"], res.get("width"), res.get("height")))
            for lay in res["layouts"]:
                shape = "%s%s%s" % ("T" if lay["title"] else "-", "B" if lay["body"] else "-",
                                    lay["images"] or "")
                print("%d\t%s\t%s\t%s" % (lay["index"], lay["name"], lay["localized"], shape))
            return 0
        if argv == ["--dialog"]:
            hits = find_dialogs()
            print(dialog_hint() if hits else "no Keynote dialog visible")
            return 1 if hits else 0
        if argv == ["--close-leftovers"]:
            print(close_leftovers())
            return 0
    except KeynoteError as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
