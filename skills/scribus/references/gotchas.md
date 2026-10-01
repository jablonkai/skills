# Gotchas (measured on Scribus 1.6.6, macOS 27)

## Running headless

| Symptom | Cause | Fix |
|---|---|---|
| The job "succeeded" (exit 0) but no PDF was written | An uncaught exception in a `-py` script still exits 0; the traceback goes to stderr only | Use `scribus.py run`, which wraps the job and exits 1 with the traceback |
| `print()` shows nothing | Script stdout is swallowed | Set `RESULT = {...}` in the job; the runner prints it |
| "File … does not exist, aborting" | Scribus parses its own argv: `--` (and anything after it) is taken as a document to open, and `-x` as an option | The runner passes job arguments via the environment; inside the job they are in `sys.argv[1:]` |
| The run hangs until `--timeout` | A modal dialog in a headless run. Not seen with missing fonts or images on 1.6.6, but possible with damaged files or `saveDoc()` on an unsaved doc | Use `saveDocAs`; the runner kills the process group on timeout (exit 3) |
| `QPixmap::setMask…` and `scpaths:` lines on stderr | Harmless startup noise | The runner filters them |
| A job changes prefs the GUI later uses | Headless runs share `~/Library/Preferences/Scribus/` with the GUI | Don't call preference-changing functions; nothing in this skill does |
| Relative paths in arguments fail | — | The runner keeps your working directory. `.sla` files store image paths relative to the `.sla` itself |

A run takes about 2–5 s, mostly startup. Batch many outputs into one job rather than one
run per record.

## Silent failures in the API

- **Overflowing text** is cut off in the PDF without any warning. `textOverflows(name)`
  is 1 when the chain does not fit. The runner reports it after every job.
- **`loadImage` of a missing file** sets the path and returns normally, and the PDF has an
  empty frame. `getImageColorSpace(name)` is −1 when nothing loaded.
- **PDF, EPS and PS files as images need Ghostscript** (`gs` on `PATH`, e.g.
  `brew install ghostscript`). Without it, `loadImage` leaves the frame empty
  (`getImageColorSpace` −1). Raster formats (PNG, JPEG, TIFF, PSD) need nothing extra.
- **Missing fonts**:
  - `openDoc` silently substitutes the default font (Arial here) for any font the `.sla`
    uses that isn't installed. `export` compares the `.sla` fonts with the installed ones
    and reports any substitutions.
  - `createCharStyle(font=…)` and `setFont` raise `ValueError`. Pick fonts with
    `L.font(...)`, which falls back through candidates.
- **Error messages are localized** ("A megadott betűkészlet nem elérhető." = "font not
  available"). Match on the exception type, never on the message.
- **`PAPER_*` constants are points.** `newDocument(PAPER_A5, …, UNIT_MILLIMETERS, …)`
  made a 421 × 595 **mm** (A2) page. Use mm tuples or `PAPER_A5_MM`.
- **`getAllObjects(1)`** means *type* 1, not page 1. Use `getAllObjects(page=0)` (0-based).
- **Margins tuples differ**: `newDocument` takes (left, right, top, bottom), while
  `getPageMargins`/`getPageNMargins` return (top, left, right, bottom).
- **`saveDoc()`** on a never-saved doc may open a file dialog. Use `saveDocAs(path)`.
- **`getInfo()` returns an empty tuple** on 1.6.6, even right after `setInfo()`. Read the
  `.sla`'s `DOCUMENT` attributes (`AUTHOR`, `TITLE`, `COMMENTS`) instead.
- **`closeDoc()` changes the working directory** to `~/Documents`, so relative paths in
  the rest of the job break. `L.reopen()`/`L.open_doc()` restore it; when calling
  `closeDoc` yourself, use absolute paths.
- **`setImageOffset(x, y)` is in points** whatever the document unit is (the docstring:
  "values shown on the properties palette when point unit is used").
- **No keep-with-next, keep-together, orphan or widow control** in the scripter. The
  `.sla` stores them on `STYLE` elements (`KeepWithNext`, `KeepTogether`,
  `KeepLinesStart`, `KeepLinesEnd`); `L.paragraph_keeps()` edits them.

## Layout behaviour

- **`gotoPage()` while editing a master page** silently leaves the master: frames created
  afterwards land on the *default* master instead. Inside `L.master(name, build)`,
  create frames with `page=None`.
- **Localized names**:
  - The default master is "Normal" in English and **"Normál"** in Hungarian. Facing
    documents get two, "Normál bal"/"Normál jobb" (left/right).
  - Auto-generated frame names are localized too ("Szöveg52" = "Text52").
  - Never hard-code them. Use `masterPageNames()`, and pass `name=` when you need to find
    a frame again.
- **Fixed leading does not follow font size**: with `linespacingmode=0`, shrinking the
  text keeps the old leading, so two shrunk lines need as much room as two full-size
  ones. Use automatic leading (`leading="auto"` in `L.para_style`) for shrink-to-fit
  frames.
- **`linkTextFrames(a, b)`** requires `b` to be empty, and both frames must already exist.
- **Image scale is relative to the image's own ppi**: `setImageScale(1, 1)` shows a
  300 ppi image at its 300 ppi size. Prefer `setScaleImageToFrame(True, True)` and check
  the effective ppi in the PDF (`verify --min-ppi`).
- Text separators: both `\r` and `\n` in `setText` make new paragraphs.
- `chr(0x1E)`, inserted with `insertText`, is the automatic page-number marker for
  master pages. Verified: it renders as 1, 2, 3.

## PDF

- `PDFfile()` starts from the document's saved PDF settings. An opened `.sla` brings its
  own (maybe odd) settings, so `L.export_pdf` sets every attribute that matters.
- Version code 10 is PDF/X-4. The full table is in [pdf-export.md](pdf-export.md).
- **The PDF Title leaks the local path**: with an empty document title, Scribus writes the
  `.sla`'s absolute path (`/Users/<you>/…`) as the PDF Title, which the printer sees. It
  comes from `setInfo()`'s second argument, read when `PDFfile()` is created.
  `L.export_pdf` sets it (to `title=` or the PDF's base name) before that.
- veraPDF cannot validate PDF/X. `verify --pdfx4` is a structural check.
- **Copy-paste text from the PDF can differ from what prints**:
  - Ligatures extract as one character ("ﬀ").
  - With Arial, a printed hyphen extracts as a soft hyphen (U+00AD), so "Müller-Lüdenscheidt" doesn't match a search for the CSV value.
  - Normalise with NFKC and map U+00AD to "-" before comparing `pdftotext` output with source data.

## Security posture

- `scribus.py run` executes the given Python file **inside Scribus with the user's
  rights**: the job can read and write anything the user can. Run only jobs you wrote or
  reviewed. The skill's own jobs (`badges.py`, `export_job.py`) only read the inputs
  named on their command line and write the outputs named there.
- No network listener, socket or bridge is opened. There is no live-session control, so
  the bridge rules (token auth, origin checks) don't apply.
- **Stop path**:
  - every run is its own process group with a `--timeout` (default 180 s), killed on
    expiry
  - `export` refuses to overwrite without `--force`, and never saves the source `.sla`
- The runner writes only a temp wrapper and a result file under the system temp dir,
  and deletes them after the run.
