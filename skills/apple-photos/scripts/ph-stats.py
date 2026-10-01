#!/usr/bin/env python3
"""Library statistics per year or month: photos, videos, favourites, edited, located,
hidden, iCloud-only. Read-only.

  ph-stats.py [--library LIB] [--by year|month] [--json] [-- extra osxphotos query args]

Counts follow the Photos app: hidden items are counted in their own column but excluded
from photos/videos unless --include-hidden; Recently Deleted is excluded (osxphotos
default). Extra query arguments narrow the set (e.g. -- --album Trips --person Anna).
"""
import argparse
import json
import sys
from collections import defaultdict

from ph_lib import library_args, osxphotos, split_query

COLS = ["photos", "videos", "favourites", "edited", "with_location", "hidden", "icloud_only"]
TEMPLATE = "{created.year}|{created.mm}|{photo.ismovie}|{photo.favorite}|{photo.hasadjustments}|" \
           "{photo.latitude}|{photo.hidden}|{photo.ismissing}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--library", help="library path (default: the system library)")
    ap.add_argument("--by", choices=["year", "month"], default="year")
    ap.add_argument("--include-hidden", action="store_true", help="count hidden items as photos/videos too")
    ap.add_argument("--json", action="store_true")
    own, extra = split_query(sys.argv[1:])
    a = ap.parse_args(own)

    out = osxphotos(["query", *library_args(a.library), *extra, "--quiet", "--print", TEMPLATE])
    rows = defaultdict(lambda: dict.fromkeys(COLS, 0))
    for line in out.splitlines():
        parts = line.split("|")
        if len(parts) != 8:
            continue
        year, month, movie, fav, edited, lat, hidden, missing = parts
        r = rows[year if a.by == "year" else f"{year}-{month}"]
        is_hidden = hidden != "_"
        r["hidden"] += is_hidden
        if is_hidden and not a.include_hidden:
            continue
        r["videos" if movie != "_" else "photos"] += 1
        r["favourites"] += fav != "_"
        r["edited"] += edited != "_"
        r["with_location"] += lat != "_"
        r["icloud_only"] += missing != "_"

    keys = sorted(rows)
    total = {c: sum(rows[k][c] for k in keys) for c in COLS}
    if a.json:
        print(json.dumps({"by": a.by, "rows": {k: rows[k] for k in keys}, "total": total}, indent=1))
        return
    head = ["period"] + COLS
    print("| " + " | ".join(head) + " |")
    print("|" + "---|" * len(head))
    for k in keys + ["total"]:
        vals = total if k == "total" else rows[k]
        print(f"| {k} | " + " | ".join(str(vals[c]) for c in COLS) + " |")


if __name__ == "__main__":
    main()
