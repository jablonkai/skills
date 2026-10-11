#!/usr/bin/env python3
"""Create, update or delete Apple Calendar events through EventKit, with read-back.

  cal-write.py create --title "Team sync" --start "2026-10-19 10:00" --duration 30 \\
      --calendar Work --repeat weekly --on MO --until 2026-12-21 --alarm 15
  cal-write.py create --title "Holiday" --start 2026-12-24 --end 2026-12-26 --all-day
  cal-write.py update --id ID --start "2026-10-23 09:00" --duration 60       a one-off event
  cal-write.py update --id ID --occurrence "2026-10-26 10:00" --start "2026-10-27 10:00"
  cal-write.py update --id ID --span future --occurrence "2026-11-02 10:00" --title "Sync v2"
  cal-write.py delete --id ID [--occurrence DATE] [--span this|future] --yes

Event ids come from `cal-list.py --format json`. A recurring event has one id for all
its occurrences: --occurrence (the original start) picks one, and --span future applies
the change to it and every later one. --span this is the default when --occurrence is
given; without --occurrence, update and delete act on the whole series.

Alarms: --alarm 15 is 15 minutes before the start (repeatable; 0 = at start, -10 = 10
after), --alarm-at "2026-10-19 08:00" is an absolute time. Exit codes: 0 ok, 2 bad
input or refused, 3 no calendar access, 4 the read-back differs from the request.
"""
import argparse
import datetime as dt
import sys

import cal_lib as L

FREQS = {"daily": "DAILY", "weekly": "WEEKLY", "monthly": "MONTHLY", "yearly": "YEARLY"}


def add_fields(p):
    p.add_argument("--title")
    p.add_argument("--start", help="2026-10-19 10:00, or a date with --all-day")
    p.add_argument("--end", help="end time; for all-day events the last day, inclusive")
    p.add_argument("--duration", type=int, help="minutes, instead of --end")
    p.add_argument("--all-day", action="store_true", default=None)
    p.add_argument("--timed", dest="all_day", action="store_false", help="make an all-day event timed")
    p.add_argument("--calendar", help="title, Source/Title or id (create: default calendar)")
    p.add_argument("--location")
    p.add_argument("--notes")
    p.add_argument("--url")
    p.add_argument("--tz", help="IANA time zone the event is pinned to, e.g. America/New_York")
    p.add_argument("--availability", choices=["busy", "free", "tentative", "unavailable"])
    p.add_argument("--alarm", type=int, action="append", help="minutes before start; repeatable")
    p.add_argument("--alarm-at", action="append", help="absolute alarm time; repeatable")
    p.add_argument("--clear-alarms", action="store_true")
    g = p.add_argument_group("recurrence")
    g.add_argument("--repeat", choices=list(FREQS))
    g.add_argument("--interval", type=int, default=1, help="every N days/weeks/months/years")
    g.add_argument("--on", help="weekdays, e.g. MO,WE,FR; monthly nth weekday: 2TU, -1FR")
    g.add_argument("--count", type=int, help="number of occurrences")
    g.add_argument("--until", help="last date (inclusive)")
    g.add_argument("--rrule", help="a raw RRULE instead of the options above")
    g.add_argument("--no-repeat", action="store_true", help="remove the recurrence")
    p.add_argument("--dry-run", action="store_true", help="print the request, change nothing")


def build_rrule(a):
    if a.no_repeat:
        return ""
    if a.rrule:
        return a.rrule.replace("RRULE:", "").upper()
    if not a.repeat:
        if a.on or a.count or a.until:
            L.die("--on/--count/--until need --repeat", 2)
        return None
    parts = [f"FREQ={FREQS[a.repeat]}"]
    if a.interval > 1:
        parts.append(f"INTERVAL={a.interval}")
    if a.on:
        parts.append("BYDAY=" + a.on.upper().replace(" ", ""))
    if a.count and a.until:
        L.die("use --count or --until, not both", 2)
    if a.count:
        parts.append(f"COUNT={a.count}")
    if a.until:
        parts.append("UNTIL=" + L.parse_when(a.until).strftime("%Y%m%d"))
    return ";".join(parts)


def build_spec(a, cals, existing=None):
    spec = {}
    if a.title is not None:
        spec["title"] = a.title
    all_day = a.all_day if a.all_day is not None else (existing or {}).get("allDay", False)
    if a.all_day is not None:
        spec["allDay"] = a.all_day
    start = L.parse_when(a.start) if a.start else None
    if start is not None:
        spec["start"] = start.date().isoformat() if all_day else L.iso(start)
    # EventKit stores an all-day end as 23:59:59 on the last day, so all-day ends are
    # sent as that last date (inclusive); a timed end is an exact instant.
    base = start or (L.ev_start(existing) if existing else None)
    if a.end:
        end = L.parse_when(a.end)
        spec["end"] = end.date().isoformat() if all_day else L.iso(end)
    elif a.duration:
        if base is None:
            L.die("--duration needs --start", 2)
        spec["end"] = L.iso(base + dt.timedelta(minutes=a.duration))
    elif start is not None and existing:
        # moving an event keeps its length
        if all_day:
            days = (L.ev_last_day(existing) - L.ev_start(existing).date()).days
            spec["end"] = (start.date() + dt.timedelta(days=days)).isoformat()
        else:
            spec["end"] = L.iso(start + (L.ev_end(existing) - L.ev_start(existing)))
    elif start is not None and all_day:
        spec["end"] = start.date().isoformat()
    if a.calendar:
        spec["calendarId"] = L.resolve_calendars([a.calendar], cals, writable=True)[0]["id"]
    for k in ("location", "notes", "url", "availability"):
        if getattr(a, k) is not None:
            spec[k] = getattr(a, k)
    if a.tz:
        spec["timeZone"] = a.tz
    if a.alarm or a.alarm_at or a.clear_alarms:
        spec["alarms"] = [-m for m in a.alarm or []] + [L.iso(L.parse_when(x)) for x in a.alarm_at or []]
    rr = build_rrule(a)
    if rr is not None:
        spec["rrule"] = rr
    return spec


def norm_rule(s):
    r = L.parse_rrule(s)
    r.setdefault("INTERVAL", "1")
    if "UNTIL" in r:
        r["UNTIL"] = r["UNTIL"][:8]
    if "BYDAY" in r:
        r["BYDAY"] = ",".join(sorted(r["BYDAY"].split(",")))
    return r


def compare(spec, ev):
    """Fields the request set that the stored event doesn't match."""
    bad = []
    for k in ("title", "location", "notes", "url", "allDay", "availability"):
        if k in spec and (ev.get(k) or ("" if k != "allDay" else False)) != spec[k]:
            bad.append(f"{k}: wanted {spec[k]!r}, got {ev.get(k)!r}")
    for k in ("start", "end"):
        if k in spec:
            want = L.parse_when(spec[k])
            if ev.get("allDay"):
                ok = want.date() == (L.ev_start(ev).date() if k == "start" else L.ev_last_day(ev))
            else:
                ok = want == L.parse_when(ev[k])
            if not ok:
                bad.append(f"{k}: wanted {spec[k]}, got {ev.get(k + 'Date') or ev[k]}")
    if "rrule" in spec:
        got = (ev.get("rrule") or [""])[0]
        if (norm_rule(spec["rrule"]) if spec["rrule"] else {}) != (norm_rule(got) if got else {}):
            bad.append(f"rrule: wanted {spec['rrule'] or 'none'}, got {got or 'none'}")
    if "alarms" in spec:
        want = sorted(str(x) for x in spec["alarms"])
        have = []
        for x in ev.get("alarms") or []:
            have.append(str(x["offsetMinutes"]) if "offsetMinutes" in x else str(x["absolute"]))
        if want != sorted(have):
            bad.append(f"alarms: wanted {want}, got {sorted(have)}")
    return bad


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create", help="new event")
    add_fields(c)
    c.add_argument("--allow-duplicate", action="store_true",
                   help="create even if the calendar has an event with this title at this start")
    u = sub.add_parser("update", help="change an event, one occurrence or the rest of a series")
    u.add_argument("--id", required=True)
    u.add_argument("--occurrence", help="original start of the occurrence to change")
    u.add_argument("--span", choices=["this", "future"])
    add_fields(u)
    d = sub.add_parser("delete", help="remove an event, one occurrence or the rest of a series")
    d.add_argument("--id", required=True)
    d.add_argument("--occurrence")
    d.add_argument("--span", choices=["this", "future"])
    d.add_argument("--yes", action="store_true", help="really delete (otherwise: show what would go)")
    a = p.parse_args()

    if a.cmd == "delete":
        ev = L.get_event(a.id, a.occurrence)
        span = a.span or ("this" if a.occurrence or not ev.get("recurring") else "future")
        what = ("the whole series" if ev.get("recurring") and span == "future" and not a.occurrence
                else "this and every later occurrence" if span == "future" and ev.get("recurring")
                else "this occurrence" if ev.get("recurring") else "the event")
        if not a.yes:
            L.write_json({"wouldDelete": what, "event": ev, "hint": "re-run with --yes to delete"})
            sys.exit(2)
        args = ["delete", a.id] + ([L.iso(L.parse_when(a.occurrence))] if a.occurrence else []) + [span]
        res = L.ek(*args)
        res["scope"] = what
        return L.write_json(res)

    cals = L.calendars()
    existing = L.get_event(a.id, a.occurrence) if a.cmd == "update" else None
    spec = build_spec(a, cals, existing)
    if a.cmd == "create":
        if not a.title or not a.start:
            L.die("create needs --title and --start", 2)
        cal = L.resolve_calendars([a.calendar], cals, writable=True)[0] if a.calendar else L.default_calendar(cals)
        spec["calendarId"] = cal["id"]
        if not a.allow_duplicate and not a.dry_run:
            s = L.parse_when(spec["start"])
            same = [e for e in L.events(s, s + dt.timedelta(minutes=1), [cal["id"]], cals)
                    if e["title"] == a.title and L.ev_start(e) == s]
            if same:
                L.write_json({"refused": "an event with this title already starts then in this calendar",
                              "existing": same[0], "hint": "--allow-duplicate to add it anyway"})
                sys.exit(2)
    else:
        if not spec:
            L.die("nothing to change", 2)
        spec["id"] = a.id
        if a.occurrence:
            spec["occurrence"] = L.iso(L.parse_when(a.occurrence))
        spec["span"] = a.span or ("this" if a.occurrence or not existing.get("recurring") else "future")

    if a.dry_run:
        return L.write_json({"dryRun": True, "action": a.cmd, "request": spec,
                             "current": existing})
    res = L.ek("save", spec=spec)
    ev = res.get("event")
    bad = compare(spec, ev) if ev else ["could not read the event back (write-only calendar access)"]
    res["readback"] = {"ok": not bad, "mismatches": bad}
    L.write_json(res)
    if bad:
        sys.exit(4)
    return None


if __name__ == "__main__":
    main()
