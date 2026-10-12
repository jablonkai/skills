# Recipes

`S` is the skill's `scripts/` directory.

## Weekly review

```bash
python3 $S/rem-list.py --overdue                  # what slipped
python3 $S/rem-list.py --upcoming 7               # what's coming
python3 $S/rem-list.py --undated --list Inbox     # what has no date yet
python3 $S/rem-list.py --completed --since=-7d   # what got done this week
```

Summarise as counts per list first, then the overdue items with how late they are.

## Overdue digest grouped by list

```bash
python3 $S/rem-list.py --overdue                  # Markdown table per list
python3 $S/rem-list.py --overdue --format json    # to build your own summary
```

Each row has the due date (all-day as a date) and `overdue Nd`. Quote the total and the
number of lists.

## A trip checklist with due dates

```markdown
## Lisbon trip
- [ ] Book flights (due 2026-10-20 14:00) !high
- [ ] Renew passport due: 2026-10-25
- [x] Ask for days off
- [ ] Pack
  - [ ] Charger
```

```bash
python3 $S/rem-import.py --file trip.md --list "Lisbon trip" --create-list --dry-run
python3 $S/rem-import.py --file trip.md --list "Lisbon trip" --create-list
python3 $S/rem-verify.py checklist --file trip.md --list "Lisbon trip" --exact
```

Or `--by-heading` to take the list name from `## Lisbon trip`.

## Mark matching reminders done

```bash
python3 $S/rem-write.py complete --match invoice --list Bills          # preview
python3 $S/rem-write.py complete --match invoice --list Bills --yes
python3 $S/rem-list.py --all --search invoice --list Bills             # confirm
```

`--match` is a case-insensitive substring of the title. Add `--in-notes` only when the
user means notes too, and `--regex` for word boundaries (`--match '\binvoice\b' --regex`).
Already-completed matches are left alone and reported.

## Move a list's contents

```bash
python3 $S/rem-write.py move --match "" --list Inbox --to Work            # preview: every open item
python3 $S/rem-write.py move --match "" --list Inbox --to Work --yes
```

Across accounts the ids change; use the ids in the output.

## Archive or clear old completed reminders

```bash
python3 $S/rem-write.py move --completed --completed-before 2025-10-01 --list Groceries --to Archive
python3 $S/rem-write.py move --completed --completed-before 2025-10-01 --list Groceries --to Archive --yes
# only when the user asked for deletion:
python3 $S/rem-write.py delete --completed --completed-before 2025-10-01 --list Groceries --yes
```

Create the archive list first with `rem-import.py`'s `--create-list`, or ask the user.

## Quick single reminders

```bash
python3 $S/rem-write.py create --title "Call Anna" --due "fri 9:00" --list Personal
python3 $S/rem-write.py create --title "Pay rent" --due 2026-11-01 --repeat monthly --list Bills --priority high
python3 $S/rem-write.py create --title "Leave for the airport" --due "2026-10-20 12:00" --alert-before 30
```

## Export to CSV

```bash
python3 $S/rem-list.py --all --list Work --format csv > work.csv
```

Columns: list, title, due, allDay, state, priorityName, completed, completionDate,
notes, id.
