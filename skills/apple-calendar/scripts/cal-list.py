#!/usr/bin/env python3
"""List Apple Calendar events in a period, recurring occurrences included. Read-only.

  cal-list.py --week next                         Markdown table, all calendars
  cal-list.py --from 2026-10-20 --to 2026-10-24 --calendar Work --calendar Home
  cal-list.py --month 2026-11 --format json|csv
  cal-list.py --calendars                         the calendars, with ids and writability
  cal-list.py --search dentist --days 90          title/location/notes contain the text
"""
import argparse
import csv
import sys

import cal_lib as L

CSV_FIELDS = ["start", "end", "allDay", "title", "calendar", "source", "location", "notes",
              "url", "recurring", "rrule", "alarms", "id", "occurrence"]


def table(evs, start, end):
    lines = [f"Events {start:%a %d %b %Y} – {(end - L.dt.timedelta(seconds=1)):%a %d %b %Y} "
             f"({len(evs)})", "",
             "| Date | Time | Title | Calendar | Location |", "|---|---|---|---|---|"]
    for e in evs:
        s = L.ev_start(e)
        title = e["title"] + (" ↻" if e.get("recurring") or e.get("detached") else "")
        lines.append(f"| {s:%a %d %b} | {L.when_text(e)} | {L.md_cell(title)} | "
                     f"{L.md_cell(e['calendar'])} | {L.md_cell(e.get('location'))} |")
    if not evs:
        lines.append("| | | (no events) | | |")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    L.add_range_args(p)
    p.add_argument("--calendar", action="append", help="title, Source/Title or id; repeatable (default: all)")
    p.add_argument("--exclude-calendar", action="append", default=[], help="skip these; repeatable")
    p.add_argument("--search", help="case-insensitive text in title, location or notes")
    p.add_argument("--no-all-day", action="store_true", help="leave all-day events out")
    p.add_argument("--format", choices=["table", "json", "csv"], default="table")
    p.add_argument("--calendars", action="store_true", help="list calendars instead of events")
    a = p.parse_args()

    cals = L.calendars()
    if a.calendars:
        if a.format == "json":
            return L.write_json(cals)
        print("| Calendar | Account | Type | Writable | Id |\n|---|---|---|---|---|")
        for c in sorted(cals, key=lambda c: (c["source"], c["title"])):
            star = " (default)" if c.get("default") else ""
            print(f"| {L.md_cell(c['title'])}{star} | {L.md_cell(c['source'])} | {c['type']} | "
                  f"{'yes' if c['writable'] else 'no'} | {c['id']} |")
        return None

    start, end = L.range_from_args(a)
    evs = L.events(start, end, a.calendar, cals)
    if a.exclude_calendar:
        skip = {c["id"] for c in L.resolve_calendars(a.exclude_calendar, cals)}
        evs = [e for e in evs if e["calendarId"] not in skip]
    if a.no_all_day:
        evs = [e for e in evs if not e.get("allDay")]
    if a.search:
        q = a.search.lower()
        evs = [e for e in evs if q in " ".join(str(e.get(k) or "") for k in ("title", "location", "notes")).lower()]

    if a.format == "json":
        return L.write_json({"from": L.iso(start), "to": L.iso(end), "count": len(evs), "events": evs})
    if a.format == "csv":
        w = csv.DictWriter(sys.stdout, CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        for e in evs:
            row = dict(e, rrule=";".join(e.get("rrule") or []),
                       alarms=" ".join(str(x.get("offsetMinutes", x.get("absolute"))) for x in e.get("alarms") or []))
            w.writerow(row)
        return None
    print(table(evs, start, end))
    return None


if __name__ == "__main__":
    main()
