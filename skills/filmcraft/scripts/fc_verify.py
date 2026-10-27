#!/usr/bin/env python3
"""Read a FilmCraft project back and assert what a job promised. Exits 1 on a failed check.

    fc_verify.py show PROJECT.fcproj [--sequence ID|NAME]
        compact summary: tracks, clips in frames, transitions, markers, in/out
    fc_verify.py seq PROJECT.fcproj SPEC.json [--sequence ID|NAME]
        SPEC keys (all optional, frames at the sequence rate):
          {"name": "Rough", "fps": 25, "size": [1920, 1080], "duration": 300,
           "tracks": {"V1": [{"name": "a.mov", "start": 0, "frames": 100}, …],
                      "V2": [{"name": "Opening", "start": 0}]},
           "transitions": [{"track": "V1", "effect": "cross_dissolve", "at": 100}],
           "markers": [{"name": "Intro", "frame": 37}], "marker_count": 5,
           "in": 25, "out": 225}
        a track list must match clip for clip, in order; "at" is the cut the transition covers
    fc_verify.py media FILE [--codec h264] [--size 1920x1080] [--frames N | --seconds S] [--fps F]
        ffprobe an exported file (±1 frame)
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fclib import cli, ffprobe, fps_of, fr, inspect, summary  # noqa: E402


def load_seq(project, want):
    seq = inspect(project, "sequence")
    if want is None:
        return seq
    if seq and (str(seq.get("id")) == str(want) or seq.get("name") == want):
        return seq
    proj = inspect(project, "project")
    found = []

    def walk(node):
        for c in node.get("children", []):
            if c.get("type") == "Sequence" and (str(c.get("item")) == str(want) or c.get("name") == want):
                found.append(c["item"])
            walk(c)
    walk(proj["root"])
    if not found:
        sys.exit(f"no sequence {want!r} in {project}")
    proc = cli("--project", project, "exec", "sequence.inspect", f"item={found[0]}", "--compact", check=True)
    return json.loads(proc.stdout)


def track_of(seq, key):
    kind = "video" if key[0].upper() == "V" else "audio"
    if key[1:].isdigit():
        idx = int(key[1:]) - 1
        tracks = seq[kind]
        return tracks[idx] if idx < len(tracks) else None
    return next((t for t in seq["video"] + seq["audio"] if t["name"] == key), None)


def check_seq(seq, spec):
    fails, notes = [], []
    fps = fps_of(seq)

    def want(label, got, exp):
        (notes if got == exp else fails).append(f"{label}: got {got!r}, expected {exp!r}")

    if "name" in spec:
        want("sequence name", seq["name"], spec["name"])
    if "fps" in spec:
        want("fps", round(fps, 3), round(float(spec["fps"]), 3))
    if "size" in spec:
        want("size", [seq["settings"]["width"], seq["settings"]["height"]], list(spec["size"]))
    if "duration" in spec:
        want("duration frames", seq["durationFrames"], spec["duration"])
    for key, clips in (spec.get("tracks") or {}).items():
        t = track_of(seq, key)
        if t is None:
            fails.append(f"track {key}: missing")
            continue
        items = sorted(t["items"], key=lambda i: i["startFrame"])
        if len(items) != len(clips):
            fails.append(f"track {key}: {len(items)} clips "
                         f"({', '.join(str(i.get('name')) for i in items)}), expected {len(clips)}")
            continue
        for n, (got, exp) in enumerate(zip(items, clips), 1):
            if "name" in exp:
                want(f"{key} clip {n} name", got.get("name"), exp["name"])
            if "start" in exp:
                want(f"{key} clip {n} start", got["startFrame"], exp["start"])
            if "frames" in exp:
                want(f"{key} clip {n} frames", got["durationFrames"], exp["frames"])
    for exp in spec.get("transitions") or []:
        t = track_of(seq, exp.get("track", "V1"))
        trs = t.get("transitions", []) if t else []
        match = [x for x in trs if ("effect" not in exp or x["effect"] == exp["effect"])
                 and ("at" not in exp or fr(x["start"], fps) <= exp["at"] <= fr(x["start"] + x["duration"], fps))]
        (notes if match else fails).append(
            f"transition {exp}: {'found' if match else 'missing'} "
            f"(track has {[(x['effect'], fr(x['start'], fps), fr(x['duration'], fps)) for x in trs]})")
    marks = seq.get("markers", [])
    if "marker_count" in spec:
        want("marker count", len(marks), spec["marker_count"])
    for exp in spec.get("markers") or []:
        hit = [m for m in marks if ("name" not in exp or m["name"] == exp["name"])
               and ("frame" not in exp or fr(m["start"], fps) == exp["frame"])]
        (notes if hit else fails).append(
            f"marker {exp}: {'found' if hit else 'missing'}")
    for edge in ("in", "out"):
        if edge in spec:
            got = fr(seq[edge], fps) if seq.get(edge) is not None else None
            want(f"{edge} point frame", got, spec[edge])
    return fails, notes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("show")
    p.add_argument("project")
    p.add_argument("--sequence")
    p = sub.add_parser("seq")
    p.add_argument("project")
    p.add_argument("spec")
    p.add_argument("--sequence")
    p = sub.add_parser("media")
    p.add_argument("file")
    p.add_argument("--codec")
    p.add_argument("--size")
    p.add_argument("--frames", type=int)
    p.add_argument("--seconds", type=float)
    p.add_argument("--fps", type=float, default=25.0)
    a = ap.parse_args()

    if a.cmd == "show":
        summary(load_seq(os.path.abspath(a.project), a.sequence))
        return
    if a.cmd == "seq":
        seq = load_seq(os.path.abspath(a.project), a.sequence)
        if not seq:
            sys.exit("no active sequence")
        spec = json.load(open(a.spec, encoding="utf-8")) if os.path.exists(a.spec) else json.loads(a.spec)
        fails, notes = check_seq(seq, spec)
        for n in notes:
            print(f"ok   {n}")
        for f in fails:
            print(f"FAIL {f}")
        print(f"{len(notes)} ok, {len(fails)} failed")
        sys.exit(1 if fails else 0)

    info = ffprobe(a.file)
    if "error" in info:
        print(f"FAIL {a.file}: {info['error']}")
        sys.exit(1)
    fails = []
    if a.codec and info.get("codec") != a.codec:
        fails.append(f"codec {info.get('codec')} != {a.codec}")
    if a.size and f"{info.get('width')}x{info.get('height')}" != a.size:
        fails.append(f"size {info.get('width')}x{info.get('height')} != {a.size}")
    frames = info.get("frames") or round(info["duration"] * a.fps)
    if a.frames is not None and abs(frames - a.frames) > 1:
        fails.append(f"frames {frames} != {a.frames}")
    if a.seconds is not None and abs(info["duration"] - a.seconds) > 1.5 / a.fps:
        fails.append(f"duration {info['duration']:.3f} s != {a.seconds}")
    print(json.dumps({"file": a.file, **info}))
    for f in fails:
        print(f"FAIL {f}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
