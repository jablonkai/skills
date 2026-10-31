#!/usr/bin/env python3
"""Report what a URL offers without downloading anything.

  ytdl_info.py URL...                       one block per video, or one row per playlist/channel entry
  ytdl_info.py URL --formats                + best height and size per video codec, audio formats
  ytdl_info.py URL --subs [--langs hu,en]   + manual and auto subtitle languages
  ytdl_info.py PLAYLIST --items 1:20        only those entries
  ytdl_info.py PLAYLIST --formats           full extraction per entry (slower) to add best H.264 height etc.
  --csv FILE | --json FILE                  write the rows/records to a file as well

Playlists and channels are read with --flat-playlist (fast: index, id, title, duration, url).
Exit 0 = report written, 1 = yt-dlp failed (with a hint), 2 = setup problem.
"""
import argparse
import csv
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ytdl_lib import error_hints, find_ytdlp  # noqa: E402

FAMILY = [("avc1", "h264"), ("avc", "h264"), ("hvc1", "hevc"), ("hev1", "hevc"), ("av01", "av1"),
          ("vp09", "vp9"), ("vp9", "vp9"), ("vp8", "vp8")]


def family(vcodec):
    for prefix, name in FAMILY:
        if (vcodec or "").startswith(prefix):
            return name
    return vcodec or "?"


def run_json(ytdlp, args):
    r = subprocess.run([ytdlp, "--no-warnings", *args], capture_output=True, text=True)
    if r.returncode != 0 and not r.stdout.strip():
        print(r.stderr.strip()[-800:], file=sys.stderr)
        for h in error_hints(r.stderr, ytdlp):
            print(f"hint: {h}", file=sys.stderr)
        sys.exit(1)
    return [json.loads(l) for l in r.stdout.splitlines() if l.strip().startswith("{")]


def fmt_dur(s):
    if s is None:
        return "?"
    s = int(round(s))
    return f"{s // 3600}:{s // 60 % 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"


def video_record(d, a):
    rec = {
        "id": d.get("id"), "title": d.get("title"), "uploader": d.get("uploader") or d.get("channel"),
        "duration": d.get("duration"), "upload_date": d.get("upload_date"), "license": d.get("license"),
        "url": d.get("webpage_url"), "extractor": d.get("extractor_key"),
        "chapters": len(d.get("chapters") or []),
    }
    if d.get("playlist_index") is not None:
        rec = {"index": d["playlist_index"], **rec}
    fmts = d.get("formats") or []
    if a.formats:
        best = {}
        for f in fmts:
            if f.get("vcodec") in (None, "none") or not f.get("height"):
                continue
            fam = family(f["vcodec"])
            if f["height"] > best.get(fam, {}).get("height", 0):
                best[fam] = {"height": f["height"], "fps": f.get("fps"), "ext": f.get("ext"), "id": f.get("format_id")}
        rec["best_height"] = max((v["height"] for v in best.values()), default=None)
        for fam, v in sorted(best.items()):
            rec[f"best_{fam}_height"] = v["height"]
        audio = sorted({f"{f.get('ext')}/{(f.get('acodec') or '').split('.')[0]}" for f in fmts
                        if f.get("vcodec") == "none" and f.get("acodec") not in (None, "none")})
        rec["audio_formats"] = " ".join(audio)
        rec["_best"] = best
    if a.subs:
        langs = [l for l in (a.langs or "").split(",") if l]
        manual = sorted((d.get("subtitles") or {}).keys())
        auto = sorted((d.get("automatic_captions") or {}).keys())
        if langs:
            auto = [l for l in auto if l.split("-")[0] in langs]
        rec["subs_manual"] = " ".join(m for m in manual if m != "live_chat")
        rec["subs_auto"] = " ".join(x for x in auto if "-" not in x or x.endswith("-orig")) if not langs else " ".join(auto)
    return rec


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("urls", nargs="+")
    p.add_argument("--formats", action="store_true")
    p.add_argument("--subs", action="store_true")
    p.add_argument("--langs", help="limit the auto-caption list to these base languages, e.g. hu,en")
    p.add_argument("--items", help="playlist items, e.g. 1:20")
    p.add_argument("--csv")
    p.add_argument("--json")
    p.add_argument("--cookies-from-browser")
    a = p.parse_args()
    ytdlp = find_ytdlp()
    common = ["--cookies-from-browser", a.cookies_from_browser] if a.cookies_from_browser else []
    if a.items:
        common += ["-I", a.items]

    records = []
    for url in a.urls:
        top = run_json(ytdlp, ["-J", "--flat-playlist", *common, url])
        if not top:
            continue
        top = top[0]
        if top.get("_type") == "playlist":
            print(f"# {top.get('title')}  ({top.get('playlist_count') or len(top.get('entries') or [])} entries, "
                  f"{top.get('uploader') or top.get('channel') or ''})", file=sys.stderr)
            if a.formats or a.subs:
                full = run_json(ytdlp, ["-j", "--ignore-errors", *common, url])
                records += [video_record(d, a) for d in full]
            else:
                for n, e in enumerate(top.get("entries") or [], 1):
                    records.append({"index": e.get("playlist_index") or n, "id": e.get("id"), "title": e.get("title"),
                                    "duration": e.get("duration"), "url": e.get("url"),
                                    "channel": e.get("channel") or e.get("uploader")})
        else:
            if a.formats or a.subs:
                top = run_json(ytdlp, ["-J", *common, url])[0]
            records.append(video_record(top, a))

    for r in records:
        line = [str(r.get("index", "")).rjust(3) if "index" in r else "", r.get("id") or "", fmt_dur(r.get("duration")),
                r.get("title") or ""]
        print("  ".join(x for x in line if x))
        if "_best" in r:
            for fam, v in sorted(r["_best"].items(), key=lambda kv: -kv[1]["height"]):
                print(f"      {fam:5s} up to {v['height']}p{int(v['fps'] or 0) or ''} ({v['ext']}, format {v['id']})")
            print(f"      audio: {r['audio_formats']}")
        if "subs_manual" in r:
            print(f"      subtitles: {r['subs_manual'] or '-'}   auto: {r['subs_auto'] or '-'}")
        if r.get("license"):
            print(f"      license: {r['license']}")
    clean = [{k: v for k, v in r.items() if not k.startswith("_")} for r in records]
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(clean, f, indent=2, ensure_ascii=False)
    if a.csv:
        keys = list(dict.fromkeys(k for r in clean for k in r))
        with open(a.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(clean)
    print(f"{len(records)} record(s)" + (f" → {a.csv or a.json}" if a.csv or a.json else ""), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
