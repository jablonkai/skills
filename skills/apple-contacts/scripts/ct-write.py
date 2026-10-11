#!/usr/bin/env python3
"""Create, update, import and group Apple Contacts, reading every change back.

  ct-write.py create --given Anna --family Nagy --email work:anna@example.com \\
                     --phone mobile:+36301234567 --org Acme --group Team --account iCloud
  ct-write.py update --id ID --phone mobile:+36301234567 [--replace] [--note "…"]
  ct-write.py import --csv people.csv --group "Running Club" --create-group --account "On My Mac" --dry-run
  ct-write.py import --vcard cards.vcf --account iCloud
  ct-write.py group create|add|remove|delete ...
  ct-write.py delete --id ID [--id ID ...] [--yes]

New contacts and groups go to --account (default: the group's account, else the system
default account, which is named in the output). Existing contacts are matched by email,
or by name plus phone (or name alone when the new entry has neither): matches are
skipped by default (--on-duplicate update merges into them; create forces a new card),
but still added to the target group. Deletes only preview without --yes.
Output: JSON with created/updated/skipped and readback.ok. Exit 4 when the read-back
differs from the request, 2 bad input, 3 no access.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct_lib as L  # noqa: E402

FIELDS = ["prefix", "given", "middle", "family", "suffix", "nickname", "org", "department", "jobTitle",
          "birthday", "type"]


def labeled(values, kind):
    """'work:anna@x.com' -> {'label': 'work', 'value': 'anna@x.com'}; a bare value has no label."""
    out = []
    for v in values or []:
        label, sep, rest = v.partition(":")
        known = {"home", "work", "other", "school", "mobile", "cell", "iphone", "main", "homefax",
                 "workfax", "pager", "homepage"}
        if sep and label.lower() in known and rest:
            out.append({"label": label.lower(), "value": rest.strip()})
        else:
            out.append({"label": "", "value": v.strip()})
    return out


def from_flags(a):
    c = {k: getattr(a, k) for k in FIELDS if getattr(a, k, None)}
    if c.get("birthday"):
        c["birthday"] = L.parse_birthday(c["birthday"])
    if a.email:
        c["emails"] = labeled(a.email, "email")
    if a.phone:
        c["phones"] = labeled(a.phone, "phone")
    if a.url:
        c["urls"] = labeled(a.url, "url")
    if a.street or a.city or a.zip or a.country:
        c["addresses"] = [{"label": a.address_label or "", "street": a.street or "", "city": a.city or "",
                           "postalCode": a.zip or "", "country": a.country or "", "state": a.state or ""}]
    if a.note is not None:
        c["note"] = a.note
    if not (c.get("given") or c.get("family") or c.get("org") or c.get("emails") or c.get("phones")):
        if a.cmd == "create":
            L.die("a new contact needs at least a name, company, email or phone", 2)
    if not (c.get("given") or c.get("family")) and c.get("org") and "type" not in c:
        c["type"] = "organization"
    return c


class Matcher:
    """Finds an existing contact for a new entry: same email, or same name with the same
    phone (or with no email/phone to tell them apart)."""

    def __init__(self, existing):
        self.by_email, self.by_name = {}, {}
        for c in existing:
            self.add(c)

    def add(self, c, ref=None):
        ref = ref or c["id"]
        for e in c.get("emails", []):
            self.by_email.setdefault(L.email_key(e["value"]), (ref, c))
        nk = L.name_key(c) or ("org " + L.fold(c.get("org", "")) if c.get("org") else "")
        if nk:
            self.by_name.setdefault(nk, []).append((ref, c))

    def find(self, c):
        for e in c.get("emails", []):
            hit = self.by_email.get(L.email_key(e["value"]))
            if hit:
                return hit[0], "same email " + e["value"]
        nk = L.name_key(c) or ("org " + L.fold(c.get("org", "")) if c.get("org") else "")
        if not nk:
            return None, ""
        phones = {L.phone_key(p["value"]) for p in c.get("phones", [])}
        for ref, other in self.by_name.get(nk, []):
            other_phones = {L.phone_key(p["value"]) for p in other.get("phones", [])}
            if phones & other_phones:
                return ref, "same name and phone"
            if not c.get("emails") and not phones:
                return ref, "same name (no email or phone to tell apart)"
        return None, ""


def strip_meta(c):
    return {k: v for k, v in c.items() if k not in ("id", "containers", "groups", "note", "_row", "name")}


def pick_account(a, conts, group=None):
    if a.account:
        return L.resolve_container(a.account, conts)
    if group and group.get("container"):
        return next(c for c in conts if c["id"] == group["container"])
    return L.default_container(conts)


def compare(want, got, note_got=None, group_id=None):
    """Field-by-field check of a saved contact against the request (merge semantics:
    requested emails/phones must be present, extra stored ones are fine)."""
    bad = []
    for k in FIELDS:
        if want.get(k) and want[k] != got.get(k, ""):
            bad.append(f"{k}: want {want[k]!r}, stored {got.get(k, '')!r}")
    have = {L.email_key(e["value"]) for e in got.get("emails", [])}
    for e in want.get("emails", []):
        if L.email_key(e["value"]) not in have:
            bad.append(f"email {e['value']} missing")
    have = {L.phone_key(p["value"]) for p in got.get("phones", [])}
    for p in want.get("phones", []):
        if L.phone_key(p["value"]) not in have:
            bad.append(f"phone {p['value']} missing")
    if "note" in want and note_got is not None and want["note"] != note_got:
        bad.append(f"note: want {want['note']!r}, stored {note_got!r}")
    if group_id and group_id not in got.get("groups", []):
        bad.append("not in the group")
    return bad


def run_plan(plan, account, group, dry_run):
    """plan: [{'action': create|update|skip, 'contact': {...}, 'id'?, 'label', 'reason'?}]."""
    ops, group_ref = [], None
    if group and not group.get("id"):
        ops.append({"op": "createGroup", "name": group["name"], "container": account["id"], "ref": "g"})
        group_ref = "g"
    elif group:
        group_ref = group["id"]
    result = {"account": account["name"], "group": group["name"] if group else None,
              "groupCreated": bool(group and not group.get("id")),
              "created": [], "updated": [], "skipped": [], "notInGroup": [], "dryRun": dry_run}
    for n, item in enumerate(plan):
        ref = f"new:{n}"
        if item["action"] == "create":
            ops.append({"op": "create", "contact": strip_meta(item["contact"]), "container": account["id"], "ref": ref})
            target = ref
        elif item["action"] == "update":
            ops.append({"op": "update", "id": item["id"], "contact": strip_meta(item["contact"]),
                        "mode": item.get("mode", "merge"), "ref": item["id"]})
            target = item["id"]
        else:
            target = item.get("id")
        item["target"] = target
        if group_ref and target and not item.get("inGroup"):
            if item["action"] != "create" and account["id"] not in item.get("containers", [account["id"]]):
                result["notInGroup"].append({"label": item["label"], "id": target,
                                             "reason": "the existing contact is in another account"})
                continue
            if item["action"] == "skip" and target.startswith("new:"):
                continue  # duplicate of an earlier row, already added
            ops.append({"op": "addMember", "contact": target, "group": group_ref})
    if dry_run:
        for item in plan:
            key = {"create": "created", "update": "updated", "skip": "skipped"}[item["action"]]
            result[key].append({k: item[k] for k in ("label", "id", "reason") if item.get(k)})
        return result, None
    notes = {item["target"]: item["contact"]["note"] for item in plan
             if item["action"] in ("create", "update") and item["contact"].get("note") and item.get("target")}
    refs, note_back = L.save(ops, notes) if (ops or notes) else ({}, {})
    gid = refs.get("g", group.get("id") if group else None)
    if group:
        result["groupId"] = gid
    ids = []
    for item in plan:
        tid = refs.get(item["target"], item["target"]) if item.get("target") else None
        item["finalId"] = tid
        if tid and not tid.startswith("new:"):
            ids.append(tid)
    notes = {refs.get(k, k): v for k, v in notes.items()}
    # read back (notes were read back inside the save)
    got = {c["id"]: c for c in L.contacts(ids=sorted(set(ids)))} if ids else {}
    mismatches = []
    not_in = {x["id"] for x in result["notInGroup"]}
    for item in plan:
        key = {"create": "created", "update": "updated", "skip": "skipped"}[item["action"]]
        tid = item.get("finalId")
        entry = {k: item[k] for k in ("label", "reason") if item.get(k)}
        entry["id"] = tid
        result[key].append(entry)
        if not tid or tid.startswith("new:"):
            continue
        stored = got.get(tid)
        if stored is None:
            mismatches.append({"label": item["label"], "id": tid, "problems": ["not found after save"]})
            continue
        want = item["contact"] if item["action"] != "skip" else {}
        problems = compare(want, stored, note_back.get(tid) if tid in notes else None,
                           gid if (group and tid not in not_in) else None)
        if problems:
            mismatches.append({"label": item["label"], "id": tid, "problems": problems})
    result["readback"] = {"ok": not mismatches, "checked": len(got), "mismatches": mismatches}
    return result, mismatches


def build_plan(entries, existing, on_dup, group_id=None):
    m = Matcher(existing)
    by_id = {c["id"]: c for c in existing}
    plan = []
    for n, c in enumerate(entries):
        label = c.get("_label") or L.display_name(c)
        ref, why = m.find(c) if on_dup != "create" else (None, "")
        if ref is None:
            plan.append({"action": "create", "contact": c, "label": label})
            m.add(c, ref=f"new:{len(plan) - 1}")
            continue
        if ref.startswith("new:"):
            plan.append({"action": "skip", "contact": c, "label": label, "id": ref,
                         "reason": f"duplicate of an earlier entry ({why})"})
            continue
        ex = by_id[ref]
        item = {"id": ref, "contact": c, "label": label, "containers": ex.get("containers", []),
                "inGroup": bool(group_id and group_id in ex.get("groups", []))}
        if on_dup == "update":
            item.update(action="update", reason=f"merged into {L.display_name(ex)} ({why})")
        else:
            item.update(action="skip", reason=f"already exists as {L.display_name(ex)} ({why})")
        plan.append(item)
    return plan


def add_contact_flags(p):
    for k in ["prefix", "given", "middle", "family", "suffix", "nickname", "org", "department"]:
        p.add_argument(f"--{k}")
    p.add_argument("--job-title", dest="jobTitle")
    p.add_argument("--birthday", help="YYYY-MM-DD or --MM-DD")
    p.add_argument("--type", choices=["person", "organization"])
    p.add_argument("--email", action="append", help="[label:]address, repeatable")
    p.add_argument("--phone", action="append", help="[label:]number, repeatable (mobile, work, home, main …)")
    p.add_argument("--url", action="append")
    p.add_argument("--street")
    p.add_argument("--city")
    p.add_argument("--state")
    p.add_argument("--zip")
    p.add_argument("--country")
    p.add_argument("--address-label")
    p.add_argument("--note")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("create", help="one new contact")
    add_contact_flags(p)
    p.add_argument("--group")
    p.add_argument("--create-group", action="store_true")
    p.add_argument("--account")
    p.add_argument("--allow-duplicate", action="store_true")
    p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("update", help="change one contact")
    p.add_argument("--id", required=True)
    add_contact_flags(p)
    p.add_argument("--replace", action="store_true", help="given emails/phones/urls/addresses replace the stored ones")
    p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("import", help="contacts from CSV or vCard")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--csv")
    src.add_argument("--vcard")
    p.add_argument("--group", help="put every imported contact in this group")
    p.add_argument("--create-group", action="store_true", help="create --group when it doesn't exist")
    p.add_argument("--account")
    p.add_argument("--on-duplicate", choices=["skip", "update", "create"], default="skip")
    p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("group", help="create, add to, remove from or delete a group")
    p.add_argument("action", choices=["create", "add", "remove", "delete"])
    p.add_argument("name")
    p.add_argument("--id", action="append", default=[], help="contact id (add/remove), repeatable")
    p.add_argument("--account")
    p.add_argument("--yes", action="store_true", help="really delete (the group only, never its members)")

    p = sub.add_parser("delete", help="delete contacts (preview without --yes)")
    p.add_argument("--id", action="append", required=True)
    p.add_argument("--yes", action="store_true")

    a = ap.parse_args()
    if not L.framework_ok():
        L.die("writing needs Contacts access for this terminal/IDE through the Contacts framework "
              f"(state: {L.access()}); see `contacts.sh check`", 3)
    conts = L.containers()
    grps = L.groups()

    if a.cmd == "group":
        cont = L.resolve_container(a.account, conts)["id"] if a.account else None
        g = L.resolve_group(a.name, grps, container=cont, missing_ok=(a.action == "create"))
        if a.action == "create":
            if g:
                L.die(f"group {a.name!r} already exists in {L.container_name(g['container'], conts)}", 2)
            acct = L.resolve_container(a.account, conts) if a.account else L.default_container(conts)
            gid = L.save([{"op": "createGroup", "name": a.name, "container": acct["id"], "ref": "g"}])[0]["g"]
            ok = any(x["id"] == gid for x in L.groups())
            L.emit_json({"group": a.name, "id": gid, "account": acct["name"], "readback": {"ok": ok}})
            sys.exit(0 if ok else 4)
        if a.action == "delete":
            if not a.yes:
                L.emit_json({"wouldDelete": g, "note": "members are kept; re-run with --yes"})
                return
            L.save([{"op": "deleteGroup", "id": g["id"]}])
            ok = not any(x["id"] == g["id"] for x in L.groups())
            L.emit_json({"deleted": g["name"], "readback": {"ok": ok}})
            sys.exit(0 if ok else 4)
        if not a.id:
            L.die("add/remove need --id", 2)
        op = "addMember" if a.action == "add" else "removeMember"
        L.save([{"op": op, "contact": i, "group": g["id"]} for i in a.id])
        back = {c["id"]: c for c in L.contacts(ids=a.id)}
        bad = [i for i in a.id if (g["id"] in back.get(i, {}).get("groups", [])) != (a.action == "add")]
        L.emit_json({"group": g["name"], a.action: a.id, "readback": {"ok": not bad, "mismatches": bad}})
        sys.exit(4 if bad else 0)

    if a.cmd == "delete":
        found = L.contacts(ids=a.id)
        missing = sorted(set(a.id) - {c["id"] for c in found})
        if missing:
            L.die("no contact with id " + ", ".join(missing), 2)
        listing = [{"id": c["id"], "name": L.display_name(c)} for c in found]
        if not a.yes:
            L.emit_json({"wouldDelete": listing, "note": "re-run with --yes to delete"})
            return
        L.save([{"op": "delete", "id": c["id"]} for c in found])
        left = L.contacts(ids=a.id)
        L.emit_json({"deleted": listing, "readback": {"ok": not left}})
        sys.exit(4 if left else 0)

    if a.cmd == "update":
        cur = L.contacts(ids=[a.id])
        if not cur:
            L.die(f"no contact with id {a.id}", 2)
        want = from_flags(a)
        plan = [{"action": "update", "id": a.id, "contact": want, "label": L.display_name(cur[0]),
                 "mode": "replace" if a.replace else "merge", "containers": cur[0].get("containers", [])}]
        acct = {"id": (cur[0].get("containers") or [""])[0], "name": ", ".join(
            L.container_name(x, conts) for x in cur[0].get("containers", []))}
        result, bad = run_plan(plan, acct, None, a.dry_run)
        L.emit_json(result)
        sys.exit(4 if bad else 0)

    # create / import
    group = None
    if a.group:
        cont = L.resolve_container(a.account, conts)["id"] if a.account else None
        group = L.resolve_group(a.group, grps, container=cont, missing_ok=True)
        if group is None:
            if not a.create_group:
                L.die(f"no group named {a.group!r}; add --create-group to create it", 2)
            group = {"name": a.group}
    account = pick_account(a, conts, group if group and group.get("id") else None)
    if group and group.get("container") and group["container"] != account["id"]:
        L.die(f"group {group['name']!r} is in {L.container_name(group['container'], conts)}, "
              f"not {account['name']}: contacts and their groups must share an account", 2)

    if a.cmd == "create":
        entries = [from_flags(a)]
        on_dup = "create" if a.allow_duplicate else "skip"
    elif a.csv:
        entries = L.read_csv_contacts(a.csv)
        for c in entries:
            c["_label"] = f"row {c['_row']}: {L.display_name(c)}"
            extra = c.pop("groups", [])
            if extra:
                L.warn(f"row {c['_row']}: group column ignored ({', '.join(extra)}); use --group")
        on_dup = a.on_duplicate
    else:
        text = Path(a.vcard).read_text(encoding="utf-8", errors="replace")
        entries = [strip_meta(c) for c in L.parse_vcard_text(text)]
        # The framework drops NOTE; take it from the text when every card parsed.
        notes = L.vcard_notes(text)
        if any(notes):
            if len(notes) == len(entries):
                for c, note in zip(entries, notes):
                    if note:
                        c["note"] = note
            else:
                L.warn("some cards were empty, so vCard notes could not be matched and were left out")
        on_dup = a.on_duplicate
    if not entries:
        L.die("nothing to import", 2)

    existing = L.contacts()
    plan = build_plan(entries, existing, on_dup, group.get("id") if group else None)
    result, bad = run_plan(plan, account, group, a.dry_run)
    L.emit_json(result)
    sys.exit(4 if bad else 0)


if __name__ == "__main__":
    main()
