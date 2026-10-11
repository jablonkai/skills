#!/usr/bin/env python3
"""Export Apple Contacts to vCard and/or CSV, then check the files.

  ct-export.py --group "Running Club" --out club.vcf --out club.csv
  ct-export.py --all --out backup.vcf --photos
  ct-export.py --query "@example.com" --out example.csv

Selection: --group, --account, --query (as ct-search.py --query), or --all. The file
type follows the extension (.vcf/.vcard or .csv). Every file is read back: vCards are
re-parsed by the Contacts framework, CSV rows re-read, and both counted against the
selection. Notes are included (the framework hides them, so they are read through
AppleScript); --no-notes skips that. Prints a JSON summary; exit 4 when a check fails.
Read-only for Contacts.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct_lib as L  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sel = ap.add_mutually_exclusive_group(required=True)
    sel.add_argument("--group", help="group name or id")
    sel.add_argument("--query", "-q", help="name, company, email or phone text")
    sel.add_argument("--all", action="store_true", help="every contact")
    ap.add_argument("--account", help="limit to one account (container): iCloud, Exchange, 'On My Mac' …")
    ap.add_argument("--out", action="append", required=True, help="output file (.vcf or .csv), repeatable")
    ap.add_argument("--photos", action="store_true", help="keep contact photos in vCards (large)")
    ap.add_argument("--no-notes", dest="notes", action="store_false",
                    help="leave notes out (they are read via AppleScript, which launches Contacts)")
    ap.add_argument("--raw", action="store_true", help="one entry per card instead of unified contacts")
    a = ap.parse_args()

    for out in a.out:
        if Path(out).suffix.lower() not in (".vcf", ".vcard", ".csv"):
            L.die(f"{out}: use a .vcf, .vcard or .csv extension", 2)
        if a.raw and Path(out).suffix.lower() != ".csv":
            L.die("--raw is for CSV only: vCards are written from unified contacts", 2)

    conts = L.containers()
    cont_names = {c["id"]: c["name"] for c in conts}
    grps = L.groups()
    group_names = {g["id"]: g["name"] for g in grps}
    group = L.resolve_group(a.group, grps)["id"] if a.group else None
    cont = L.resolve_container(a.account, conts)["id"] if a.account else None

    cs = L.contacts(group=group, container=None if group else cont, raw=a.raw, notes=a.notes)
    if group and cont:
        cs = [c for c in cs if cont in c.get("containers", [])]
    if a.query:
        q = L.fold(a.query)
        digits = "".join(ch for ch in a.query if ch.isdigit())
        cs = [c for c in cs if q in L.fold(" ".join([L.display_name(c), c.get("nickname", ""), c.get("org", "")]
                                                      + [e["value"] for e in c.get("emails", [])]))
              or (len(digits) >= 4 and any(digits in "".join(ch for ch in p["value"] if ch.isdigit())
                                           for p in c.get("phones", [])))]
    ids = [c["id"] for c in cs]
    if not cs:
        L.die("the selection is empty; nothing exported", 2)

    summary = {"selected": len(cs), "files": [], "ok": True}
    for out in a.out:
        path = Path(out).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix.lower() == ".csv":
            cols = L.CSV_COLUMNS if a.notes else [c for c in L.CSV_COLUMNS if c != "note"]
            L.write_csv([L.csv_row(c, group_names, cont_names) for c in cs], path, columns=cols)
            with path.open(encoding="utf-8", newline="") as f:
                back = list(csv.DictReader(f))
            got_ids = [r["id"] for r in back]
            ok = got_ids == ids
            summary["files"].append({"path": str(path), "format": "csv", "rows": len(back), "ok": ok})
        else:
            # By ids, so the file holds exactly the selection; the whole book needs no list.
            everything = a.all and not cont
            text = L.vcard(ids=None if everything else ids, photos=a.photos, notes=a.notes)
            path.write_text(text, encoding="utf-8")
            cards = L.parse_vcard_text(text)
            names_back = sorted(L.name_key(c) or L.fold(c.get("org", "")) for c in cards)
            names_want = sorted(L.name_key(c) or L.fold(c.get("org", "")) for c in cs)
            # The framework's parser skips cards with no data at all, so count BEGIN lines and
            # compare names only when every card parsed.
            n_cards = sum(1 for line in text.splitlines() if line.strip().upper() == "BEGIN:VCARD")
            ok = n_cards == len(cs) and (len(cards) != n_cards or names_back == names_want)
            summary["files"].append({"path": str(path), "format": "vcard", "version": "3.0",
                                     "cards": n_cards, "parsed": len(cards), "ok": ok,
                                     "photos": a.photos, "notes": a.notes})
        summary["ok"] &= ok
    if group:
        summary["group"] = group_names[group]
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    sys.exit(0 if summary["ok"] else 4)


if __name__ == "__main__":
    main()
