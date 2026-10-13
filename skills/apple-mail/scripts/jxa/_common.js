// _common.js: prepended to every jxa/*.js by mail_lib.jxa(). Not a script on its own.
ObjC.import("Foundation");
const M = Application("Mail");
const LOCAL = "On My Mac";

function readArgs(p) {
  return JSON.parse($.NSString.stringWithContentsOfFileEncodingError(p, $.NSUTF8StringEncoding, null).js);
}
function nfc(s) { return (s || "").normalize("NFC"); }
function iso(d) { return d ? d.toISOString() : null; }

// Paths of every mailbox in an element collection, relative to its account
// ("[Gmail]/All Mail", "Importálás/Skill-Eval Seed"). Walks container.container... as
// bulk property reads, one Apple event per level: per-mailbox walks cost ~100 ms each.
function bulkPaths(coll) {
  const parts = coll.name().map(n => [nfc(n)]);
  let spec = coll;
  for (let d = 0; d < 12; d++) {
    spec = spec.container;
    let up;
    try { up = spec.name(); } catch (e) { break; }
    if (!up.some(x => x)) break;
    up.forEach((n, i) => { if (n) parts[i].unshift(nfc(n)); });
  }
  return parts.map(p => p.join("/"));
}

// Every mailbox as {account, accountId, path, key, ref}. key = "Account/path".
function allMailboxes(onlyAccount) {
  const out = [];
  if (!onlyAccount || onlyAccount === LOCAL) {
    bulkPaths(M.mailboxes).forEach((p, i) =>
      out.push({ account: LOCAL, accountId: null, path: p, key: LOCAL + "/" + p, ref: M.mailboxes[i] }));
  }
  const names = M.accounts.name(), ids = M.accounts.id();
  names.forEach((an0, j) => {
    const an = nfc(an0);
    if (onlyAccount && onlyAccount !== an) return;
    const coll = M.accounts[j].mailboxes;
    bulkPaths(coll).forEach((p, i) =>
      out.push({ account: an, accountId: ids[j], path: p, key: an + "/" + p, ref: coll[i] }));
  });
  return out;
}

function findMailbox(key, cache) {
  const want = nfc(key);
  const list = cache || allMailboxes(want.startsWith(LOCAL + "/") ? LOCAL : want.split("/")[0]);
  const hit = list.find(m => m.key === want);
  if (!hit) throw new Error("mailbox not found: " + key);
  return hit;
}

// "Account/path#id" -> message specifier
function msgByRef(ref, cache) {
  const i = ref.lastIndexOf("#");
  const mb = findMailbox(ref.slice(0, i), cache);
  return { mb: mb, msg: mb.ref.messages.byId(parseInt(ref.slice(i + 1), 10)) };
}

function writeText(path, text) {
  $(text).writeToFileAtomicallyEncodingError(path, true, $.NSUTF8StringEncoding, null);
}
