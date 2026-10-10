"""Build an EPUB (or AZW3/PDF/DOCX…) from a folder of Markdown or HTML chapters.

    bash calibre.sh py md_to_epub.py chapters/ -o book.epub --title "T" --authors "A" \
        --language en [--cover cover.jpg] [--series S --series-index 2] [--toc-levels 2]

Each chapter becomes its own spine document, so footnote ids and page breaks never
collide. Chapters are taken in natural filename order (or --order), the first heading
of each is its TOC entry, local images are copied in, and links to other chapter
files are rewritten. The result is read back and compared with what was asked for;
the JSON on stdout says what was built. Exit 4 when the read-back disagrees.
"""
import argparse
import fnmatch
import html
import os
import re
import shutil
import sys
import tempfile
from urllib.parse import unquote, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cal_common import emit, fail, read_meta, tool  # noqa: E402
from ebook_check import epub_report  # noqa: E402

MD_EXT = (".md", ".markdown", ".mdown", ".txt")
HTML_EXT = (".html", ".htm", ".xhtml")
CSS = """body { font-family: serif; line-height: 1.4; }
h1 { page-break-before: always; margin-top: 2em; }
img { max-width: 100%; height: auto; }
figure, .figure { text-align: center; }
table { border-collapse: collapse; margin: 1em 0; }
td, th { border: 1px solid #888; padding: .2em .5em; }
pre, code { font-family: monospace; font-size: .9em; }
pre { white-space: pre-wrap; }
.footnote { font-size: .85em; }
"""


def natural_key(name):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


def collect(src, order, excludes):
    if order:
        files = [os.path.abspath(f) for f in order]
        missing = [f for f in files if not os.path.isfile(f)]
        if missing:
            fail(3, "files in --order not found", missing=missing)
        return files, []
    if os.path.isfile(src):
        return [os.path.abspath(src)], []
    if not os.path.isdir(src):
        fail(3, f"no such file or folder: {src}")
    files, skipped = [], []
    for name in sorted(os.listdir(src), key=natural_key):
        path = os.path.join(src, name)
        if not os.path.isfile(path) or name.startswith("."):
            continue
        ext = os.path.splitext(name)[1].lower()
        if ext not in MD_EXT + HTML_EXT:
            skipped.append({"file": name, "reason": "not a chapter format"})
        elif ext == ".txt":
            skipped.append({"file": name, "reason": ".txt is not taken from a folder; list it in --order"})
        elif any(fnmatch.fnmatch(name, pat) for pat in excludes):
            skipped.append({"file": name, "reason": "matches --exclude"})
        else:
            files.append(os.path.abspath(path))
    if not files:
        fail(3, f"no Markdown/HTML chapters in {src}", skipped=skipped)
    return files, skipped


FRONT = re.compile(r"\A---\s*\n(.*?)\n(---|\.\.\.)\s*\n", re.S)


def render_markdown(text):
    import markdown
    meta = {}
    m = FRONT.match(text)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip().lower()] = v.strip().strip("'\"")
        text = text[m.end():]
    # dotted names, and no "extra": the frozen calibre bundle has no entry points for
    # the short names, which "extra" itself relies on
    md = markdown.Markdown(extensions=[f"markdown.extensions.{e}" for e in (
        "footnotes", "tables", "fenced_code", "attr_list", "def_list", "abbr", "md_in_html",
        "sane_lists", "smarty")])
    return md.convert(text), meta


def title_from_filename(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    stem = re.sub(r"^[\d\s._-]+", "", stem) or stem
    return re.sub(r"[-_]+", " ", stem).strip().title()


def shift_headings(body, shift):
    if shift <= 0:
        return body
    def repl(m):
        n = max(1, int(m.group(2)) - shift)
        return f"<{m.group(1)}h{n}"
    return re.sub(r"<(/?)h([1-6])", repl, body)


def build(args):
    from lxml import html as lhtml

    files, skipped = collect(args.src, args.order, args.exclude)
    stage = tempfile.mkdtemp(prefix="md2epub-")
    os.makedirs(os.path.join(stage, "images"))
    chapters, warnings, used_images = [], [], {}
    href_of = {os.path.abspath(f): f"ch{i:03d}.html" for i, f in enumerate(files, 1)}

    for i, path in enumerate(files, 1):
        raw = open(path, encoding="utf-8-sig").read()
        if path.lower().endswith(HTML_EXT):
            doc = lhtml.fromstring(raw)
            body_el = doc.find(".//body")
            body = "".join(lhtml.tostring(c, encoding="unicode") for c in (body_el if body_el is not None else [doc]))
            meta = {}
        else:
            body, meta = render_markdown(raw)
        levels = [int(n) for n in re.findall(r"<h([1-6])[\s>]", body)]
        if levels and min(levels) > 1:          # chapters written with ## as the top level
            body = shift_headings(body, min(levels) - 1)
            levels = [n - (min(levels) - 1) for n in levels]
        h1s = re.findall(r"<h1[^>]*>(.*?)</h1>", body, re.S)
        if not h1s or not body.lstrip().startswith("<h1"):
            title = meta.get("title") or (html.unescape(re.sub("<[^>]+>", "", h1s[0])) if h1s else title_from_filename(path))
            if not h1s:
                body = f"<h1>{html.escape(title)}</h1>\n{body}"
                warnings.append(f"{os.path.basename(path)}: no top-level heading, added '{title}'")
        else:
            title = html.unescape(re.sub(r"<[^>]+>", "", h1s[0])).strip()
        if len(h1s) > 1:
            warnings.append(f"{os.path.basename(path)}: {len(h1s)} top-level headings, each becomes a TOC entry")

        frag = lhtml.fragment_fromstring(body, create_parent="div")
        base = os.path.dirname(path)
        for img in frag.iter("img"):
            src = img.get("src", "")
            if urlparse(src).scheme in ("http", "https", "data"):
                if urlparse(src).scheme != "data":
                    warnings.append(f"{os.path.basename(path)}: remote image not embedded: {src}")
                continue
            ipath = os.path.abspath(os.path.join(base, unquote(src)))
            if not os.path.isfile(ipath):
                warnings.append(f"{os.path.basename(path)}: missing image {src}")
                continue
            if ipath not in used_images:
                name = f"img{len(used_images) + 1:03d}{os.path.splitext(ipath)[1].lower()}"
                shutil.copy2(ipath, os.path.join(stage, "images", name))
                used_images[ipath] = name
            img.set("src", "images/" + used_images[ipath])
            if not img.get("alt"):
                img.set("alt", "")
        for a in frag.iter("a"):
            href = a.get("href", "")
            if not href or urlparse(href).scheme or href.startswith("#"):
                continue
            target, _, anchor = href.partition("#")
            tpath = os.path.abspath(os.path.join(base, unquote(target)))
            if tpath in href_of:
                a.set("href", href_of[tpath] + ("#" + anchor if anchor else ""))
        inner = "".join(lhtml.tostring(c, encoding="unicode") for c in frag)
        inner = (frag.text or "") + inner
        doc = (f'<?xml version="1.0" encoding="utf-8"?>\n<html xmlns="http://www.w3.org/1999/xhtml">'
               f'<head><title>{html.escape(title)}</title><link rel="stylesheet" href="style.css"/>'
               f'</head><body>{inner}</body></html>')
        with open(os.path.join(stage, href_of[path]), "w", encoding="utf-8") as f:
            f.write(doc)
        chapters.append({"file": os.path.basename(path), "title": title})

    with open(os.path.join(stage, "style.css"), "w") as f:
        f.write(CSS + (open(args.css).read() if args.css else ""))
    manifest = ['<item id="css" href="style.css" media-type="text/css"/>']
    manifest += [f'<item id="c{i}" href="ch{i:03d}.html" media-type="application/xhtml+xml"/>'
                 for i in range(1, len(files) + 1)]
    for name in used_images.values():
        mt = {".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png", ".gif": "gif", ".svg": "svg+xml",
              ".webp": "webp"}.get(os.path.splitext(name)[1], "png")
        manifest.append(f'<item id="{name.replace(".", "_")}" href="images/{name}" media-type="image/{mt}"/>')
    spine = "".join(f'<itemref idref="c{i}"/>' for i in range(1, len(files) + 1))
    opf = os.path.join(stage, "book.opf")
    with open(opf, "w", encoding="utf-8") as f:
        f.write(f'<?xml version="1.0" encoding="utf-8"?>\n<package xmlns="http://www.idpf.org/2007/opf" '
                f'version="2.0" unique-identifier="id"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
                f'<dc:title>{html.escape(args.title)}</dc:title><dc:language>{args.language}</dc:language>'
                f'</metadata><manifest>{"".join(manifest)}</manifest><spine>{spine}</spine></package>')

    out = os.path.abspath(args.output)
    if not args.author_sort:  # ebook-convert leaves file-as empty, which reads back "Unknown"
        from calibre.ebooks.metadata import author_to_author_sort
        args.author_sort = " & ".join(author_to_author_sort(a.strip()) for a in args.authors.split("&"))
    cmd = [opf, out, "--title", args.title, "--authors", args.authors, "--language", args.language,
           "--level1-toc", "//h:h1", "--chapter", "//h:h1", "--page-breaks-before", "//h:h1",
           "--max-toc-links", "0", "--toc-threshold", "1"]
    if args.toc_levels >= 2:
        cmd += ["--level2-toc", "//h:h2"]
    if args.toc_levels >= 3:
        cmd += ["--level3-toc", "//h:h3"]
    if args.cover:
        if not os.path.isfile(args.cover):
            fail(3, f"cover not found: {args.cover}")
        cmd += ["--cover", os.path.abspath(args.cover), "--preserve-cover-aspect-ratio"]
    for flag in ("series", "series_index", "publisher", "tags", "comments", "pubdate", "isbn",
                 "author_sort", "title_sort"):
        val = getattr(args, flag)
        if val not in (None, ""):
            cmd += ["--" + flag.replace("_", "-"), str(val)]
    if out.lower().endswith(".epub"):
        cmd += ["--epub-version", args.epub_version]
        if args.inline_toc:
            cmd += ["--epub-inline-toc"]
        if not args.cover and args.no_generated_cover:
            cmd += ["--no-default-epub-cover"]
    cmd += args.extra
    tool("ebook-convert", *cmd)
    shutil.rmtree(stage, ignore_errors=True)

    meta = read_meta(out)
    problems = []
    if meta["title"] != args.title:
        problems.append(f"title read back as {meta['title']!r}")
    want_authors = [a.strip() for a in args.authors.split("&")]
    if meta["authors"] != want_authors:
        problems.append(f"authors read back as {meta['authors']}")
    if args.series and meta["series"] != args.series:
        problems.append(f"series read back as {meta['series']!r}")
    result = {"ok": True, "output": out, "metadata": meta, "chapters": chapters,
              "images": len(used_images), "skipped": skipped, "warnings": warnings}
    if out.lower().endswith(".epub"):
        rep = epub_report(out, run_epubcheck=not args.no_epubcheck)
        top = [e["title"] for e in rep["toc"] if e["level"] == 1]
        want = [c["title"] for c in chapters]
        if [t.strip() for t in top] != [t.strip() for t in want]:
            problems.append(f"TOC level 1 is {top}, expected {want}")
        if args.cover and not rep["cover"]:
            problems.append("cover missing from the EPUB")
        result.update(toc=rep["toc"], cover=rep["cover"], epubcheck=rep["epubcheck"])
        if rep["epubcheck"].get("errors"):
            problems.append(f"epubcheck: {rep['epubcheck']['errors']} errors")
    if problems:
        result.update(ok=False, problems=problems)
        emit(result, 4)
    emit(result)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", nargs="?", default=".", help="folder of chapters (or one file)")
    ap.add_argument("-o", "--output", required=True, help="book.epub / .azw3 / .pdf / .docx")
    ap.add_argument("--title", required=True)
    ap.add_argument("--authors", required=True, help='"A & B" for several authors')
    ap.add_argument("--language", required=True,
                    help="ISO 639 code of the book's text (en, hu, de…); calibre would otherwise use the UI locale")
    ap.add_argument("--cover")
    ap.add_argument("--series")
    ap.add_argument("--series-index", type=float)
    ap.add_argument("--publisher")
    ap.add_argument("--tags", help="comma separated")
    ap.add_argument("--comments", help="description (HTML allowed)")
    ap.add_argument("--pubdate", help="YYYY-MM-DD")
    ap.add_argument("--isbn")
    ap.add_argument("--author-sort")
    ap.add_argument("--title-sort")
    ap.add_argument("--order", nargs="+", help="explicit chapter files in order")
    ap.add_argument("--exclude", nargs="*", default=["README*", "_*", "NOTES*"],
                    help="filename globs to skip in a folder (default: README*, _*, NOTES*)")
    ap.add_argument("--toc-levels", type=int, default=2, choices=(1, 2, 3))
    ap.add_argument("--css", help="extra stylesheet appended to the default one")
    ap.add_argument("--epub-version", default="3", choices=("2", "3"))
    ap.add_argument("--inline-toc", action="store_true", help="also add a printed contents page")
    ap.add_argument("--no-generated-cover", action="store_true",
                    help="no cover at all when --cover is not given (default: calibre draws one)")
    ap.add_argument("--no-epubcheck", action="store_true")
    argv = sys.argv[1:]
    extra = []
    if "--" in argv:  # everything after a second -- goes to ebook-convert unchanged
        cut = argv.index("--")
        argv, extra = argv[:cut], argv[cut + 1:]
    args = ap.parse_args(argv)
    args.extra = extra
    build(args)


if __name__ == "__main__":
    main()
