"""Shared helpers for the yt-dlp skill scripts (stdlib only, Python 3.9+).

- find_ytdlp(): the yt-dlp to run (YTDLP env var, PATH, Homebrew), exit 2 if missing
- install_method() / update_command(): brew, pip, pipx or standalone, and how to update it
- error_hints(): turns known yt-dlp failures into the next step to take
- probe(): ffprobe JSON summary of a media file
- parse_subs(): cue count, last cue end and text sample of an SRT/VTT file
"""
import json
import os
import re
import shutil
import subprocess
import sys


def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def find_ytdlp():
    for c in [os.environ.get("YTDLP"), shutil.which("yt-dlp"), "/opt/homebrew/bin/yt-dlp", "/usr/local/bin/yt-dlp"]:
        if c and os.access(c, os.X_OK):
            return c
    die("yt-dlp not found. Install: brew install yt-dlp  (or: python3 -m pip install -U 'yt-dlp[default]')", 2)


def find_ffprobe():
    return shutil.which("ffprobe") or next(
        (p for p in ["/opt/homebrew/bin/ffprobe", "/usr/local/bin/ffprobe"] if os.access(p, os.X_OK)), None)


def install_method(binary):
    real = os.path.realpath(binary)
    if "/Cellar/" in real:
        return "brew"
    if "/pipx/" in real:
        return "pipx"
    try:
        with open(real, "rb") as f:
            head = f.read(200)
    except OSError:
        head = b""
    if head.startswith(b"#!") and b"python" in head:
        return "pip"
    return "binary"


def update_command(binary):
    return {
        "brew": "brew update && brew upgrade yt-dlp",
        "pipx": "pipx upgrade yt-dlp",
        "pip": "python3 -m pip install -U 'yt-dlp[default]'",
        "binary": f"{binary} -U   (or --update-to nightly when stable is still broken)",
    }[install_method(binary)]


HINTS = [
    (r"Sign in to confirm|not a bot|HTTP Error 429",
     "the IP is bot-flagged (it usually clears within hours): stop retrying; options are waiting, another "
     "network, a PO token provider plugin (bgutil-ytdlp-pot-provider), or, after asking the user, "
     "--cookies-from-browser BROWSER with a secondary account; see references/gotchas.md"),
    (r"Unsupported URL|Unable to extract|nsig|signature|HTTP Error 403|Precondition check failed",
     "extractor failure: update yt-dlp ({update}) and retry once before anything else"),
    (r"Requested format is not available",
     "no format matches the hard filter: list what exists with ytdl_info.py URL --formats, "
     "then relax --max-height/--vcodec or pass --prefer for a soft preference"),
    (r"No supported JavaScript runtime|JS runtime|EJS",
     "YouTube needs a JavaScript runtime: brew install deno (or pass --js-runtimes node)"),
    (r"DRM|drm protected",
     "the content is DRM-protected; yt-dlp cannot and must not be used to circumvent DRM. Stop here."),
    (r"Private video|members-only|This video is available to this channel's members|age",
     "access-restricted: only with the user's own account (--cookies-from-browser BROWSER), never shared cookies"),
    (r"ffmpeg not found|ffprobe and ffmpeg not found",
     "merging, sections, audio extraction and subtitle conversion need ffmpeg: brew install ffmpeg"),
]


def error_hints(text, binary):
    out = []
    for pat, hint in HINTS:
        if re.search(pat, text, re.I):
            out.append(hint.format(update=update_command(binary)))
    return out


def probe(path):
    ffprobe = find_ffprobe()
    if not ffprobe:
        return {"error": "ffprobe not found"}
    r = subprocess.run([ffprobe, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return {"error": r.stderr.strip()[-300:]}
    d = json.loads(r.stdout)
    video = [s for s in d.get("streams", []) if s.get("codec_type") == "video"
             and not s.get("disposition", {}).get("attached_pic")]
    audio = [s for s in d.get("streams", []) if s.get("codec_type") == "audio"]
    v = video[0] if video else {}
    return {
        "container": d.get("format", {}).get("format_name"),
        "duration": round(float(d.get("format", {}).get("duration") or 0), 3),
        "vcodec": v.get("codec_name"),
        "width": v.get("width"),
        "height": v.get("height"),
        "acodec": audio[0].get("codec_name") if audio else None,
        "video_streams": len(video),
        "audio_streams": len(audio),
    }


_TS = re.compile(r"(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{3})\s*-->\s*(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{3})")


def parse_subs(path):
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        text = f.read()
    cues, last_end, words = 0, 0.0, []
    for line in text.splitlines():
        m = _TS.search(line)
        if m:
            cues += 1
            h, mi, s, ms = (int(x or 0) for x in m.groups()[4:])
            last_end = max(last_end, h * 3600 + mi * 60 + s + ms / 1000)
        elif line.strip() and not line.strip().isdigit() and not line.startswith(("WEBVTT", "Kind:", "Language:")):
            words.append(line.strip())
    return {"cues": cues, "last_cue_end": round(last_end, 3), "sample": " / ".join(words[:3])[:120]}


def hms(value):
    """'1:30', '00:01:30', '90', '90.5' -> seconds; 'inf' -> None."""
    if value in ("inf", ""):
        return None
    parts = [float(p) for p in value.split(":")]
    secs = 0.0
    for p in parts:
        secs = secs * 60 + p
    return secs
