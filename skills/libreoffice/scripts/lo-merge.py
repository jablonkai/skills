#!/usr/bin/env python3
"""Fill a Writer template from data: one document per record, or one combined PDF.

  python3 lo-merge.py letter.odt --list                       # what the template can take
  python3 lo-merge.py letter.docx people.csv --out-dir letters --to pdf --name "{last}-{first}"
  python3 lo-merge.py letter.odt people.csv --combined all-letters.pdf --no-per-record
  python3 lo-merge.py invoice.ott rows.json --out-dir out --to pdf,docx --pdfa 2

Fill targets, matched by the record's column names (case-sensitive):
  {{column}} placeholders anywhere — body, tables, headers, footers, text frames
  user fields (Insert > Field > More Fields > Variables > User Field) named column
  bookmarks named column (the text goes at, or replaces, the bookmark)
  mail-merge (database) fields whose column is column, and input fields whose hint is
  column — both are replaced by the text.
The template is never modified (it is opened as a template copy). A record that leaves
a {{placeholder}} unfilled fails the run unless --allow-unfilled; an empty value is a
fill, not a miss. Values are inserted as text, never parsed.

--combined puts every record into one file, each starting on a new page. When the
template's header or footer holds a fill target, the combined file is built by joining
the per-record PDFs with pdfunite (poppler), because a Writer header can't differ per
record in one document.
Standard library only (python3 3.9).
"""
import argparse
import csv
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lo_run import LOError, add_pdf_args, pdf_options, real, run_ops, sniff  # noqa: E402


def read_records(path, delimiter, encoding):
    with open(path, "rb") as f:
        text = f.read().decode(encoding)
    if text.startswith("﻿"):
        text = text[1:]
    if path.lower().endswith(".json"):
        data = json.loads(text)
        if not isinstance(data, list) or not all(isinstance(r, dict) for r in data):
            raise LOError("JSON data must be a list of objects")
        return [{k: "" if v is None else str(v) for k, v in r.items()} for r in data]
    if not delimiter:
        try:
            delimiter = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|").delimiter
        except csv.Error:
            delimiter = ","
    rows = list(csv.DictReader(io.StringIO(text), delimiter=delimiter))
    return [{(k or "").strip(): (v or "") for k, v in r.items() if k} for r in rows]


def safe_name(text):
    text = re.sub(r"[/\\:\x00-\x1f]", "-", text).strip().strip(".")
    return re.sub(r"\s+", " ", text)[:120] or "record"


def out_names(records, pattern, stem):
    names, seen = [], {}
    for i, rec in enumerate(records, 1):
        try:
            name = pattern.format(n=i, **rec) if pattern else "%s-%03d" % (stem, i)
        except (KeyError, IndexError) as e:
            raise LOError("--name uses %s, which is not a data column" % e)
        name = safe_name(name)
        if name in seen:
            seen[name] += 1
            name = "%s-%d" % (name, seen[name])
        else:
            seen[name] = 1
        names.append(name)
    return names


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("template", help=".odt/.ott/.docx/.dotx/.doc template")
    ap.add_argument("data", nargs="?", help="CSV/TSV (header row) or JSON list of objects")
    ap.add_argument("--list", action="store_true", help="list the template's fill targets")
    ap.add_argument("--out-dir", help="folder for the per-record files")
    ap.add_argument("--to", default="pdf", help="per-record formats, comma list (default pdf)")
    ap.add_argument("--name", help="file name pattern, e.g. '{n:03}-{last_name}' "
                                   "(default: <template>-001 ...)")
    ap.add_argument("--combined", action="append", default=[],
                    help="one file with every record (pdf, odt, docx); repeat for several")
    ap.add_argument("--no-per-record", action="store_true",
                    help="only write --combined, no file per record")
    ap.add_argument("--open", default="{{", help="placeholder opening mark (default {{)")
    ap.add_argument("--close", default="}}", help="placeholder closing mark (default }})")
    ap.add_argument("--allow-unfilled", action="store_true",
                    help="keep going when a placeholder has no column")
    ap.add_argument("--delimiter", help="CSV delimiter (default: sniffed)")
    ap.add_argument("--encoding", default="utf-8")
    ap.add_argument("--force", action="store_true", help="overwrite existing outputs")
    ap.add_argument("--json", action="store_true")
    add_pdf_args(ap)
    a = ap.parse_args()

    template = real(a.template)
    bad = sniff(template)
    if bad:
        raise LOError("%s: %s" % (template, bad))
    inv = run_ops("writer_fields", {"src": template, "open": a.open, "close": a.close})
    targets = sorted(set(inv["placeholders"] + inv["user_fields"] + inv["bookmarks"]
                         + inv["database_fields"] + inv["input_fields"]))
    if a.list or not a.data:
        if a.json:
            print(json.dumps(inv, ensure_ascii=False, indent=1))
        else:
            for k in ("placeholders", "user_fields", "bookmarks", "database_fields",
                      "input_fields"):
                print("%-16s %s" % (k + ":", ", ".join(inv[k]) or "-"))
            print("pages: %s" % inv["pages"])
            if inv["header_footer_targets"]:
                print("header/footer: holds fill targets (a combined PDF is joined per record)")
        return 0

    records = read_records(real(a.data), a.delimiter, a.encoding)
    if not records:
        raise LOError("no records in %s" % a.data)
    columns = list(records[0].keys())
    missing = [t for t in inv["placeholders"] if t not in columns]
    if missing and not a.allow_unfilled:
        raise LOError("the template's placeholders %s have no data column (columns: %s); "
                      "rename the columns or pass --allow-unfilled"
                      % (", ".join(missing), ", ".join(columns)))
    unused = [c for c in columns if c not in targets]

    formats = [f.strip().lower().lstrip(".") for f in a.to.split(",") if f.strip()]
    if a.no_per_record:
        formats = []
    if formats and not a.out_dir:
        raise LOError("--out-dir is required for per-record files (or --no-per-record)")
    if not formats and not a.combined:
        raise LOError("nothing to write: give --out-dir or --combined")
    stem = os.path.splitext(os.path.basename(template))[0]
    names = out_names(records, a.name, stem)
    outputs = [[os.path.join(real(a.out_dir), "%s.%s" % (n, f)) for f in formats]
               for n in names] if formats else []
    combined = [real(c) for c in a.combined]
    for p in [p for o in outputs for p in o] + combined:
        if os.path.exists(p) and not a.force:
            raise LOError("%s exists (use --force)" % p)
    if outputs:
        os.makedirs(real(a.out_dir), exist_ok=True)
    for c in combined:
        os.makedirs(os.path.dirname(c), exist_ok=True)

    if combined and inv["header_footer_targets"]:
        if any(not c.lower().endswith(".pdf") for c in combined):
            raise LOError("the template's header/footer holds fill targets, so one combined "
                          "Writer document can't show each record's header; combine to .pdf")
        if a.pdfa:
            raise LOError("the template's header/footer holds fill targets, so the combined "
                          "PDF is joined from per-record PDFs and would lose PDF/A "
                          "conformance; write per-record PDF/A files instead")
        if not shutil.which("pdfunite"):
            raise LOError("the template's header/footer holds fill targets, so the combined "
                          "PDF is joined from per-record PDFs — install poppler (pdfunite)")
    pdf = pdf_options(a.pdfa, a.pdf_ua, a.pdf_opt)
    tmp = tempfile.mkdtemp(prefix="lo-merge-")
    try:
        out = run_ops("writer_fill", {
            "template": template, "records": records, "outputs": outputs,
            "combined": combined, "tmp_dir": tmp, "open": a.open, "close": a.close,
            "strict": not a.allow_unfilled, "pdf": pdf})
        if out.get("pdf_parts"):
            for c in combined:
                p = subprocess.run([shutil.which("pdfunite")] + out["pdf_parts"] + [c],
                                   capture_output=True, text=True)
                if p.returncode:
                    raise LOError("pdfunite failed: %s" % p.stderr.strip())
            out["combined"] = combined
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    written = [p for r in out["records"] for p in r.get("outputs", [])] + out.get("combined", [])
    lost = [p for p in written if not os.path.exists(p)]
    if lost:
        raise LOError("outputs missing after the run: %s" % ", ".join(lost))
    if a.json:
        out["unused_columns"] = unused
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0
    for r in out["records"]:
        tag = "  UNFILLED: %s" % ", ".join(r["unfilled"]) if r.get("unfilled") else ""
        print("record %d: %s%s" % (r["index"] + 1, ", ".join(os.path.basename(p) for p in
                                                           r["outputs"]) or "(combined only)", tag))
    for c in out.get("combined", []):
        print("combined: %s%s" % (c, " (%s pages)" % out["combined_pages"]
                                  if out.get("combined_pages") else ""))
    if unused:
        print("data columns with no fill target in the template: %s" % ", ".join(unused))
    print("%d records merged" % len(out["records"]))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except LOError as e:
        print("error: %s" % e, file=sys.stderr)
        sys.exit(1)
