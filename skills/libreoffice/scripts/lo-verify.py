#!/usr/bin/env python3
"""Assert facts about an output file; prints PASS/FAIL per check, exits 1 on any FAIL.

  python3 lo-verify.py out.pdf --pages 3 --pdfa 2B --fonts-embedded --contains "Total"
  python3 lo-verify.py out.pdf --verapdf                 # full PDF/A validation
  python3 lo-verify.py out.xlsx --expect Summary!B4=1935 --formula Summary!B4 --no-errors
  python3 lo-verify.py out.ods --expect Summary.B4=1935 --no-errors   # through Calc
  python3 lo-verify.py letter.docx --contains "Kovács Ágnes" --not-contains "{{"

PDF: page count and PDF/A claim from the file; fonts with poppler's pdffonts, text with
pdftotext, validation with veraPDF when installed.
XLSX: values are the CACHED results stored in the file, read straight from the zip —
what Excel, openpyxl (data_only) or a viewer shows before any recalculation. Add
--recalc to check what Calc computes instead.
ODS, XLS and other formats are read through Calc (recalculated). Text documents (docx,
odt, doc, rtf) are checked through Writer for --contains/--not-contains/--pages.
--expect compares numbers within --tol (default 1e-6) and text exactly.
Standard library only (python3 3.9).
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lo_run import LOError, pdf_info, real, run_ops  # noqa: E402

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "rel": "http://schemas.openxmlformats.org/package/2006/relationships"}

results = []


def check(ok, label, detail=""):
    results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", label, ("  — " + detail) if detail else ""))


def split_ref(ref):
    """'Sheet!B4', 'Sheet.B4', "'My sheet'!B4" -> (sheet or None, 'B4')."""
    m = re.match(r"^(?:'([^']+)'|([^.!']+))[.!](\$?[A-Za-z]+\$?\d+)$", ref)
    if m:
        return m.group(1) or m.group(2), m.group(3).replace("$", "").upper()
    return None, ref.replace("$", "").upper()


def same(got, want, tol):
    if got is None:
        return want == ""
    try:
        return abs(float(got) - float(want)) <= tol
    except (TypeError, ValueError):
        return str(got) == want


# ------------------------------------------------------------------ PDF

def verify_pdf(path, a):
    info = pdf_info(path)
    if a.pages is not None or a.contains or a.not_contains or a.fonts_embedded:
        if not shutil.which("pdfinfo"):
            raise LOError("PDF page, font and text checks need poppler (pdfinfo, pdffonts, "
                          "pdftotext)")
    if a.pages is not None:
        out = subprocess.run(["pdfinfo", path], capture_output=True, text=True).stdout
        m = re.search(r"^Pages:\s+(\d+)", out, re.M)
        n = int(m.group(1)) if m else None
        check(n == a.pages, "pages == %d" % a.pages, "got %s" % n)
    if a.pdfa:
        want = a.pdfa.upper()
        check((info["pdfa"] or "") == want, "declares PDF/A-%s" % want,
              "got %s" % (info["pdfa"] or "no PDF/A claim"))
    if a.fonts_embedded:
        out = subprocess.run(["pdffonts", path], capture_output=True, text=True).stdout
        rows = [ln.split() for ln in out.splitlines()[2:] if ln.strip()]
        # columns end with: emb sub uni object ID  -> emb is the 5th from the end
        missing = [r[0] for r in rows if len(r) >= 5 and r[-5] != "yes"]
        check(not missing, "all fonts embedded (%d fonts)" % len(rows),
              "not embedded: %s" % ", ".join(missing) if missing else "")
    if a.contains or a.not_contains:
        text = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True,
                              text=True).stdout
        text_checks(text, a)
    if a.verapdf:
        vp = shutil.which("verapdf")
        if not vp:
            raise LOError("--verapdf needs veraPDF (brew install verapdf)")
        p = subprocess.run([vp, "--format", "text", path], capture_output=True, text=True)
        line = next((ln for ln in p.stdout.splitlines() if ln.startswith(("PASS", "FAIL"))),
                    p.stdout.strip()[:200])
        check(line.startswith("PASS"), "veraPDF validation", line.replace(path, "").strip())


def text_checks(text, a):
    flat = re.sub(r"\s+", " ", text)
    for t in a.contains:
        check(t in text or t in flat, "contains %r" % t)
    for t in a.not_contains:
        check(t not in text and t not in flat, "does not contain %r" % t)


# ------------------------------------------------------------------ XLSX cache

def xlsx_cells(path):
    """{sheet: {"B4": (value, formula, is_error)}} from the stored (cached) values."""
    with zipfile.ZipFile(path) as z:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        targets = {r.get("Id"): r.get("Target") for r in rels.findall("rel:Relationship", NS)}
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
                shared.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
        out = {}
        for sh in wb.find("m:sheets", NS).findall("m:sheet", NS):
            target = targets[sh.get("{%s}id" % NS["r"])].lstrip("/")
            target = target if target.startswith("xl/") else "xl/" + target
            cells = {}
            for c in ET.fromstring(z.read(target)).iter("{%s}c" % NS["m"]):
                t = c.get("t")
                v = c.find("m:v", NS)
                f = c.find("m:f", NS)
                val = v.text if v is not None else None
                if t == "s" and val is not None:
                    val = shared[int(val)]
                elif t == "inlineStr":
                    val = "".join(x.text or "" for x in c.iter("{%s}t" % NS["m"]))
                elif t == "b" and val is not None:
                    val = val == "1"
                cells[c.get("r")] = (val, f is not None, t == "e")
            out[sh.get("name")] = cells
    return out


def verify_xlsx_cache(path, a):
    sheets = xlsx_cells(path)
    first = next(iter(sheets))
    for exp in a.expect:
        ref, want = exp.split("=", 1)
        sheet, cell = split_ref(ref.strip())
        got = sheets.get(sheet or first, {}).get(cell, (None, False, False))
        check(not got[2] and same(got[0], want, a.tol), "%s == %s (cached)" % (ref, want),
              "got %s%s" % (got[0], " (error)" if got[2] else ""))
    for ref in a.formula:
        sheet, cell = split_ref(ref)
        got = sheets.get(sheet or first, {}).get(cell, (None, False, False))
        check(got[1], "%s holds a formula" % ref)
    if a.no_errors:
        bad = ["%s!%s=%s" % (s, c, v[0]) for s, cells in sheets.items()
               for c, v in cells.items() if v[2]]
        check(not bad, "no error values cached", ", ".join(bad[:10]))


# ------------------------------------------------------------------ through LibreOffice

def verify_calc(path, a):
    reads = [e.split("=", 1)[0].strip() for e in a.expect] + list(a.formula)
    out = run_ops("calc_read", {"src": path, "read": reads})
    cells = [rd["cells"][0][0] for rd in out["reads"]]
    for exp, c in zip(a.expect, cells):
        ref, want = exp.split("=", 1)
        check("e" not in c and same(c.get("v"), want, a.tol), "%s == %s (recalculated)"
              % (ref, want), "got %s" % (c.get("e") or c.get("v")))
    for ref, c in zip(a.formula, cells[len(a.expect):]):
        check("f" in c, "%s holds a formula" % ref)
    if a.no_errors:
        check(not out["errors"], "no formula errors (%d formulas)" % out["formulas"],
              ", ".join("%s %s" % (e["cell"], e["error"]) for e in out["errors"][:10]))


def verify_text(path, a):
    out = run_ops("inspect", {"src": path, "text": True})
    if out["kind"] != "writer":
        raise LOError("%s is a %s document; text checks work on text documents and PDFs"
                      % (path, out["kind"]))
    if a.pages is not None:
        check(out["pages"] == a.pages, "pages == %d" % a.pages, "got %s" % out["pages"])
    text_checks(out.get("text", ""), a)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("file")
    ap.add_argument("--pages", type=int, help="exact page count")
    ap.add_argument("--pdfa", help="declared PDF/A level, e.g. 2B, 1B, 3B, 4")
    ap.add_argument("--fonts-embedded", action="store_true", help="every PDF font embedded")
    ap.add_argument("--verapdf", action="store_true", help="validate PDF/A with veraPDF")
    ap.add_argument("--contains", action="append", default=[], help="text present (repeat)")
    ap.add_argument("--not-contains", action="append", default=[], help="text absent (repeat)")
    ap.add_argument("--expect", action="append", default=[], metavar="CELL=VALUE",
                    help="cell value, e.g. Summary!B4=1935 (repeat)")
    ap.add_argument("--formula", action="append", default=[], metavar="CELL",
                    help="cell holds a formula (repeat)")
    ap.add_argument("--no-errors", action="store_true", help="no formula evaluates to an error")
    ap.add_argument("--recalc", action="store_true", help="xlsx: check Calc's recalculated "
                                                          "values instead of the cached ones")
    ap.add_argument("--tol", type=float, default=1e-6, help="numeric tolerance")
    a = ap.parse_args()

    path = real(a.file)
    if not os.path.isfile(path):
        raise LOError("not found: %s" % path)
    ext = os.path.splitext(path)[1].lower()
    cell_checks = a.expect or a.formula or a.no_errors
    if ext == ".pdf":
        verify_pdf(path, a)
    elif ext in (".xlsx", ".xlsm") and not a.recalc:
        verify_xlsx_cache(path, a)
    elif cell_checks:
        verify_calc(path, a)
    if ext != ".pdf" and (a.contains or a.not_contains or a.pages is not None):
        verify_text(path, a)
    if not results:
        raise LOError("no checks given")
    failed = results.count(False)
    print("%d checks, %d failed" % (len(results), failed))
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except LOError as e:
        print("error: %s" % e, file=sys.stderr)
        sys.exit(1)
