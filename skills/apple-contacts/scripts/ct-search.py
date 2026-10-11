#!/usr/bin/env python3
"""Search and list Apple Contacts.

  ct-search.py --query anna                      name, nickname, company, email or phone
  ct-search.py --email @example.com --group Team  fields combine with AND
  ct-search.py --group "Running Club" --format csv
  ct-search.py --accounts | --groups              the accounts and groups themselves

Output: a Markdown table (default), JSON (--format json, full fields and ids) or CSV.
Read-only.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct_lib as L  # noqa: E402


def matches(c, a):
    def has(text, needle):
        return L.fold(needle) in L.fold(text)

    if a.name and not has(" ".join([L.display_name(c), c.get("nickname", "")]), a.name):
        return False
    if a.org and not has(c.get("org", ""), a.org):
        return False
    if a.email and not any(a.email.lower() in e["value"].lower() for e in c.get("emails", [])):
        return False
    if a.phone:
        want = "".join(ch for ch in a.phone if ch.isdigit())
        if not any(L.phone_key(p["value"]) == L.phone_key(want) or want in "".join(ch for ch in p["value"] if ch.isdigit())
                   for p in c.get("phones", [])):
            return False
    if a.query:
        q = a.query
        texts = [L.display_name(c), c.get("nickname", ""), c.get("org", ""), c.get("jobTitle", "")]
        texts += [e["value"] for e in c.get("emails", [])]
        hit = any(has(t, q) for t in texts)
        digits = "".join(ch for ch in q if ch.isdigit())
        if not hit and len(digits) >= 4:
            hit = any(digits in "".join(ch for ch in p["value"] if ch.isdigit()) for p in c.get("phones", []))
        if not hit and a.notes:
            hit = has(c.get("note", ""), q)
        if not hit:
            return False
    if a.missing:
        for field in a.missing:
            if c.get(field):
                return False
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--query", "-q", help="free text: name, nickname, company, title, email, phone digits")
    ap.add_argument("--name")
    ap.add_argument("--email", help="substring of any email (e.g. @example.com)")
    ap.add_argument("--phone", help="phone number in any format")
    ap.add_argument("--org", help="company substring")
    ap.add_argument("--missing", action="append", choices=["emails", "phones", "addresses", "birthday", "org"],
                    help="only contacts without this field (repeatable)")
    ap.add_argument("--group", help="group name or id")
    ap.add_argument("--account", help="account (container) name or id: iCloud, Exchange, 'On My Mac' …")
    ap.add_argument("--notes", action="store_true", help="read notes too (via AppleScript, opens Contacts)")
    ap.add_argument("--raw", action="store_true", help="one row per card, not unified across accounts")
    ap.add_argument("--format", choices=["table", "json", "csv"], default="table")
    ap.add_argument("--out", help="write to this file instead of stdout")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--accounts", action="store_true", help="list accounts (containers)")
    ap.add_argument("--groups", action="store_true", help="list groups")
    a = ap.parse_args()

    conts = L.containers()
    cont_names = {c["id"]: c["name"] for c in conts}
    if a.accounts:
        rows = [[c["name"], c["type"], c["count"], "yes" if c["default"] else "", c["id"]] for c in conts]
        print(L.md_table(["account", "type", "contacts", "default", "id"], rows) if a.format == "table"
              else json.dumps(conts, indent=2))
        return
    grps = L.groups()
    group_names = {g["id"]: g["name"] for g in grps}
    if a.groups:
        rows = [[g["name"], cont_names.get(g["container"], g["container"]), g["count"], g["id"]] for g in grps]
        print(L.md_table(["group", "account", "members", "id"], rows) if a.format == "table"
              else json.dumps(grps, indent=2))
        return

    group = L.resolve_group(a.group, grps)["id"] if a.group else None
    cont = L.resolve_container(a.account, conts)["id"] if a.account else None
    cs = L.contacts(group=group, container=None if group else cont, raw=a.raw, notes=a.notes)
    if group and cont:
        cs = [c for c in cs if cont in c.get("containers", [])]
    cs = [c for c in cs if matches(c, a)]
    cs.sort(key=lambda c: (L.fold(c.get("family", "")) or L.fold(L.display_name(c)), L.fold(c.get("given", ""))))
    if a.limit:
        cs = cs[: a.limit]

    if a.format == "json":
        for c in cs:
            c["name"] = L.display_name(c)
            c["groupNames"] = [group_names.get(g, g) for g in c.get("groups", [])]
            c["accountNames"] = [cont_names.get(x, x) for x in c.get("containers", [])]
        text = json.dumps(cs, indent=2, ensure_ascii=False) + "\n"
    elif a.format == "csv":
        cols = L.CSV_COLUMNS if a.notes else [c for c in L.CSV_COLUMNS if c != "note"]
        text = L.write_csv([L.csv_row(c, group_names, cont_names) for c in cs], columns=cols)
    else:
        rows = [[L.display_name(c), c.get("org", ""),
                 ", ".join(e["value"] for e in c.get("emails", [])),
                 ", ".join(p["value"] for p in c.get("phones", [])),
                 ", ".join(group_names.get(g, g) for g in c.get("groups", [])),
                 ", ".join(cont_names.get(x, x) for x in c.get("containers", []))] for c in cs]
        text = L.md_table(["name", "company", "emails", "phones", "groups", "account"], rows)
        text += f"\n\n{len(cs)} contact(s)\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"wrote {len(cs)} contact(s) to {a.out}")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
