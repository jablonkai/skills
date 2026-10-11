#!/usr/bin/env python3
"""Find free slots in Apple Calendar. Read-only.

  cal-free.py --week next --min 60                  free hours next week, 09:00-17:00, Mon-Fri
  cal-free.py --from "2026-10-15 13:00" --to "2026-10-15 18:00" --min 30
  cal-free.py --days 3 --hours 08:00-19:00 --weekends --calendar Work --format json

Busy time is every timed event in the chosen calendars, except events marked "free"
(availability) and events the user declined. All-day events block nothing unless
--all-day-busy is given: holidays, birthdays and trips are usually all-day.
"""
import argparse
import datetime as dt

import cal_lib as L


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    L.add_range_args(p)
    p.add_argument("--min", type=int, default=30, help="shortest slot worth listing, minutes (default 30)")
    p.add_argument("--hours", default="09:00-17:00", help="working hours each day (default 09:00-17:00)")
    p.add_argument("--weekends", action="store_true", help="include Saturday and Sunday")
    p.add_argument("--calendar", action="append", help="calendars that count as busy (default: all)")
    p.add_argument("--exclude-calendar", action="append", default=[], help="calendars to ignore")
    p.add_argument("--all-day-busy", action="store_true", help="all-day events block the whole day")
    p.add_argument("--format", choices=["table", "json"], default="table")
    a = p.parse_args()

    try:
        h0, h1 = [dt.time.fromisoformat(x) for x in a.hours.split("-")]
    except ValueError:
        L.die("--hours wants HH:MM-HH:MM", 2)
    start, end = L.range_from_args(a)
    start = max(start, L.now())  # free time in the past is no use
    cals = L.calendars()
    evs = L.events(start, end, a.calendar, cals)
    if a.exclude_calendar:
        skip = {c["id"] for c in L.resolve_calendars(a.exclude_calendar, cals)}
        evs = [e for e in evs if e["calendarId"] not in skip]

    busy = []
    for e in evs:
        if e.get("availability") == "free" or (e.get("allDay") and not a.all_day_busy):
            continue
        if any(x.get("status") == "declined" and x.get("self") for x in e.get("attendees") or []):
            continue
        busy.append((L.ev_start(e), L.ev_end(e), e["title"]))
    busy.sort()

    slots = []
    day = start.date()
    while L.start_of_day(day) < end:
        if a.weekends or day.weekday() < 5:
            w0 = max(start, dt.datetime.combine(day, h0, L.LOCAL_TZ))
            w1 = min(end, dt.datetime.combine(day, h1, L.LOCAL_TZ))
            cur = w0
            for b0, b1, _ in busy:
                if b1 <= cur or b0 >= w1:
                    continue
                if b0 > cur:
                    slots.append((cur, b0))
                cur = max(cur, b1)
            if cur < w1:
                slots.append((cur, w1))
        day += dt.timedelta(days=1)
    slots = [(s, t) for s, t in slots if (t - s) >= dt.timedelta(minutes=a.min)]

    if a.format == "json":
        return L.write_json({"from": L.iso(start), "to": L.iso(end), "hours": a.hours, "minMinutes": a.min,
                             "busyEvents": len(busy),
                             "slots": [{"start": L.iso(s), "end": L.iso(t),
                                        "minutes": int((t - s).total_seconds() // 60)} for s, t in slots]})
    print(f"Free slots ≥ {a.min} min, {a.hours}{'' if a.weekends else ', Mon–Fri'} "
          f"({len(busy)} busy events considered)\n")
    print("| Day | From | To | Length |\n|---|---|---|---|")
    for s, t in slots:
        mins = int((t - s).total_seconds() // 60)
        print(f"| {s:%a %d %b} | {s:%H:%M} | {t:%H:%M} | {mins // 60}h {mins % 60:02d}m |")
    if not slots:
        print("| (none) | | | |")
    return None


if __name__ == "__main__":
    main()
