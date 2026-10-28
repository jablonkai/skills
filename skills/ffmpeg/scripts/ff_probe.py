#!/usr/bin/env python3
"""Inspect media and verify outputs against expectations.

  ff_probe.py FILE...                         one-line-per-stream summary
  ff_probe.py FILE --json                     condensed JSON (format + streams)
  ff_probe.py FILE --keyframes [--near T]     keyframe times (or the ones around T)
  ff_probe.py FILE --loudness                 EBU R128 integrated loudness, LRA, true peak
  ff_probe.py FILE --expect duration=12,vcodec=h264,size=1920x1080,streams=v1a1,arate=48000
      exit 1 and list mismatches when the file does not match.  Keys:
      duration=S[±tol] (default ±0.25)  vcodec  acodec  size=WxH  fps  streams=vNaNsN
      arate  pix_fmt  container (format_name contains)  loudness=I[±tol]  tp_max=dBTP
"""
import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ff_lib as L  # noqa: E402


def summary(path, info):
    f = info["format"]
    print(f"{path}: {f.get('format_name')}  {L.duration(info):.3f}s  {int(f.get('size', 0)) / 1e6:.1f} MB"
          f"  {int(f.get('bit_rate', 0)) // 1000} kb/s")
    for s in info["streams"]:
        k = s["codec_type"]
        line = f"  #{s['index']} {k} {s.get('codec_name')}"
        if k == "video":
            line += f" {s.get('width')}x{s.get('height')} {L.fps(s):.3f}fps {s.get('pix_fmt')}"
            rot = [d.get("rotation") for d in s.get("side_data_list", []) if "rotation" in d]
            if rot:
                line += f" rotation={rot[0]}"
            if s.get("sample_aspect_ratio") not in (None, "1:1", "0:1"):
                line += f" SAR={s['sample_aspect_ratio']}"
        elif k == "audio":
            line += f" {s.get('sample_rate')}Hz {s.get('channels')}ch"
        lang = s.get("tags", {}).get("language")
        if lang:
            line += f" [{lang}]"
        if s.get("duration"):
            line += f" {float(s['duration']):.3f}s"
        print(line)


def loudness(path, ffmpeg):
    r = subprocess.run([ffmpeg, "-hide_banner", "-nostats", "-i", path, "-map", "0:a:0",
                        "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    tail = r.stderr[r.stderr.rfind("Summary:"):]
    g = lambda pat: (lambda m: float(m.group(1)) if m else None)(re.search(pat, tail))  # noqa: E731
    return {"I": g(r"I:\s+(-?[\d.]+) LUFS"), "LRA": g(r"LRA:\s+(-?[\d.]+) LU"),
            "TP": g(r"Peak:\s+(-?[\d.]+) dBFS")}


def tol(v, default):
    m = re.match(r"^(-?[\d.:]+)(?:±|\+-|~)([\d.]+)$", v)
    return (L.parse_time(m.group(1)), float(m.group(2))) if m else (L.parse_time(v), default)


def check(path, info, expect, ffmpeg):
    bad, v, a = [], L.streams(info, "video"), L.streams(info, "audio")
    loud = None
    for item in expect.split(","):
        key, _, want = item.partition("=")
        key = key.strip()
        if key == "duration":
            t, d = tol(want, 0.25)
            got = L.duration(info)
            ok = abs(got - t) <= d
            got = f"{got:.3f}"
        elif key == "vcodec":
            got = v[0]["codec_name"] if v else None
            ok = got == want
        elif key == "acodec":
            got = a[0]["codec_name"] if a else None
            ok = got == want
        elif key == "size":
            got = f"{v[0]['width']}x{v[0]['height']}" if v else None
            ok = got == want
        elif key == "fps":
            got = round(L.fps(v[0]), 3) if v else None
            ok = got is not None and abs(got - float(want)) < 0.01
        elif key == "streams":
            got = "v%da%ds%d" % (len(v), len(a), len(L.streams(info, "subtitle")))
            ok = all(f"{c}{n}" in got for c, n in re.findall(r"([vas])(\d+)", want))
        elif key == "arate":
            got = a[0].get("sample_rate") if a else None
            ok = got == want
        elif key == "pix_fmt":
            got = v[0].get("pix_fmt") if v else None
            ok = got == want
        elif key == "container":
            got = info["format"].get("format_name")
            ok = want in (got or "")
        elif key in ("loudness", "tp_max"):
            loud = loud or loudness(path, ffmpeg)
            if key == "loudness":
                t, d = tol(want, 1.0)
                got = loud["I"]
                ok = got is not None and abs(got - t) <= d
            else:
                got = loud["TP"]
                ok = got is not None and got <= float(want) + 0.1
        else:
            L.die(f"unknown expectation key: {key}")
        if not ok:
            bad.append(f"{key}: want {want}, got {got}")
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--keyframes", action="store_true")
    ap.add_argument("--near", help="with --keyframes: show the keyframes around this time")
    ap.add_argument("--loudness", action="store_true")
    ap.add_argument("--expect")
    args = ap.parse_args()
    ffmpeg = L.find_ffmpeg()
    ffprobe = L.ffprobe_for(ffmpeg)
    failed = 0
    for path in args.files:
        info = L.probe(path, ffprobe)
        if args.json:
            keep = ("index", "codec_type", "codec_name", "profile", "width", "height", "pix_fmt", "avg_frame_rate",
                    "sample_rate", "channels", "channel_layout", "duration", "bit_rate", "tags", "sample_aspect_ratio")
            print(json.dumps({"file": path, "format": {k: info["format"].get(k) for k in ("format_name", "duration", "size", "bit_rate")},
                              "streams": [{k: s[k] for k in keep if k in s} for s in info["streams"]]}, indent=1))
        elif not (args.keyframes or args.loudness or args.expect):
            summary(path, info)
        if args.keyframes:
            kf = L.keyframes(path, ffprobe)
            if args.near:
                t = L.parse_time(args.near)
                before = [k for k in kf if k <= t + 1e-3][-2:]
                after = [k for k in kf if k > t + 1e-3][:2]
                print(f"{path}: keyframes around {t}: {before} | {after}")
            else:
                gaps = [b - a for a, b in zip(kf, kf[1:])]
                print(f"{path}: {len(kf)} keyframes, max gap {max(gaps or [0]):.2f}s: "
                      + " ".join(f"{k:.3f}" for k in kf[:200]) + (" ..." if len(kf) > 200 else ""))
        if args.loudness:
            print(f"{path}: {json.dumps(loudness(path, ffmpeg))}")
        if args.expect:
            bad = check(path, info, args.expect, ffmpeg)
            print(f"{path}: {'OK' if not bad else 'MISMATCH'}" + "".join(f"\n  - {b}" for b in bad))
            failed += bool(bad)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
