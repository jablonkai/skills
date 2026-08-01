---
name: duv
description: "Search and retrieve data from the DUV Ultramarathon Statistics website (statistik.d-u-v.org). Use when the user asks about ultramarathon results, runner profiles, race events, rankings, records, or finishing times — e.g. 'find runner X on DUV', 'what was the Spartathlon 2024 result', 'best 100km times in Hungary', 'lookup ultra runner'. The DUV database covers 10M+ performances, 2.4M+ runners, and 115k+ ultra events worldwide."
summary: "search and retrieve data from the DUV Ultramarathon Statistics website (statistik.d-u-v.org), including runner profiles, events, and rankings"
category: data-lookup
risk: low
tags:
  - ultrarunning
  - duv
  - race-results
  - statistics
  - web-scraping
allowed-tools: Bash, Read, WebFetch
argument-hint: "[runner name, event name, or ranking query]"
---

# DUV Ultramarathon Statistics

The DUV (Deutsche Ultramarathon-Vereinigung) statistics site at `https://statistik.d-u-v.org/` is the canonical database for ultramarathon results worldwide.

**There is no official API.** All data is served as HTML. Use `curl` / `WebFetch` and parse the returned pages.

**Bad-parameter failure warning.** Passing a value the backend doesn't recognise is not consistently handled. Depending on the endpoint and parameter, DUV may return a tiny `Error - Invalid input: '<value>'` page, return 0 rows, drop only that filter, or fall back to a broader result set up to a hard row cap (1000 rows on most endpoints, 4000 on `getintbestlist.php`). That's why exact tokens matter: a wrong-looking result is often a bad parameter, not a shortage of data. When in doubt, vary one parameter and watch the result count and page heading change.

## Detailed references

Load these on demand — don't read them up front:

- [references/parameters.md](references/parameters.md) — shared value vocabularies (country/nation, distance, surface, year, gender, age category, IAU label). Read this whenever a query needs a filter beyond a plain id lookup.
- [references/endpoints.md](references/endpoints.md) — per-endpoint parameters, example `curl` calls, and response shapes. Read the section for the endpoint you're about to call.

## Core URL patterns

All endpoints are under `https://statistik.d-u-v.org/`. Every endpoint accepts `language=EN|DE|FR|ES|IT|RU|ZH|JA` — always pass `language=EN` for consistent parsing.

| Endpoint | Purpose | Primary params |
|---|---|---|
| `searchrunner.php` | Search runners by name | `sname` |
| `getresultperson.php` | Runner profile + all results | `runner` |
| `searchevent.php` | Search events by name or town | `sname` |
| `getresultevent.php` | Race results + finisher list | `event` |
| `eventdetail.php` | Race metadata/details: date, start town, length, organizer | `event` |
| `geteventlist.php` | Browse/filter past events | `year`, `country`, `dist`, `surface`, `label`, `from`, `to`, `sort` |
| `getresultclub.php` | Club results | `club`, `year`, `racetype`, `aktype`, `sort` |
| `getintbestlist.php` | International rankings | `year`, `dist`, `nat`, `gender`, `cat`, `label`, `hili`, `tt` |
| `calendar.php` | Race calendar (upcoming/future events) | `year`, `country`, `dist`, `cups`, `rproof`, `mode`, `radius` |
| `bulk_search.php` | Bulk runner search (POST, textarea of names) | form-encoded |
| `overview_intbestlist.php` | International rankings overview | — |
| `overview_dtbestlist.php` | German rankings overview | — |
| `overview_records.php` | Records overview | — |
| `overview_champions.php` | Championships overview | — |
| `overview_cups.php` | Cups overview | — |
| `latestresults_rss.php` | Recent results RSS feed | — |
| `xml/nextraces_rss.php` | Upcoming races RSS feed | — |

## Choosing an endpoint

- **Past races with results** → `geteventlist.php`; **upcoming/scheduled races** → `calendar.php`. They are tuned for opposite directions in time.
- **A runner's best time at a standard distance** → the personal-bests table on `getresultperson.php`; **any non-standard distance** → that page's per-year listing instead.
- **"Top N in year X"** → `getintbestlist.php`. Its rows already carry athlete, nation, date and venue — don't follow each event link.
- **Host town, organizer, participant cap, course notes** → `eventdetail.php?event=<id>`, reached from any list or result page.

Read the matching section of [references/endpoints.md](references/endpoints.md) before building the URL.

## Scraping tips

- Always append `&language=EN` so labels are predictable.
- Use `curl -sL` to follow the single-match redirects from search endpoints.
- Parse IDs with regex — the HTML is stable but not semantic.
- HTML entities: links contain `&amp;` — decode before following.
- Be polite: sequential requests with small delays. The site is community-run.
- If a param you expect isn't filtering, fetch the page and check both the `name='...'` attribute *and* the `<option value='...'>` text in the form HTML — param names *and* value tokens both diverge from user-facing labels. Recurring traps (full detail in [references/parameters.md](references/parameters.md)):
  - `nat` vs "Country" on rankings; the worldwide value is `all`, not `World`; continents are numeric `1`–`6`, not their English names.
  - `gender=W` (not `F`) for the women's list.
  - `surface=Indoo` / `Backy` / `Elim` / `Walk` (5-char truncation, case-sensitive) — full words like `Backyard` can fail with `Error - Invalid input`, and lowercase words can fail or get ignored.
  - `label` value differs by endpoint: `Y` on `geteventlist.php`, `IAU` on `getintbestlist.php`.
  - `sort` is numeric (`1`/`2`) on `geteventlist.php` and `getresultclub.php` — not the dropdown labels.
  - `racetype`/`aktype` on `getresultclub.php` are misleadingly named — see their section in [references/endpoints.md](references/endpoints.md).
  - Page caps: 1000 rows on most endpoints, **4000** on `getintbestlist.php`. A wrong-looking value may parse as "no filter", partially apply other filters, return 0 rows, or produce a short invalid-input page.

## When unsure of an ID

Never guess runner, event, or club IDs — always resolve them via `searchrunner.php` / `searchevent.php` / `getresultclub.php` first, or via `geteventlist.php` filters. IDs are opaque and not derivable from names.
