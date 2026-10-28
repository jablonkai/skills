#!/usr/bin/env python3
"""Convert one presentation or a folder of them with DeckCraft, headless; originals untouched.

  dk_convert.py IN OUT_DIR --to pdf,png [--thumb-width 480 | --scale 2] [--all-slides]
                [--notes] [--include-hidden] [--recursive] [--overwrite]

IN is a .deckcraft/.pptx file or a folder of them. Each deck NAME.ext becomes, per target:
  pdf        OUT_DIR/NAME.pdf (slides; --notes writes notes pages instead)
  pptx, deckcraft, md, txt, gif   OUT_DIR/NAME.<ext>
  png        OUT_DIR/NAME.png, slide 1 (--all-slides: OUT_DIR/NAME/slide-01.png …)
  jpg        OUT_DIR/NAME.jpg, slide 1
PNG size: --thumb-width W pixels wide, or --scale S pixels per point (2 = 1920 px for a
16:9 slide). Hidden slides are left out of PDFs unless --include-hidden.

Every input is hashed before and after; PDFs are checked against the deck's slide count
(pdfinfo) and images against the asked width. Prints a JSON report; exits 1 on any
failure or changed input. A target that already exists stops the run before anything is
written, unless --overwrite.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

from dklib import image_size, info, refuse_existing, run_cli, sha256

EXTS = (".deckcraft", ".pptx")
TARGETS = ("pdf", "pptx", "deckcraft", "md", "txt", "gif", "png", "jpg")


def decks(src, recursive):
    if os.path.isfile(src):
        return [src]
    found = []
    for root, dirs, files in os.walk(src):
        dirs[:] = sorted(d for d in dirs if not d.startswith(".")) if recursive else []
        found += [os.path.join(root, f) for f in sorted(files)
                  if f.lower().endswith(EXTS) and not f.startswith(("~$", "."))]
    return found


def pdf_pages(path):
    if not shutil.which("pdfinfo"):
        return None
    out = subprocess.run(["pdfinfo", path], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("Pages:"):
            return int(line.split()[1])
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("out_dir")
    ap.add_argument("--to", required=True, help="comma list of: " + ", ".join(TARGETS))
    size = ap.add_mutually_exclusive_group()
    size.add_argument("--thumb-width", type=int, help="PNG/JPG width in pixels")
    size.add_argument("--scale", type=float, default=None, help="pixels per point (default 2)")
    ap.add_argument("--all-slides", action="store_true", help="png: every slide into OUT_DIR/NAME/")
    ap.add_argument("--notes", action="store_true", help="pdf: notes pages instead of slides")
    ap.add_argument("--include-hidden", action="store_true")
    ap.add_argument("--recursive", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()

    targets = [t.strip().lower().lstrip(".") for t in a.to.split(",") if t.strip()]
    bad = [t for t in targets if t not in TARGETS]
    if bad:
        ap.error("unknown target(s) %s; pick from %s" % (bad, ", ".join(TARGETS)))
    files = decks(a.input, a.recursive)
    if not files:
        sys.exit("no .deckcraft or .pptx files in " + a.input)

    plan = []
    for f in files:
        name = os.path.splitext(os.path.basename(f))[0]
        for t in targets:
            if t == "png" and a.all_slides:
                plan.append((f, t, os.path.join(a.out_dir, name)))
            else:
                plan.append((f, t, os.path.join(a.out_dir, "%s.%s" % (name, t))))
    outs = [p for _, _, p in plan]
    if len(set(outs)) != len(outs):
        sys.exit("two inputs share a name and would write the same output; convert them separately")
    if any(os.path.realpath(p) in map(os.path.realpath, files) for p in outs):
        sys.exit("an output would replace an input; pick another OUT_DIR")
    refuse_existing(outs, a.overwrite)
    os.makedirs(a.out_dir, exist_ok=True)
    hashes = {f: sha256(f) for f in files}

    report, failed = [], False
    for f, t, out in plan:
        entry = {"input": f, "target": t, "output": out}
        try:
            d = info(f)
            width_pt = d["slideSize"][0]
            scale = a.thumb_width / width_pt if a.thumb_width else (a.scale or 2.0)
            if t in ("png", "jpg"):
                if t == "png" and a.all_slides:
                    if os.path.isdir(out):
                        shutil.rmtree(out)
                    run_cli(["render", f, "--all", "--scale", "%g" % scale, out])
                    imgs = sorted(os.listdir(out))
                    entry["files"] = len(imgs)
                    ok = len(imgs) == len(d["slides"])
                    entry["size"] = image_size(os.path.join(out, imgs[0])) if imgs else None
                elif t == "png":
                    run_cli(["render", f, "--slide", "0", "--scale", "%g" % scale, out])
                    entry["size"] = image_size(out)
                    ok = bool(entry["size"])
                else:
                    run_cli(["run", "--in", f, "--cmd", 'slide.go={"index":0}',
                             "--export", out, "--export-params", json.dumps({"scale": scale})])
                    entry["size"] = image_size(out)
                    ok = bool(entry["size"])
                if a.thumb_width and entry.get("size"):
                    ok = ok and abs(entry["size"][0] - a.thumb_width) <= 2
            elif t == "pdf" and (a.notes or a.include_hidden):
                params = {}
                if a.notes:
                    params["layout"] = "notes"
                if a.include_hidden:
                    params["includeHidden"] = True
                run_cli(["run", "--in", f, "--export", out, "--export-params", json.dumps(params)])
                ok = True
            else:
                run_cli(["convert", f, out])
                ok = os.path.isfile(out)
            if t == "pdf":
                visible = sum(1 for s in d["slides"] if a.include_hidden or not s.get("hidden"))
                entry["pages"], entry["slides"] = pdf_pages(out), visible
                if entry["pages"] is not None:
                    ok = ok and entry["pages"] == visible
            entry["ok"] = ok
        except RuntimeError as e:
            entry["ok"], entry["error"] = False, str(e)
        failed = failed or not entry["ok"]
        report.append(entry)

    changed = [f for f in files if sha256(f) != hashes[f]]
    print(json.dumps({"converted": report, "inputs": len(files), "inputs_changed": changed,
                      "ok": not failed and not changed}, indent=1, ensure_ascii=False))
    sys.exit(1 if failed or changed else 0)


if __name__ == "__main__":
    main()
