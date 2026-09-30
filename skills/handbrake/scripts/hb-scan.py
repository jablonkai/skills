#!/usr/bin/env python3
"""List the titles, audio tracks and subtitle tracks HandBrake sees.

    python3 hb-scan.py SOURCE... [--title N] [--min-duration SEC] [--recursive] [--json]

SOURCE is a video file, a folder of videos, a DVD/Blu-ray folder (VIDEO_TS,
BDMV, or a folder containing one) or an ISO. Track numbers are the 1-based
indices HandBrakeCLI's -a / -s expect. Disc sources list every title of at
least --min-duration seconds (HandBrake's default: 10) and mark the main
feature. Exits 1 if any source fails to scan.
"""

import argparse
import json
import sys

from hb_lib import HBError, collect_sources, find_cli, scan, summarize_title


def fmt_time(s):
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{sec:05.2f}"


def print_source(src, info):
    titles = info["titles"]
    main = info["main_feature"]
    print(f"{src} — {len(titles)} title(s)" + (f", main feature: {main}" if main else ""))
    for t in titles:
        star = " *main*" if t["title"] == main and len(titles) > 1 else ""
        print(f"  Title {t['title']}{star}  {fmt_time(t['duration_s'])}  "
              f"{t['width']}x{t['height']}  {t['fps']} fps  {t['video_codec']}  "
              f"chapters {t['chapters']}")
        for a in t["audio"]:
            extra = "  (commentary)" if a["commentary"] else ""
            print(f"    audio {a['track']:>2}  {a['lang'] or 'und':<4} "
                  f"{a['codec'] or '?':<7} {a['channels'] or '':<8} {a['description']}{extra}")
        for s in t["subtitles"]:
            forced = "  (forced)" if s["forced"] else ""
            print(f"    sub   {s['track']:>2}  {s['lang'] or 'und':<4} "
                  f"{s['format'] or '?'} ({s['source'] or '?'}){forced}")
        if not t["audio"]:
            print("    (no audio)")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sources", nargs="+")
    ap.add_argument("--title", type=int, default=0, help="scan one title (default: all)")
    ap.add_argument("--min-duration", type=int)
    ap.add_argument("--recursive", action="store_true", help="descend into subfolders")
    ap.add_argument("--json", action="store_true", help="print a JSON list instead")
    args = ap.parse_args()

    try:
        cli = find_cli()
        sources = collect_sources(args.sources, recursive=args.recursive)
    except HBError as e:
        print(e, file=sys.stderr)
        return 2
    if not sources:
        print("no video files found", file=sys.stderr)
        return 1

    results, failed = [], 0
    for src, _root in sources:
        try:
            ts = scan(cli, src, args.title, args.min_duration)
            info = {"source": src, "main_feature": ts.get("MainFeature") or None,
                    "titles": [summarize_title(t) for t in ts["TitleList"]]}
        except (HBError, OSError) as e:
            failed += 1
            info = {"source": src, "error": str(e)}
        results.append(info)
        if not args.json:
            if "error" in info:
                print(f"{src} — ERROR: {info['error']}")
            else:
                print_source(src, info)
    if args.json:
        json.dump(results, sys.stdout, indent=1, ensure_ascii=False)
        print()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
