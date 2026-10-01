"""Shared helpers for the compressor skill scripts. Standard library only (Python 3.9+).

Locates the Compressor CLI, indexes built-in and user settings (with their
English display names), submits batches, parses -monitor output, and wraps
ffprobe.
"""

import json
import os
import re
import shutil
import subprocess
import urllib.parse

DEFAULT_APP = "/Applications/Compressor.app"
USER_SETTINGS = os.path.expanduser("~/Library/Application Support/Compressor/Settings")
SETTING_EXTS = (".compressorsetting", ".cmprstng", ".setting")
# Relative to Contents/: where 5.x keeps the built-in settings and their names.
_STOMP = ("PlugIns/Compressor/CompressorKit.bundle/Contents/Frameworks/"
          "Compressor.framework/Versions/A/Frameworks")
BUILTIN_REL = _STOMP + "/StompUI.framework/Versions/A/Resources/BuiltInSettings"
STRINGS_REL = _STOMP + "/StompTypes.framework/Versions/A/Resources/en.lproj/Localizable.strings"
VIDEO_EXTS = {".mov", ".mp4", ".m4v", ".mxf", ".mts", ".m2ts", ".avi", ".mkv",
              ".mpg", ".mpeg", ".3gp", ".dv", ".braw", ".r3d", ".crm", ".insv"}
# MXF settings name the codec by an MTCompression* constant instead of a FourCC.
MXF_CODECS = {"MTCompressionPRORES422PROXY": "apco", "MTCompressionPRORES422LT": "apcs",
              "MTCompressionPRORES422": "apcn", "MTCompressionPRORES422HQ": "apch",
              "MTCompressionPRORES4444": "ap4h", "MTCompressionPRORES4444XQ": "ap4x"}
ACTIVE = re.compile(r"process|pend|wait|submit|queue|pause|prepar|ready|unknown", re.I)


class CmpError(Exception):
    pass


# --------------------------------------------------------------------- app / CLI

def app_path():
    app = os.environ.get("COMPRESSOR_APP", DEFAULT_APP)
    if not os.path.isdir(app):
        raise CmpError("Compressor not found at %s. Install it from the Mac App Store, "
                       "or set COMPRESSOR_APP=/path/to/Compressor.app" % app)
    return app


def find_cli():
    cli = os.path.join(app_path(), "Contents/MacOS/Compressor")
    if not os.access(cli, os.X_OK):
        raise CmpError("Compressor binary missing or not executable: %s" % cli)
    return cli


def app_version():
    plist = os.path.join(app_path(), "Contents/Info.plist")
    out = subprocess.run(["/usr/bin/defaults", "read", plist[:-6], "CFBundleShortVersionString"],
                         capture_output=True, text=True)
    return out.stdout.strip() or "unknown"


def _clean(text):
    """Drop the NSLog lines (`2026-10-01 20:30:44.162 Compressor[pid:tid] ...`)."""
    return "\n".join(l for l in text.splitlines()
                     if not re.match(r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+ Compressor\[", l))


def run_cli(args, timeout=120):
    p = subprocess.run([find_cli()] + list(args), capture_output=True, text=True,
                       timeout=timeout)
    return p.returncode, _clean(p.stdout), _clean(p.stderr)


# --------------------------------------------------------------------- settings

def builtin_dir():
    d = os.path.join(app_path(), "Contents", BUILTIN_REL)
    if os.path.isdir(d):
        return d
    for root, dirs, _ in os.walk(os.path.join(app_path(), "Contents")):
        if "BuiltInSettings" in dirs:
            return os.path.join(root, "BuiltInSettings")
    raise CmpError("BuiltInSettings folder not found inside %s" % app_path())


_STRINGS = None


def display_strings():
    global _STRINGS
    if _STRINGS is None:
        _STRINGS = {}
        path = os.path.join(app_path(), "Contents", STRINGS_REL)
        if os.path.isfile(path):
            p = subprocess.run(["/usr/bin/plutil", "-convert", "json", "-o", "-", path],
                               capture_output=True, text=True)
            if p.returncode == 0:
                _STRINGS = json.loads(p.stdout)
    return _STRINGS


def _attr(tag_text, name):
    m = re.search(r'\b%s="([^"]*)"' % name, tag_text)
    return m.group(1) if m else None


def size_spec(w, h):
    """Describe Compressor's <automatic width height> pair.

    -100/-100 → source size; -P/-P → P percent; -W/H → fit inside WxH (no upscale);
    W/H (both positive) → exactly WxH.
    """
    if w is None or h is None:
        return {"mode": "source", "text": "source size"}
    if w < 0 and h < 0:
        if w == h == -100:
            return {"mode": "source", "text": "source size"}
        return {"mode": "percent", "percent": -w, "text": "%g%% of source" % -w}
    if w < 0 < h:
        return {"mode": "fit", "width": int(-w), "height": int(h),
                "text": "fit %dx%d" % (-w, h)}
    if w > 0 and h > 0:
        return {"mode": "exact", "width": int(w), "height": int(h), "text": "%dx%d" % (w, h)}
    return {"mode": "source", "text": "source size"}


def parse_setting(path, source="builtin", group=""):
    with open(path, encoding="utf-8", errors="replace") as fh:
        t = fh.read()
    m = re.search(r'<setting name="([^"]*)"', t)
    if not m:
        return None
    key = m.group(1)
    name_key = re.search(r"<nameKey>([^<]*)</nameKey>", t)
    strings = display_strings()
    display = (strings.get(key) or (name_key and strings.get(name_key.group(1)))
               or urllib.parse.unquote(key))
    enc = re.search(r'<encoder name="([^"]*)"', t)
    ext = re.search(r"<file-extension>([^<]*)</file-extension>", t)
    venc = re.search(r'<video-encode[^>]*isEnabled="yes"[^>]*>(.*?)</video-encode>', t, re.S)
    vcodec, w, h = None, None, None
    if venc:
        c = (re.search(r"<codec-type>([^<]*)</codec-type>", venc.group(1))
             or re.search(r"<codec>([^<]*)</codec>", venc.group(1)))
        vcodec = c.group(1).strip() if c else None
        vcodec = MXF_CODECS.get(vcodec, vcodec)
        a = re.search(r"<automatic [^>]*>", venc.group(1))
        if a:
            w, h = _attr(a.group(), "width"), _attr(a.group(), "height")
            w, h = (float(w), float(h)) if w and h else (None, None)
    encoder = enc.group(1) if enc else None
    ext = ext.group(1).strip() if ext else ""
    sequence = encoder == "TIFF" and ext not in ("gif", "")
    if sequence:
        vcodec = ext
    has_audio = bool(re.search(r'<audio-encode[^>]*isEnabled="yes"', t)) or (encoder in (
        "CoreAudio", "MP3", "AC3") and not venc)
    return {
        "name": display, "key": key, "group": group, "source": source, "path": path,
        "encoder": encoder, "ext": ext, "video_codec": vcodec,
        "audio_only": not venc and not sequence, "image_sequence": sequence,
        "has_audio": has_audio, "size": size_spec(w, h),
    }


def _walk_settings(top, source):
    out = []
    if not os.path.isdir(top):
        return out
    for root, dirs, files in os.walk(top):
        dirs.sort()
        for f in sorted(files):
            if f.endswith(SETTING_EXTS):
                s = parse_setting(os.path.join(root, f), source,
                                  os.path.relpath(root, top) if root != top else "")
                if s:
                    out.append(s)
    return out


def all_settings(include_builtin=True):
    out = _walk_settings(USER_SETTINGS, "user")
    if include_builtin:
        out += _walk_settings(builtin_dir(), "builtin")
    return out


def resolve_setting(query):
    """Resolve a path, exact name, file stem or unique substring to one setting."""
    if os.path.isfile(os.path.expanduser(query)):
        s = parse_setting(os.path.abspath(os.path.expanduser(query)), "file")
        if not s:
            raise CmpError("%s is not a Compressor setting (no <setting name=...>)" % query)
        return s
    q = query.lower()
    items = all_settings()

    def stem(s):
        return os.path.splitext(os.path.basename(s["path"]))[0].lower()

    for test in (lambda s: s["name"].lower() == q,
                 lambda s: s["key"].lower() == q or stem(s) == q):
        hits = [s for s in items if test(s)]
        if hits:
            # Custom settings win over a same-named built-in, and QuickTime over MXF
            # ("Apple ProRes 422 Proxy" exists as both); --setting PATH picks exactly.
            hits.sort(key=lambda s: (s["source"] != "user", s["encoder"] == "MXF"))
            return hits[0]
    hits = [s for s in items if q in s["name"].lower() or q in stem(s)]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise CmpError("no setting matches %r — list them with cmp-settings.py" % query)
    names = "; ".join("%s [%s]" % (s["name"], s["group"] or s["source"]) for s in hits[:12])
    raise CmpError("%r is ambiguous (%d matches): %s" % (query, len(hits), names))


# --------------------------------------------------------------------- batches

def file_url(path):
    # Not percent-encoded: Compressor takes the URL text literally ("%20" fails).
    return "file://" + os.path.abspath(path)


def submit(jobs, batch_name, priority=None):
    """jobs: list of (source, setting_path, output_path). Returns (batch_id, [job_id])."""
    args = ["-batchname", batch_name]
    if priority:
        args += ["-priority", priority]
    for src, setting, out in jobs:
        args += ["-jobpath", file_url(src), "-settingpath", setting, "-locationpath", out]
    args += ["-outputformat", "json"]
    code, out, err = run_cli(args)
    try:
        start = out.index("{")
        batch = json.JSONDecoder().raw_decode(out, start)[0]["batch"]
    except (ValueError, KeyError):
        msg = (err.strip() or out.strip() or "no output").splitlines()
        raise CmpError("Compressor rejected the batch (exit %d): %s" % (code, " | ".join(msg[-3:])))
    return batch["batchID"], [j.get("jobID") for j in batch.get("jobs", [])]


def monitor_once(batch_id):
    """Return the batchStatus dict (with its 'jobs' list) or None if not visible yet.

    -monitor -once prints one or more JSON arrays; they are empty until the batch
    is registered, so take the last non-empty one.
    """
    _, out, _ = run_cli(["-monitor", "-batchid", batch_id, "-outputformat", "json", "-once"])
    dec, i, last = json.JSONDecoder(), 0, None
    while True:
        j = out.find("[", i)
        if j < 0:
            break
        try:
            obj, i = dec.raw_decode(out, j)
        except ValueError:
            i = j + 1
            continue
        if obj:
            last = obj
    if not last:
        return None
    for item in last:
        if "batchStatus" in item:
            bs = dict(item["batchStatus"])
            bs["jobs"] = [x.get("jobStatus", x) for x in bs.get("jobs", [])]
            return bs
    return None


def is_active(status):
    return not status or bool(ACTIVE.search(status))


def kill(batch_id):
    return run_cli(["-kill", "-batchid", batch_id])[0]


# --------------------------------------------------------------------- media

def ffprobe(path):
    exe = shutil.which("ffprobe")
    if not exe:
        raise CmpError("ffprobe not found (brew install ffmpeg)")
    p = subprocess.run([exe, "-v", "error", "-show_format", "-show_streams", "-of", "json",
                        path], capture_output=True, text=True)
    if p.returncode != 0:
        raise CmpError("ffprobe failed on %s: %s" % (path, p.stderr.strip()[:200]))
    return json.loads(p.stdout)


def media_facts(path):
    d = ffprobe(path)
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"
              and s.get("codec_name") not in (None, "unknown")), None)
    a = [s for s in d.get("streams", []) if s.get("codec_type") == "audio"]
    dur = d.get("format", {}).get("duration")
    fps = None
    if v and v.get("avg_frame_rate", "0/0") != "0/0":
        n, m = v["avg_frame_rate"].split("/")
        fps = float(n) / float(m) if float(m) else None
    return {
        "codec": v and v.get("codec_name"),
        "tag": v and v.get("codec_tag_string") if v and "[0]" not in v.get("codec_tag_string", "[0]") else None,
        "width": v and v.get("width"), "height": v and v.get("height"),
        "fps": fps, "duration": float(dur) if dur else None, "audio": len(a),
    }


def expected_size(spec, src_w, src_h):
    """Frame size a setting should produce for a source, or None if unknown."""
    if not src_w or not src_h:
        return None
    mode = spec.get("mode")
    if mode == "exact":
        return spec["width"], spec["height"]
    if mode == "percent":
        f = spec["percent"] / 100.0
        return int(round(src_w * f)), int(round(src_h * f))
    if mode == "fit":
        f = min(1.0, spec["width"] / float(src_w), spec["height"] / float(src_h))
        return int(round(src_w * f)), int(round(src_h * f))
    return src_w, src_h
