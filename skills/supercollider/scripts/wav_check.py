#!/usr/bin/env python3
"""Measure a SuperCollider render or take with ffmpeg/ffprobe and print JSON.

    wav_check.py TAKE.wav                       duration, loudness, true peak, onsets
    wav_check.py TAKE.wav --start 8 --end 16    only that window
    wav_check.py TAKE.wav --highpass 6000       loudness above 6 kHz (hi-hats, cymbals)
    wav_check.py TAKE.wav --expect-seconds 96 --tolerance 1.5
                                                exit 1 if the duration is off

Loudness is EBU R128 integrated (LUFS) with true peak (dBTP). "silent" is true when
integrated loudness is below -60 LUFS, which is what a muted or failed take gives.
Onsets count the ends of silences (below --silence-db for at least --min-gap s), plus
one if the take starts with sound: a rough note count for separated notes, not for
legato or a busy mix.
"""

import argparse
import json
import re
import subprocess
import sys
from types import SimpleNamespace


def ffprobe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"ffprobe failed: {out.stderr.strip()}")
    return float(out.stdout.strip())


def ffmpeg_filter(path, filters, start=None, end=None):
    cmd = ["ffmpeg", "-nostats", "-hide_banner"]
    if start is not None:
        cmd += ["-ss", str(start)]
    if end is not None:
        cmd += ["-to", str(end)]
    cmd += ["-i", path, "-af", filters, "-f", "null", "-"]
    return subprocess.run(cmd, capture_output=True, text=True).stderr


def loudness(path, args):
    chain = (f"highpass=f={args.highpass}," if args.highpass else "") + "ebur128=peak=true"
    log = ffmpeg_filter(path, chain, args.start, args.end)
    summary = log[log.rfind("Summary:"):]

    def grab(label):
        match = re.search(label + r":\s+(-?[\d.]+|-inf)", summary)
        if not match or match.group(1) == "-inf":
            return None
        return float(match.group(1))
    return grab(r"\bI"), grab("Peak"), grab("LRA")


def onsets(path, args, duration):
    log = ffmpeg_filter(path, f"silencedetect=n={args.silence_db}dB:d={args.min_gap}",
                        args.start, args.end)
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    window_end = (args.end if args.end is not None else duration) - (args.start or 0)
    # ffmpeg closes a trailing silence at end of file; that is not a new note
    new_notes = [e for e in ends if e < window_end - 0.02]
    count = len(new_notes) + (0 if starts and starts[0] <= 0.01 else 1)
    gaps = [round(e - s, 3) for s, e in zip(starts, ends)]
    return count, max(gaps) if gaps else 0.0


def measure(path, start=None, end=None, highpass=None, silence_db=-40, min_gap=0.05):
    """The report as a dict; sc.py calls this after every render and take."""
    args = SimpleNamespace(start=start, end=end, highpass=highpass,
                           silence_db=silence_db, min_gap=min_gap)
    duration = ffprobe_duration(path)
    integrated, true_peak, lra = loudness(path, args)
    count, longest_gap = onsets(path, args, duration)
    report = {
        "file": path,
        "duration_s": round(duration, 3),
        "integrated_lufs": integrated,
        "true_peak_dbtp": true_peak,
        "loudness_range_lu": lra,
        "silent": integrated is None or integrated < -60,
        "clipping": true_peak is not None and true_peak > 0,
        "onsets": count,
        "longest_silence_s": longest_gap,
    }
    if highpass:
        report["highpass_hz"] = highpass
    if start is not None or end is not None:
        report["window"] = [start, end]
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("wav")
    parser.add_argument("--start", type=float)
    parser.add_argument("--end", type=float)
    parser.add_argument("--highpass", type=float, help="measure only above this frequency (Hz)")
    parser.add_argument("--silence-db", type=float, default=-40)
    parser.add_argument("--min-gap", type=float, default=0.05)
    parser.add_argument("--expect-seconds", type=float)
    parser.add_argument("--tolerance", type=float, default=1.0)
    args = parser.parse_args()

    report = measure(args.wav, args.start, args.end, args.highpass,
                     args.silence_db, args.min_gap)
    ok = True
    if args.expect_seconds is not None:
        ok = abs(report["duration_s"] - args.expect_seconds) <= args.tolerance
        report["duration_ok"] = ok
    print(json.dumps(report, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
