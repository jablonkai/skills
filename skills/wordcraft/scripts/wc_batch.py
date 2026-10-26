#!/usr/bin/env python3
"""Convert a folder of documents with WordCraft, optionally adding an updated TOC.

    wc_batch.py IN_DIR OUT_DIR --to docx[,pdf,…] [--glob '*.md'] [--toc [--toc-levels 3]]
                [--update-fields] [--markup] [--overwrite]

Every file in IN_DIR matching --glob (default: every readable document) becomes
OUT_DIR/<base>.<ext> for each --to extension, all formats in one run per file.
--toc puts a filled-in table of contents at the top (before the first heading, with no
empty paragraph above it); --update-fields refreshes every field in all stories;
--markup prints comments and tracked changes into pdf/png. OUT_DIR must not be IN_DIR,
and inputs are never written. Prints one JSON line per output with a read-back.
"""
import argparse
import fnmatch
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wclib import inspect, pdf_pages, refuse_existing, run_cli, run_script  # noqa: E402

READABLE = (".docx", ".doc", ".odt", ".rtf", ".html", ".htm", ".md", ".markdown", ".tex", ".txt",
            ".json", ".xml")

# references.toc at the very start leaves an empty heading-styled paragraph above the
# TOC, and deleting it merges the TOC heading away; so open a Normal paragraph first.
TOC_PREFIX = ["caret.docStart", "text.newParagraph", "caret.up",
              {"command": "para.style", "params": {"style": "Normal"}}]


def readback(path):
    if path.lower().endswith(".pdf"):
        return {"pages": pdf_pages(path)}
    if path.lower().endswith(".docx"):
        d = inspect(path)
        toc = [b.get("text", "").split("\t")[0] for b in d["blocks"]
               if str(b.get("style", "")).startswith("TOC") and b.get("style") != "TOCHeading"]
        heads = [(b.get("style"), b.get("text", "")) for b in d["blocks"]
                 if str(b.get("style", "")).startswith("Heading")]
        return {"pages": d.get("pages"), "headings": heads[:20], "toc": toc[:20]}
    return {"bytes": os.path.getsize(path)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("in_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--to", required=True, help="comma-separated output extensions, e.g. docx,pdf")
    ap.add_argument("--glob", default="*")
    ap.add_argument("--toc", action="store_true")
    ap.add_argument("--toc-levels", type=int, default=3)
    ap.add_argument("--update-fields", action="store_true")
    ap.add_argument("--markup", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()

    src, dst = os.path.realpath(a.in_dir), os.path.realpath(a.out_dir)
    if src == dst:
        sys.exit("OUT_DIR must differ from IN_DIR")
    exts = [e.strip().lstrip(".").lower() for e in a.to.split(",") if e.strip()]
    files = sorted(f for f in os.listdir(src) if fnmatch.fnmatch(f, a.glob)
                   and f.lower().endswith(READABLE) and os.path.isfile(os.path.join(src, f)))
    if not files:
        sys.exit("no matching documents in " + src)
    jobs = [(f, [os.path.join(dst, os.path.splitext(f)[0] + "." + e) for e in exts]) for f in files]
    refuse_existing([o for _, outs in jobs for o in outs], a.overwrite)
    os.makedirs(dst, exist_ok=True)

    failed = 0
    for f, outs in jobs:
        path = os.path.join(src, f)
        try:
            if a.toc or (a.markup and len(outs) > 1):
                cmds = []
                if a.toc:
                    cmds = TOC_PREFIX + [{"command": "references.toc", "params": {"levels": a.toc_levels}}]
                if a.toc or a.update_fields:
                    cmds.append({"command": "references.updateFields", "params": {"all": True}})
                if a.markup:
                    cmds.append({"command": "file.printMarkup", "params": {"value": True}})
                run_script({"file": path, "commands": cmds, "save": outs})
            else:
                for o in outs:
                    flags = (["--update-fields"] if a.update_fields else []) + (["--markup"] if a.markup else [])
                    run_cli(["convert", path, o] + flags)
            for o in outs:
                print(json.dumps({"in": f, "out": o, **readback(o)}, ensure_ascii=False))
        except RuntimeError as e:
            failed += 1
            print(json.dumps({"in": f, "error": str(e)}, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
