#!/usr/bin/env python3
"""Create a custom Compressor setting by deriving it from an existing one.

    python3 cmp-setting-new.py --from "Apple Devices 4K (HEVC 8-bit)" \\
        --name "HEVC 720p Review" --size 1280x720

    --from QUERY       base setting: path, display name or unique substring
                       (see cmp-settings.py); its codec, audio and container are kept
    --name NAME        new display name; also the file name (NAME.compressorsetting)
    Frame size (pick one; default: keep the base setting's):
      --size WxH       exactly WxH
      --fit WxH        scale down to fit inside WxH, keep aspect, never upscale
      --scale PCT      PCT percent of the source (e.g. 50)
      --source-size    same as the source
    --description TEXT shown in Compressor's inspector
    --out-dir DIR      default: ~/Library/Application Support/Compressor/Settings
                       (where Compressor lists custom settings)
    --force            replace an existing setting of the same name

The frame size lives in <video-encode><automatic width= height=>; changing only
<bounds> has no effect (verified on Compressor 5.4), so both are written.
Prints the new file's path. Use it with cmp-encode.py --setting PATH or by name.
"""

import argparse
import os
import re
import sys
import urllib.parse
from xml.etree import ElementTree

from cmp_lib import USER_SETTINGS, CmpError, parse_setting, resolve_setting


def wxh(text):
    m = re.fullmatch(r"(\d+)[x:](\d+)", text.strip())
    if not m:
        raise argparse.ArgumentTypeError("expected WxH, e.g. 1280x720")
    w, h = int(m.group(1)), int(m.group(2))
    if w % 2 or h % 2:
        raise argparse.ArgumentTypeError("width and height must be even")
    return w, h


def set_size(xml, auto_w, auto_h, bounds_w, bounds_h):
    m = re.search(r'<video-encode[^>]*isEnabled="yes"[^>]*>.*?</video-encode>', xml, re.S)
    if not m:
        raise CmpError("the base setting has no enabled video encoder (audio-only?)")
    body = m.group()
    if not re.search(r"<automatic [^>]*>", body):
        raise CmpError("the base setting has no <automatic> sizing element; pick another base")
    body = re.sub(r'(<automatic [^>]*?)width="[^"]*" height="[^"]*"',
                  r'\g<1>width="%s" height="%s"' % (auto_w, auto_h), body, count=1)
    body = re.sub(r'(<bounds )width="[^"]*" height="[^"]*"',
                  r'\g<1>width="%s" height="%s"' % (bounds_w, bounds_h), body, count=1)
    return xml[:m.start()] + body + xml[m.end():]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--from", dest="base", required=True)
    ap.add_argument("--name", required=True)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--size", type=wxh)
    g.add_argument("--fit", type=wxh)
    g.add_argument("--scale", type=float)
    g.add_argument("--source-size", action="store_true")
    ap.add_argument("--description")
    ap.add_argument("--out-dir", default=USER_SETTINGS)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    if "/" in a.name or a.name.startswith("."):
        ap.error("--name must not contain '/' or start with '.'")
    out = os.path.join(os.path.expanduser(a.out_dir), a.name + ".compressorsetting")
    try:
        base = resolve_setting(a.base)
        if os.path.abspath(base["path"]) == os.path.abspath(out):
            raise CmpError("--from and the new setting are the same file")
        if os.path.exists(out) and not a.force:
            raise CmpError("%s exists (use --force to replace it)" % out)
        with open(base["path"], encoding="utf-8") as fh:
            xml = fh.read()
        if a.size:
            xml = set_size(xml, a.size[0], a.size[1], a.size[0], a.size[1])
        elif a.fit:
            xml = set_size(xml, -a.fit[0], a.fit[1], -100, -100)
        elif a.scale:
            xml = set_size(xml, -a.scale, -a.scale, -100, -100)
        elif a.source_size:
            xml = set_size(xml, -100, -100, -100, -100)
        # Built-ins name themselves with a localisation key; a custom setting carries
        # its literal name, percent-encoded the way Compressor writes them.
        enc = urllib.parse.quote(a.name, safe="()-_.,:+'")
        desc = urllib.parse.quote(a.description or "Custom setting based on " + base["name"],
                                  safe="()-_.,:+'")
        xml = re.sub(r'<setting name="[^"]*"', '<setting name="%s"' % enc, xml, count=1)
        for tag, val in (("description", desc), ("nameKey", enc), ("descriptionKey", desc)):
            xml = re.sub(r"<%s>[^<]*</%s>" % (tag, tag), "<%s>%s</%s>" % (tag, val, tag), xml, count=1)
        ElementTree.fromstring(xml.encode("utf-8"))  # still well-formed?
        os.makedirs(os.path.dirname(out), exist_ok=True)
        tmp = out + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(xml)
        os.replace(tmp, out)
        s = parse_setting(out, "user")
    except (CmpError, ElementTree.ParseError, OSError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    print(out)
    print("name: %s · based on: %s · .%s, %s, %s" % (s["name"], base["name"], s["ext"],
                                                     s["video_codec"], s["size"]["text"]),
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
