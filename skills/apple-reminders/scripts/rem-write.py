#!/usr/bin/env python3
"""Create, change, complete, move and delete Apple Reminders, each change read back.

  rem-write.py create --title "Call Anna" --due "fri 9:30" --list Work [--priority high]
               [--notes N] [--url U] [--alert "2026-10-16 09:00" | --no-alert]
               [--repeat weekly [--interval 2] [--count 5 | --until DATE]] [--flag]
  rem-write.py update --id ID [--title T] [--due DATE|none] [--priority P] [--notes N] [--flag|--unflag]
  rem-write.py complete   --match invoice --list Bills          preview: what would change
  rem-write.py complete   --match invoice --list Bills --yes    do it
  rem-write.py uncomplete --id ID
  rem-write.py flag --overdue --match "" --list Home --yes      (flagged goes through AppleScript)
  rem-write.py move   --match "trip" --list Inbox --to Travel [--create-list] --yes
  rem-write.py delete --completed --completed-before 2025-10-01 --list Groceries --yes

Selecting: --id (repeatable) or --match TEXT [--regex] [--in-notes], narrowed by --list,
--overdue, --due-before, --completed/--any-state. A --match selection only previews
until --yes is added; delete always previews until --yes. Exit codes: 2 bad input or
nothing matched, 3 no access, 4 the read-back differs from the request.
"""
import argparse
import datetime as dt
import json
import sys

import rem_lib as L


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def fields(sp):
        sp.add_argument("--title")
        sp.add_argument("--due", help="date, date + time, or 'none' to clear")
        sp.add_argument("--priority", choices=["none", "high", "medium", "low"])
        sp.add_argument("--notes")
        sp.add_argument("--url")
        sp.add_argument("--alert", help="alert at this date/time (default for a timed due: at the due time)")
        sp.add_argument("--alert-before", type=int, metavar="MIN", help="alert MIN minutes before the due time")
        sp.add_argument("--no-alert", action="store_true")
        sp.add_argument("--repeat", choices=["none", "daily", "weekly", "monthly", "yearly"])
        sp.add_argument("--interval", type=int, default=1)
        sp.add_argument("--count", type=int)
        sp.add_argument("--until")
        flag = sp.add_mutually_exclusive_group()
        flag.add_argument("--flag", action="store_true", help="flag it (AppleScript, a few seconds)")
        flag.add_argument("--unflag", action="store_true")

    c = sub.add_parser("create")
    fields(c)
    c.add_argument("--list", help="target list (default: the default list, named in the output)")
    c.add_argument("--allow-duplicate", action="store_true")
    c.add_argument("--create-list", action="store_true", help="create --list if missing (default account)")

    u = sub.add_parser("update")
    fields(u)
    u.add_argument("--id", action="append", required=True)

    for name in ("complete", "uncomplete", "move", "delete", "flag", "unflag"):
        sp = sub.add_parser(name)
        sp.add_argument("--id", action="append", default=[])
        sp.add_argument("--match", help="text in the title (case-insensitive)")
        sp.add_argument("--regex", action="store_true")
        sp.add_argument("--in-notes", action="store_true", help="--match also looks in notes")
        L.add_list_args(sp)
        sp.add_argument("--overdue", action="store_true", help="only overdue reminders")
        sp.add_argument("--due-before", help="only due before this date")
        state = sp.add_mutually_exclusive_group()
        state.add_argument("--completed", action="store_true", help="select completed reminders")
        state.add_argument("--any-state", action="store_true", help="select open and completed")
        sp.add_argument("--completed-before", help="with --completed: completed before this date")
        sp.add_argument("--yes", action="store_true", help="apply (otherwise a --match selection only previews)")
        if name == "move":
            sp.add_argument("--to", required=True, help="destination list")
            sp.add_argument("--create-list", action="store_true",
                            help="create --to if missing, in the account of the reminders being moved")
    for sp in sub.choices.values():
        sp.add_argument("--format", choices=["text", "json"], default="text")
    a = p.parse_args()

    L.require_ek()
    {"create": create, "update": update}.get(a.cmd, bulk)(a)


# ---- create / update --------------------------------------------------------------

def spec_from_args(a, current=None):
    spec = {}
    if a.title is not None:
        spec["title"] = a.title
    if a.notes is not None:
        spec["notes"] = a.notes
    if a.url is not None:
        spec["url"] = a.url
    if a.priority:
        spec["priority"] = L.PRIORITY[a.priority]
    due = current.get("due") if current else None
    all_day = current.get("allDay") if current else False
    if a.due is not None:
        if a.due.lower() == "none":
            spec["due"], due = None, None
        else:
            due = L.when_to_due(a.due)
            all_day = len(due) == 10
            spec["due"] = due
    if a.no_alert:
        spec["alarms"] = []
    elif a.alert:
        spec["alarms"] = [{"absolute": _timed(a.alert)}]
    elif a.alert_before is not None:
        if not due or all_day:
            L.die("--alert-before needs a due date with a time", 2)
        spec["alarms"] = [{"offsetMinutes": -a.alert_before}]
    elif a.due is not None and due and not all_day:
        spec["alarms"] = [{"absolute": due}]   # what the Reminders app does for a timed due
    elif a.due is not None:
        spec["alarms"] = []                      # all-day or cleared due: drop the old time alert
    if a.repeat:
        if a.repeat == "none":
            spec["repeat"] = None
        else:
            if not due:
                L.die("--repeat needs a due date", 2)
            rr = {"freq": a.repeat.upper(), "interval": a.interval}
            if a.count:
                rr["count"] = a.count
            if a.until:
                rr["until"] = _timed(a.until, end_of_day=True)
            spec["repeat"] = rr
    return spec


def _timed(s, end_of_day=False):
    kind, v = L.parse_when(s)
    if kind == "date":
        t = dt.time(23, 59) if end_of_day else dt.time(9, 0)
        v = dt.datetime.combine(dt.date.fromisoformat(v), t).astimezone()
    return v.isoformat(timespec="seconds")


def create(a):
    if not a.title:
        L.die("create needs --title", 2)
    all_lists = L.lists()
    if a.list and a.create_list and not find_list(a.list, all_lists):
        lst = L.ek("newlist", a.list)
        print(f"Created list {L.label(lst)}")
    else:
        lst = L.resolve_lists([a.list], all_lists, writable=True)[0] if a.list else L.default_list(all_lists)
    spec = {**spec_from_args(a), "list": lst["id"]}
    if not a.allow_duplicate:
        for r in L.reminders("open", [lst]):
            if r["title"].casefold() == a.title.casefold() and L.same_due(r, {"due": spec.get("due"),
                                                                             "allDay": len(spec.get("due") or "") == 10}):
                L.die(f"an open reminder {a.title!r} with that due date is already in {L.label(lst)} "
                      f"(id {r['id']}); use --allow-duplicate to add another", 2)
    back = L.ek("save", spec=spec)
    if a.flag:
        L.set_flagged([back], True)
        back["flagged"] = True
    finish(a, [(spec, back)], f"Created in {L.label(lst)}")


def update(a):
    currents = L.get(a.id)
    pairs = []
    for cur in currents:
        spec = {**spec_from_args(a, cur), "id": cur["id"]}
        pairs.append((spec, None))
    saved = L.ek("save", spec=[s for s, _ in pairs]) if any(len(s) > 1 for s, _ in pairs) else currents
    pairs = [(s, b) for (s, _), b in zip(pairs, saved)]
    if a.flag or a.unflag:
        L.set_flagged([b for _, b in pairs], bool(a.flag))
        for _, b in pairs:
            b["flagged"] = bool(a.flag)
    finish(a, pairs, "Updated")


# ---- bulk: complete / uncomplete / move / delete ----------------------------------------

def select(a, all_lists):
    if a.id:
        rems = L.get(a.id)
    elif a.match is not None:   # "" selects everything in --list
        if not a.match and not a.list:
            L.die('--match "" selects everything: name the list with --list', 2)
        scope = L.lists_from_args(a, all_lists)
        kind = "completed" if a.completed else "all" if a.any_state else "open"
        if a.cmd == "uncomplete" and not a.any_state:
            kind = "completed"
        hi = L.day_start(a.completed_before) if a.completed_before else None
        rems = L.reminders(kind, scope if (a.list or a.exclude_list) else None, None, hi)
        m = L.matcher(a.match, a.regex, a.in_notes)
        rems = [r for r in rems if m(r)]
    elif a.completed and a.list:
        hi = L.day_start(a.completed_before) if a.completed_before else None
        rems = L.reminders("completed", L.lists_from_args(a, all_lists), None, hi)
    else:
        L.die("select reminders with --id, --match, or --completed --list (for cleanup)", 2)
    if a.overdue:
        rems = [r for r in rems if L.state(r) == "overdue"]
    if a.due_before:
        kind, v = L.parse_when(a.due_before)
        lim = L.due_key({"due": v, "allDay": True} if kind == "date" else {"due": v.isoformat()})
        rems = [r for r in rems if r.get("due") and L.due_key(r) < lim]
    return sorted(rems, key=lambda r: (L._bare(r["list"]), L.sort_key(r)))


def bulk(a):
    all_lists = L.lists()
    rems = select(a, all_lists)
    if not rems:
        L.die("nothing matched; no change made", 2)
    dest = None
    if a.cmd == "move":
        dest = find_list(a.to, all_lists)
        if dest is None and a.create_list:
            accounts = sorted({r["source"] for r in rems})
            if len(accounts) > 1:
                L.die(f"the reminders are in several accounts ({', '.join(accounts)}): create {a.to!r} first", 2)
            if a.yes or a.id:
                dest = L.ek("newlist", a.to, accounts[0])
                print(f"Created list {L.label(dest)}")
            else:
                dest = {"id": None, "title": a.to, "source": accounts[0], "writable": True}
        elif dest is None:
            L.resolve_lists([a.to], all_lists)  # dies with the known names
        if not dest["writable"]:
            L.die(f"list {L.label(dest)!r} is read-only", 2)
    if a.cmd == "complete":
        skip = [r for r in rems if r["completed"]]
        rems = [r for r in rems if not r["completed"]]
    elif a.cmd == "uncomplete":
        skip = [r for r in rems if not r["completed"]]
        rems = [r for r in rems if r["completed"]]
    elif a.cmd == "move":
        skip = [r for r in rems if r["listId"] == dest["id"]]
        rems = [r for r in rems if r["listId"] != dest["id"]]
    elif a.cmd in ("flag", "unflag"):
        L.add_flagged(rems)
        want = a.cmd == "flag"
        skip = [r for r in rems if r["flagged"] == want]
        rems = [r for r in rems if r["flagged"] != want]
    else:
        skip = []
    needs_yes = a.cmd == "delete" or not a.id
    if needs_yes and not a.yes:
        preview(a, rems, skip, dest)
        return
    if not rems:
        print(f"Nothing to {a.cmd}: all {len(skip)} matched reminder(s) already are.")
        return
    if a.cmd == "delete":
        out = L.ek("delete", *[r["id"] for r in rems])
        gone = L.get(out["deleted"], missing_ok=True)
        if gone:
            L.die("some reminders are still there after delete: " + json.dumps(gone, ensure_ascii=False), 4)
        _print(a, {"deleted": len(rems), "items": [_brief(r) for r in rems]},
               f"Deleted {len(rems)} reminder(s):", rems)
        return
    if a.cmd in ("flag", "unflag"):
        want = a.cmd == "flag"
        L.set_flagged(rems, want)
        back = L.add_flagged([{k: v for k, v in r.items() if k != "flagged"} for r in rems])
        wrong = [r["title"] for r in back if r["flagged"] != want]
        out = {"action": a.cmd, "count": len(back), "items": [_brief(r) for r in back],
               "readback": {"ok": not wrong, "mismatches": wrong}}
        _print(a, out, f"{'Flagged' if want else 'Unflagged'}: {len(back)} reminder(s)", back)
        if skip:
            print(f"Left alone (already in that state): {len(skip)}")
        sys.exit(4 if wrong else 0)
    if a.cmd == "move":
        specs = [{"id": r["id"], "list": dest["id"]} for r in rems]
    else:
        specs = [{"id": r["id"], "completed": a.cmd == "complete"} for r in rems]
    saved = L.ek("save", spec=specs, timeout=300)
    finish(a, list(zip(specs, saved)), {"complete": "Completed", "uncomplete": "Reopened",
                                        "move": f"Moved to {L.label(dest) if dest else ''}"}[a.cmd],
           skipped=skip, before={r["id"]: r for r in rems})


def find_list(name, all_lists):
    """The list called name, None when there is none (ambiguous names still die)."""
    want = name.strip().casefold()
    hits = [x for x in all_lists if want in (x["id"].casefold(), L.label(x).casefold(), x["title"].casefold())]
    hits = hits or [x for x in all_lists if L._bare(x["title"]) == L._bare(name)]
    if len(hits) > 1:
        L.die(f"{name!r} is ambiguous, use one of: " + ", ".join(L.label(x) for x in hits), 2)
    return hits[0] if hits else None


def preview(a, rems, skip, dest):
    what = {"complete": "complete", "uncomplete": "reopen", "delete": "DELETE", "move": "move",
            "flag": "flag", "unflag": "unflag"}[a.cmd]
    where = f" to {L.label(dest)}" + (" (new list)" if not dest["id"] else "") if dest else ""
    if a.format == "json":
        print(json.dumps({"preview": True, "action": a.cmd, "count": len(rems),
                          "items": [_brief(r) for r in rems], "unchanged": [_brief(r) for r in skip]},
                         ensure_ascii=False, indent=2))
        return
    print(f"PREVIEW, nothing changed: would {what} {len(rems)} reminder(s){where}. Re-run with --yes to apply.")
    print()
    sys.stdout.write(L.render(rems))
    if skip:
        print(f"Already in the target state, left alone: {len(skip)} ("
              + ", ".join(r["title"] for r in skip[:10]) + (" …" if len(skip) > 10 else "") + ")")


# ---- read-back ------------------------------------------------------------------------

def finish(a, pairs, verb, skipped=(), before=None):
    mismatches, advanced = [], []
    for spec, back in pairs:
        diff = compare(spec, back)
        if diff and advanced_to_next(spec, back, (before or {}).get(back.get("id"))):
            advanced.append(_brief(back))
            continue
        if diff:
            mismatches.append({"id": back.get("id"), "title": back.get("title"), "diff": diff})
    backs = [b for _, b in pairs]
    out = {"action": a.cmd, "count": len(backs), "items": backs,
           "unchanged": [_brief(r) for r in skipped],
           "readback": {"ok": not mismatches, "mismatches": mismatches}}
    if advanced:
        out["advanced"] = advanced
    _print(a, out, f"{verb}: {len(backs)} reminder(s)", backs)
    if advanced and a.format != "json":
        print(f"Repeating: {len(advanced)} moved on to the next due date (same id); the done "
              "occurrence is kept as a separate completed reminder.")
    if skipped:
        print(f"Left alone (already in that state): {len(skipped)}")
    if mismatches:
        sys.exit(4)


def compare(spec, back):
    if back is None or back.get("missing"):
        return {"missing": True}
    diff = {}
    for k in ("title", "notes", "url"):
        if k in spec and (spec[k] or "") != (back.get(k) or ""):
            diff[k] = [spec[k], back.get(k)]
    if "list" in spec and spec["list"] != back["listId"]:
        diff["list"] = [spec["list"], back["listId"]]
    if "priority" in spec and L.priority_band(spec["priority"]) != L.priority_band(back["priority"]):
        diff["priority"] = [spec["priority"], back["priority"]]
    if "completed" in spec and spec["completed"] != back["completed"]:
        diff["completed"] = [spec["completed"], back["completed"]]
    if "due" in spec:
        want = {"due": spec["due"], "allDay": len(spec["due"] or "") == 10}
        if not L.same_due(want, back):
            diff["due"] = [spec["due"], back["due"]]
    if "alarms" in spec and len(spec["alarms"]) != len(back.get("alarms", [])):
        diff["alarms"] = [spec["alarms"], back.get("alarms")]
    if "repeat" in spec and bool(spec["repeat"]) != bool(back.get("repeat")):
        diff["repeat"] = [spec["repeat"], back.get("repeat")]
    return diff


def advanced_to_next(spec, back, orig):
    """Completing a repeating reminder keeps its id open with the next due date, and
    Reminders stores the done occurrence as a new completed reminder."""
    return bool(spec.get("completed") and orig and orig.get("repeat") and back.get("repeat")
                and not back.get("completed") and orig.get("due") and back.get("due")
                and not L.same_due(orig, back))


def _brief(r):
    return {k: r.get(k) for k in ("id", "title", "list", "due", "allDay", "completed", "priority")}


def _print(a, out, headline, rems):
    if a.format == "json":
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    print(headline)
    print()
    sys.stdout.write(L.render(rems))
    rb = out.get("readback")
    if rb is not None:
        print("Read-back: OK, the stored reminders match the request." if rb["ok"]
              else "Read-back MISMATCH:\n" + json.dumps(rb["mismatches"], ensure_ascii=False, indent=2))
    if any(r.get("id") for r in rems) and a.cmd in ("create", "update"):
        print("ids: " + ", ".join(r["id"] for r in rems))


if __name__ == "__main__":
    main()
