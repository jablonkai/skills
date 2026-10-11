#!/usr/bin/env python3
"""Export Apple Calendar events to .ics or CSV, or import an .ics file. Calendar.app has
no scripted export or import, so this writes and reads RFC 5545 itself.

  cal-ics.py export --month 2026-11 --out nov.ics                 all calendars
  cal-ics.py export --from 2026-11-01 --to 2026-11-30 --calendar Work --out work.ics
  cal-ics.py export --month 2026-11 --mode occurrences --out flat.ics
  cal-ics.py export --week next --out week.csv                    CSV by file extension
  cal-ics.py import --file invite.ics --calendar Work --dry-run    then without --dry-run

Export modes: `series` (default) writes each recurring event once, with its RRULE,
EXDATEs for occurrences deleted inside the period, and RECURRENCE-ID overrides for
moved ones, the way Calendar's own export does. `occurrences` writes one plain VEVENT per
occurrence in the period, which is what spreadsheets and simple importers want.
The JSON summary on stdout gives both counts; quote the one that matches the file.
"""
import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path

import cal_lib as L
import ics_lib as I


def export(a):
    start, end = L.range_from_args(a)
    cals = L.calendars()
    evs = L.events(start, end, a.calendar, cals)
    if a.exclude_calendar:
        skip = {c["id"] for c in L.resolve_calendars(a.exclude_calendar, cals)}
        evs = [e for e in evs if e["calendarId"] not in skip]
    out = Path(a.out)
    summary = {"file": str(out.resolve()), "from": L.iso(start), "to": L.iso(end),
               "occurrences": len(evs), "calendars": sorted({e["calendar"] for e in evs})}

    if out.suffix.lower() == ".csv":
        import importlib
        lister = importlib.import_module("cal-list")
        with out.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, lister.CSV_FIELDS, extrasaction="ignore")
            w.writeheader()
            for e in evs:
                w.writerow(dict(e, rrule=";".join(e.get("rrule") or []),
                                alarms=" ".join(str(x.get("offsetMinutes", x.get("absolute")))
                                                for x in e.get("alarms") or [])))
        summary.update(format="csv", rows=len(evs))
        return summary

    stamp = I.utc(L.now())
    vevents, tzids = [], set()
    if a.mode == "occurrences":
        for e in evs:
            uid = L.series_key(e, "externalId")
            if e.get("recurring") or e.get("detached"):
                uid = f"{uid}-{L.ev_start(e):%Y%m%dT%H%M%S}"
            vevents.append(I.vevent(e, stamp, uid=uid))
            if e.get("timeZone") and not e.get("allDay"):
                tzids.add(e["timeZone"])
        summary.update(mode="occurrences", vevents=len(vevents))
    else:
        series, singles, overrides = {}, [], []
        for e in evs:
            if e.get("recurring"):
                series.setdefault(e["id"], []).append(e)
            elif e.get("detached"):
                overrides.append(e)
            else:
                singles.append(e)
        for e in singles:
            vevents.append(I.vevent(e, stamp))
        for sid, occs in series.items():
            first = occs[0]
            master = dict(first, start=first.get("seriesStart", first["start"]),
                          end=first.get("seriesEnd", first["end"]))
            rrule = (first.get("rrule") or [""])[0]
            # Occurrences the rule produces inside the period but EventKit didn't return
            # were deleted (or moved: those come back as detached overrides).
            seen = {L.ev_start(o) for o in occs} | {L.parse_when(o["occurrence"]) for o in overrides
                                                   if L.series_key(o) == sid and o.get("occurrence")}
            expected = L.expand(dict(master, rrule=[rrule], excluded=[]), start, end) if rrule else []
            exdates = [x["start"] for x in expected if L.parse_when(x["start"]) not in seen]
            vevents.append(I.vevent(master, stamp, rrule=rrule, exdates=exdates))
        for o in overrides:
            vevents.append(I.vevent(o, stamp, recurrence_id=o.get("occurrence") or o["start"],
                                    uid=L.series_key(o, "externalId")))
        for e in evs:
            if e.get("timeZone") and not e.get("allDay"):
                tzids.add(e["timeZone"])
        summary.update(mode="series", vevents=len(vevents), singleEvents=len(singles),
                       recurringSeries=len(series), movedOccurrences=len(overrides))
    name = a.calendar[0] if a.calendar and len(a.calendar) == 1 else None
    out.write_text(I.calendar_text(vevents, tzids, start.year, name), encoding="utf-8")
    summary["format"] = "ics"
    return summary


def ics_to_spec(comp):
    """An ek save spec from a parsed VEVENT (or None with the reason)."""
    if not comp.get("DTSTART"):
        return None, "no DTSTART"
    start, is_date = I.parse_dt(*comp["DTSTART"][0])
    if comp.get("DTEND"):
        end, _ = I.parse_dt(*comp["DTEND"][0])
    elif comp.get("DURATION"):
        end = start + (I.parse_duration(comp["DURATION"][0][1]) or dt.timedelta(0))
    else:
        end = start + (dt.timedelta(days=1) if is_date else dt.timedelta(0))
    spec = {"title": I.unesc(I.first(comp, "SUMMARY", "")[1]), "allDay": is_date}
    if is_date:
        last = end - dt.timedelta(days=1) if end > start else start  # DTEND is exclusive
        spec.update(start=start.isoformat(), end=last.isoformat())
    else:
        spec.update(start=L.iso(start), end=L.iso(end))
        tzid = comp["DTSTART"][0][0].get("TZID")
        if tzid:
            try:
                I.zone(tzid)
                spec["timeZone"] = tzid
            except Exception:  # noqa: BLE001
                pass
    for prop, key in (("LOCATION", "location"), ("DESCRIPTION", "notes"), ("URL", "url")):
        if comp.get(prop):
            spec[key] = I.unesc(comp[prop][0][1])
    if comp.get("RRULE"):
        spec["rrule"] = comp["RRULE"][0][1]
    if I.first(comp, "TRANSP", "")[1].upper() == "TRANSPARENT":
        spec["availability"] = "free"
    alarms = []
    for al in comp["_alarms"]:
        params, trig = al.get("TRIGGER", [({}, "")])[0]
        if params.get("VALUE") == "DATE-TIME":
            alarms.append(L.iso(I.parse_dt({}, trig)[0]))
        elif I.parse_duration(trig) is not None:
            alarms.append(int(I.parse_duration(trig).total_seconds() // 60))
    if alarms:
        spec["alarms"] = alarms
    exdates = []
    for params, value in comp.get("EXDATE", []):
        for v in value.split(","):
            d, _ = I.parse_dt(params, v)
            exdates.append(d.isoformat() if isinstance(d, dt.date) and not isinstance(d, dt.datetime) else L.iso(d))
    return (spec, exdates), None


def do_import(a):
    path = Path(a.file)
    comps = I.parse(path.read_text(encoding="utf-8", errors="replace"))
    cals = L.calendars()
    cal = L.resolve_calendars([a.calendar], cals, writable=True)[0]
    report = {"file": str(path.resolve()), "calendar": L.label(cal), "vevents": len(comps),
              "created": [], "skippedDuplicates": [], "skipped": [], "dryRun": a.dry_run}
    uid_map = {}  # UID -> id of the series created from it
    masters = [c for c in comps if not c.get("RECURRENCE-ID")]
    overrides = [c for c in comps if c.get("RECURRENCE-ID")]
    for comp in masters:
        res, why = ics_to_spec(comp)
        title = I.unesc(I.first(comp, "SUMMARY", "")[1])
        if res is None:
            report["skipped"].append({"title": title, "reason": why})
            continue
        spec, exdates = res
        spec["calendarId"] = cal["id"]
        s = L.parse_when(spec["start"])
        dupes = [e for e in L.events(s, s + dt.timedelta(minutes=1), [cal["id"]], cals)
                 if e["title"] == spec["title"] and L.ev_start(e) == s]
        if dupes and not a.allow_duplicate:
            report["skippedDuplicates"].append({"title": spec["title"], "start": spec["start"], "id": dupes[0]["id"]})
            uid_map[I.first(comp, "UID", "")[1]] = "duplicate"
            continue
        if a.dry_run:
            report["created"].append(dict(spec, exdates=exdates))
            uid_map[I.first(comp, "UID", "")[1]] = None
            continue
        saved = L.ek("save", spec=spec)["event"]
        uid_map[I.first(comp, "UID", "")[1]] = saved["id"]
        for x in exdates:
            if L.ek("delete", saved["id"], L.iso(L.parse_when(x)), "this", check=False) is None:
                L.warn(f"{spec['title']}: could not remove excluded occurrence {x}")
        report["created"].append({"title": saved["title"], "start": saved["start"], "id": saved["id"],
                                  "rrule": saved.get("rrule"), "alarms": saved.get("alarms"),
                                  "excludedOccurrences": len(exdates)})
    # Moved or edited occurrences (RECURRENCE-ID) become changes to the series just made.
    report["movedOccurrences"] = []
    for comp in overrides:
        uid = I.first(comp, "UID", "")[1]
        title = I.unesc(I.first(comp, "SUMMARY", "")[1])
        if uid_map.get(uid, "missing") in ("missing", "duplicate"):
            why = ("its series was already in the calendar (skipped as a duplicate)" if uid in uid_map
                   else "RECURRENCE-ID for a series that is not in the file")
            report["skipped"].append({"title": title, "reason": why})
            continue
        (spec, _), rid = ics_to_spec(comp)[0], I.parse_dt(*comp["RECURRENCE-ID"][0])[0]
        for k in ("rrule", "allDay", "timeZone"):
            spec.pop(k, None)
        spec.update(occurrence=rid.isoformat() if not isinstance(rid, dt.datetime) else L.iso(rid), span="this")
        if a.dry_run:
            report["movedOccurrences"].append(spec)
            continue
        spec["id"] = uid_map[uid]
        saved = L.ek("save", spec=spec)["event"]
        report["movedOccurrences"].append({"title": saved["title"], "from": spec["occurrence"], "start": saved["start"]})
    report["createdCount"] = len(report["created"])
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export", help="events in a period to .ics or .csv")
    L.add_range_args(e)
    e.add_argument("--calendar", action="append", help="repeatable (default: all calendars)")
    e.add_argument("--exclude-calendar", action="append", default=[])
    e.add_argument("--mode", choices=["series", "occurrences"], default="series")
    e.add_argument("--out", required=True, help="file.ics or file.csv")
    i = sub.add_parser("import", help="create the events of an .ics file")
    i.add_argument("--file", required=True)
    i.add_argument("--calendar", required=True, help="writable target calendar")
    i.add_argument("--dry-run", action="store_true")
    i.add_argument("--allow-duplicate", action="store_true")
    a = p.parse_args()
    report = export(a) if a.cmd == "export" else do_import(a)
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
