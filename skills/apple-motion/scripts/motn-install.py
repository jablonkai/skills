#!/usr/bin/env python3
"""Install, list and remove templates in ~/Movies/Motion Templates.localized.

  motn-install.py FILE --category "Brand" [--name NAME] [--thumb FRAME.png] [--force]
  motn-install.py --list [--category C]
  motn-install.py --uninstall "Category/Name" [--kind titles]
  motn-install.py --in-library ~/Movies/X.fcpbundle     user templates the library resolved

FILE's extension picks the type: .moti -> Titles, .motn -> Generators, .moef -> Effects,
.motr -> Transitions. The template lands in <Type>.localized/<Category>/<Name>/<Name>.ext,
the layout Final Cut Pro scans (a template directly under Titles.localized does not
show up). A Media/ folder next to FILE is copied along. --thumb makes the browser
thumbnails (large.png 640x360, small.png 192x108) from a frame, e.g. one rendered by
motn-render.py; otherwise large/small.png next to FILE are used if present.
Prints the FCPXML uid for the final-cut-pro skill. --uninstall moves the template
folder to the Trash (recoverable). --in-library reads the library's Effects.map, where
FCP records every user template it resolved on import; an FCPXML uid that pointed
nowhere never shows up there (FCP imports it without a warning). Final Cut Pro picks up new templates when it
(re)opens the Titles/Generators browser; a running FCP may need a relaunch.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ozml  # noqa: E402

KIND_ARG = {"titles": "Titles", "generators": "Generators", "effects": "Effects", "transitions": "Transitions"}


def kind_dir(kind):
    return os.path.join(ozml.USER_ROOT, kind + ".localized")


def safe(name, what):
    if not name or "/" in name or name.startswith(".") or ":" in name:
        raise ozml.OzmlError(f"{what} {name!r}: no '/', ':' or leading '.'")
    return name


def thumbs(src_png, dest):
    made = []
    for fname, w, h in (("large.png", 640, 360), ("small.png", 192, 108)):
        out = os.path.join(dest, fname)
        p = subprocess.run(["sips", "-z", str(h), str(w), src_png, "--out", out, "-s", "format", "png"],
                           capture_output=True, text=True)
        if p.returncode != 0:
            raise ozml.OzmlError(f"sips could not make {fname}: {p.stderr.strip()[:200]}")
        made.append(fname)
    return made


def install(a):
    src = a.file
    kind = ozml.kind_of(src)
    if not kind:
        raise ozml.OzmlError(f"{src}: extension must be .moti, .motn, .moef or .motr")
    doc = ozml.Doc(src)  # refuse anything Motion cannot load
    name = safe(a.name or os.path.splitext(os.path.basename(src))[0], "name")
    cat = safe(a.category, "category")
    dest = os.path.join(kind_dir(kind), cat, name)
    target = os.path.join(dest, name + os.path.splitext(src)[1])
    if os.path.exists(dest):
        if not a.force:
            raise ozml.OzmlError(f"{dest} exists (use --force to replace it)")
        trash(dest)
    os.makedirs(dest)
    shutil.copyfile(src, target)
    srcdir = os.path.dirname(os.path.abspath(src))
    media = os.path.join(srcdir, "Media")
    if os.path.isdir(media) and any(m.get("relativeURL") for m in ozml.media_refs(doc)):
        shutil.copytree(media, os.path.join(dest, "Media"))
    made = []
    if a.thumb:
        made = thumbs(a.thumb, dest)
    else:
        for f in ("large.png", "small.png"):
            if os.path.isfile(os.path.join(srcdir, f)):
                shutil.copyfile(os.path.join(srcdir, f), os.path.join(dest, f))
                made.append(f)
    ozml.Doc(target)
    return {"ok": True, "installed": target, "kind": kind, "category": cat, "name": name,
            "uid": ozml.fcp_uid(target), "thumbnails": made,
            "fcpxml_template": {"name": name, "uid": ozml.fcp_uid(target)}}


def trash(path):
    t = os.path.expanduser("~/.Trash")
    dst = os.path.join(t, os.path.basename(path) + time.strftime(" %Y%m%d-%H%M%S"))
    shutil.move(path, dst)
    return dst


def listing(cat=None):
    rows = []
    for t in ozml.walk_templates([ozml.USER_ROOT]):
        if cat and t["category"].lower() != cat.lower():
            continue
        rows.append({"kind": t["kind"], "category": t["category"], "name": t["name"],
                     "path": t["path"], "uid": ozml.fcp_uid(t["path"])})
    return {"ok": True, "root": ozml.USER_ROOT, "count": len(rows), "templates": rows}


def uninstall(spec, kind):
    cat, _, name = spec.rpartition("/")
    if not cat:
        raise ozml.OzmlError("--uninstall needs Category/Name")
    hits = [t for t in ozml.walk_templates([ozml.USER_ROOT])
            if t["name"] == name and t["category"] == cat and (not kind or t["kind"] == kind)]
    if not hits:
        raise ozml.OzmlError(f"no installed template {spec!r}")
    if len(hits) > 1:
        raise ozml.OzmlError(f"{spec!r} exists as {', '.join(h['kind'] for h in hits)}; add --kind")
    folder = os.path.dirname(hits[0]["path"])
    moved = trash(folder)
    catdir = os.path.dirname(folder)
    if not os.listdir(catdir):
        os.rmdir(catdir)
    return {"ok": True, "removed": folder, "trash": moved}


def in_library(lib):
    m = os.path.join(os.path.expanduser(lib), "Effects.map")
    if not os.path.isfile(m):
        raise ozml.OzmlError(f"{m} not found (not an FCP library, or nothing imported yet)")
    p = subprocess.run(["plutil", "-p", m], capture_output=True, text=True)
    rels = sorted(set(re.findall(r'"(Movies/Motion Templates\.localized/[^"]+)"', p.stdout)))
    home = os.path.expanduser("~")
    rows = [{"uid": "~/" + r.split("Motion Templates.localized/", 1)[1], "path": os.path.join(home, r),
             "exists": os.path.isfile(os.path.join(home, r))} for r in rels]
    return {"ok": True, "library": os.path.expanduser(lib), "user_templates": rows}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?")
    ap.add_argument("--category")
    ap.add_argument("--name")
    ap.add_argument("--thumb", metavar="PNG")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--uninstall", metavar="CATEGORY/NAME")
    ap.add_argument("--kind", choices=sorted(KIND_ARG))
    ap.add_argument("--in-library", metavar="FCPBUNDLE")
    a = ap.parse_args()
    try:
        if a.in_library:
            r = in_library(a.in_library)
        elif a.list:
            r = listing(a.category)
        elif a.uninstall:
            r = uninstall(a.uninstall, KIND_ARG.get(a.kind))
        else:
            if not a.file or not a.category:
                ap.error("FILE and --category are required to install")
            r = install(a)
    except (ozml.OzmlError, OSError) as e:
        r = {"ok": False, "error": str(e)}
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
