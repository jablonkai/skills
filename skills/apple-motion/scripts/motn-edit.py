#!/usr/bin/env python3
"""Edit an Apple Motion template's text, fonts, colours and published parameters.

  motn-edit.py IN --out OUT [edits...] [--unrig] [--force]

Edits (repeatable, applied left to right). LAYER is a layer name (case-insensitive),
'#N' for the Nth text field in FCP order, or '*' for every text layer:
  --text   "LAYER=New text"        line breaks as \\n
  --font   "LAYER=PostScriptName"  e.g. Georgia-Bold (see --fonts to look one up)
  --size   "LAYER=120"
  --color  "LAYER=#00ADEF"         text face colour; also r,g,b in 0..1
  --fill   "SHAPE=#00ADEF"         shape fill colour
  --opacity "LAYER=1"              layer opacity 0..1 (a plate at 0.65 is see-through)
  --set    "Published Name=value"  any published parameter: colour, font, text,
                                   checkbox 0/1, popup index, slider number
  --publish "LAYER:PROP=Name"      PROP: color font size text fill opacity position
  --unpublish "Name"
  --unrig                          for a channel a rig widget drives (ColorWay popup,
                                   Backplate checkbox): delete that rig behaviour
                                   instead of the default, which also writes the value
                                   into the widget's current option
  --fonts FRAGMENT                 list installed PostScript names matching FRAGMENT

The input is never modified (OUT must differ unless --in-place). The output is
re-parsed after writing and fonts are checked; a missing font is an error (Motion would
silently substitute Helvetica) unless --allow-missing-font. Prints JSON with the
change log and a read-back of every text field.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ozml  # noqa: E402


class Collect(argparse.Action):
    def __call__(self, parser, ns, value, option_string=None):
        op = self.dest
        if op == "unpublish":
            target, val = value, None
        else:
            target, sep, val = value.partition("=")
            if not sep:
                parser.error(f"--{op} {value!r}: expected TARGET=VALUE")
            if op == "text":
                val = val.replace("\\n", "\n")
        ns.ops.append((op, target.strip(), val))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--in-place", action="store_true")
    ap.add_argument("--force", action="store_true", help="overwrite an existing OUT")
    ap.add_argument("--unrig", action="store_true")
    ap.add_argument("--allow-missing-font", action="store_true")
    ap.add_argument("--fonts", metavar="FRAGMENT")
    ap.set_defaults(ops=[])
    for op in ozml.OPS:
        ap.add_argument(f"--{op}", dest=op, action=Collect, default=None, metavar="SPEC")
    a = ap.parse_args()

    if a.fonts:
        print(json.dumps({"ok": True, "fonts": ozml.font_suggest(a.fonts),
                          "app_fonts": sorted(f for f in ozml.app_fonts()
                                              if a.fonts.lower().replace(" ", "") in f.lower())}, indent=1))
        return 0
    if not a.input:
        ap.error("input file required")
    out = a.input if a.in_place else a.out
    if not out:
        ap.error("--out OUT (or --in-place) required")
    if not a.in_place and os.path.abspath(out) == os.path.abspath(a.input):
        ap.error("OUT is the input; pass --in-place to edit it")
    if os.path.exists(out) and not (a.force or a.in_place):
        ap.error(f"{out} exists (use --force)")
    if ozml.kind_of(out) != ozml.kind_of(a.input):
        ap.error(f"keep the extension: {os.path.splitext(a.input)[1]} (it decides the template type)")
    try:
        doc = ozml.Doc(a.input)
        log = ozml.apply_edits(doc, a.ops, unrig=a.unrig)
        fonts = set()
        for n in ozml.text_layers(doc):
            for st in ozml.styles_of(n):
                p = ozml.param_at(st, ozml.STYLE_FONT)
                if p is not None and p.findtext("font"):
                    fonts.add(p.findtext("font"))
        fc = ozml.font_check(sorted(fonts))
        missing = [f for f, s in fc.items() if s == "missing"]
        if missing and not a.allow_missing_font:
            hint = {f: ozml.font_suggest(f.split("-")[0])[:6] for f in missing}
            raise ozml.OzmlError(f"font(s) not installed: {', '.join(missing)} — Motion would use "
                                 f"Helvetica instead. Close matches: {json.dumps(hint)}")
        doc.save(out)
        back = ozml.Doc(out)
        fields = [{"field": i, "name": n.get("name"), "text": ozml.get_text(n)}
                  for i, n in enumerate(ozml.text_layers(back), 1)]
    except (ozml.OzmlError, OSError, ValueError) as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, "out": os.path.abspath(out), "changes": log,
                      "fonts": fc, "text_fields": fields}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
