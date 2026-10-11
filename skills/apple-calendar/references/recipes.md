# Recipes

`S=scripts` relative to the skill directory. Every listing is read-only.

## Weekly agenda without the noise

```bash
python3 $S/cal-list.py --week next --exclude-calendar "Birthdays" \
  --exclude-calendar "Exchange/Magyar ünnepnapok" --no-all-day
```

To get the agenda as Markdown in a file, redirect the table. For further processing,
use `--format json` and filter on `calendar`, `availability` or `attendees`.

## A meeting slot that fits two calendars

```bash
python3 $S/cal-free.py --from "2026-10-20" --to "2026-10-23" --hours 09:30-17:30 \
  --min 60 --calendar Work --calendar Home --format json
```

Offer the first two or three slots. Once the user picks one, create it with
`cal-write.py create … --calendar Work`, which reads it back.

## Move a recurring meeting to a new time from next week on

```bash
python3 $S/cal-list.py --search "Team sync" --days 21 --format json   # id + occurrence
python3 $S/cal-write.py update --id ID --occurrence "2026-10-26 10:00" --span future \
  --start "2026-10-26 14:00"
```

Earlier occurrences keep the old time, and the series is split. Use `--occurrence` with
the first occurrence that should change. Skip it only to change every occurrence,
including past ones.

## Cancel one occurrence (a holiday week)

```bash
python3 $S/cal-write.py delete --id ID --occurrence "2026-12-21 10:00"         # preview
python3 $S/cal-write.py delete --id ID --occurrence "2026-12-21 10:00" --yes
```

## A term's timetable from a CSV

For each row (`title,weekday,start,end,first_date,last_date,room`), run:

```bash
python3 $S/cal-write.py create --title "$title" --start "$first_date $start" \
  --end "$first_date $end" --repeat weekly --on "$weekday" --until "$last_date" \
  --location "$room" --calendar "School" --alarm 10
```

`create` refuses an existing title+start pair, so re-running after a failure doesn't
duplicate. Finish with `cal-list.py --week <first week> --calendar School` to show the
result.

## Back up a month, then check the file

```bash
python3 $S/cal-ics.py export --month 2026-11 --out ~/Backups/calendar-2026-11.ics
python3 $S/cal-verify.py ics --file ~/Backups/calendar-2026-11.ics --month 2026-11
```

Use the same period and calendars for both. `--mode occurrences` gives a flat file in
which the VEVENT count equals the number of occurrences, which suits spreadsheets and
counts. `series` (the default) gives a file that re-imports as real recurring events.

## Bring an .ics into a calendar

```bash
python3 $S/cal-ics.py import --file ~/Downloads/conference.ics --calendar Work --dry-run
python3 $S/cal-ics.py import --file ~/Downloads/conference.ics --calendar Work
```

Show the dry run's titles and times first. Existing matches are reported under
`skippedDuplicates`. Calendar's own import (`open -a Calendar file.ics`) opens a GUI
dialog and can't be scripted. Use it only when the user wants to click through.

## Export to CSV for a timesheet

```bash
python3 $S/cal-ics.py export --month last --calendar Work --out work.csv
```

The columns are start, end, allDay, title, calendar, source, location, notes, url,
recurring, rrule, alarms, id and occurrence. Durations are `end - start`.
