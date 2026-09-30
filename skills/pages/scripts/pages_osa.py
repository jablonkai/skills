#!/usr/bin/env python3
"""Shared plumbing for the Pages scripts: run pages_ops.applescript, diagnose a
blocked Pages, and track the documents a run opened so they can be closed.

Also a small CLI:
  python3 pages_osa.py --dialog          detect a modal Pages alert, screenshot it
  python3 pages_osa.py --close-leftovers close documents a killed run left open

Standard library only; runs on the macOS system python3 (3.9).
"""
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
OPS = os.path.join(HERE, "pages_ops.applescript")
BUNDLE_ID = "com.apple.Pages"
FORMATS = ("pdf", "docx", "epub", "rtf", "txt")
STATE = os.path.join(tempfile.gettempdir(), "pages-skill-open.txt")
TIMEOUT = int(os.environ.get("PAGES_TIMEOUT", "300"))


class PagesError(Exception):
    pass


def norm_text(s):
    """Pages separates paragraphs with CR (and U+2029 in some exports)."""
    return s.replace("\r\n", "\n").replace("\r", "\n").replace(" ", "\n")


def check_pages_file(path):
    """A .pages is a package directory or a zip. Opening anything else makes Pages
    show a modal "invalid file format" alert that blocks every later Apple Event."""
    if not os.path.exists(path):
        raise PagesError("not found: %s" % path)
    if os.path.isdir(path):
        if not os.path.exists(os.path.join(path, "Index.zip")) and not os.path.isdir(
            os.path.join(path, "Index")
        ):
            raise PagesError("not a Pages package (no Index): %s" % path)
    elif not zipfile.is_zipfile(path):
        raise PagesError("not a Pages file (not a zip or package): %s" % path)


def copy_pages(src, dst):
    if os.path.isdir(src):
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)


def remove_path(path):
    if os.path.isdir(path) and not os.path.islink(path):
        shutil.rmtree(path)
    elif os.path.exists(path):
        os.remove(path)


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
    """Run one pages_ops op. docs = paths the op will open (tracked for cleanup)."""
    docs = [os.path.realpath(d) for d in docs]
    _track(docs, True)
    env = dict(os.environ, PAGES_TIMEOUT=str(TIMEOUT))
    try:
        proc = subprocess.run(
            ["osascript", OPS, op] + list(args),
            capture_output=True,
            text=True,
            env=env,
            timeout=TIMEOUT + 30,
        )
    except subprocess.TimeoutExpired:
        raise PagesError("osascript did not return in %ss. %s" % (TIMEOUT + 30, dialog_hint()))
    err = proc.stderr.strip()
    if proc.returncode != 0:
        if "-1712" in err:  # AppleEvent timed out: almost always a modal dialog
            raise PagesError("Pages did not answer (timeout). %s" % dialog_hint())
        if "-1743" in err:
            raise PagesError(
                "not allowed to control Pages: grant it in System Settings > "
                "Privacy & Security > Automation, then retry"
            )
        raise PagesError(err or "osascript failed with code %d" % proc.returncode)
    _track(docs, False)
    return norm_text(proc.stdout.rstrip("\n"))


# ------------------------------------------------------------------ dialogs

_WINDOWS_JXA = r"""
ObjC.import("CoreGraphics");
const l = ObjC.deepUnwrap(ObjC.castRefToObject($.CGWindowListCopyWindowInfo(1, 0)));
// Alerts can sit on the normal layer (0) or the modal-panel layer (8); both count.
l.filter(w => w.kCGWindowOwnerName && /^Pages/.test(w.kCGWindowOwnerName) && [0, 8].includes(w.kCGWindowLayer))
 .map(w => [w.kCGWindowNumber, w.kCGWindowBounds.Width, w.kCGWindowBounds.Height, w.kCGWindowName || ""].join("\t"))
 .join("\n");
"""


def find_dialogs():
    """On-screen, untitled, alert-sized Pages windows. Needs no Accessibility access."""
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
        return "No Pages dialog is visible; the document may be very large, or Pages is busy."
    shots = []
    for wid in hits:
        shot = os.path.join(tempfile.gettempdir(), "pages-dialog-%s.png" % wid)
        if subprocess.run(["screencapture", "-x", "-o", "-l", wid, shot]).returncode == 0:
            shots.append(shot)
    return (
        "Pages is showing a modal dialog, which blocks all scripting until someone "
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
    g.add_argument("--title", help="EPUB title")
    g.add_argument("--author", help="EPUB author")
    g.add_argument("--genre", help="EPUB genre")
    g.add_argument("--language", help="EPUB language, ISO code (default: the Mac's system language)")
    g.add_argument("--publisher", help="EPUB publisher")
    g.add_argument("--cover", action="store_true", help="EPUB: first page is the cover")
    g.add_argument("--fixed-layout", action="store_true", help="EPUB fixed layout")
    g.add_argument("--password", help="PDF/DOCX open password")
    g.add_argument("--password-hint")
    g.add_argument("--image-quality", choices=("good", "better", "best"), help="PDF")
    g.add_argument("--comments", action="store_true", help="include comments")
    g.add_argument("--annotations", action="store_true", help="include smart annotations")


def export_opt_args(ns):
    """Argument namespace -> ["O", key, value, ...] for pages_ops."""
    out = []
    for key in ("title", "author", "genre", "language", "publisher", "password", "image_quality"):
        val = getattr(ns, key)
        if val:
            out += ["O", key.replace("_", "-"), val]
    if ns.password_hint:
        out += ["O", "password-hint", ns.password_hint]
    for key in ("cover", "fixed_layout", "comments", "annotations"):
        if getattr(ns, key):
            out += ["O", key.replace("_", "-"), "true"]
    return out


def format_of(path):
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    if ext not in FORMATS:
        raise PagesError("unsupported export extension .%s (use %s)" % (ext, ", ".join(FORMATS)))
    return ext


# ------------------------------------------------------------------ fill


def fill(source, work, values, token="{{%s}}", images=(), adds=(), exports=(), opts=(),
         save=True):
    """Core used by pages-fill and pages-merge. work = .pages path to create and edit.
    Returns dict with counts, images, exports and leftover text."""
    # Pages reports /private/tmp for /tmp; realpath keeps the open-document checks exact.
    work = os.path.join(os.path.realpath(os.path.dirname(os.path.abspath(work))),
                        os.path.basename(work))
    if source.startswith("template:"):
        run_ops("new", [source[len("template:"):], work])
    else:
        check_pages_file(source)
        copy_pages(source, work)
    args = [work]
    for k, v in values.items():
        args += ["T", token % k, v]
    for k, path in images:
        args += ["I", k, os.path.abspath(path)]
    for spec, path in adds:
        parts = spec.split(",")
        if len(parts) != 4:
            raise PagesError("--add-image needs PAGE,X,Y,WIDTH=PATH, got %r" % spec)
        args += ["A"] + [p.strip() for p in parts] + [os.path.abspath(path)]
    args += list(opts)
    for path in exports:
        args += ["X", os.path.abspath(path), format_of(path)]
    if save:
        args.append("S")
    prefix = token.split("%s")[0]
    if prefix:
        args += ["L", prefix]
    out = run_ops("fill", args, docs=[work])
    result = {"counts": {}, "images": {}, "exported": [], "leftover": ""}
    for line in out.split("\n"):
        parts = line.split("\t")
        if parts[0] == "COUNT":
            result["counts"][parts[1]] = int(parts[2])
        elif parts[0] == "IMAGE":
            result["images"][parts[1]] = int(parts[2])
        elif parts[0] == "EXPORTED":
            result["exported"].append(parts[1])
        elif parts[0] == "LEFTOVER":
            result["leftover"] = "\t".join(parts[1:]).strip()
    return result



def main(argv):
    try:
        if argv == ["--dialog"]:
            hits = find_dialogs()
            print(dialog_hint() if hits else "no Pages dialog visible")
            return 1 if hits else 0
        if argv == ["--close-leftovers"]:
            print(close_leftovers())
            return 0
    except PagesError as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
