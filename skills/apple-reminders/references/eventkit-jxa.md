# EventKit and AppleScript reference

## `ek` commands

`ek` is compiled from [ek.swift](../scripts/ek.swift) and prints JSON. The Python helpers
call it; run it directly only to debug (`~/Library/Caches/apple-reminders/ek-<hash>`).

| Command | Does |
|---|---|
| `ek status` | `{"status": "fullAccess"}` etc.; never prompts |
| `ek lists` | every reminder list: `id`, `title`, `source` (account), `writable`, `default` |
| `ek query open [LIST_ID…]` | open reminders, undated ones included |
| `ek query all [LIST_ID…]` | open and completed |
| `ek query completed FROM\|- TO\|- [LIST_ID…]` | completed in `[FROM, TO)` (ISO with offset) |
| `ek get ID…` | reminders by id; unknown ids are left out of the array |
| `ek save < spec.json` | create or update one spec object or an array, commit once, read back from a fresh store |
| `ek delete ID…` | remove reminders, commit once |
| `ek newlist TITLE [ACCOUNT]` | create a list (default: the default list's account) |

Exit codes: 0 ok, 2 bad input or not found, 3 no access, 1 EventKit error.

## Reminder JSON

```json
{"id": "461B568B-…", "title": "Book flights", "list": "Trip", "listId": "89D1…",
 "source": "iCloud", "completed": false, "completionDate": null,
 "due": "2026-10-20T14:00:00+02:00", "allDay": false, "priority": 1, "priorityName": "high",
 "notes": "", "url": "", "alarms": [{"absolute": "2026-10-20T14:00:00+02:00"}],
 "repeat": "FREQ=WEEKLY", "created": "…", "modified": "…"}
```

- An all-day due is `"due": "2026-10-22", "allDay": true` (EventKit date components
  without an hour). A timed due is ISO 8601 with the local offset.
- `alarms` entries are `{"absolute": ISO}` or `{"offsetMinutes": -15}` (relative to due).
- `repeat` is an RRULE fragment: `FREQ=DAILY|WEEKLY|MONTHLY|YEARLY`, `INTERVAL`, `COUNT`
  or `UNTIL`.

## Save spec

Only the keys present are changed, so an update spec is `{"id": …}` plus what changes.

| Key | Value |
|---|---|
| `id` | update this reminder (omit to create) |
| `list` | list id (create: default list when omitted; update: moves it) |
| `title`, `notes`, `url` | strings (`null` clears notes/url) |
| `priority` | 0 none, 1 high, 5 medium, 9 low |
| `due` | `"2026-10-20"` all-day, ISO with offset timed, `null` clears |
| `alarms` | array replaces all alarms; `[]` removes them |
| `repeat` | `{"freq": "WEEKLY", "interval": 2, "count": 5}` or `"until"`; `null` removes; needs a due |
| `completed` | true/false (EventKit stamps `completionDate` now) |
| `completionDate` | override the stamp (only when completed) |

## Which path exposes what

| Field | EventKit (`ek`) | AppleScript / JXA |
|---|---|---|
| title, notes, completed, completion date, priority | ✓ | ✓ (`name`, `body`, …) |
| due date | `dueDateComponents` (no hour = all-day) | `due date` + `allday due date` |
| alert | `alarms` (absolute, relative, location) | `remind me date` only |
| flagged | ✗ | ✓ |
| URL, repeat rules | ✓ | ✗ |
| list colour / emblem | colour only | ✓ / ✓ |
| sections, tags, subtasks, smart lists, images | ✗ | ✗ |

## AppleScript dictionary (Reminders 7.0)

`application` › `account` (`name`, `id`) › `list` (`name`, `id`, `color`, `emblem`,
`container`) › `reminder` (`name`, `id`, `body`, `completed`, `completion date`,
`due date`, `allday due date`, `remind me date`, `priority`, `flagged`,
`creation date`, `modification date`, `container`). Also `default account`,
`default list`. Commands: `make`, `delete`, `move`, `show`.

- A JXA reminder id is `x-apple-reminder://` + the EventKit id; a JXA list id is the
  EventKit list id. The helpers accept either form.
- An all-day reminder has `due date` = `allday due date` = local midnight. A timed one
  has `allday due date` at midnight of that day and `due date` at the time.
- Address reminders through their list: `R.lists.byId(L).reminders.byId(…)` takes about
  2 s, while `R.reminders.byId(…)` scans every reminder in every account (60 s here).
- Fetch properties in bulk (`q.name()`, `q.dueDate()` on a `whose` query), never per
  reminder in a loop.
