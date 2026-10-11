# Contacts surfaces: the `cn` helper, the JSON shape, and AppleScript

## Which path does what

| Job | Contacts framework (`cn`) | AppleScript / JXA |
|---|---|---|
| read contacts, groups | yes, ~1 s for the whole book, unified across accounts | fallback, ~1.2 s bulk read, raw cards, no accounts |
| accounts (containers) | yes | no |
| notes | **no** (needs an Apple entitlement; reading `note` raises) | yes, `person.note` |
| create contact / group in a chosen account | yes | no (always the default account) |
| update a contact, change its groups | yes, unless the contact has a note | yes (used for noted contacts) |
| delete a contact | yes | yes |
| delete a group | yes (members removed first) | yes |
| vCard out | `CNContactVCardSerialization`, 3.0, no NOTE | `person.vcard`, 3.0, with NOTE |
| vCard in | `CNContactVCardSerialization` parse, then save | no import command (`open -a Contacts f.vcf` is a GUI dialog) |

`ct_lib.save()` picks the path per operation, so callers never need to.

## Contact JSON (what `--format json` and `cn contacts` return)

```json
{
  "id": "2BBC6CE8-…:ABPerson", "type": "person",
  "prefix": "", "given": "Zelda", "middle": "", "family": "Kovács", "suffix": "", "nickname": "",
  "org": "Acme", "department": "", "jobTitle": "",
  "emails": [{"label": "work", "value": "zelda@example.com"}],
  "phones": [{"label": "mobile", "value": "+36 30 555 0101"}],
  "urls": [{"label": "homepage", "value": "https://…"}],
  "addresses": [{"label": "home", "street": "", "city": "", "state": "", "postalCode": "", "country": "", "countryCode": "hu"}],
  "birthday": "1990-05-04",
  "containers": ["_local:ABAccount"], "groups": ["9B67…:ABGroup"],
  "name": "Zelda Kovács", "groupNames": ["Skill-Eval"], "accountNames": ["On My Mac"]
}
```

- `birthday` is `YYYY-MM-DD`, or `--MM-DD` without a year.
- Labels are short: `home`, `work`, `other`, `mobile`, `iphone`, `main`, `homefax`,
  `workfax`, `pager`, `school`, `homepage`; anything else is a custom label kept as is.
  Stored labels look like `_$!<Mobile>!$_`; both paths convert.
- `containers` can list more than one account for a contact Contacts links across
  accounts. `note` appears only with `ct-search.py --notes`.
- Ids are the same in the framework and AppleScript (`…:ABPerson`, `…:ABGroup`). A
  unified contact's id is the id of one of its linked cards.

## `cn` commands

```
cn status                                   {"status": "authorized" | "denied" | …}, no prompt
cn containers                               [{id, name, type: local|exchange|cardDAV, default, count}]
cn groups                                   [{id, name, container, count}]
cn contacts [--group ID|--container ID|--ids A,B] [--raw]
cn vcard    [same filters]                  vCard 3.0 text on stdout
cn parse-vcard FILE                         contacts JSON, nothing saved (empty cards are dropped)
cn save < {"ops": [...]}                    {"ok": true, "refs": {ref: id}}
```

Save ops run in order in one `CNSaveRequest` (all or nothing):

```json
{"op": "createGroup", "name": "Club", "container": "_local:ABAccount", "ref": "g"}
{"op": "create", "contact": {…}, "container": "_local:ABAccount", "ref": "new:0"}
{"op": "update", "id": "…:ABPerson", "contact": {…}, "mode": "merge"}
{"op": "addMember", "contact": "new:0", "group": "g"}
{"op": "removeMember", "contact": "…:ABPerson", "group": "…:ABGroup"}
{"op": "delete", "id": "…:ABPerson"}
{"op": "deleteGroup", "id": "…:ABGroup"}
```

`merge` sets non-empty scalars and appends emails/phones/urls/addresses not already
stored (emails case-insensitive, phones by digits). `replace` replaces the given lists.
Call these through `ct_lib.save(ops)`, which sends noted contacts' `update`,
`addMember` and `removeMember` to AppleScript instead.

## AppleScript dictionary (JXA names)

- `Application('Contacts')`: `people`, `groups`, `myCard`, `selection`, `save()`,
  `add(person, {to: group})`, `remove(person, {from: group})`.
- `person`: `id`, `firstName`, `middleName`, `lastName`, `title` (prefix), `suffix`,
  `nickname`, `organization`, `department`, `jobTitle`, `company` (true for an
  organization card), `birthDate`, `note`, `vcard` (read-only, 3.0), `image`;
  elements `emails`, `phones`, `urls`, `addresses` (`street`, `city`, `state`, `zip`,
  `country`, `countryCode`), `relatedNames`, `customDates`, `socialProfiles`,
  `instantMessages`.
- Bulk reads are fast: `app.people.emails.value()` returns one array per person. Per
  element loops are slow; keep to bulk reads.
- New elements: `p.emails.push(app.Email({label: '_$!<Work>!$_', value: 'x@y.z'}))`,
  then `app.save()`; changes without `save()` are lost when Contacts quits.
