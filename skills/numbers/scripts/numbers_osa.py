#!/usr/bin/env python3
"""Shared plumbing for the Numbers scripts: run numbers_ops.js with a JSON request,
diagnose a blocked Numbers, address cells, and track the documents a run opened so
they can be closed.

Also a small CLI:
  python3 numbers_osa.py --dialog            detect a modal Numbers alert, screenshot it
  python3 numbers_osa.py --close-leftovers   close documents a killed run left open
  python3 numbers_osa.py --locale            decimal and list separators Numbers uses

Standard library only; runs on the macOS system python3 (3.9).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
OPS = os.path.join(HERE, "numbers_ops.js")
BUNDLE_ID = "com.apple.Numbers"
STATE = os.path.join(tempfile.gettempdir(), "numbers-skill-open.txt")
TIMEOUT = int(os.environ.get("NUMBERS_TIMEOUT", "300"))

# Output extension -> Numbers export format name.
EXPORT_AS = {
    "xlsx": "Microsoft Excel",
    "csv": "CSV",
    "pdf": "PDF",
    "numbers09": "Numbers 09",
}
FORMATS = ("automatic", "number", "currency", "percent", "text", "date and time",
           "duration", "fraction", "scientific", "checkbox")


class NumbersError(Exception):
    pass


# ------------------------------------------------------------------ files

def check_numbers_file(path):
    """A .numbers is a zip or a package directory; opening anything else makes Numbers
    show a modal "can't be opened" alert that blocks every later Apple Event."""
    if not os.path.exists(path):
        raise NumbersError("not found: %s" % path)
    if os.path.isdir(path):
        if not os.path.exists(os.path.join(path, "Index.zip")) and not os.path.isdir(
            os.path.join(path, "Index")
        ):
            raise NumbersError("not a Numbers package (no Index): %s" % path)
    elif path.lower().endswith(".numbers") and not zipfile.is_zipfile(path):
        raise NumbersError("not a Numbers file (not a zip or package): %s" % path)


def real(path):
    """Numbers reports /private/tmp for /tmp; realpath keeps open-document checks exact.
    The file itself may not exist yet, so resolve its folder."""
    path = os.path.abspath(os.path.expanduser(path))
    return os.path.join(os.path.realpath(os.path.dirname(path)), os.path.basename(path))


def remove_path(path):
    if os.path.isdir(path) and not os.path.islink(path):
        shutil.rmtree(path)
    elif os.path.exists(path):
        os.remove(path)


def export_as(path):
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    if ext not in EXPORT_AS:
        raise NumbersError("unsupported export extension .%s (use %s)"
                           % (ext, ", ".join(sorted(EXPORT_AS))))
    return EXPORT_AS[ext]


def add_export_args(parser):
    g = parser.add_argument_group("export options")
    g.add_argument("--summary-worksheet", action="store_true",
                   help="XLSX: keep Numbers' summary worksheet (a localized index sheet "
                        "Numbers adds when a document has several sheets or tables)")
    g.add_argument("--password", help="XLSX/PDF/Numbers 09 open password")
    g.add_argument("--password-hint")
    g.add_argument("--pdf-quality", choices=("good", "better", "best"), help="PDF image quality")
    g.add_argument("--comments", action="store_true", help="PDF: include comments")


def export_options(ns, as_name):
    """Argument namespace -> the `with properties` record for one export format."""
    opts = {}
    if as_name == "Microsoft Excel":
        opts["excludeSummaryWorksheet"] = not ns.summary_worksheet
    if as_name == "PDF":
        if ns.pdf_quality:
            opts["imageQuality"] = ns.pdf_quality.capitalize()
        if ns.comments:
            opts["includeComments"] = True
    if ns.password and as_name != "CSV":
        opts["password"] = ns.password
        if ns.password_hint:
            opts["passwordHint"] = ns.password_hint
    return opts


# ------------------------------------------------------------------ cells

def col_letter(c):
    s = ""
    while c > 0:
        c, m = divmod(c - 1, 26)
        s = chr(65 + m) + s
    return s


def col_index(letters):
    n = 0
    for ch in letters.upper():
        n = n * 26 + ord(ch) - 64
    return n


def addr(r, c):
    return "%s%d" % (col_letter(c), r)


def parse_addr(a):
    m = re.match(r"^\$?([A-Za-z]+)\$?(\d+)$", a.strip())
    if not m:
        raise NumbersError("bad cell address %r" % a)
    return int(m.group(2)), col_index(m.group(1))


# ------------------------------------------------------------------ run

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


def run_ops(op, req, docs=()):
    """Run one numbers_ops.js op with a JSON request; docs = paths the op will open
    (tracked for cleanup). Returns the parsed JSON result."""
    docs = [real(d) for d in docs]
    fd, req_path = tempfile.mkstemp(prefix="numbers-req-", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(req, fh, ensure_ascii=False)
    _track(docs, True)
    try:
        proc = subprocess.run(
            ["osascript", "-l", "JavaScript", OPS, op, req_path],
            capture_output=True, text=True, timeout=TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        raise NumbersError("osascript did not return in %ss. %s" % (TIMEOUT, dialog_hint()))
    finally:
        os.remove(req_path)
    err = proc.stderr.strip()
    if proc.returncode != 0:
        if "-1712" in err:  # AppleEvent timed out: almost always a modal dialog
            raise NumbersError("Numbers did not answer (timeout). %s" % dialog_hint())
        if "-1743" in err:
            raise NumbersError(
                "not allowed to control Numbers: grant it in System Settings > "
                "Privacy & Security > Automation, then retry")
        # "numbers_ops.js: execution error: Error: Error: <message> (-2700)" -> message
        m = re.search(r"execution error: (?:Error: )*(.*?)(?: \(-2700\))?$", err, re.S)
        raise NumbersError((m.group(1) if m else err) or "osascript failed with code %d"
                           % proc.returncode)
    _track(docs, False)
    return json.loads(proc.stdout)


# ------------------------------------------------------------------ locale

def locale_info():
    """Separators Numbers parses and formats with (the system region's)."""
    proc = subprocess.run(
        ["osascript", "-l", "JavaScript", "-e",
         'ObjC.import("Foundation"); const l = $.NSLocale.currentLocale;'
         ' [l.localeIdentifier.js, l.decimalSeparator.js, l.groupingSeparator.js].join("\\t")'],
        capture_output=True, text=True)
    # rstrip("\n") only: the grouping separator can be a no-break space.
    parts = proc.stdout.rstrip("\n").split("\t")
    if len(parts) != 3:
        return {"locale": "?", "decimal": ".", "grouping": ",", "csv_separator": ","}
    dec = parts[1]
    return {"locale": parts[0], "decimal": dec, "grouping": parts[2],
            # Numbers' CSV export separates with ";" wherever "," is the decimal mark.
            "csv_separator": ";" if dec == "," else ","}


# ------------------------------------------------------------------ dialogs

_WINDOWS_JXA = r"""
ObjC.import("CoreGraphics");
const l = ObjC.deepUnwrap(ObjC.castRefToObject($.CGWindowListCopyWindowInfo(1, 0)));
// Alerts can sit on the normal layer (0) or the modal-panel layer (8); both count.
l.filter(w => w.kCGWindowOwnerName && /^Numbers/.test(w.kCGWindowOwnerName) && [0, 8].includes(w.kCGWindowLayer))
 .map(w => [w.kCGWindowNumber, w.kCGWindowBounds.Width, w.kCGWindowBounds.Height, w.kCGWindowName || ""].join("\t"))
 .join("\n");
"""


def find_dialogs():
    """On-screen, untitled, alert-sized Numbers windows. Needs no Accessibility access."""
    proc = subprocess.run(
        ["osascript", "-l", "JavaScript", "-e", _WINDOWS_JXA], capture_output=True, text=True)
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
        return "No Numbers dialog is visible; the document may be very large, or Numbers is busy."
    shots = []
    for wid in hits:
        shot = os.path.join(tempfile.gettempdir(), "numbers-dialog-%s.png" % wid)
        if subprocess.run(["screencapture", "-x", "-o", "-l", wid, shot]).returncode == 0:
            shots.append(shot)
    return ("Numbers is showing a modal dialog, which blocks all scripting until someone "
            "clicks it away. Screenshot: %s - read it and ask the user to dismiss it."
            % (", ".join(shots) or "unavailable"))


def close_paths(paths):
    return run_ops("close", {"paths": [real(p) for p in paths]})


def close_leftovers():
    if not os.path.exists(STATE):
        return {"closed": 0}
    with open(STATE, encoding="utf-8") as fh:
        paths = [line.rstrip("\n") for line in fh if line.strip()]
    out = close_paths(paths) if paths else {"closed": 0}
    os.remove(STATE)
    return out


def main(argv):
    try:
        if argv == ["--dialog"]:
            hits = find_dialogs()
            print(dialog_hint() if hits else "no Numbers dialog visible")
            return 1 if hits else 0
        if argv == ["--close-leftovers"]:
            print("closed: %d" % close_leftovers()["closed"])
            return 0
        if argv and argv[0] == "--close" and len(argv) > 1:
            print("closed: %d" % close_paths(argv[1:])["closed"])
            return 0
        if argv == ["--locale"]:
            info = locale_info()
            for k in ("locale", "decimal", "grouping", "csv_separator"):
                print("%s: %r" % (k, info[k]) if k == "grouping" else "%s: %s" % (k, info[k]))
            return 0
    except NumbersError as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
