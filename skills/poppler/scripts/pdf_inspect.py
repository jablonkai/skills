#!/usr/bin/env python3
"""Inspection report for one or more PDFs (or folders of them).

  pdf_inspect.py FILE_OR_DIR... [--json] [--password-file F | --password-env VAR]

Per file: page count, page sizes (pt, mm, paper name; mixed sizes listed by page),
fonts with embedded/subset flags, metadata (pdfinfo), PDF version, encryption,
linearisation, tagging and a qpdf --check status. Text table by default, JSON with --json.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdfcommon import (add_password_args, check, emit, is_encrypted, needs_password,  # noqa: E402
                       page_sizes, paper_name, read_password, readable, run)

META_KEYS = ["Title", "Author", "Subject", "Keywords", "Creator", "Producer", "CreationDate", "ModDate",
             "PDF version", "Tagged", "Optimized", "Form", "JavaScript"]


def fonts(path):
    lines = run(["pdffonts", path]).stdout.splitlines()[2:]
    out = []
    for line in lines:
        # name may be blank for Type 3 fonts; parse from the right
        m = re.match(r"^(.*?)\s+(Type 1C?|Type 1 \(CID\)|Type 1C \(OT\)|Type 3|TrueType(?: \(CID\))?|CID Type 0C?(?: \(OT\))?|CID TrueType|Unknown)\s+(\S+)\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+(\d+)\s+(\d+)\s*$", line)
        if m:
            out.append({"name": m.group(1).strip() or "[none]", "type": m.group(2), "encoding": m.group(3),
                        "embedded": m.group(4) == "yes", "subset": m.group(5) == "yes"})
    return out


def inspect(path, pw):
    rep = {"file": path, "encrypted": is_encrypted(path)}
    if rep["encrypted"]:
        rep["needs_password"] = needs_password(path)
        if rep["needs_password"] and pw is None:
            rep["error"] = "needs a user password (--password-file)"
            return rep
    rep["check"] = check(path, pw)
    with readable(path, pw) as p:
        info = run(["pdfinfo", p]).stdout
        meta = {}
        for line in info.splitlines():
            k, _, v = line.partition(":")
            if k.strip() in META_KEYS and v.strip():
                meta[k.strip()] = v.strip()
        rep["pdf_version"] = meta.pop("PDF version", None)
        rep["linearized"] = meta.pop("Optimized", "no") == "yes"
        rep["tagged"] = meta.pop("Tagged", "no") == "yes"
        rep["form"] = meta.pop("Form", "none")
        rep["javascript"] = meta.pop("JavaScript", "no") == "yes"
        rep["metadata"] = meta
        sizes = page_sizes(p)
        rep["pages"] = len(sizes)
        groups = []
        for i, (w, h, rot) in enumerate(sizes, 1):
            key = (round(w, 1), round(h, 1), rot)
            if groups and groups[-1]["key"] == key:
                groups[-1]["pages"][1] = i
            else:
                groups.append({"key": key, "pages": [i, i]})
        rep["page_sizes"] = [{
            "pages": f"{g['pages'][0]}" if g["pages"][0] == g["pages"][1] else f"{g['pages'][0]}-{g['pages'][1]}",
            "width_pt": g["key"][0], "height_pt": g["key"][1],
            "width_mm": round(g["key"][0] * 25.4 / 72, 1), "height_mm": round(g["key"][1] * 25.4 / 72, 1),
            "rotation": g["key"][2], "paper": paper_name(*g["key"])} for g in groups]
        rep["fonts"] = fonts(p)
        rep["fonts_not_embedded"] = sorted({f["name"] for f in rep["fonts"] if not f["embedded"]})
    return rep


def print_text(rep):
    print(f"== {rep['file']}")
    if "error" in rep:
        print(f"   {rep['error']}")
        return
    print(f"   pages: {rep['pages']}   PDF {rep['pdf_version']}   check: {rep['check']['status']}"
          f"   encrypted: {'yes' if rep['encrypted'] else 'no'}   linearized: {'yes' if rep['linearized'] else 'no'}"
          f"   tagged: {'yes' if rep['tagged'] else 'no'}   form: {rep['form']}"
          f"{'   JAVASCRIPT' if rep['javascript'] else ''}")
    for s in rep["page_sizes"]:
        rot = f", rotated {s['rotation']}" if s["rotation"] else ""
        print(f"   pages {s['pages']}: {s['width_pt']} x {s['height_pt']} pt = {s['width_mm']} x {s['height_mm']} mm ({s['paper']}{rot})")
    for k, v in rep["metadata"].items():
        print(f"   {k}: {v}")
    if rep["fonts"]:
        for f in rep["fonts"]:
            print(f"   font {f['name']} [{f['type']}] embedded={'yes' if f['embedded'] else 'NO'}"
                  f"{' subset' if f['subset'] else ''}")
    else:
        print("   fonts: none (image-only or vector-only PDF)")
    if rep["fonts_not_embedded"]:
        print(f"   NOT EMBEDDED: {', '.join(rep['fonts_not_embedded'])}")
    for m in rep["check"]["messages"]:
        print(f"   check: {m}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--json", action="store_true")
    add_password_args(ap)
    a = ap.parse_args()
    pw = read_password(a.password_file, a.password_env)
    files = []
    for p in a.paths:
        if os.path.isdir(p):
            files += sorted(os.path.join(p, f) for f in os.listdir(p) if f.lower().endswith(".pdf"))
        else:
            files.append(p)
    reports = [inspect(f, pw) for f in files]
    if a.json:
        emit(reports if len(reports) != 1 else reports[0])
    else:
        for r in reports:
            print_text(r)
    sys.exit(1 if any("error" in r or r["check"]["status"] == "errors" for r in reports) else 0)


if __name__ == "__main__":
    main()
