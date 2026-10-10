"""Convert a text PDF to a clean EPUB: ebook-convert with heuristics, then a repair
pass over the result, then a quality report.

    bash calibre.sh py pdf_to_epub.py book.pdf -o book.epub --language en \
        [--title T --authors "A"] [--cover c.jpg] [--keep-headers] [--no-unwrap] [--dry-run]

Repair pass (calibre's own container API, so the EPUB stays valid):
  - words split by a line-break hyphen are rejoined when the joined word is in
    calibre's dictionary or used elsewhere in the book ("con-tinued" -> "continued";
    "well-known" stays), including splits across two paragraphs and splits with the
    page number caught inside them at a page break ("mech-1 anism")
  - paragraphs broken mid-sentence are merged (previous has no closing punctuation,
    next starts lower-case)
  - bare page numbers and running headers/footers (short lines repeated 3+ times
    that are upper-case, contain the title/author, or carry a page number) are removed
  - when the TOC has no chapters, it is rebuilt from the most frequent heading level,
    and each document gets its chapter title instead of the PDF's file path
The JSON lists every change and the issues that remain. Scanned PDFs (no text
layer) exit 3: they need OCR before any conversion is worth doing.
"""
import argparse
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cal_common import emit, fail, read_meta, tool  # noqa: E402
from ebook_check import PAGE_NO, SCENE, SPLIT, SPLIT_END, Speller, epub_report, pdf_report, smell_list  # noqa: E402

XHTML = "http://www.w3.org/1999/xhtml"
END_PUNCT = re.compile(r"[.!?:;\"'”’)\]…]\s*$")


def text_of(el):
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def merge_into(p, q):
    """Append paragraph q's content to p and drop q."""
    children = list(q)
    if len(p):
        last = p[-1]
        last.tail = (last.tail or "") + (q.text or "")
    else:
        p.text = (p.text or "") + (q.text or "")
    for c in children:
        p.append(c)
    q.getparent().remove(q)


def strip_trailing(p, pattern):
    """Remove a regex match from the very end of p's text content."""
    node = p[-1] if len(p) else None
    if node is not None and node.tail and node.tail.strip():
        node.tail = re.sub(pattern, "", node.tail)
    elif node is not None and node.text is not None and not len(node):
        node.text = re.sub(pattern, "", node.text)
    else:
        p.text = re.sub(pattern, "", p.text or "")


def repair(path, args, speller_langs):
    from calibre.ebooks.oeb.polish.container import get_container
    from calibre.ebooks.oeb.polish.toc import commit_toc, from_xpaths, get_toc

    c = get_container(path, tweak_mode=True)
    spine = [name for name, _ in c.spine_names]
    meta = read_meta(path)
    title_l = (meta["title"] or "").lower()
    authors_l = [a.lower() for a in meta["authors"]]

    # pass 1: vocabulary + paragraph census
    vocab, counts = Counter(), Counter()
    for name in spine:
        for p in c.parsed(name).iter(f"{{{XHTML}}}p"):
            t = text_of(p)
            vocab.update(w.lower() for w in re.findall(r"[A-Za-z]{3,}", t))
            if t and len(t) <= 80:
                counts[t] += 1
    sp = Speller(speller_langs, vocab)

    def running_header(t):
        if counts[t] < 3 or SCENE.match(t):
            return False
        low = t.lower()
        return (t.isupper() or (title_l and title_l in low) or any(a in low for a in authors_l)
                or bool(re.search(r"\d", t)))

    stats = Counter()
    joined, removed_headers = Counter(), Counter()

    def join_words(text):
        def fix(m):
            if sp.is_line_break_split(m.group(1), m.group(2)):
                joined[m.group(1) + m.group(2)] += 1
                return m.group(1) + m.group(2)
            return m.group(0)
        return SPLIT.sub(fix, text)

    for name in spine:
        root = c.parsed(name)
        changed = False
        paras = list(root.iter(f"{{{XHTML}}}p"))
        for p in paras:
            if p.getparent() is None:
                continue
            t = text_of(p)
            if t and PAGE_NO.match(t):
                p.getparent().remove(p)
                stats["page_numbers_removed"] += 1
                changed = True
                continue
            if t and not args.keep_headers and running_header(t):
                p.getparent().remove(p)
                removed_headers[t] += 1
                changed = True
                continue
            for el in p.iter():
                for attr in ("text", "tail"):
                    v = getattr(el, attr)
                    if el is p and attr == "tail":
                        continue
                    if v and "-" in v:
                        nv = join_words(v)
                        if nv != v:
                            setattr(el, attr, nv)
                            changed = True
        # cross-paragraph repairs; blank spacer paragraphs between the two halves
        # (calibre's "softbreak"/"whitespace" at a PDF page end) are dropped
        paras = [p for p in root.iter(f"{{{XHTML}}}p") if p.getparent() is not None and text_of(p)]
        i = 0
        while i < len(paras) - 1:
            p, q = paras[i], paras[i + 1]
            tp, tq = text_of(p), text_of(q)
            gap, nxt = [], p.getnext()
            while nxt is not None and nxt is not q and nxt.tag == f"{{{XHTML}}}p" and not text_of(nxt) \
                    and not len(nxt):
                gap.append(nxt)
                nxt = nxt.getnext()
            if nxt is not q:
                i += 1
                continue
            m, n = SPLIT_END.search(tp), re.match(r"([a-z]{2,})", tq)
            if m and n and sp.is_line_break_split(m.group(1), n.group(1)):
                for g in gap:
                    g.getparent().remove(g)
                strip_trailing(p, r"-(?:\s*\d{1,3})?\s*$")
                q.text = (q.text or "").lstrip()
                merge_into(p, q)
                joined[m.group(1) + n.group(1)] += 1
                paras.pop(i + 1)
                changed = True
                continue
            if not args.no_unwrap and not END_PUNCT.search(tp) and re.match(r"[a-z]", tq):
                for g in gap:
                    g.getparent().remove(g)
                if p.text is not None or len(p):
                    q.text = " " + (q.text or "").lstrip()
                merge_into(p, q)
                stats["paragraphs_merged"] += 1
                paras.pop(i + 1)
                changed = True
                continue
            i += 1
        # document title: first heading instead of the PDF path
        heading = next((h for h in root.iter(*(f"{{{XHTML}}}h{k}" for k in range(1, 4))) if text_of(h)), None)
        tel = root.find(f".//{{{XHTML}}}title")
        if heading is not None and tel is not None and (not tel.text or "/" in tel.text or tel.text.endswith(".pdf")):
            tel.text = text_of(heading)
            changed = True
        if changed:
            c.dirty(name)

    # TOC: rebuild from headings when it has no real chapters
    toc = get_toc(c)
    before = [n.title for n in toc.iterdescendants()]
    rebuilt = None
    if len(before) <= 1:
        levels = Counter()
        for name in spine:
            for k in range(1, 4):
                levels[k] += sum(1 for h in c.parsed(name).iter(f"{{{XHTML}}}h{k}") if text_of(h))
        top = next((k for k in (1, 2, 3) if levels[k] >= 2), None)
        if top:
            xp = [f"//h:h{top}"] + ([f"//h:h{top + 1}"] if levels[top + 1] >= 2 and top < 3 else [])
            new = from_xpaths(c, xp)
            if len(list(new.iterdescendants())) >= 2:
                commit_toc(c, new)
                rebuilt = [n.title for n in new.iterdescendants()]
    if not args.dry_run:
        c.commit()
    return {
        "words_rejoined": sum(joined.values()), "rejoined_examples": dict(joined.most_common(12)),
        "page_numbers_removed": stats["page_numbers_removed"],
        "running_headers_removed": dict(removed_headers),
        "paragraphs_merged": stats["paragraphs_merged"],
        "toc_before": before, "toc_rebuilt": rebuilt,
        "header_candidates_kept": {t: n for t, n in counts.most_common(8)
                                   if n >= 3 and t not in removed_headers and not SCENE.match(t)
                                   and not PAGE_NO.match(t)},
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("-o", "--output", required=True, help="book.epub (repair pass is EPUB only)")
    ap.add_argument("--language", required=True, help="ISO 639 code of the text, e.g. en")
    ap.add_argument("--title")
    ap.add_argument("--authors", help='"A & B"')
    ap.add_argument("--cover", help="image file; default: calibre renders the first page")
    ap.add_argument("--no-heuristics", action="store_true", help="skip calibre's heuristic processing")
    ap.add_argument("--keep-headers", action="store_true", help="do not remove repeated header lines")
    ap.add_argument("--no-unwrap", action="store_true", help="do not merge mid-sentence paragraph breaks")
    ap.add_argument("--force", action="store_true", help="convert even without a text layer")
    ap.add_argument("--dry-run", action="store_true", help="convert and report, but leave repairs unsaved")
    argv = sys.argv[1:]
    extra = []
    if "--" in argv:  # everything after a second -- goes to ebook-convert unchanged
        cut = argv.index("--")
        argv, extra = argv[:cut], argv[cut + 1:]
    args = ap.parse_args(argv)
    if not os.path.isfile(args.pdf):
        fail(3, f"no such file: {args.pdf}")
    out = os.path.abspath(args.output)
    if not out.lower().endswith(".epub"):
        fail(2, "output must be .epub; convert the EPUB onward with ebook-convert afterwards")
    src = pdf_report(args.pdf)
    if not src["text_layer"] and not args.force:
        fail(3, "the PDF has no text layer (scanned); run OCR first (e.g. ocrmypdf) or pass --force",
             pdf=src)

    # the PDF's own Title/Author fill what was not given; author sort is always set,
    # because ebook-convert leaves it empty and it reads back as "Unknown"
    from calibre.ebooks.metadata import author_to_author_sort
    pdf_meta = read_meta(args.pdf)
    title = args.title or pdf_meta["title"]
    authors = args.authors or " & ".join(pdf_meta["authors"])
    cmd = [args.pdf, out, "--language", args.language]
    if not args.no_heuristics:
        cmd += ["--enable-heuristics"]
    if title and title != "Unknown":
        cmd += ["--title", title]
    if authors and authors != "Unknown":
        cmd += ["--authors", authors, "--author-sort",
                " & ".join(author_to_author_sort(a.strip()) for a in authors.split("&"))]
    if args.cover:
        cmd += ["--cover", os.path.abspath(args.cover)]
    tool("ebook-convert", *(cmd + extra))
    before = epub_report(out, run_epubcheck=False)["smells"]
    fixes = repair(out, args, [args.language])
    rep = epub_report(out)
    meta = read_meta(out)
    issues = smell_list(rep["smells"], rep["toc_level1"], rep["smells"]["words"])
    if meta["title"] in (None, "", "Unknown") or meta["authors"] in ([], ["Unknown"]):
        issues.append("title or author is Unknown; pass --title/--authors")
    emit({"ok": True, "output": out, "source": src, "metadata": meta, "fixes": fixes,
          "smells_before_repair": {k: before[k] for k in ("split_word_count", "page_number_paragraphs",
                                                          "mid_sentence_breaks")},
          "toc": [(e["level"], e["title"]) for e in rep["toc"]], "smells": rep["smells"],
          "epubcheck": rep["epubcheck"], "remaining_issues": issues})


if __name__ == "__main__":
    main()
