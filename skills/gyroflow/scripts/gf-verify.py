#!/usr/bin/env python3
"""Verify stabilized outputs with ffprobe against their sources and expectations.

  gf-verify.py --summary SUMMARY.json [expectations]      outputs of a gf-render.py run
  gf-verify.py OUT... --source SRC... [expectations]      explicit pairs, in order
  gf-verify.py OUT...                  [expectations]      no source: only expectations

Expectations:
  --codec prores|h264|hevc|dnxhd|cfhd|av1   ffprobe codec_name
  --profile HQ                              ffprobe profile (ProRes: Proxy, LT, Standard, HQ, 4444, 4444 XQ)
  --size 1920x1080                          exact output size (default with a source: same as source)
  --audio / --no-audio                      audio stream present / absent
Against the source (always, when known): frame count and duration within
--frame-tolerance frames (default 1).

Exit 0 when everything passes, 1 otherwise. --json prints the per-file checks.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gf_lib as gf  # noqa: E402

CODEC_NAMES = {"prores": "prores", "h264": "h264", "h.264/avc": "h264", "hevc": "hevc",
               "h265": "hevc", "h.265/hevc": "hevc", "dnxhd": "dnxhd", "dnxhr": "dnxhd",
               "cineform": "cfhd", "cfhd": "cfhd", "av1": "av1"}


def check_one(out, src, args):
    checks = []

    def add(name, ok, detail):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    if not os.path.isfile(out):
        add("exists", False, out)
        return checks
    info = gf.video_info(out, count_frames=True)
    if not info:
        add("readable", False, "ffprobe finds no video stream")
        return checks
    add("readable", True, f"{info['codec']} {info['profile'] or ''} {info['width']}x{info['height']}")
    if args.codec:
        want = CODEC_NAMES.get(args.codec.lower(), args.codec.lower())
        add("codec", info["codec"] == want, f"{info['codec']} (want {want})")
    if args.profile:
        got = (info["profile"] or "").replace(" ", "").lower()
        add("profile", got == args.profile.replace(" ", "").lower(),
            f"{info['profile']} (want {args.profile})")
    sinfo = gf.video_info(src, count_frames=True) if src else None
    if args.size:
        w, _, h = args.size.lower().partition("x")
        add("size", (info["width"], info["height"]) == (int(w), int(h)),
            f"{info['width']}x{info['height']} (want {args.size})")
    elif sinfo:
        add("size", (info["width"], info["height"]) == (sinfo["width"], sinfo["height"]),
            f"{info['width']}x{info['height']} (source {sinfo['width']}x{sinfo['height']})")
    if sinfo:
        tol = args.frame_tolerance
        if info["frames"] is not None and sinfo["frames"] is not None:
            add("frames", abs(info["frames"] - sinfo["frames"]) <= tol,
                f"{info['frames']} (source {sinfo['frames']})")
        fps = sinfo["fps"] or info["fps"] or 30
        add("duration", abs(info["duration"] - sinfo["duration"]) <= (tol + 0.5) / fps,
            f"{info['duration']:.3f}s (source {sinfo['duration']:.3f}s)")
    if args.audio is not None:
        add("audio", (info["audio"] > 0) == args.audio,
            f"{info['audio']} audio stream(s) (want {'some' if args.audio else 'none'})")
    return checks


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("outputs", nargs="*")
    ap.add_argument("--summary", help="gf-render.py --summary file")
    ap.add_argument("--source", nargs="*", default=[], help="source clips, same order as outputs")
    ap.add_argument("--codec")
    ap.add_argument("--profile")
    ap.add_argument("--size")
    ap.add_argument("--audio", dest="audio", action="store_true", default=None)
    ap.add_argument("--no-audio", dest="audio", action="store_false")
    ap.add_argument("--frame-tolerance", type=int, default=1)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    pairs = []
    if args.summary:
        with open(args.summary, encoding="utf-8") as fh:
            summary = json.load(fh)
        for job in summary.get("jobs", []):
            if job.get("status") in ("done", "skipped"):
                pairs.append((job["output"], job["source"]))
            else:
                pairs.append((None, job["source"], job.get("status"), job.get("reason")))
    if args.source and len(args.source) != len(args.outputs):
        ap.error("--source needs one clip per output")
    for i, out in enumerate(args.outputs):
        pairs.append((out, args.source[i] if args.source else None))
    if not pairs:
        ap.error("nothing to verify")

    results, ok_all = [], True
    for pair in pairs:
        if pair[0] is None:
            row = {"output": None, "source": pair[1], "ok": False,
                   "checks": [{"check": "rendered", "ok": False, "detail": f"{pair[2]}: {pair[3]}"}]}
        else:
            checks = check_one(pair[0], pair[1], args)
            row = {"output": pair[0], "source": pair[1], "ok": all(c["ok"] for c in checks),
                   "checks": checks}
        ok_all &= row["ok"]
        results.append(row)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for row in results:
            name = row["output"] or row["source"]
            print(f"{'PASS' if row['ok'] else 'FAIL'} {name}")
            for c in row["checks"]:
                print(f"  {'ok  ' if c['ok'] else 'FAIL'} {c['check']}: {c['detail']}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
