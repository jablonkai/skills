#!/usr/bin/env python3
"""Read-back checks for SoundCraft results. Prints JSON; exit 1 if any check fails.

Usage:
  sc_verify.py audio FILE [--rate HZ] [--depth 16|24|32f] [--channels N]
                          [--seconds S] [--tol S] [--max-peak DB] [--peak DB] [--peak-tol DB]
                          [--level START:END]...
      Checks an audio file through `soundcraft-cli info`; peak/RMS are measured from
      the WAV samples. --level prints peak and RMS over a window (seconds), e.g. to
      compare a ducked span with an unducked one.
  sc_verify.py session FILE [--rate HZ] [--depth 16|24] [--tracks N] [--track NAME]...
                            [--inserts TRACK=plug1,plug2]... [--automation TRACK=param]...
                            [--clips TRACK=N]... [--fades TRACK]...
      Checks a .scraft through session.inspect. --inserts checks the exact insert
      order on that track; --fades requires a fade-in on the first clip and a fade-out
      on the last.
  sc_verify.py hash DIR [--compare MANIFEST.json]
      Without --compare prints a sha256 manifest of DIR; with it, fails on any changed,
      missing or added file. Snapshot inputs before a batch, compare after.
"""

import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sclib import ScError, die, find_track, info, inspect, wav_levels  # noqa: E402

DEPTHS = {"16": "Int16", "24": "Int24", "32": "Int32", "32f": "Float32"}


class Report(object):
    def __init__(self):
        self.checks = []
        self.data = {}

    def add(self, name, passed, detail=""):
        self.checks.append({"check": name, "passed": bool(passed), "detail": detail})

    def finish(self):
        ok = all(c["passed"] for c in self.checks)
        out = {"ok": ok, "checks": self.checks}
        out.update(self.data)
        print(json.dumps(out, indent=2, ensure_ascii=False))
        sys.exit(0 if ok else 1)


def check_audio(a, r):
    meta = info(a.file)
    r.data["info"] = meta
    if a.rate:
        r.add("rate", meta["sample_rate"] == a.rate, "%s Hz" % meta["sample_rate"])
    if a.depth:
        want = DEPTHS.get(a.depth, a.depth)
        r.add("depth", meta["sample_format"] == want, meta["sample_format"])
    if a.channels:
        r.add("channels", meta["channels"] == a.channels, str(meta["channels"]))
    if a.seconds is not None:
        r.add("duration", abs(meta["seconds"] - a.seconds) <= a.tol,
              "%.4f s (want %.4f ±%.4f)" % (meta["seconds"], a.seconds, a.tol))
    need_levels = a.max_peak is not None or a.peak is not None or a.level
    if need_levels and meta.get("format", "").lower() != "wav":
        r.add("levels", False, "peak/RMS checks need a WAV file")
        return
    if a.max_peak is not None or a.peak is not None:
        lv = wav_levels(a.file)
        r.data["levels"] = lv
        if a.max_peak is not None:
            r.add("max_peak", lv["peak_db"] <= a.max_peak,
                  "%.2f dBFS (max %.2f)" % (lv["peak_db"], a.max_peak))
        if a.peak is not None:
            r.add("peak", abs(lv["peak_db"] - a.peak) <= a.peak_tol,
                  "%.2f dBFS (want %.2f ±%.2f)" % (lv["peak_db"], a.peak, a.peak_tol))
    windows = []
    for spec in a.level or []:
        start, _, end = spec.partition(":")
        lv = wav_levels(a.file, float(start), float(end))
        windows.append({"window": spec, "peak_db": lv["peak_db"], "rms_db": lv["rms_db"]})
    if windows:
        r.data["windows"] = windows


def check_session(a, r):
    doc = inspect(a.file)
    r.data["tracks"] = [t["name"] for t in doc["tracks"]]
    if a.rate:
        r.add("rate", doc["sample_rate"] == a.rate, str(doc["sample_rate"]))
    if a.depth:
        want = DEPTHS.get(a.depth, a.depth)
        r.add("depth", doc["bit_depth"] == want, doc["bit_depth"])
    if a.tracks is not None:
        audio = [t for t in doc["tracks"] if t["kind"] != "master"]
        r.add("tracks", len(audio) == a.tracks, "%d non-master tracks" % len(audio))
    for name in a.track or []:
        try:
            find_track(doc, name)
            r.add("track %s" % name, True)
        except ScError as exc:
            r.add("track %s" % name, False, str(exc))
    for spec in a.inserts or []:
        name, _, plugs = spec.partition("=")
        want = [p for p in plugs.split(",") if p]
        try:
            have = [i["plugin"] for i in sorted(find_track(doc, name)["inserts"],
                                                key=lambda i: i["slot"])]
            r.add("inserts %s" % name, have == want, ",".join(have) or "(none)")
        except ScError as exc:
            r.add("inserts %s" % name, False, str(exc))
    for spec in a.automation or []:
        name, _, param = spec.partition("=")
        try:
            lanes = {x["param"]: len(x["points"]) for x in find_track(doc, name)["automation"]}
            r.add("automation %s.%s" % (name, param), lanes.get(param, 0) > 0,
                  "%d points" % lanes.get(param, 0))
        except ScError as exc:
            r.add("automation %s.%s" % (name, param), False, str(exc))
    for spec in a.clips or []:
        name, _, n = spec.partition("=")
        try:
            have = len(find_track(doc, name)["clips"])
            r.add("clips %s" % name, have == int(n), str(have))
        except ScError as exc:
            r.add("clips %s" % name, False, str(exc))
    for name in a.fades or []:
        try:
            clips = sorted(find_track(doc, name)["clips"], key=lambda c: c["start"])
            ok = bool(clips) and clips[0]["fade_in"] > 0 and clips[-1]["fade_out"] > 0
            r.add("fades %s" % name, ok, "in %s / out %s samples" % (
                clips[0]["fade_in"] if clips else "-", clips[-1]["fade_out"] if clips else "-"))
        except ScError as exc:
            r.add("fades %s" % name, False, str(exc))


def manifest(root):
    out = {}
    for base, _, files in os.walk(root):
        for f in sorted(files):
            p = os.path.join(base, f)
            h = hashlib.sha256()
            with open(p, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    h.update(chunk)
            out[os.path.relpath(p, root)] = h.hexdigest()
    return out


def check_hash(a, r):
    now = manifest(a.dir)
    if not a.compare:
        print(json.dumps(now, indent=2))
        sys.exit(0)
    with open(a.compare) as fh:
        before = json.load(fh)
    changed = sorted(k for k in before if k in now and now[k] != before[k])
    missing = sorted(k for k in before if k not in now)
    added = sorted(k for k in now if k not in before)
    r.add("unchanged", not changed, ", ".join(changed))
    r.add("none missing", not missing, ", ".join(missing))
    r.add("none added", not added, ", ".join(added))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="mode")
    au = sub.add_parser("audio")
    au.add_argument("file")
    au.add_argument("--rate", type=int)
    au.add_argument("--depth")
    au.add_argument("--channels", type=int)
    au.add_argument("--seconds", type=float)
    au.add_argument("--tol", type=float, default=0.01)
    au.add_argument("--max-peak", type=float)
    au.add_argument("--peak", type=float)
    au.add_argument("--peak-tol", type=float, default=0.1)
    au.add_argument("--level", action="append")
    se = sub.add_parser("session")
    se.add_argument("file")
    se.add_argument("--rate", type=int)
    se.add_argument("--depth")
    se.add_argument("--tracks", type=int)
    se.add_argument("--track", action="append")
    se.add_argument("--inserts", action="append")
    se.add_argument("--automation", action="append")
    se.add_argument("--clips", action="append")
    se.add_argument("--fades", action="append")
    ha = sub.add_parser("hash")
    ha.add_argument("dir")
    ha.add_argument("--compare")
    a = ap.parse_args()
    if not a.mode:
        ap.print_help()
        sys.exit(2)
    r = Report()
    {"audio": check_audio, "session": check_session, "hash": check_hash}[a.mode](a, r)
    r.finish()


if __name__ == "__main__":
    try:
        main()
    except ScError as exc:
        die(exc)
