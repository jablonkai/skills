---
name: duv
description: "Search, retrieve and analyse data from the DUV Ultramarathon Statistics database (statistik.d-u-v.org, 10M+ results, 2.4M+ runners, 115k+ events). Use whenever the user asks about ultramarathon results, runners, races or rankings: national, continental and age-group records and their progression, personal bests, race results and course records, race history and winners, race calendars, IAU championship medallists, head-to-head comparisons, lifetime or yearly ultra mileage, oldest finishers, women who won outright, doping cases. Examples: 'Hungarian 100 km record', 'Spartathlon 2024 results', 'top 24 h women in 2024', 'course record at Ultrabalaton', 'who ran the most km in 2025', 'compare runner A and B'. Also Hungarian: 'országos csúcs', 'magyar rekord', 'pályacsúcs', 'ultrafutó eredmények', 'ki futott a legtöbbet', 'VB-érmesek'. Not for training data from Garmin/Strava or ITRA trail scores."
summary: "search and analyse the DUV Ultramarathon Statistics database (statistik.d-u-v.org) — runner profiles, event results and course records, rankings, calendars, national/continental records and their progression, IAU championships, head-to-head and mileage statistics"
category: data-lookup
risk: low
tags:
  - ultrarunning
  - duv
  - race-results
  - records
  - statistics
  - json-api
allowed-tools: Bash, Read, WebFetch
argument-hint: "[runner name, event name, ranking or record query]"
metadata:
  version: "1.1.0"
---

# DUV Ultramarathon Statistics

`https://statistik.d-u-v.org/` is the canonical database of ultramarathon results worldwide.
It has **no documented API, but it does have a JSON one**: the `json/m*.php` endpoints that
feed the DUV mobile app return clean JSON for runners, events, results, rankings, the calendar
and national records. Use those first; scrape the HTML only for the handful of pages without a
JSON twin. Everything is public and unauthenticated — but volunteer-run, so keep requests
sequential and spaced.

## Fastest path: the bundled client

`scripts/duv.py` (Python 3, standard library) wraps every JSON endpoint and prints CSV by
default (`--format md|json`, `--out FILE`). Run it from the skill directory:

```bash
python3 scripts/duv.py records --nat HUN --dist 100km --dist 24h            # national records
python3 scripts/duv.py records --nat HUN --dist all --overall-only --format md
python3 scripts/duv.py records --nat 1 --dist 24h --type track --gender W     # Europe, track, women
python3 scripts/duv.py rankings --year 2024 --dist 100km --gender W --nat HUN
python3 scripts/duv.py rankings --year all --dist 24h --gender M --pages all --primary-only --out 24h.csv
python3 scripts/duv.py runner --name "Berces, Edit"          # or --id 5752
python3 scripts/duv.py search-event "Spartathlon"            # or "York,100,USA"
python3 scripts/duv.py event --id 100580                     # finisher list (scraped HTML)
python3 scripts/duv.py event-detail --id 100580              # organizer, venue, editions
python3 scripts/duv.py calendar --year 2024 --country HUN --dist 100km
python3 scripts/duv.py get "json/msearchrunner.php?sname=Jablonkai"   # any JSON URL, raw
```

Derived views and HTML-only pages, also one command each:

```bash
python3 scripts/duv.py event-history --id 100580 --format md   # editions, winners, course records
python3 scripts/duv.py multiple-finishers --id 100580           # most finishes of a race series
python3 scripts/duv.py event-list --year 2024 --country HUN --from 80 --to 120 --sort finishers
python3 scripts/duv.py progression --nat HUN --dist 24h --gender W   # record progression
python3 scripts/duv.py head-to-head --runner 3510 --runner "Sipos, Istvan"
python3 scripts/duv.py champions --dist 24hWC --cnt 3           # IAU WC/EC medallists, every edition
python3 scripts/duv.py stats lifetime-mileage --country HUN     # also: year-km, oldest-finishers,
#   timespan, female-winners, top-abroad, long-running-races, 100x100mi, doping
```

`python3 scripts/duv.py <subcommand> -h` lists every flag. The script handles the two things
that trip up hand-written calls — the UTF-8 BOM some responses carry, and the fact that DUV
answers an **unrecognised parameter value with an empty 200 body** rather than an error. If
Python's `urllib` can't verify the site certificate (a bare python.org install on macOS) it
silently retries through `curl`. The server drops or refuses connections in bursts; the
script retries those with a growing pause, so don't wrap it in your own retry loop.
An HTTP 401 means DUV has put that endpoint behind a login — switch to its HTML twin rather
than retrying. A 404 from `meventdetail.php` is *not* an error: the body is the full payload, and
the script uses it.

## Records — the most asked-for thing

DUV lists *best performances*, not ratified records, and says so on every records page. Report
a "national record" from here with that one-sentence caveat; for official world records send
the user to the IAU table (linked from `overview_records.php`). What exists:

| Ask | Do |
|---|---|
| National record, country X, distance D, either gender | `records --nat X --dist D` — both genders and every age group come back in one call |
| All records of a country / several countries | `--dist all`, repeat `--nat`; add `--overall-only` for just the open records |
| Continental bests | `--nat 1..6` (1 Europe, 2 Asia, 3 Africa, 4 N. America, 5 S. America, 6 Oceania) |
| Road / track / indoor only | `--type road|track|indoor` (default `overall`) |
| Age-group (masters) records | every row is an age group; `--cat DOB` = IAU groups (U23/23/35/40…), `--cat YOB` = German year-of-birth groups (U20/20/30/35…) |
| World record | not on DUV → IAU; the unofficial "best ever" is `rankings --year all --dist D --gender G`, first row |
| German official records | `recordsGER.php?dist=D` (HTML only) |

Read [references/records.md](references/records.md) before answering any records question — it
covers the `S`/`T`/`I` split-track-indoor flags (a 100 km *split* inside a 24 h is not a
stand-alone race record), scheme differences, and how to phrase the answer.

## Choosing an endpoint

| Need | Endpoint (JSON unless noted) |
|---|---|
| Runner ID from a name | `msearchrunner.php?sname=Surname,Given` |
| Profile, PBs, every result, year-by-year comparison | `mgetresultperson.php?runner=<id>` — PBs only for ranking-eligible distances; odd distances (81 km, 111 km) live in `AllPerfs` |
| Event ID from a name or town | `msearchevent.php?sname=Name,100,HUN` — hits already carry full metadata |
| Finisher list | `getresultevent.php?event=<id>` (HTML, 2000 rows per `page`) — the JSON twin `mgetresultevent.php` now answers 401 (needs a login token); `duv.py event` scrapes the HTML |
| Host town, organizer, limits, every past edition | `meventdetail.php?event=<id>` — `editions[]` walks a race's history |
| Top-N in a year / all-time list | `mgetintbestlist.php` — 400 rows per `page`, no hard cap; rows carry athlete, nation, date and venue, so don't follow links |
| National / continental records | `mbestperfcountry.php` — see above |
| Races in a year, past or future | `mcalendar.php?year=2024|futur&country=HUN&dist=…` — finished ones have `Results: "C"` |
| Past events with finisher counts, km bounds (`from`/`to`), sort by finishers | `geteventlist.php` (HTML) |
| Club results | `getresultclub.php` (HTML) |
| Course record, winners per edition, race history | `event-history` (from `meventdetail.php`) — `getresulteventalltime.php` now answers 404 |
| Statistics, championships, cups, German lists | HTML pages in [references/statistics.md](references/statistics.md) |

Details: [references/json-api.md](references/json-api.md) for every JSON field,
[references/endpoints.md](references/endpoints.md) for the HTML pages and their form quirks,
[references/parameters.md](references/parameters.md) for the shared value vocabularies. Read the
section for the endpoint you're about to call rather than all of it.

## Questions that need more than one call

Course records, record progression, head-to-head, a runner's career curve, "who ran the most",
medal tables, the biggest races of a country: [references/analysis.md](references/analysis.md)
maps each to a recipe, with the limits to state in the answer (ranking-eligible results only,
splits, netto vs brutto, derived vs listed figures). Read it for any question that is not a
single lookup.

## Traps worth knowing before the first request

- **Exact tokens or nothing.** `dist=100km` not `100 km`; `gender=W` not `F`; `nat=1` not
  `Europe`; `surface=Backy`/`Indoo` (5-char truncation, case-sensitive). JSON answers a bad
  token with an empty body; HTML pages may return 0 rows, drop the filter, or show a tiny
  `Error - Invalid input` page. A suspicious result is usually a bad parameter, not missing data.
- **`nat` filters by athlete nationality, not venue.** "Best 24 h run in Europe" needs the world
  list filtered client-side on the event `Country`.
- **Multi-performance rows** in rankings are ranked `(2)`, `(3)` … — strip them before counting
  distinct athletes (`--primary-only`).
- **No world scope on records.** `nat=all` returns nothing there.
- **Same concept, different token per page:** `label=Y` on `geteventlist.php` vs `label=IAU` on
  the rankings; `country=` on the calendar vs `nat=` on rankings and records; `sort=1|2`
  numeric on the HTML lists.
- **Calendar quirks.** `calendar --year all` means *from today on*; loop the years for
  history. The JSON calendar ignores `cups`, so filter championships with `--cupname "NC 24h"`.
- **Never guess IDs.** Runner, event and club IDs are opaque — resolve them by search first.
  When a name search returns several people, `ActivRange` (years active) and `YOB` separate
  namesakes faster than opening each profile.
- **Privacy.** Runners with `Privacy: "1"` asked to be anonymised; don't work around it.

## Answering well

Give DUV IDs or links so the user can check, and say when a figure is derived (course record
from edition winners, progression replayed from the ranking) rather than listed by DUV. Name
the scope you used (country vs nationality, year vs all-time, surface, age scheme, splits
included or not). Keep DUV's `dd.mm.yyyy` vs ISO date difference in mind when sorting across
endpoints. When a question is ambiguous — "best women's 24 h in Europe" — pick the more likely
reading, say which one, and offer the other.
