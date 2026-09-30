"""Shared helpers for the handbrake skill scripts. Standard library only.

Locates HandBrakeCLI, pulls the labelled JSON blocks (`Version: {...}`,
`JSON Title Set: {...}`, `Progress: {...}`) out of its --json output, runs a
scan, resolves presets, and wraps ffprobe.
"""

import json
import os
import re
import shutil
import subprocess
import tempfile

VIDEO_EXTS = {".mp4", ".m4v", ".mov", ".mkv", ".webm", ".avi", ".wmv", ".flv",
              ".mpg", ".mpeg", ".m2ts", ".mts", ".ts", ".vob", ".3gp", ".ogv",
              ".dv", ".mxf"}
FORMATS = {"mp4": "av_mp4", "m4v": "av_mp4", "mov": "av_mov", "mkv": "av_mkv",
           "webm": "av_webm"}
EXT_FOR_FORMAT = {"av_mp4": ".mp4", "av_mov": ".mov", "av_mkv": ".mkv",
                  "av_webm": ".webm"}
TICKS = 90000  # HandBrake durations are in 90 kHz ticks
BLOCK = re.compile(r"^([A-Za-z][A-Za-z ]*): \{", re.M)


class HBError(Exception):
    pass


def find_cli():
    """Return the HandBrakeCLI path, or raise HBError with install hints."""
    for candidate in (os.environ.get("HANDBRAKE_CLI"),
                      shutil.which("HandBrakeCLI"),
                      "/opt/homebrew/bin/HandBrakeCLI",
                      "/usr/local/bin/HandBrakeCLI",
                      "/Applications/HandBrakeCLI"):
        if candidate and os.access(candidate, os.X_OK):
            return candidate
    raise HBError("HandBrakeCLI not found. Install it with `brew install handbrake` "
                  "(the HandBrake.app GUI does not include it), or download "
                  "HandBrakeCLI-<version>.dmg from handbrake.fr/downloads2.php, "
                  "or set HANDBRAKE_CLI=/path/to/HandBrakeCLI")


def json_blocks(text):
    """Yield (label, object) for every `Label: {...}` block in --json output."""
    decoder = json.JSONDecoder()
    for m in BLOCK.finditer(text):
        try:
            obj, _ = decoder.raw_decode(text, m.end() - 1)
        except json.JSONDecodeError:
            continue
        yield m.group(1), obj


def is_disc(path):
    """True for an ISO/IMG image or a DVD/Blu-ray folder structure."""
    if os.path.isfile(path):
        return os.path.splitext(path)[1].lower() in (".iso", ".img")
    if not os.path.isdir(path):
        return False
    base = os.path.basename(os.path.normpath(path)).upper()
    return (base in ("VIDEO_TS", "BDMV")
            or os.path.isdir(os.path.join(path, "VIDEO_TS"))
            or os.path.isdir(os.path.join(path, "BDMV")))


def collect_sources(paths, recursive=False, exts=None):
    """Expand files and folders to a list of (source, root) pairs.

    `root` is the folder the source was found under (for mirroring subfolders
    in the output), or None for sources given directly. Disc folders are one
    source each and are never descended into."""
    exts = {e.lower() if e.startswith(".") else "." + e.lower()
            for e in exts} if exts else VIDEO_EXTS
    found = []
    for path in paths:
        if is_disc(path) or os.path.isfile(path):
            found.append((path, None))
            continue
        if not os.path.isdir(path):
            raise HBError(f"not found: {path}")
        for dirpath, dirnames, filenames in os.walk(path):
            dirnames.sort()
            for d in list(dirnames):
                full = os.path.join(dirpath, d)
                if d.startswith("."):
                    dirnames.remove(d)
                elif is_disc(full):
                    found.append((full, path))
                    dirnames.remove(d)
            for name in sorted(filenames):
                if not name.startswith(".") and os.path.splitext(name)[1].lower() in exts:
                    found.append((os.path.join(dirpath, name), path))
            if not recursive:
                break
    return found


def scan(cli, source, title=0, min_duration=None, timeout=600):
    """Run a JSON scan and return the `JSON Title Set` object."""
    cmd = [cli, "-i", source, "-t", str(title), "--scan", "--json"]
    if min_duration is not None:
        cmd += ["--min-duration", str(min_duration)]
    proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                          timeout=timeout)
    for label, obj in json_blocks(proc.stdout):
        if label == "JSON Title Set":
            if not obj.get("TitleList"):
                raise HBError(f"no titles found in {source} (not a video, or all "
                              f"titles shorter than --min-duration)")
            return obj
    tail = [l for l in proc.stderr.splitlines() if not l.startswith("[")][-5:]
    raise HBError(f"scan failed for {source} (exit {proc.returncode}): "
                  + " | ".join(tail))


def seconds(duration):
    """HandBrake Duration dict → seconds."""
    if "Ticks" in duration:
        return duration["Ticks"] / TICKS
    return duration.get("Hours", 0) * 3600 + duration.get("Minutes", 0) * 60 \
        + duration.get("Seconds", 0)


def summarize_title(t):
    """Compact, stable view of one scanned title."""
    g = t.get("Geometry", {})
    fr = t.get("FrameRate", {})
    fps = round(fr["Num"] / fr["Den"], 3) if fr.get("Den") else None
    return {
        "title": t["Index"],
        "duration_s": round(seconds(t.get("Duration", {})), 3),
        "width": g.get("Width"), "height": g.get("Height"), "fps": fps,
        "video_codec": t.get("VideoCodec"),
        "chapters": len(t.get("ChapterList", [])),
        "name": t.get("Name"),
        "audio": [{"track": i, "lang": a.get("LanguageCode"),
                   "codec": a.get("CodecName"), "channels": a.get("ChannelLayout"),
                   "description": a.get("Description"),
                   "commentary": a.get("Attributes", {}).get("Commentary", False)}
                  for i, a in enumerate(t.get("AudioList", []), 1)],
        "subtitles": [{"track": i, "lang": s.get("LanguageCode"),
                       "format": s.get("Format"), "source": s.get("SourceName"),
                       "forced": s.get("Attributes", {}).get("Forced", False)}
                      for i, s in enumerate(t.get("SubtitleList", []), 1)],
    }


def resolve_preset(cli, name, preset_files=()):
    """Return the effective settings of a built-in or imported preset.

    Uses `-Z NAME --preset-export`, which writes the fully resolved preset."""
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "p.json")
        cmd = [cli]
        for f in preset_files:
            cmd += ["--preset-import-file", f]
        cmd += ["-Z", name, "--preset-export", "resolved", "--preset-export-file", out]
        proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                              timeout=60)
        if proc.returncode != 0 or not os.path.exists(out):
            raise HBError(f"preset not found: {name!r} (names are case-sensitive; "
                          f"list them with hb-preset.py)")
        with open(out, encoding="utf-8") as fh:
            return json.load(fh)["PresetList"][0]


def ffprobe(path):
    """ffprobe streams + format as a dict, or raise HBError."""
    if not shutil.which("ffprobe"):
        raise HBError("ffprobe not found (brew install ffmpeg)")
    proc = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json",
                           "-show_streams", "-show_format", path],
                          capture_output=True, text=True, errors="replace")
    if proc.returncode != 0:
        raise HBError(f"ffprobe failed on {path}: {proc.stderr.strip()[:200]}")
    return json.loads(proc.stdout)
