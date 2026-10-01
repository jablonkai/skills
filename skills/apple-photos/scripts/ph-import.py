#!/usr/bin/env python3
"""Import files or folders into the library open in Photos, optionally into an album.

  ph-import.py PATH... [--album NAME] [--recursive] [--library LIB] [--dry-run] [--allow-duplicates]

Files already in the library (same original file name and byte size) are skipped
unless --allow-duplicates. Photos' own duplicate check is always bypassed, because it
opens a modal sheet that blocks AppleScript until someone clicks it.
Prints a JSON summary with the ids of the imported items.
Exit: 0 ok, 1 error, 3 wrong/no library open in Photos, 4 no Automation permission,
124 timeout, 130 interrupted.
"""
import argparse
import json
import sys
from pathlib import Path

from ph_lib import chunks, die, jxa, osxphotos, require_open_library

MEDIA_EXT = {".jpg", ".jpeg", ".heic", ".heif", ".png", ".tif", ".tiff", ".gif", ".webp", ".bmp",
             ".dng", ".cr2", ".cr3", ".nef", ".arw", ".raf", ".orf", ".rw2",
             ".mov", ".mp4", ".m4v", ".avi", ".3gp"}

IMPORT = r"""
function run(argv) {
  const P = Application('Photos');
  const files = JSON.parse(argv[0]).map(f => Path(f));
  const opts = {skipCheckDuplicates: true};
  if (argv[1]) {
    const found = P.albums.whose({name: argv[1]})();
    if (found.length > 1) throw new Error('more than one top-level album named ' + argv[1]);
    if (!found.length) {
      // make can create the album yet return null or fail with -1700: find it by name instead
      try { P.make({new: 'album', named: argv[1]}); } catch (e) {}
      for (let i = 0; i < 20 && !found.length; i++) { delay(0.5); found.push(...P.albums.whose({name: argv[1]})()); }
      if (!found.length) throw new Error('Photos did not create the album ' + argv[1]);
    }
    opts.into = found[0];
  }
  const items = P.import(files, opts) || [];
  return JSON.stringify(items.map(m => m.id()));
}
"""


def collect(paths, recursive):
    files = []
    for p in map(lambda s: Path(s).expanduser(), paths):
        if p.is_dir():
            it = p.rglob("*") if recursive else p.iterdir()
            files += sorted(f for f in it if f.is_file() and f.suffix.lower() in MEDIA_EXT
                            and not f.name.startswith("."))
        elif p.is_file():
            files.append(p)
        else:
            die(f"not found: {p}")
    return [f.resolve() for f in files]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--album", help="top-level album to import into (created if missing)")
    ap.add_argument("--recursive", action="store_true", help="descend into subfolders")
    ap.add_argument("--library", help="expected library; must be the one open in Photos")
    ap.add_argument("--allow-duplicates", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--batch", type=int, default=100)
    a = ap.parse_args()

    library = require_open_library(a.library)
    files = collect(a.paths, a.recursive)
    if not files:
        die("no media files found")

    existing = set()
    if not a.allow_duplicates:
        out = osxphotos(["query", "--library", library, "--quiet", "--print",
                         "{photo.original_filename}|{photo.original_filesize}"])
        existing = {tuple(l.rsplit("|", 1)) for l in out.splitlines() if "|" in l}
        existing = {(n.lower(), s) for n, s in existing}
    todo = [f for f in files if (f.name.lower(), str(f.stat().st_size)) not in existing]
    report = {"library": library, "album": a.album, "files": len(files),
              "skipped_duplicates": [f.name for f in files if f not in todo], "to_import": len(todo)}
    if a.dry_run or not todo:
        report["dry_run"] = a.dry_run
        print(json.dumps(report, indent=1))
        return

    ids = []
    try:
        for batch in chunks(todo, a.batch):
            ids += jxa(IMPORT, [json.dumps([str(f) for f in batch]), a.album or ""])
            print(f"imported {len(ids)}/{len(todo)}", file=sys.stderr)
    except KeyboardInterrupt:
        report.update(imported=len(ids), ids=ids, stopped="interrupted")
        print(json.dumps(report, indent=1))
        sys.exit(130)
    report.update(imported=len(ids), ids=ids)
    print(json.dumps(report, indent=1))
    if len(ids) != len(todo):
        die(f"Photos imported {len(ids)} of {len(todo)} files (unsupported or unreadable files are skipped silently)")


if __name__ == "__main__":
    main()
