#!/usr/bin/env python3
"""List what an FCPXML timeline contains: clips with timeline and source in/out,
titles, markers and chapter markers, transitions and gaps.

  fcpxml-read.py export.fcpxmld                  table of clips per project
  fcpxml-read.py export.fcpxml --json            one JSON object per project
  fcpxml-read.py export.fcpxml --project "Rough cut" --all --expand

Times are exact: seconds as decimals rounded to the millisecond for display, plus
timecode at the sequence rate for the timeline (from the sequence tcStart) and at the
source rate for the source (the media's own timecode, as FCP shows it). "out" points
are exclusive, as in FCP (in + duration).

Clips: asset-clip, clip, ref-clip (compound), sync-clip, mc-clip (multicam), video,
audio, title. Connected clips carry their lane (positive above, negative below the
primary storyline); items inside a connected storyline get the storyline's lane.
--expand also lists what is inside compound clips. Gaps and transitions only with --all.
"""
import argparse
import os
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fcptime import FD_TEXT, fmt_time, frames_to_tc, is_drop_capable, snap  # noqa: E402
from fcpxml_common import (FcpError, Resources, emit, item_source_fd, load, markers_of,  # noqa: E402
                           projects, t, url_to_path, walk)

KIND = {"asset-clip": "clip", "clip": "clip", "ref-clip": "compound", "sync-clip": "sync",
        "mc-clip": "multicam", "video": "video", "audio": "audio", "title": "title",
        "gap": "gap", "transition": "transition", "audition": "audition",
        "live-drawing": "drawing"}


def tc(time, fd, drop):
    """Timecode of an absolute time; '~' marks a time between frames."""
    n = Fraction(time) / fd
    if n.denominator == 1:
        return frames_to_tc(n.numerator, fd, drop)
    return frames_to_tc(int(snap(time, fd, "floor") / fd), fd, drop) + "~"


def media_of(el, res):
    ref = el.get("ref")
    r = res.get(ref) if ref else None
    if r is None:
        return None, None
    if r.tag == "asset":
        rep = r.find("media-rep")
        src = rep.get("src") if rep is not None else r.get("src")
        return r, (url_to_path(src) if src else None)
    return r, None


def read_project(ev, pr, res, show_all, expand):
    seq = pr.find("sequence")
    fd = res.frame_duration(seq.get("format")) or Fraction(1, 25)
    drop = seq.get("tcFormat") == "DF" and is_drop_capable(fd)
    tc_start = t(seq, "tcStart", "0s")
    spine = seq.find("spine")
    # Spine offsets are in sequence time (which starts at tcStart); report both.
    items = list(walk(spine, res, Fraction(0), tc_start, expand=expand)) if spine is not None else []
    clips, titles, others = [], [], []
    for it in items:
        el, tag = it["el"], it["tag"]
        row = {"kind": KIND.get(tag, tag), "name": el.get("name"), "lane": it["lane"],
               "timeline_in": fmt_time(it["tl_in"]), "timeline_out": fmt_time(it["tl_out"]),
               "tl_in_s": round(float(it["tl_in"]), 3), "tl_out_s": round(float(it["tl_out"]), 3),
               "tc_in": tc(it["tl_in"] + tc_start, fd, drop),
               "tc_out": tc(it["tl_out"] + tc_start, fd, drop),
               "duration": fmt_time(it["duration"]), "duration_s": round(float(it["duration"]), 3)}
        if it["depth"] and it["lane"] == 0:
            row["inside"] = "compound" if "/media" in it["path"] else "container"
        if el.get("enabled") == "0":
            row["enabled"] = False
        if tag in ("gap", "transition"):
            if show_all:
                others.append(row)
            continue
        if tag == "title":
            texts = ["".join(x.itertext()).strip() for x in el.findall("text")]
            row["text"] = texts
            eff = res.get(el.get("ref"))
            row["template"] = eff.get("name") if eff is not None else None
            titles.append(row)
            continue
        asset, path = media_of(el, res)
        sfd = item_source_fd(el, res, fd)
        src_in = it["start"]
        if tag in ("asset-clip", "video", "audio", "clip", "sync-clip", "mc-clip", "ref-clip"):
            row["source_in"] = fmt_time(src_in)
            row["source_out"] = fmt_time(src_in + it["duration"])
            row["src_in_s"] = round(float(src_in), 3)
            row["src_out_s"] = round(float(src_in + it["duration"]), 3)
            sdrop = (el.get("tcFormat") == "DF" or (asset is not None and drop)) and is_drop_capable(sfd)
            row["source_tc_in"] = tc(src_in, sfd, sdrop)
            row["source_tc_out"] = tc(src_in + it["duration"], sfd, sdrop)
            row["source_rate"] = FD_TEXT.get(sfd, fmt_time(sfd))
            if asset is not None:
                a_start = t(asset, "start", "0s")
                row["source_in_from_first_frame_s"] = round(float(src_in - a_start), 3)
        if path:
            row["media"] = path
            row["media_exists"] = os.path.exists(path)
        elif asset is not None and asset.tag == "media":
            row["media"] = f"compound: {asset.get('name')}"
        if el.find("timeMap") is not None:
            # A speed change maps clip time to source time: in + duration is not the out.
            row["retimed"] = True
            for k in ("source_out", "src_out_s", "source_tc_out"):
                row.pop(k, None)
        if el.get("srcEnable") and el.get("srcEnable") != "all":
            row["enabled_tracks"] = el.get("srcEnable")
        roles = el.get("audioRole") or el.get("videoRole")
        if roles:
            row["role"] = roles
        clips.append(row)
    marks = []
    if spine is not None:
        for m in markers_of(spine, res, Fraction(0), tc_start):
            el = m["el"]
            if m["tag"] == "keyword":
                continue
            kind = "chapter" if m["tag"] == "chapter-marker" else (
                "todo" if el.get("completed") == "0" else
                "done" if el.get("completed") == "1" else "marker")
            marks.append({"kind": kind, "name": el.get("value"), "at": fmt_time(m["tl"]),
                          "at_s": round(float(m["tl"]), 3), "tc": tc(m["tl"] + tc_start, fd, drop),
                          "on": m["owner"].get("name"), **({"note": el.get("note")} if el.get("note") else {})})
        marks.sort(key=lambda x: x["at_s"])
    keywords = sorted({k.strip() for k in (x.get("value", "") for x in spine.iter("keyword"))
                       for k in k.split(",") if k.strip()}) if spine is not None else []
    dur = t(seq, "duration", "0s")
    return {"event": ev, "project": pr.get("name"), "frame_duration": FD_TEXT.get(fd, fmt_time(fd)),
            "tc_start": tc(tc_start, fd, drop), "tc_format": "DF" if drop else "NDF",
            "duration": fmt_time(dur), "duration_s": round(float(dur), 3),
            "tc_end": tc(tc_start + dur, fd, drop),
            "clips": clips, "titles": titles, "markers": marks, "keywords": keywords,
            **({"gaps_and_transitions": others} if show_all else {})}


def print_table(p):
    print(f"# {p['project']}  (event {p['event']})  {p['duration_s']} s  "
          f"{p['tc_start']} – {p['tc_end']}  {p['frame_duration']} {p['tc_format']}")
    print(f"{'#':>3} {'lane':>4}  {'timeline in':<12} {'timeline out':<12} {'source in':<12} "
          f"{'source out':<12} {'dur s':>7}  name  [media]")
    for i, c in enumerate(p["clips"], 1):
        print(f"{i:>3} {c['lane']:>4}  {c['tc_in']:<12} {c['tc_out']:<12} "
              f"{c.get('source_tc_in', ''):<12} {c.get('source_tc_out', ''):<12} "
              f"{c['duration_s']:>7}  {c['name']}  [{os.path.basename(c.get('media') or '') or c['kind']}]"
              + ("  (in compound)" if c.get("inside") == "compound" else "")
              + ("  (disabled)" if c.get("enabled") is False else "")
              + ("  (retimed)" if c.get("retimed") else ""))
    for x in p.get("gaps_and_transitions", []):
        print(f"  - {x['kind']:<10} {x['tc_in']} – {x['tc_out']}  {x['name'] or ''}")
    if p["titles"]:
        print("titles:")
        for x in p["titles"]:
            print(f"  {x['tc_in']} – {x['tc_out']}  lane {x['lane']}  {x['template']}: "
                  + " | ".join(x["text"]))
    if p["markers"]:
        print("markers:")
        for m in p["markers"]:
            print(f"  {m['tc']}  {m['kind']:<7} {m['name']}")
    if p["keywords"]:
        print("keywords: " + ", ".join(p["keywords"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", help=".fcpxml or .fcpxmld")
    ap.add_argument("--project", help="only this project (exact name)")
    ap.add_argument("--json", action="store_true", help="JSON lines instead of a table")
    ap.add_argument("--all", action="store_true", help="also list gaps and transitions")
    ap.add_argument("--expand", action="store_true", help="also list clips inside compound clips")
    a = ap.parse_args()
    try:
        root = load(a.file)
        res = Resources(root)
        found = 0
        for ev, pr in projects(root):
            if a.project and pr.get("name") != a.project:
                continue
            if pr.find("sequence") is None:
                continue
            found += 1
            p = read_project(ev, pr, res, a.all, a.expand)
            if a.json:
                emit(p)
            else:
                print_table(p)
                print()
        if not found:
            raise FcpError("no project" + (f" named {a.project!r}" if a.project else "") +
                           f" in {a.file}")
        return 0
    except FcpError as e:
        emit({"ok": False, "error": str(e)})
        return 1


if __name__ == "__main__":
    sys.exit(main())
