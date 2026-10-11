// make_folder.js {account, parentId?, name} -> {id}
ObjC.import("Foundation");
function readArgs(p) {
  return JSON.parse($.NSString.stringWithContentsOfFileEncodingError(p, $.NSUTF8StringEncoding, null).js);
}
function run(argv) {
  const a = readArgs(argv[0]);
  const N = Application("Notes");
  const parent = a.parentId ? N.folders.byId(a.parentId) : N.accounts.byName(a.account);
  parent.folders.push(N.Folder({ name: a.name }));
  return JSON.stringify({ id: parent.folders.byName(a.name).id() });
}
