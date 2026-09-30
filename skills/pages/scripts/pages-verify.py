#!/usr/bin/env python3
"""Check exported files without trusting the exporter.

  pages-verify.py FILE... [--pages N] [--contains TEXT]... [--not-contains TEXT]...
                  [--no-tokens] [--title T] [--author A] [--language L] [--show]

PDF   page count and text: pdftotext/pdfinfo when installed, else PDFKit via JXA
      (no install needed).
EPUB  zip + mimetype sanity, OPF metadata (dc:title, dc:creator, dc:language), and
      the text of the content documents.
DOCX  text of word/document.xml.
PAGES text of body, text boxes, shapes and tables, read through Pages.
TXT   the file itself.

Assertions apply to every FILE. --no-tokens fails on any leftover {{...}}. --show
prints the extracted text. Exit 0 when every assertion holds, 1 otherwise.
"""
import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pages_osa as po  # noqa: E402

_PDFKIT_JXA = r"""
ObjC.import("PDFKit");
function run(argv) {
  const d = $.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath(argv[0]));
  if (!d || d.isNil()) return "ERR";
  const s = d.string;
  return d.pageCount + "\n" + (s && !s.isNil() ? s.js : "");
}
"""


def pdf_info(path):
    if shutil.which("pdftotext") and shutil.which("pdfinfo"):
        info = subprocess.run(["pdfinfo", path], capture_output=True, text=True).stdout
        m = re.search(r"^Pages:\s+(\d+)", info, re.M)
        text = subprocess.run(["pdftotext", path, "-"], capture_output=True, text=True).stdout
        return (int(m.group(1)) if m else None), text, {}
    out = subprocess.run(
        ["osascript", "-l", "JavaScript", "-e", _PDFKIT_JXA, path],
        capture_output=True, text=True,
    ).stdout.rstrip("\n")
    if out == "ERR" or not out:
        raise ValueError("not a readable PDF")
    count, _, text = out.partition("\n")
    return int(count), text, {}


def xml_text(xml):
    xml = re.sub(r"</(w:p|p|h[1-6]|li|div|br)\s*>|<br\s*/?>", "\n", xml)
    xml = re.sub(r"<w:tab/>", "\t", xml)
    return html.unescape(re.sub(r"<[^>]+>", "", xml))


def docx_info(path):
    with zipfile.ZipFile(path) as z:
        return None, xml_text(z.read("word/document.xml").decode("utf-8")), {}


def epub_info(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if not names or names[0] != "mimetype" or \
                z.read("mimetype").decode().strip() != "application/epub+zip":
            raise ValueError("bad EPUB: first entry must be mimetype application/epub+zip")
        container = z.read("META-INF/container.xml").decode("utf-8")
        opf_path = re.search(r'full-path="([^"]+)"', container).group(1)
        opf = z.read(opf_path).decode("utf-8")
        meta = {}
        for tag, key in (("title", "title"), ("creator", "author"), ("language", "language")):
            m = re.search(r"<dc:%s[^>]*>([^<]*)</dc:%s>" % (tag, tag), opf)
            meta[key] = html.unescape(m.group(1)).strip() if m else None
        base = os.path.dirname(opf_path)
        manifest = dict(re.findall(r'<item\b[^>]*\bid="([^"]+)"[^>]*\bhref="([^"]+)"', opf))
        manifest.update({i: h for h, i in re.findall(
            r'<item\b[^>]*\bhref="([^"]+)"[^>]*\bid="([^"]+)"', opf)})
        spine = re.findall(r'<itemref\b[^>]*\bidref="([^"]+)"', opf)
        texts = []
        for idref in spine:
            href = manifest.get(idref)
            if href:
                name = os.path.normpath(os.path.join(base, href)).replace(os.sep, "/")
                if name in names:
                    texts.append(xml_text(z.read(name).decode("utf-8", "replace")))
        return len(spine), "\n".join(texts), meta


def pages_info(path):
    return None, po.run_ops("text", [os.path.abspath(path)], docs=[path]), {}


def inspect(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return pdf_info(path)
    if ext == ".docx":
        return docx_info(path)
    if ext == ".epub":
        return epub_info(path)
    if ext == ".pages":
        return pages_info(path)
    if ext in (".txt", ".text"):
        with open(path, encoding="utf-8", errors="replace") as fh:
            return None, fh.read(), {}
    raise ValueError("unsupported file type %s" % ext)


def squash(s):
    return re.sub(r"\s+", " ", s)


def main(argv):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("files", nargs="+")
    ap.add_argument("--pages", type=int, help="expected PDF page count")
    ap.add_argument("--contains", action="append", default=[])
    ap.add_argument("--not-contains", action="append", default=[])
    ap.add_argument("--no-tokens", action="store_true")
    ap.add_argument("--title")
    ap.add_argument("--author")
    ap.add_argument("--language")
    ap.add_argument("--show", action="store_true")
    ns = ap.parse_args(argv)

    all_ok = True
    for path in ns.files:
        rep = {"file": path, "ok": True, "failures": []}
        try:
            if not os.path.exists(path):
                raise ValueError("missing")
            count, text, meta = inspect(path)
        except (ValueError, KeyError, AttributeError, zipfile.BadZipFile, po.PagesError) as e:
            rep.update(ok=False, failures=["unreadable: %s" % e])
            print(json.dumps(rep, ensure_ascii=False))
            all_ok = False
            continue
        text = po.norm_text(text)
        flat = squash(text)  # line breaks in the export must not break a phrase match
        rep["pages" if path.lower().endswith(".pdf") else "units"] = count
        rep.update(meta)
        rep["chars"] = len(text)
        fails = rep["failures"]
        if ns.pages is not None and path.lower().endswith(".pdf") and count != ns.pages:
            fails.append("pages %s != %s" % (count, ns.pages))
        for s in ns.contains:
            if squash(s) not in flat:
                fails.append("missing text: %r" % s)
        for s in ns.not_contains:
            if squash(s) in flat:
                fails.append("unexpected text: %r" % s)
        if ns.no_tokens:
            m = re.search(r"\{\{[^}]*\}\}", text)
            if m:
                fails.append("leftover token %s" % m.group(0))
        for key in ("title", "author", "language"):
            want = getattr(ns, key)
            if want is not None and meta and meta.get(key) != want:  # EPUB only
                fails.append("%s %r != %r" % (key, meta.get(key), want))
        if ns.show:
            rep["text"] = text
        rep["ok"] = not fails
        all_ok &= rep["ok"]
        print(json.dumps(rep, ensure_ascii=False))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
