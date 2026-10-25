#!/usr/bin/env python3
"""Look up CADCraft commands without dumping the ~440-entry catalogue.

    cc_commands.py WORD...            ids, aliases, labels or menu paths containing every WORD
    cc_commands.py --id dimlinear     exactly that id (or alias)
    cc_commands.py --prefix layer.    ids starting with a prefix

Prints `id [aliases] (interactive)` and the full params signature. "interactive" only
means the command also prompts in the GUI; every listed command runs headless when given
complete JSON params.
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cclib import cli  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("words", nargs="*")
    ap.add_argument("--id")
    ap.add_argument("--prefix")
    a = ap.parse_args()
    if not (a.words or a.id or a.prefix):
        ap.error("give WORDs, --id or --prefix")
    cmds = json.loads(subprocess.run([cli(), "commands"], capture_output=True, text=True, check=True).stdout)
    hits = []
    for c in cmds:
        names = [c["id"]] + c.get("aliases", [])
        if a.id and a.id.lower() not in [n.lower() for n in names]:
            continue
        if a.prefix and not c["id"].startswith(a.prefix):
            continue
        hay = " ".join(names + [c.get("label", "")] + c.get("menu", [])).lower()
        if all(w.lower() in hay for w in a.words):
            hits.append(c)
    for c in hits:
        flags = []
        if c.get("aliases"):
            flags.append("[%s]" % ", ".join(c["aliases"]))
        if c.get("interactive"):
            flags.append("(interactive)")
        if not c.get("enabled", True):
            flags.append("(disabled)")
        print("%s %s\n    %s" % (c["id"], " ".join(flags), c.get("params") or "{}"))
    if not hits:
        print("no match", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
