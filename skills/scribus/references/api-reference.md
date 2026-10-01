# Scribus 1.6 scripter API — curated by task

The `scribus` module exists only inside Scribus. It has 558 public names in 1.6.6, and
this page covers the ones layout jobs need. The authoritative text is each function's
docstring. To dump them all, run a job that writes `help()`-style output to a file
(`print()` is lost):

```python
import scribus
with open("/tmp/scribus-api.txt", "w") as fh:
    for n in sorted(dir(scribus)):
        fh.write("### %s\n%s\n\n" % (n, getattr(scribus, n).__doc__ or ""))
```

Conventions:

- Positions and sizes are in the **document unit** (the helpers set mm).
- Font sizes, leading and line widths are always **pt**.
- `name` is the frame name. Omit it to act on the current selection; in a headless job,
  always pass it.
- Pages are **1-based** for `gotoPage`, `newPage`, `applyMasterPage`, `getPageNSize` and
  `getMasterPage`, and **0-based** for `getAllObjects(page=)`.

## Contents
1. Document
2. Pages and master pages
3. Frames and shapes
4. Text and threading
5. Styles
6. Colours
7. Images
8. Layers
9. Query and checks
10. Exceptions

## 1. Document

| Call | Notes |
|---|---|
| `newDocument((w, h), (l, r, t, b), PORTRAIT, firstPageNumber, UNIT_MILLIMETERS, PAGE_1, firstPageOrder, numPages)` | Size and margins are in the given unit. `PAPER_A4` etc. are **points**; `PAPER_A4_MM`, `PAPER_A5_MM`… exist. `PAGE_2` = facing pages, with `firstPageOrder` 1 = start on a right page. |
| `openDoc(path)` | Fonts the doc uses that are missing get substituted silently. |
| `saveDocAs(path)` | Use this, not `saveDoc()`, which can open a dialog for an unsaved doc. |
| `closeDoc()` | Closes without prompting. Changes the working directory to `~/Documents`. |
| `haveDoc()` | 0/1 |
| `setUnit(UNIT_MILLIMETERS)` / `getUnit()` | Do this after `openDoc`, because a saved doc keeps its own unit. |
| `setBleeds(l, r, t, b)` / `getBleeds()` | Document bleeds, in the doc unit. |
| `setInfo(author, title, description)` | Document metadata; the 2nd value becomes the PDF Title. `getInfo()` returns `()` on 1.6.6. |
| `setRedraw(False)` | Speeds up big jobs in the GUI; it makes no difference headless. |

## 2. Pages and master pages

| Call | Notes |
|---|---|
| `pageCount()`, `currentPage()` | |
| `gotoPage(n)` | Sets the page that `create*` calls target. **Never call it while editing a master.** |
| `newPage(-1 [, "Master"])` | Appends a page; `n` inserts it before page n. |
| `deletePage(n)` | |
| `getPageNSize(n)` → (w, h) | |
| `getPageNMargins(n)` → (**top, left, right, bottom**) | The order differs from `newDocument`'s (l, r, t, b). |
| `getPageType()` | 0 left, 1 middle, 2 right (facing docs) |
| `createMasterPage(name)`, `editMasterPage(name)`, `closeMasterPage()` | Objects created between edit and close belong to the master. |
| `applyMasterPage(name, n)`, `getMasterPage(n)`, `masterPageNames()` | The default master is named in the **UI language** ("Normal", "Normál"…). |
| `importPage(file, (pages,), create=1, importwhere=2)` | Copies pages in from another `.sla`. |

Page numbering text: insert the page-number special character with
`insertText(chr(0x1E), -1, frame)` in a master frame. `chr(0x1E)` is Scribus's
page-number marker, and it renders as the current page number.

## 3. Frames and shapes

| Call | Notes |
|---|---|
| `createText(x, y, w, h [, name])` | Returns the name. Raises `NameExistsError` on a duplicate. |
| `createImage(x, y, w, h [, name])` | |
| `createRect`, `createEllipse`, `createLine(x1, y1, x2, y2)`, `createPolygon([x1, y1, …])` | |
| `moveObject(dx, dy, name)`, `moveObjectAbs(x, y, name)`, `sizeObject(w, h, name)`, `rotateObject(deg, name)` | |
| `setFillColor(color, name)`, `setLineColor`, `setLineWidth(pt, name)` | Use `"None"` for no fill or no line. |
| `setFillTransparency(0..1, name)` | 0 = opaque. Fine in PDF/X-4, but flattened or forbidden in X-1a/X-3. |
| `setCornerRadius(pt, name)` | |
| `groupObjects([names])`, `lockObject(name)` | |
| `deleteObject(name)`, `objectExists(name)` | |
| `setTextDistances(l, r, t, b, name)` | Inner padding of a text frame, in the doc unit. |
| `setColumns(n, name)`, `setColumnGap(gap, name)` | Multi-column text frames. |
| `setTextVerticalAlignment(ALIGNV_TOP/CENTERED/BOTTOM, name)` | |

## 4. Text and threading

| Call | Notes |
|---|---|
| `setText(str, name)` | Replaces the story. `\r` (or `\n`) starts a new paragraph. Takes Python `str` (UTF-8 is fine). |
| `insertText(str, pos, name)` | `pos=-1` appends. The layout is not updated, so call `layoutText`. |
| `getAllText(name)` / `getFrameText(name)` | The whole chain, or only the visible part of this frame. |
| `getTextLength(name)`, `getTextLines(name)` | `getTextLines` needs an up-to-date layout. |
| `selectText(start, count, name)` | Later formatting calls apply to the selection. `count=0` clears it. |
| `setFont(font, name)`, `setFontSize(pt, name)`, `setLineSpacing(pt, name)`, `setTextColor`, `setTextAlignment(ALIGN_*, name)` | These are local formatting on the selection (or the whole frame). Prefer styles. |
| `linkTextFrames(a, b)`, `unlinkTextFrames(a)` | `b` must be empty. |
| `getNextLinkedFrame(name)` / `getPrevLinkedFrame(name)` | |
| `textOverflows(name [, nolinks])` → 0/1 | Without `nolinks` it checks the whole chain. |
| `layoutText(name)`, `layoutTextChain(name)` | Call before reading overflow or line counts. |
| `hyphenateText(name)` / `dehyphenateText(name)` | Uses the language of the text's style. |

## 5. Styles

```python
scribus.createCharStyle(name="Body_c", font="Georgia Regular", fontsize=10,
                        fillcolor="Black", features="inherit")   # bold,italic,smallcaps,…
scribus.createParagraphStyle(name="Body", linespacingmode=0, linespacing=13,
                             alignment=3, gapbefore=0, gapafter=4,
                             firstindent=0, charstyle="Body_c",
                             hasdropcap=0, tabs=[(50, 0)])
scribus.setParagraphStyle("Body", frame)        # whole frame, or the selected range
scribus.setCharacterStyle("Emph", frame)        # selected range
scribus.getParagraphStyles(), scribus.getCharStyles()
```

- `linespacingmode`: 0 is fixed (the `linespacing` pt), 1 is automatic (follows the font
  size), 2 is the baseline grid.
- `alignment`: 0 left, 1 centre, 2 right, 3 justify, 4 forced.
- Gaps and indents are in **pt**. `L.para_style` converts mm for you.
- Font names are "Family Style" exactly as `getFontNames()` lists them: "Arial Bold",
  "Helvetica Neue Regular", "Georgia Italic". Check them with `L.font()` or
  `L.find_fonts("garamond")`.

## 6. Colours

| Call | Notes |
|---|---|
| `defineColorCMYK(name, c, m, y, k)` | Components are **0–255**. `L.cmyk()` takes percentages. |
| `defineColorRGB(name, r, g, b)` | 0–255 |
| `getColorNames()` | The defaults include Black, White, Cyan, Magenta, Yellow, Registration and None. |
| `setSpotColor(name, True)` | Marks a colour as a spot (Pantone-style) separation. |

## 7. Images

| Call | Notes |
|---|---|
| `loadImage(path, name)` | **No error for a missing file.** Check `getImageColorSpace(name) >= 0` afterwards (−1 = nothing loaded). |
| `setScaleImageToFrame(True, True, name)` | Fit proportionally, so the picture is letterboxed inside the frame. |
| `setImageScale(sx, sy, name)`, `setImageOffset(dx, dy, name)` | For a crop/fill look: scale up and offset. Scale is relative to the image's ppi. |
| `getImageFile(name)`, `getImageScale(name)` | |
| `setImageGrayscale(name)`, `setImageBrightness(n, name)` | Non-destructive effects. |

**Fill the frame (cover)**: `L.image_box(..., fit="cover")`. Under the hood:
`setScaleImageToFrame(True, False)` (non-proportional) gives `sx, sy`; the natural size is
`w/sx × h/sy`. Then `setScaleImageToFrame(False, False)`, `setImageScale(k, k)` with
`k = max(sx, sy)`, and centre it with `setImageOffset` — **in points**, not the doc unit.

## 8. Layers

`createLayer(name)`, `setActiveLayer(name)`, `setLayerPrintable(name, False)` (for a
guides layer), `setLayerVisible`, `sendToLayer(layer, name)`, `getLayers()`.

## 9. Query and checks

- `getAllObjects(page=n-1)`: all items on page n. The **first positional argument is the
  item type** (`ITEMTYPE_TEXTFRAME` = 4, `ITEMTYPE_IMAGEFRAME` = 2), so always use the keyword.
- `getObjectType(name)`: `'TextFrame'`, `'ImageFrame'`, `'Polygon'`, `'Line'`, `'Group'`…
- `getPosition(name)`, `getSize(name)`: doc unit.
- `getFontNames()`, `getXFontNames()`: installed fonts (882 on a stock macOS).
- `L.doc_summary()`: per page size, master and frames, plus all overflow and missing
  images. The runner always calls it.

## 10. Exceptions

`ScribusException` is the base, with `NoDocOpenError`, `NoValidObjectError` (unknown
frame name), `NameExistsError`, `WrongFrameTypeError` and `NotFoundError`. Standard
`ValueError` and `IndexError` are raised for bad arguments and pages.
