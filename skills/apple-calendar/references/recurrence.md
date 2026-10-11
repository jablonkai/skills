# Recurrence, occurrences, all-day and time zones

## RRULE subset

`cal-write.py` builds RRULEs from `--repeat daily|weekly|monthly|yearly`, `--interval N`,
`--on MO,WE` (weekly) or `--on 2TU` / `--on -1FR` (monthly: second Tuesday, last
Friday), and `--count N` or `--until DATE`. `--rrule` takes a raw rule.

`ek` maps these parts onto `EKRecurrenceRule`: `FREQ`, `INTERVAL`, `BYDAY` (with an
optional week number), `BYMONTHDAY`, `BYMONTH`, `BYSETPOS`, `COUNT` and `UNTIL`. Others,
such as `WKST`, `BYHOUR` and `BYWEEKNO`, are dropped silently, and the read-back then
shows the stored rule. Examples:

| Want | Flags |
|---|---|
| every weekday | `--repeat weekly --on MO,TU,WE,TH,FR` |
| every other Thursday, 8 times | `--repeat weekly --interval 2 --on TH --count 8` |
| first Monday of the month | `--repeat monthly --on 1MO` |
| the 15th of every month until June | `--repeat monthly --rrule "FREQ=MONTHLY;BYMONTHDAY=15;UNTIL=20270630"` |
| yearly (birthday-style) | `--repeat yearly --all-day` |

`--until` is inclusive: EventKit stores the end of that day, and the read-back shows it
in UTC (`UNTIL=20261221T225959Z`). The comparison only checks the date.

## Occurrence ids and spans

- Every occurrence of a series shares one `id`. An occurrence is identified by the id
  plus its **original** start (`occurrence` in the JSON). That stays the same after the
  occurrence is moved, so always pass the value from `occurrence`, not the current
  `start`.
- `update`/`delete` with `--occurrence` and no `--span` change only that occurrence. It
  becomes *detached*, and its id gains `/RID=…`.
- `--span future` applies to that occurrence and all later ones. EventKit splits the
  series: the earlier part keeps the old rule with an `UNTIL`, and the rest is a new
  series.
- Without `--occurrence`, the helper acts on the series from its first occurrence (span
  future), which is the **whole series**.
- Moving a series' start time moves every occurrence. The duration is kept unless
  `--end`/`--duration` is given.

## All-day events

- Pass dates: `--start 2026-12-24 --end 2026-12-26 --all-day` is three days. The end is
  the **last day, inclusive**.
- EventKit stores the end as 23:59:59 of the last day, and AppleScript and .ics use the
  next midnight. `cal_lib.ev_last_day()` handles both.
- All-day events have no time zone, so they show on the same dates everywhere.

## Time zones and DST

- Times without an offset are local. The helpers use the IANA zone behind
  `/etc/localtime` (or `$TZ`), so arithmetic keeps the wall-clock time across DST
  changes: a weekly 10:00 meeting stays at 10:00 in winter.
- `--tz America/New_York` pins an event to that zone (`timeZone` in the JSON). It then
  moves on the user's calendar when either zone changes DST. Use it for meetings set in
  another city's time.
- Events with no `timeZone` are *floating*: 09:00 wherever the Mac is. Calendar creates
  these for some imported events.

## .ics mapping

| Calendar | .ics |
|---|---|
| a single event | `VEVENT` with `DTSTART;TZID=…`/`DTEND`, or `VALUE=DATE` for all-day (DTEND exclusive) |
| a series (`--mode series`) | one `VEVENT` with `RRULE`, starting at `seriesStart` |
| an occurrence deleted inside the period | `EXDATE` on the series |
| a moved occurrence | an extra `VEVENT` with the same `UID` and `RECURRENCE-ID` = original start |
| `--mode occurrences` | one `VEVENT` per occurrence, `UID` = `<uid>-<YYYYMMDDTHHMMSS>`, no RRULE |
| alarms | `VALARM` with `ACTION:DISPLAY` and `TRIGGER:-PT15M` or `TRIGGER;VALUE=DATE-TIME:…Z` |
| availability free | `TRANSP:TRANSPARENT` |
| time zones | a `VTIMEZONE` per zone used, generated from zoneinfo for the export's year |

EXDATEs are only computed inside the exported period. A series that started earlier is
written whole, as Calendar's own export does.

Import reverses this: `RRULE` is kept, each `EXDATE` deletes that occurrence after the
series is created, and a `RECURRENCE-ID` VEVENT is applied as a one-occurrence update. A
`TZID` that zoneinfo doesn't know (a Windows name such as `W. Europe Standard Time`) is
read as local time, with a warning. `ATTENDEE` and `ORGANIZER` aren't imported, because
EventKit can't create invitations.
