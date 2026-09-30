#!/usr/bin/env python3
"""Export or batch-convert .pages files with Pages itself.

  pages-export.py SRC... --to pdf|docx|epub|rtf|txt [--out-dir DIR] [-r]
                  [export options] [--force]
  pages-export.py SRC.pages --out "Exact Name.epub" [export options] [--force]

SRC is a .pages file or a folder of them (-r recurses and mirrors subfolders under
--out-dir). Without --out-dir each export lands next to its source. Existing outputs
are skipped unless --force. Sources are opened read-only in effect: they are closed
without saving, and a document the user already has open in Pages is refused.

Prints one JSON line per file, then a summary. Exit 0 if every file exported.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pages_osa as po  # noqa: E402

BATCH = 8  # files per osascript call; keeps each call well inside the timeout


def collect(srcs, recursive):
    """-> list of (source path, path relative to its root folder)."""
    found = []
    for src in srcs:
        src = os.path.realpath(src)
        if src.endswith(".pages"):  # a package directory is a file here
            found.append((src, os.path.basename(src)))
            continue
        if not os.path.isdir(src):
            raise po.PagesError("not a .pages file or folder: %s" % src)
        for root, dirs, files in os.walk(src):
            names = sorted(dirs + files)
            for n in names:
                if n.endswith(".pages") and not n.startswith("."):
                    p = os.path.join(root, n)
                    found.append((p, os.path.relpath(p, src)))
            # never descend into .pages packages; only into real subfolders with -r
            dirs[:] = sorted(d for d in dirs if recursive and not d.endswith(".pages"))
    return found


def main(argv):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("src", nargs="+")
    ap.add_argument("--to", choices=po.FORMATS)
    ap.add_argument("--out", help="exact output path, for a single .pages source")
    ap.add_argument("--out-dir")
    ap.add_argument("-r", "--recursive", action="store_true")
    ap.add_argument("--force", action="store_true")
    po.add_export_args(ap)
    ns = ap.parse_args(argv)
    if ns.out:
        if len(ns.src) != 1 or not ns.src[0].endswith(".pages") or ns.out_dir:
            ap.error("--out takes exactly one .pages source and no --out-dir")
        try:
            ns.to = po.format_of(ns.out)
        except po.PagesError as e:
            ap.error(str(e))
    elif not ns.to:
        ap.error("give --to FORMAT (or --out FILE)")

    try:
        files = collect(ns.src, ns.recursive)
    except po.PagesError as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return 1
    if not files:
        print(json.dumps({"ok": False, "error": "no .pages files found"}))
        return 1

    jobs, results = [], []
    for src, rel in files:
        stem = os.path.splitext(rel)[0] + "." + ns.to
        if ns.out:
            dst = os.path.abspath(ns.out)
        elif ns.out_dir:
            dst = os.path.join(os.path.abspath(ns.out_dir), stem)
        else:
            dst = os.path.splitext(src)[0] + "." + ns.to
        if os.path.exists(dst) and not ns.force:
            results.append({"src": src, "out": dst, "ok": True, "skipped": "exists"})
            continue
        try:
            po.check_pages_file(src)
        except po.PagesError as e:
            results.append({"src": src, "out": dst, "ok": False, "error": str(e)})
            continue
        if os.path.exists(dst):
            po.remove_path(dst)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        jobs.append((src, dst))

    opts = po.export_opt_args(ns)
    for k in range(0, len(jobs), BATCH):
        chunk = jobs[k:k + BATCH]
        args = [ns.to] + opts + ["--"]
        for src, dst in chunk:
            args += [src, dst]
        try:
            out = po.run_ops("export", args, docs=[s for s, _ in chunk])
        except po.PagesError as e:
            results += [{"src": s, "out": d, "ok": False, "error": str(e)} for s, d in chunk]
            # Pages is blocked or refused; the next batch would fail the same way.
            results += [{"src": s, "out": d, "ok": False, "error": "not attempted"}
                        for s, d in jobs[k + BATCH:]]
            break
        by_src = {}
        for line in out.split("\n"):
            parts = line.split("\t")
            if parts[0] in ("OK", "ERR") and len(parts) >= 3:
                by_src[parts[1]] = parts
        for src, dst in chunk:
            parts = by_src.get(src)
            if parts and parts[0] == "OK" and os.path.exists(dst):
                results.append({"src": src, "out": dst, "ok": True})
            else:
                err = parts[2] if parts else "no result"
                results.append({"src": src, "out": dst, "ok": False, "error": err})

    for r in results:
        print(json.dumps(r, ensure_ascii=False))
    failed = sum(1 for r in results if not r["ok"])
    print(json.dumps({"ok": failed == 0, "files": len(results), "failed": failed}))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
