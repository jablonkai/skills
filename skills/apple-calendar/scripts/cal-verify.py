#!/usr/bin/env python3
"""Check Apple Calendar against what was asked for. Read-only. Exit 4 on any mismatch.

  cal-verify.py event --id ID [--occurrence DATE] --title "Team sync" \\
      --start "2026-10-19 10:00" --end "2026-10-19 10:30" --rrule "FREQ=WEEKLY;BYDAY=MO" --alarm 15
  cal-verify.py ics --file nov.ics --month 2026-11 [--calendar Work]

`event` compares the stored event with the given fields (the same comparison cal-write
runs after every save). `ics` parses the file, counts its VEVENTs, and checks that each
UID/DTSTART pair exists in the store, and that every series in the period is in the file.
"""
import argparse
import importlib
import re
import sys
from pathlib import Path

import cal_lib as L
import ics_lib as I

writer = importlib.import_module("cal-write")


def verify_event(a):
    ev = L.get_event(a.id, a.occurrence)
    a.calendar = None
    spec = writer.build_spec(a, L.calendars(), ev)
    spec.pop("calendarId", None)
    bad = writer.compare(spec, ev)
    if a.calendar_name and ev["calendar"] != a.calendar_name:
        bad.append(f"calendar: wanted {a.calendar_name!r}, got {ev['calendar']!r}")
    return {"ok": not bad, "checked": sorted(spec), "mismatches": bad, "event": ev}


def verify_ics(a):
    comps = I.parse(Path(a.file).read_text(encoding="utf-8", errors="replace"))
    start, end = L.range_from_args(a)
    evs = L.events(start, end, a.calendar)
    store = {}
    for e in evs:
        uid = L.series_key(e, "externalId")
        store.setdefault(uid, set()).add(L.ev_start(e))
        for k in ("seriesStart", "occurrence"):
            if e.get(k):
                store[uid].add(L.parse_when(e[k]))
    problems, file_uids, recurring = [], set(), 0
    for c in comps:
        uid = I.first(c, "UID", "")[1].split("/RID=")[0]
        if uid not in store:  # occurrences mode: <series uid>-<YYYYMMDDTHHMMSS>
            uid = re.sub(r"-\d{8}T\d{6}$", "", uid)
        file_uids.add(uid)
        title = I.unesc(I.first(c, "SUMMARY", "")[1])
        if not c.get("DTSTART"):
            problems.append(f"{title}: no DTSTART")
            continue
        recurring += bool(c.get("RRULE"))
        d, is_date = I.parse_dt(*c["DTSTART"][0])
        when = L.start_of_day(d) if is_date else d
        if uid not in store:
            # a series that began before the period only shows up by its later occurrences
            problems.append(f"{title} ({uid}): not found in the calendar store for this period")
        elif when not in store[uid] and not c.get("RRULE") and not c.get("RECURRENCE-ID"):
            problems.append(f"{title}: DTSTART {L.iso(when)} differs from the store "
                            f"({', '.join(sorted(L.iso(x) for x in store[uid]))})")
    missing = sorted({e["title"] for e in evs if L.series_key(e, "externalId") not in file_uids})
    for t in missing:
        problems.append(f"{t}: in the calendar for this period but not in the file")
    occ_ok = None
    if not any(c.get("RRULE") or c.get("RECURRENCE-ID") for c in comps):
        occ_ok = len(comps) == len(evs)
        if not occ_ok:
            problems.append(f"{len(comps)} VEVENTs but {len(evs)} occurrences in the store")
    return {"ok": not problems, "file": str(Path(a.file).resolve()), "vevents": len(comps),
            "recurringSeries": recurring, "storeOccurrences": len(evs), "occurrenceCountMatches": occ_ok,
            "problems": problems}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("event", help="compare a stored event with expected fields")
    e.add_argument("--id", required=True)
    e.add_argument("--occurrence")
    e.add_argument("--calendar-name", help="expected calendar title")
    writer.add_fields(e)
    i = sub.add_parser("ics", help="check an exported .ics file against the store")
    i.add_argument("--file", required=True)
    L.add_range_args(i)
    i.add_argument("--calendar", action="append")
    a = p.parse_args()
    res = verify_event(a) if a.cmd == "event" else verify_ics(a)
    L.write_json(res)
    sys.exit(0 if res["ok"] else 4)


if __name__ == "__main__":
    main()
