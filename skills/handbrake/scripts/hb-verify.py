#!/usr/bin/env python3
"""Check encoded outputs with ffprobe against what was asked for.

    python3 hb-verify.py (--summary hb-summary.json | OUTPUT...) [expectations]

Expectations (each applies to every output checked):
  --codec hevc|h264|av1|vp9|prores   video codec (ffprobe codec_name)
  --max-res 1080p                     fits the resolution class in its own orientation
                                      (landscape <= 1920x1080, portrait <= 1080x1920)
  --max-height N / --height N         picture height at most / exactly N
  --square-pixels                     sample aspect ratio 1:1 (no anamorphic stretch)
  --container mp4|mkv|mov|webm        container family
  --audio-count N                     number of audio streams
  --audio-langs eng,hun               audio stream languages, in this order
  --audio-codec aac|opus|ac3|...      every audio stream's codec
  --subtitle-count N                  number of subtitle streams (0 = none, e.g. after burn-in)
  --source FILE                       compare duration with this source (single output)
  --duration-tolerance SEC            allowed duration difference (default 0.5)

With --summary (written by hb-encode.py --summary) every job with status done
is checked, and its duration is compared with the scanned source duration;
jobs that failed or were stopped count as failures. Prints one JSON line per
output and exits 1 if anything does not match. Needs ffprobe only.
"""

import argparse
import json
import os
import sys

from hb_lib import HBError, ffprobe

RES = {"480p": 480, "576p": 576, "720p": 720, "1080p": 1080, "1440p": 1440,
       "2160p": 2160, "4k": 2160}
CONTAINERS = {"mp4": ("mp4", "mov"), "mov": ("mov",), "mkv": ("matroska",),
              "webm": ("webm", "matroska")}


def facts(path):
    d = ffprobe(path)
    streams = d.get("streams", [])
    video = [s for s in streams if s["codec_type"] == "video"
             and not s.get("disposition", {}).get("attached_pic")]
    audio = [s for s in streams if s["codec_type"] == "audio"]
    subs = [s for s in streams if s["codec_type"] == "subtitle"]
    v = video[0] if video else {}
    return {
        "format": d.get("format", {}).get("format_name"),
        "duration_s": round(float(d.get("format", {}).get("duration", 0) or 0), 3),
        "video_codec": v.get("codec_name"), "width": v.get("width"),
        "height": v.get("height"), "pix_fmt": v.get("pix_fmt"),
        "sar": v.get("sample_aspect_ratio", "1:1"),
        "audio": [{"codec": a.get("codec_name"), "channels": a.get("channels"),
                   "lang": a.get("tags", {}).get("language", "und")} for a in audio],
        "subtitles": [{"codec": s.get("codec_name"),
                       "lang": s.get("tags", {}).get("language", "und")} for s in subs],
    }


def check(f, args, source_duration):
    bad = []
    if args.codec and f["video_codec"] != args.codec:
        bad.append(f"video codec {f['video_codec']} != {args.codec}")
    if args.max_res and f["width"] and f["height"]:
        short = RES[args.max_res]
        if min(f["width"], f["height"]) > short or max(f["width"], f["height"]) > round(short * 16 / 9):
            bad.append(f"{f['width']}x{f['height']} exceeds {args.max_res}")
    if args.max_height and (f["height"] or 0) > args.max_height:
        bad.append(f"height {f['height']} > {args.max_height}")
    if args.height and f["height"] != args.height:
        bad.append(f"height {f['height']} != {args.height}")
    if args.square_pixels and f["sar"] not in ("1:1", "0:1", None):
        bad.append(f"anamorphic output (SAR {f['sar']}, stored {f['width']}x{f['height']})")
    if args.container:
        fam = CONTAINERS[args.container]
        if not any(x in (f["format"] or "").split(",") for x in fam):
            bad.append(f"container {f['format']} is not {args.container}")
    if args.audio_count is not None and len(f["audio"]) != args.audio_count:
        bad.append(f"{len(f['audio'])} audio streams != {args.audio_count}")
    if args.audio_langs:
        want = [x.strip() for x in args.audio_langs.split(",")]
        got = [a["lang"] for a in f["audio"]]
        if got != want:
            bad.append(f"audio languages {got} != {want}")
    if args.audio_codec:
        wrong = [a["codec"] for a in f["audio"] if a["codec"] != args.audio_codec]
        if wrong:
            bad.append(f"audio codecs {wrong} != {args.audio_codec}")
    if args.subtitle_count is not None and len(f["subtitles"]) != args.subtitle_count:
        bad.append(f"{len(f['subtitles'])} subtitle streams != {args.subtitle_count}")
    if source_duration:
        diff = abs(f["duration_s"] - source_duration)
        if diff > args.duration_tolerance:
            bad.append(f"duration {f['duration_s']}s differs from source "
                       f"{source_duration}s by {diff:.2f}s")
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("outputs", nargs="*")
    ap.add_argument("--summary")
    ap.add_argument("--codec")
    ap.add_argument("--max-res", type=str.lower, choices=sorted(RES))
    ap.add_argument("--max-height", type=int)
    ap.add_argument("--height", type=int)
    ap.add_argument("--square-pixels", action="store_true")
    ap.add_argument("--container", choices=sorted(CONTAINERS))
    ap.add_argument("--audio-count", type=int)
    ap.add_argument("--audio-langs")
    ap.add_argument("--audio-codec")
    ap.add_argument("--subtitle-count", type=int)
    ap.add_argument("--source")
    ap.add_argument("--duration-tolerance", type=float, default=0.5)
    args = ap.parse_args()

    items = []  # (output, source_duration, prior failure)
    if args.summary:
        with open(args.summary, encoding="utf-8") as fh:
            for job in json.load(fh)["jobs"]:
                status = job.get("status")
                if status == "done" or (status == "skipped" and os.path.exists(job["output"])):
                    items.append((job["output"], job.get("source_duration_s"), None))
                else:
                    items.append((job["output"], None, f"job {status}: {job.get('reason', '')}"))
    for out in args.outputs:
        items.append((out, None, None))
    if not items:
        ap.error("give OUTPUT files or --summary")
    if args.source and len(items) != 1:
        ap.error("--source compares one output only")

    failed = 0
    for out, src_dur, prior in items:
        rec = {"output": out}
        try:
            if prior:
                raise HBError(prior)
            if args.source:
                src_dur = round(float(ffprobe(args.source)["format"]["duration"]), 3)
            f = facts(out)
            rec.update(f)
            problems = check(f, args, src_dur)
        except (HBError, OSError, KeyError, ValueError) as e:
            problems = [str(e)]
        rec["ok"] = not problems
        if problems:
            rec["problems"] = problems
            failed += 1
        print(json.dumps(rec, ensure_ascii=False))
    print(f"{len(items) - failed}/{len(items)} outputs OK", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
