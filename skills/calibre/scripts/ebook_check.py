"""Inspect an e-book and report metadata, structure and conversion smells as JSON.

    bash calibre.sh py ebook_check.py book.epub [--expect-title T] [--expect-authors "A & B"]
        [--expect-language en] [--expect-series S] [--expect-series-index 2]
        [--expect-toc 6] [--expect-cover] [--max-epubcheck-errors 0] [--strict]

EPUB: OPF metadata, spine, cover, TOC (nav or NCX, with levels), images, word count,
epubcheck (when installed) and the usual PDF-conversion smells: running headers or
footers repeated as paragraphs, bare page numbers, words split by a hyphen, sentences
broken across paragraphs, image-only pages. Other formats: metadata via calibre; PDF
also gets page count and whether it has a text layer. Exit 4 when an --expect-*
check fails (or, with --strict, when any smell is found).
"""
import argparse
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from urllib.parse import unquote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cal_common import emit, fail, read_meta  # noqa: E402

NS = {"opf": "http://www.idpf.org/2007/opf", "dc": "http://purl.org/dc/elements/1.1/",
      "ncx": "http://www.daisy.org/z3986/2005/ncx/", "x": "http://www.w3.org/1999/xhtml",
      "ops": "http://www.idpf.org/2007/ops", "c": "urn:oasis:names:tc:opendocument:xmlns:container"}
PAGE_NO = re.compile(r"^\s*(?:page\s*)?[-–—(\[]?\s*\d{1,3}\s*[-–—)\]]?\s*$", re.I)
# a word split at a line end; at a page break the page number can land inside it ("mech-1 anism")
SPLIT = re.compile(r"\b([A-Za-z]{2,})-\s*(?:\d{1,3}\s+)?([a-z]{2,})\b")
SPLIT_END = re.compile(r"([A-Za-z]{2,})-(?:\s*\d{1,3})?$")
SCENE = re.compile(r"^[\s*#~•·◆◇—-]{1,12}$")


class Speller:
    """Is a word real? calibre's bundled hunspell (en-US and en-GB, or the book's
    language) plus every word the book itself uses unhyphenated."""

    def __init__(self, langs, vocab):
        self.vocab = vocab
        self.dicts, self.locales = None, []
        try:
            from calibre.spell import parse_lang_code
            from calibre.spell.dictionary import Dictionaries
            self.dicts = Dictionaries()
            self.dicts.initialize()
            codes = [lang for lang in langs if lang] or ["en"]
            if any(c.startswith("en") for c in codes):
                codes += ["en-US", "en-GB"]
            self.locales = [parse_lang_code(c) for c in dict.fromkeys(codes)]
        except Exception:
            self.dicts = None

    def known(self, word):
        w = word.lower()
        if w in self.vocab:
            return True
        if self.dicts:
            for loc in self.locales:
                try:
                    if self.dicts.recognized(w, loc):
                        return True
                except Exception:
                    pass
        return False

    def is_line_break_split(self, a, b):
        """'con-tinued' yes; 'well-known' no (both halves are words, the join isn't)."""
        joined = a + b
        if self.known(joined):
            return True
        return not (self.known(a) or self.known(b))


def _xml(data):
    from lxml import etree
    return etree.fromstring(data, parser=etree.XMLParser(recover=True, huge_tree=True))


def _text(el):
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def epub_structure(path):
    z = zipfile.ZipFile(path)
    names = set(z.namelist())
    opf_path = _xml(z.read("META-INF/container.xml")).find(".//c:rootfile", NS).get("full-path")
    opf = _xml(z.read(opf_path))
    base = posixpath.dirname(opf_path)

    def full(href):
        return posixpath.normpath(posixpath.join(base, unquote(href.split("#")[0])))

    manifest = {i.get("id"): i for i in opf.iterfind(".//opf:manifest/opf:item", NS)}
    spine_ids = [r.get("idref") for r in opf.iterfind(".//opf:spine/opf:itemref", NS)]
    spine = [full(manifest[i].get("href")) for i in spine_ids if i in manifest]
    md = opf.find(".//opf:metadata", NS)

    cover = None
    for item in manifest.values():
        if "cover-image" in (item.get("properties") or ""):
            cover = full(item.get("href"))
    meta_cover = md.find("opf:meta[@name='cover']", NS) if md is not None else None
    if not cover and meta_cover is not None and meta_cover.get("content") in manifest:
        cover = full(manifest[meta_cover.get("content")].get("href"))
    if cover and cover not in names:
        cover = None

    toc = []
    nav = next((i for i in manifest.values() if "nav" in (i.get("properties") or "").split()), None)
    ncx_id = opf.find(".//opf:spine", NS).get("toc")
    if ncx_id and ncx_id in manifest:
        ncx = _xml(z.read(full(manifest[ncx_id].get("href"))))

        def walk(parent, level):
            for np in parent.iterfind("ncx:navPoint", NS):
                label = np.find("ncx:navLabel/ncx:text", NS)
                toc.append({"level": level, "title": _text(label) if label is not None else "",
                            "href": np.find("ncx:content", NS).get("src")})
                walk(np, level + 1)
        walk(ncx.find("ncx:navMap", NS), 1)
    elif nav is not None:
        doc = _xml(z.read(full(nav.get("href"))))
        navel = next((n for n in doc.iter("{%s}nav" % NS["x"])
                      if n.get("{%s}type" % NS["ops"]) == "toc"), None)

        def walk_ol(ol, level):
            for li in ol.iterfind("x:li", NS):
                a = li.find("x:a", NS)
                if a is None:
                    a = li.find("x:span", NS)
                toc.append({"level": level, "title": _text(a) if a is not None else "",
                            "href": a.get("href") if a is not None else None})
                sub = li.find("x:ol", NS)
                if sub is not None:
                    walk_ol(sub, level + 1)
        if navel is not None and navel.find("x:ol", NS) is not None:
            walk_ol(navel.find("x:ol", NS), 1)
    return z, md, spine, cover, toc


def text_smells(z, spine, langs, cover=None):
    paras, images_only, empty, words = [], [], [], 0
    for name in spine:
        try:
            doc = _xml(z.read(name))
        except KeyError:
            continue
        body = doc.find(".//x:body", NS)
        if body is None:
            body = doc
        txt = _text(body)
        imgs = len(body.findall(".//x:img", NS)) + len(body.findall(".//{http://www.w3.org/2000/svg}image"))
        if not txt:
            srcs = [i.get("src") or i.get("{http://www.w3.org/1999/xlink}href") or ""
                    for i in body.iter("{%s}img" % NS["x"], "{http://www.w3.org/2000/svg}image")]
            if cover and any(posixpath.basename(unquote(s)) == posixpath.basename(cover) for s in srcs):
                continue  # the cover page
            (images_only if imgs else empty).append(name)
        words += len(txt.split())
        for el in body.iter("{%s}p" % NS["x"], "{%s}div" % NS["x"]):
            if el.tag.endswith("div") and el.find("x:p", NS) is not None:
                continue
            t = _text(el)
            if t:
                paras.append(t)

    vocab = Counter()
    for p in paras:
        vocab.update(w.lower() for w in re.findall(r"[A-Za-z]{3,}", p))
    sp = Speller(langs, vocab)
    split_words = Counter()
    for p in paras:
        for a, b in SPLIT.findall(p):
            if sp.is_line_break_split(a, b):
                split_words[f"{a}-{b}"] += 1
    for p, q in zip(paras, paras[1:]):  # hyphen at a paragraph end, word continues in the next
        m, n = SPLIT_END.search(p), re.match(r"([a-z]{2,})", q)
        if m and n and sp.is_line_break_split(m.group(1), n.group(1)):
            split_words[f"{m.group(1)}-|{n.group(1)}"] += 1
    page_numbers = [p for p in paras if PAGE_NO.match(p)]
    counts = Counter(p for p in paras if len(p) <= 80 and not SCENE.match(p) and not PAGE_NO.match(p))
    repeated = {p: c for p, c in counts.most_common(10) if c >= 3}
    broken = sum(1 for p, q in zip(paras, paras[1:])
                 if not re.search(r"[.!?:;\"'”’)\]…]$", p) and re.match(r"[a-z]", q))
    return {
        "paragraphs": len(paras), "words": words,
        "page_number_paragraphs": len(page_numbers),
        "repeated_short_paragraphs": repeated,
        "split_words": dict(split_words.most_common(25)), "split_word_count": sum(split_words.values()),
        "mid_sentence_breaks": broken,
        "image_only_documents": len(images_only), "empty_documents": len(empty),
    }


def run_epubcheck(path):
    exe = shutil.which("epubcheck")
    jar = os.environ.get("EPUBCHECK_JAR")
    if not exe and not jar:
        return {"available": False}
    out = tempfile.mktemp(suffix=".json")
    cmd = [exe] if exe else ["java", "-jar", jar]
    subprocess.run(cmd + [path, "--json", out], capture_output=True, text=True)
    try:
        data = json.load(open(out))
    except (OSError, ValueError):
        return {"available": True, "errors": None, "note": "epubcheck produced no report"}
    finally:
        if os.path.exists(out):
            os.remove(out)
    msgs = data.get("messages", [])
    errs = [m for m in msgs if m.get("severity") in ("ERROR", "FATAL")]
    return {"available": True, "version": data.get("checker", {}).get("checkerVersion"),
            "errors": len(errs), "warnings": sum(1 for m in msgs if m.get("severity") == "WARNING"),
            "first_errors": [f"{m.get('ID')}: {m.get('message')}" for m in errs[:8]]}


def epub_report(path, run_epubcheck=True):
    z, md, spine, cover, toc = epub_structure(path)
    langs = [_text(e) for e in md.iterfind("dc:language", NS)] if md is not None else []
    rep = {"spine_documents": len(spine), "cover": cover, "toc": toc,
           "toc_entries": len(toc), "toc_level1": sum(1 for e in toc if e["level"] == 1),
           "images": sum(1 for n in z.namelist() if re.search(r"\.(jpe?g|png|gif|svg|webp)$", n, re.I)),
           "smells": text_smells(z, spine, langs, cover)}
    rep["epubcheck"] = run_epubcheck_safe(path) if run_epubcheck else {"available": False, "skipped": True}
    return rep


def run_epubcheck_safe(path):
    try:
        return run_epubcheck(path)
    except Exception as e:  # epubcheck trouble must not hide the rest of the report
        return {"available": True, "errors": None, "note": f"epubcheck failed: {e}"}


def smell_list(s, toc_level1, words):
    issues = []
    if s["repeated_short_paragraphs"]:
        top = max(s["repeated_short_paragraphs"].items(), key=lambda kv: kv[1])
        issues.append(f"running header/footer kept as text: {top[0]!r} ×{top[1]}")
    if s["page_number_paragraphs"]:
        issues.append(f"{s['page_number_paragraphs']} bare page-number paragraphs")
    if s["split_word_count"]:
        issues.append(f"{s['split_word_count']} words split by a line-break hyphen, e.g. "
                      + ", ".join(list(s["split_words"])[:4]))
    if s["mid_sentence_breaks"] > max(3, s["paragraphs"] // 20):
        issues.append(f"{s['mid_sentence_breaks']} paragraphs end mid-sentence (lines not unwrapped)")
    if s["image_only_documents"]:
        issues.append(f"{s['image_only_documents']} image-only pages (scanned or full-page figures; no text)")
    if words > 3000 and toc_level1 <= 1:
        issues.append("no chapter structure in the TOC")
    return issues


def pdf_report(path):
    utils = os.environ.get("CALIBRE_UTILS", "/Applications/calibre.app/Contents/utils.app/Contents/MacOS")
    info = subprocess.run([os.path.join(utils, "pdfinfo"), path], capture_output=True, text=True).stdout
    pages = int(re.search(r"Pages:\s+(\d+)", info).group(1)) if "Pages:" in info else None
    text = subprocess.run([os.path.join(utils, "pdftotext"), "-l", "10", path, "-"],
                          capture_output=True, text=True).stdout
    per_page = len(text.strip()) / max(1, min(10, pages or 1))
    return {"pages": pages, "text_layer": per_page > 200,
            "chars_per_page_first10": round(per_page),
            "note": None if per_page > 200 else "little or no text layer: scanned PDF, needs OCR first"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("book")
    ap.add_argument("--expect-title")
    ap.add_argument("--expect-authors", help='"A & B"')
    ap.add_argument("--expect-language", help="ISO 639-1 or -2 code, e.g. en or eng")
    ap.add_argument("--expect-series")
    ap.add_argument("--expect-series-index", type=float)
    ap.add_argument("--expect-toc", type=int, help="number of level-1 TOC entries")
    ap.add_argument("--expect-cover", action="store_true")
    ap.add_argument("--max-epubcheck-errors", type=int)
    ap.add_argument("--no-epubcheck", action="store_true")
    ap.add_argument("--strict", action="store_true", help="exit 4 when any conversion smell is found")
    args = ap.parse_args()
    if not os.path.isfile(args.book):
        fail(3, f"no such file: {args.book}")
    ext = os.path.splitext(args.book)[1].lower()
    try:
        meta = read_meta(args.book)
    except Exception as e:
        fail(3, f"calibre cannot read {args.book}: {e}")
    out = {"ok": True, "file": os.path.abspath(args.book), "format": ext[1:],
           "size_kb": round(os.path.getsize(args.book) / 1024), "metadata": meta}
    issues = []
    if ext == ".epub":
        try:
            rep = epub_report(args.book, run_epubcheck=not args.no_epubcheck)
        except (zipfile.BadZipFile, KeyError, AttributeError) as e:
            fail(3, f"not a readable EPUB: {e}")
        out.update(rep)
        issues = smell_list(rep["smells"], rep["toc_level1"], rep["smells"]["words"])
    elif ext == ".pdf":
        out["pdf"] = pdf_report(args.book)
    if meta["title"] in (None, "", "Unknown") or meta["authors"] in ([], ["Unknown"]):
        issues.append("title or author is Unknown")
    if not meta["languages"] or meta["languages"] == ["und"]:
        issues.append("no language set")
    out["issues"] = issues

    failed = []
    def check(cond, msg):
        if not cond:
            failed.append(msg)
    if args.expect_title is not None:
        check(meta["title"] == args.expect_title, f"title is {meta['title']!r}")
    if args.expect_authors is not None:
        want = [a.strip() for a in args.expect_authors.split("&")]
        check(meta["authors"] == want, f"authors are {meta['authors']}")
    if args.expect_language:
        from calibre.utils.localization import canonicalize_lang
        check(canonicalize_lang(args.expect_language) in meta["languages"],
              f"languages are {meta['languages']}")
    if args.expect_series is not None:
        check(meta["series"] == args.expect_series, f"series is {meta['series']!r}")
    if args.expect_series_index is not None:
        check(meta["series_index"] == args.expect_series_index, f"series index is {meta['series_index']}")
    if args.expect_cover:
        check(meta["has_cover"] or out.get("cover"), "no cover")
    if args.expect_toc is not None:
        check(out.get("toc_level1") == args.expect_toc, f"TOC has {out.get('toc_level1')} level-1 entries")
    if args.max_epubcheck_errors is not None and out.get("epubcheck", {}).get("available"):
        errs = out["epubcheck"].get("errors")
        check(errs is not None and errs <= args.max_epubcheck_errors, f"epubcheck errors: {errs}")
    if args.strict:
        check(not issues, "conversion issues: " + "; ".join(issues))
    if failed:
        out.update(ok=False, failed=failed)
        emit(out, 4)
    emit(out)


if __name__ == "__main__":
    main()
