// folders.js {account?} -> [{id, name, account, path, parent}]
// account.folders is flat (nested folders included); container() gives the parent.
ObjC.import("Foundation");
function readArgs(p) {
  return JSON.parse($.NSString.stringWithContentsOfFileEncodingError(p, $.NSUTF8StringEncoding, null).js);
}
function run(argv) {
  const a = readArgs(argv[0]);
  const N = Application("Notes");
  const out = [];
  N.accounts().forEach(acc => {
    const accName = acc.name();
    if (a.account && accName.toLowerCase() !== a.account.toLowerCase()) return;
    const fs = acc.folders;
    const ids = fs.id(), names = fs.name();
    const byId = {};
    ids.forEach((id, i) => {
      let parent = null;
      try { const c = fs[i].container(); const cid = c.id(); if (ids.indexOf(cid) >= 0) parent = cid; } catch (e) {}
      byId[id] = { id: id, name: names[i], account: accName, parent: parent };
    });
    const pathOf = f => (f.parent && byId[f.parent] ? pathOf(byId[f.parent]) : accName) + "/" + f.name;
    ids.forEach(id => { byId[id].path = pathOf(byId[id]); out.push(byId[id]); });
  });
  return JSON.stringify(out);
}
