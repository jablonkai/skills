#!/usr/bin/env python3
"""Create (or reuse) a Photos album and fill it from an osxphotos query. Idempotent.

  ph-album.py --name "Hiking" [--folder "Trips"] [--library LIB] [--dry-run] -- --keyword hiking -i

Everything after `--` is passed to `osxphotos query` (see references/osxphotos-cli.md).
The album is reused when it exists (an error if the name is ambiguous); only items not
already in it are added, so re-running never duplicates. Items the album holds that the
query does not match are reported, never removed.
Exit: 0 ok, 1 error, 3 wrong/no library open in Photos, 4 no Automation permission,
124 timeout, 130 interrupted.
"""
import argparse
import json
import sys
import time

from ph_lib import chunks, die, jxa, query_uuids, require_open_library, split_query

ENSURE = r"""
// `make` can create the object yet return null or fail with -1700 (seen right after a
// library opens), so never trust its result: make once, then find the object by name.
function makeThenFind(P, kind, name, parent, elements) {
  try {
    P.make(parent === P ? {new: kind, named: name} : {new: kind, named: name, at: parent});
  } catch (e) {}
  for (let i = 0; i < 20; i++) {
    const found = elements().whose({name: name})();
    if (found.length) return found[0];
    delay(0.5);
  }
  throw new Error('Photos did not create the ' + kind + ' ' + name +
                  ' (is the library read-only, or a dialog open in Photos?)');
}

function run(argv) {
  const [name, folderName, create] = argv;
  const P = Application('Photos');
  let parent = P, folderCreated = false;
  if (folderName) {
    const fs = P.folders.whose({name: folderName})();
    if (fs.length > 1) throw new Error('more than one folder named ' + folderName);
    if (fs.length) parent = fs[0];
    else if (create === '1') { parent = makeThenFind(P, 'folder', folderName, P, () => P.folders); folderCreated = true; }
    else return JSON.stringify({album: null, members: [], folderMissing: true});
  }
  const found = parent.albums.whose({name: name})();
  if (found.length > 1) return JSON.stringify({ambiguous: found.map(a => a.id())});
  let album = found[0] || null, created = false;
  if (!album && create === '1') {
    const p = parent;
    album = makeThenFind(P, 'album', name, p, () => p.albums);
    created = true;
  }
  return JSON.stringify({album: album ? album.id() : null, created: created, folderCreated: folderCreated,
                         members: album ? album.mediaItems.id() : []});
}
"""

ADD = r"""
function run(argv) {
  const P = Application('Photos');
  const album = P.albums.byId(argv[0]);
  const items = JSON.parse(argv[1]).map(u => P.mediaItems.byId(u + '/L0/001'));
  P.add(items, {to: album});
  return JSON.stringify(album.mediaItems.id().length);
}
"""

MEMBERS = r"""
function run(argv) { return JSON.stringify(Application('Photos').albums.byId(argv[0]).mediaItems.id()); }
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True, help="album name (exact, case-sensitive)")
    ap.add_argument("--folder", help="top-level folder to hold the album (created if missing)")
    ap.add_argument("--library", help="library the query reads; must be the one open in Photos")
    ap.add_argument("--dry-run", action="store_true", help="show what would change, write nothing")
    ap.add_argument("--batch", type=int, default=200, help="items per add call (default 200)")
    ap.add_argument("--timeout", type=float, default=0, help="stop after SEC seconds (0 = no limit)")
    own, query = split_query(sys.argv[1:])
    a = ap.parse_args(own)
    if not query:
        die("give the osxphotos query after --, e.g. -- --keyword hiking -i (an empty query would add every item)")

    require_open_library(a.library)
    uuids = query_uuids(a.library, query)
    state = jxa(ENSURE, [a.name, a.folder or "", "0" if a.dry_run else "1"])
    if state.get("ambiguous"):
        die(f"{len(state['ambiguous'])} albums are named {a.name!r}; rename one or pick another name")
    members = {m.split("/")[0] for m in state["members"]}
    missing = [u for u in uuids if u not in members]
    extra = sorted(members - set(uuids))
    report = {"album": a.name, "folder": a.folder, "matched": len(uuids), "already_in_album": len(uuids) - len(missing),
              "to_add": len(missing), "not_matching_query": len(extra), "created": state.get("created", False)}

    if a.dry_run:
        report["dry_run"] = True
        print(json.dumps(report, indent=1))
        return

    added, start = 0, time.monotonic()
    try:
        for batch in chunks(missing, a.batch):
            if a.timeout and time.monotonic() - start > a.timeout:
                report.update(added=added, stopped="timeout")
                print(json.dumps(report, indent=1))
                sys.exit(124)
            jxa(ADD, [state["album"], json.dumps(batch)])
            added += len(batch)
            print(f"added {added}/{len(missing)}", file=sys.stderr)
    except KeyboardInterrupt:
        report.update(added=added, stopped="interrupted")
        print(json.dumps(report, indent=1))
        sys.exit(130)

    final = {m.split("/")[0] for m in jxa(MEMBERS, [state["album"]])}
    report.update(added=added, album_count=len(final), all_matched_in_album=set(uuids) <= final)
    print(json.dumps(report, indent=1))
    if not report["all_matched_in_album"]:
        die("read-back: some matched items are not in the album")


if __name__ == "__main__":
    main()
