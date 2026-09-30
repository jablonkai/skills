#!/usr/bin/env python3
"""Check decks and exports without trusting the exporter.

  keynote-verify.py FILE... [--slides N] [--contains TEXT]... [--not-contains TEXT]...
                    [--no-tokens] [--title N=TEXT]... [--notes N=TEXT]...
                    [--skipped N,N...] [--theme ID] [--show]

KEY   read back through Keynote: theme, and per slide the layout, title, body,
      presenter notes, skipped flag, image count and every other text.
PDF   page count and text: pdftotext/pdfinfo when installed, else PDFKit via JXA.
PPTX  slide count in presentation order, hidden (skipped) slides, slide text and
      notes text, straight from the zip.
DIR   a slide-image export folder: the number of images.

--slides counts slides (KEY, PPTX), pages (PDF) or images (DIR). --contains and
--no-tokens search slide text and notes. --title N=TEXT: slide N's title equals
TEXT (KEY) or slide N's text contains it (PDF page, PPTX slide). --notes N=TEXT:
slide N's notes contain TEXT (KEY, PPTX). --skipped: exactly these slides are
skipped (KEY) or hidden (PPTX); give "" for none. --show prints what was read.
Exit 0 when every assertion holds, 1 otherwise.
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
import keynote_osa as ko  # noqa: E402

_PDFKIT_JXA = r"""
ObjC.import("PDFKit");
function run(argv) {
  const d = $.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath(argv[0]));
  if (!d || d.isNil()) return "ERR";
  const out = [String(d.pageCount)];
  for (let i = 0; i < d.pageCount; i++) {
    const s = d.pageAtIndex(i).string;
    out.push(s && !s.isNil() ? s.js : "");
  }
  return out.join("\f");
}
"""


def pdf_info(path):
    """-> list of per-page dicts."""
    if shutil.which("pdftotext"):
        text = subprocess.run(["pdftotext", "-layout", path, "-"],
                              capture_output=True, text=True).stdout
        pages = text.split("\f")
        if pages and not pages[-1].strip():
            pages.pop()
    else:
        out = subprocess.run(["osascript", "-l", "JavaScript", "-e", _PDFKIT_JXA, path],
                             capture_output=True, text=True).stdout.rstrip("\n")
        if out == "ERR" or not out:
            raise ValueError("not a readable PDF")
        count, *pages = out.split("\f")
        pages = pages[:int(count)]
    return {"slides": [{"slide": i, "text": ko.norm_text(t)} for i, t in enumerate(pages, 1)]}


def _para_text(xml):
    paras = re.findall(r"<a:p>.*?</a:p>|<a:p .*?</a:p>", xml, re.S)
    lines = ["".join(html.unescape(t) for t in re.findall(r"<a:t>([^<]*)</a:t>", p)) for p in paras]
    return "\n".join(line for line in lines if line)


def pptx_info(path):
    with zipfile.ZipFile(path) as z:
        pres = z.read("ppt/presentation.xml").decode("utf-8")
        rels = z.read("ppt/_rels/presentation.xml.rels").decode("utf-8")
        target = dict(re.findall(r'Id="([^"]+)"[^>]*Target="([^"]+)"', rels))
        target.update({i: t for t, i in re.findall(r'Target="([^"]+)"[^>]*Id="([^"]+)"', rels)})
        slides = []
        for n, rid in enumerate(re.findall(r'<p:sldId\b[^>]*r:id="([^"]+)"', pres), 1):
            name = "ppt/" + target[rid].lstrip("/").replace("ppt/", "", 1)
            xml = z.read(name).decode("utf-8")
            hidden = bool(re.search(r'<p:sld\b[^>]*\bshow="0"', xml))
            notes = ""
            srel = name.replace("slides/", "slides/_rels/") + ".rels"
            if srel in z.namelist():
                m = re.search(r'Target="\.\./notesSlides/([^"]+)"', z.read(srel).decode("utf-8"))
                if m:
                    nxml = z.read("ppt/notesSlides/" + m.group(1)).decode("utf-8")
                    # the notes page also carries the slide image and a slide number
                    body = re.findall(r'<p:sp>.*?</p:sp>', nxml, re.S)
                    notes = "\n".join(_para_text(sp) for sp in body
                                      if 'type="body"' in sp)
            slides.append({"slide": n, "skipped": hidden, "text": _para_text(xml),
                           "notes": notes})
    return {"slides": slides}


def key_info(path):
    out = ko.run_ops("info", [ko.real(path)], docs=[path])
    res = {"slides": []}
    for r in ko.rows(out):
        if r[0] == "DOC":
            res["theme"], res["theme_name"] = r[1], r[2]
        elif r[0] == "SLIDE":
            res["slides"].append({
                "slide": int(r[1]), "skipped": r[2] == "true", "layout": r[3].replace("­", ""),
                "images": int(r[4]), "title": ko.norm_text(r[5]), "body": ko.norm_text(r[6]),
                "notes": ko.norm_text(r[7]), "texts": [],
            })
        elif r[0] == "TEXT":
            res["slides"][int(r[1]) - 1]["texts"].append(ko.norm_text(r[2]))
    names = ko.english_names([s["layout"] for s in res["slides"]])
    for s, en in zip(res["slides"], names):
        s["text"] = "\n".join(s.pop("texts"))
        s["layout"] = en
    return res


def dir_info(path):
    return {"slides": [{"slide": i, "file": f, "text": ""}
                       for i, f in enumerate(ko.image_files(path), 1)]}


def inspect(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".key":
        return key_info(path)
    if ext == ".pdf":
        return pdf_info(path)
    if ext == ".pptx":
        return pptx_info(path)
    if os.path.isdir(path):
        return dir_info(path)
    raise ValueError("unsupported file type %s" % (ext or "(no extension)"))


def squash(s):
    return re.sub(r"\s+", " ", s).strip()


def pair(spec, flag):
    n, sep, text = spec.partition("=")
    if not sep or not n.strip().isdigit():
        raise SystemExit("%s wants N=TEXT, got %r" % (flag, spec))
    return int(n), text


def main(argv):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("files", nargs="+")
    ap.add_argument("--slides", type=int)
    ap.add_argument("--contains", action="append", default=[])
    ap.add_argument("--not-contains", action="append", default=[])
    ap.add_argument("--no-tokens", action="store_true")
    ap.add_argument("--title", action="append", default=[])
    ap.add_argument("--notes", action="append", default=[])
    ap.add_argument("--skipped")
    ap.add_argument("--theme")
    ap.add_argument("--show", action="store_true")
    ns = ap.parse_args(argv)
    titles = [pair(s, "--title") for s in ns.title]
    notes = [pair(s, "--notes") for s in ns.notes]

    all_ok = True
    for path in ns.files:
        rep = {"file": path, "ok": True, "failures": []}
        try:
            if not os.path.exists(path):
                raise ValueError("missing")
            info = inspect(path)
        except (ValueError, KeyError, AttributeError, zipfile.BadZipFile, ko.KeynoteError) as e:
            rep.update(ok=False, failures=["unreadable: %s" % e])
            print(json.dumps(rep, ensure_ascii=False))
            all_ok = False
            continue
        slides = info["slides"]
        kind = "key" if path.lower().endswith(".key") else \
            "pptx" if path.lower().endswith(".pptx") else "pdf" if path.lower().endswith(".pdf") else "dir"
        rep["slides"] = len(slides)
        if "theme" in info:
            rep["theme"] = info["theme"]
        if kind in ("key", "pptx"):
            rep["skipped"] = [s["slide"] for s in slides if s.get("skipped")]
        everything = "\n".join(
            "\n".join([s.get("title", ""), s.get("body", ""), s.get("text", ""), s.get("notes", "")])
            for s in slides)
        flat = squash(everything)
        fails = rep["failures"]
        if ns.slides is not None and len(slides) != ns.slides:
            fails.append("slides %d != %d" % (len(slides), ns.slides))
        for s in ns.contains:
            if squash(s) not in flat:
                fails.append("missing text: %r" % s)
        for s in ns.not_contains:
            if squash(s) in flat:
                fails.append("unexpected text: %r" % s)
        if ns.no_tokens:
            m = re.search(r"\{\{[^}]*\}\}", everything)
            if m:
                fails.append("leftover token %s" % m.group(0))
        for n, want in titles:
            if n > len(slides):
                fails.append("title %d: no such slide" % n)
            elif kind == "key":
                if squash(slides[n - 1]["title"]) != squash(want):
                    fails.append("title %d %r != %r" % (n, slides[n - 1]["title"], want))
            elif squash(want) not in squash(slides[n - 1].get("text", "")):
                fails.append("slide %d lacks title text %r" % (n, want))
        for n, want in notes:
            if kind not in ("key", "pptx"):
                fails.append("--notes needs a .key or .pptx")
            elif n > len(slides):
                fails.append("notes %d: no such slide" % n)
            elif squash(want) not in squash(slides[n - 1]["notes"]):
                fails.append("notes %d lack %r" % (n, want))
        if ns.skipped is not None and kind in ("key", "pptx"):
            want = sorted(int(x) for x in ns.skipped.split(",") if x.strip())
            if rep["skipped"] != want:
                fails.append("skipped %s != %s" % (rep["skipped"], want))
        if ns.theme and kind == "key" and ns.theme not in (info.get("theme"), info.get("theme_name")):
            fails.append("theme %r != %r" % (info.get("theme"), ns.theme))
        if ns.show:
            rep["detail"] = slides
        rep["ok"] = not fails
        all_ok &= rep["ok"]
        print(json.dumps(rep, ensure_ascii=False))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
