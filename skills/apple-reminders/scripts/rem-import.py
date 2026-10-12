#!/usr/bin/env python3
"""Create reminders in bulk from a Markdown or plain-text checklist, then read them back.

  rem-import.py --file todo.md --list "Trip" --create-list --dry-run
  rem-import.py --file todo.md --list "Trip" --create-list
  pbpaste | rem-import.py --list Inbox
  rem-import.py --file plan.md --by-heading          one list per `## Heading`

Items: `- [ ] text`, `- [x] text` (created completed), `- text`, `1. text`. Due dates:
`(due 2026-10-20 14:00)`, `due: fri`, `@due(...)`, `📅 2026-10-20`, or a date at the end
of the line. A date alone makes an all-day reminder; a date with a time is timed and gets
an alert at that time (--no-alerts to skip). Priority: `!high` `!medium` `!low` (or
`!!!` `!!` `!`). Indented plain lines become notes. Nested items are created flat, with
"Subtask of: <parent>" in their notes, because Reminders subtasks aren't scriptable.
An item already in the list with the same title and due date is skipped.
Exit codes: 2 bad input, 3 no access, 4 the read-back differs from the checklist.
"""
import argparse
import json
import sys

import rem_lib as L


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--file", help="checklist file (default: stdin)")
    p.add_argument("--list", help="target list (title, Account/Title or id)")
    p.add_argument("--by-heading", action="store_true",
                   help="each `#` heading names the target list; items before any heading go to --list")
    p.add_argument("--create-list", action="store_true", help="create missing target lists")
    p.add_argument("--account", help="account for new lists (default: the default list's account)")
    p.add_argument("--no-bare-dates", action="store_true",
                   help="don't read a date at the end of a line as the due date")
    p.add_argument("--no-alerts", action="store_true", help="no alert on timed due dates")
    p.add_argument("--allow-duplicate", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="show what would be created, change nothing")
    p.add_argument("--format", choices=["table", "json"], default="table")
    a = p.parse_args()

    text = open(a.file, encoding="utf-8").read() if a.file else sys.stdin.read()
    items = L.parse_checklist(text, bare_dates=not a.no_bare_dates)
    if not items:
        L.die("no checklist items found (want lines like `- [ ] Title (due 2026-10-20)`)", 2)
    for it in items:
        if not it["title"]:
            L.die(f"an item has no title after removing its date/priority: {it}", 2)
        if it["parent"]:
            it["notes"] = (f"Subtask of: {it['parent']}\n" + it["notes"]).strip()

    if not a.dry_run:
        L.require_ek()
    all_lists = L.lists()

    # Target list per item.
    targets = {}
    for it in items:
        name = it["heading"] if a.by_heading and it["heading"] else a.list
        if not name:
            if a.by_heading:
                L.die("items before the first heading need --list", 2)
            dl = L.default_list(all_lists)
            L.warn(f"no --list given: using the default list {L.label(dl)!r}")
            name = dl["id"]
        it["target"] = name
        targets.setdefault(name, None)

    created_lists = []
    for name in targets:
        hits = _find(name, all_lists)
        if hits:
            targets[name] = hits
        elif a.create_list:
            if a.dry_run:
                targets[name] = {"id": None, "title": name, "source": a.account or "(default account)",
                                 "writable": True}
            else:
                args = ["newlist", name] + ([a.account] if a.account else [])
                new = L.ek(*args)
                all_lists.append(new)
                targets[name] = new
                created_lists.append(new)
        else:
            L.die(f"no reminder list named {name!r} (add --create-list to create it)", 2)
        if not targets[name]["writable"]:
            L.die(f"list {L.label(targets[name])!r} is read-only", 2)

    # Duplicates: same title (case-insensitive) and same due date, open or completed.
    existing = {}
    real = [t for t in targets.values() if t["id"]]
    if real and not a.allow_duplicate:
        for r in L.reminders("all", real):
            existing.setdefault(r["listId"], []).append(r)
    specs, plan, skipped = [], [], []
    for it in items:
        lst = targets[it["target"]]
        dupe = next((r for r in existing.get(lst["id"], [])
                     if r["title"].casefold() == it["title"].casefold() and L.same_due(r, it)), None)
        row = {**it, "list": lst["title"], "listId": lst["id"]}
        if dupe:
            skipped.append({**row, "existingId": dupe["id"]})
            continue
        plan.append(row)
        spec = {"title": it["title"], "list": lst["id"], "priority": it["priority"],
                "completed": it["completed"]}
        if it["notes"]:
            spec["notes"] = it["notes"]
        if it["due"]:
            spec["due"] = it["due"]
            if not it["allDay"] and not a.no_alerts:
                spec["alarms"] = [{"absolute": it["due"]}]
        specs.append(spec)

    result = {"dryRun": a.dry_run, "lists": sorted({t["title"] for t in targets.values()}),
              "createdLists": [x["title"] for x in created_lists],
              "toCreate": len(plan), "skippedDuplicates": len(skipped)}
    if a.dry_run or not specs:
        _report(result, plan, skipped, a.format)
        return

    saved = L.ek("save", spec=specs, timeout=300)
    mismatches = []
    for it, back in zip(plan, saved):
        diff = _compare(it, back)
        if diff:
            mismatches.append({"title": it["title"], "id": back.get("id"), "diff": diff})
        it["id"] = back.get("id")
    result["created"] = len(saved)
    result["readback"] = {"ok": not mismatches, "mismatches": mismatches}
    _report(result, plan, skipped, a.format)
    if mismatches:
        sys.exit(4)


def _find(name, all_lists):
    want = name.strip().casefold()
    hits = [x for x in all_lists if want in (x["id"].casefold(), L.label(x).casefold(), x["title"].casefold())]
    hits = hits or [x for x in all_lists if L._bare(x["title"]) == L._bare(name)]
    if len(hits) > 1:
        L.die(f"{name!r} is ambiguous, use one of: " + ", ".join(L.label(x) for x in hits), 2)
    return hits[0] if hits else None


def _compare(it, back):
    diff = {}
    if back.get("missing"):
        return {"missing": True}
    if back["title"] != it["title"]:
        diff["title"] = [it["title"], back["title"]]
    if not L.same_due(it, back):
        diff["due"] = [it["due"], back["due"]]
    if back["completed"] != it["completed"]:
        diff["completed"] = [it["completed"], back["completed"]]
    if L.priority_band(back["priority"]) != L.priority_band(it["priority"]):
        diff["priority"] = [it["priority"], back["priority"]]
    return diff


def _report(result, plan, skipped, fmt):
    if fmt == "json":
        print(json.dumps({**result, "items": plan, "skipped": skipped}, ensure_ascii=False, indent=2))
        return
    verb = "Would create" if result["dryRun"] else "Created"
    print(f"{verb} {len(plan)} reminder(s) in {', '.join(result['lists'])}"
          + (f" (new list: {', '.join(result['createdLists'])})" if result["createdLists"] else "")
          + (f"; skipped {len(skipped)} already there" if skipped else "") + ".")
    print()
    print("| | List | Due | Title | Priority |")
    print("|---|---|---|---|---|")
    for it in plan:
        due = L.fmt_due(it) or ""
        prio = L.priority_name(it["priority"])
        print(f"| {'☑' if it['completed'] else '☐'} | {it['list']} | {due} | {it['title']} | "
              f"{'' if prio == 'none' else prio} |")
    for it in skipped:
        print(f"| = | {it['list']} | {L.fmt_due(it)} | {it['title']} (already there) | |")
    if "readback" in result:
        rb = result["readback"]
        print()
        print("Read-back: OK, every reminder matches the checklist." if rb["ok"]
              else "Read-back MISMATCH:\n" + json.dumps(rb["mismatches"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
