#!/usr/bin/env python3
"""Turn an aubio_tool.py CSV (beats, onsets, quiet, notes) into editor markers.

  export_markers.py beats.csv --format resolve-json --out markers.json [--select bars]
  export_markers.py beats.csv --format resolve-edl  --out markers.edl --fps 25 [--tc-start 01:00:00:00]
  export_markers.py beats.csv --format fcp-csv      --out markers.csv [--kind marker]
  export_markers.py quiet.csv --format resolve-json --out cuts.json --color Red

Formats
  resolve-json  [{"seconds", "name", "color", "note", "duration"}] — feed each entry to the
                davinci-resolve skill's R.marker(seconds, name, color, note, duration)
  resolve-edl   CMX3600 marker EDL — Resolve: Timeline > Import > Timeline Markers from EDL
  fcp-csv       at,name,kind,note — final-cut-pro skill: fcpxml-edit.py IN --markers this.csv
  csv           seconds,name,duration_s — plain list

--select (beats CSV): all | bars (beat 1 of every bar) | every:N (every Nth beat)
--offset SEC shifts every marker, for music that does not start at the timeline start.
Markers that round to the same frame are merged (Resolve allows one marker per frame).
"""
import argparse, csv, io, json, sys

RESOLVE_COLORS = {"Blue", "Cyan", "Green", "Yellow", "Red", "Pink", "Purple", "Fuchsia", "Rose",
                  "Lavender", "Sky", "Mint", "Lemon", "Sand", "Cocoa", "Cream"}


def load(path):
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit(f"error: {path} has no rows")
    cols = set(rows[0])
    if {"bar", "beat", "time_s"} <= cols:
        kind = "beats"
    elif {"start_s", "end_s"} <= cols and "midi" in cols:
        kind = "notes"
    elif {"start_s", "end_s"} <= cols:
        kind = "quiet"
    elif "time_s" in cols:
        kind = "onsets"
    else:
        sys.exit(f"error: {path}: not an aubio_tool.py CSV (columns {sorted(cols)})")
    return kind, rows


def markers(kind, rows, a):
    out = []
    if kind == "beats":
        sel = a.select
        every = int(sel.split(":", 1)[1]) if sel.startswith("every:") else None
        for i, rw in enumerate(rows):
            bar, beat = int(rw["bar"]), int(rw["beat"])
            if sel == "bars" and beat != 1:
                continue
            if every and i % every:
                continue
            down = beat == 1
            name = f"Bar {bar}" if sel == "bars" else f"{bar}.{beat}"
            color = a.downbeat_color if down and sel != "bars" else a.color
            out.append({"seconds": float(rw["time_s"]), "name": name, "color": color, "note": "", "duration": 0.0})
    elif kind == "onsets":
        for rw in rows:
            out.append({"seconds": float(rw["time_s"]), "name": f"Onset {rw['index']}", "color": a.color,
                        "note": f"strength {rw.get('strength', '')}", "duration": 0.0})
    elif kind == "quiet":
        for rw in rows:
            s, e = float(rw["start_s"]), float(rw["end_s"])
            out.append({"seconds": s, "name": f"Quiet {rw['index']}", "color": a.color,
                        "note": f"{e - s:.2f} s quiet", "duration": e - s})
    else:
        for rw in rows:
            s, e = float(rw["start_s"]), float(rw["end_s"])
            out.append({"seconds": s, "name": rw["name"], "color": a.color, "note": f"midi {rw['midi']}",
                        "duration": e - s})
    for m in out:
        m["seconds"] = round(m["seconds"] + a.offset, 4)
    return [m for m in out if m["seconds"] >= 0]


def dedupe(ms, fps):
    seen, keep, dropped = set(), [], 0
    for m in sorted(ms, key=lambda m: m["seconds"]):
        f = int(round(m["seconds"] * fps))
        if f in seen:
            dropped += 1
            continue
        seen.add(f)
        keep.append(m)
    return keep, dropped


def nominal(fps):
    return int(round(fps))


def tc(frames, fps):
    n = nominal(fps)
    h, rem = divmod(frames, 3600 * n)
    mi, rem = divmod(rem, 60 * n)
    s, f = divmod(rem, n)
    return f"{h:02d}:{mi:02d}:{s:02d}:{f:02d}"


def parse_tc(s, fps):
    h, mi, sec, f = (int(x) for x in s.replace(";", ":").split(":"))
    return ((h * 60 + mi) * 60 + sec) * nominal(fps) + f


def write_edl(ms, a):
    base = parse_tc(a.tc_start, a.fps)
    lines = [f"TITLE: {a.title}", "FCM: NON-DROP FRAME", ""]
    for i, m in enumerate(ms, 1):
        start = base + int(round(m["seconds"] * a.fps))
        dur = max(1, int(round(m["duration"] * a.fps)))
        t0, t1 = tc(start, a.fps), tc(start + 1, a.fps)
        lines.append(f"{i:03d}  001      V     C        {t0} {t1} {t0} {t1}  ")
        lines.append(f" |C:ResolveColor{m['color']} |M:{m['name']} |D:{dur}")
        lines.append("")
    return "\n".join(lines)


def table(header, rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("--format", required=True, choices=["resolve-json", "resolve-edl", "fcp-csv", "csv"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--select", default="all", help="beats only: all | bars | every:N")
    ap.add_argument("--offset", type=float, default=0.0, help="seconds added to every marker")
    ap.add_argument("--fps", type=float, default=25.0, help="timeline frame rate (frame rounding, EDL timecode)")
    ap.add_argument("--tc-start", default="01:00:00:00", help="EDL: timeline start timecode")
    ap.add_argument("--title", default="aubio markers", help="EDL title")
    ap.add_argument("--color", default="Blue", help="Resolve marker colour")
    ap.add_argument("--downbeat-color", default="Red", help="Resolve colour for beat 1 when --select all")
    ap.add_argument("--kind", default="marker", choices=["marker", "chapter", "todo"], help="fcp-csv marker kind")
    a = ap.parse_args()
    if not (a.select in ("all", "bars") or (a.select.startswith("every:") and a.select[6:].isdigit())):
        ap.error("--select must be all, bars or every:N")
    for c in (a.color, a.downbeat_color):
        if c not in RESOLVE_COLORS:
            ap.error(f"unknown Resolve colour {c!r}; one of {', '.join(sorted(RESOLVE_COLORS))}")
    if abs(a.fps - round(a.fps)) > 0.01 and a.format == "resolve-edl":
        print("note: fractional fps — EDL timecode is non-drop-frame", file=sys.stderr)

    kind, rows = load(a.csv)
    ms, dropped = dedupe(markers(kind, rows, a), a.fps)
    if not ms:
        sys.exit("error: no markers selected")
    if a.format == "resolve-json":
        for m in ms:
            m["duration"] = max(1, int(round(m["duration"] * a.fps)))  # Resolve marker duration is frames
        text = json.dumps(ms, indent=1)
    elif a.format == "resolve-edl":
        text = write_edl(ms, a)
    elif a.format == "fcp-csv":
        text = table(["at", "name", "kind", "note"], [[f"{m['seconds']:.4f}", m["name"], a.kind, m["note"]] for m in ms])
    else:
        text = table(["seconds", "name", "duration_s"], [[f"{m['seconds']:.4f}", m["name"], f"{m['duration']:.3f}"] for m in ms])
    with open(a.out, "w", newline="") as f:
        f.write(text)
    print(json.dumps({"out": a.out, "source": kind, "format": a.format, "markers": len(ms),
                      "merged_same_frame": dropped, "first_s": ms[0]["seconds"], "last_s": ms[-1]["seconds"],
                      "fps": a.fps, "offset_s": a.offset}))


if __name__ == "__main__":
    main()
