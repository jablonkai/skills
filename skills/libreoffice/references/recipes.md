# Raw UNO recipes

For what the scripts don't cover, write a UNO snippet and run it inside the skill's
headless instance:

```bash
python3 scripts/lo_run.py --script my.py --arg '{"src": "/abs/in.xlsx", "dst": "/abs/out.xlsx"}'
```

The snippet runs inside `soffice` (Python 3.13 on LibreOffice 26.8) and has these names:

| Name | What |
|---|---|
| `ARGS` | the `--arg` JSON (use absolute paths) |
| `load(path, readonly=True, as_template=False, infilter=None, password=None)` | open hidden, macros off; `as_template=True` for an editable copy |
| `store(doc, dst, pdf=None, filter_name=None, filter_options=None)` | export by extension (filter picked per document kind, see [filters.md](filters.md)) |
| `props(dict)`, `filter_data(dict)`, `url(path)` | PropertyValue tuples, typed FilterData, file URLs |
| `desktop()`, `context()`, `XSCRIPTCONTEXT`, `uno` | the usual UNO entry points |
| `close(doc)`, `kind_of(doc)` | close; `writer`/`calc`/`impress`/`draw` |

Assign a JSON-serializable value to `RESULT` and it is printed. An exception is
reported with the snippet's file and line, and every document the snippet left open is
closed (soffice would otherwise never exit).

**Edit through `load(..., as_template=True)`, never `readonly=True`.** A read-only
document accepts value writes but silently drops formatting changes. A plain load
leaves a `.~lock.<name>#` file next to the user's file. Style names are the
programmatic English ones (`Text body`, `Heading 1`, `Standard` for the default page
style), not the names the UI shows.

Every recipe below was run as written against LibreOffice 26.8.0.3, and the outputs
were checked with openpyxl, python-docx, python-pptx or poppler.

## Calc: number format, bold header, chart, sheet protection

```python
# Format, protect and chart a sheet, then save as a new xlsx.
from com.sun.star.lang import Locale
from com.sun.star.awt import Rectangle
doc = load(ARGS["src"], as_template=True)  # editable copy; ReadOnly would drop formatting
sheet = doc.Sheets.getByName("Data")
fmts = doc.getNumberFormats()
loc = Locale("en", "US", "")
code = "#,##0.00"
key = fmts.queryKey(code, loc, False)
if key == -1:
    key = fmts.addNew(code, loc)
sheet.getCellRangeByName("C2:C100").NumberFormat = key
head = sheet.getCellRangeByName("A1:C1")
head.CharWeight = 150  # com.sun.star.awt.FontWeight.BOLD
head.CellBackColor = 0xDDEEFF
sheet.getColumns().getByIndex(0).OptimalWidth = True
charts = sheet.getCharts()
addr = sheet.getCellRangeByName("A1:B4").getRangeAddress()
charts.addNewByName("Units", Rectangle(5000, 1000, 12000, 7000), (addr,), True, True)
chart = charts.getByName("Units").getEmbeddedObject()
chart.setDiagram(chart.createInstance("com.sun.star.chart.BarDiagram"))
sheet.protect("secret")
store(doc, ARGS["dst"])
RESULT = {"format_key": key, "charts": list(charts.getElementNames()),
          "protected": sheet.isProtected()}
```

The xlsx gets `xl/charts/chart1.xml`, a `<sheetProtection>` element, the `#,##0.00`
format and a bold header. Freeze panes, zoom and the active sheet are **view** settings;
hidden documents have no real view, so `freezeAtPosition` does nothing there.

## Writer: build a report (styles, TOC, table, image)

```python
# Build a Writer document: margins, headings, body text, a table from rows, an image,
# a table of contents; save as docx and pdf.
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.awt import Size
doc = desktop().loadComponentFromURL("private:factory/swriter", "_blank", 0,
                                     props({"Hidden": True}))
page = doc.getStyleFamilies().getByName("PageStyles").getByName("Standard")
page.LeftMargin = page.RightMargin = 2000  # 1/100 mm
text = doc.getText()
cur = text.createTextCursor()

def para(s, style="Text body"):
    cur.ParaStyleName = style
    text.insertString(cur, s, False)
    text.insertControlCharacter(cur, PARAGRAPH_BREAK, False)

para(ARGS["title"], "Title")
toc = doc.createInstance("com.sun.star.text.ContentIndex")
toc.CreateFromOutline = True
text.insertTextContent(cur, toc, False)
text.insertControlCharacter(cur, PARAGRAPH_BREAK, False)
for sec in ARGS["sections"]:
    para(sec["heading"], "Heading 1")
    para(sec["body"])
rows = ARGS["table"]
table = doc.createInstance("com.sun.star.text.TextTable")
table.initialize(len(rows), len(rows[0]))
text.insertTextContent(cur, table, False)
table.setDataArray(tuple(tuple(str(c) for c in r) for r in rows))
img = doc.createInstance("com.sun.star.text.TextGraphicObject")
img.GraphicURL = url(ARGS["image"])  # linked by URL; storing to docx/pdf embeds it
img.Size = Size(6000, 3000)
text.insertTextContent(cur, img, False)
toc.update()
for dst in ARGS["out"]:
    store(doc, dst)
RESULT = {"pages": doc.getCurrentController().getPropertyValue("PageCount")}
```

`--arg '{"title": "Report", "sections": [{"heading": "Intro", "body": "…"}],
"table": [["Name", "Value"], ["A", 1]], "image": "/abs/logo.png", "out":
["/abs/report.docx", "/abs/report.pdf"]}'`. The TOC title follows the profile language
(`LO_LOCALE`, default en-US: "Table of Contents"); set `toc.Title` to override it.

## Impress: deck from an outline, with speaker notes

```python
# Build a deck from an outline: title slide, then title + bullets slides, with notes.
doc = desktop().loadComponentFromURL("private:factory/simpress", "_blank", 0,
                                     props({"Hidden": True}))
pages = doc.getDrawPages()
TITLE, TITLE_CONTENT = 0, 1  # AutoLayout: title slide, title + content
for i, s in enumerate(ARGS["slides"]):
    # a new presentation has one slide; insertNewByIndex(n) adds one after slide n
    page = pages.getByIndex(0) if i == 0 else pages.insertNewByIndex(pages.getCount() - 1)
    page.Layout = TITLE if i == 0 else TITLE_CONTENT
    shapes = [page.getByIndex(k) for k in range(page.getCount())]
    title = next(sh for sh in shapes if sh.getShapeType().endswith("TitleTextShape"))
    title.setString(s["title"])
    body = [sh for sh in shapes if sh.getShapeType().endswith(("OutlinerShape", "SubtitleShape"))]
    if body and s.get("bullets"):
        body[0].setString("\n".join(s["bullets"]))
    if s.get("notes"):
        notes = page.getNotesPage()
        for k in range(notes.getCount()):
            sh = notes.getByIndex(k)
            if sh.getShapeType().endswith("NotesShape"):
                sh.setString(s["notes"])
for dst in ARGS["out"]:
    store(doc, dst)
RESULT = {"slides": pages.getCount()}
```

`--arg '{"slides": [{"title": "Q3", "bullets": ["2026"]}, {"title": "Results",
"bullets": ["Revenue +12%"], "notes": "Stress growth"}], "out": ["/abs/deck.pptx"]}'`.
Each `\n` in a placeholder is one bullet. Shape types are
`com.sun.star.presentation.TitleTextShape`, `…SubtitleShape` (lower-case t),
`…OutlinerShape` and `…NotesShape`.

## Writer: accept tracked changes and remove comments

```python
# Accept (or reject) every tracked change and delete every comment, then save a copy.
doc = load(ARGS["src"], as_template=True)
frame = doc.getCurrentController().getFrame()
dispatcher = context().getServiceManager().createInstanceWithContext(
    "com.sun.star.frame.DispatchHelper", context())
before = doc.getRedlines().getCount()
cmd = ".uno:RejectAllTrackedChanges" if ARGS.get("reject") else ".uno:AcceptAllTrackedChanges"
dispatcher.executeDispatch(frame, cmd, "", 0, ())
doc.RecordChanges = False
fields = doc.getTextFields().createEnumeration()
comments = []
while fields.hasMoreElements():
    f = fields.nextElement()
    if f.supportsService("com.sun.star.text.TextField.Annotation"):
        comments.append(f)
for f in comments:
    f.dispose()
store(doc, ARGS["dst"])
RESULT = {"changes_before": before, "changes_after": doc.getRedlines().getCount(),
          "comments_removed": len(comments)}
```

Dispatcher commands (`.uno:…`) work on hidden documents through their frame. The saved
docx has no `<w:ins>`/`<w:del>` and no comments part.

## Writer: native mail merge with a registered CSV data source

`lo-merge.py` covers mail merge without any registration. Use this only when the output
must come from LibreOffice's own MailMerge service (for example a template whose
mail-merge fields name a data source).

```python
# Native mail merge: register a folder of CSV files as a data source (a "flat" text
# database, one table per file), then run the MailMerge service.
import os
dbctx = context().getServiceManager().createInstanceWithContext(
    "com.sun.star.sdb.DatabaseContext", context())
name = ARGS.get("source_name", "skill_csv")
ds = dbctx.createInstance()
ds.URL = "sdbc:flat:" + url(ARGS["csv_dir"])
ds.Info = props({"Extension": "csv", "HeaderLine": True, "FieldDelimiter": ",",
                 "StringDelimiter": '"', "CharSet": "UTF-8"})
odb = os.path.join(ARGS["out_dir"], name + ".odb")
ds.DatabaseDocument.storeAsURL(url(odb), ())
if dbctx.hasByName(name):
    dbctx.revokeObject(name)
dbctx.registerObject(name, ds)
mm = context().getServiceManager().createInstanceWithContext(
    "com.sun.star.text.MailMerge", context())
mm.DataSourceName = name
mm.CommandType = 0  # com.sun.star.sdb.CommandType.TABLE
mm.Command = ARGS["table"]  # the CSV file name without extension
mm.DocumentURL = url(ARGS["template"])
mm.OutputType = 2  # com.sun.star.text.MailMergeType.FILE
mm.OutputURL = url(ARGS["out_dir"])
mm.FileNamePrefix = ARGS.get("prefix", "letter")
mm.SaveAsSingleFile = ARGS.get("single", False)
mm.SaveFilter = "writer_pdf_Export"
mm.execute(())
dbctx.revokeObject(name)
RESULT = {"files": sorted(f for f in os.listdir(ARGS["out_dir"]) if f.endswith(".pdf"))}
```

The template's database fields must name the source (`DataBaseName` = `skill_csv`,
`DataTableName` = the CSV's stem). Output files are `<prefix>0.pdf`, `<prefix>1.pdf`, …
The `.odb` is written to `out_dir`, and the registration is removed again; it would
otherwise persist in the skill profile.
