#!/usr/bin/env python3
"""Download video, audio or subtitles with yt-dlp, then verify every output with ffprobe.

  ytdl_get.py URL... --out DIR [options]

Video:     --max-height 1080 --vcodec h264|hevc|av1|vp9 --container mp4|mkv|webm
           hard filters by default (fails when nothing matches); --prefer makes them soft (-S)
Audio:     --audio m4a|mp3|opus|flac|wav   (audio only; m4a/opus are kept without re-encoding when possible)
Sections:  --section 00:01:00-00:01:30 (repeatable; frame-accurate re-encode unless --keyframe-cut)
Subtitles: --subs hu,en [--auto-subs] [--sub-format srt|vtt|ass] [--subs-only]
Batches:   --items 1:3 (playlist items), --archive FILE (re-runs skip finished items)
Access:    --cookies-from-browser safari|chrome|firefox[:PROFILE]  (the user's own account only)
Other:     -o TEMPLATE (relative to --out), --dry-run, --summary FILE, --no-verify, -- EXTRA yt-dlp ARGS

Prints the exact yt-dlp command, streams yt-dlp's log, then a JSON summary on stdout:
files with their ffprobe facts, subtitle cue counts, archive skips and failed checks.
Exit 0 = downloaded (or nothing new) and verified, 1 = yt-dlp or a check failed, 2 = setup problem.
"""
import argparse
import json
import os
import shlex
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ytdl_lib import die, error_hints, find_ytdlp, hms, parse_subs, probe  # noqa: E402

VCODEC_FILTER = {
    "h264": "[vcodec^=avc1]",
    "hevc": "[vcodec~='^(hvc1|hev1)']",
    "av1": "[vcodec^=av01]",
    "vp9": "[vcodec~='^vp0?9']",
}
VCODEC_SORT = {"h264": "h264", "hevc": "h265", "av1": "av01", "vp9": "vp9"}
PROBE_VCODEC = {"h264": "h264", "hevc": "hevc", "av1": "av1", "vp9": "vp9"}
SUB_EXTS = (".srt", ".vtt", ".ass", ".ttml", ".lrc", ".json3", ".srv3")
MEDIA_EXTS = (".mp4", ".mkv", ".webm", ".mov", ".m4a", ".mp3", ".opus", ".ogg", ".flac", ".wav", ".aac")


def build_format(a):
    """Return the yt-dlp args selecting formats for a video or audio request."""
    if a.audio:
        best = "ba[ext=m4a]/ba" if a.audio in ("m4a", "aac") else "ba[acodec^=opus]/ba" if a.audio == "opus" else "ba"
        return ["-f", best, "-x", "--audio-format", a.audio]
    args = []
    filt = (f"[height<={a.max_height}]" if a.max_height else "") + (VCODEC_FILTER[a.vcodec] if a.vcodec else "")
    if a.prefer and filt:
        sort = ([f"res:{a.max_height}"] if a.max_height else []) + ([f"vcodec:{VCODEC_SORT[a.vcodec]}"] if a.vcodec else [])
        if a.container == "mp4":
            sort.append("acodec:aac")
        args += ["-f", "bv*+ba/b", "-S", ",".join(sort)]
    else:
        # MP4 holds AAC cleanly; Opus-in-MP4 plays badly in QuickTime and older players.
        audio = "ba[ext=m4a]/ba" if a.container == "mp4" else "ba"
        sel = [f"bv*{filt}+{x}" for x in audio.split("/")] + [f"b{filt}"]
        args += ["-f", "/".join(sel)]
    if a.container:
        args += ["--merge-output-format", a.container]
    return args


def build_command(a, ytdlp, paths_file):
    cmd = [ytdlp, "--no-progress", "--newline", "--paths", a.out, "-o", a.output,
           "--print-to-file", "after_move:filepath", paths_file]
    if not a.subs_only:
        cmd += build_format(a)
    else:
        cmd += ["--skip-download"]
    for sec in a.section or []:
        cmd += ["--download-sections", sec if sec.startswith("*") or not sec[0].isdigit() else "*" + sec]
    if a.section and not a.keyframe_cut:
        cmd += ["--force-keyframes-at-cuts"]
    if a.subs:
        if not a.auto_only:
            cmd += ["--write-subs"]
        if a.auto_subs or a.auto_only:
            cmd += ["--write-auto-subs"]
        cmd += ["--sub-langs", a.subs, "--convert-subs", a.sub_format]
    if a.items:
        cmd += ["-I", a.items]
    if a.archive:
        cmd += ["--download-archive", a.archive]
    if a.cookies_from_browser:
        cmd += ["--cookies-from-browser", a.cookies_from_browser]
    cmd += a.extra
    cmd += ["--"] + a.urls
    return cmd


def section_lengths(sections):
    out = []
    for sec in sections or []:
        s = sec.lstrip("*")
        if "-" not in s or not s[0].isdigit():
            return None  # chapter regex: length unknown
        start, end = s.split("-", 1)
        e = hms(end)
        if e is None:
            return None
        out.append(e - hms(start))
    return out


def verify_media(path, a, expected_len):
    info = probe(path)
    fails = []
    if "error" in info:
        return info, [f"ffprobe failed: {info['error']}"]
    if a.audio:
        if info["video_streams"]:
            fails.append("audio-only requested but the file has a video stream")
        if not info["audio_streams"]:
            fails.append("no audio stream")
    else:
        if not info["video_streams"]:
            fails.append("no video stream")
        if not info["audio_streams"]:
            fails.append("no audio stream (video-only format merged without audio?)")
        if a.max_height and not a.prefer and (info["height"] or 0) > a.max_height:
            fails.append(f"height {info['height']} > {a.max_height}")
        if a.vcodec and not a.prefer and info["vcodec"] != PROBE_VCODEC[a.vcodec]:
            fails.append(f"video codec {info['vcodec']} != {PROBE_VCODEC[a.vcodec]}")
        if a.container and not path.endswith("." + a.container):
            fails.append(f"container is {os.path.splitext(path)[1]}, not .{a.container}")
    if expected_len is not None and abs(info["duration"] - expected_len) > 2:
        fails.append(f"duration {info['duration']}s, section is {expected_len}s (±2)")
    return info, fails


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("urls", nargs="+")
    p.add_argument("--out", required=True, help="output folder (created if missing)")
    p.add_argument("-o", "--output", default=None,
                   help="output template relative to --out (default: '%%(title)s [%%(id)s].%%(ext)s', "
                        "with a playlist index prefix when --items or --archive is given)")
    p.add_argument("--max-height", type=int)
    p.add_argument("--vcodec", choices=sorted(VCODEC_FILTER))
    p.add_argument("--container", choices=["mp4", "mkv", "webm", "mov"])
    p.add_argument("--prefer", action="store_true", help="treat --max-height/--vcodec as preferences (-S), not filters")
    p.add_argument("--audio", choices=["m4a", "aac", "mp3", "opus", "flac", "wav", "vorbis"])
    p.add_argument("--section", action="append", help="START-END like 00:01:00-00:01:30 or 90-120 or a chapter regex")
    p.add_argument("--keyframe-cut", action="store_true", help="copy from the previous keyframe instead of re-encoding (keeps hidden pre-roll)")
    p.add_argument("--subs", help="subtitle languages, yt-dlp regex list: hu,en  or  'en.*,-live_chat'")
    p.add_argument("--auto-subs", action="store_true", help="also accept auto-generated captions")
    p.add_argument("--auto-only", action="store_true", help="only auto-generated captions")
    p.add_argument("--sub-format", default="srt", choices=["srt", "vtt", "ass", "lrc"])
    p.add_argument("--subs-only", action="store_true", help="subtitles only, no media download")
    p.add_argument("--items", help="playlist items, e.g. 1:3 or 1,4,-1")
    p.add_argument("--archive", help="download archive file; finished ids are recorded and skipped on re-runs")
    p.add_argument("--cookies-from-browser")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-verify", action="store_true")
    p.add_argument("--summary", help="also write the JSON summary to this file")
    argv = sys.argv[1:]
    extra = []
    if "--" in argv:
        i = argv.index("--")
        argv, extra = argv[:i], argv[i + 1:]
    a = p.parse_args(argv)
    a.extra = extra
    if a.audio and (a.max_height or a.vcodec or a.container):
        die("--audio is audio-only; drop --max-height/--vcodec/--container", 2)
    if a.subs_only and not a.subs:
        die("--subs-only needs --subs LANGS", 2)
    if a.container is None and not a.audio and not a.subs_only:
        a.container = "mkv" if a.vcodec == "vp9" else "mp4"
    if a.output is None:
        prefix = "%(playlist_index&{:03d} |)s" if (a.items or a.archive) else ""
        # a clip must not take the full video's name, or a later full download would be skipped as "already done"
        suffix = " %(section_start)d-%(section_end)ds" if a.section else ""
        a.output = prefix + "%(title)s [%(id)s]" + suffix + ".%(ext)s"
    if a.archive:
        a.archive = os.path.abspath(a.archive)
    a.out = os.path.abspath(a.out)

    ytdlp = find_ytdlp()
    fd, paths_file = tempfile.mkstemp(prefix="ytdl-paths-", suffix=".txt")
    os.close(fd)
    cmd = build_command(a, ytdlp, paths_file)
    shown = [c for c in cmd]
    i = shown.index("--print-to-file")
    del shown[i:i + 3]
    print("$ " + " ".join(shlex.quote(c) for c in shown), file=sys.stderr)
    if a.dry_run:
        os.unlink(paths_file)
        return 0

    os.makedirs(a.out, exist_ok=True)
    start = time.time() - 1
    log = []
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in proc.stdout:
        log.append(line)
        if not line.startswith("[download]  ") or "Destination" in line or "100%" in line:
            sys.stderr.write(line)
    rc = proc.wait()
    text = "".join(log)

    with open(paths_file, encoding="utf-8") as f:
        media = list(dict.fromkeys(l.strip() for l in f if l.strip()))
    os.unlink(paths_file)
    skipped = [l.split("]", 1)[1].split(":")[0].strip() for l in log if "already been recorded in the archive" in l]
    already = [l for l in log if "has already been downloaded" in l]

    subs = []
    for root, _, files in os.walk(a.out):
        for n in files:
            fp = os.path.join(root, n)
            if n.endswith(SUB_EXTS) and os.path.getmtime(fp) >= start:
                subs.append(fp)
    media = [m for m in media if not m.endswith(SUB_EXTS)]

    summary = {"command": shown, "returncode": rc, "files": [], "subtitles": [], "skipped_by_archive": skipped,
               "already_downloaded": len(already), "failed_checks": [], "hints": []}
    lens = section_lengths(a.section)
    expected = lens[0] if lens and len(lens) == 1 else None
    for m in media:
        if not os.path.exists(m):
            summary["failed_checks"].append(f"{m}: reported but missing")
            continue
        entry = {"path": m}
        if not a.no_verify and m.endswith(MEDIA_EXTS):
            info, fails = verify_media(m, a, expected)
            entry.update(info)
            summary["failed_checks"] += [f"{os.path.basename(m)}: {x}" for x in fails]
        summary["files"].append(entry)
    wanted = [l for l in (a.subs or "").split(",") if l and not l.startswith("-") and not any(c in l for c in ".*?[")]
    for s in sorted(subs):
        stem = os.path.basename(s).rsplit(".", 2)
        lang = stem[-2] if len(stem) == 3 else None
        entry = {"path": s, "lang": lang}
        entry.update(parse_subs(s) if s.endswith((".srt", ".vtt")) else {})
        if entry.get("cues") == 0:
            summary["failed_checks"].append(f"{os.path.basename(s)}: no cues")
        summary["subtitles"].append(entry)
    got = {e["lang"] for e in summary["subtitles"]}
    for w in wanted:
        if a.subs and not skipped and w not in got:
            summary["failed_checks"].append(
                f"no '{w}' subtitle written (missing, only auto-generated, or under another code like {w}-US/{w}-orig: "
                "check with ytdl_info.py URL --subs)")
    if a.subs_only and not media:
        stray = [n for n in os.listdir(a.out) if n.endswith(MEDIA_EXTS) and os.path.getmtime(os.path.join(a.out, n)) >= start]
        if stray:
            summary["failed_checks"].append(f"media written despite --subs-only: {stray}")
    if rc != 0:
        tail = [l.rstrip() for l in log if l.startswith(("ERROR", "WARNING"))][-5:]
        summary["errors"] = tail
        summary["hints"] = error_hints(text, ytdlp)
    elif not media and not subs and not skipped and not already:
        summary["failed_checks"].append("yt-dlp exited 0 but wrote nothing")

    out = json.dumps(summary, indent=2, ensure_ascii=False)
    print(out)
    if a.summary:
        with open(a.summary, "w", encoding="utf-8") as f:
            f.write(out + "\n")
    for h in summary["hints"]:
        print(f"hint: {h}", file=sys.stderr)
    return 1 if rc != 0 or summary["failed_checks"] else 0


if __name__ == "__main__":
    sys.exit(main())
