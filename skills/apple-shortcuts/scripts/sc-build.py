#!/usr/bin/env python3
"""Build a signed .shortcut file from a small JSON spec.

    python3 sc-build.py SPEC.json [-o OUT.shortcut] [--mode anyone|people-who-know-me]
                        [--unsigned] [--import]

Spec:
    {
      "name": "Resize to 320",                 # becomes the file name -> shortcut name on import
      "input": ["image"],                      # image|text|file|pdf|url|... (omit: no input)
      "actions": [
        {"action": "image.resize", "params": {"WFImage": "$input", "WFImageResizeWidth": "320"}},
        {"action": "output", "params": {"WFOutput": "$prev:text"}}
      ]
    }

Parameter values are copied verbatim, except these tokens:
    "$input"        the shortcut input (as a variable attachment)
    "$prev"         the previous action's output
    "$N"            the output of action N (1-based)
    "...:text"      any of the above as a text token string (for text fields like WFOutput)

"action" is a short identifier ("image.resize") or a full one ("is.workflow.actions.image.resize").
Actions outside VERIFIED print a warning: they may import as a blank, unconfigured action.

--import opens the file in Shortcuts; the user still has to click "Add Shortcut".
Exit codes: 0 ok, 1 bad spec, 2 signing failed.
"""
import argparse
import json
import os
import plistlib
import subprocess
import sys
import tempfile
import uuid

PREFIX = "is.workflow.actions."

# Actions checked by importing and running a generated shortcut on Shortcuts 10.0
# (value: the OutputName shown on the variable). Anything else may import with a
# parameter left empty, and an empty required parameter makes `shortcuts run` hang.
VERIFIED = {
    "image.resize": "Resized Image",
    "count": "Count",
    "getitemfromlist": "Item from List",
    "output": None,
}

INPUT_CLASSES = {
    "image": "WFImageContentItem",
    "text": "WFStringContentItem",
    "file": "WFGenericFileContentItem",
    "pdf": "WFPDFContentItem",
    "url": "WFURLContentItem",
    "richtext": "WFRichTextContentItem",
    "media": "WFAVAssetContentItem",
    "folder": "WFFolderContentItem",
}


def fail(msg, code=1):
    print(f"sc-build: {msg}", file=sys.stderr)
    sys.exit(code)


def short_id(action):
    return action[len(PREFIX):] if action.startswith(PREFIX) else action


def token_value(token, index, uuids, names):
    """Resolve $input / $prev / $N to the attachment dict, or None if not a token."""
    if token == "$input":
        return {"Type": "ExtensionInput"}
    if token == "$prev":
        ref = index - 1
    elif token[1:].isdigit():
        ref = int(token[1:]) - 1
    else:
        return None
    if ref < 0 or ref >= index:
        fail(f"action {index + 1}: {token} refers to an action that has not run yet")
    return {"Type": "ActionOutput", "OutputUUID": uuids[ref], "OutputName": names[ref] or "Output"}


def resolve(value, index, uuids, names):
    if isinstance(value, dict):
        return {k: resolve(v, index, uuids, names) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve(v, index, uuids, names) for v in value]
    if not isinstance(value, str) or not value.startswith("$"):
        return value
    token, as_text = (value[:-5], True) if value.endswith(":text") else (value, False)
    attachment = token_value(token, index, uuids, names)
    if attachment is None:
        return value
    if as_text:
        return {"Value": {"string": "￼", "attachmentsByRange": {"{0, 1}": attachment}},
                "WFSerializationType": "WFTextTokenString"}
    return {"Value": attachment, "WFSerializationType": "WFTextTokenAttachment"}


def build(spec):
    actions = spec.get("actions")
    if not isinstance(actions, list) or not actions:
        fail("spec needs a non-empty 'actions' list")
    unknown_inputs = [i for i in spec.get("input", []) if i not in INPUT_CLASSES]
    if unknown_inputs:
        fail(f"unknown input type(s) {unknown_inputs}; use {sorted(INPUT_CLASSES)}")

    uuids = [str(uuid.uuid4()).upper() for _ in actions]
    names = []
    out = []
    for i, act in enumerate(actions):
        if "action" not in act:
            fail(f"action {i + 1} has no 'action' key")
        sid = short_id(act["action"])
        if sid not in VERIFIED:
            print(f"sc-build: warning: '{sid}' is not in the verified list; check it in the editor",
                  file=sys.stderr)
        names.append(act.get("output_name") or VERIFIED.get(sid))
        params = resolve(act.get("params", {}), i, uuids, names)
        params["UUID"] = uuids[i]
        out.append({"WFWorkflowActionIdentifier": PREFIX + sid, "WFWorkflowActionParameters": params})

    inputs = [INPUT_CLASSES[i] for i in spec.get("input", [])]
    return {
        "WFWorkflowClientVersion": "2605.0.5",
        "WFWorkflowMinimumClientVersion": 900,
        "WFWorkflowMinimumClientVersionString": "900",
        "WFWorkflowIcon": {"WFWorkflowIconStartColor": spec.get("color", 4282601983),
                           "WFWorkflowIconGlyphNumber": spec.get("glyph", 59511)},
        "WFWorkflowInputContentItemClasses": inputs,
        "WFWorkflowHasShortcutInputVariables": bool(inputs),
        "WFWorkflowTypes": [],
        "WFWorkflowImportQuestions": [],
        "WFWorkflowActions": out,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("-o", "--output", help="output path (default: '<name>.shortcut' next to the spec)")
    ap.add_argument("--mode", default="people-who-know-me", choices=["anyone", "people-who-know-me"])
    ap.add_argument("--unsigned", action="store_true", help="write the plain plist (not importable)")
    ap.add_argument("--import", dest="do_import", action="store_true", help="open the result in Shortcuts")
    args = ap.parse_args()

    try:
        with open(args.spec, encoding="utf-8") as f:
            spec = json.load(f)
    except (OSError, ValueError) as e:
        fail(f"cannot read spec: {e}")
    name = spec.get("name")
    if not name or "/" in name:
        fail("spec needs a 'name' without '/'")

    plist = build(spec)
    out = args.output or os.path.join(os.path.dirname(os.path.abspath(args.spec)), f"{name}.shortcut")
    if args.unsigned:
        with open(out, "wb") as f:
            plistlib.dump(plist, f, fmt=plistlib.FMT_BINARY)
    else:
        # The source file's name is what Shortcuts shows on import, so sign from '<name>.shortcut'.
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, f"{name}.shortcut")
            with open(src, "wb") as f:
                plistlib.dump(plist, f, fmt=plistlib.FMT_BINARY)
            r = subprocess.run(["shortcuts", "sign", "--mode", args.mode, "--input", src, "--output", out],
                               capture_output=True, text=True)
            if r.returncode != 0 or not os.path.exists(out):
                fail(f"shortcuts sign failed ({r.returncode}): {r.stderr.strip() or r.stdout.strip()}", 2)
    print(out)
    if args.do_import:
        subprocess.run(["open", out], check=False)
        print("sc-build: Shortcuts shows an import preview; click 'Add Shortcut' to add it.", file=sys.stderr)


if __name__ == "__main__":
    main()
