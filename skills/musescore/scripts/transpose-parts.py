#!/usr/bin/env python3
"""Transpose a score and/or export its full score and individual parts.

    transpose-parts.py SCORE OUT_DIR [--to-key KEY | --interval IVL] [options]

Transposition (optional; without it the score is only split into parts):
  --to-key KEY        target concert key: C, Bb, F#, Eb, Am, F#m ... (minor = relative major's signature)
  --interval IVL      M2 m3 P4 P5 TT A4 d5 M6 m7 P8 ... (see --help-intervals)
  --direction D       up | down | closest (default: up for --interval, closest for --to-key)
  --no-chords         leave chord symbols untransposed
  --double-accidentals allow double sharps/flats instead of enharmonic respelling

Output:
  --formats F[,F]     full-score formats (default pdf); add musicxml, mscz, mid, mp3 ...
  --no-parts          skip part PDFs
  --combined          also write "<name>-Score_and_parts.pdf"
  --name NAME         output base name (default: SCORE's stem, plus "-in-<key>"/"-up-M2" when transposing)

Writes OUT_DIR/<name>.mscz (the transposed score, reusable), OUT_DIR/<name>.<fmt>
for each format, and OUT_DIR/<name>-<Part>.pdf for every part. The input is only
read. Prints a JSON summary with the resulting concert key (--score-meta) and the
files written; exit 1 if anything is missing.
"""

import argparse
import base64
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ms_lib  # noqa: E402

# MuseScore's interval list: the index is what --transpose's "transposeInterval" takes.
INTERVALS = ["P1", "A1", "d2", "m2", "M2", "A2", "d3", "m3", "M3", "A3", "d4", "P4", "A4", "d5",
             "P5", "A5", "d6", "m6", "M6", "A6", "d7", "m7", "M7", "A7", "d8", "P8"]
INTERVAL_ALIASES = {"TT": "A4", "unison": "P1", "octave": "P8"}
MAJOR = {"Cb": -7, "Gb": -6, "Db": -5, "Ab": -4, "Eb": -3, "Bb": -2, "F": -1, "C": 0,
         "G": 1, "D": 2, "A": 3, "E": 4, "B": 5, "F#": 6, "C#": 7}
MINOR = {"Ab": -7, "Eb": -6, "Bb": -5, "F": -4, "C": -3, "G": -2, "D": -1, "A": 0,
         "E": 1, "B": 2, "F#": 3, "C#": 4, "G#": 5, "D#": 6, "A#": 7}
FIFTHS_NAME = {v: k for k, v in MAJOR.items()}


def key_fifths(key):
    k = key.strip().replace("♭", "b").replace("♯", "#")
    lower = k.lower()
    for suffix in (" minor", "minor", " min", "min", "m"):
        if lower.endswith(suffix) and not lower.endswith("maj"):
            root = k[: len(k) - len(suffix)].strip()
            root = root[:1].upper() + root[1:]
            if root in MINOR:
                return MINOR[root]
    for suffix in (" major", "major", " maj", "maj"):
        if lower.endswith(suffix):
            k = k[: len(k) - len(suffix)].strip()
    k = k[:1].upper() + k[1:]
    if k in MAJOR:
        return MAJOR[k]
    raise SystemExit(f"unknown key {key!r} (want e.g. D, Bb, F#m, Eb major)")


def interval_index(ivl):
    i = INTERVAL_ALIASES.get(ivl, ivl)
    if i not in INTERVALS:
        raise SystemExit(f"unknown interval {ivl!r}; one of {' '.join(INTERVALS)} or TT")
    return INTERVALS.index(i)


def write_b64(data, path):
    with open(path, "wb") as fh:
        fh.write(base64.b64decode(data))
    return path


def main():
    if "--help-intervals" in sys.argv:
        print("\n".join(f"{i:2d} {n}" for i, n in enumerate(INTERVALS)))
        return 0
    if "-h" in sys.argv or "--help" in sys.argv or len(sys.argv) < 3:
        print(__doc__.strip())
        return 0 if len(sys.argv) >= 2 else 2
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("score")
    ap.add_argument("out_dir")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--to-key")
    g.add_argument("--interval")
    ap.add_argument("--direction", choices=["up", "down", "closest"])
    ap.add_argument("--no-chords", action="store_true")
    ap.add_argument("--double-accidentals", action="store_true")
    ap.add_argument("--formats", default="pdf")
    ap.add_argument("--no-parts", action="store_true")
    ap.add_argument("--combined", action="store_true")
    ap.add_argument("--name")
    a = ap.parse_args()

    src = os.path.abspath(a.score)
    if not os.path.exists(src):
        raise SystemExit(f"no such score: {a.score}")
    os.makedirs(a.out_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(src))[0]
    opts = None
    if a.to_key:
        target = key_fifths(a.to_key)
        opts = {"mode": "by_key", "targetKey": target, "direction": a.direction or "closest"}
        suffix = f"-in-{FIFTHS_NAME[target]}"
    elif a.interval:
        opts = {"mode": "by_interval", "transposeInterval": interval_index(a.interval),
                "direction": a.direction or "up"}
        suffix = f"-{opts['direction']}-{a.interval}"
    else:
        suffix = ""
    name = a.name or stem + suffix
    base = os.path.abspath(os.path.join(a.out_dir, name))
    if os.path.abspath(base + ".mscz") == src:
        raise SystemExit("output would overwrite the input; pass --name or another OUT_DIR")

    written, errors = [], []
    # 1. the working score: transposed (or a plain copy-conversion) as .mscz
    work = base + ".mscz"
    extra = []
    if opts:
        opts.update(transposeKeySignatures=True, transposeChordNames=not a.no_chords,
                    useDoubleSharpsFlats=a.double_accidentals)
        extra = ["--transpose", json.dumps(opts)]
    try:
        written += ms_lib.convert(src, work, extra=extra)
    except ms_lib.MuseScoreError as e:
        print(json.dumps({"ok": False, "error": str(e)}, indent=1))
        return 1

    # 2. full-score formats from the working score
    for fmt in [f.strip().lstrip(".") for f in a.formats.split(",") if f.strip()]:
        if fmt == "mscz":
            continue
        try:
            written += ms_lib.convert(work, f"{base}.{fmt}")
        except ms_lib.MuseScoreError as e:
            errors.append(str(e))

    # 3. parts (+ optional combined PDF) from one --score-parts-pdf call
    parts = []
    if not a.no_parts or a.combined:
        try:
            data = ms_lib.json_from_stdout(["--score-parts-pdf", work], timeout=300)
            if not a.no_parts:
                used = {}
                for pname, blob in zip(data.get("parts", []), data.get("partsBin", [])):
                    fname = ms_lib.safe_name(pname.replace("♭", "b").replace("♯", "#"))
                    used[fname] = used.get(fname, 0) + 1
                    if used[fname] > 1:
                        fname += f" {used[fname]}"
                    parts.append(pname)
                    written.append(write_b64(blob, f"{base}-{fname}.pdf"))
            if a.combined and data.get("scoreFullBin"):
                written.append(write_b64(data["scoreFullBin"], f"{base}-Score_and_parts.pdf"))
        except ms_lib.MuseScoreError as e:
            errors.append(str(e))

    meta = {}
    try:
        m = ms_lib.score_meta(work)
        meta = {"keysig": m.get("keysig"), "key": FIFTHS_NAME.get(m.get("keysig")),
                "measures": m.get("measures"), "pages": m.get("pages")}
    except ms_lib.MuseScoreError as e:
        errors.append(str(e))
    report = {"ok": not errors, "input": a.score, "transpose": opts, "concert_key_after": meta,
              "parts": parts, "written": [os.path.relpath(w) for w in written], "errors": errors}
    print(json.dumps(report, indent=1, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
