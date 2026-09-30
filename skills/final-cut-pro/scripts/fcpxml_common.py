"""Shared helpers for the final-cut-pro scripts: the installed app and its DTDs,
FCPXML load/save, media URLs, the timeline walk, and the read-only AppleScript model.
Standard library only (system python3 3.9+)."""
import glob
import json
import os
import re
import shutil
import subprocess
import tempfile
import unicodedata
import urllib.parse
import xml.etree.ElementTree as ET
from fractions import Fraction

from fcptime import fmt_time, parse_time

BUNDLE_ID = "com.apple.FinalCut"
DTD_SUBDIR = "Contents/Frameworks/Interchange.framework/Versions/A/Resources"

# Element order inside a clip (DTD): these ranks decide where an inserted child goes.
ANCHOR_TAGS = {"audio", "video", "clip", "title", "caption", "mc-clip", "ref-clip", "sync-clip",
               "asset-clip", "audition", "spine", "live-drawing"}
MARKER_TAGS = {"marker", "chapter-marker", "rating", "keyword", "analysis-marker", "hidden-clip-marker"}
CLIP_TAGS = {"asset-clip", "clip", "ref-clip", "sync-clip", "mc-clip", "video", "audio", "title",
             "gap", "audition", "live-drawing"}


class FcpError(Exception):
    pass


# ---------------------------------------------------------------- app and DTDs

def find_app():
    try:
        out = subprocess.run(["mdfind", f"kMDItemCFBundleIdentifier == '{BUNDLE_ID}'"],
                             capture_output=True, text=True, timeout=10).stdout
        for line in out.splitlines():
            if line.endswith(".app") and os.path.isdir(line):
                return line
    except (OSError, subprocess.TimeoutExpired):
        pass
    for cand in ("/Applications/Final Cut Pro.app",
                 os.path.expanduser("~/Applications/Final Cut Pro.app")):
        if os.path.isdir(cand):
            return cand
    return None


def app_version(app):
    try:
        return subprocess.run(["defaults", "read", os.path.join(app, "Contents/Info"),
                               "CFBundleShortVersionString"], capture_output=True, text=True,
                              timeout=10).stdout.strip() or None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _vkey(v):
    return tuple(int(x) for x in v.split("."))


def dtd_versions(app):
    """FCPXML versions the installed app ships a DTD for, oldest first."""
    found = []
    for p in glob.glob(os.path.join(app, DTD_SUBDIR, "FCPXMLv*.dtd")):
        m = re.search(r"FCPXMLv(\d+)_(\d+)\.dtd$", p)
        if m:
            found.append(f"{m.group(1)}.{m.group(2)}")
    return sorted(found, key=_vkey)


def latest_version(app=None):
    app = app or find_app()
    if not app:
        raise FcpError("Final Cut Pro not found (bundle id com.apple.FinalCut); pass --version")
    versions = dtd_versions(app)
    if not versions:
        raise FcpError(f"no FCPXML DTDs in {app}/{DTD_SUBDIR}")
    return versions[-1]


def dtd_copy(version, app=None):
    """Copy the DTD to a temp path: xmllint cannot load it from inside
    'Final Cut Pro.app' because of the space in the path."""
    app = app or find_app()
    if not app:
        raise FcpError("Final Cut Pro not found; cannot locate the FCPXML DTD")
    src = os.path.join(app, DTD_SUBDIR, "FCPXMLv%s.dtd" % version.replace(".", "_"))
    if not os.path.isfile(src):
        raise FcpError(f"FCP {app_version(app)} has no DTD for FCPXML {version} "
                       f"(has {', '.join(dtd_versions(app))})")
    d = os.path.join(tempfile.gettempdir(), "fcp-skill-dtd")
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, os.path.basename(src))
    if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
        shutil.copyfile(src, dst)
    return dst


# ---------------------------------------------------------------- templates

TITLE_TEMPLATES = {
    "basic": ("Basic Title",
              ".../Titles.localized/Bumper:Opener.localized/Basic Title.localized/Basic Title.moti"),
    "lower-third": ("Basic Lower Third",
                    ".../Titles.localized/Lower Thirds.localized/Basic Lower Third.localized/"
                    "Basic Lower Third.moti"),
}
TRANSITIONS = {
    "cross-dissolve": ("Cross Dissolve", "FxPlug:4731E73A-8DAC-4113-9A30-AE85B1761265"),
}
TEMPLATE_ROOTS = ["Contents/PlugIns/MediaProviders/MotionEffect.fxp/Contents/Resources/"
                  + d for d in ("Templates.localized", "PETemplates.localized")]



def find_template(name, what):
    """Resolve a Motion template to its FCPXML uid. `name` is the display name
    ("Formal") or, when several categories share it ("Bug"), "Category/Name"
    ("Lower Thirds/Formal", "Cinema/Bug")."""
    app = find_app()
    if not app:
        raise FcpError(f"unknown {what} {name!r} and Final Cut Pro not found to search")
    sub = "Titles.localized" if what == "title" else "Transitions.localized"
    want = [part.strip().lower() for part in str(name).split("/") if part.strip()]
    hits = {}
    for rootdir in TEMPLATE_ROOTS:
        base = os.path.join(app, rootdir, sub)
        for dirpath, dirs, files in os.walk(base):
            for f in files:
                stem, ext = os.path.splitext(f)
                if ext not in (".moti", ".motr") or stem.lower() != want[-1]:
                    continue
                rel = os.path.relpath(os.path.join(dirpath, f), os.path.join(app, rootdir))
                parts = [x[:-len(".localized")].lower() for x in rel.split(os.sep)
                         if x.endswith(".localized")]
                if all(w in parts for w in want[:-1]):
                    hits[".../" + rel] = stem
    if len(hits) == 1:
        uid, stem = next(iter(hits.items()))
        return stem, uid
    if not hits:
        raise FcpError(f"no {what} template named {name!r} (bash fcp.sh --templates lists them)")
    cats = sorted({uid.split("/")[-3].replace(".localized", "") for uid in hits})
    raise FcpError(f"{len(hits)} {what} templates are named {name!r}; say which one as "
                   f"Category/{want[-1]}: " + ", ".join(cats))


# ---------------------------------------------------------------- load / save

def info_path(path):
    """.fcpxmld bundles keep the document in Info.fcpxml."""
    if os.path.isdir(path):
        p = os.path.join(path, "Info.fcpxml")
        if not os.path.isfile(p):
            raise FcpError(f"{path} is a directory without Info.fcpxml")
        return p
    return path


def load(path):
    p = info_path(path)
    if not os.path.isfile(p):
        raise FcpError(f"no such file: {path}")
    # ElementTree never fetches external entities or DTDs.
    try:
        root = ET.parse(p).getroot()
    except ET.ParseError as e:
        raise FcpError(f"{path}: not well-formed XML: {e}")
    if root.tag != "fcpxml":
        raise FcpError(f"{path}: root element is <{root.tag}>, not <fcpxml>")
    return root


def save(root, path, force=False):
    """Write with the DOCTYPE FCP expects. A .fcpxmld path gets a bundle."""
    target = os.path.join(path, "Info.fcpxml") if path.endswith(".fcpxmld") else path
    if os.path.exists(target) and not force:
        raise FcpError(f"{target} exists; pass --force to replace it")
    os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
    ET.indent(root, space="    ")
    body = ET.tostring(root, encoding="unicode")
    with open(target, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE fcpxml>\n\n')
        f.write(body)
        f.write("\n")
    return target


def xmllint(path, version):
    """DTD-validate; returns (ok, messages)."""
    dtd = dtd_copy(version)
    try:
        r = subprocess.run(["xmllint", "--noout", "--dtdvalid", dtd, info_path(path)],
                           capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        raise FcpError("xmllint not found (it ships with macOS in /usr/bin)")
    msgs = [ln for ln in r.stderr.splitlines() if ln.strip()]
    return r.returncode == 0, msgs


# ---------------------------------------------------------------- media URLs

def media_url(path):
    """Absolute, percent-encoded file URL for a media path (the file must exist)."""
    ap = os.path.abspath(os.path.expanduser(path))
    if not os.path.isfile(ap):
        raise FcpError(f"media not found: {path}")
    return "file://" + urllib.parse.quote(ap)


def url_to_path(src):
    """file URL -> NFC path. FCP writes decomposed (NFD) escapes such as U%CC%88."""
    if not src.startswith("file://"):
        return None
    p = urllib.parse.unquote(urllib.parse.urlparse(src).path)
    return unicodedata.normalize("NFC", p)


def media_exists(src):
    p = url_to_path(src)
    return bool(p) and (os.path.exists(p) or os.path.exists(unicodedata.normalize("NFD", p)))


# ---------------------------------------------------------------- resources

class Resources:
    def __init__(self, root):
        self.root = root
        self.res = root.find("resources")
        if self.res is None:
            self.res = ET.Element("resources")
            idx = 1 if root.find("import-options") is not None else 0
            root.insert(idx, self.res)
        self.by_id = {e.get("id"): e for e in self.res if e.get("id")}

    def get(self, rid):
        return self.by_id.get(rid)

    def new_id(self):
        n = 1
        used = {e.get("id") for e in self.root.iter() if e.get("id")}
        while f"r{n}" in used:
            n += 1
        return f"r{n}"

    def add(self, el):
        if not el.get("id"):
            el.set("id", self.new_id())
        self.res.append(el)
        self.by_id[el.get("id")] = el
        return el.get("id")

    def effect(self, uid, name):
        for e in self.res.findall("effect"):
            if e.get("uid") == uid:
                return e.get("id")
        return self.add(ET.Element("effect", {"name": name, "uid": uid}))

    def frame_duration(self, fmt_id):
        f = self.by_id.get(fmt_id)
        if f is None or not f.get("frameDuration"):
            return None
        return parse_time(f.get("frameDuration"))


def t(el, attr, default="0s"):
    v = el.get(attr)
    return parse_time(v if v is not None else default)


# ---------------------------------------------------------------- timeline walk

def projects(root):
    """Yield (event_name, project_element) for every project in the document."""
    for ev in root.iter("event"):
        for pr in ev.findall("project"):
            yield ev.get("name"), pr
    for pr in root.findall("project"):
        yield None, pr


def item_source_fd(el, res, seq_fd):
    ref = el.get("ref")
    r = res.get(ref) if ref else None
    if r is not None and r.tag == "asset":
        fd = res.frame_duration(r.get("format"))
        if fd:
            return fd
    if el.get("format"):
        fd = res.frame_duration(el.get("format"))
        if fd:
            return fd
    return seq_fd


def walk(container, res, parent_tl, parent_start, lane_base=0, depth=0, path="", expand=False):
    """Yield dicts for every timed child of a container.

    Timeline position of a child = parent timeline in + (child offset - parent start).
    A connected storyline (<spine lane=…>) is its own 0-based time space: its children's
    offsets count from the storyline's start (verified on FCP 12.4; a non-zero first
    offset makes FCP shift the storyline by that amount on every import).
    """
    for i, el in enumerate(list(container)):
        tag = el.tag
        if tag in MARKER_TAGS:
            continue
        if tag not in CLIP_TAGS and tag not in ("spine", "transition"):
            continue
        off = t(el, "offset", "0s")
        start = t(el, "start", "0s")
        tl_in = parent_tl + (off - parent_start)
        lane = int(el.get("lane", "0"))
        if tag == "spine":
            yield from walk(el, res, tl_in, Fraction(0), lane_base + lane, depth + 1,
                            f"{path}/spine[{i}]", expand)
            continue
        dur = t(el, "duration", "0s")
        if el.get("duration") is None and tag == "asset-clip":
            a = res.get(el.get("ref"))
            if a is not None:
                dur = t(a, "duration", "0s")
        yield {"el": el, "tag": tag, "tl_in": tl_in, "tl_out": tl_in + dur, "start": start,
               "duration": dur, "lane": lane_base + lane, "depth": depth,
               "path": f"{path}/{tag}[{i}]"}
        if tag == "transition":
            continue
        # Anchored children (connected clips, titles, storylines) live in el's local time.
        yield from walk(el, res, tl_in, start, lane_base + lane if lane else lane_base,
                        depth + 1, f"{path}/{tag}[{i}]", expand)
        if expand and tag == "ref-clip":
            media = res.get(el.get("ref"))
            seq = media.find("sequence") if media is not None else None
            if seq is not None and seq.find("spine") is not None:
                # ref-clip start is a time in the compound's own sequence.
                yield from walk(seq.find("spine"), res, tl_in, start, lane_base + lane,
                                depth + 1, f"{path}/{tag}[{i}]/media", expand)


def markers_of(container, res, parent_tl, parent_start):
    """Markers/keywords anywhere under a container, with timeline positions."""
    out = []
    for item in [{"el": container, "tl_in": parent_tl, "start": parent_start}] + \
            list(walk(container, res, parent_tl, parent_start)):
        el = item["el"]
        for m in el:
            if m.tag in ("marker", "chapter-marker", "keyword"):
                ms = t(m, "start", "0s")
                out.append({"el": m, "tag": m.tag, "tl": item["tl_in"] + (ms - item["start"]),
                            "duration": t(m, "duration", "0s"), "owner": el})
    return out


def insert_child(parent, child):
    """Insert respecting the DTD order: timing, adjust-*, anchors, markers, the rest."""
    def rank(tag):
        if tag == "note":
            return 0
        if tag in ("conform-rate", "timeMap"):
            return 1
        if tag.startswith("adjust-"):
            return 2
        if tag in ("mc-source",):
            return 3
        if tag in ("param", "text", "text-style-def"):
            return 0
        if tag in ANCHOR_TAGS:
            return 4
        if tag in MARKER_TAGS:
            return 5
        return 6
    r = rank(child.tag)
    for i, c in enumerate(list(parent)):
        if rank(c.tag) > r:
            parent.insert(i, child)
            return child
    parent.append(child)
    return child


# ---------------------------------------------------------------- AppleScript model

def osascript(script, timeout=60):
    try:
        r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True,
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        raise FcpError(f"osascript timed out after {timeout}s")
    return r.returncode, r.stdout.strip(), r.stderr.strip()


# Seven bulk Apple events, then local loops: FCP answers each event slowly when it is in
# the background or paged out (seconds per event under memory pressure), so the number
# of events, not the number of projects, sets the cost.
LIST_SCRIPT = r'''
with timeout of %(timeout)d seconds
  tell application id "com.apple.FinalCut"
    set libNames to name of every library
    set libFiles to {}
    try
      set libFiles to file of every library
    end try
    set evNames to name of every event of every library
    set prNames to name of every project of every event of every library
    set prIds to id of every project of every event of every library
    set prDur to duration of sequence of every project of every event of every library
    set prFd to frame duration of sequence of every project of every event of every library
    set prStart to start time of sequence of every project of every event of every library
  end tell
end timeout
set out to ""
using terms from application id "com.apple.FinalCut"
repeat with i from 1 to count of libNames
  set lf to ""
  try
    set lf to POSIX path of ((item i of libFiles) as text)
  end try
  repeat with j from 1 to count of (item i of evNames)
    set names to item j of (item i of prNames)
    repeat with k from 1 to count of names
      set d to item k of item j of (item i of prDur)
      set fd to item k of item j of (item i of prFd)
      set startRec to item k of item j of (item i of prStart)
      set out to out & (item i of libNames) & tab & lf & tab & (item j of (item i of evNames)) & tab & (item k of names) & tab & (item k of item j of (item i of prIds)) & tab & ((value of d) as text) & "/" & ((timescale of d) as text) & tab & ((value of fd) as text) & "/" & ((timescale of fd) as text) & tab & ((value of startRec) as text) & "/" & ((timescale of startRec) as text) & linefeed
    end repeat
  end repeat
end repeat
end using terms from
return out
'''


def app_running():
    r = subprocess.run(["pgrep", "-x", "Final Cut Pro"], capture_output=True)
    return r.returncode == 0


def _num(text):
    v, ts = text.split("/")
    v = Fraction(v.replace(",", "."))
    return v / int(ts) if int(ts) else Fraction(0)


def list_projects(timeout=None):
    """Every project FCP has open, via the read-only AppleScript model. Never launches FCP.
    FCP_AE_TIMEOUT (default 180 s) bounds the whole query."""
    if not app_running():
        raise FcpError("Final Cut Pro is not running")
    timeout = int(timeout or os.environ.get("FCP_AE_TIMEOUT", 180))
    script = LIST_SCRIPT % {"timeout": timeout}
    try:
        rc, out, err = osascript(script, timeout + 15)
    except FcpError:
        rc, out, err = 1, "", "-1712 osascript timed out"
    if rc != 0 and "-1712" in err:
        raise FcpError(f"Final Cut Pro did not answer within {timeout}s (-1712). It answers "
                       "Apple events slowly when busy after an import or paged out under memory "
                       "pressure; retry, or raise FCP_AE_TIMEOUT")
    if rc != 0:
        if "-1743" in err:
            raise FcpError("Automation permission denied: allow the terminal in System Settings "
                           "▸ Privacy & Security ▸ Automation ▸ Final Cut Pro")
        raise FcpError(f"AppleScript failed: {err}")
    rows = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) != 8:
            continue
        lib, lib_file, ev, name, pid, d, fd, st = parts
        rows.append({"library": lib, "library_file": lib_file.rstrip("/") or None, "event": ev,
                     "project": name, "id": pid, "duration": fmt_time(_num(d)),
                     "seconds": float(_num(d)), "frame_duration": fmt_time(_num(fd)),
                     "start": fmt_time(_num(st))})
    return rows


def emit(obj):
    print(json.dumps(obj, ensure_ascii=False))
