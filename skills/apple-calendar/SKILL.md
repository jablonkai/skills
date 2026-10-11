---
name: apple-calendar
description: 'List, find, create and export Apple Calendar events on macOS through EventKit (AppleScript as a slow fallback): events in a date range across all calendars with recurring occurrences expanded, as a table, JSON or CSV; free-slot search; creating, moving and deleting events with alarms, recurrence and time zones, one occurrence or a whole series; .ics export and import; all read back to verify. Read-only by default; never writes to subscribed, holiday or birthday calendars. Use for "what''s on my calendar next week", "am I free Thursday afternoon", "add a weekly team sync every Monday at 10 with a 15-minute alert", "move my dentist appointment to Friday", "export November to an .ics file", "dump this month''s events to CSV", "import this .ics invite", Hungarian "mi van a naptáramban a jövő héten", "tegyél be egy heti ismétlődő eseményt". Not for the Google Calendar web API or connector, Reminders or to-dos, scheduling cron jobs or agents, or .ics files unrelated to the Mac''s calendars.
summary: "list, find, create and export Apple Calendar events via EventKit and JXA — date-range queries with recurring occurrences, free-slot search, events with alarms and recurrence, .ics/CSV export and .ics import, read-back verified"
category: mac-automation
risk: medium
tags:
    - calendar
    - apple-calendar
    - eventkit
    - jxa
    - macos
    - ics
metadata:
  version: "1.0.0"
---

# Apple Calendar via EventKit

Everything goes through `scripts/`: stdlib Python helpers on top of `ek`, a small
EventKit tool compiled from [ek.swift](scripts/ek.swift) on first use (cached under
`~/Library/Caches/apple-calendar/`). EventKit answers a month's query across every
calendar in well under a second and expands recurring events into their occurrences.
Calendar's AppleScript can do neither: one week took 32 s there, and its `whose` matches
only the first event of a series. Calendar doesn't need to be open.

Verified against **Calendar 27.0 on macOS 27.0.1**.

## Privacy and safety rules (read first)

- **Read-only by default.** Listing, free-slot search, export and verify change nothing.
  Write only when the user asks for an event to be added, changed or removed.
- **Name the calendar you write to.** The system default calendar can be anything (an
  Exchange holiday calendar, say). When the user didn't name one, pick the obvious one
  from `cal.sh check` or ask, and always say which calendar you used.
- **Deleting is explicit.** `cal-write.py delete` without `--yes` only shows what would
  go. A recurring event's whole series goes only when the user asked for the series.
- Subscribed, holiday and birthday calendars are read-only, and the helpers refuse them.
- Calendar data is personal: keep it local, no delegate agents or web services.

## Setup

```bash
S=scripts   # relative to this skill's directory
bash $S/cal.sh check    # versions, EventKit access, the calendars with type and writability
```

`eventkit: fullAccess` is what you want. The first read asks for permission. If it says
`writeOnly` or `denied`, the user has to turn on **Full Access** for the terminal/IDE in
System Settings › Privacy & Security › Calendars, because macOS won't ask a second time.
Until then, reads fall back to AppleScript, which is slow and approximate (see
[gotchas](references/gotchas.md)), and writes fail when the access is `denied`.

Calendars are named by title (`Work`), `Account/Title` when two share a title
(`Exchange/Birthdays`), or id. Dates are local: `2026-10-20`, `2026-10-20 14:30`,
`today`, `tomorrow`. Periods: `--week this|next|last|<date>` (Monday start),
`--month this|next|YYYY-MM`, `--from/--to` (a bare `--to` date includes that day), or
`--days N`.

## Tasks

| The user wants | Run |
|---|---|
| what's on next week, as a table | `python3 $S/cal-list.py --week next` (add `--calendar X`, repeatable; `--exclude-calendar`; `--no-all-day`) |
| events as data | `cal-list.py --month 2026-11 --format json` (ids, rrule, alarms, attendees) or `--format csv` |
| find an event | `cal-list.py --search dentist --days 90` (title, location and notes) |
| free time | `cal-free.py --week next --min 60 [--hours 08:00-18:00] [--weekends] [--calendar Work]` |
| add an event | `cal-write.py create --title T --start "2026-10-19 10:00" --duration 30 --calendar Work [--alarm 15] [--location L]` |
| a recurring event | `... create ... --repeat weekly --on MO [--interval 2] [--count 10 / --until 2026-12-21]` (or `--rrule`) |
| an all-day event | `cal-write.py create --title T --start 2026-12-24 --end 2026-12-26 --all-day` (end is the last day) |
| move or edit one | `cal-write.py update --id ID --start "2026-10-23 09:00"` (the length is kept) |
| one occurrence of a series | `update --id ID --occurrence "2026-10-26 10:00" --start ...` (`--span future` for it and later ones) |
| remove | `cal-write.py delete --id ID [--occurrence DATE] [--span this/future]`, then again with `--yes` |
| export to .ics / CSV | `cal-ics.py export --month 2026-11 --out nov.ics` (`--mode occurrences` for one event per occurrence; `.csv` by extension) |
| import an .ics | `cal-ics.py import --file f.ics --calendar Work --dry-run`, then without `--dry-run` |
| check a result | `cal-verify.py event --id ID --start ... --rrule ... --alarm 15` / `cal-verify.py ics --file f.ics --month 2026-11` |

Ids come from `--format json`. A recurring event has **one id for all its occurrences**:
`--occurrence` (the original start of that occurrence) picks one. Without it, `update`
and `delete` act on the whole series.

## Workflow

1. **Look before writing.** List the period, or search, so you know the ids, which
   calendar the event is in, and whether it repeats. Before changing a recurring event,
   say whether you mean one occurrence, this and later ones, or the series.
2. **Run the helper,** not hand-written AppleScript or EventKit code: the helpers handle
   occurrence ids, all-day end dates, DST and the duplicate guard. `create` refuses a
   second event with the same title and start in the same calendar (`--allow-duplicate`
   overrides), so re-running a task is safe.
3. **Read back.** `cal-write.py` re-reads every saved event and compares it with the
   request: `readback.ok`, with `mismatches`, and exit 4 when they differ. For an export,
   run `cal-verify.py ics` with the same period. Report what's stored: the times,
   recurrence, alarms and calendar, and for an export the file path and counts.

## Reporting

- Tables are by day, with `↻` marking recurring events. All-day events show as `all day`.
- Free slots ignore all-day events, events marked *free*, and events the user declined.
  `--all-day-busy` makes all-day events block the day.
- An export's JSON gives `occurrences` (in the period) and `vevents` (in the file). In
  `series` mode, a weekly meeting is one VEVENT with an RRULE, so the two counts differ;
  say which you are quoting.

## Stopping

Every call is a one-shot process with a timeout. Nothing keeps running and nothing
listens on a port. The only thing that can stall is the first-run permission prompt:
answer it and re-run. Exit codes: 2 bad input or refused, 3 no calendar access, 4 the
read-back or verification found a mismatch, 124 timeout.

## References

- [references/recipes.md](references/recipes.md): worked jobs (weekly agenda, meeting
  slot across calendars, move a series, a term's timetable from CSV, month backup).
- [references/eventkit-jxa.md](references/eventkit-jxa.md): the `ek` JSON fields and
  commands, the AppleScript dictionary, and what each path can do.
- [references/recurrence.md](references/recurrence.md): the RRULE subset, occurrence ids
  and spans, all-day and time-zone rules, and .ics mapping.
- [references/gotchas.md](references/gotchas.md): permissions, the AppleScript fallback's
  limits, synced calendars, and the security posture.
