// organize.js {refs:[ref], action: move|flag|unflag|read|unread, target?: mailbox key, color?: 0-6}
//   -> [{ref, ok, error?}]   (never deletes; no send path exists in this skill)
function run(argv) {
  const a = readArgs(argv[0]);
  const cache = allMailboxes(null);
  const target = a.target ? findMailbox(a.target, cache).ref : null;
  return JSON.stringify(a.refs.map(ref => {
    try {
      const m = msgByRef(ref, cache).msg;
      switch (a.action) {
        case "move": M.move(m, { to: target }); break;
        case "flag": m.flaggedStatus = true; if (a.color != null) m.flagIndex = a.color; break;
        case "unflag": m.flaggedStatus = false; break;
        case "read": m.readStatus = true; break;
        case "unread": m.readStatus = false; break;
        default: throw new Error("unknown action " + a.action);
      }
      return { ref: ref, ok: true };
    } catch (e) { return { ref: ref, ok: false, error: e.errorNumber || String(e) }; }
  }));
}
