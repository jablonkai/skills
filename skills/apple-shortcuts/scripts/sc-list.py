#!/usr/bin/env python3
"""List shortcuts as JSON: name, id, folder and whether it accepts input.

    python3 sc-list.py [--folder NAME] [--names]

Reads `shortcuts list` (names, ids, folders) and adds `accepts_input` from the
Shortcuts Events scripting dictionary. The dictionary's `action count` and `subtitle`
are left out on purpose: on Shortcuts 10.0 they report 0 / "No actions" for imported
shortcuts that do have actions. To see what a shortcut does, decode an exported
.shortcut file with sc-decode.py, or open it with `shortcuts view NAME`.

Exit codes: 0 ok, 1 the CLI failed. Without Automation permission for Shortcuts Events,
`accepts_input` is null and a warning goes to stderr.
"""
import argparse
import json
import subprocess
import sys

JXA = """
const s = Application("Shortcuts Events").shortcuts;
JSON.stringify(s.id().map((id, i) => [id, s.acceptsInput()[i]]));
"""


def cli(*args):
    r = subprocess.run(["shortcuts", "list", *args], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"sc-list: shortcuts list failed: {r.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return [line for line in r.stdout.splitlines() if line.strip()]


def split_id(line):
    name, ident = line[:-1].rsplit(" (", 1)
    return name, ident


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--folder", help="only this folder (name, id, or 'none')")
    ap.add_argument("--names", action="store_true", help="print names only, one per line")
    args = ap.parse_args()

    if args.folder:
        rows = [(*split_id(line), args.folder) for line in cli("--folder-name", args.folder, "--show-identifiers")]
    else:
        folder_of = {}
        for fline in cli("--folders", "--show-identifiers"):
            fname, fid = split_id(fline)
            for line in cli("--folder-name", fid, "--show-identifiers"):
                folder_of[split_id(line)[1]] = fname
        rows = [(*split_id(line), None) for line in cli("--show-identifiers")]
        rows = [(n, i, folder_of.get(i)) for n, i, _ in rows]

    if args.names:
        print("\n".join(n for n, _, _ in rows))
        return

    accepts = {}
    r = subprocess.run(["osascript", "-l", "JavaScript", "-e", JXA], capture_output=True, text=True, timeout=30)
    if r.returncode == 0:
        accepts = dict(json.loads(r.stdout))
    else:
        print(f"sc-list: warning: no accepts_input (Automation permission for Shortcuts Events?): "
              f"{r.stderr.strip()}", file=sys.stderr)
    print(json.dumps([{"name": n, "id": i, "folder": f, "accepts_input": accepts.get(i)} for n, i, f in rows],
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
