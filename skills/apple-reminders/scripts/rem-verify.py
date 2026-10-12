#!/usr/bin/env python3
"""Check stored reminders against what was asked for (an independent read-back).

  rem-verify.py checklist --file todo.md --list Trip [--exact]
      every checklist item is in the list with the same title, due date (all-day or
      timed), completion and priority; --exact also fails on extra reminders
  rem-verify.py ids --id ID [--id ID ...] [--completed yes|no] [--list NAME] [--due DATE|none]
      the reminders exist and have these values

Prints a pass/fail line per item; exit 4 when anything differs, 2 on bad input.
"""
import argparse
import json
import sys

import rem_lib as L


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("checklist")
    c.add_argument("--file", required=True)
    c.add_argument("--list", required=True)
    c.add_argument("--exact", action="store_true", help="the list holds nothing else")
    c.add_argument("--no-bare-dates", action="store_true")
    i = sub.add_parser("ids")
    i.add_argument("--id", action="append", required=True)
    i.add_argument("--completed", choices=["yes", "no"])
    i.add_argument("--list")
    i.add_argument("--due")
    for sp in (c, i):
        sp.add_argument("--format", choices=["text", "json"], default="text")
    a = p.parse_args()

    results = checklist(a) if a.cmd == "checklist" else ids(a)
    ok = all(r["ok"] for r in results)
    if a.format == "json":
        print(json.dumps({"ok": ok, "results": results}, ensure_ascii=False, indent=2))
    else:
        for r in results:
            print(("PASS " if r["ok"] else "FAIL ") + r["what"] + ("" if r["ok"] else f"  {r['detail']}"))
        print(f"{sum(r['ok'] for r in results)}/{len(results)} checks passed.")
    sys.exit(0 if ok else 4)


def checklist(a):
    items = L.parse_checklist(open(a.file, encoding="utf-8").read(), bare_dates=not a.no_bare_dates)
    lst = L.resolve_lists([a.list])[0]
    stored = L.reminders("all", [lst])
    pool = list(stored)
    out = []
    for it in items:
        match = next((r for r in pool if r["title"] == it["title"]), None) \
            or next((r for r in pool if r["title"].casefold() == it["title"].casefold()), None)
        if not match:
            out.append({"ok": False, "what": it["title"], "detail": "not in the list"})
            continue
        pool.remove(match)
        detail = {}
        if match["title"] != it["title"]:
            detail["title"] = [it["title"], match["title"]]
        if not L.same_due(it, match):
            detail["due"] = [L.fmt_due(it) or None, L.fmt_due(match) or None]
        if match["completed"] != it["completed"]:
            detail["completed"] = [it["completed"], match["completed"]]
        if L.priority_band(match["priority"]) != L.priority_band(it["priority"]):
            detail["priority"] = [L.priority_name(it["priority"]), L.priority_name(match["priority"])]
        out.append({"ok": not detail, "what": it["title"], "detail": detail, "id": match["id"]})
    if a.exact:
        out.append({"ok": not pool, "what": f"no other reminders in {lst['title']}",
                    "detail": [r["title"] for r in pool]})
    return out


def ids(a):
    found = {r["id"]: r for r in L.get(a.id, missing_ok=True)}
    lst = L.resolve_lists([a.list])[0] if a.list else None
    want_due = None
    if a.due and a.due.lower() != "none":
        kind, v = L.parse_when(a.due)
        want_due = {"due": v, "allDay": True} if kind == "date" else {"due": v.isoformat(), "allDay": False}
    out = []
    for rid in a.id:
        r = found.get(rid.replace("x-apple-reminder://", ""))
        if not r:
            out.append({"ok": False, "what": rid, "detail": "no such reminder"})
            continue
        detail = {}
        if a.completed and r["completed"] != (a.completed == "yes"):
            detail["completed"] = [a.completed == "yes", r["completed"]]
        if lst and r["listId"] != lst["id"]:
            detail["list"] = [lst["title"], r["list"]]
        if a.due:
            if want_due is None and r.get("due"):
                detail["due"] = [None, r["due"]]
            elif want_due and not L.same_due(want_due, r):
                detail["due"] = [want_due["due"], r.get("due")]
        out.append({"ok": not detail, "what": f"{r['title']} ({rid})", "detail": detail})
    return out


if __name__ == "__main__":
    main()
