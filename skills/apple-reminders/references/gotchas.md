# Gotchas

## Permissions

- **Reminders access belongs to the terminal or IDE** that runs the scripts (Terminal,
  iTerm, VS Code …), not to `python3` or `ek`. Granting Terminal doesn't cover VS Code.
- **The prompt only appears for a compiled binary.** Under `swift ek.swift` (the
  interpreter, used when `swiftc` is missing) `requestFullAccessToReminders` returns
  `false` without a prompt and the status stays `notDetermined`. Install the Command
  Line Tools (`xcode-select --install`) so `ek` can be compiled.
- `notDetermined`: the first `ek` call shows the prompt. A headless session waits until
  the timeout (exit 124). Ask the user to answer it, then re-run.
- `denied`: only System Settings › Privacy & Security › Reminders fixes it.
- The AppleScript path needs Automation (Apple Events) permission for Reminders. Error
  -1743 means denied (System Settings › Privacy & Security › Automation). Error -609 or
  -600 means Reminders wasn't running; the helper launches it, so retry. AppleScript
  error **messages are localized**, so match the number.

## The AppleScript fallback

- It's slow: each list costs seconds to tens of seconds, and an app-wide `whose` over
  ~1,900 reminders took 41 s. Large Exchange lists are the slowest.
- It can't see URLs or repeat rules, and it shows only one alert (`remind me date`).
- Writes always need EventKit; only `flagged` is written through AppleScript.

## What can't be scripted

- **Sections, tags, subtasks, smart lists, attachments and early reminders** aren't in
  EventKit or the AppleScript dictionary. Don't try private frameworks or GUI scripting.
  - Tags typed as `#tag` stay as plain text in the title.
  - Subtasks from a nested checklist are created as separate reminders with
    "Subtask of: <parent>" in the notes. Tell the user they can drag them under the
    parent in the app.
  - A "smart list" request (e.g. everything flagged and due this week) becomes a
    `rem-list.py` query, not a saved list.
- **Grocery lists** (auto-categorised sections) behave like ordinary lists here; the
  categories aren't readable.

## Ids and moves

- **Moving a reminder to a list in another account gives it a new id** (EventKit copies
  it to the new account and removes the original). `rem-write.py move` reports the new
  ids; don't reuse the old ones. Moves within one account keep the id.
- Ids are stable otherwise, including across edits and completion.
- **Completing a repeating reminder doesn't complete that id.** Like the Reminders app,
  EventKit keeps the id open with the next due date and stores the done occurrence as
  a new completed reminder with a new id (verified on macOS 27.2). `rem-write.py
  complete` reports these under `advanced` and still exits 0, but
  `rem-verify.py ids --completed yes` on that id fails. Only the last occurrence of a
  `--count`/`--until` series completes for real.

## Dates

- An all-day reminder due today isn't overdue until tomorrow, matching the app. A timed
  one is overdue once its time has passed.
- A timed due date without an alert doesn't notify. The helpers add an alert at the due
  time, as the app does, unless `--no-alert`/`--no-alerts`.
- Changing a timed due date replaces the alerts with one at the new time. Use `--alert`
  or `--alert-before` to set something else.
- Due dates are stored with the local time zone. A reminder created in Budapest for 9:00
  shows at 9:00 Budapest time when travelling.

## Priority

- EventKit stores 0 or 1–9. The app writes 1/5/9; Exchange lists use 3 for high. The
  helpers read 1–4 as high, 5 as medium, 6–9 as low, and write 1/5/9.

## Synced accounts

- Writes to iCloud and Exchange lists are saved locally and pushed by the sync engine.
  The read-back confirms the local store; another device may lag by seconds or minutes.
- Some accounts (older CalDAV, Yahoo!) don't support every field: priority, notes or
  alerts can be dropped by the server later. The read-back catches it only if it
  happens before the read.
- Deleting or completing on one device syncs everywhere. There is no undo from a script,
  which is why bulk changes preview first.

## Security posture

- No server, port or background process: each helper is a short-lived process, so the
  bridge rules for the live-app skills (token, origin checks, stop path) don't apply.
- Reminder titles and notes are personal data. They stay on the machine; never pass
  them to delegate CLIs or web services.
- AppleScript input is passed as a JSON argument, never spliced into script text.
