# LibreOffice-side operations for the libreoffice skill. Runs INSIDE soffice as a
# Python macro (lo_run.py copies it into the skill profile and starts soffice with
# vnd.sun.star.script:lo_ops.py$main?language=Python&location=user). The request is
# the JSON file named by the LO_REQ environment variable:
#   {"op": NAME, "args": {...}, "result": PATH}
# and the result is written to PATH as {"ok": true, ...} or {"ok": false, "error": ...}.
#
# Documents are always loaded hidden with MacroExecutionMode NEVER and without link
# updates, so macros and external links inside input files never run. Sources are
# never stored back: Calc sources load read-only and Writer templates load AsTemplate
# (an untitled copy); every output goes through storeToURL.
import glob
import json
import os
import re
import traceback

import uno
from com.sun.star.beans import PropertyValue

NEVER_EXECUTE = 0  # com.sun.star.document.MacroExecMode.NEVER_EXECUTE
NO_UPDATE = 0  # com.sun.star.document.UpdateDocMode.NO_UPDATE

KIND_SERVICES = (
    ("writer", "com.sun.star.text.TextDocument"),
    ("calc", "com.sun.star.sheet.SpreadsheetDocument"),
    ("impress", "com.sun.star.presentation.PresentationDocument"),
    ("draw", "com.sun.star.drawing.DrawingDocument"),
    ("math", "com.sun.star.formula.FormulaProperties"),
)

# Export filter per document kind and output extension: (FilterName, FilterOptions).
EXPORT_FILTERS = {
    "writer": {
        "pdf": ("writer_pdf_Export", None),
        "odt": ("writer8", None),
        "docx": ("MS Word 2007 XML", None),
        "doc": ("MS Word 97", None),
        "rtf": ("Rich Text Format", None),
        "txt": ("Text (encoded)", "UTF8,LF"),
        "html": ("HTML (StarWriter)", None),
        "epub": ("EPUB", None),
        "fodt": ("OpenDocument Text Flat XML", None),
        "png": ("writer_png_Export", None),
        "jpg": ("writer_jpg_Export", None),
        "svg": ("writer_svg_Export", None),
    },
    "calc": {
        "pdf": ("calc_pdf_Export", None),
        "ods": ("calc8", None),
        "xlsx": ("Calc MS Excel 2007 XML", None),
        "xls": ("MS Excel 97", None),
        # comma, double quote, UTF-8, line 1, no column formats, language 1033 (en-US:
        # "." decimal — 0 would use the system locale, e.g. "1,5"), quoted as text off,
        # detect special numbers on, save as shown off (raw values), formulas off
        "csv": ("Text - txt - csv (StarCalc)", "44,34,76,1,,1033,false,true,false,false"),
        "html": ("HTML (StarCalc)", None),
        "fods": ("OpenDocument Spreadsheet Flat XML", None),
        "png": ("calc_png_Export", None),
        "svg": ("calc_svg_Export", None),
    },
    "impress": {
        "pdf": ("impress_pdf_Export", None),
        "odp": ("impress8", None),
        "pptx": ("Impress MS PowerPoint 2007 XML", None),
        "ppt": ("MS PowerPoint 97", None),
        "fodp": ("OpenDocument Presentation Flat XML", None),
        "html": ("impress_html_Export", None),
        "png": ("impress_png_Export", None),
        "jpg": ("impress_jpg_Export", None),
        "svg": ("impress_svg_Export", None),
    },
    "draw": {
        "pdf": ("draw_pdf_Export", None),
        "odg": ("draw8", None),
        "fodg": ("OpenDocument Drawing Flat XML", None),
        "png": ("draw_png_Export", None),
        "jpg": ("draw_jpg_Export", None),
        "svg": ("draw_svg_Export", None),
    },
    "math": {
        "pdf": ("math_pdf_Export", None),
        "odf": ("math8", None),
        "mml": ("MathML XML (Math)", None),
    },
}

# Calc error codes (com.sun.star.sheet cell getError()) -> the English error name.
CALC_ERRORS = {
    501: "Err:501 invalid character", 502: "Err:502 invalid argument", 503: "#NUM!",
    504: "Err:504 parameter list", 507: "Err:507 missing pair", 508: "Err:508 bracket",
    509: "Err:509 missing operator", 510: "Err:510 missing variable",
    511: "Err:511 missing variable", 512: "Err:512 formula overflow",
    513: "Err:513 string overflow", 514: "Err:514 internal overflow",
    516: "Err:516 internal syntax", 517: "Err:517 internal syntax",
    518: "Err:518 internal syntax", 519: "#VALUE!", 520: "Err:520 internal syntax",
    521: "Err:521 internal syntax", 522: "Err:522 circular reference",
    523: "Err:523 no convergence", 524: "#REF!", 525: "#NAME?",
    527: "Err:527 internal overflow", 532: "#DIV/0!", 533: "Err:533 nested arrays",
    538: "Err:538 matrix size", 539: "Err:539 unsupported inline array",
    540: "Err:540 external content disabled", 32767: "#N/A",
}

EMPTY, VALUE, TEXT, FORMULA = "EMPTY", "VALUE", "TEXT", "FORMULA"


# ------------------------------------------------------------------ helpers

def props(d):
    out = []
    for k, v in d.items():
        p = PropertyValue()
        p.Name = k
        p.Value = v
        out.append(p)
    return tuple(out)


def filter_data(d):
    """FilterData as the typed sequence the export filters expect."""
    return uno.Any("[]com.sun.star.beans.PropertyValue", props(d))


def url(path):
    return uno.systemPathToFileUrl(os.path.abspath(path))


def desktop():
    return XSCRIPTCONTEXT.getDesktop()  # noqa: F821 (injected by the script provider)


def context():
    return XSCRIPTCONTEXT.getComponentContext()  # noqa: F821


def load(path, readonly=True, as_template=False, infilter=None, password=None,
         filter_options=None):
    if not os.path.isfile(path):
        raise RuntimeError("not found: %s" % path)
    args = {"Hidden": True, "MacroExecutionMode": NEVER_EXECUTE,
            "UpdateDocMode": NO_UPDATE, "Silent": True}
    if as_template:
        args["AsTemplate"] = True
    elif readonly:
        args["ReadOnly"] = True
    if infilter:
        args["FilterName"] = infilter
    if filter_options:
        args["FilterOptions"] = filter_options
    if password is not None:
        args["Password"] = password
    try:
        doc = desktop().loadComponentFromURL(url(path), "_blank", 0, props(args))
    except Exception as e:
        raise RuntimeError("could not load %s: %s" % (path, getattr(e, "Message", e) or e))
    if doc is None:
        raise RuntimeError("could not load %s (unsupported, damaged or password-protected)"
                           % path)
    return doc


def close(doc):
    try:
        doc.close(True)
    except Exception:
        try:
            doc.dispose()
        except Exception:
            pass


def kind_of(doc):
    for kind, service in KIND_SERVICES:
        if doc.supportsService(service):
            return kind
    return "unknown"


def import_filter(doc):
    for p in doc.getArgs():
        if p.Name == "FilterName":
            return p.Value
    return None


def export_filter(kind, ext, override=None):
    ext = ext.lower().lstrip(".")
    if override:
        return override, None
    table = EXPORT_FILTERS.get(kind, {})
    if ext not in table:
        raise RuntimeError("cannot export a %s document to .%s (supported: %s)"
                           % (kind, ext, ", ".join(sorted(table))))
    return table[ext]


def store(doc, dst, kind=None, pdf=None, filter_name=None, filter_options=None,
          filter_data_extra=None):
    kind = kind or kind_of(doc)
    ext = os.path.splitext(dst)[1]
    name, options = export_filter(kind, ext, filter_name)
    args = {"FilterName": name, "Overwrite": True}
    if filter_options or options:
        args["FilterOptions"] = filter_options or options
    data = dict(filter_data_extra or {})
    if ext.lower() == ".pdf" and pdf:
        data.update(pdf)
    if data:
        args["FilterData"] = filter_data(data)
    d = os.path.dirname(os.path.abspath(dst))
    os.makedirs(d, exist_ok=True)
    doc.storeToURL(url(dst), props(args))
    if not os.path.exists(dst) or os.path.getsize(dst) == 0:
        # CSV with the sheet token -1 writes <stem>-<Sheet>.csv per sheet instead
        stem, e = os.path.splitext(dst)
        if not glob.glob(glob.escape(stem) + "-*" + e):
            raise RuntimeError("export wrote nothing: %s" % dst)
    return name


def update_all(doc):
    """Refresh fields and rebuild indexes (TOC etc.) in a Writer document."""
    try:
        doc.TextFields.refresh()
    except Exception:
        pass
    try:
        idx = doc.getDocumentIndexes()
        for i in range(idx.getCount()):
            idx.getByIndex(i).update()
    except Exception:
        pass
    try:
        doc.refresh()
    except Exception:
        pass


def page_count(doc, kind):
    try:
        if kind == "writer":
            return doc.getCurrentController().getPropertyValue("PageCount")
        if kind in ("impress", "draw"):
            return doc.getDrawPages().getCount()
    except Exception:
        return None
    return None


# ------------------------------------------------------------------ convert

def op_convert(a):
    results = []
    for job in a["jobs"]:
        r = {"src": job["src"], "dst": job["dst"]}
        doc = None
        try:
            doc = load(job["src"], infilter=job.get("infilter"),
                       password=job.get("password"),
                       filter_options=job.get("infilter_options"))
            kind = kind_of(doc)
            r["kind"] = kind
            r["import_filter"] = import_filter(doc)
            if kind == "writer" and job.get("update_indexes"):
                update_all(doc)
            r["export_filter"] = store(doc, job["dst"], kind, pdf=job.get("pdf"),
                                       filter_name=job.get("filter"),
                                       filter_options=job.get("options"))
            r["pages"] = page_count(doc, kind)
            r["ok"] = True
        except Exception as e:
            r["ok"] = False
            r["error"] = str(e)
        finally:
            if doc is not None:
                close(doc)
        results.append(r)
    return {"results": results}


# ------------------------------------------------------------------ calc

def sheet_of(doc, name):
    sheets = doc.getSheets()
    if name is None or name == "":
        return sheets.getByIndex(0)
    if isinstance(name, int):
        return sheets.getByIndex(name)
    if sheets.hasByName(name):
        return sheets.getByName(name)
    raise RuntimeError("no sheet %r (sheets: %s)" % (name, ", ".join(sheets.getElementNames())))


def cell_type(cell):
    return cell.getType().value


def cell_info(cell, with_formula=True):
    """{"v": value, "t": text shown, "f": formula, "e": error} for one cell."""
    t = cell_type(cell)
    out = {}
    if t == EMPTY:
        out["v"] = None
        return out
    if t == FORMULA:
        if with_formula:
            out["f"] = cell.getFormula()
        err = cell.getError()
        if err:
            out["e"] = CALC_ERRORS.get(err, "Err:%d" % err)
            out["v"] = None
            return out
        # FormulaResultType2: 1 VALUE, 2 STRING, 4 ERROR
        rtype = cell.getPropertyValue("FormulaResultType2")
        out["v"] = cell.getString() if rtype == 2 else cell.getValue()
    elif t == VALUE:
        out["v"] = cell.getValue()
    else:
        out["v"] = cell.getString()
    shown = cell.getString()
    if shown != out.get("v") and not (isinstance(out["v"], float) and shown == repr(out["v"])):
        out["t"] = shown
    return out


def parse_ref(doc, ref, default_sheet=None):
    """'Sheet.A1:B2', 'Sheet!A1', "'My sheet'.A1", 'A1' or a named range -> range obj."""
    named = doc.NamedRanges
    if named.hasByName(ref):
        cr = named.getByName(ref).getReferredCells()
        if cr is None:
            raise RuntimeError("named range %r does not refer to cells" % ref)
        return cr
    m = re.match(r"^(?:'([^']+)'|([^.!']+))[.!](\$?[A-Za-z]+\$?\d+(?::\$?[A-Za-z]+\$?\d+)?)$", ref)
    if m:
        sheet = sheet_of(doc, m.group(1) or m.group(2))
        return sheet.getCellRangeByName(m.group(3).replace("$", ""))
    return sheet_of(doc, default_sheet).getCellRangeByName(ref.replace("$", ""))


def range_name(rng):
    addr = rng.getRangeAddress()
    sheet = rng.getSpreadsheet().getName()
    a = col_name(addr.StartColumn) + str(addr.StartRow + 1)
    b = col_name(addr.EndColumn) + str(addr.EndRow + 1)
    return "%s.%s" % (sheet, a if a == b else a + ":" + b)


def col_name(i):
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def read_range(rng, with_formula=True, limit=20000):
    addr = rng.getRangeAddress()
    rows = addr.EndRow - addr.StartRow + 1
    cols = addr.EndColumn - addr.StartColumn + 1
    if rows * cols > limit:
        raise RuntimeError("range %s has %d cells (limit %d)" % (range_name(rng), rows * cols, limit))
    grid = []
    for r in range(rows):
        grid.append([cell_info(rng.getCellByPosition(c, r), with_formula) for c in range(cols)])
    return {"range": range_name(rng), "cells": grid}


def used_range(sheet):
    cur = sheet.createCursor()
    cur.gotoStartOfUsedArea(False)
    cur.gotoEndOfUsedArea(True)
    return cur


def formula_errors(doc, limit=100):
    """[(address, error)] for every formula cell that evaluates to an error."""
    from com.sun.star.sheet.CellFlags import FORMULA as F
    out = []
    count = 0
    sheets = doc.getSheets()
    for i in range(sheets.getCount()):
        sheet = sheets.getByIndex(i)
        ranges = sheet.queryContentCells(F)
        cells = ranges.getCells().createEnumeration()
        while cells.hasMoreElements():
            cell = cells.nextElement()
            count += 1
            err = cell.getError()
            if err and len(out) < limit:
                a = cell.getCellAddress()
                out.append({"cell": "%s.%s%d" % (sheet.getName(), col_name(a.Column), a.Row + 1),
                            "formula": cell.getFormula(),
                            "error": CALC_ERRORS.get(err, "Err:%d" % err)})
    return out, count


class FormulaWriter:
    """Sets formulas in Excel syntax (`,` separators, `Sheet!A1` references) or in
    LibreOffice's native syntax (`;`, `$Sheet.A1`). cell.setFormula() only understands
    the native one, so Excel formulas are parsed to tokens with the OOXML op-code map."""

    def __init__(self, doc, syntax="excel"):
        self.doc, self.syntax, self.parser = doc, syntax, None

    def set(self, cell, formula, syntax=None):
        if (syntax or self.syntax) == "native":
            cell.setFormula(formula)
            return
        if self.parser is None:
            from com.sun.star.sheet.FormulaLanguage import OOXML
            from com.sun.star.sheet.FormulaMapGroup import ALL_EXCEPT_SPECIAL, SPECIAL
            mapper = self.doc.createInstance("com.sun.star.sheet.FormulaOpCodeMapper")
            self.parser = self.doc.createInstance("com.sun.star.sheet.FormulaParser")
            self.parser.CompileEnglish = True
            self.parser.FormulaConvention = 3  # AddressConvention.XL_OOX
            self.parser.OpCodeMap = (mapper.getAvailableMappings(OOXML, SPECIAL)
                                     + mapper.getAvailableMappings(OOXML, ALL_EXCEPT_SPECIAL))
        cell.setTokens(self.parser.parseFormula(formula, cell.getCellAddress()))


def write_cell(cell, v, fw=None):
    if v is None:
        cell.setString("")
        cell.clearContents(1 | 2 | 4 | 16)  # VALUE, DATETIME, STRING, FORMULA
    elif isinstance(v, dict) and "formula" in v:
        if fw is None:
            raise RuntimeError("formulas are not allowed in this write")
        fw.set(cell, v["formula"], v.get("syntax"))
    elif isinstance(v, bool):
        cell.setValue(1 if v else 0)
    elif isinstance(v, (int, float)):
        cell.setValue(v)
    else:
        # setString never re-parses: "007", "1/2", "=x" stay text
        cell.setString(str(v))


def op_calc_fill(a):
    # AsTemplate: an editable untitled copy. A ReadOnly load would silently drop
    # formatting changes, and a normal load puts a .~lock file next to the source.
    doc = load(a["src"], as_template=True)
    try:
        if kind_of(doc) != "calc":
            raise RuntimeError("%s is not a spreadsheet" % a["src"])
        for c in a.get("clear", []):
            parse_ref(doc, c).clearContents(1 | 2 | 4 | 16)
        fw = FormulaWriter(doc, a.get("syntax", "excel"))
        written = []
        for w in a.get("writes", []):
            start = parse_ref(doc, w["at"], w.get("sheet"))
            sa = start.getRangeAddress()
            sheet = start.getSpreadsheet()
            rows = w["rows"]
            for r, row in enumerate(rows):
                for c, v in enumerate(row):
                    write_cell(sheet.getCellByPosition(sa.StartColumn + c, sa.StartRow + r), v, fw)
            width = max((len(r) for r in rows), default=0)
            if rows and width:
                written.append(range_name(sheet.getCellRangeByPosition(
                    sa.StartColumn, sa.StartRow, sa.StartColumn + width - 1,
                    sa.StartRow + len(rows) - 1)))
        for s in a.get("sets", []):
            rng = parse_ref(doc, s["cell"], s.get("sheet"))
            write_cell(rng.getCellByPosition(0, 0), s["value"], fw)
        doc.calculateAll()
        errors, nformulas = formula_errors(doc)
        reads = [read_range(parse_ref(doc, r)) for r in a.get("read", [])]
        outputs = []
        for o in a.get("outputs", []):
            outputs.append({"dst": o["dst"], "filter": store(
                doc, o["dst"], "calc", pdf=o.get("pdf"), filter_name=o.get("filter"),
                filter_options=o.get("options"))})
        return {"written": written, "formulas": nformulas, "errors": errors,
                "reads": reads, "outputs": outputs}
    finally:
        close(doc)


def op_calc_read(a):
    doc = load(a["src"], readonly=True, password=a.get("password"))
    try:
        if kind_of(doc) != "calc":
            raise RuntimeError("%s is not a spreadsheet" % a["src"])
        if a.get("recalc", True):
            doc.calculateAll()
        sheets = doc.getSheets()
        info = []
        for i in range(sheets.getCount()):
            sh = sheets.getByIndex(i)
            used = used_range(sh)
            entry = {"name": sh.getName(), "used": range_name(used),
                     "visible": bool(sh.getPropertyValue("IsVisible"))}
            if a.get("grid") and (not a.get("sheets") or sh.getName() in a["sheets"]):
                entry["grid"] = read_range(used, limit=a.get("limit", 20000))
            info.append(entry)
        errors, nformulas = formula_errors(doc)
        reads = [read_range(parse_ref(doc, r)) for r in a.get("read", [])]
        return {"kind": "calc", "import_filter": import_filter(doc), "sheets": info,
                "named_ranges": list(doc.NamedRanges.getElementNames()),
                "formulas": nformulas, "errors": errors, "reads": reads}
    finally:
        close(doc)


# ------------------------------------------------------------------ writer

def placeholder_regex(open_, close_):
    return re.escape(open_) + r"[^\n]*?" + re.escape(close_)


def find_placeholders(doc, open_, close_):
    sd = doc.createSearchDescriptor()
    sd.SearchRegularExpression = True
    sd.SearchString = placeholder_regex(open_, close_)
    # findFirst/findNext, not findAll: findAll crashes soffice (SIGABRT in
    # SwXTextRanges::Create) when nothing matches (26.8).
    names = []
    found = doc.findFirst(sd)
    while found is not None:
        s = found.getString()
        key = s[len(open_):len(s) - len(close_)]
        if key not in names:
            names.append(key)
        found = doc.findNext(found.getEnd(), sd)
    return names


USER_MASTER = "com.sun.star.text.fieldmaster.User."


def field_inventory(doc, open_="{{", close_="}}"):
    masters = [n[len(USER_MASTER):] for n in doc.getTextFieldMasters().getElementNames()
               if n.startswith(USER_MASTER)]
    db_cols, inputs = [], []
    en = doc.getTextFields().createEnumeration()
    while en.hasMoreElements():
        f = en.nextElement()
        if f.supportsService("com.sun.star.text.TextField.Database"):
            col = f.getTextFieldMaster().getPropertyValue("DataColumnName")
            if col not in db_cols:
                db_cols.append(col)
        elif f.supportsService("com.sun.star.text.TextField.Input"):
            hint = f.getPropertyValue("Hint")
            if hint not in inputs:
                inputs.append(hint)
    return {"placeholders": find_placeholders(doc, open_, close_),
            "user_fields": masters,
            "bookmarks": list(doc.getBookmarks().getElementNames()),
            "database_fields": db_cols, "input_fields": inputs}


def op_writer_fields(a):
    doc = load(a["src"], readonly=True)
    try:
        if kind_of(doc) != "writer":
            raise RuntimeError("%s is not a text document" % a["src"])
        inv = field_inventory(doc, a.get("open", "{{"), a.get("close", "}}"))
        inv["header_footer_targets"] = header_footer_varies(doc, a.get("open", "{{"))
        inv["pages"] = page_count(doc, "writer")
        inv["import_filter"] = import_filter(doc)
        return inv
    finally:
        close(doc)


def fill_writer(doc, rec, open_, close_):
    """Fill one record into doc; returns the list of names that were used."""
    used = []
    for key, val in rec.items():
        val = "" if val is None else str(val)
        rd = doc.createReplaceDescriptor()
        rd.SearchString = open_ + key + close_
        rd.ReplaceString = val
        rd.SearchCaseSensitive = True
        rd.SearchRegularExpression = False
        if doc.replaceAll(rd):
            used.append(key)
    masters = doc.getTextFieldMasters()
    for key, val in rec.items():
        name = USER_MASTER + key
        if masters.hasByName(name):
            masters.getByName(name).setPropertyValue("Content", "" if val is None else str(val))
            used.append(key)
    marks = doc.getBookmarks()
    for key, val in rec.items():
        if marks.hasByName(key):
            marks.getByName(key).getAnchor().setString("" if val is None else str(val))
            used.append(key)
    # Mail-merge (database) fields and input fields: replace by the record's text.
    fields = []
    en = doc.getTextFields().createEnumeration()
    while en.hasMoreElements():
        fields.append(en.nextElement())
    for f in fields:
        key = None
        if f.supportsService("com.sun.star.text.TextField.Database"):
            key = f.getTextFieldMaster().getPropertyValue("DataColumnName")
        elif f.supportsService("com.sun.star.text.TextField.Input"):
            key = f.getPropertyValue("Hint")
        if key is not None and key in rec:
            anchor = f.getAnchor()
            anchor.getText().insertString(anchor, "" if rec[key] is None else str(rec[key]), True)
            used.append(key)
    update_all(doc)
    return sorted(set(used))


def append_document(base, path):
    """Append the document at path to base, starting on a new page."""
    from com.sun.star.style.BreakType import PAGE_BEFORE
    from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
    text = base.getText()
    cur = text.createTextCursor()
    cur.gotoEnd(False)
    text.insertControlCharacter(cur, PARAGRAPH_BREAK, False)
    cur.setPropertyValue("BreakType", PAGE_BEFORE)
    cur.insertDocumentFromURL(url(path), ())


HF_TEXTS = ("HeaderText", "HeaderTextFirst", "HeaderTextLeft",
            "FooterText", "FooterTextFirst", "FooterTextLeft")


def header_footer_varies(doc, open_):
    """True when a header or footer holds a placeholder, a field or a bookmark. Those
    belong to the page style, so every record in one concatenated document would show
    the first record's header."""
    styles = doc.getStyleFamilies().getByName("PageStyles")
    for i in range(styles.getCount()):
        st = styles.getByIndex(i)
        if not st.isInUse():
            continue
        for attr in HF_TEXTS:
            try:
                text = st.getPropertyValue(attr)
            except Exception:
                continue
            if text is None:
                continue
            if open_ in text.getString():
                return True
            paras = text.createEnumeration()
            while paras.hasMoreElements():
                para = paras.nextElement()
                if not para.supportsService("com.sun.star.text.Paragraph"):
                    continue
                portions = para.createEnumeration()
                while portions.hasMoreElements():
                    kind = portions.nextElement().getPropertyValue("TextPortionType")
                    if kind in ("TextField", "Bookmark"):
                        return True
    return False


def flatten_user_fields(doc):
    """Replace user fields by their current text. User fields are document-global, so in
    a concatenated document every record would show the last record's value."""
    fields = []
    en = doc.getTextFields().createEnumeration()
    while en.hasMoreElements():
        f = en.nextElement()
        if f.supportsService("com.sun.star.text.TextField.User"):
            fields.append(f)
    for f in fields:
        anchor = f.getAnchor()
        anchor.getText().insertString(anchor, f.getPresentation(False), True)


def op_writer_fill(a):
    open_, close_ = a.get("open", "{{"), a.get("close", "}}")
    strict = a.get("strict", True)
    results, parts = [], []
    tmp = a.get("tmp_dir")
    pdf_parts = None
    for i, rec in enumerate(a["records"]):
        r = {"index": i}
        doc = load(a["template"], as_template=True)
        try:
            if kind_of(doc) != "writer":
                raise RuntimeError("%s is not a text document" % a["template"])
            if pdf_parts is None:
                pdf_parts = bool(a.get("combined")) and header_footer_varies(doc, open_)
            r["used"] = fill_writer(doc, rec, open_, close_)
            left = find_placeholders(doc, open_, close_)
            if left:
                r["unfilled"] = left
                if strict:
                    raise RuntimeError("record %d leaves placeholders unfilled: %s"
                                       % (i + 1, ", ".join(left)))
            r["outputs"] = []
            for dst in rec_outputs(a, i):
                store(doc, dst, "writer", pdf=a.get("pdf"))
                r["outputs"].append(dst)
            if a.get("combined"):
                if pdf_parts:
                    part = os.path.join(tmp, "part-%04d.pdf" % i)
                    store(doc, part, "writer", pdf=a.get("pdf"))
                else:
                    flatten_user_fields(doc)
                    part = os.path.join(tmp, "part-%04d.odt" % i)
                    store(doc, part, "writer")
                parts.append(part)
            r["pages"] = page_count(doc, "writer")
        finally:
            close(doc)
        results.append(r)
    if not (a.get("combined") and parts):
        return {"records": results}
    if pdf_parts:
        # The driver joins these (pdfunite): a per-record header can't survive
        # concatenation into one Writer document.
        return {"records": results, "pdf_parts": parts}
    base = load(parts[0], as_template=True)
    try:
        for p in parts[1:]:
            append_document(base, p)
        update_all(base)
        combined = []
        for dst in a["combined"]:
            store(base, dst, "writer", pdf=a.get("pdf"))
            combined.append(dst)
        pages = page_count(base, "writer")
    finally:
        close(base)
    return {"records": results, "combined": combined, "combined_pages": pages}


def rec_outputs(a, i):
    outs = a.get("outputs") or []
    return outs[i] if i < len(outs) else []


# ------------------------------------------------------------------ pages

def op_export_pages(a):
    doc = load(a["src"], readonly=True, password=a.get("password"))
    try:
        kind = kind_of(doc)
        if kind not in ("impress", "draw"):
            raise RuntimeError("per-page image export needs an Impress or Draw document; "
                               "this is %s — convert it to PDF and rasterize that" % kind)
        fmt = a.get("format", "png").lower()
        media = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                 "svg": "image/svg+xml", "gif": "image/gif", "bmp": "image/bmp",
                 "tif": "image/tiff", "tiff": "image/tiff", "webp": "image/webp"}
        if fmt not in media:
            raise RuntimeError("unsupported page image format %s (use %s)"
                               % (fmt, ", ".join(sorted(media))))
        pages = doc.getDrawPages()
        n = pages.getCount()
        wanted = a.get("pages") or list(range(1, n + 1))
        bad = [p for p in wanted if p < 1 or p > n]
        if bad:
            raise RuntimeError("no page %s (document has %d)" % (bad[0], n))
        gf = context().getServiceManager().createInstanceWithContext(
            "com.sun.star.drawing.GraphicExportFilter", context())
        files = []
        for p in wanted:
            page = pages.getByIndex(p - 1)
            if kind == "impress" and not a.get("include_hidden", False):
                try:
                    if not page.getPropertyValue("Visible"):
                        continue
                except Exception:
                    pass
            data = {}
            w, h = a.get("width"), a.get("height")
            if w or h:
                pw, ph = page.getPropertyValue("Width"), page.getPropertyValue("Height")
                if w and not h:
                    h = round(w * ph / pw)
                elif h and not w:
                    w = round(h * pw / ph)
                data = {"PixelWidth": int(w), "PixelHeight": int(h)}
            if fmt in ("jpg", "jpeg") and a.get("quality"):
                data["Quality"] = int(a["quality"])
            dst = os.path.join(a["out_dir"], "%s%0*d.%s" % (a.get("prefix", "page-"),
                                                           len(str(n)), p, fmt))
            os.makedirs(a["out_dir"], exist_ok=True)
            gf.setSourceDocument(page)
            fprops = {"URL": url(dst), "MediaType": media[fmt]}
            if data:
                fprops["FilterData"] = filter_data(data)
            gf.filter(props(fprops))
            if not os.path.exists(dst):
                raise RuntimeError("page %d export wrote nothing" % p)
            name = ""
            try:
                name = page.getName()
            except Exception:
                pass
            files.append({"page": p, "name": name, "file": dst})
        return {"kind": kind, "pages": n, "files": files}
    finally:
        close(doc)


# ------------------------------------------------------------------ inspect

def op_inspect(a):
    doc = load(a["src"], readonly=True, password=a.get("password"),
               infilter=a.get("infilter"))
    try:
        kind = kind_of(doc)
        out = {"kind": kind, "import_filter": import_filter(doc),
               "pages": page_count(doc, kind)}
        dp = doc.getDocumentProperties()
        out["title"] = dp.Title
        if kind == "writer":
            if a.get("text"):
                out["text"] = doc.getText().getString()
            out["fields"] = field_inventory(doc)
            out["tables"] = list(doc.getTextTables().getElementNames())
        elif kind == "calc":
            out["sheets"] = list(doc.getSheets().getElementNames())
        elif kind in ("impress", "draw"):
            pages = doc.getDrawPages()
            out["page_names"] = [pages.getByIndex(i).getName() for i in range(pages.getCount())]
        return out
    finally:
        close(doc)


# ------------------------------------------------------------------ script

def op_script(a):
    """Run an agent-written UNO snippet (references/recipes.md). The file is executed
    with these names defined: XSCRIPTCONTEXT, ARGS (the --arg JSON), load, store,
    props, filter_data, url, close, kind_of, desktop, context. Whatever it assigns to
    RESULT is returned (must be JSON-serializable)."""
    with open(a["path"], encoding="utf-8") as f:
        code = f.read()
    env = {"__name__": "lo_script", "XSCRIPTCONTEXT": XSCRIPTCONTEXT,  # noqa: F821
           "ARGS": a.get("args") or {}, "load": load, "store": store, "props": props,
           "filter_data": filter_data, "url": url, "close": close, "kind_of": kind_of,
           "desktop": desktop, "context": context, "uno": uno, "RESULT": None}
    exec(compile(code, a["path"], "exec"), env)
    return {"result": env.get("RESULT")}


OPS = {
    "script": op_script,
    "convert": op_convert,
    "calc_fill": op_calc_fill,
    "calc_read": op_calc_read,
    "writer_fields": op_writer_fields,
    "writer_fill": op_writer_fill,
    "export_pages": op_export_pages,
    "inspect": op_inspect,
}


def main(*_):
    req_path = os.environ.get("LO_REQ")
    if not req_path:
        return
    with open(req_path, encoding="utf-8") as f:
        req = json.load(f)
    try:
        out = OPS[req["op"]](req.get("args") or {})
        out["ok"] = True
    except Exception as e:
        where = traceback.extract_tb(e.__traceback__)[-1]
        out = {"ok": False, "error": "%s: %s (%s:%d)" % (
            type(e).__name__, str(e).strip() or "no message",
            os.path.basename(where.filename), where.lineno),
            "trace": traceback.format_exc()}
    # soffice exits after the macro only when no document is open; close whatever an
    # operation or a failing script left behind (this instance runs on the skill's
    # private profile, so every component is ours).
    try:
        comps = desktop().getComponents().createEnumeration()
        left = []
        while comps.hasMoreElements():
            left.append(comps.nextElement())
        for c in left:
            close(c)
    except Exception:
        pass
    fd = os.open(req["result"], os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)


g_exportedScripts = (main,)
