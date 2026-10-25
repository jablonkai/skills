---
name: apple-contacts
description: 'Search, export, audit and write Apple Contacts on macOS through the Contacts framework, with JXA where the framework falls short: find people by name, email, phone or company across every account (iCloud, Exchange, Google, On My Mac); export a group or a search to vCard or CSV; report likely duplicates (same name, email or phone) and incomplete cards; create or update contacts and groups from CSV, vCard or flags; every write read back. Read-only by default; never merges or deletes unless asked. Use for "export my Running Club group to vCard and CSV", "find duplicate contacts", "which contacts have no phone number", "import these 5 people from people.csv into a new group", "add a contact for Anna Nagy with her mobile", "back up my address book". Not for Calendar events (apple-calendar), Notes (apple-notes), Mail, Google/Outlook contacts through a web API or connector, or reshaping a CSV/vCard file that never touches the address book.'
summary: "search, export and import Apple Contacts via the Contacts framework and JXA — group and search exports to vCard/CSV, duplicate and incomplete-card reports, contacts and groups created from CSV or vCard, read-back verified"
category: mac-automation
compatibility: "Built for Contacts 14.0 on macOS 27.0.1 (Contacts framework and JXA)."
risk: medium
tags:
    - contacts
    - apple-contacts
    - address-book
    - vcard
    - jxa
    - macos
metadata:
  version: "1.0.1"
---

# Apple Contacts via the Contacts framework

Everything goes through `scripts/`: stdlib Python helpers on top of `cn`, a small
Contacts-framework tool compiled from [cn.swift](scripts/cn.swift) on first use (cached
under `~/Library/Caches/apple-contacts/`). The framework reads a whole address book in
about a second, sees every account, merges cards Contacts links across accounts, and can
create contacts and groups in a chosen account. Contacts' AppleScript can't pick an
account. It fills two gaps: notes (the framework hides them without an Apple
entitlement) and saving contacts that have a note (see [gotchas](references/gotchas.md)).
Contacts doesn't need to be open, but AppleScript steps launch it.

Verified against **Contacts 14.0 on macOS 27.0.1**.

## Privacy and safety rules (read first)

- **Read-only by default.** Search, export, audit and verify change nothing. Write only
  when the user asks for contacts or groups to be added, changed or removed.
- **Report duplicates, don't merge them.** Merging is destructive and loses whichever
  card's data you didn't pick; point the user to Card › Merge Selected Cards in Contacts,
  or merge one pair with `update` + `delete` only when they ask for exactly that.
- **Name the account you write to.** New contacts and groups go to `--account`, else to
  the group's account, else the system default (often iCloud, which syncs to every
  device). Say which one was used. A contact and its group must share an account.
- **Deleting is explicit.** `delete` and `group delete` only preview without `--yes`.
  Deleting a group keeps its members.
- Contacts are personal data: keep them local. No delegate agents, web services or
  uploads, and print only the rows the user needs.

## Setup

```bash
S=scripts   # relative to this skill's directory
```

Go straight to the task: the helpers check access themselves and the first call asks
for permission if needed. Run `bash $S/contacts.sh check` (versions, access, accounts,
groups) only when a helper exits 3 or you need the account list. If access is `denied`,
the user turns on this terminal/IDE in System Settings › Privacy & Security › Contacts
(macOS won't ask again). Until then reads fall back to AppleScript (no accounts, linked
cards not merged) and writes stop with exit 3.

Groups are named by name or id; accounts by name (`iCloud`, `Exchange`, `On My Mac`, or
`local`) or id. Contact ids come from `--format json`.

## Tasks

| The user wants | Run |
|---|---|
| find someone | `python3 $S/ct-search.py -q anna` (name, nickname, company, title, email, phone digits) |
| narrow it down | `ct-search.py --email @acme.com --group Team --account iCloud` (fields AND together) |
| contacts lacking a field | `ct-search.py --missing phones [--group G]` |
| accounts / groups | `ct-search.py --accounts` / `ct-search.py --groups` |
| export a group | `ct-export.py --group "Running Club" --out club.vcf --out club.csv` (notes included; `--photos`, `--no-notes`) |
| back up everything | `ct-export.py --all --out contacts.vcf --photos` |
| duplicates | `ct-audit.py duplicates [--group G] [--fuzzy]` (`--format json/csv`, `--out`) |
| incomplete cards | `ct-audit.py incomplete [--require phones --require emails] [--check intl-phone]` |
| import from CSV | `ct-write.py import --csv people.csv --group "Club" --create-group --account "On My Mac" --dry-run`, then without `--dry-run` |
| import a vCard | `ct-write.py import --vcard cards.vcf --account iCloud [--group G]` |
| add one contact | `ct-write.py create --given Anna --family Nagy --email work:anna@acme.com --phone mobile:+36301234567 [--org Acme] [--group G] [--note "…"]` |
| change one | `ct-write.py update --id ID --phone mobile:+36301234567 [--job-title …]` (merges; `--replace` replaces the lists) |
| group membership | `ct-write.py group create NAME --account A` · `group add NAME --id ID` · `group remove NAME --id ID` |
| remove | `ct-write.py delete --id ID`, then again with `--yes` |
| check a result | `ct-verify.py --group G --csv people.csv` · `--vcard out.vcf` · `--count 5` |

CSV import reads the usual headers (First Name/Last Name or Name, Email, Phone/Mobile,
Company, Job Title, address parts, Birthday, Notes; Google and Outlook exports work) and
warns about columns it ignored. A column holding several values separates them with `;`.

## Workflow

1. **Look before writing** when the request leaves room: if the user didn't name the
   account, the group or what to do with people who already exist, run the import with
   `--dry-run` (or search) and settle that first. When they did, go straight to the
   write; its output already lists what was created, merged and skipped.
2. **Run the helpers,** not hand-written AppleScript or Swift: they handle accounts,
   labels, linked cards, notes, the noted-contact save limit and the duplicate guard.
   Import and create skip a person who already exists (same email, or same name and
   phone), so a re-run creates nothing twice; `--on-duplicate update` merges new details
   into the existing card instead ("update them, don't duplicate"). Skipped and merged
   people are still added to the target group.
3. **Trust the built-in read-back.** `ct-write.py` re-reads every saved contact, note
   and group membership and compares it with the request (`readback.ok`, exit 4 on a
   mismatch); `ct-export.py` re-parses and counts every file it writes. A separate
   `ct-verify.py` run is only for checking files or groups you didn't just write. Report
   the stored names, the account, the group and the counts from that JSON.

## Reporting

- Counts: the framework merges linked cards, so 328 cards can be 292 contacts. Say
  "contacts" for the unified number; `--raw` lists cards (CSV only).
- Duplicates come in groups with a confidence (`high`: name plus email/phone, or email
  plus phone; `medium`: one signal; `low`: `--fuzzy` similar names) and the reason. A
  value shared by more than `--max-shared` contacts (a switchboard number) is ignored
  and listed as such. Present them for the user to decide; don't merge.
- Exports print `selected`, `cards`/`rows` and `ok` per file. vCards are version 3.0.

## Stopping

Every call is a one-shot process with a timeout. Nothing keeps running and nothing
listens on a port. The only thing that can stall is a first-run privacy prompt (Contacts
access, or Automation for `osascript` to control Contacts): answer it and re-run. Exit
codes: 2 bad input or refused, 3 no access, 4 read-back or verification mismatch, 124
timeout.

## References

- [references/recipes.md](references/recipes.md): worked jobs (group export, duplicate
  clean-up plan, CSV import into a new group, address-book backup, fixing incomplete cards).
- [references/contacts-api.md](references/contacts-api.md): the contact JSON fields,
  `cn` commands and save ops, the AppleScript dictionary, and which path does what.
- [references/gotchas.md](references/gotchas.md): permissions, notes and the save limit,
  linked cards, accounts, labels, phone matching, and the security posture.
