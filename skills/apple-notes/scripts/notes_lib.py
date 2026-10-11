"""Shared helpers for the apple-notes scripts (Python 3.9+ stdlib only).

Everything goes through Notes' JXA dictionary: one `osascript -l JavaScript` call per
operation, JSON in through a temp file (bodies with inline images exceed argv limits),
JSON out on stdout. Nothing listens on a port and no process outlives its call.
"""
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

JXA_DIR = Path(__file__).resolve().parent / "jxa"
DEFAULT_TIMEOUT = 300

# AppleScript error numbers. Messages are localized (Hungarian, German, ...), so match
# the number in osascript's stderr, never the text.
ERRORS = {
    -1743: "Automation permission denied: allow this terminal/IDE to control Notes in "
           "System Settings > Privacy & Security > Automation, then retry.",
    -1712: "Notes did not answer in time (a modal dialog, a locked note prompt or an "
           "iCloud sync stall). Bring Notes to the front, dismiss any dialog, retry.",
    -600: "Notes is not running and could not be launched.",
    -1728: "Object not found (note, folder or account id/name no longer exists).",
    -10000: "Notes refused the operation (often: saving an attachment that is not a "
            "file, such as a table, or a destination Notes may not write to).",
}


def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def jxa(name, payload=None, timeout=DEFAULT_TIMEOUT):
    """Run scripts/jxa/<name>.js with `payload` (JSON) and return its parsed JSON result."""
    script = JXA_DIR / f"{name}.js"
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(payload or {}, fh)
        arg_path = fh.name
    try:
        res = subprocess.run(["osascript", "-l", "JavaScript", str(script), arg_path],
                             capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        die(f"timed out after {timeout}s in {name}. " + ERRORS[-1712], 124)
    finally:
        os.unlink(arg_path)
    if res.returncode != 0:
        m = re.search(r"\((-?\d+)\)\s*$", res.stderr.strip())
        num = int(m.group(1)) if m else None
        hint = ERRORS.get(num, "")
        die(f"{name} failed{f' ({num})' if num else ''}: {hint or res.stderr.strip()[-800:]}",
            3 if num == -1743 else 1)
    out = res.stdout.strip()
    return json.loads(out) if out else None


# ---- folders -----------------------------------------------------------------

def folders(account=None):
    """[{id, name, account, path, parent}] for every folder; path is 'Account/Folder/Sub'."""
    return jxa("folders", {"account": account})


def resolve_folder(path, all_folders=None):
    """Find one folder by 'Account/Folder/Sub', 'Folder/Sub' or bare 'Folder' (case-insensitive)."""
    fs = all_folders if all_folders is not None else folders()
    want = path.strip("/").lower()
    hits = [f for f in fs if f["path"].lower() == want]
    if not hits:
        hits = [f for f in fs if f["path"].lower().split("/", 1)[-1] == want]
    if not hits:
        hits = [f for f in fs if f["name"].lower() == want.rsplit("/", 1)[-1]
                and f["path"].lower().endswith(want)]
    if not hits:
        die(f"folder not found: {path!r}. Known: " + ", ".join(f["path"] for f in fs), 2)
    if len(hits) > 1:
        die(f"folder {path!r} is ambiguous: " + ", ".join(f["path"] for f in hits)
            + ". Pass the full Account/Folder path.", 2)
    return hits[0]


def subtree(folder, all_folders):
    """The folder plus every folder below it."""
    prefix = folder["path"] + "/"
    return [folder] + [f for f in all_folders if f["path"].startswith(prefix)]


DELETED_NAMES = {"recently deleted", "nemrég törölt", "zuletzt gelöscht",
                 "suppressions récentes", "eliminados recientemente"}


def is_deleted_folder(f):
    """Recently Deleted itself, or a deleted folder that shows up under it."""
    return any(seg.lower() in DELETED_NAMES for seg in f["path"].split("/")[1:])


# ---- notes -------------------------------------------------------------------

def find_note(ref, all_folders=None):
    """A note by x-coredata id, or by 'Folder path/Title' (must be unique)."""
    if ref.startswith("x-coredata://"):
        return jxa("note_get", {"id": ref})
    if "/" not in ref:
        die("pass a note id (x-coredata://...) or 'Folder/Title'; search with nt-search.py", 2)
    fpath, title = ref.rsplit("/", 1)
    folder = resolve_folder(fpath, all_folders)
    hits = [n for n in jxa("list_notes", {"folderIds": [folder["id"]], "text": False})
            if n["name"] == title]
    if not hits:
        die(f"no note titled {title!r} in {folder['path']}", 2)
    if len(hits) > 1:
        die(f"{len(hits)} notes titled {title!r} in {folder['path']}; pass the id: "
            + ", ".join(h["id"] for h in hits), 2)
    return jxa("note_get", {"id": hits[0]["id"]})


def body_media_counts(body):
    """(inline data-URI images, embedded table objects) in a note body."""
    return (len(re.findall(r"<img[^>]+src=\"data:", body or "")),
            len(re.findall(r"<object>", body or "")))


def body_loses_attachments(note):
    """True if rewriting this note's body would drop attachments.

    Notes keeps newer images, PDFs, scans and drawings as attachments that do not appear
    in `body` at all. Setting `body` rebuilds the note from the HTML, so those vanish.
    Only data-URI images and tables survive, because they are in the HTML.
    """
    imgs, objs = body_media_counts(note["body"])
    return note["attachmentCount"] > imgs + objs


# ---- files -------------------------------------------------------------------

MAGIC = [
    (b"\x89PNG", "png"), (b"\xff\xd8\xff", "jpg"), (b"GIF8", "gif"), (b"%PDF", "pdf"),
    (b"II*\x00", "tiff"), (b"MM\x00*", "tiff"), (b"RIFF", "webp"),
]


def sniff_ext(data, fallback="bin"):
    for sig, ext in MAGIC:
        if data.startswith(sig):
            return ext
    if data[4:8] == b"ftyp":
        brand = data[8:12]
        return "heic" if brand in (b"heic", b"heix", b"mif1", b"msf1") else "mov" if brand == b"qt  " else "mp4"
    return fallback


def data_uri_bytes(uri):
    head, _, b64 = uri.partition(",")
    return base64.b64decode(b64) if ";base64" in head else b""


def slug(text, maxlen=80):
    s = re.sub(r"[\\/:*?\"<>|\x00-\x1f]+", "-", (text or "untitled").strip())
    s = re.sub(r"\s+", " ", s).strip(" .-")
    return (s or "untitled")[:maxlen]


def unique_path(path, taken):
    stem, suffix, n = path.stem, path.suffix, 2
    cand = path
    while str(cand).lower() in taken:
        cand = path.with_name(f"{stem}-{n}{suffix}")
        n += 1
    taken.add(str(cand).lower())
    return cand


def dump(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))
