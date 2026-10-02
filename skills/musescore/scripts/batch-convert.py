#!/usr/bin/env python3
"""Convert a folder of scores in one MuseScore launch per output kind (generated -j job files).

    batch-convert.py IN_DIR OUT_DIR --to pdf[,mp3,musicxml,...] [options]

Options:
  --to FMT[,FMT]      output formats: pdf png svg mp3 wav ogg flac mid musicxml mxl mscz brf
  --ext EXT[,EXT]     input extensions to pick up (default: every format MuseScore imports)
  --flat              write all outputs directly into OUT_DIR instead of mirroring sub-folders
  --overwrite         replace existing outputs (default: skip inputs whose outputs all exist)
  --sound-profile P   "MuseScore Basic" or "MuseSounds" for audio outputs
  --dry-run           print the job file and exit

Recursive; spaces and non-ASCII names are fine; inputs are only read and
OUT_DIR is never scanned for inputs. PNG/SVG come out page-numbered
(name-1.png ...). Prints OK/FAIL/SKIP per input and a SUMMARY line; exit 1 if
anything failed. Success is judged by the files on disk, not mscore's exit
code (it can abort at shutdown after writing everything). Score/image formats
and audio formats run as two separate jobs (mixing them in one job entry crashes
mscore 4.7). Inputs whose outputs are missing afterwards are retried once each.
"""

import argparse
import json
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ms_lib  # noqa: E402

IMPORTABLE = ["mscz", "mscx", "musicxml", "mxl", "xml", "mid", "midi", "kar", "md", "mgu", "sgu",
              "cap", "capx", "ove", "scw", "bmw", "bww", "gtp", "gp3", "gp4", "gp5", "gpx", "gp",
              "ptb", "mei"]
OUTPUTS = {"pdf", "png", "svg", "mp3", "wav", "ogg", "flac", "mid", "midi", "musicxml", "mxl",
           "mscz", "mscx", "brf", "mei"}
AUDIO = {"mp3", "wav", "ogg", "flac"}


def collect(in_dir, out_dir, exts):
    out_abs = os.path.abspath(out_dir)
    found = []
    for root, dirs, files in os.walk(in_dir):
        dirs[:] = sorted(d for d in dirs if not d.startswith(".")
                         and os.path.abspath(os.path.join(root, d)) != out_abs)
        for f in sorted(files):
            if f.startswith("."):
                continue
            if os.path.splitext(f)[1].lower().lstrip(".") in exts:
                found.append(os.path.join(root, f))
    return found


def targets(src, in_dir, out_dir, fmts, flat):
    rel = os.path.relpath(src, in_dir)
    stem = os.path.splitext(os.path.basename(rel) if flat else rel)[0]
    return [os.path.abspath(os.path.join(out_dir, f"{stem}.{fmt}")) for fmt in fmts]


def done(dst, since=None):
    files = ms_lib.expected_files(dst)
    files = [f for f in files if os.path.getsize(f) > 0 and (since is None or os.path.getmtime(f) >= since - 1)]
    return bool(files)


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("in_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--to", required=True)
    ap.add_argument("--ext")
    ap.add_argument("--flat", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--sound-profile")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("-h", "--help", action="store_true")
    if "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__.strip())
        return 0
    a = ap.parse_args()
    fmts = [f.strip().lower().lstrip(".") for f in a.to.split(",") if f.strip()]
    bad = [f for f in fmts if f not in OUTPUTS]
    if bad:
        print(f"unsupported output format(s): {', '.join(bad)}", file=sys.stderr)
        return 2
    exts = {e.strip().lower().lstrip(".") for e in (a.ext.split(",") if a.ext else IMPORTABLE) if e.strip()}
    if not os.path.isdir(a.in_dir):
        print(f"no such folder: {a.in_dir}", file=sys.stderr)
        return 2
    inputs = collect(a.in_dir, a.out_dir, exts)
    if not inputs:
        print(f"no inputs with extensions {sorted(exts)} under {a.in_dir}", file=sys.stderr)
        return 1

    plan, skipped = [], []
    for src in inputs:
        outs = targets(src, a.in_dir, a.out_dir, fmts, a.flat)
        if not a.overwrite and all(done(o) for o in outs):
            skipped.append(src)
            continue
        plan.append((os.path.abspath(src), outs))
    if a.flat:
        seen = {}
        for src, outs in plan:
            for o in outs:
                if o in seen:
                    print(f"--flat name clash: {seen[o]} and {src} both write {o}", file=sys.stderr)
                    return 2
                seen[o] = src
    job = [{"in": src, "out": outs} for src, outs in plan]
    if a.dry_run:
        print(json.dumps(job, indent=1, ensure_ascii=False))
        return 0
    for _, outs in plan:
        for o in outs:
            os.makedirs(os.path.dirname(o), exist_ok=True)
            if ms_lib.expected_files(o) and a.overwrite:
                for f in ms_lib.expected_files(o):
                    os.remove(f)

    extra = ["--sound-profile", a.sound_profile] if a.sound_profile and any(f in AUDIO for f in fmts) else []
    start = time.time()
    # A job entry that mixes audio with score/image outputs segfaults mscore 4.7, so audio
    # gets its own job: at most two launches per batch, however many files.
    for label, kinds in (("score", lambda f: f not in AUDIO), ("audio", lambda f: f in AUDIO)):
        sub = [{"in": e["in"], "out": [o for o in e["out"] if kinds(os.path.splitext(o)[1].lstrip("."))]}
               for e in job]
        sub = [e for e in sub if e["out"]]
        if not sub:
            continue
        per_file = 60 if label == "audio" else 20
        t0 = time.time()
        with tempfile.TemporaryDirectory() as tmp:
            rc = ms_lib.run_job(sub, os.path.join(tmp, "job.json"), timeout=60 + per_file * len(sub),
                                extra=extra if label == "audio" else ())
        print(f"JOB {label}: {len(sub)} input(s), 1 launch, mscore rc={rc}, {time.time() - t0:.1f}s")

    ok = fail = 0
    for src, outs in plan:
        missing = [o for o in outs if not done(o, start)]
        retried = False
        for o in missing:  # one individual retry per missing output
            try:
                ms_lib.convert(src, o, extra=extra)
                retried = True
            except ms_lib.MuseScoreError:
                pass
        missing = [o for o in outs if not done(o, start)]
        rel = os.path.relpath(src)
        if missing:
            fail += 1
            print(f"FAIL {rel} -> missing {', '.join(os.path.relpath(m) for m in missing)}")
        else:
            ok += 1
            written = [os.path.relpath(f) for o in outs for f in ms_lib.expected_files(o)]
            print(f"OK   {rel} -> {', '.join(written)}" + (" (retried)" if retried else ""))
    for src in skipped:
        print(f"SKIP {os.path.relpath(src)} (outputs exist; --overwrite to redo)")
    print(f"SUMMARY ok={ok} fail={fail} skip={len(skipped)}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
