#!/usr/bin/env python3
"""Check the Gyroflow install, or report what Gyroflow sees in each clip.

  gf-probe.py --check                 CLI path, version, sandbox status, ffprobe
  gf-probe.py CLIP|FOLDER... [--json] per clip: camera, gyro samples, size, fps, frames

A clip without gyro samples cannot be stabilized from embedded data: it needs an
external log (-g / --gyro-file, e.g. .gcsv or Betaflight blackbox) or a sidecar
<clip>.gcsv next to it.
"""

import argparse
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gf_lib as gf  # noqa: E402


def probe_motion(binary, sandboxed, path, gyro_file=None, timeout=120):
    """Run --export-metadata 2 and summarize the parsed motion data."""
    stage = gf.Stage(sandboxed)
    try:
        clip = stage.add(path) if sandboxed else path
        if not gyro_file:
            sidecar = os.path.splitext(path)[0] + ".gcsv"
            if os.path.isfile(sidecar):
                gyro_file = sidecar
        argv = [clip]
        if gyro_file:
            argv += ["-g", stage.add(gyro_file) if sandboxed else os.path.abspath(gyro_file)]
        meta_path = os.path.join(stage.out, "meta.json")
        argv += ["-f", "--export-metadata", f"2:{meta_path}"]
        res = gf.run_gyroflow(binary, argv, stage, timeout=timeout, stall=30)
        if not os.path.isfile(meta_path):
            reason = next((j.error for j in res.jobs.values() if j.error), None) \
                or (res.errors[-1] if res.errors else res.killed or "no metadata written")
            return {"readable": False, "error": reason}
        with open(meta_path, encoding="utf-8") as fh:
            meta = json.load(fh)
        ident = meta.get("camera_identifier") or {}
        imu = meta.get("raw_imu") or []
        quats = meta.get("quaternions") or {}
        return {"readable": True,
                "camera": meta.get("detected_source") or "",
                "lens_info": ident.get("lens_info") or "",
                "imu_samples": len(imu),
                "has_accelerometer": any(s.get("accl") for s in imu[:50]),
                "quaternions": bool(quats),
                "gyro_ok": bool(imu) or bool(quats),
                "gyro_file": gyro_file,
                "imu_orientation": meta.get("imu_orientation"),
                "embedded_lens_profile": meta.get("lens_profile") is not None}
    finally:
        stage.cleanup()


def check():
    try:
        binary = gf.find_bin()
    except gf.GFError as exc:
        print(exc, file=sys.stderr)
        return 2
    sandboxed = gf.is_sandboxed(binary)
    print(f"cli: {binary}")
    print(f"version: {gf.version(binary)}")
    print(f"sandboxed: {'yes (inputs are staged into ' + gf.RUNS_DIR + ')' if sandboxed else 'no'}")
    for tool in ("ffprobe", "ffmpeg"):
        print(f"{tool}: {shutil.which(tool) or 'MISSING (brew install ffmpeg) - needed for verification'}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="*")
    ap.add_argument("--check", action="store_true", help="report the install and exit")
    ap.add_argument("--recursive", action="store_true")
    ap.add_argument("-g", "--gyro-file", help="external gyro log to test against the clip")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.check:
        return check()
    if not args.inputs:
        ap.error("give clips or folders, or --check")
    try:
        binary = gf.find_bin()
        sandboxed = gf.is_sandboxed(binary)
        clips = gf.collect_inputs(args.inputs, args.recursive)
    except gf.GFError as exc:
        print(exc, file=sys.stderr)
        return 2
    rows = []
    for clip in clips:
        row = {"file": clip}
        info = gf.video_info(clip)
        if not info:
            row.update(readable=False, error="ffprobe cannot read a video stream")
        else:
            row.update({k: info[k] for k in ("codec", "width", "height", "fps", "frames", "duration")})
            row.update(probe_motion(binary, sandboxed, clip, args.gyro_file))
        rows.append(row)
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        for r in rows:
            if not r.get("readable"):
                print(f"{r['file']}: UNREADABLE - {r.get('error')}")
                continue
            gyro = (f"{r['imu_samples']} IMU samples" + (" +accel" if r["has_accelerometer"] else "")
                    if r["imu_samples"] else ("quaternions" if r["quaternions"] else "NO GYRO DATA"))
            src = f" from {os.path.basename(r['gyro_file'])}" if r.get("gyro_file") else ""
            print(f"{r['file']}: {r['camera'] or 'unknown camera'} {r['lens_info']}".rstrip()
                  + f" | {r['width']}x{r['height']} {r['fps']}fps {r['frames']} frames"
                  + f" {r['duration']:.2f}s | {gyro}{src}")
    return 0 if all(r.get("readable") and r.get("gyro_ok") for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
