#!/usr/bin/env python3
"""Report likely duplicate and incomplete Apple Contacts. Read-only: never merges or edits.

  ct-audit.py duplicates [--group G] [--account A] [--fuzzy]
  ct-audit.py incomplete [--require emails --require phones] [--check intl-phone]
  ct-audit.py all --format json --out audit.json

Duplicates are found on the unified view, so cards Contacts already links across
accounts are one contact and are not reported. Signals: same email (case-insensitive),
same phone (digits, last 9 compared, so +36 30 …, 06 30 … and 0036 30 … agree), same
name (accents, case and word order ignored). An email or phone shared by more than
--max-shared contacts (a switchboard, a family address) is ignored as a signal.
Confidence: high = name plus email/phone, or email plus phone; medium = one signal;
low (--fuzzy only) = similar names (same family name, one given name a prefix of the
other or same initial). Exit 0 always; the report says what was found.
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct_lib as L  # noqa: E402

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class DSU:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


def similar_names(a, b):
    fa, fb = L.fold(a.get("family", "")), L.fold(b.get("family", ""))
    ga, gb = L.fold(a.get("given", "")), L.fold(b.get("given", ""))
    if not (fa and fb and ga and gb) or fa != fb or ga == gb:
        return False
    short, long_ = sorted((ga, gb), key=len)
    return (len(short) >= 3 and long_.startswith(short)) or (len(short) <= 2 and short[0] == long_[0])


def find_duplicates(cs, max_shared=3, fuzzy=False):
    by_id = {c["id"]: c for c in cs}
    index = {"email": defaultdict(set), "phone": defaultdict(set), "name": defaultdict(set)}
    for c in cs:
        for e in c.get("emails", []):
            if L.email_key(e["value"]):
                index["email"][L.email_key(e["value"])].add(c["id"])
        for p in c.get("phones", []):
            k = L.phone_key(p["value"])
            if len(k) >= 7:
                index["phone"][k].add(c["id"])
        nk = L.name_key(c) if c.get("type") != "organization" else "org " + L.fold(c.get("org", ""))
        if nk and len(nk.split()) >= 2:  # a lone first name is too weak to call a duplicate
            index["name"][nk].add(c["id"])
    shared = {}
    pairs = defaultdict(lambda: defaultdict(list))  # (a, b) -> kind -> [values]
    for kind, idx in index.items():
        for key, ids in idx.items():
            if len(ids) < 2:
                continue
            if kind != "name" and len(ids) > max_shared:
                shared[f"{kind}:{key}"] = len(ids)
                continue
            ids = sorted(ids)
            for i, a in enumerate(ids):
                for b in ids[i + 1:]:
                    pairs[(a, b)][kind].append(key)
    if fuzzy:
        by_family = defaultdict(list)
        for c in cs:
            if c.get("family"):
                by_family[L.fold(c["family"])].append(c)
        for group in by_family.values():
            for i, a in enumerate(group):
                for b in group[i + 1:]:
                    if similar_names(a, b):
                        key = tuple(sorted((a["id"], b["id"])))
                        pairs[key]["similar-name"].append(f"{L.display_name(a)} ~ {L.display_name(b)}")

    def confidence(kinds):
        strong = {"email", "phone"} & set(kinds)
        if ("name" in kinds and strong) or len(strong) == 2:
            return "high"
        if strong or "name" in kinds:
            return "medium"
        return "low"

    rank = {"high": 0, "medium": 1, "low": 2}
    dsu = DSU()
    pair_info = []
    for (a, b), kinds in pairs.items():
        conf = confidence(kinds)
        if conf == "low" and not fuzzy:
            continue
        dsu.union(a, b)
        pair_info.append({"a": a, "b": b, "confidence": conf,
                          "reasons": {k: sorted(set(v)) for k, v in kinds.items()}})
    clusters = defaultdict(list)
    for p in pair_info:
        clusters[dsu.find(p["a"])].append(p)
    out = []
    for plist in clusters.values():
        ids = sorted({x for p in plist for x in (p["a"], p["b"])})
        conf = min((p["confidence"] for p in plist), key=rank.get)
        reasons = sorted({k for p in plist for k in p["reasons"]})
        out.append({"confidence": conf, "reasons": reasons, "pairs": plist,
                    "contacts": [summary(by_id[i]) for i in ids]})
    out.sort(key=lambda c: (rank[c["confidence"]], L.fold(c["contacts"][0]["name"])))
    return out, shared


def summary(c):
    return {"id": c["id"], "name": L.display_name(c), "org": c.get("org", ""),
            "emails": [e["value"] for e in c.get("emails", [])],
            "phones": [p["value"] for p in c.get("phones", [])],
            "containers": c.get("containers", [])}


def find_incomplete(cs, require=(), checks=()):
    out = []
    for c in cs:
        issues = []
        has_name = c.get("given") or c.get("family") or c.get("org")
        if not has_name:
            issues.append("no name or company")
        if not c.get("emails") and not c.get("phones"):
            issues.append("no email or phone")
        for e in c.get("emails", []):
            if not EMAIL_RE.match(e["value"].strip()):
                issues.append(f"malformed email {e['value']!r}")
        for p in c.get("phones", []):
            digits = re.sub(r"\D", "", p["value"])
            if len(digits) < 5 or re.search(r"[A-Za-z]{3,}", p["value"]):
                issues.append(f"suspicious phone {p['value']!r}")
            elif "intl-phone" in checks and not p["value"].strip().startswith(("+", "00")):
                issues.append(f"phone without country code {p['value']!r}")
        for field in require:
            if not c.get(field):
                issues.append(f"missing {field}")
        if issues:
            out.append({**summary(c), "issues": issues})
    out.sort(key=lambda r: L.fold(r["name"]))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", choices=["duplicates", "incomplete", "all"])
    ap.add_argument("--group", help="group name or id")
    ap.add_argument("--account", help="account (container) name or id")
    ap.add_argument("--fuzzy", action="store_true", help="also report similar names (low confidence)")
    ap.add_argument("--max-shared", type=int, default=3,
                    help="ignore an email/phone shared by more contacts than this (default 3)")
    ap.add_argument("--require", action="append", default=[],
                    choices=["emails", "phones", "addresses", "birthday", "org", "given", "family", "jobTitle"],
                    help="flag contacts missing this field (repeatable)")
    ap.add_argument("--check", action="append", default=[], choices=["intl-phone"],
                    help="extra checks: intl-phone flags numbers without a country code")
    ap.add_argument("--format", choices=["md", "json", "csv"], default="md")
    ap.add_argument("--out")
    a = ap.parse_args()

    conts = L.containers()
    cont_names = {c["id"]: c["name"] for c in conts}
    group = L.resolve_group(a.group)["id"] if a.group else None
    cont = L.resolve_container(a.account, conts)["id"] if a.account else None
    cs = L.contacts(group=group, container=None if group else cont)
    if group and cont:
        cs = [c for c in cs if cont in c.get("containers", [])]

    result = {"scanned": len(cs), "view": "unified (linked cards count once)" if conts else "cards (AppleScript)"}
    if a.what in ("duplicates", "all"):
        clusters, shared = find_duplicates(cs, a.max_shared, a.fuzzy)
        result["duplicates"] = clusters
        result["ignoredSharedValues"] = shared
    if a.what in ("incomplete", "all"):
        result["incomplete"] = find_incomplete(cs, a.require, a.check)

    acct = lambda x: ", ".join(cont_names.get(i, i) for i in x["containers"])  # noqa: E731
    if a.format == "json":
        text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    elif a.format == "csv":
        rows = []
        for n, cl in enumerate(result.get("duplicates", []), 1):
            for c in cl["contacts"]:
                rows.append({"kind": "duplicate", "cluster": n, "confidence": cl["confidence"],
                             "reasons": "; ".join(cl["reasons"]), "id": c["id"], "name": c["name"],
                             "emails": "; ".join(c["emails"]), "phones": "; ".join(c["phones"]),
                             "accounts": acct(c)})
        for c in result.get("incomplete", []):
            rows.append({"kind": "incomplete", "cluster": "", "confidence": "", "reasons": "; ".join(c["issues"]),
                         "id": c["id"], "name": c["name"], "emails": "; ".join(c["emails"]),
                         "phones": "; ".join(c["phones"]), "accounts": acct(c)})
        text = L.write_csv(rows, columns=["kind", "cluster", "confidence", "reasons", "id", "name",
                                          "emails", "phones", "accounts"])
    else:
        parts = [f"Scanned {len(cs)} contacts ({result['view']})."]
        if "duplicates" in result:
            cl = result["duplicates"]
            parts.append(f"\n## Likely duplicates: {len(cl)} group(s)\n")
            for n, d in enumerate(cl, 1):
                parts.append(f"**{n}. {d['confidence']}** — same {', '.join(d['reasons'])}\n")
                parts.append(L.md_table(["name", "emails", "phones", "account", "id"],
                                        [[c["name"], ", ".join(c["emails"]), ", ".join(c["phones"]), acct(c), c["id"]]
                                         for c in d["contacts"]]) + "\n")
            if result["ignoredSharedValues"]:
                parts.append("Ignored as shared (not evidence of a duplicate): "
                             + ", ".join(f"{k} ×{v}" for k, v in result["ignoredSharedValues"].items()))
        if "incomplete" in result:
            inc = result["incomplete"]
            parts.append(f"\n## Incomplete: {len(inc)} contact(s)\n")
            parts.append(L.md_table(["name", "issues", "account", "id"],
                                    [[c["name"], "; ".join(c["issues"]), acct(c), c["id"]] for c in inc]))
        text = "\n".join(parts) + "\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(json.dumps({"wrote": a.out, "scanned": len(cs),
                          "duplicateGroups": len(result.get("duplicates", [])),
                          "incomplete": len(result.get("incomplete", []))}))
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
