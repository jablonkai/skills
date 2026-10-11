#!/usr/bin/env python3
"""Check stored contacts against a file or an expectation. Read-only.

  ct-verify.py --group "Running Club" --csv people.csv     every CSV row is in the group,
                                                           with its emails and phones
  ct-verify.py --group "Running Club" --vcard club.vcf     the file and the group hold the
                                                           same people (both directions)
  ct-verify.py --group "Running Club" --count 5            the group has exactly 5 members
                                                           (combines with --csv / --vcard)

Entries match a stored contact by email and name, then email, then name. Prints JSON with ok, missing,
extra and field mismatches; exit 4 when anything differs.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct_lib as L  # noqa: E402


def find(entry, stored, used):
    """The stored contact for a file entry: same email and name first, then same email,
    then same name; each stored contact is matched at most once, so two people who share
    an email (a likely duplicate) still pair up with their own cards."""
    emails = {L.email_key(e["value"]) for e in entry.get("emails", [])}
    nk = L.name_key(entry) or L.fold(entry.get("org", ""))
    free = [c for c in stored if c["id"] not in used]

    def same_email(c):
        return bool(emails & {L.email_key(e["value"]) for e in c.get("emails", [])})

    def same_name(c):
        return bool(nk) and nk == (L.name_key(c) or L.fold(c.get("org", "")))

    for test in (lambda c: same_email(c) and same_name(c), same_email, same_name):
        hit = next((c for c in free if test(c)), None)
        if hit:
            return hit
    return None


def diff(entry, c):
    bad = []
    for k in ("given", "family", "org", "jobTitle"):
        if entry.get(k) and entry[k] != c.get(k, ""):
            bad.append(f"{k}: file {entry[k]!r}, stored {c.get(k, '')!r}")
    have = {L.email_key(e["value"]) for e in c.get("emails", [])}
    bad += [f"email {e['value']} missing" for e in entry.get("emails", []) if L.email_key(e["value"]) not in have]
    have = {L.phone_key(p["value"]) for p in c.get("phones", [])}
    bad += [f"phone {p['value']} missing" for p in entry.get("phones", []) if L.phone_key(p["value"]) not in have]
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--group", required=True, help="group name or id")
    ap.add_argument("--account", help="account of the group when the name is ambiguous")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--csv")
    src.add_argument("--vcard")
    ap.add_argument("--count", type=int, help="expected member count (combines with --csv/--vcard)")
    a = ap.parse_args()

    cont = L.resolve_container(a.account)["id"] if a.account else None
    g = L.resolve_group(a.group, container=cont)
    stored = L.contacts(group=g["id"])
    if not (a.csv or a.vcard or a.count is not None):
        L.die("give --csv, --vcard and/or --count", 2)
    out = {"group": g["name"], "members": len(stored), "ok": True}
    if a.count is not None:
        out["expected"] = a.count
        out["ok"] = len(stored) == a.count
    if a.csv or a.vcard:
        entries = L.read_csv_contacts(a.csv) if a.csv else L.parse_vcard_text(Path(a.vcard).read_text(encoding="utf-8"))
        out["fileEntries"] = len(entries)
        missing, mismatches, used = [], [], set()
        for e in entries:
            c = find(e, stored, used)
            label = L.display_name(e)
            if c is None:
                missing.append(label)
                continue
            used.add(c["id"])
            bad = diff(e, c)
            if bad:
                mismatches.append({"entry": label, "id": c["id"], "problems": bad})
        out["missing"] = missing
        out["mismatches"] = mismatches
        if a.vcard:  # an export must not hold more or fewer people than the group
            out["extra"] = [L.display_name(c) for c in stored if c["id"] not in used]
        out["ok"] = out["ok"] and not missing and not mismatches and not out.get("extra")
    L.emit_json(out)
    sys.exit(0 if out["ok"] else 4)


if __name__ == "__main__":
    main()
