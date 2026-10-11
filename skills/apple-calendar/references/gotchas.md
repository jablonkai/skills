# Gotchas

## Permissions

- **EventKit access belongs to the terminal or IDE** that runs the scripts (Terminal,
  iTerm, VS Code …), not to `python3` or `ek`. Granting Terminal doesn't cover VS Code.
- `writeOnly` is a real state in recent macOS: the app may add events but not see any.
  `requestFullAccessToEvents` then returns `false` **without a prompt**. Only System
  Settings › Privacy & Security › Calendars › *app* › Full Access fixes it.
- `notDetermined`: the first `ek` read shows the prompt. A headless session waits until
  the timeout (exit 124). Ask the user to answer it, then re-run.
- The AppleScript fallback needs a different permission: Automation (Apple Events) for
  Calendar. Error -1743 means it was denied: System Settings › Privacy & Security ›
  Automation. AppleScript error **messages are localized** (`Nem olvasható be objektum`),
  so match the number in parentheses.

## The AppleScript fallback

- It's slow: ~2 s per calendar per query, and longer on large Exchange/Google calendars.
  A busy month over many calendars can take minutes.
- `whose` matches **series masters only**. Occurrences are expanded by
  `cal_lib.expand()`, which handles the RRULE subset in [recurrence.md](recurrence.md).
- A **moved occurrence** comes back as a copy of its series (same uid, same RRULE). The
  helper lists it once at its new time, but AppleScript can't say which slot it
  replaced, so the original slot is listed too. Say so when the fallback was used.
- `{_not: […]}` in a `whose` clause is ignored, so it matches everything. Use
  `{recurrence: {_contains: 'FREQ'}}`.
- `calendarIdentifier` fails with a type-conversion error in Calendar 27, and fetching a
  calendar's `properties()` fails with -10000. Calendars are addressed by index.
- The AppleScript `uid` isn't the iCalendar UID, so don't mix ids from the two paths.

## Synced calendars

- Writes to iCloud, Google (CalDAV) and Exchange calendars are saved locally and pushed
  by the sync engine. The read-back confirms the local store. The server copy may lag by
  seconds or minutes, and the server can reject the change later (for example, a shared
  calendar where the user is a viewer). Mention it if the user checks on another device.
- An event that has attendees and an organizer other than the user is the organizer's.
  Changing its time only changes the local copy, and the server may revert it. Don't
  move other people's meetings: tell the user to propose a new time instead.
- Google holiday and other subscribed calendars, and Birthdays, are read-only
  (`writable: false`). Some Exchange "Birthdays"/holiday calendars report writable but
  shouldn't be used for new events.
- Local ("On My Mac") calendars don't store free/busy. `--availability free` (or
  `TRANSP:TRANSPARENT` on import) is dropped, and the read-back reports the mismatch.
  Say so, or use an iCloud/Exchange calendar when free/busy matters.
- Duplicate calendar titles across accounts are common (`Birthdays`,
  `Magyar ünnepnapok`). Address them as `Account/Title` or by id.
- The system's **default calendar** for new events may be surprising, so always pass
  `--calendar` and say which one was used.

## Reading results

- Ranges are half-open: `--from 2026-10-19 --to 2026-10-25` covers the 19th 00:00 to the
  26th 00:00. A bare `--to` date includes that day.
- Events that started before the period but are still running are included (overlap
  semantics). So are multi-day all-day events that cover the period.
- Declined invitations are still in the store. `cal-free.py` ignores them, `cal-list.py`
  shows them (`attendees[].self` with `status: declined`).

## Security posture

- No listener and no daemon: every helper is a one-shot process with a timeout, so there
  is no network surface, nothing to authenticate, and nothing to stop.
- Read-only by default. Writes only create or change what the user asked for. Delete
  needs `--yes`, and a series is deleted only on request. Read-only calendars are
  refused.
- `create` and `import` skip an event that already exists (same title, start and
  calendar), so a re-run doesn't duplicate.
- Calendar contents stay local. Don't send them to delegate agents or web services.
- `ek` is compiled from source in this skill on first use. Its cache directory holds
  nothing but the binary.
