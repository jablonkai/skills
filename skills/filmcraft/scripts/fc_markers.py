#!/usr/bin/env python3
"""Turn a list of timecodes into FilmCraft markers.add steps (JSONL on stdout) for fc_run.py.

    fc_markers.py PROJECT.fcproj LIST [--color Green] [--fps F] [--sequence-start HH:MM:SS:FF]

LIST is a .csv (header optional; columns: time, name, comment, color, duration; also
accepted: timecode/tc/seconds/frame, note/label/title, colour, description) or a text
file with one "TIME [name…]" per line, or - for stdin. TIME is HH:MM:SS:FF (";FF" =
drop-frame), a frame count written as 123f, or seconds (12.5). The sequence frame rate
comes from the project's active sequence unless --fps is given. Timecodes are converted to
exact ticks on frame boundaries here, so no marker lands between frames.

--sequence-start subtracts a start timecode (e.g. 01:00:00:00 from a conformed list);
FilmCraft sequences count from 00:00:00:00. Exits 1 if a marker falls outside the sequence.
"""
import argparse
import csv
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fclib import TICKS, fps_of, inspect, tc_to_frame  # noqa: E402


LABELS = ["Violet", "Iris", "Caribbean", "Lavender", "Cerulean", "Forest", "Rose", "Mango", "Purple",
          "Blue", "Teal", "Magenta", "Tan", "Green", "Brown", "Yellow"]
# everyday colour names -> the nearest FilmCraft label (markers take label names only)
ALIASES = {"red": "Rose", "orange": "Mango", "pink": "Magenta", "cyan": "Caribbean", "white": "Lavender",
           "gray": "Tan", "grey": "Tan", "black": "Brown"}


def label_of(color):
    c = color.strip()
    for name in LABELS:
        if name.lower() == c.lower():
            return name
    if c.lower() in ALIASES:
        return ALIASES[c.lower()]
    sys.exit(f"unknown marker colour {color!r}; FilmCraft labels: {', '.join(LABELS)}")


def frame_of(text, fps):
    text = text.strip()
    m = re.fullmatch(r"(\d+)f", text)
    if m:
        return int(m.group(1))
    return tc_to_frame(text, fps)


# header spellings -> the field they feed; a column matching none of them stops the script
COLUMNS = {"time": "time", "timecode": "time", "tc": "time", "seconds": "time", "frame": "time",
           "start": "time", "in": "time", "name": "name", "note": "name", "notes": "name",
           "label": "name", "title": "name", "marker": "name", "comment": "comment",
           "comments": "comment", "description": "comment", "color": "color", "colour": "color",
           "duration": "duration", "length": "duration"}


def rows(text):
    first = text.lstrip().splitlines()[0] if text.strip() else ""
    if "," in first or "\t" in first:
        dialect = "excel-tab" if "\t" in first else "excel"
        reader = list(csv.reader(io.StringIO(text), dialect=dialect))
        if reader and not re.match(r"^[\d:;.]+f?$", reader[0][0].strip()):
            header = [h.strip().lower() for h in reader[0]]
            unknown = [h for h in header if h and h not in COLUMNS]
            if unknown:
                sys.exit(f"unknown column(s) {unknown}; rename to one of: time, name, comment, color, duration")
            header = [COLUMNS.get(h, h) for h in header]
            for r in reader[1:]:
                if any(c.strip() for c in r):
                    yield dict(zip(header, r))
        else:
            for r in reader:
                if r and r[0].strip():
                    yield dict(zip(["time", "name", "comment", "color", "duration"], r))
        return
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        yield {"time": parts[0], "name": parts[1] if len(parts) > 1 else ""}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("list")
    ap.add_argument("--color", help="default marker colour label (Green, Red, Blue, …)")
    ap.add_argument("--fps", type=float, help="override the sequence frame rate")
    ap.add_argument("--sequence-start", help="subtract this start timecode from every time")
    a = ap.parse_args()

    seq = inspect(os.path.abspath(a.project), "sequence")
    if not seq and not a.fps:
        sys.exit("the project has no active sequence; open one or pass --fps")
    fps = a.fps or fps_of(seq)
    num, den = (seq["settings"]["frame_rate"]["num"], seq["settings"]["frame_rate"]["den"]) if seq and not a.fps \
        else (fps, 1)
    total = seq["durationFrames"] if seq else None
    offset = frame_of(a.sequence_start, fps) if a.sequence_start else 0

    text = sys.stdin.read() if a.list == "-" else open(a.list, encoding="utf-8-sig").read()
    bad = 0
    for r in rows(text):
        if not (r.get("time") or "").strip():
            continue
        key = "time"
        frame = frame_of(r[key], fps) - offset
        if frame < 0 or (total is not None and frame >= total):
            bad += 1
            print(f"marker {r.get('name', '')!r} at {r[key]} (frame {frame}) is outside the sequence "
                  f"(0-{total - 1 if total else '?'})", file=sys.stderr)
            continue
        params = {"target": "program", "time": round(frame * TICKS * den / num)}
        for k in ("name", "comment"):
            if r.get(k):
                params[k] = r[k].strip()
        color = (r.get("color") or "").strip() or a.color
        if color:
            params["color"] = label_of(color)
        if (r.get("duration") or "").strip():
            params["durationFrames"] = frame_of(r["duration"], fps)
        print(json.dumps({"id": "markers.add", "params": params}, ensure_ascii=False))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
