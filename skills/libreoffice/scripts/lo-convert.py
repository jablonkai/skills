#!/usr/bin/env python3
"""Convert office documents with headless LibreOffice: one file or whole folders.

  python3 lo-convert.py report.docx --to pdf
  python3 lo-convert.py ~/Contracts -r --to pdf --pdfa 2 --out-dir ~/Contracts-pdfa
  python3 lo-convert.py deck.pptx --to odp --out /tmp/deck.odp
  python3 lo-convert.py old/ --to docx --ext doc,rtf

Targets: pdf, odt/ods/odp/odg, docx/xlsx/pptx, doc/xls/ppt, rtf, txt, csv, html, epub,
and png/jpg/svg (first page only; use lo-export-pages.py for every page). The target
must suit the document: a spreadsheet can't become .docx.

Every source is checked before LibreOffice sees it: LibreOffice imports a corrupt .docx
as plain text and "converts" it with exit code 0, so a file whose container does not
match its extension is reported as failed instead. Folders are searched for office
files (-r: recursively, lock files and hidden files skipped); the tree is mirrored
under --out-dir, or outputs land next to their sources. Existing outputs are skipped
unless --force. Sources are opened read-only with macros disabled.
Exit code: 0 all converted, 1 any failure. Standard library only (python3 3.9).
"""
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lo_run import (  # noqa: E402
    LOError, TIMEOUT, add_pdf_args, pdf_info, pdf_options, real, run_ops, sniff)

DEFAULT_EXTS = ("doc docx docm dot dotx odt ott fodt rtf wpd pages xls xlsx xlsm xlt "
                "xltx ods ots fods numbers ppt pptx pptm pps ppsx pot potx odp otp fodp "
                "key odg otg fodg vsd vsdx").split()
BATCH = 20  # documents per soffice call: bounds the damage of one stuck file


def find_sources(paths, recursive, exts):
    out = []
    for p in paths:
        p = real(p)
        if os.path.isfile(p):
            out.append((p, os.path.basename(p), None))
            continue
        if not os.path.isdir(p):
            raise LOError("not a file or folder: %s" % p)
        for root, dirs, files in os.walk(p):
            for name in sorted(files):
                if name.startswith((".", "~$")):
                    continue  # hidden, .~lock.x#, Word owner files ~$x.docx
                if os.path.splitext(name)[1].lower().lstrip(".") in exts:
                    full = os.path.join(root, name)
                    out.append((full, os.path.relpath(full, p), p))
            dirs[:] = sorted(d for d in dirs if not d.startswith(".")) if recursive else []
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("sources", nargs="+", help="files and/or folders")
    ap.add_argument("--to", required=True, help="target extension: pdf, docx, odt, xlsx ...")
    ap.add_argument("-r", "--recursive", action="store_true", help="search folders recursively")
    ap.add_argument("--out-dir", help="output root (the source tree is mirrored below it)")
    ap.add_argument("--out", help="output file (single source only)")
    ap.add_argument("--ext", help="comma list of source extensions to pick from folders")
    ap.add_argument("--force", action="store_true", help="overwrite existing outputs")
    ap.add_argument("--password", help="password to open protected sources")
    ap.add_argument("--filter", help="export filter name override (see references/filters.md)")
    ap.add_argument("--options", help="export FilterOptions string (CSV/text filters)")
    ap.add_argument("--infilter", help="import filter override, e.g. 'Text (encoded):UTF8'")
    ap.add_argument("--update-indexes", action="store_true",
                    help="refresh fields and rebuild tables of contents before export")
    ap.add_argument("--all-sheets", action="store_true",
                    help="csv: one file per sheet, named <name>-<Sheet>.csv")
    ap.add_argument("--json", action="store_true", help="machine-readable result")
    add_pdf_args(ap)
    a = ap.parse_args()

    to = a.to.lower().lstrip(".")
    exts = set(e.strip().lower().lstrip(".") for e in a.ext.split(",")) if a.ext else set(DEFAULT_EXTS)
    if not a.ext:
        exts.discard(to)
    sources = find_sources(a.sources, a.recursive, exts)
    if not sources:
        raise LOError("no source documents found (extensions: %s)" % ", ".join(sorted(exts)))
    if a.out and len(sources) != 1:
        raise LOError("--out needs exactly one source; use --out-dir")
    if a.all_sheets:
        if to != "csv" or a.options:
            raise LOError("--all-sheets goes with --to csv and without --options")
        a.options = "44,34,76,1,,1033,false,true,false,false,false,-1"
    pdf = pdf_options(a.pdfa, a.pdf_ua, a.pdf_opt) if to == "pdf" else None
    if to != "pdf" and (a.pdfa or a.pdf_ua or a.pdf_opt):
        raise LOError("--pdfa/--pdf-ua/--pdf-opt apply to --to pdf only")

    results, jobs, claimed = [], [], {}
    for src, rel, _root in sources:
        if a.out:
            dst = real(a.out)
        elif a.out_dir:
            dst = os.path.join(real(a.out_dir), os.path.splitext(rel)[0] + "." + to)
        else:
            dst = os.path.splitext(src)[0] + "." + to
        r = {"src": src, "dst": dst}
        if dst in claimed:
            r.update(ok=False, error="output collides with the one from %s" % claimed[dst])
        elif os.path.abspath(dst) == os.path.abspath(src):
            r.update(ok=False, error="output would overwrite the source")
        elif os.path.exists(dst) and not a.force:
            r.update(ok=True, skipped="exists (use --force)")
        else:
            bad = sniff(src, bool(a.password))
            if bad:
                r.update(ok=False, error=bad)
            else:
                job = {"src": src, "dst": dst, "pdf": pdf, "filter": a.filter,
                       "options": a.options, "infilter": a.infilter,
                       "password": a.password, "update_indexes": a.update_indexes}
                jobs.append({k: v for k, v in job.items() if v not in (None, False)})
        claimed.setdefault(dst, src)
        results.append(r)

    done = {}
    for i in range(0, len(jobs), BATCH):
        chunk = jobs[i:i + BATCH]
        try:
            out = run_ops("convert", {"jobs": chunk}, timeout=TIMEOUT)
            for r in out["results"]:
                done[r["src"]] = r
        except LOError as e:
            # A crash or hang takes the whole batch down; redo it one file at a time
            # so only the culprit fails.
            for j in chunk:
                if len(chunk) == 1:
                    done[j["src"]] = {"ok": False, "error": str(e)}
                    continue
                try:
                    done[j["src"]] = run_ops("convert", {"jobs": [j]})["results"][0]
                except LOError as e1:
                    done[j["src"]] = {"ok": False, "error": str(e1)}

    for r in results:
        d = done.get(r["src"])
        if d is None:
            continue
        r.update({k: d[k] for k in ("ok", "error", "kind", "import_filter", "pages") if k in d})
        if r["ok"] and d.get("import_filter", "").startswith("Text") and \
                not r["src"].lower().endswith((".txt", ".csv", ".tsv")):
            r.update(ok=False, error="LibreOffice could only read it as plain text — "
                                     "the file is damaged or not what its extension says")
        if r["ok"] and a.all_sheets:
            stem = os.path.splitext(r["dst"])[0]
            r["outputs"] = sorted(glob.glob(glob.escape(stem) + "-*.csv"))
            r["dst"] = ", ".join(os.path.basename(o) for o in r["outputs"])
        if r["ok"] and to == "pdf":
            info = pdf_info(r["dst"])
            r["pdfa"] = info["pdfa"]
            if a.pdfa and not (info["pdfa"] or "").startswith(a.pdfa):
                r.update(ok=False, error="PDF/A-%s requested but the file declares %s"
                                         % (a.pdfa, info["pdfa"]))

    failed = [r for r in results if not r["ok"]]
    if a.json:
        print(json.dumps({"results": results, "failed": len(failed)}, ensure_ascii=False,
                         indent=1))
    else:
        for r in results:
            if r.get("skipped"):
                print("SKIP  %s  (%s)" % (r["dst"], r["skipped"]))
            elif r["ok"]:
                extra = ", ".join(x for x in (
                    "%s p." % r["pages"] if r.get("pages") else "",
                    "PDF/A-%s" % r["pdfa"] if r.get("pdfa") else "") if x)
                print("OK    %s -> %s%s" % (r["src"], r["dst"], "  (%s)" % extra if extra else ""))
            else:
                print("FAIL  %s  %s" % (r["src"], r["error"]))
        print("%d converted, %d skipped, %d failed" % (
            sum(1 for r in results if r["ok"] and not r.get("skipped")),
            sum(1 for r in results if r.get("skipped")), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except LOError as e:
        print("error: %s" % e, file=sys.stderr)
        sys.exit(1)
