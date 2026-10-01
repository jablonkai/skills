"""Helpers for job scripts running *inside* Scribus (``scribus.py run JOB.py``).

Import from a job with ``import scribus_lib as L`` — the runner puts this directory on
``sys.path``. Everything here works in millimetres and wraps the traps of the raw API:

- page sizes are given in the document unit (``PAPER_*`` constants are in points)
- ``loadImage`` accepts a missing file without complaint
- overflowing text is silently cut off in the PDF
- missing fonts are silently substituted
- ``getAllObjects``' first positional argument is the item *type*, not the page

The runner calls :func:`doc_summary` after the job, so overflow and missing images are
reported even when the job never checks for them.
"""
import os

import scribus

MM = scribus.UNIT_MILLIMETERS

# PDFfile().version codes, measured against Scribus 1.6.6
PDF_VERSIONS = {"x4": 10, "x1a": 11, "x3": 12, "1.3": 13, "1.4": 14, "1.5": 15, "1.6": 16}
ALIGN = {"left": 0, "center": 1, "right": 2, "justify": 3, "forced": 4}


class LayoutError(Exception):
    """A layout check failed (overflow, missing image, missing font)."""


# ---------------------------------------------------------------- document
def new_doc(width, height, margins=(10, 10, 10, 10), pages=1, bleed=0.0, facing=False,
            first_page_number=1):
    """Create a document in mm. ``margins`` is (left, right, top, bottom).

    ``facing=True`` makes a facing-pages document (left/right margins become
    inside/outside). Returns the page count.
    """
    if not scribus.newDocument((float(width), float(height)), tuple(float(m) for m in margins),
                               scribus.PORTRAIT, first_page_number, MM,
                               scribus.PAGE_2 if facing else scribus.PAGE_1,
                               1 if facing else 0, int(pages)):
        raise LayoutError("newDocument failed")
    if bleed:
        scribus.setBleeds(bleed, bleed, bleed, bleed)
    return scribus.pageCount()


def open_doc(path):
    """Open an existing .sla and switch it to mm so all helpers agree on units."""
    if not os.path.isfile(path):
        raise LayoutError("no such document: %s" % path)
    cwd = os.getcwd()
    scribus.openDoc(os.path.abspath(path))
    os.chdir(cwd)  # keep the job's relative paths working
    scribus.setUnit(MM)


def save_sla(path):
    """Save the document as .sla (``saveDocAs``; ``saveDoc`` may pop a dialog)."""
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not scribus.saveDocAs(path):
        raise LayoutError("saveDocAs failed: %s" % path)
    return path


# ---------------------------------------------------------------- fonts, colours, styles
def font(*candidates):
    """Return the first installed font name from ``candidates`` ("Family Style").

    Scribus substitutes a missing font silently, so pick fonts through this.
    """
    have = set(scribus.getFontNames())
    for name in candidates:
        if name in have:
            return name
    raise LayoutError("none of these fonts is installed: %s" % ", ".join(candidates))


def find_fonts(fragment):
    """Installed font names containing ``fragment`` (case-insensitive)."""
    frag = fragment.lower()
    return sorted(n for n in scribus.getFontNames() if frag in n.lower())


def cmyk(name, c, m, y, k):
    """Define a CMYK colour from percentages (0-100)."""
    scribus.defineColorCMYK(name, *(int(round(v * 2.55)) for v in (c, m, y, k)))
    return name


def char_style(name, font_name, size, color=None, features=None, tracking=None):
    kw = {"name": name, "font": font_name, "fontsize": float(size)}
    if color:
        kw["fillcolor"] = color
    if features:
        kw["features"] = features
    if tracking is not None:
        kw["tracking"] = tracking
    scribus.createCharStyle(**kw)
    return name


def para_style(name, font_name, size, leading=None, align="left", space_before=0.0,
               space_after=0.0, first_indent=0.0, color=None, features=None):
    """Paragraph style with its own char style ``<name>_c``. Sizes in pt, gaps in mm.

    ``leading`` in pt is fixed (it does not follow later font-size changes); pass
    ``leading="auto"`` for leading proportional to the size, e.g. for shrink-to-fit text.
    """
    cs = char_style(name + "_c", font_name, size, color=color, features=features)
    auto = leading == "auto"
    scribus.createParagraphStyle(
        name=name, linespacingmode=1 if auto else 0,
        linespacing=float(size * 1.2 if auto else (leading or size * 1.25)),
        alignment=ALIGN[align], gapbefore=_mm2pt(space_before), gapafter=_mm2pt(space_after),
        firstindent=_mm2pt(first_indent), charstyle=cs)
    return name


def _mm2pt(v):
    return float(v) * 72.0 / 25.4


# ---------------------------------------------------------------- text
def text_box(page, x, y, w, h, text="", style=None, name=None):
    """Text frame on ``page`` (1-based; None = current page, which is what you want
    inside :func:`master`). ``text`` may be a str or a list of (paragraph_text, style)
    pairs."""
    _goto(page)
    frame = scribus.createText(x, y, w, h, name) if name else scribus.createText(x, y, w, h)
    if text:
        set_paragraphs(frame, text if isinstance(text, list) else [(text, style)])
    return frame


def set_paragraphs(frame, paras):
    """Replace a frame's story with paragraphs, each with its own paragraph style.

    ``paras`` is a list of (text, style_or_None). Styles are applied by selecting each
    paragraph's character range.
    """
    texts = [t for t, _ in paras]
    scribus.setText("\r".join(texts), frame)
    pos = 0
    for text, style in paras:
        if style:
            scribus.selectText(pos, len(text), frame)
            scribus.setParagraphStyle(style, frame)
        pos += len(text) + 1
    scribus.selectText(0, 0, frame)
    scribus.layoutTextChain(frame)


def link(*frames):
    """Thread frames in order so text flows from each into the next."""
    for a, b in zip(frames, frames[1:]):
        scribus.linkTextFrames(a, b)


def flow(first_frame, box=None, master=None, max_pages=200):
    """Continue an overflowing story onto new pages until everything fits.

    Each added page gets a frame at ``box`` = (x, y, w, h), default the page's margin
    box. Returns the list of frames added.
    """
    added = []
    last = first_frame
    while overflows(last):
        if len(added) >= max_pages:
            raise LayoutError("text still overflows after %d added pages" % max_pages)
        if master:
            scribus.newPage(-1, master)
        else:
            scribus.newPage(-1)
        page = scribus.pageCount()
        x, y, w, h = box or margin_box(page)
        nxt = text_box(page, x, y, w, h)
        scribus.linkTextFrames(last, nxt)
        scribus.layoutTextChain(first_frame)
        added.append(nxt)
        last = nxt
    return added


def overflows(frame):
    """True if the story of ``frame``'s chain does not fit."""
    scribus.layoutTextChain(frame)
    return bool(scribus.textOverflows(frame))


def fit_text(frame, min_size=6.0, step=0.5, start=None):
    """Shrink a single frame's text until it fits; returns the final size in pt.

    ``start`` first resets the whole story to that size (use it to retry after
    enlarging the frame). Raises LayoutError if it still overflows at ``min_size``.
    """
    if start is not None:
        _set_size(frame, start)
    scribus.layoutText(frame)
    size = scribus.getFontSize(frame)
    while scribus.textOverflows(frame, 1) and size - step >= min_size:
        size -= step
        _set_size(frame, size)
    if scribus.textOverflows(frame, 1):
        raise LayoutError("%s overflows even at %.1f pt" % (frame, size))
    return size


def _set_size(frame, size):
    scribus.selectText(0, scribus.getTextLength(frame), frame)
    scribus.setFontSize(size, frame)
    scribus.selectText(0, 0, frame)
    scribus.layoutText(frame)


def paragraph_keeps(sla_path, keep_with_next=(), keep_together=(), orphans=0, widows=0,
                    styles=None):
    """Set keep-with-next / keep-together / orphan / widow control on paragraph styles.

    The scripter has no API for these, but the .sla stores them on each STYLE, so this
    edits the saved file. Call it after ``save_sla`` and then :func:`reopen` before
    exporting. ``orphans``/``widows`` = minimum lines kept at the start/end of a
    paragraph when it breaks (2 is typical), applied to ``styles`` (default: all).
    """
    import xml.etree.ElementTree as ET
    tree = ET.parse(sla_path)
    found = set()
    for st in tree.getroot().find("DOCUMENT").findall("STYLE"):
        name = st.get("NAME")
        if name in keep_with_next:
            st.set("KeepWithNext", "1")
            found.add(name)
        if name in keep_together:
            st.set("KeepTogether", "1")
            found.add(name)
        if styles is None or name in styles:
            if orphans:
                st.set("KeepLinesStart", str(int(orphans)))
            if widows:
                st.set("KeepLinesEnd", str(int(widows)))
    missing = (set(keep_with_next) | set(keep_together)) - found
    if missing:
        raise LayoutError("no such paragraph style(s): %s" % sorted(missing))
    tree.write(sla_path, encoding="UTF-8", xml_declaration=True)


def reopen(path):
    """Close the current document and open ``path`` again (after editing the .sla)."""
    path = os.path.abspath(path)
    cwd = os.getcwd()
    scribus.closeDoc()             # closeDoc switches the working directory to ~/Documents
    os.chdir(cwd)
    open_doc(path)


# ---------------------------------------------------------------- images
def image_box(page, path, x, y, w, h, name=None, fit="contain"):
    """Image frame on ``page`` (None = current page).

    fit:
      - ``"contain"`` (default): whole image visible, proportional, letterboxed
      - ``"cover"``: fills the frame proportionally, centred, cropping the overflow
        (full-bleed photos, hero images)
      - ``None``: leave Scribus's default (image at its own ppi, top-left)
    Raises if the file is missing or Scribus could not load it (``loadImage`` alone
    does not).
    """
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        raise LayoutError("image not found: %s" % path)
    _goto(page)
    frame = scribus.createImage(x, y, w, h, name) if name else scribus.createImage(x, y, w, h)
    scribus.loadImage(path, frame)
    if scribus.getImageColorSpace(frame) < 0:
        raise LayoutError("Scribus could not load image: %s" % path)
    if fit in (True, "contain"):
        scribus.setScaleImageToFrame(True, True, frame)
    elif fit == "cover":
        # A non-proportional fit reveals the image's natural size in doc units.
        scribus.setScaleImageToFrame(True, False, frame)
        sx, sy = scribus.getImageScale(frame)
        k = max(sx, sy)
        nw, nh = w / sx, h / sy
        scribus.setScaleImageToFrame(False, False, frame)
        scribus.setImageScale(k, k, frame)
        # setImageOffset takes points whatever the document unit is
        scribus.setImageOffset(_mm2pt((w - nw * k) / 2), _mm2pt((h - nh * k) / 2), frame)
    return frame


def rect(page, x, y, w, h, fill=None, line=None, line_width=0.0, name=None):
    _goto(page)
    r = scribus.createRect(x, y, w, h, name) if name else scribus.createRect(x, y, w, h)
    scribus.setFillColor(fill or "None", r)
    if line:
        scribus.setLineColor(line, r)
        scribus.setLineWidth(line_width or 0.25, r)
    else:
        scribus.setLineColor("None", r)
    return r


# ---------------------------------------------------------------- pages
def _goto(page):
    # gotoPage while a master page is being edited silently leaves it (objects then
    # land on the default master), so helpers called from master() pass page=None.
    if page is not None:
        scribus.gotoPage(page)


def margin_box(page):
    """(x, y, w, h) of the page's margin box in mm."""
    w, h = scribus.getPageNSize(page)
    m = scribus.getPageNMargins(page)  # (top, left, right, bottom)
    top, left, right, bottom = m
    return left, top, w - left - right, h - top - bottom


def master(name, build):
    """Create master page ``name`` and fill it by calling ``build()`` while editing it.

    Inside ``build`` pass ``page=None`` to the frame helpers and never call gotoPage.
    """
    scribus.createMasterPage(name)
    scribus.editMasterPage(name)
    try:
        build()
    finally:
        scribus.closeMasterPage()
    return name


def apply_master(name, pages=None):
    for p in pages or range(1, scribus.pageCount() + 1):
        scribus.applyMasterPage(name, p)


# ---------------------------------------------------------------- export
def export_pdf(path, preset="x4", bleed=None, marks=False, mark_offset=3.0, pages=None,
               title=None, resolution=300):
    """Export the open document to PDF.

    preset:
      - ``x4``: PDF/X-4 with the document's output profile (print)
      - ``x1a`` / ``x3``: older PDF/X flavours (no transparency in x1a)
      - ``print``: PDF 1.6, print colours, no PDF/X
      - ``screen``: PDF 1.5, RGB, 150 ppi downsampling
    bleed: mm on all sides; None uses the document bleeds.
    marks: crop + bleed + registration + colour bars, ``mark_offset`` mm from trim.
    """
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # The PDF Title comes from the document info. When it is empty Scribus writes the
    # .sla's absolute path there, leaking the local folder structure to the printer.
    author, doc_title, desc = _doc_info()
    if title or not doc_title:
        doc_title = title or os.path.splitext(os.path.basename(path))[0]
        scribus.setInfo(author, doc_title, desc)
    pdf = scribus.PDFfile()            # snapshots the document info, so set it first
    pdf.file = path
    pdf.info = doc_title
    pdf.fontEmbedding = 0          # embed (subset) every font
    if preset == "screen":
        pdf.version, pdf.outdst = 15, 0
        pdf.downsample, pdf.resolution = 150, 150
    else:
        pdf.version = PDF_VERSIONS.get(preset, 16)
        pdf.outdst = 1             # print: CMYK output intent
        pdf.resolution = resolution
    if bleed is None:
        pdf.useDocBleeds = True
    else:
        pdf.useDocBleeds = False
        pdf.bleedt = pdf.bleedb = pdf.bleedl = pdf.bleedr = float(bleed)
    if marks:
        pdf.cropMarks = pdf.bleedMarks = pdf.registrationMarks = pdf.colorMarks = True
        pdf.markOffset = float(mark_offset)
    if pages:
        pdf.pages = list(pages)
    pdf.save()
    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        raise LayoutError("PDF export produced no file: %s" % path)
    return path


def _doc_info():
    """(author, title, description). getInfo() returns () on 1.6.6, so fall back to the
    attributes of the .sla on disk (empty for a new, unsaved document)."""
    info = tuple(scribus.getInfo() or ())
    if len(info) == 3:
        return info
    name = scribus.getDocName()
    if name and os.path.isfile(name):
        import xml.etree.ElementTree as ET
        doc = ET.parse(name).getroot().find("DOCUMENT")
        if doc is not None:
            return doc.get("AUTHOR", ""), doc.get("TITLE", ""), doc.get("COMMENTS", "")
    return "", "", ""


# ---------------------------------------------------------------- checks
def doc_summary():
    """Pages, frames, overflow and image problems of the open document (mm)."""
    if not scribus.haveDoc():
        return None
    scribus.setUnit(MM)
    pages = []
    overflow, missing = [], []
    for p in range(1, scribus.pageCount() + 1):
        scribus.gotoPage(p)
        w, h = scribus.getPageNSize(p)
        items = scribus.getAllObjects(page=p - 1)
        texts = images = 0
        for name in items:
            kind = scribus.getObjectType(name)
            if kind == "TextFrame":
                texts += 1
                scribus.layoutText(name)
                if scribus.textOverflows(name, 1) and not _has_next(name):
                    overflow.append({"page": p, "frame": name})
            elif kind == "ImageFrame":
                images += 1
                f = scribus.getImageFile(name)
                if f and scribus.getImageColorSpace(name) < 0:
                    missing.append({"page": p, "frame": name, "file": f})
        pages.append({"page": p, "size_mm": [round(w, 2), round(h, 2)],
                      "master": scribus.getMasterPage(p), "text_frames": texts,
                      "image_frames": images, "items": len(items)})
    return {"pages": len(pages), "page_list": pages, "overflow": overflow,
            "missing_images": missing,
            "paragraph_styles": [s for s in scribus.getParagraphStyles()],
            "masters": list(scribus.masterPageNames())}


def _has_next(frame):
    try:
        return bool(scribus.getNextLinkedFrame(frame))
    except Exception:  # noqa: BLE001 — older builds lack the call
        return False


def assert_clean():
    """Raise if any story overflows or any image frame lost its image."""
    s = doc_summary() or {}
    if s.get("overflow") or s.get("missing_images"):
        raise LayoutError("layout problems: overflow=%s missing_images=%s"
                          % (s.get("overflow"), s.get("missing_images")))
    return s
