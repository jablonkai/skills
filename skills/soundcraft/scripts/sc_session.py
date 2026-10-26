#!/usr/bin/env python3
"""Build or edit a SoundCraft session from a JSON spec, save it and optionally bounce it.

Usage:
  sc_session.py SPEC.json [--overwrite] [--dry-run]

Spec (times are seconds, "m:ss.fff" or "<n>smp"; paths resolve against the cwd):
  {
    "new":  {"name": "VO", "sample_rate": 48000, "bit_depth": 24},   # or
    "open": "in.scraft",
    "tracks": [
      {"name": "Voice", "file": "vo.wav", "at": 2.0, "gain_db": -2, "pan": 0,
       "volume_db": 0, "fade_in": 0.05, "fade_out": 0.5, "fade_shape": "s-curve",
       "inserts": [{"plugin": "eq_7band", "params": {"hpf_on": 1, "hpf_freq": 90}}]},
      {"name": "Music", "clips": [{"file": "bed.wav", "at": 0}],
       "fade_in": 2, "fade_out": 3,
       "duck": {"under": "Voice", "db": -12, "ramp": 0.3, "gap": 1.0},
       "automation": [{"param": "pan", "points": [[0, -0.5], [10, 0.5]]}]}
    ],
    "commands": [["markers.add", {"at": "0:05.000", "name": "Hit"}]],
    "save": "out/VO.scraft",
    "bounce": {"path": "out/VO.wav", "bit_depth": 24, "format": "wav",
               "start": null, "end": null, "normalize": false, "dither": true}
  }

A track with "file"/"clips" is created (or reused when it already exists) and the files
are imported onto it; a track without them must already exist in the opened session.
fade_in applies to the track's first clip, fade_out to its last; a clip entry may carry
its own fade_in/fade_out/gain_db; a track-level gain_db sets every clip on the track.
"pan" (-1..1) pans a mono track; on a stereo track it shifts the L/R pair keeping its
width, and a list [l, r] sets both knobs. "duck" writes volume automation that dips this track
by `db` under every clip of track `under` (spans closer than `gap` s are merged, with
`ramp` s slopes) relative to the track's volume_db.

Runs soundcraft-cli in two passes (structure, then clip-level edits that need the
clip ids the first pass created), reads the result back, and prints a JSON summary.
Refuses to overwrite an existing save/bounce or the opened session unless --overwrite.
"""

import argparse
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sclib import (ScError, cli, die, find_track, info, inspect,  # noqa: E402
                   result_lines, to_samples)


def line(cid, params=None):
    return "%s %s" % (cid, json.dumps(params if params is not None else {}))


def run_script(lines, session_in=None, save=None, dry=False, label=""):
    if dry:
        print("# --- %s" % label)
        print("\n".join(lines))
        return []
    fd, path = tempfile.mkstemp(suffix=".txt", prefix="sc_")
    with os.fdopen(fd, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    args = ["script", path]
    if session_in:
        args += ["--in", session_in]
    if save:
        args += ["--save", save]
    try:
        out = cli(*args)
    except ScError as exc:
        raise ScError("%s pass failed: %s (script kept at %s)" % (label, exc, path))
    os.remove(path)
    return result_lines(out)


def abspath(p):
    return os.path.abspath(os.path.expanduser(p))


def clip_list(track):
    if "clips" in track:
        return track["clips"]
    if "file" in track:
        return [{"file": track["file"], "at": track.get("at", 0)}]
    return []


def pan_values(pan, knobs):
    """[(index, value)]: a list sets knobs explicitly; a scalar pans a mono track, or
    shifts a stereo pair (L -1, R +1) by that amount, keeping its width."""
    if isinstance(pan, list):
        return list(enumerate(pan))
    if knobs < 2:
        return [(0, pan)]
    clamp = lambda v: max(-1.0, min(1.0, v))  # noqa: E731
    return [(0, clamp(-1.0 + pan)), (1, clamp(1.0 + pan))]


def duck_points(spans, rate, base, depth, ramp, gap):
    spans = sorted(spans)
    merged = []
    for s, e in spans:
        if merged and s - merged[-1][1] <= gap * rate:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    r = int(ramp * rate)
    pts = []
    for s, e in merged:
        if s - r > 0:
            pts.append((s - r, base))
        pts.append((max(0, s), base + depth))
        pts.append((e, base + depth))
        pts.append((e + r, base))
    return pts


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("spec")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the generated command scripts, run nothing")
    a = ap.parse_args()
    with open(a.spec) as fh:
        spec = json.load(fh)

    if ("new" in spec) == ("open" in spec):
        die("spec needs exactly one of `new` or `open`")
    if not spec.get("save"):
        die("spec needs `save` (the .scraft to write)")
    save = abspath(spec["save"])
    opened = abspath(spec["open"]) if "open" in spec else None
    bounce = dict(spec.get("bounce") or {})
    if bounce:
        if not bounce.get("path"):
            die("bounce needs `path`")
        bounce["path"] = abspath(bounce["path"])

    inputs = set()
    for t in spec.get("tracks", []):
        for c in clip_list(t):
            inputs.add(abspath(c["file"]))
    for f in inputs:
        if not os.path.exists(f):
            die("input file not found: " + f)
    if opened and not os.path.exists(opened):
        die("session not found: " + opened)
    if not a.overwrite and not a.dry_run:
        if save == opened:
            die("save would overwrite the opened session %s; pick a new path or pass "
                "--overwrite" % opened)
        if os.path.exists(save):
            die("%s exists; pass --overwrite to replace it" % save)
        if bounce and os.path.exists(bounce["path"]):
            die("%s exists; pass --overwrite to replace it" % bounce["path"])
    if bounce and bounce["path"] in inputs:
        die("bounce path is one of the input files")
    for d in {os.path.dirname(save)} | ({os.path.dirname(bounce["path"])} if bounce else set()):
        if not a.dry_run:
            os.makedirs(d, exist_ok=True)

    # sample rate for time conversion
    if opened:
        before = inspect(opened)
        rate = before["sample_rate"]
        existing = {t["name"] for t in before["tracks"]}
        knobs = {t["name"]: len(t["pan"]) for t in before["tracks"]}
    else:
        rate = int(spec["new"].get("sample_rate", 48000))
        existing = set()
        knobs = {}

    # ---- pass 1: session, tracks, imports, mixer, inserts ----------------------
    p1 = []
    if "new" in spec:
        p1.append(line("session.new", spec["new"]))
    for t in spec.get("tracks", []):
        name = t["name"]
        clips = clip_list(t)
        if clips and name not in existing:
            chans = max(info(abspath(c["file"])).get("channels", 1) for c in clips)
            p1.append(line("track.new", {"kind": "audio", "name": name,
                                         "format": "mono" if chans == 1 else "stereo"}))
            existing.add(name)
            knobs[name] = 1 if chans == 1 else 2
        for c in clips:
            p1.append(line("file.import_audio", {
                "path": abspath(c["file"]), "track": name, "new_tracks": False,
                "at": to_samples(c.get("at", 0), rate)}))
        if "volume_db" in t:
            p1.append(line("mix.volume", {"tracks": [name], "db": t["volume_db"]}))
        for ins in t.get("inserts", []):
            params = {"track": name, "plugin": ins["plugin"]}
            if "slot" in ins:
                params["slot"] = ins["slot"]
            if ins.get("params"):
                params["params"] = ins["params"]
            p1.append(line("mix.insert", params))
        for auto in t.get("automation", []):
            for at, value in auto["points"]:
                p1.append(line("automation.set_point", {
                    "track": name, "param": auto["param"],
                    "at": to_samples(at, rate), "value": value}))

    run_script(p1, session_in=opened, save=save, dry=a.dry_run, label="structure")
    if a.dry_run:
        doc = None
    else:
        doc = inspect(save)

    # ---- pass 2: clip fades, clip gain, ducking, raw commands, bounce ----------
    p2 = []
    for t in spec.get("tracks", []):
        name = t["name"]
        tr = find_track(doc, name) if doc else {"clips": [], "volume_db": 0.0}
        own = clip_list(t)
        imported = sorted(tr["clips"], key=lambda c: c["start"])
        # clip-level settings map onto the clips this spec imported, by position
        by_file = []
        if own and doc:
            starts = [to_samples(c.get("at", 0), rate) for c in own]
            for c, s in zip(own, starts):
                match = [x for x in imported if x["start"] == s]
                by_file.append((c, match[-1] if match else None))
        if "pan" in t:
            for idx, value in pan_values(t["pan"], len(tr["pan"]) if doc else knobs.get(name, 1)):
                p2.append(line("mix.pan", {"tracks": [name], "pan": value, "index": idx}))
        shape = t.get("fade_shape")
        targets = imported if imported else []
        if t.get("fade_in") and (targets or a.dry_run):
            p = {"clip": targets[0]["id"] if targets else "<first clip id>", "side": "in",
                 "length": to_samples(t["fade_in"], rate)}
            if shape:
                p["shape"] = shape
            p2.append(line("edit.fades_create", p))
        if t.get("fade_out") and (targets or a.dry_run):
            p = {"clip": targets[-1]["id"] if targets else "<last clip id>", "side": "out",
                 "length": to_samples(t["fade_out"], rate)}
            if shape:
                p["shape"] = shape
            p2.append(line("edit.fades_create", p))
        clip_gain_ids = [c["id"] for c in imported] if "gain_db" in t else []
        if clip_gain_ids:
            p2.append(line("clip.gain", {"clips": clip_gain_ids, "db": t["gain_db"]}))
        for c, hit in by_file:
            if hit is None:
                continue
            for side in ("in", "out"):
                if c.get("fade_" + side):
                    p2.append(line("edit.fades_create", {
                        "clip": hit["id"], "side": side,
                        "length": to_samples(c["fade_" + side], rate)}))
            if "gain_db" in c:
                p2.append(line("clip.gain", {"clips": [hit["id"]], "db": c["gain_db"]}))
        duck = t.get("duck")
        if duck:
            base = t.get("volume_db", tr.get("volume_db", 0.0))
            if not doc:
                p2.append("# duck %s under %s: breakpoints computed from pass-1 clips"
                          % (name, duck["under"]))
                continue
            under = find_track(doc, duck["under"])
            spans = [(c["start"], c["end"]) for c in under["clips"] if not c.get("muted")]
            for at, value in duck_points(spans, rate, base, float(duck.get("db", -12)),
                                         float(duck.get("ramp", 0.3)),
                                         float(duck.get("gap", 1.0))):
                p2.append(line("automation.set_point", {
                    "track": name, "param": "volume", "at": at, "value": value}))
    for cid, params in spec.get("commands", []):
        p2.append(line(cid, params))
    if bounce:
        b = {"path": bounce["path"]}
        for key in ("format", "bit_depth", "normalize", "dither", "source", "fold_down"):
            if key in bounce:
                b[key] = bounce[key]
        for key in ("start", "end"):
            if bounce.get(key) is not None:
                b[key] = to_samples(bounce[key], rate)
        p2.append(line("file.bounce_mix", b))

    results = []
    if p2:
        results = run_script(p2, session_in=save, save=save, dry=a.dry_run, label="edit")
    if a.dry_run:
        return

    doc = inspect(save)
    summary = {
        "session": save, "sample_rate": doc["sample_rate"], "bit_depth": doc["bit_depth"],
        "length_s": round(doc["length_samples"] / float(doc["sample_rate"]), 3),
        "tracks": [{
            "name": t["name"], "kind": t["kind"], "volume_db": t["volume_db"], "pan": t["pan"],
            "clips": [{"id": c["id"], "start_s": round(c["start"] / float(rate), 3),
                       "end_s": round(c["end"] / float(rate), 3), "gain_db": c["gain_db"],
                       "fade_in_s": round(c["fade_in"] / float(rate), 3),
                       "fade_out_s": round(c["fade_out"] / float(rate), 3)}
                      for c in t["clips"]],
            "inserts": [i["plugin"] for i in t["inserts"]],
            "automation": {x["param"]: len(x["points"]) for x in t["automation"]},
        } for t in doc["tracks"]],
    }
    for cid, value in results:
        if cid == "file.bounce_mix":
            summary["bounce"] = value
            summary["bounce"].update({k: info(bounce["path"])[k]
                                      for k in ("sample_rate", "sample_format", "channels")})
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    try:
        main()
    except ScError as exc:
        die(exc)
