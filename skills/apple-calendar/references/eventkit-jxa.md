# EventKit helper and Calendar's AppleScript dictionary

## `ek` (scripts/ek.swift)

Compiled by `cal_lib.ek_binary()` to `~/Library/Caches/apple-calendar/ek-<hash>`. It is
rebuilt when the source changes and falls back to `swift ek.swift` when `swiftc` is
missing. It runs with the terminal/IDE's calendar permission, because macOS grants
access to the responsible app, not to the binary.

| Command | Does |
|---|---|
| `ek status` | `{"status": "fullAccess"/"writeOnly"/"denied"/"restricted"/"notDetermined"}`. Never prompts |
| `ek calendars` | `[{id, title, source, type, writable, default}]`. `type` is local, calDAV, exchange, subscription or birthday |
| `ek range FROM TO [CAL_ID…]` | occurrences overlapping `[FROM, TO)`, sorted. Spans over 4 years are refused (EventKit clips them) |
| `ek get ID [OCCURRENCE]` | the series' first occurrence, or the occurrence originally starting at `OCCURRENCE` |
| `ek save` (JSON on stdin) | create (no `id`) or update, then read back through a fresh store |
| `ek delete ID [OCCURRENCE] this/future` | remove one occurrence, or it and every later one |

Exit codes: 0 ok, 2 bad input or not found, 3 no access, 1 an EventKit error.

### Event JSON

`id` (eventIdentifier, shared by every occurrence of a series), `externalId` (the
iCalendar UID on CalDAV/iCloud), `title`, `start`, `end` (ISO with the local offset),
`allDay`, plus `startDate`/`endDate` (the last day, inclusive) for all-day events,
`calendar`, `calendarId`, `source`, `recurring`, `rrule` (list of strings), `detached`
(a moved or edited occurrence), `occurrence` (its original start), `seriesStart`/
`seriesEnd`, `availability` (busy/free/tentative/unavailable), `alarms`
(`{"offsetMinutes": -15}` or `{"absolute": ISO}`), and when set: `location`, `notes`,
`url`, `timeZone` (absent = floating), `attendees` (`name`, `email`, `status`, `self`).

A detached occurrence's `id` and `externalId` end in `/RID=<n>`. `cal_lib.series_key()`
strips it.

### Save spec

```json
{"id": "…optional…", "occurrence": "2026-10-26T10:00:00+01:00", "span": "this|future",
 "calendarId": "…", "title": "…", "start": "ISO or YYYY-MM-DD", "end": "…",
 "allDay": false, "timeZone": "Europe/Budapest", "location": "", "notes": "", "url": "",
 "availability": "busy", "alarms": [-15, "2026-10-19T08:00:00+02:00"],
 "rrule": "FREQ=WEEKLY;BYDAY=MO;COUNT=10"}
```

An empty string clears a text field. `"rrule": ""` removes the recurrence, and
`"alarms": []` removes all alarms. Alarm numbers are minutes, negative before the start.
EventKit can't set attendees: invitations are sent by the server, so add them in
Calendar or the mail client.

## Calendar's AppleScript / JXA dictionary (fallback only)

`application` › `calendar` (`name`, `color`, `writable`, `description`; and
`calendarIdentifier`, which Calendar 27 fails to return) › `event` (`summary`,
`start date`, `end date`, `allday event`, `recurrence` (an RRULE string without
`RRULE:`), `excluded dates`, `location`, `description`, `url`, `uid`, `status`,
`stamp date`, `sequence`) › `attendee` (`display name`, `email`, `participation
status`, read-only) and `display`/`mail`/`sound`/`open file alarm` (`trigger interval`
in minutes or `trigger date`). Commands: `make`, `create calendar`, `reload calendars`,
`switch view`, `view calendar`, `show`. There is **no export or import command**.

What the fallback can do, by comparison:

| | EventKit (`ek`) | AppleScript |
|---|---|---|
| a week across 16 calendars | ~0.1 s | ~30 s |
| recurring occurrences | expanded | masters only; expanded by `cal_lib.expand()` |
| moved occurrences | detached, with their original slot | a copy of the master; the original slot isn't known |
| calendar id | stable identifier | index only (`jxa:<n>`) |
| account (source) | yes | no |
| `uid` | iCalendar UID | a different, Calendar-internal uid |

The helpers use AppleScript only for reads, and only when EventKit has no read access.
