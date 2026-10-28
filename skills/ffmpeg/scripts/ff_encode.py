#!/usr/bin/env python3
"""Delivery encodes and proxies for one file or whole folders.

  ff_encode.py SRC [SRC ...] (-o OUT | --out-dir DIR) --profile P [options] [--dry-run]

Profiles (software encoder / --hw VideoToolbox encoder):
  h264      libx264 CRF 20 / h264_videotoolbox q 65    MP4, AAC 192k   plays everywhere
  hevc      libx265 CRF 24 / hevc_videotoolbox q 60    MP4 hvc1-tagged (Apple players need the tag)
  av1       libsvtav1 CRF 32 preset 6                  MP4, Opus->AAC  smallest, slow-ish
  vp9       libvpx-vp9 CRF 32                          WebM, Opus      web
  prores    prores_ks HQ / prores_videotoolbox HQ      MOV, PCM        edit master (--prores proxy|lt|422|hq|4444|xq)
  proxy     prores_ks Proxy at half height (max 1080)  MOV, PCM        offline editing
  proxy-h264 libx264 CRF 23 veryfast, max 540p         MP4, AAC        light review copies

Options: --quality N (CRF for software encoders, 1-100 q for VideoToolbox, higher=better),
--max-res 1080 (short side, orientation-aware; --max-height caps the height literally), --fps 30, --audio copy|aac|none,
--recursive, --force, --timeout SEC, --summary FILE.json, -- EXTRA FFMPEG OUTPUT ARGS.
Existing complete outputs are skipped, so re-running resumes a batch.
"""
import argparse
import json
import os
import signal
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ff_lib as L  # noqa: E402

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".avi", ".mts", ".m2ts", ".mxf", ".webm", ".wmv", ".flv", ".mpg", ".ts", ".3gp"}
PRORES = {"proxy": 0, "lt": 1, "422": 2, "hq": 3, "4444": 4, "xq": 5}
PROFILES = {
    "h264": dict(ext=".mp4", sw="libx264", hw="h264_videotoolbox", q=20, hq=65, audio="aac"),
    "hevc": dict(ext=".mp4", sw="libx265", hw="hevc_videotoolbox", q=24, hq=60, audio="aac"),
    "av1": dict(ext=".mp4", sw="libsvtav1", hw=None, q=32, audio="aac"),
    "vp9": dict(ext=".webm", sw="libvpx-vp9", hw=None, q=32, audio="libopus"),
    "prores": dict(ext=".mov", sw="prores_ks", hw="prores_videotoolbox", audio="pcm_s16le"),
    "proxy": dict(ext=".mov", sw="prores_ks", hw="prores_videotoolbox", audio="pcm_s16le", height="half"),
    "proxy-h264": dict(ext=".mp4", sw="libx264", hw="h264_videotoolbox", q=23, hq=50, audio="aac", height=540),
}


def video_args(prof, name, a, src_w, src_h):
    enc = prof["hw"] if a.hw and prof.get("hw") else prof["sw"]
    if a.hw and not prof.get("hw"):
        print(f"note: no VideoToolbox encoder for {name}; using {enc}", file=sys.stderr)
    out = ["-c:v", enc]
    if enc in ("libx264", "libx265"):
        out += ["-crf", str(a.quality or prof["q"]), "-preset", a.preset or ("veryfast" if name == "proxy-h264" else "medium")]
    elif enc == "libsvtav1":
        out += ["-crf", str(a.quality or prof["q"]), "-preset", a.preset or "6"]
    elif enc == "libvpx-vp9":
        out += ["-crf", str(a.quality or prof["q"]), "-b:v", "0", "-row-mt", "1"]
    elif enc.endswith("_videotoolbox") and not enc.startswith("prores"):
        out += ["-q:v", str(a.quality or prof["hq"])]
    if enc.startswith("prores"):
        level = "proxy" if name == "proxy" and not a.prores else (a.prores or "hq")
        out += ["-profile:v", str(PRORES[level])]
        out += ["-pix_fmt", "yuva444p10le" if level in ("4444", "xq") else "yuv422p10le"] if enc == "prores_ks" else []
        if enc == "prores_ks":
            out += ["-vendor", "apl0"]
    elif enc in ("libx265", "hevc_videotoolbox"):
        out += ["-tag:v", "hvc1", "-pix_fmt", "yuv420p10le" if a.ten_bit else "yuv420p"]
    else:
        out += ["-pix_fmt", "yuv420p"]
    vf = []
    h = prof.get("height")
    src_short = min(src_w, src_h)
    if a.max_res:
        # "480p" names the short side: 1920x1080 -> 854x480, a 1080x1920 phone clip -> 480x854
        if src_short > a.max_res:
            sc = "scale=-2:%d" % even(a.max_res) if src_w >= src_h else "scale=%d:-2" % even(a.max_res)
            vf.append(sc + ",setsar=1")
    else:
        target = a.max_height or (min(1080, src_h // 2) if h == "half" else h)
        if target and src_h > target:
            # -2 rounds the width to even, which leaves a non-square SAR (e.g. 1280:1281) unless reset
            vf.append(f"scale=-2:{even(target)},setsar=1")
    if a.fps:
        vf.append(f"fps={a.fps}")
    if vf:
        out += ["-vf", ",".join(vf)]
    return out


def even(n):
    return int(n) // 2 * 2


def audio_args(prof, a, info, ext):
    if a.audio == "none" or not L.streams(info, "audio"):
        return ["-an"]
    if a.audio == "copy":
        return ["-c:a", "copy"]
    codec = prof["audio"]
    if codec == "aac":
        return ["-c:a", "aac", "-b:a", a.abitrate]
    if codec == "libopus":
        return ["-c:a", "libopus", "-b:a", "128k"]
    return ["-c:a", codec]


def complete(path, src_dur, ffprobe):
    try:
        info = L.probe(path, ffprobe)
    except SystemExit:
        return False
    return abs(L.duration(info) - src_dur) <= max(0.5, src_dur * 0.01)


def collect(srcs, recursive):
    out = []
    for s in srcs:
        if os.path.isdir(s):
            for root, dirs, files in os.walk(s):
                dirs[:] = [d for d in sorted(dirs) if not d.startswith(".")] if recursive else []
                out += [(os.path.join(root, f), os.path.relpath(root, s)) for f in sorted(files)
                        if os.path.splitext(f)[1].lower() in VIDEO_EXT and not f.startswith(".")]
        elif os.path.exists(s):
            out.append((s, "."))
        else:
            L.die(f"no such file or folder: {s}")
    return out


def main():
    argv = sys.argv[1:]
    extra = []
    if "--" in argv:
        i = argv.index("--")
        argv, extra = argv[:i], argv[i + 1:]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sources", nargs="+")
    ap.add_argument("-o", "--output")
    ap.add_argument("--out-dir")
    ap.add_argument("--profile", required=True, choices=sorted(PROFILES))
    ap.add_argument("--hw", action="store_true", help="use the VideoToolbox hardware encoder")
    ap.add_argument("--quality", type=int)
    ap.add_argument("--preset")
    ap.add_argument("--prores", choices=sorted(PRORES))
    ap.add_argument("--ten-bit", action="store_true", help="HEVC Main10")
    ap.add_argument("--max-res", type=int, help="cap the short side (480/720/1080), orientation-aware, never upscales")
    ap.add_argument("--max-height", type=int, help="cap the height literally (portrait 1080x1920 -> 270x480 at 480)")
    ap.add_argument("--fps")
    ap.add_argument("--audio", choices=("aac", "copy", "none"), default="aac")
    ap.add_argument("--abitrate", default="192k")
    ap.add_argument("--recursive", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--timeout", type=float, help="stop cleanly after SEC seconds (exit 124); re-run resumes")
    ap.add_argument("--summary")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if bool(a.output) == bool(a.out_dir):
        L.die("give exactly one of -o FILE or --out-dir DIR")
    ffmpeg = L.find_ffmpeg()
    ffprobe = L.ffprobe_for(ffmpeg)
    prof = PROFILES[a.profile]
    jobs = collect(a.sources, a.recursive)
    if a.output and len(jobs) != 1:
        L.die("-o takes a single source; use --out-dir for batches")
    plan, targets = [], {}
    for src, rel in jobs:
        out = a.output or os.path.normpath(os.path.join(a.out_dir, rel, os.path.splitext(os.path.basename(src))[0] + prof["ext"]))
        if os.path.abspath(out) == os.path.abspath(src):
            L.die(f"output would overwrite the source: {src}")
        if out in targets:
            L.die(f"{src} and {targets[out]} both map to {out}")
        targets[out] = src
        plan.append((src, out))

    stop = {"flag": False}
    signal.signal(signal.SIGTERM, lambda *_: stop.update(flag=True))
    t0, results = time.time(), []
    for src, out in plan:
        if stop["flag"] or (a.timeout and time.time() - t0 > a.timeout):
            results.append({"source": src, "output": out, "status": "pending"})
            continue
        info = L.probe(src, ffprobe)
        d = L.duration(info)
        if os.path.exists(out) and not a.force and complete(out, d, ffprobe):
            results.append({"source": src, "output": out, "status": "skipped"})
            print(f"skip (complete): {out}", file=sys.stderr)
            continue
        v = L.streams(info, "video")
        if not v:
            results.append({"source": src, "output": out, "status": "failed", "error": "no video stream"})
            continue
        cmd = [ffmpeg, "-i", src, "-map", "0:v:0", "-map", "0:a?", "-map_metadata", "0"]
        cmd += video_args(prof, a.profile, a, int(v[0].get("width", 0)), int(v[0].get("height", 0))) + audio_args(prof, a, info, prof["ext"])
        if prof["ext"] in (".mp4", ".mov"):
            cmd += ["-movflags", "+faststart+use_metadata_tags"]
        cmd += extra + [out]
        t1 = time.time()
        try:
            L.run_ffmpeg(cmd, out, total=d, dry_run=a.dry_run)
        except SystemExit as e:
            if e.code == 130:
                results.append({"source": src, "output": out, "status": "pending"})
                stop["flag"] = True
                continue
            results.append({"source": src, "output": out, "status": "failed"})
            continue
        if a.dry_run:
            results.append({"source": src, "output": out, "status": "planned"})
            continue
        oi = L.probe(out, ffprobe)
        ov = L.streams(oi, "video")[0]
        results.append({"source": src, "output": out, "status": "done", "seconds": round(time.time() - t1, 1),
                        "duration": round(L.duration(oi), 3), "codec": ov["codec_name"],
                        "size": f"{ov['width']}x{ov['height']}", "mb": round(os.path.getsize(out) / 1e6, 2),
                        "source_mb": round(os.path.getsize(src) / 1e6, 2)})
        print(f"done: {out}  {ov['codec_name']} {ov['width']}x{ov['height']}  "
              f"{results[-1]['mb']} MB (source {results[-1]['source_mb']} MB)", file=sys.stderr)
    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    summary = {"profile": a.profile, "hw": a.hw, "counts": counts, "jobs": results}
    if a.summary and not a.dry_run:
        with open(a.summary, "w") as fh:
            json.dump(summary, fh, indent=1)
    print(json.dumps(counts))
    if counts.get("failed"):
        sys.exit(1)
    if counts.get("pending"):
        sys.exit(124 if not stop["flag"] else 130)


if __name__ == "__main__":
    main()
