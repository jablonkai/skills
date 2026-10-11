// save_attachments.js {noteId, dir} -> [{id, name, path|null, error?}]
// Saves into `dir` (a temp dir; Notes is sandboxed and may not write to ~/Documents etc).
// Tables and other inline objects have no file and fail to save: reported, not fatal.
ObjC.import("Foundation");
function readArgs(p) {
  return JSON.parse($.NSString.stringWithContentsOfFileEncodingError(p, $.NSUTF8StringEncoding, null).js);
}
function run(argv) {
  const a = readArgs(argv[0]);
  const N = Application("Notes");
  const atts = N.notes.byId(a.noteId).attachments;
  const out = [];
  for (let i = 0; i < atts.length; i++) {
    const x = atts[i];
    const r = { id: x.id(), name: x.name(), path: null };
    if (r.name === null) { r.error = "no file (inline object such as a table)"; out.push(r); continue; }
    const p = a.dir + "/" + i + "_" + r.name.replace(/[\/:]/g, "-");
    try { N.save(x, { in: Path(p) }); r.path = p; } catch (e) { r.error = String(e); }
    out.push(r);
  }
  return JSON.stringify(out);
}
