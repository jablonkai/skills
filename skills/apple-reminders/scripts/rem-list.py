#!/usr/bin/env python3
"""List Apple Reminders by list: open, overdue, due today or soon, undated, completed.

  rem-list.py                              every open reminder, grouped by list
  rem-list.py --overdue                    open and past due (all-day: before today)
  rem-list.py --today | --upcoming 7       due today / due within 7 days (overdue excluded)
  rem-list.py --completed --since 2026-01-01 [--until DATE]
  rem-list.py --search invoice [--in-notes] --list Work --format json
  rem-list.py --lists                      the lists with their open and overdue counts

Output is a Markdown table per list (default), JSON or CSV. Read-only.
"""
import argparse
import datetime as dt
import json
import sys

import rem_lib as L


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    what = p.add_mutually_exclusive_group()
    what.add_argument("--open", action="store_true", help="every open reminder (default)")
    what.add_argument("--overdue", action="store_true")
    what.add_argument("--today", action="store_true", help="open and due today")
    what.add_argument("--upcoming", type=int, metavar="DAYS", help="open, due from now to DAYS days ahead")
    what.add_argument("--undated", action="store_true", help="open, without a due date")
    what.add_argument("--completed", action="store_true")
    what.add_argument("--all", action="store_true", help="open and completed")
    what.add_argument("--lists", action="store_true", help="the lists, with open/overdue counts")
    L.add_list_args(p)
    p.add_argument("--since", help="--completed: completed on or after this date")
    p.add_argument("--until", help="--completed: completed before this date")
    p.add_argument("--due-before", help="due before this date (all-day items on that day excluded)")
    p.add_argument("--due-after", help="due on or after this date")
    p.add_argument("--search", help="text to find in titles (case-insensitive)")
    p.add_argument("--regex", action="store_true", help="--search is a regular expression")
    p.add_argument("--in-notes", action="store_true", help="--search also looks in notes")
    p.add_argument("--flagged", action="store_true", help="only flagged (AppleScript: a few s per list)")
    p.add_argument("--priority", choices=["high", "medium", "low"], help="only this priority")
    p.add_argument("--format", choices=["table", "json", "csv"], default="table")
    p.add_argument("--limit", type=int)
    a = p.parse_args()

    all_lists = L.lists()
    chosen = L.lists_from_args(a, all_lists)

    if a.lists:
        rems = L.reminders("open", chosen if (a.list or a.exclude_list) else None)
        at = L.now()
        counts = {}
        for r in rems:
            c = counts.setdefault(r["listId"], [0, 0])
            c[0] += 1
            c[1] += L.state(r, at) == "overdue"
        rows = [{**x, "open": counts.get(x["id"], [0, 0])[0], "overdue": counts.get(x["id"], [0, 0])[1]}
                for x in chosen]
        if a.format == "json":
            print(json.dumps(rows, ensure_ascii=False, indent=2))
        else:
            print("| List | Account | Open | Overdue | Default |")
            print("|---|---|---|---|---|")
            for x in rows:
                print(f"| {x['title']} | {x['source']} | {x['open']} | {x['overdue']} | "
                      f"{'yes' if x.get('default') else ''} |")
        return

    scope = chosen if (a.list or a.exclude_list) else None
    if a.completed:
        lo = _bound(a.since)
        hi = _bound(a.until)
        rems = L.reminders("completed", scope, lo, hi)
    elif a.all:
        rems = L.reminders("all", scope)
    else:
        rems = L.reminders("open", scope)

    at = L.now()
    if a.overdue:
        rems = [r for r in rems if L.state(r, at) == "overdue"]
    elif a.today:
        rems = [r for r in rems if L.state(r, at) == "today"]
    elif a.undated:
        rems = [r for r in rems if L.state(r, at) == "undated"]
    elif a.upcoming is not None:
        horizon = at.date() + dt.timedelta(days=a.upcoming)
        rems = [r for r in rems if L.state(r, at) in ("today", "upcoming")
                and L.due_key(r).date() <= horizon]

    if a.due_before:
        lim = L.due_key(_as_due(a.due_before))
        rems = [r for r in rems if r.get("due") and L.due_key(r) < lim]
    if a.due_after:
        lim = L.due_key(_as_due(a.due_after))
        rems = [r for r in rems if r.get("due") and L.due_key(r) >= lim]
    if a.search:
        m = L.matcher(a.search, a.regex, a.in_notes)
        rems = [r for r in rems if m(r)]
    if a.priority:
        want = L.PRIORITY[a.priority]
        rems = [r for r in rems if L.priority_band(r["priority"]) == want]
    if a.flagged:
        rems = [r for r in L.add_flagged(rems) if r["flagged"]]

    rems.sort(key=lambda r: (L._bare(r["list"]), L.sort_key(r)))
    if a.limit:
        rems = rems[:a.limit]
    sys.stdout.write(L.render(rems, a.format))
    if a.format == "table":
        n_lists = len(L.by_list(rems))
        print(f"{len(rems)} reminder(s) in {n_lists} list(s).")


def _bound(s):
    if not s:
        return None
    kind, v = L.parse_when(s)
    if kind == "date":
        v = dt.datetime.combine(dt.date.fromisoformat(v), dt.time()).astimezone()
    return v.isoformat(timespec="seconds")


def _as_due(s):
    kind, v = L.parse_when(s)
    return {"due": v, "allDay": True} if kind == "date" else {"due": v.isoformat(), "allDay": False}



if __name__ == "__main__":
    main()
