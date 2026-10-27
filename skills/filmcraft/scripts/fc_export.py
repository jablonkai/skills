#!/usr/bin/env python3
"""Export a FilmCraft sequence to one or more files in one process, then ffprobe every output.

    fc_export.py PROJECT.fcproj [--sequence ID|NAME] [--range entire|inOut|START-END]
                 [--overwrite] [--allow-offline] JOB...

JOB is OUT=PRESET[@SCALE] or OUT=fmt:FORMAT[@SCALE], e.g.
    yt.mp4="YouTube 1080p Full HD"   preview.mp4="YouTube 1080p Full HD@0.5"
    master.mov=fmt:prores            frames/f.png=fmt:png
--range defaults to entire, stated explicitly: FilmCraft's own default follows the in/out
points when they are set. START-END is seconds (e.g. 2-7.5). A preset with a fixed frame
size ignores scale, so @SCALE is turned into explicit width/height for those presets.

Refuses to overwrite existing outputs (without --overwrite) and to export an empty
sequence (FilmCraft writes a 1-frame file and exits 0). Each output is checked: video
frame count vs the range (±1 frame), codec and size; image sequences by file count.
Exit 1 when any job or check fails.
"""
import argparse
import glob
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fclib import TICKS, cli, ffprobe, fps_of, inspect  # noqa: E402

STILLS = {"png", "tiff", "tif", "bmp", "jpg", "jpeg", "tga", "dpx", "exr"}
AUDIO = {"wav", "aiff", "aif", "aac", "m4a", "flac"}


def presets():
    proc = cli("export", "--list-presets", "--compact", check=True)
    return {p["name"]: p for p in json.loads(proc.stdout)}


def pick_sequence(project, want):
    proj = inspect(project, "project")
    seqs = []

    def walk(node):
        for c in node.get("children", []):
            if c.get("type") == "Sequence":
                seqs.append(c)
            walk(c)
    walk(proj["root"])
    if want is None:
        return proj.get("activeSequence"), seqs
    for s in seqs:
        if str(s.get("item")) == str(want) or s.get("name") == want:
            return s["item"], seqs
    sys.exit(f"no sequence {want!r}; sequences: " + ", ".join(f"{s['name']} ({s['item']})" for s in seqs))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--sequence", help="sequence id or name (default: the project's active sequence)")
    ap.add_argument("--range", default="entire", help="entire | inOut | START-END in seconds")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--allow-offline", action="store_true", help="accept placeholder frames for offline media")
    ap.add_argument("jobs", nargs="+")
    a = ap.parse_args()

    project = os.path.abspath(a.project)
    seq_id, seqs = pick_sequence(project, a.sequence)
    if seq_id is None:
        sys.exit("the project has no active sequence; pass --sequence (" +
                 ", ".join(f"{s['name']} ({s['item']})" for s in seqs) + ")")

    seq = inspect(project, "sequence")
    if seq is None or seq.get("id") != seq_id:
        proc = cli("--project", project, "exec", "sequence.inspect", f"item={seq_id}", "--compact", check=True)
        seq = json.loads(proc.stdout)
    fps = fps_of(seq)
    total = seq["durationFrames"]
    clips = sum(len(t["items"]) for t in seq["video"] + seq["audio"])
    if total <= 1 or clips == 0:
        sys.exit(f"sequence {seq['name']} is empty ({clips} clips, {total} frames); nothing to export")

    params_range = {}
    if a.range == "entire":
        expect = total
        params_range = {"range": "entire"}
    elif a.range == "inOut":
        if seq.get("in") is None or seq.get("out") is None:
            sys.exit("--range inOut but the sequence has no in and out points")
        expect = round((seq["out"] - seq["in"]) * fps / TICKS) + 1  # the out frame is included
        params_range = {"range": "inOut"}
    else:
        m = re.fullmatch(r"([\d.]+)-([\d.]+)", a.range)
        if not m:
            sys.exit("--range must be entire, inOut or START-END (seconds)")
        start, end = float(m.group(1)), float(m.group(2))
        expect = round((end - start) * fps)
        params_range = {"range": "custom", "startSeconds": start, "endSeconds": end}

    known = presets()
    lines, checks = [], []
    for job in a.jobs:
        if "=" not in job:
            sys.exit(f"job must be OUT=PRESET[@SCALE] or OUT=fmt:FORMAT[@SCALE]: {job}")
        out, spec = job.split("=", 1)
        out = os.path.abspath(out)
        scale = 1.0
        if "@" in spec:
            spec, s = spec.rsplit("@", 1)
            scale = float(s)
        p = {"path": out, "sequence": seq_id, **params_range}
        size = [seq["settings"]["width"], seq["settings"]["height"]]
        if spec.startswith("fmt:"):
            fmt = spec[4:]
            p["format"] = fmt
        else:
            if spec not in known:
                close = [n for n in known if spec.lower() in n.lower()]
                sys.exit(f"no preset {spec!r}" + (f"; did you mean: {', '.join(close)}" if close else
                                                   " (filmcraft-cli export --list-presets)"))
            p["preset"] = spec
            fmt = known[spec]["format"]
            if known[spec].get("frameSize"):
                size = known[spec]["frameSize"]
        if scale != 1.0:
            w, h = (round(size[0] * scale / 2) * 2, round(size[1] * scale / 2) * 2)
            p.update(width=w, height=h)
        size = [p.get("width", size[0]), p.get("height", size[1])]
        if fmt not in STILLS and os.path.exists(out) and not a.overwrite:
            sys.exit(f"{out} exists; pass --overwrite or pick a new name")
        lines.append(json.dumps({"id": "file.exportMedia", "params": p}))
        checks.append((out, fmt, size))

    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
        f.write("\n".join(lines) + "\n")
        script = f.name
    proc = cli("--project", project, "run", script, "--compact")
    os.unlink(script)
    ok = True
    results = [json.loads(l) for l in proc.stdout.splitlines() if l.startswith("{")]
    for r in results:
        if not r.get("ok"):
            ok = False
            print(f"FAIL export: {r.get('error')}")
            continue
        off = (r.get("result") or {}).get("offlineMedia") or []
        if off and not a.allow_offline:
            ok = False
            print(f"OFFLINE MEDIA rendered as placeholders: {off}")
    if proc.returncode != 0 and ok:
        ok = False
        print(f"FAIL filmcraft-cli exit {proc.returncode}: {proc.stderr.strip()[-400:]}")

    print(f"sequence {seq['name']} ({seq_id}) @ {fps:g} fps, range {a.range}: expect {expect} frames "
          f"({expect / fps:.3f} s)")
    for out, fmt, size in checks:
        if fmt in STILLS:
            stem, ext = os.path.splitext(out)
            files = sorted(glob.glob(f"{glob.escape(stem)}*{ext}"))
            good = abs(len(files) - expect) <= 1
            print(f"{'ok  ' if good else 'FAIL'} {out}: {len(files)} stills (expect {expect})")
            ok &= good
            continue
        if not os.path.exists(out):
            print(f"FAIL {out}: not written")
            ok = False
            continue
        info = ffprobe(out)
        if fmt in AUDIO:
            good = abs(info["duration"] - expect / fps) <= 2 / fps
        else:
            frames = info.get("frames") or round(info["duration"] * fps)
            good = abs(frames - expect) <= 1 and [info.get("width"), info.get("height")] == list(size)
        print(f"{'ok  ' if good else 'FAIL'} {out}: {info.get('codec')} {info.get('width')}x{info.get('height')} "
              f"{info.get('frames')} frames {info['duration']:.3f} s audio={info.get('audio')} "
              f"(expect {size[0]}x{size[1]}, {expect} frames)")
        ok &= good
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
