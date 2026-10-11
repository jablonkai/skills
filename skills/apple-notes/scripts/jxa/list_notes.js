// list_notes.js {folderIds:[...], text:bool} -> [{id, name, folderId, created, modified, locked, shared, plaintext?}]
// Properties are read in one Apple event per folder (fs.notes.name() etc.), not per note.
ObjC.import("Foundation");
function readArgs(p) {
  return JSON.parse($.NSString.stringWithContentsOfFileEncodingError(p, $.NSUTF8StringEncoding, null).js);
}
function run(argv) {
  const a = readArgs(argv[0]);
  const N = Application("Notes");
  const out = [];
  a.folderIds.forEach(fid => {
    const ns = N.folders.byId(fid).notes;
    if (ns.length === 0) return;
    const ids = ns.id(), names = ns.name(), cr = ns.creationDate(), mo = ns.modificationDate();
    const locked = ns.passwordProtected(), shared = ns.shared();
    const txt = a.text ? ns.plaintext() : null;
    ids.forEach((id, i) => {
      const r = { id: id, name: names[i], folderId: fid, created: cr[i], modified: mo[i],
                  locked: locked[i], shared: shared[i] };
      if (txt) {
        r.plaintext = locked[i] ? "" : txt[i];
        // Tables show up as U+FFFC in plaintext; their cell text is only in the body.
        if (r.plaintext.indexOf("\uFFFC") >= 0) {
          const tables = ns[i].body().match(/<table[\s\S]*?<\/table>/g) || [];
          if (tables.length) r.plaintext += "\n" + tables.map(t =>
            t.replace(/<\/td>/g, " \t ").replace(/<[^>]+>/g, " ").replace(/&nbsp;/g, " ")
             .replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/[ \t]+/g, " ")).join("\n");
        }
      }
      out.push(r);
    });
  });
  return JSON.stringify(out);
}
