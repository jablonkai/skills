#!/usr/bin/env python3
"""Two-pass EBU R128 loudness normalization with an ebur128 read-back.

  ff_loudnorm.py IN -o OUT [--I -16] [--TP -1.5] [--LRA 11] [--acodec aac] [--abitrate 192k]

Pass 1 measures with loudnorm print_format=json; pass 2 feeds measured_I/TP/LRA/
thresh and target_offset back with linear=true. Video and other streams are
stream-copied. The output keeps the source sample rate (loudnorm itself resamples
to 192 kHz). When the file cannot reach the target linearly (true-peak headroom
too small), loudnorm falls back to dynamic mode; the report says which happened.
Presets: podcast/streaming -16 (stereo), EBU broadcast -23, Apple Music/Spotify -14/-16.
"""
import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ff_lib as L  # noqa: E402

DEFAULT_CODEC = {".mp4": "aac", ".m4a": "aac", ".mov": "aac", ".mkv": "aac", ".webm": "libopus",
                 ".opus": "libopus", ".mp3": "libmp3lame", ".wav": "pcm_s16le", ".flac": "flac"}


def measure(ffmpeg, path, target, extra=""):
    r = subprocess.run([ffmpeg, "-hide_banner", "-nostdin", "-nostats", "-i", path, "-map", "0:a:0", "-af",
                        f"loudnorm={target}{extra}:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    if r.returncode != 0 or not m:
        L.die(f"loudnorm measurement failed: {r.stderr.strip()[-500:]}")
    return json.loads(m.group(0))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--I", type=float, default=-16.0, help="integrated loudness target, LUFS")
    ap.add_argument("--TP", type=float, default=-1.5, help="true-peak ceiling, dBTP")
    ap.add_argument("--LRA", type=float, default=11.0, help="loudness range target, LU")
    ap.add_argument("--acodec", help="audio encoder (default: from the output extension)")
    ap.add_argument("--abitrate", default="192k")
    ap.add_argument("--ar", help="output sample rate (default: the source's)")
    ap.add_argument("--audio-only", action="store_true", help="drop video/subtitles")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ffmpeg = L.find_ffmpeg()
    info = L.probe(args.input)
    a = L.streams(info, "audio")
    if not a:
        L.die("input has no audio stream")
    if os.path.abspath(args.input) == os.path.abspath(args.output):
        L.die("output would overwrite the input")
    ext = os.path.splitext(args.output)[1].lower()
    codec = args.acodec or DEFAULT_CODEC.get(ext, "aac")
    rate = args.ar or a[0].get("sample_rate") or "48000"
    target = f"I={args.I}:TP={args.TP}:LRA={args.LRA}"

    m1 = measure(ffmpeg, args.input, target)
    print(f"pass 1: I={m1['input_i']} LUFS  TP={m1['input_tp']} dBTP  LRA={m1['input_lra']} LU  "
          f"thresh={m1['input_thresh']}", file=sys.stderr)
    feed = (f":measured_I={m1['input_i']}:measured_TP={m1['input_tp']}:measured_LRA={m1['input_lra']}"
            f":measured_thresh={m1['input_thresh']}:offset={m1['target_offset']}:linear=true")

    def encode(tp):
        af = f"loudnorm=I={args.I}:TP={tp}:LRA={args.LRA}{feed}"
        cmd = [ffmpeg, "-i", args.input]
        if args.audio_only:
            cmd += ["-map", "0:a:0", "-vn"]
        else:
            # keep every stream; only the first audio track is normalized, others are copied
            cmd += ["-map", "0", "-map", "-0:d?", "-c", "copy"]
        cmd += ["-filter:a:0", af, "-c:a:0", codec, "-ar:a:0", str(rate)]
        if codec not in ("pcm_s16le", "pcm_s24le", "flac"):
            cmd += ["-b:a:0", args.abitrate]
        if ext in (".mp4", ".mov", ".m4a"):
            cmd += ["-movflags", "+faststart"]
        cmd.append(args.output)
        L.run_ffmpeg(cmd, args.output, total=L.duration(info), dry_run=args.dry_run)

    def readback():
        r = subprocess.run([ffmpeg, "-hide_banner", "-nostats", "-i", args.output, "-map", "0:a:0", "-af",
                            "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
        tail = r.stderr[r.stderr.rfind("Summary:"):]
        mi = re.search(r"I:\s+(-?[\d.]+) LUFS", tail)
        mp = re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail)
        lra = re.search(r"LRA:\s+(-?[\d.]+) LU", tail)
        return (float(mi.group(1)), float(mp.group(1)), float(lra.group(1)) if lra else None)

    tp_used = args.TP
    encode(tp_used)
    if args.dry_run:
        return
    got_i, got_tp, got_lra = readback()
    if got_tp > args.TP + 0.1:
        # the limiter works at 192 kHz; resampling and lossy encoding add inter-sample overshoot
        tp_used = round(args.TP - (got_tp - args.TP) - 0.2, 2)
        print(f"true peak {got_tp} over the {args.TP} ceiling after encoding; re-running pass 2 with TP={tp_used}",
              file=sys.stderr)
        encode(tp_used)
        got_i, got_tp, got_lra = readback()
    mode = "linear" if float(m1["input_tp"]) + (args.I - float(m1["input_i"])) <= tp_used else "dynamic (true-peak limited)"
    ok = abs(got_i - args.I) <= 1.0 and got_tp <= args.TP + 0.1
    report = {"output": args.output, "target_I": args.I, "measured_I": got_i, "true_peak": got_tp,
              "lra": got_lra, "source_I": float(m1["input_i"]), "mode": mode, "tp_used": tp_used,
              "sample_rate": rate, "within_tolerance": ok}
    print(json.dumps(report))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
