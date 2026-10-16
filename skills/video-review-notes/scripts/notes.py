#!/usr/bin/env python3
"""Read review notes left with the Video Review app (desktop app writing <video>.comments.json).

Notes live next to each video as `<video>.comments.json`; scene cuts as `<video>.scenes.json`.

  notes.py list PATH...              open notes of every video under PATH (files or folders)
      --all                          include notes marked done
      --timeline-fps 24 --timeline-start 01:00:00:00
                                     also print the matching Resolve timeline timecode
                                     (assumes the render covers the timeline from its start)
      --json                         machine-readable output
  notes.py frames VIDEO [--id ID]... [--all] [--out DIR]
                                     grab the exact frame(s) of each note with its mark drawn on
                                     (point: that frame; range: first, middle, last frame)

  notes.py done VIDEO ID [--undo]   mark one note done (or open again); nothing else changes

Only `done` writes, and only the `done` field of one note.
"""
import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

VIDEO_EXT = {".mp4", ".m4v", ".mov", ".webm", ".mkv", ".mxf", ".avi"}


def frame_of(t, fps):
    # Same rule as the app: frame n starts at n / fps; epsilon absorbs float error.
    return math.floor(t * fps + 1e-3)


def timecode(frame, fps):
    nominal = max(1, round(fps))
    s = frame // nominal
    return f"{s // 3600:02}:{s // 60 % 60:02}:{s % 60:02}:{frame % nominal:02}"


def parse_tc(tc, fps):
    h, m, s, f = (int(x) for x in tc.replace(";", ":").split(":"))
    return ((h * 60 + m) * 60 + s) * round(fps) + f


def videos_under(paths):
    out = []
    for p in map(Path, paths):
        if p.is_dir():
            out += sorted(x for x in p.iterdir() if x.suffix.lower() in VIDEO_EXT and not x.name.startswith("."))
        elif p.suffix == ".json" and p.name.endswith(".comments.json"):
            out.append(Path(str(p)[: -len(".comments.json")]))
        else:
            out.append(p)
    return out


def load(video):
    f = Path(f"{video}.comments.json")
    if not f.exists():
        return None
    data = json.loads(f.read_text())
    comments = sorted(data.get("comments", []), key=lambda c: c["t_in"])
    cuts = None
    sf = Path(f"{video}.scenes.json")
    if sf.exists():
        cuts = json.loads(sf.read_text()).get("cuts")
    return data.get("fps") or 24.0, comments, cuts


def scene_of(frame, fps, cuts, duration_frames=None):
    if cuts is None:
        return None
    n = 1
    for c in cuts:
        if c > 0 and frame >= frame_of(c, fps):
            n += 1
    return n


def describe(video, fps, c, number, cuts, tl):
    fin = frame_of(c["t_in"], fps)
    fout = frame_of(c["t_out"], fps) if c.get("t_out") is not None else None
    a = c.get("area")
    if c.get("scenes"):
        sc = c["scenes"]
        span = "scene" if sc[0] == sc[-1] else "scenes"
        kind = f"{span} {sc[0]}" + (f"-{sc[-1]}" if sc[0] != sc[-1] else "")
    elif fout is not None:
        kind = "range"
    else:
        kind = "moment"
    if a is None:
        where = "whole frame"
    elif a.get("w", 0) == 0 and a.get("h", 0) == 0:
        where = f"point at x={a['x']:.0%} y={a['y']:.0%} of the picture"
    else:
        where = (f"box x={a['x']:.0%}..{a['x'] + a['w']:.0%} y={a['y']:.0%}..{a['y'] + a['h']:.0%} of the picture")
    rec = {
        "video": Path(video).name,
        "number": number,
        "id": c["id"],
        "text": c.get("text", ""),
        "kind": kind,
        "frame_in": fin,
        "frame_out": fout,
        "tc_in": timecode(fin, fps),
        "tc_out": timecode(fout, fps) if fout is not None else None,
        "seconds": round(c["t_in"], 3),
        "duration_s": round(c["t_out"] - c["t_in"], 2) if fout is not None else None,
        "scene": scene_of(fin, fps, cuts) if not c.get("scenes") else None,
        "where": where,
        "done": bool(c.get("done")),
        "created": c.get("created"),
    }
    if tl:
        tl_fps, tl_start = tl
        conv = lambda f: tl_start + round(f * tl_fps / fps)
        rec["timeline_frame_in"] = conv(fin)
        rec["timeline_tc_in"] = timecode(conv(fin), tl_fps)
        if fout is not None:
            rec["timeline_frame_out"] = conv(fout)
            rec["timeline_tc_out"] = timecode(conv(fout), tl_fps)
    return rec


def cmd_list(args):
    tl = None
    if args.timeline_fps:
        tl = (args.timeline_fps, parse_tc(args.timeline_start or "00:00:00:00", args.timeline_fps))
    out = []
    for v in videos_under(args.paths):
        loaded = load(v)
        if loaded is None:
            continue
        fps, comments, cuts = loaded
        for i, c in enumerate(comments, 1):  # numbering matches the app: all notes, time order
            if c.get("done") and not args.all:
                continue
            out.append(describe(v, fps, c, i, cuts, tl))
    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return
    if not out:
        print("No open notes.")
        return
    current = None
    for r in out:
        if r["video"] != current:
            current = r["video"]
            print(f"\n## {current}")
        span = f"{r['tc_in']} - {r['tc_out']} ({r['duration_s']} s)" if r["tc_out"] else r["tc_in"]
        scene = f", scene {r['scene']}" if r["scene"] else ""
        tlinfo = ""
        if "timeline_tc_in" in r:
            tlinfo = f"\n    timeline: {r['timeline_tc_in']}" + (f" - {r['timeline_tc_out']}" if r.get("timeline_tc_out") else "")
        done = " [done]" if r["done"] else ""
        print(f"#{r['number']}{done} {r['kind']}{scene} | {span} | frames {r['frame_in']}"
              + (f"-{r['frame_out']}" if r["frame_out"] is not None else "")
              + f" | {r['where']}{tlinfo}\n    \"{r['text']}\"  (id {r['id']})")


def ffmpeg():
    exe = shutil.which("ffmpeg") or next((p for p in ("/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg") if Path(p).exists()), None)
    if not exe:
        sys.exit("ffmpeg not found")
    return exe


def cmd_frames(args):
    loaded = load(args.video)
    if loaded is None:
        sys.exit(f"no notes for {args.video}")
    fps, comments, _ = loaded
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    exe = ffmpeg()
    for i, c in enumerate(comments, 1):
        if args.id and c["id"] not in args.id:
            continue
        if c.get("done") and not (args.all or args.id):
            continue
        fin = frame_of(c["t_in"], fps)
        frames = [("frame", fin)]
        if c.get("t_out") is not None:
            fout = frame_of(c["t_out"], fps) - 1  # t_out is exclusive
            frames = [("first", fin), ("middle", (fin + fout) // 2), ("last", fout)]
        a = c.get("area")
        vf = []
        if a:
            if a.get("w", 0) == 0 and a.get("h", 0) == 0:
                r = 0.035  # same size as the app's pencil loop, relative to picture height
                vf.append(f"drawbox=x=iw*{a['x']}-ih*{r}:y=ih*{a['y']}-ih*{r}:w=ih*{2*r}:h=ih*{2*r}:color=yellow@0.95:t=5")
            else:
                vf.append(f"drawbox=x=iw*{a['x']}:y=ih*{a['y']}:w=iw*{a['w']}:h=ih*{a['h']}:color=yellow@0.95:t=5")
        vf.append("scale=1280:-2")
        for label, f in frames:
            # ffmpeg keeps the first frame whose pts >= t, so aim half a frame early.
            t = max(0.0, (f - 0.5) / fps)
            dst = out_dir / f"note{i:02}_{c['id']}_{label}_f{f}.jpg"
            subprocess.run([exe, "-v", "error", "-ss", f"{t:.4f}", "-i", str(args.video), "-frames:v", "1",
                            "-vf", ",".join(vf), "-q:v", "3", "-y", str(dst)], check=True)
            print(dst)


def cmd_done(args):
    f = Path(f"{args.video}.comments.json")
    data = json.loads(f.read_text())
    hits = [c for c in data.get("comments", []) if c.get("id") == args.id]
    if not hits:
        sys.exit(f"no note with id {args.id} in {f.name}")
    hits[0]["done"] = not args.undo
    tmp = f.with_name(f.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    tmp.replace(f)  # atomic, like the app
    print(f"{args.id}: done={not args.undo}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list")
    p.add_argument("paths", nargs="+")
    p.add_argument("--all", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--timeline-fps", type=float)
    p.add_argument("--timeline-start")
    p.set_defaults(fn=cmd_list)
    p = sub.add_parser("frames")
    p.add_argument("video")
    p.add_argument("--id", action="append")
    p.add_argument("--all", action="store_true")
    p.add_argument("--out", default="review-frames")
    p.set_defaults(fn=cmd_frames)
    p = sub.add_parser("done")
    p.add_argument("video")
    p.add_argument("id")
    p.add_argument("--undo", action="store_true")
    p.set_defaults(fn=cmd_done)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
