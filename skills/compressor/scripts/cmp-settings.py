#!/usr/bin/env python3
"""List, search and resolve Compressor settings (built-in and custom).

    python3 cmp-settings.py                       every setting, grouped
    python3 cmp-settings.py prores                name/group/codec contains "prores"
    python3 cmp-settings.py --codec hvc1          video FourCC (apco apcs apcn apch ap4h
                                                  avc1 hvc1 ...; tiff/exr for sequences)
    python3 cmp-settings.py --user                custom settings only
    python3 cmp-settings.py --resolve "Apple ProRes 422 Proxy"
                                                  one setting → its path and details

Matching is case-insensitive on the English display name (as shown in the
Compressor sidebar), the file name and the group. --resolve takes a path, an
exact name or a unique substring, exactly like cmp-encode.py --setting.
Add --json for machine-readable output.
"""

import argparse
import json
import sys

from cmp_lib import USER_SETTINGS, CmpError, all_settings, resolve_setting


def kind(s):
    if s["image_sequence"]:
        return "%s sequence" % s["ext"]
    if s["audio_only"]:
        return "audio only"
    return s["video_codec"] or "?"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("search", nargs="?", help="substring of name, file name or group")
    ap.add_argument("--codec", help="video FourCC, e.g. apco, avc1, hvc1, tiff")
    ap.add_argument("--user", action="store_true", help="custom settings only")
    ap.add_argument("--resolve", metavar="QUERY", help="resolve one setting")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    try:
        if a.resolve:
            s = resolve_setting(a.resolve)
            if a.json:
                print(json.dumps(s, indent=2))
            else:
                print("name:   %s\npath:   %s\ngroup:  %s (%s)\noutput: .%s, %s, %s, audio %s"
                      % (s["name"], s["path"], s["group"] or "-", s["source"], s["ext"],
                         kind(s), s["size"]["text"], "yes" if s["has_audio"] else "no"))
            return 0
        items = all_settings(include_builtin=not a.user)
    except CmpError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2

    if a.search:
        q = a.search.lower()
        items = [s for s in items if q in s["name"].lower() or q in s["group"].lower()
                 or q in s["path"].lower() or q == (s["video_codec"] or "").lower()]
    if a.codec:
        items = [s for s in items if (s["video_codec"] or "").lower() == a.codec.lower()]
    if a.json:
        print(json.dumps(items, indent=2))
        return 0
    if not items:
        print("no matching settings" + ("" if not a.user else " (user folder: %s)" % USER_SETTINGS))
        return 1
    group = None
    for s in items:
        g = "[custom] " + USER_SETTINGS if s["source"] == "user" else s["group"]
        if g != group:
            group = g
            print("\n%s" % g)
        print("  %-48s .%-5s %-14s %s" % (s["name"], s["ext"], kind(s), s["size"]["text"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
