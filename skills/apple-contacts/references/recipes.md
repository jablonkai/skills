# Recipes

`S` is this skill's `scripts/` directory.

## Export a group to vCard and CSV

```bash
python3 $S/ct-search.py --groups                      # exact group name, account, size
python3 $S/ct-export.py --group "Running Club" --out ~/Desktop/club.vcf --out ~/Desktop/club.csv
python3 $S/ct-verify.py --group "Running Club" --vcard ~/Desktop/club.vcf   # optional, both directions
```

Report the paths and counts from the JSON (`selected`, `cards`, `rows`, `ok`). Notes
are included (read through AppleScript, which launches Contacts; `--no-notes` skips
them); add `--photos` for pictures (much bigger files). CSV columns: id, name, given,
middle, family, nickname, org, department, jobTitle, emails, phones, addresses, urls,
birthday, note, groups, accounts. Multiple values are `label: value; label: value`.

## Duplicate report the user can act on

```bash
python3 $S/ct-audit.py duplicates                     # Markdown, grouped, with confidence
python3 $S/ct-audit.py duplicates --format csv --out ~/Desktop/duplicates.csv
python3 $S/ct-audit.py duplicates --fuzzy             # adds similar names (Kati / Katalin)
```

Lead with the `high` groups. For each, say what matched (email, phone, name) and the
accounts involved: the same person in Exchange and Google is often a sync artefact, not
a typing slip. Don't merge. If the user then asks to merge one pair: copy the missing
details onto the card to keep with `ct-write.py update --id KEEP --email … --phone …`,
check the read-back, then `ct-write.py delete --id DROP` (preview), then `--yes`.

## Incomplete cards

```bash
python3 $S/ct-audit.py incomplete                               # no name, no email/phone, malformed values
python3 $S/ct-audit.py incomplete --require phones --group Team # team members without a phone
python3 $S/ct-audit.py incomplete --check intl-phone            # numbers without +country code
python3 $S/ct-search.py --missing emails --format csv --out no-email.csv
```

## Import a CSV into a new group

```bash
python3 $S/ct-write.py import --csv people.csv --group "Running Club" --create-group --account "On My Mac" --dry-run
python3 $S/ct-write.py import --csv people.csv --group "Running Club" --create-group --account "On My Mac"
python3 $S/ct-verify.py --group "Running Club" --csv people.csv
```

The dry run lists `created`, `skipped` (with the reason and the matched contact) and the
account. Check that the ignored-column warnings don't hide data the user cares about.
Re-running the import creates nothing new. When the user didn't name an account, use
the default account shown by `contacts.sh check` and tell them which it was.

## Add or fix one person

```bash
python3 $S/ct-search.py -q "anna nagy" --format json          # exists already? get the id
python3 $S/ct-write.py create --given Anna --family Nagy --email work:anna@acme.com \
  --phone mobile:+36301234567 --org Acme --group Team
python3 $S/ct-write.py update --id ID --phone "mobile:+36 30 123 4567" --note "met at UB 2026"
python3 $S/ct-write.py update --id ID --phone "mobile:+36 30 765 4321" --replace   # replace all phones
```

## Back up the address book

```bash
python3 $S/ct-export.py --all --out ~/Backups/contacts-$(date +%F).vcf --photos
python3 $S/ct-export.py --all --out ~/Backups/contacts-$(date +%F).csv
```

The vCard re-imports in Contacts (File › Import) or with `ct-write.py import --vcard`.

## Move people into a group in bulk

```bash
python3 $S/ct-search.py --email @acme.com --format json > /tmp/acme.json
python3 $S/ct-write.py group create Acme --account iCloud
python3 $S/ct-write.py group add Acme --id ID1 --id ID2 …
```

Only contacts in the group's account can join; the others need a group in their own
account.
