// Apple Numbers operations in JXA, driven by a JSON request file so no value is ever
// spliced into script source. Called by the Python helpers through numbers_osa.py;
// usable directly:
//
//   osascript -l JavaScript numbers_ops.js OP REQUEST.json
//
// Ops (request fields):
//   build   out, into (bool), sheet, table, rowCount, columnCount, headerRows,
//           headerCols, footerRows, formats [{range, format}], writes [[addr, value]],
//           exports [{path, as, options}]
//   read    path, sheets [names], tables [names], maxRows
//   export  as, options, items [{src, dst}]
//   close   paths
//
// Output is one JSON document on stdout. JXA numbers are locale-free; AppleScript
// would print 42,5 under a comma-decimal locale.
// Documents this script opens are closed again, even on error; documents the user
// already had open are refused rather than touched.

ObjC.import("Foundation");

const BUNDLE_ID = "com.apple.Numbers";
const N = Application(BUNDLE_ID);

function run(argv) {
  if (argv.length < 2) throw new Error("usage: numbers_ops.js OP REQUEST.json");
  const req = readJson(argv[1]);
  const ops = { build, read, export: exportMany, close: closePaths };
  if (!ops[argv[0]]) throw new Error("unknown op: " + argv[0]);
  return JSON.stringify(ops[argv[0]](req));
}

function readJson(p) {
  const s = $.NSString.stringWithContentsOfFileEncodingError(p, $.NSUTF8StringEncoding, null);
  if (s.isNil()) throw new Error("cannot read request " + p);
  return JSON.parse(ObjC.unwrap(s));
}

// ---------------------------------------------------------------- open / close

function docPath(d) {
  try {
    const f = d.file();
    return f ? f.toString() : null;
  } catch (e) {
    return null;
  }
}

function findOpenDoc(p) {
  const docs = N.documents();
  for (const d of docs) if (docPath(d) === p) return d;
  return null;
}

function openOwned(p) {
  if (findOpenDoc(p)) throw new Error("already open in Numbers (close it first, unsaved edits would conflict): " + p);
  const d = N.open(Path(p));
  if (!d) throw new Error("Numbers could not open " + p + " (see numbers.sh --dialog)");
  return d;
}

function closeQuietly(d) {
  if (!d) return;
  try {
    d.close({ saving: "no" });
  } catch (e) {}
}

function closePaths(req) {
  let n = 0;
  for (const p of req.paths) {
    const d = findOpenDoc(p);
    if (d) {
      d.close({ saving: "no" });
      n++;
    }
  }
  return { closed: n };
}

function newDoc(out) {
  const d = N.Document().make();
  // Save at once: an unsaved new document is autosaved as "Untitled" into iCloud.
  try {
    d.save({ in: Path(out) });
  } catch (e) {
    closeQuietly(d);
    throw e;
  }
  return d;
}

// ---------------------------------------------------------------- build

function byName(coll, name) {
  const names = coll.name();
  const i = names.indexOf(name);
  return i < 0 ? null : coll[i];
}

// The table a build writes into: the new document's own table, a new sheet's own
// table, or a new table pushed onto an existing sheet.
function targetTable(d, req) {
  if (!req.into) {
    const sh = d.sheets[0];
    if (req.sheet) sh.name = req.sheet;
    return sh.tables[0];
  }
  let sh = req.sheet ? byName(d.sheets, req.sheet) : null;
  if (!sh) {
    // `make new sheet at end of sheets` fails (-10000); push works.
    d.sheets.push(N.Sheet());
    sh = d.sheets[d.sheets.length - 1];
    if (req.sheet) sh.name = req.sheet;
    if (sh.tables.length > 0) return sh.tables[0];
  }
  if (req.table && byName(sh.tables, req.table)) throw new Error("table already exists: " + req.sheet + " / " + req.table);
  sh.tables.push(N.Table({ rowCount: req.rowCount, columnCount: req.columnCount }));
  return sh.tables[sh.tables.length - 1];
}

function build(req) {
  const d = req.into ? openOwned(req.out) : newDoc(req.out);
  try {
    const tb = targetTable(d, req);
    if (req.table) tb.name = req.table;
    // Header and footer counts must fit inside the row count, so size first. Shrinking
    // below the header rows fails, hence counts are zeroed before resizing.
    tb.headerColumnCount = 0;
    tb.footerRowCount = 0;
    tb.headerRowCount = 0;
    tb.rowCount = req.rowCount;
    tb.columnCount = req.columnCount;
    tb.headerRowCount = req.headerRows;
    tb.headerColumnCount = req.headerCols;
    tb.footerRowCount = req.footerRows;
    for (const f of req.formats) tb.ranges[f.range].format = f.format;
    for (const [a, v] of req.writes) tb.cells[a].value = v;
    const res = {
      out: req.out,
      sheet: tb.parent().name(),
      table: tb.name(),
      rows: tb.rowCount(),
      columns: tb.columnCount(),
      formulas: req.formulaCells.map((a) => cellInfo(tb.cells[a], a)),
      exports: [],
    };
    d.save();
    for (const x of req.exports) {
      exportDoc(d, x.path, x.as, x.options);
      res.exports.push(x.path);
    }
    d.close({ saving: "no" });
    return res;
  } catch (e) {
    closeQuietly(d);
    throw e;
  }
}

function cellInfo(c, addr) {
  const v = c.value();
  return {
    cell: addr,
    value: v instanceof Date ? null : v,
    formatted: c.formattedValue(),
    formula: c.formula(),
    error: v === null && c.formula() !== null,
  };
}

// ---------------------------------------------------------------- read

function read(req) {
  const d = openOwned(req.path);
  try {
    const out = { path: req.path, sheets: [] };
    for (const sh of d.sheets()) {
      const sname = sh.name();
      if (req.sheets && req.sheets.length && req.sheets.indexOf(sname) < 0) continue;
      const s = { name: sname, charts: sh.charts.length, tables: [] };
      for (const tb of sh.tables()) {
        const tname = tb.name();
        if (req.tables && req.tables.length && req.tables.indexOf(tname) < 0) continue;
        s.tables.push(readTable(tb, tname, req.maxRows));
      }
      out.sheets.push(s);
    }
    d.close({ saving: "no" });
    return out;
  } catch (e) {
    closeQuietly(d);
    throw e;
  }
}

function readTable(tb, name, maxRows) {
  const rows = tb.rowCount();
  const cols = tb.columnCount();
  const t = {
    name,
    rows,
    columns: cols,
    headerRows: tb.headerRowCount(),
    headerColumns: tb.headerColumnCount(),
    footerRows: tb.footerRowCount(),
    truncated: false,
    values: [],
    formatted: [],
    formulas: {},
    errors: [],
  };
  let last = rows;
  if (maxRows && rows > maxRows) {
    last = maxRows;
    t.truncated = true;
  }
  // Bulk reads: one Apple event per property for the whole range, row-major.
  const rng = tb.ranges[addr(1, 1) + ":" + addr(last, cols)];
  const vals = rng.cells.value();
  const fmts = rng.cells.formattedValue();
  const fs = rng.cells.formula();
  for (let r = 0; r < last; r++) {
    const vr = [];
    const fr = [];
    for (let c = 0; c < cols; c++) {
      const i = r * cols + c;
      let v = vals[i];
      // Date values come back shifted by hours; the formatted value is what is shown.
      if (v instanceof Date) v = fmts[i];
      vr.push(v === undefined ? null : v);
      fr.push(fmts[i] === undefined ? null : fmts[i]);
      if (fs[i] !== null && fs[i] !== undefined) {
        t.formulas[addr(r + 1, c + 1)] = fs[i];
        // An error cell reads as missing value, like an empty one; its formula tells.
        if (v === null) t.errors.push(addr(r + 1, c + 1));
      }
    }
    t.values.push(vr);
    t.formatted.push(fr);
  }
  return t;
}

function addr(r, c) {
  let s = "";
  while (c > 0) {
    const m = (c - 1) % 26;
    s = String.fromCharCode(65 + m) + s;
    c = Math.floor((c - 1) / 26);
  }
  return s + r;
}

// ---------------------------------------------------------------- export

function exportDoc(d, dst, as, options) {
  const args = { to: Path(dst), as };
  if (options && Object.keys(options).length) args.withProperties = options;
  N.export(d, args);
}

function exportMany(req) {
  const out = [];
  for (const it of req.items) {
    let d = null;
    try {
      d = openOwned(it.src);
      const sheets = d.sheets.length;
      let tables = 0;
      for (const sh of d.sheets()) tables += sh.tables.length;
      exportDoc(d, it.dst, req.as, req.options);
      d.close({ saving: "no" });
      out.push({ src: it.src, dst: it.dst, ok: true, sheets, tables });
    } catch (e) {
      closeQuietly(d);
      out.push({ src: it.src, dst: it.dst, ok: false, error: String(e) });
    }
  }
  return out;
}
