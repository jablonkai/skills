#!/usr/bin/env python3
"""Decode a .shortcut file and summarise its actions.

    python3 sc-decode.py FILE.shortcut [--json | --plist OUT.plist]

Handles both signed files (an Apple Encrypted Archive, magic "AEA1", as exported from
Shortcuts or made by `shortcuts sign`) and plain plist files. Signed files are checked
against the leaf certificate in their own signature, then unpacked with the built-in
`aea` and `aa` tools. Nothing is run.

Default output: one line per action, "N. identifier  key=value ...", with variable
references shown as {Shortcut Input} or {Output of N}. --json prints the whole workflow.
Exit codes: 0 ok, 1 unreadable or not a shortcut.
"""
import argparse
import base64
import json
import os
import plistlib
import struct
import subprocess
import sys
import tempfile

PREFIX = "is.workflow.actions."
P256_SPKI_PREFIX = bytes.fromhex("3059301306072a8648ce3d020106082a8648ce3d030107034200")


def fail(msg):
    print(f"sc-decode: {msg}", file=sys.stderr)
    sys.exit(1)


def load(path):
    with open(path, "rb") as f:
        data = f.read()
    if not data.startswith(b"AEA1"):
        try:
            return plistlib.loads(data)
        except Exception as e:  # noqa: BLE001 - any parse error means "not a shortcut"
            fail(f"not a plist or signed shortcut: {e}")
    size = struct.unpack("<I", data[8:12])[0]
    try:
        auth = plistlib.loads(data[12:12 + size])
    except Exception as e:  # noqa: BLE001
        fail(f"signed file with unreadable auth data: {e}")
    with tempfile.TemporaryDirectory() as tmp:
        der, pem, aar, out = (os.path.join(tmp, n) for n in ("leaf.der", "pub.pem", "x.aar", "x"))
        if "SigningPublicKey" in auth:
            # "people-who-know-me": a raw X9.63 P-256 key; wrap it as SubjectPublicKeyInfo.
            with open(pem, "w") as f:
                f.write("-----BEGIN PUBLIC KEY-----\n"
                        + base64.b64encode(P256_SPKI_PREFIX + auth["SigningPublicKey"]).decode()
                        + "\n-----END PUBLIC KEY-----\n")
        elif auth.get("SigningCertificateChain"):
            # "anyone": the leaf certificate of the chain holds the signing key.
            with open(der, "wb") as f:
                f.write(auth["SigningCertificateChain"][0])
            r = subprocess.run(["openssl", "x509", "-inform", "der", "-in", der, "-pubkey", "-noout"],
                               capture_output=True, text=True)
            if r.returncode != 0:
                fail(f"openssl failed: {r.stderr.strip()}")
            with open(pem, "w") as f:
                f.write(r.stdout)
        else:
            fail(f"unknown signature format (auth data keys: {sorted(auth)})")
        steps = [["aea", "decrypt", "-i", path, "-o", aar, "-sign-pub", pem],
                  ["mkdir", "-p", out],
                  ["aa", "extract", "-i", aar, "-d", out]]
        for cmd in steps:
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                fail(f"{cmd[0]} failed: {r.stderr.strip()}")
        wflows = [n for n in os.listdir(out) if n.endswith(".wflow")]
        if not wflows:
            fail("archive has no .wflow file")
        with open(os.path.join(out, wflows[0]), "rb") as f:
            return plistlib.load(f)


def describe(value, uuid_index):
    if isinstance(value, dict):
        v = value.get("Value")
        kind = value.get("WFSerializationType")
        if kind == "WFTextTokenAttachment" and isinstance(v, dict):
            return ref(v, uuid_index)
        if kind == "WFTextTokenString" and isinstance(v, dict):
            text = v.get("string", "")
            for rng, att in sorted(v.get("attachmentsByRange", {}).items(), reverse=True):
                pos = int(rng.strip("{}").split(",")[0])
                text = text[:pos] + ref(att, uuid_index) + text[pos + 1:]
            return text
        if v is not None:
            return describe(v, uuid_index)
        return {k: describe(x, uuid_index) for k, x in value.items()}
    if isinstance(value, list):
        return [describe(x, uuid_index) for x in value]
    return value


def ref(att, uuid_index):
    kind = att.get("Type")
    if kind == "ExtensionInput":
        return "{Shortcut Input}"
    if kind == "ActionOutput":
        n = uuid_index.get(att.get("OutputUUID"))
        return f"{{Output of {n}}}" if n else f"{{{att.get('OutputName', 'Output')}}}"
    if kind == "Variable":
        return "{Var " + att.get("VariableName", "?") + "}"
    return "{" + str(kind) + "}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--json", action="store_true")
    g.add_argument("--plist", help="write the decoded workflow plist (XML) here")
    args = ap.parse_args()

    wf = load(args.file)
    if "WFWorkflowActions" not in wf:
        fail("no WFWorkflowActions: not a shortcut")
    if args.plist:
        with open(args.plist, "wb") as f:
            plistlib.dump(wf, f)
        return
    if args.json:
        print(json.dumps(wf, default=lambda b: f"<{len(b)} bytes>", ensure_ascii=False, indent=1))
        return

    actions = wf["WFWorkflowActions"]
    uuid_index = {a.get("WFWorkflowActionParameters", {}).get("UUID"): i + 1 for i, a in enumerate(actions)}
    inputs = [c.replace("WF", "", 1).replace("ContentItem", "") for c in wf.get("WFWorkflowInputContentItemClasses", [])]
    print(f"input: {', '.join(inputs) if inputs and wf.get('WFWorkflowHasShortcutInputVariables') else 'none'}")
    print(f"actions: {len(actions)}")
    for i, a in enumerate(actions, 1):
        ident = a.get("WFWorkflowActionIdentifier", "?")
        params = {k: describe(v, uuid_index) for k, v in a.get("WFWorkflowActionParameters", {}).items()
                  if k not in ("UUID", "GroupingIdentifier")}
        shown = " ".join(f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in params.items())
        print(f"{i}. {ident.replace(PREFIX, '')}  {shown}".rstrip())


if __name__ == "__main__":
    main()
