#!/usr/bin/env python3
"""Build a set of branded variants from one base template, then install them.

  motn-variants.py SPEC.json [--no-install] [--render] [--force]
  motn-variants.py --csv rows.csv --base base.moti --category "Brand" [--out-dir DIR] ...

SPEC.json (paths relative to the spec file):
  {"base": "LT.moti", "category": "EMU Lower Thirds", "out_dir": "variants",
   "common":   {"font": {"*": "Georgia-Bold"}, "set": {"Backplate": "1"}},
   "variants": [{"name": "EMU 6-Day", "text": {"#1": "Name", "#2": "Role"},
                 "color": {"#1": "#00ADEF"}, "fill": {"Rectangle": "#1A1A1A"},
                 "set": {"Backplate Color": "#00ADEF"},
                 "publish": {"#1:color": "Name Color"}, "unpublish": ["Build In"]}]}

CSV: a `name` column plus one column per edit, headed OP:TARGET — `text:#1`,
`font:*`, `color:Headline Text`, `fill:Rectangle`, `set:Backplate Color`, `size:#2`.
Empty cells are skipped. Edits are the motn-edit.py ones, applied common first,
then per variant, in the order text, font, size, color, fill, opacity, set, publish,
unpublish.

Each variant is written to OUT_DIR/<name>.<ext> (the base is never modified),
installed under the category unless --no-install, and with --render rendered through
Compressor (motn-render.py) — the middle frame becomes the browser thumbnail.
Prints one JSON report; exit 1 if any variant failed (the others still run).
"""
import argparse
import csv
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ozml  # noqa: E402

ORDER = ("text", "font", "size", "color", "fill", "opacity", "set", "publish", "unpublish")


def ops_from(block):
    ops = []
    for op in ORDER:
        v = block.get(op)
        if not v:
            continue
        if op == "unpublish":
            ops += [("unpublish", n, None) for n in (v if isinstance(v, list) else [v])]
        else:
            ops += [(op, k, str(val)) for k, val in v.items()]
    return ops


def from_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            name = (r.pop("name", "") or "").strip()
            if not name:
                continue
            v = {"name": name}
            for col, val in r.items():
                if not col or val is None or val.strip() == "":
                    continue
                op, _, target = col.partition(":")
                op = op.strip().lower()
                if op not in ORDER or not target:
                    raise ozml.OzmlError(f"CSV column {col!r}: use OP:TARGET, OP one of {', '.join(ORDER)}")
                v.setdefault(op, {})[target.strip()] = val.replace("\\n", "\n")
            rows.append(v)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", nargs="?")
    ap.add_argument("--csv")
    ap.add_argument("--base")
    ap.add_argument("--category")
    ap.add_argument("--out-dir")
    ap.add_argument("--no-install", action="store_true")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--force", action="store_true", help="overwrite variant files and installed copies")
    ap.add_argument("--unrig", action="store_true")
    a = ap.parse_args()

    try:
        if a.spec:
            with open(a.spec, encoding="utf-8") as f:
                spec = json.load(f)
            root = os.path.dirname(os.path.abspath(a.spec))
        elif a.csv:
            spec = {"variants": from_csv(a.csv)}
            root = os.getcwd()
        else:
            ap.error("SPEC.json or --csv required")
        base = a.base or spec.get("base")
        category = a.category or spec.get("category")
        if not base:
            ap.error("no base template (spec 'base' or --base)")
        base = base if os.path.isabs(base) else os.path.join(root, base)
        if not category and not a.no_install:
            ap.error("no category (spec 'category' or --category), or pass --no-install")
        out_dir = a.out_dir or spec.get("out_dir") or "variants"
        out_dir = out_dir if os.path.isabs(out_dir) else os.path.join(root, out_dir)
        os.makedirs(out_dir, exist_ok=True)
        ozml.Doc(base)
        common = ops_from(spec.get("common", {}))
        variants = spec.get("variants") or []
        if not variants:
            raise ozml.OzmlError("no variants")
        names = [v.get("name") for v in variants]
        if len(set(names)) != len(names) or not all(names):
            raise ozml.OzmlError("every variant needs a unique name")
    except (ozml.OzmlError, OSError, ValueError) as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return 1

    ext = os.path.splitext(base)[1]
    report = []
    for v in variants:
        r = {"name": v["name"]}
        try:
            out = os.path.join(out_dir, v["name"] + ext)
            if os.path.exists(out) and not a.force:
                raise ozml.OzmlError(f"{out} exists (use --force)")
            doc = ozml.Doc(base)
            r["changes"] = ozml.apply_edits(doc, common + ops_from(v), unrig=a.unrig)
            fonts = sorted({ozml.param_at(st, ozml.STYLE_FONT).findtext("font")
                            for n in ozml.text_layers(doc) for st in ozml.styles_of(n)
                            if ozml.param_at(st, ozml.STYLE_FONT) is not None})
            missing = [f for f, s in ozml.font_check(fonts).items() if s == "missing"]
            if missing:
                raise ozml.OzmlError(f"font(s) not installed: {', '.join(missing)}")
            doc.save(out)
            r["file"] = out
            thumb = None
            if a.render:
                rd = os.path.join(out_dir, "render", v["name"])
                p = subprocess.run([sys.executable, os.path.join(HERE, "motn-render.py"), out, "--out", rd],
                                   capture_output=True, text=True)
                rr = json.loads(p.stdout or "{}")
                r["render"] = {k: rr.get(k) for k in ("ok", "status", "video", "error")}
                r["render"]["frames"] = [{k: fr[k] for k in ("t", "png", "blank")} for fr in rr.get("frames", [])]
                if rr.get("frames"):
                    thumb = rr["frames"][-1]["png"]
                if not rr.get("ok"):
                    raise ozml.OzmlError(f"render failed: {rr.get('error') or rr.get('status')}")
            if not a.no_install:
                cmd = [sys.executable, os.path.join(HERE, "motn-install.py"), out, "--category", category]
                if thumb:
                    cmd += ["--thumb", thumb]
                if a.force:
                    cmd.append("--force")
                p = subprocess.run(cmd, capture_output=True, text=True)
                ir = json.loads(p.stdout or "{}")
                if not ir.get("ok"):
                    raise ozml.OzmlError(f"install failed: {ir.get('error')}")
                r.update(installed=ir["installed"], uid=ir["uid"])
            back = ozml.Doc(out)
            r["text_fields"] = [ozml.get_text(n) for n in ozml.text_layers(back)]
            r["ok"] = True
        except (ozml.OzmlError, OSError, ValueError) as e:
            r.update(ok=False, error=str(e))
        report.append(r)
    ok = all(r["ok"] for r in report)
    print(json.dumps({"ok": ok, "base": base, "category": category, "variants": report},
                     ensure_ascii=False, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
