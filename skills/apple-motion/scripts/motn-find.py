#!/usr/bin/env python3
"""Find Motion templates and copy one out as a starting point (seed).

  motn-find.py [REGEX] [--kind titles|generators|effects|transitions] [--user | --stock]
  motn-find.py --copy "NAME" | "Category/NAME" [--kind titles] --out DIR/NewName.moti [--force]

Searches the templates Final Cut Pro and Motion ship (inside the app bundles) and the
user's ~/Movies/Motion Templates.localized. Prints name, kind, category, path, and for
user templates the FCPXML uid. --copy copies a template's file (plus a Media/ folder
when it references one) to a new path to edit — the original is never touched.
Names repeat across categories ("Lower Third" exists many times); then use
"Category/Name", e.g. "Basic Text/Lower Third Text & Subhead".
"""
import argparse
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ozml  # noqa: E402

KIND_ARG = {"titles": "Titles", "generators": "Generators", "effects": "Effects", "transitions": "Transitions"}


def all_templates(kind=None, user=True, stock=True):
    roots = ([ozml.USER_ROOT] if user else []) + (ozml.STOCK_ROOTS if stock else [])
    seen, out = set(), []
    for t in ozml.walk_templates(roots):
        if kind and t["kind"] != kind:
            continue
        t["source"] = "user" if t["root"] == ozml.USER_ROOT else "stock"
        key = (t["kind"], t["category"], t["name"], t["source"])
        if key in seen:  # the same stock template ships in several FCP template roots
            continue
        seen.add(key)
        if t["source"] == "user":
            t["uid"] = ozml.fcp_uid(t["path"])
        t.pop("root")
        out.append(t)
    return out


def resolve(name, kind):
    want = [p.strip().lower() for p in name.split("/") if p.strip()]
    hits = [t for t in all_templates(kind) if t["name"].lower() == want[-1]
            and all(w in [c.lower() for c in t["category"].split("/")] for w in want[:-1])]
    if not hits:
        raise ozml.OzmlError(f"no template named {name!r}" + (f" among {kind}" if kind else ""))
    if len({(h["kind"], h["category"]) for h in hits}) > 1:
        opts = sorted({f"{h['kind']}: {h['category']}/{h['name']}" for h in hits})
        raise ozml.OzmlError(f"{len(opts)} templates are named {name!r}; say which: " + "; ".join(opts))
    return hits[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("regex", nargs="?", default=".")
    ap.add_argument("--kind", choices=sorted(KIND_ARG))
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--user", action="store_true", help="only ~/Movies/Motion Templates")
    g.add_argument("--stock", action="store_true", help="only templates shipped with FCP/Motion")
    ap.add_argument("--copy", metavar="NAME")
    ap.add_argument("--out")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    kind = KIND_ARG.get(a.kind)
    try:
        if a.copy:
            if not a.out:
                ap.error("--copy needs --out DIR/NewName.ext")
            t = resolve(a.copy, kind)
            ext = os.path.splitext(t["path"])[1]
            out = a.out if a.out.lower().endswith(ext) else (
                os.path.join(a.out, t["name"] + ext) if os.path.isdir(a.out) else a.out + ext)
            if os.path.exists(out) and not a.force:
                raise ozml.OzmlError(f"{out} exists (use --force)")
            os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
            shutil.copyfile(t["path"], out)
            media = os.path.join(os.path.dirname(t["path"]), "Media")
            copied_media = False
            if os.path.isdir(media):
                dst = os.path.join(os.path.dirname(os.path.abspath(out)), "Media")
                shutil.copytree(media, dst, dirs_exist_ok=True)
                copied_media = True
            thumbs = [f for f in ("large.png", "small.png") if os.path.isfile(os.path.join(os.path.dirname(t["path"]), f))]
            doc = ozml.Doc(out)
            print(json.dumps({"ok": True, "copied_from": t["path"], "out": os.path.abspath(out),
                              "kind": t["kind"], "media_folder": copied_media,
                              "thumbnails_in_source": thumbs,
                              "text_fields": [{"field": i, "name": n.get("name"), "text": ozml.get_text(n)}
                                              for i, n in enumerate(ozml.text_layers(doc), 1)],
                              "published": [x.get("name") for x in ozml.targets(doc)]},
                             ensure_ascii=False, indent=1))
            return 0
        rx = re.compile(a.regex, re.I)
        rows = [t for t in all_templates(kind, user=not a.stock, stock=not a.user)
                if rx.search(f"{t['category']}/{t['name']}")]
        if a.json:
            print(json.dumps({"ok": True, "count": len(rows), "templates": rows}, ensure_ascii=False, indent=1))
        else:
            for t in rows:
                extra = f"\t{t['uid']}" if t.get("uid") else ""
                print(f"{t['source']}\t{t['kind']}\t{t['category']}/{t['name']}{extra}")
            print(f"{len(rows)} template(s)", file=sys.stderr)
    except (ozml.OzmlError, OSError) as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
