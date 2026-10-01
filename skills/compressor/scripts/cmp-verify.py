#!/usr/bin/env python3
"""Check Compressor outputs with ffprobe against their sources and settings.

    python3 cmp-verify.py --summary SUMMARY.json [expectations]
    python3 cmp-verify.py OUTPUT... --source SRC [expectations]

With --summary (written by cmp-encode.py --summary) every job is checked:
  - Successful in Compressor, output present and non-empty
  - video codec matches the setting's FourCC (apco, avc1, hvc1, ...)
  - frame size matches what the setting does to this source
    (source size, N% of it, fit inside WxH, or exactly WxH)
  - duration within --duration-tolerance of the source (default 0.1 s);
    image sequences: frame count = source duration × fps (±1)
Skipped jobs (output already existed) are checked the same way.

Extra expectations, applied to every output:
  --codec apco|avc1|hvc1|h264|hevc|prores   FourCC or ffprobe codec name
  --size 1280x720                           exact frame size
  --audio                                   an audio stream (when the source has one)

Prints one line per output (or --json) and exits 1 if anything does not match.
"""

import argparse
import json
import os
import sys

from cmp_lib import CmpError, expected_size, media_facts, parse_setting

HEVC_TAGS = {"hvc1", "hev1"}


def codec_ok(facts, want):
    want = want.lower()
    tag, name = (facts["tag"] or "").lower(), (facts["codec"] or "").lower()
    if want in HEVC_TAGS:
        return tag in HEVC_TAGS or name == "hevc"
    return want in (tag, name)


def check(output, source, setting, a):
    problems, info = [], {}
    if setting and setting.get("image_sequence"):
        frames = sorted(f for f in os.listdir(output) if not f.startswith(".")) \
            if os.path.isdir(output) else []
        if not frames:
            return ["no frames in %s" % output], info
        info["frames"] = len(frames)
        facts = media_facts(os.path.join(output, frames[0]))
        if source:
            src = media_facts(source)
            if src["duration"] and src["fps"]:
                want = int(round(src["duration"] * src["fps"]))
                if abs(len(frames) - want) > 1:
                    problems.append("%d frames, source has %d" % (len(frames), want))
    else:
        if not os.path.isfile(output) or os.path.getsize(output) == 0:
            return ["missing or empty: %s" % output], info
        facts = media_facts(output)
        if source:
            src = media_facts(source)
            if src["duration"] and facts["duration"] is not None and \
                    abs(facts["duration"] - src["duration"]) > a.duration_tolerance:
                problems.append("duration %.3fs vs source %.3fs" % (facts["duration"], src["duration"]))
    info.update({"codec": facts["tag"] or facts["codec"], "size": "%sx%s" % (facts["width"], facts["height"]),
                 "duration": facts["duration"], "audio": facts["audio"]})
    if setting and setting.get("video_codec") and not setting.get("image_sequence") \
            and not codec_ok(facts, setting["video_codec"]):
        problems.append("codec %s, setting wants %s" % (info["codec"], setting["video_codec"]))
    if setting and source:
        src = media_facts(source)
        want = expected_size(setting["size"], src["width"], src["height"])
        if want and (abs(want[0] - (facts["width"] or 0)) > 2 or abs(want[1] - (facts["height"] or 0)) > 2):
            problems.append("size %s, expected %dx%d (%s)" % (info["size"], want[0], want[1],
                                                             setting["size"]["text"]))
    if a.codec and not codec_ok(facts, a.codec):
        problems.append("codec %s, expected %s" % (info["codec"], a.codec))
    if a.size and info["size"] != a.size:
        problems.append("size %s, expected %s" % (info["size"], a.size))
    if a.audio and not facts["audio"] and not (setting and setting.get("image_sequence")):
        # Only a fault when there was audio to carry over.
        if not source or media_facts(source)["audio"]:
            problems.append("no audio stream")
    return problems, info


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("outputs", nargs="*")
    ap.add_argument("--summary")
    ap.add_argument("--source", help="source to compare a single output against")
    ap.add_argument("--setting", help="setting path the outputs were made with")
    ap.add_argument("--codec")
    ap.add_argument("--size")
    ap.add_argument("--audio", action="store_true")
    ap.add_argument("--duration-tolerance", type=float, default=0.1)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    rows = []
    if a.summary:
        with open(a.summary) as fh:
            for j in json.load(fh)["jobs"]:
                rows.append((j["output"], j["source"], j.get("setting_path"), j["status"]))
    for o in a.outputs:
        rows.append((os.path.abspath(o), a.source, a.setting, None))
    if not rows:
        ap.error("give --summary or output files")

    results, bad = [], 0
    for output, source, setting_path, status in rows:
        try:
            setting = parse_setting(setting_path) if setting_path else None
            problems, info = check(output, source, setting, a)
        except (CmpError, OSError) as e:
            problems, info = [str(e)], {}
        if status and status != "Successful" and not status.startswith("skipped"):
            problems.insert(0, "Compressor status: %s" % status)
        bad += bool(problems)
        results.append(dict(output=output, ok=not problems, problems=problems, **info))
    if a.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            desc = ", ".join("%s=%s" % (k, r[k]) for k in ("codec", "size", "duration", "frames", "audio")
                             if k in r)
            print("%s %s  %s%s" % ("OK  " if r["ok"] else "FAIL", r["output"], desc,
                                   "" if r["ok"] else "  ← " + "; ".join(r["problems"])))
        print("%d/%d outputs OK" % (len(results) - bad, len(results)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
