#!/usr/bin/env python3
"""Print @font-face CSS for the bundled Nebula Sans WOFF2 files.

Default: embed each weight as a base64 data URI, so a single HTML file renders
with the brand font anywhere (email previews, artifacts, headless screenshots).
With --href PREFIX: reference the files by URL instead (PREFIX/NebulaSans-Book.woff2),
for sites where the fonts are copied next to the page.

Usage:
  font_face_css.py                          # Book + Bold, embedded
  font_face_css.py Book Semibold Black      # pick weights
  font_face_css.py --italic Book            # also add the italic of each weight
  font_face_css.py --href fonts Book Bold   # url('fonts/NebulaSans-Book.woff2')
"""
from __future__ import annotations

import argparse
import base64
import sys
from pathlib import Path

WEIGHTS = {"Light": 300, "Book": 400, "Medium": 500, "Semibold": 600, "Bold": 700, "Black": 900}
FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "NebulaSans" / "WOFF2"


def face(style_name: str, weight: int, italic: bool, href: str | None) -> str:
    file_name = f"NebulaSans-{style_name}{'Italic' if italic else ''}.woff2"
    if href is not None:
        src = f"url('{href.rstrip('/')}/{file_name}')"
    else:
        data = base64.b64encode((FONT_DIR / file_name).read_bytes()).decode("ascii")
        src = f"url(data:font/woff2;base64,{data})"
    return (
        "@font-face {\n"
        "  font-family: 'Nebula Sans';\n"
        f"  src: {src} format('woff2');\n"
        f"  font-weight: {weight};\n"
        f"  font-style: {'italic' if italic else 'normal'};\n"
        "  font-display: swap;\n"
        "}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("weights", nargs="*", default=["Book", "Bold"], help=f"any of: {', '.join(WEIGHTS)}")
    parser.add_argument("--italic", action="store_true", help="also emit the italic of each weight")
    parser.add_argument("--href", metavar="PREFIX", help="link to PREFIX/<file>.woff2 instead of embedding")
    args = parser.parse_args()

    unknown = [w for w in args.weights if w not in WEIGHTS]
    if unknown:
        parser.error(f"unknown weight(s) {unknown}; choose from {list(WEIGHTS)}")

    blocks = []
    for name in args.weights:
        blocks.append(face(name, WEIGHTS[name], False, args.href))
        if args.italic:
            blocks.append(face(name, WEIGHTS[name], True, args.href))
    print("\n".join(blocks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
