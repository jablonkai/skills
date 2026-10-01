"""Shared helpers for nk.py: locating Nuke, parsing .nk text, image sequences, ffprobe.

Runs under the system python3 (3.9+), stdlib only. Nothing here imports `nuke`.
"""
import glob
import json
import os
import re
import shutil
import subprocess

NC_MAX_W, NC_MAX_H = 1920, 1080
NC_DISABLED_CODECS = ("h264", "avc1", "mpeg4", "mp4v")
# Top-level .nk statements that look like `word {…}` but are not nodes.
NON_NODE_COMMANDS = {"add_layer", "define_window_layout_xml", "set", "push", "version",
                     "end_group", "clone", "cut_paste_input", "addUserKnob"}
SKIP_APPS = ("Non-Commercial", "Studio", "NukeX", "Indie", "Assist", "Hiero", "Player")


# ---------------------------------------------------------------- Nuke binary
def _version_key(path):
    m = re.search(r"Nuke(\d+)\.(\d+)v(\d+)", path)
    return tuple(int(x) for x in m.groups()) if m else (0, 0, 0)


def find_nuke():
    """Return the Nuke executable: $NUKE_BIN, else the newest /Applications/Nuke*/Nuke<ver>.app."""
    env = os.environ.get("NUKE_BIN")
    if env:
        return env if os.access(env, os.X_OK) else None
    hits = []
    for app in glob.glob("/Applications/Nuke*/Nuke*.app"):
        if any(s in os.path.basename(app) for s in SKIP_APPS):
            continue
        for exe in glob.glob(os.path.join(app, "Contents/MacOS/Nuke[0-9]*")):
            if os.access(exe, os.X_OK) and not os.path.isdir(exe):
                hits.append(exe)
    hits.sort(key=_version_key)
    return hits[-1] if hits else None


# ---------------------------------------------------------------- .nk parsing
def _read_word(s, i):
    """Read one TCL word starting at s[i] (no leading space). Return (word, raw, next_i)."""
    n = len(s)
    if s[i] == "{":
        depth, j = 0, i
        while j < n:
            c = s[j]
            if c == "\\":
                j += 2
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return s[i + 1:j], s[i:j + 1], j + 1
            j += 1
        raise ValueError("unbalanced '{' starting at offset %d" % i)
    if s[i] == '"':
        j = i + 1
        while j < n:
            if s[j] == "\\":
                j += 2
                continue
            if s[j] == '"':
                return _unescape(s[i + 1:j]), s[i:j + 1], j + 1
            j += 1
        raise ValueError("unterminated '\"' starting at offset %d" % i)
    j, depth = i, 0
    while j < n and (depth > 0 or not s[j].isspace()):
        if s[j] == "\\":
            j += 2
            continue
        if s[j] == "[":
            depth += 1
        elif s[j] == "]":
            depth = max(0, depth - 1)
        j += 1
    return _unescape(s[i:j]), s[i:j], j


def _unescape(v):
    return re.sub(r"\\(.)", lambda m: {"n": "\n", "t": "\t"}.get(m.group(1), m.group(1)), v)


def _statements(s):
    """Yield (words, raw_words, line_no) for each top-level statement (newline-terminated)."""
    i, n = 0, len(s)
    while i < n:
        while i < n and s[i] in " \t\r\n":
            i += 1
        if i >= n:
            break
        line_no = s.count("\n", 0, i) + 1
        if s[i] == "#":
            while i < n and s[i] != "\n":
                i += 1
            continue
        words, raws = [], []
        while i < n and s[i] != "\n":
            if s[i] in " \t\r":
                i += 1
                continue
            w, raw, i = _read_word(s, i)
            words.append(w)
            raws.append(raw)
        yield words, raws, line_no


def _knobs(body):
    words, i = [], 0
    while i < len(body):
        if body[i].isspace():
            i += 1
            continue
        w, raw, i = _read_word(body, i)
        words.append((w, raw))
    knobs = {}
    for k in range(0, len(words) - 1, 2):
        knobs[words[k][0]] = words[k + 1][0]
    return knobs


def parse_nk(text):
    """Parse .nk text into a list of nodes: {class, name, knobs, line, group}.

    Group/Gizmo contents get dotted names (Group1.Write1), which is what
    nuke.execute() and nuke.toNode() expect.
    """
    nodes, groups, counters = [], [], {}
    for words, raws, line in _statements(text):
        if not words:
            continue
        if words[0] == "end_group":
            if groups:
                groups.pop()
            continue
        if (len(words) == 2 and raws[1].startswith("{") and words[0] not in NON_NODE_COMMANDS
                and re.match(r"^[A-Za-z_][\w.]*$", words[0])):
            cls = words[0]
            knobs = _knobs(words[1])
            counters[cls] = counters.get(cls, 0) + 1
            name = knobs.get("name") or ("root" if cls == "Root" else "%s%d" % (cls, counters[cls]))
            full = ".".join(groups + [name]) if cls != "Root" else "root"
            nodes.append({"class": cls, "name": full, "knobs": knobs, "line": line,
                          "group": ".".join(groups)})
            if cls in ("Group", "LiveGroup"):
                groups.append(name)
    return nodes


def is_true(v):
    return str(v).strip().lower() in ("true", "1", "yes")


def root_info(nodes):
    root = next((n for n in nodes if n["class"] == "Root"), None)
    k = root["knobs"] if root else {}
    first = int(float(k.get("first_frame", 1)))
    last = int(float(k.get("last_frame", 100 if "first_frame" not in k else first)))
    w = h = None
    fmt = k.get("format")
    if fmt:
        parts = fmt.split()
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            w, h = int(parts[0]), int(parts[1])
    return {"first": first, "last": last, "width": w, "height": h, "format": fmt}


def writes(nodes):
    out = []
    for n in nodes:
        if n["class"] != "Write":
            continue
        k = n["knobs"]
        out.append({"name": n["name"], "file": k.get("file", ""),
                    "file_type": k.get("file_type", ""),
                    "codec": k.get("mov64_codec", ""),
                    "disabled": is_true(k.get("disable", "false")),
                    "use_limit": is_true(k.get("use_limit", "false")),
                    "first": int(float(k["first"])) if "first" in k else None,
                    "last": int(float(k["last"])) if "last" in k else None,
                    "line": n["line"]})
    return out


# ---------------------------------------------------------------- sequences
SEQ_TOKEN = re.compile(r"(#+|%0?(\d*)d)")


def seq_regex(pattern):
    """Regex matching a frame-pattern basename (####, %04d, or a literal frame number)."""
    base = os.path.basename(pattern)
    m = None
    for m in SEQ_TOKEN.finditer(base):
        pass
    if m:
        pre, post = base[:m.start()], base[m.end():]
    else:
        m = re.search(r"(\d+)(\.[A-Za-z0-9]+)$", base)
        if not m:
            return None
        pre, post = base[:m.start(1)], base[m.end(1):]
    return re.compile("^" + re.escape(pre) + r"(-?\d+)" + re.escape(post) + "$")


def find_frames(pattern):
    """Frames on disk for a sequence pattern. Returns (sorted frame list, padding, hash_pattern)."""
    d = os.path.dirname(pattern) or "."
    rx = seq_regex(pattern)
    if rx is None or not os.path.isdir(d):
        return [], 0, pattern
    frames, pad = [], 0
    for f in os.listdir(d):
        m = rx.match(f)
        if m:
            frames.append(int(m.group(1)))
            pad = max(pad, len(m.group(1).lstrip("-")))
    frames.sort()
    pre_post = rx.pattern[1:-1].split(r"(-?\d+)")
    pre = re.sub(r"\\(.)", r"\1", pre_post[0])
    post = re.sub(r"\\(.)", r"\1", pre_post[1])
    return frames, pad, os.path.join(d, pre + "#" * max(pad, 1) + post)


def frame_path(hash_pattern, frame):
    def rep(m):
        tok = m.group(1)
        width = len(tok) if tok.startswith("#") else int(m.group(2) or 0)
        return "%0*d" % (width, frame)
    return SEQ_TOKEN.sub(rep, hash_pattern, count=1)


def is_movie(path):
    return os.path.splitext(path)[1].lower() in (".mov", ".mp4", ".mxf", ".avi", ".mkv", ".m4v")


# ---------------------------------------------------------------- ffprobe
def ffprobe(path, count_frames=False):
    exe = shutil.which("ffprobe")
    if not exe or not os.path.exists(path):
        return None
    cmd = [exe, "-v", "error", "-select_streams", "v:0", "-show_entries",
           "stream=codec_name,width,height,pix_fmt,nb_frames,nb_read_frames", "-of", "json"]
    if count_frames:
        cmd.insert(1, "-count_frames")
    try:
        r = subprocess.run(cmd + [path], capture_output=True, text=True, timeout=120)
        streams = json.loads(r.stdout or "{}").get("streams", [])
        return streams[0] if streams else None
    except (subprocess.SubprocessError, ValueError):
        return None


def fit_nc(w, h):
    """Largest even size with w×h's aspect that fits the Non-commercial 1920×1080 cap."""
    if w <= NC_MAX_W and h <= NC_MAX_H:
        return w, h
    s = min(NC_MAX_W / float(w), NC_MAX_H / float(h))
    return int(w * s) // 2 * 2, int(h * s) // 2 * 2
