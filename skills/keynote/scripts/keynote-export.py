#!/usr/bin/env python3
"""Export or batch-convert .key files with Keynote itself.

  keynote-export.py SRC... --to pdf|pptx|png|jpeg|tiff|m4v [--out-dir DIR] [-r]
                    [export options] [--force]
  keynote-export.py SRC.key --out "Exact Name.pdf" [export options] [--force]

SRC is a .key file or a folder of them (-r recurses and mirrors subfolders under
--out-dir). Without --out-dir each export lands next to its source. Image formats
write a folder named after the deck holding NAME.001.png, NAME.002.png, ...
Existing outputs are skipped unless --force. Sources are closed without saving, and
a deck the user already has open in Keynote is refused.

Skipped slides: PDF and images leave them out unless --include-skipped; PPTX always
keeps them, marked hidden. Each JSON line reports the deck's slide and skipped
counts so the output can be checked against them.

Prints one JSON line per file, then a summary. Exit 0 if every file exported.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import keynote_osa as ko  # noqa: E402

BATCH = 8  # files per osascript call; keeps each call well inside the timeout
EXT = {"jpeg": "", "png": "", "tiff": "", "m4v": ".m4v", "pdf": ".pdf", "pptx": ".pptx"}


def collect(srcs, recursive):
    """-> list of (source path, path relative to its root folder)."""
    found = []
    for src in srcs:
        src = os.path.realpath(src)
        if src.endswith(".key"):  # a package directory is a file here
            found.append((src, os.path.basename(src)))
            continue
        if not os.path.isdir(src):
            raise ko.KeynoteError("not a .key file or folder: %s" % src)
        for root, dirs, files in os.walk(src):
            for n in sorted(dirs + files):
                if n.endswith(".key") and not n.startswith("."):
                    p = os.path.join(root, n)
                    found.append((p, os.path.relpath(p, src)))
            # never descend into .key packages; only into real subfolders with -r
            dirs[:] = sorted(d for d in dirs if recursive and not d.endswith(".key"))
    return found


def main(argv):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("src", nargs="+")
    ap.add_argument("--to", choices=ko.FORMATS)
    ap.add_argument("--out", help="exact output path, for a single .key source")
    ap.add_argument("--out-dir")
    ap.add_argument("-r", "--recursive", action="store_true")
    ap.add_argument("--force", action="store_true")
    ko.add_export_args(ap)
    ns = ap.parse_args(argv)
    if ns.out:
        if len(ns.src) != 1 or not ns.src[0].endswith(".key") or ns.out_dir:
            ap.error("--out takes exactly one .key source and no --out-dir")
        if ns.to in ko.IMAGE_FORMATS:
            pass  # --out names the image folder
        else:
            try:
                ns.to = ko.format_of(ns.out)
            except ko.KeynoteError as e:
                ap.error(str(e) + " (for images give --to png and --out FOLDER)")
    elif not ns.to:
        ap.error("give --to FORMAT (or --out FILE)")

    try:
        files = collect(ns.src, ns.recursive)
    except ko.KeynoteError as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return 1
    if not files:
        print(json.dumps({"ok": False, "error": "no .key files found"}))
        return 1

    jobs, results = [], []
    for src, rel in files:
        stem = os.path.splitext(rel)[0] + EXT[ns.to]
        if ns.out:
            dst = ko.real(ns.out)
        elif ns.out_dir:
            dst = ko.real(os.path.join(os.path.abspath(ns.out_dir), stem))
        else:
            dst = os.path.splitext(src)[0] + EXT[ns.to]
        if os.path.exists(dst) and not ns.force:
            results.append({"src": src, "out": dst, "ok": True, "skipped": "exists"})
            continue
        try:
            ko.check_key_file(src)
        except ko.KeynoteError as e:
            results.append({"src": src, "out": dst, "ok": False, "error": str(e)})
            continue
        if os.path.exists(dst):
            ko.remove_path(dst)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        jobs.append((src, dst))

    opts = ko.export_opt_args(ns)
    for k in range(0, len(jobs), BATCH):
        chunk = jobs[k:k + BATCH]
        args = [ns.to] + opts + ["--"]
        for src, dst in chunk:
            args += [src, dst]
        try:
            out = ko.run_ops("export", args, docs=[s for s, _ in chunk])
        except ko.KeynoteError as e:
            results += [{"src": s, "out": d, "ok": False, "error": str(e)} for s, d in chunk]
            # Keynote is blocked or refused; the next batch would fail the same way.
            results += [{"src": s, "out": d, "ok": False, "error": "not attempted"}
                        for s, d in jobs[k + BATCH:]]
            break
        by_src = {r[1]: r for r in ko.rows(out) if r[0] in ("OK", "ERR") and len(r) >= 3}
        for src, dst in chunk:
            r = by_src.get(src)
            if r and r[0] == "OK" and os.path.exists(dst):
                rep = {"src": src, "out": dst, "ok": True,
                       "slides": int(r[3]), "skipped_slides": int(r[4])}
                if ns.to in ko.IMAGE_FORMATS:
                    rep["images"] = len(ko.image_files(dst))
                results.append(rep)
            else:
                err = r[2] if r else "no result"
                results.append({"src": src, "out": dst, "ok": False, "error": err})

    for r in results:
        print(json.dumps(r, ensure_ascii=False))
    failed = sum(1 for r in results if not r["ok"])
    print(json.dumps({"ok": failed == 0, "files": len(results), "failed": failed}))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
