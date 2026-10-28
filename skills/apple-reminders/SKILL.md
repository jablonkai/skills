---
name: apple-reminders
description: 'List, create, complete, move and clean up Apple Reminders on macOS through EventKit (AppleScript as a slow fallback): open, overdue, due-today, upcoming and completed reminders grouped by list as a table, JSON or CSV; bulk creation from a Markdown or text checklist with due dates, priorities and alerts; matched completion, moves between lists and cleanup of old completed items with a preview first; all read back to verify. Read-only by default. Use for "what reminders are overdue", "show my open to-dos by list", "turn this checklist into a Reminders list with due dates", "remind me to call Anna on Friday at 9", "mark all the invoice reminders done", "move everything from Inbox to Work", "clear out completed reminders older than a year". Not for calendar events (apple-calendar), Apple Notes, Microsoft To Do, Todoist, Things or OmniFocus, TODO comments in code, or scheduling agents or cron jobs.'
summary: "list, create, complete and move Apple Reminders via EventKit and JXA — open, overdue and completed reminders by list, bulk creation from Markdown checklists with due dates, matched completion and cleanup with preview, read-back verified"
category: mac-automation
compatibility: "Built for Reminders 7.0 on macOS 27.0.1 (EventKit and JXA)."
risk: medium
tags:
    - reminders
    - apple-reminders
    - eventkit
    - jxa
    - macos
    - todo
metadata:
  version: "1.0.2"
  author: "Tamás Jablonkai"
---

# Apple Reminders via EventKit

Everything goes through `scripts/`: stdlib Python helpers on top of `ek`, a small
EventKit tool compiled from [ek.swift](scripts/ek.swift) on first use (cached under
`~/Library/Caches/apple-reminders/`). EventKit answers a query over thousands of
reminders in well under a second. Reminders' AppleScript took 41 s for the same
overdue query, so it is only a fallback, plus the one way to read or set *flagged*.
Reminders doesn't need to be open.

Verified against **Reminders 7.0 on macOS 27.0.1**.

## Privacy and safety rules (read first)

- **Read-only by default.** Listing, reports and verify change nothing. Write only when
  the user asks for reminders to be added, changed, completed, moved or removed.
- **Name the list you write to.** Without `--list`, new reminders go to the default list
  (shown by `rem.sh check`), which may be in a different account than the user expects.
  Always say which list you used.
- **Preview bulk changes.** A `--match` selection only shows what would change until
  `--yes` is added; `delete` always previews first. Show the preview (or its count) to
  the user when the match could catch more than they meant, then apply.
- **"Clean up" means complete or move unless the user says delete.** Deleting can't be
  undone from a script, and synced deletions reach every device.
- Reminder data is personal: keep it local, no delegate agents or web services.

## Setup

```bash
S=scripts   # relative to this skill's directory
bash $S/rem.sh check    # versions, EventKit access, every list with account and open/overdue counts
```

`eventkit: fullAccess` is what you want. The first run asks for permission. If it says
`denied`, the user has to enable the terminal/IDE in System Settings › Privacy &
Security › Reminders, because macOS won't ask a second time. Until then reads fall back
to AppleScript (tens of seconds per list) and writes fail.

Lists are named by title (`Work`), `Account/Title` when two share a title, or id. A
leading emoji is optional: `Számlák` finds `🧾 Számlák`. Dates are local: `2026-10-20`
(all-day), `2026-10-20 14:30` (timed), `today`, `tomorrow`, `fri`, `+3d`, each with an
optional time (`fri 9:30`).

## Tasks

| The user wants | Run |
|---|---|
| open reminders by list | `python3 $S/rem-list.py` (add `--list X`, repeatable; `--exclude-list`) |
| overdue, grouped by list | `rem-list.py --overdue` |
| due today / this week / undated | `rem-list.py --today` / `--upcoming 7` / `--undated` |
| find reminders | `rem-list.py --search invoice [--in-notes] [--all]` (`--regex` for patterns) |
| what got done | `rem-list.py --completed --since 2026-10-01 [--until DATE]` |
| lists with counts | `rem-list.py --lists` |
| as data | any of the above with `--format json` (ids, dues, alarms, notes) or `--format csv` |
| a checklist → reminders | `rem-import.py --file todo.md --list Trip --create-list --dry-run`, then without `--dry-run` |
| one reminder | `rem-write.py create --title T --due "fri 9:30" --list Work [--priority high] [--notes N] [--flag] [--create-list]` |
| a repeating one | `... create ... --repeat weekly [--interval 2] [--count 10 / --until DATE]` |
| change one | `rem-write.py update --id ID [--due DATE/none] [--title T] [--priority P] [--flag/--unflag]` |
| mark done | `rem-write.py complete --match invoice --list Bills`, then the same with `--yes` (or `--id ID`) |
| reopen | `rem-write.py uncomplete --id ID` |
| move | `rem-write.py move --match trip --list Inbox --to Travel --yes` (`--create-list` makes `--to` in the same account) |
| flag / unflag | `rem-write.py flag --overdue --match "" --list Home --yes` (AppleScript: a few seconds per list) |
| clean up old completed | `rem-write.py move/delete --completed --completed-before 2025-10-01 --list X` (+ `--yes`) |
| check a result | `rem-verify.py checklist --file todo.md --list Trip --exact` / `rem-verify.py ids --id ID --completed yes` |

`--match ""` selects everything in `--list`. Bulk selections can be narrowed with `--overdue`, `--due-before DATE`, `--completed` or
`--any-state` (default: open reminders only; `uncomplete` defaults to completed ones).

## Checklist format

`rem-import.py` reads `- [ ] item`, `- [x] item` (created completed), `- item`, `* item`
and `1. item`. A due date comes from `(due 2026-10-20 14:00)`, `due: fri`,
`@due(2026-10-20)`, `📅 2026-10-20`, or a date at the end of the line (`--no-bare-dates`
turns that off). A date alone is all-day; a date with a time is timed and gets an alert
at that time, as in the Reminders app (`--no-alerts` skips it). Priority: `!high`
`!medium` `!low`, `!!!` `!!` `!`, or the Obsidian Tasks emoji. Indented plain lines
become notes. `--by-heading` sends each `## Heading`'s items to the list of that name.
The parsed title has the date and priority markers removed; check the dry run when a
title itself contains a date.

## Workflow

1. **Look before writing.** List or search first so you know the ids, which list each
   reminder is in and how many a match will catch.
2. **Run the helper,** not hand-written AppleScript or EventKit code: the helpers handle
   all-day vs timed due dates, alerts, priority bands and the duplicate guard. `create`
   and `rem-import.py` skip a reminder already in the list with the same title and due
   date, so re-running a task is safe.
3. **Read back.** Every write re-reads the stored reminders and compares them with the
   request: `Read-back: OK`, or the mismatches and exit 4. For a checklist import, also
   run `rem-verify.py checklist`. Report what's stored: titles, due dates, completion,
   the list, and the count.

## Reporting

- Tables are per list. All-day due dates show as a date, timed ones with the time.
  `overdue 5d` counts whole days; an all-day reminder due today is *today*, not overdue,
  as in the Reminders app.
- Priority shows as high/medium/low. Exchange lists store high as 3, not 1; the helpers
  read 1–4 as high, 5 as medium, 6–9 as low.
- ⚑ marks flagged reminders, but only when `--flagged` was asked for, because reading
  flags goes through AppleScript.

## Stopping

Every call is a one-shot process with a timeout. Nothing keeps running and nothing
listens on a port. The only thing that can stall is the first-run permission prompt:
answer it and re-run. Exit codes: 2 bad input, refused, or nothing matched; 3 no
Reminders access; 4 the read-back or verification found a mismatch; 124 timeout.

## References

- [references/recipes.md](references/recipes.md): worked jobs (weekly review, overdue
  digest, a trip checklist, bulk completion, archiving a list, exporting to CSV).
- [references/eventkit-jxa.md](references/eventkit-jxa.md): the `ek` commands and JSON
  fields, the AppleScript dictionary, and which fields each path exposes.
- [references/gotchas.md](references/gotchas.md): permissions, what can't be scripted
  (sections, tags, subtasks, smart lists), id changes on cross-account moves, sync, and
  the security posture.
