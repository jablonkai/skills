#!/usr/bin/env python3
"""Fill a .docx template's {{placeholders}} from JSON, keeping all formatting.

    wc_fill.py TEMPLATE DATA.json OUT.docx [OUT.pdf …] [--allow-missing] [--overwrite]

DATA is a flat JSON object {"name": "value", …}; each {{name}} is replaced with its value.
Replaces in the body, table cells, and every header, footer, footnote and text box (a
plain edit.replaceAll reaches only the story the caret is in, so headers and footers keep
their placeholders). Values are literal: ^p, ^t, ^& in a value are not expanded. A
placeholder split across differently formatted runs is still found, and the replacement
takes the formatting of the placeholder's first character.

The template is never written. All outputs are saved in one run (docx, pdf, odt, …),
then read back: exits 1 if any {{…}} is left or (without --allow-missing) if the
template has a placeholder DATA does not cover. Prints a JSON report.
"""
import argparse
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wclib import inspect, pdf_pages, placeholders, refuse_existing, run_script, same_file  # noqa: E402


def replace_cmds(keys, data):
    return [{"command": "edit.replaceAll",
             "params": {"text": "{{%s}}" % k, "with": str(data[k]), "matchCase": True,
                        "special": False, "wildcards": False}}
            for k in keys]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("template")
    ap.add_argument("data")
    ap.add_argument("outputs", nargs="+", help="output files; the extension picks the format")
    ap.add_argument("--allow-missing", action="store_true", help="leave placeholders DATA lacks")
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()

    template = os.path.abspath(a.template)
    outs = [os.path.abspath(o) for o in a.outputs]
    if any(same_file(template, o) or template == o for o in outs):
        sys.exit("refusing to write over the template")
    refuse_existing(outs, a.overwrite)
    data = json.load(open(a.data))
    if not isinstance(data, dict):
        sys.exit("DATA must be a JSON object of name: value")

    doc = inspect(template)
    found = placeholders(doc)
    unknown = sorted(set(found) - set(data))
    if unknown and not a.allow_missing:
        print(json.dumps({"error": "placeholders without data", "missing": {k: found[k] for k in unknown}},
                         ensure_ascii=False, indent=2))
        return 1
    keys = sorted((k for k in data if k in found), key=len, reverse=True)

    commands = ["caret.docStart"] + replace_cmds(keys, data)
    for part in doc.get("parts", []):
        if part.get("kind") == "comment" or "{{" not in part.get("text", ""):
            continue
        commands.append({"command": "caret.set",
                         "params": {"pos": {"story": {"part": part["id"]}, "path": [0], "off": 0}}})
        commands += replace_cmds([k for k in keys if "{{%s}}" % k in part["text"]], data)
    for o in outs:
        os.makedirs(os.path.dirname(o), exist_ok=True)
    run_script({"file": template, "commands": commands, "save": outs})

    docx = next((o for o in outs if o.lower().endswith(".docx")), None)
    check_path = docx
    if not check_path:  # read back through a temporary docx when only other formats were asked
        check_path = os.path.join(tempfile.mkdtemp(), "check.docx")
        run_script({"file": template, "commands": commands, "save": [check_path]})
    left = placeholders(inspect(check_path))
    report = {"template": template, "outputs": outs, "replaced": keys,
              "unused_data": sorted(set(data) - set(found)), "left": left}
    for o in outs:
        if o.lower().endswith(".pdf"):
            report.setdefault("pdf_pages", {})[o] = pdf_pages(o)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if left and not a.allow_missing else 0


if __name__ == "__main__":
    sys.exit(main())
