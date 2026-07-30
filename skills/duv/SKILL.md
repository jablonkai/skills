---
name: duv
description: "Search and retrieve data from the DUV Ultramarathon Statistics website (statistik.d-u-v.org). Use when the user asks about ultramarathon results, runner profiles, race events, rankings, records, or finishing times — e.g. 'find runner X on DUV', 'what was the Spartathlon 2024 result', 'best 100km times in Hungary', 'lookup ultra runner'. The DUV database covers 10M+ performances, 2.4M+ runners, and 115k+ ultra events worldwide."
---

# DUV Ultramarathon Statistics

The DUV (Deutsche Ultramarathon-Vereinigung) statistics site at `https://statistik.d-u-v.org/` is the canonical database for ultramarathon results worldwide.

**There is no official API.** All data is served as HTML. Use `curl` / `WebFetch` and parse the returned pages.

Parameter names and values were verified against the live HTML forms — neither is always what the on-screen label suggests (e.g. the "country" dropdown on rankings posts as `nat`, not `country`; the "F" option posts as `W`). When in doubt, fetch the page and grep for `name='...'` inside `<select>`/`<input>` elements, and pull `<option value='...'>` to see the exact tokens.

**Bad-parameter failure warning.** Passing a value the backend doesn't recognise is not consistently handled. Depending on the endpoint and parameter, DUV may return a tiny `Error - Invalid input: '<value>'` page, return 0 rows, drop only that filter, or fall back to a broader result set up to a hard row cap (1000 rows on most endpoints, 4000 on `getintbestlist.php`). That's why the exact tokens below matter: a wrong-looking result is often a bad parameter, not a shortage of data. When in doubt, vary one parameter and watch the result count and page heading change.

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

## Shared parameter vocabulary

Different endpoints use different names and different value vocabularies for conceptually similar fields. Pick the right one for the endpoint you're calling.

### Country / nation

One shared scheme, two param names. The same numeric continent codes and IOC-3 country codes work on every country/nation filter — only the param name changes.

- `geteventlist.php`, `calendar.php`, `getresultclub.php` → `country=`
- `getintbestlist.php` → `nat=` (same value vocabulary, different param name)

Accepted values:
- `all` (or omit the param) → worldwide.
- Numeric continent codes: `1`=Europe, `2`=Asia, `3`=Africa, `4`=North America, `5`=South America, `6`=Oceania.
- IOC-3 country codes (e.g. `HUN`, `GER`, `USA`) — work on all four endpoints, including `getintbestlist.php`'s `nat=` even though the visible dropdown there only shows the seven continental options.

The labels shown in the dropdown (`World`, `Europe`, …) are **not** valid values — `nat=Europe` silently returns 0 rows; use `nat=1`. Likewise the worldwide selector is `all`, not `World`.

### Distance (`dist`)

One shared vocabulary across `geteventlist.php`, `getintbestlist.php`, and `calendar.php`. Values are **compact, no spaces, no `+`** — e.g. `100km`, not `100 km` or `100+km`. Bad distance tokens can produce an explicit invalid-input page, 0 rows, or a broader/odd-looking page heading.

- Fixed distances: `50km`, `50mi`, `100km`, `100mi`
- Time-limited: `6h`, `12h`, `24h`, `48h`, `72h`, `6d`, `10d`
- Multi-day / long: `1000km`, `1000mi` (only `getintbestlist.php`)
- Distance-range codes (geteventlist + calendar only): `1` = 45–79 km, `2` = 80–119 km, `4` = 120–179 km, `8` = 180 km+
- `calendar.php` additionally accepts surface tokens in the `dist` slot (same values as `surface`, see next section): `Road`, `Trail`, `Stage`, `Track`, `Indoo`, `Elim`, `Backy`, `Walk`

### Race surface (`surface` on `geteventlist.php`; `dist` slot on `calendar.php`)

Case-sensitive, truncated tokens exactly as they appear in the form dropdown. Common full-word variants (`road`, `trail`, `indoor`, `elimination`, `backyard`, `walking`) are NOT recognised and may return `Error - Invalid input`, be ignored, or return 0 rows. `getresultclub.php` has *no* surface filter — its `racetype` param is something else entirely (see that section).

- `Road` — road race
- `Trail`
- `Stage` — stage race
- `Track`
- `Indoo` — indoor (yes, truncated at 5 chars)
- `Elim` — elimination race
- `Backy` — Backyard Ultra
- `Walk` — ultra-walking

Omit the param or pass `all` for no surface filter.

### Year

- Most endpoints: a 4-digit year (e.g. `2024`) or `all`. `geteventlist.php` years go back to 1798.
- `calendar.php` additionally: `futur` = all upcoming from today, `past1` = 1 year back from today. (Plain `past` is *not* recognised — use `past1`.)

### Gender (`getintbestlist.php` only)

`gender=M|W`. The form *label* for the female list renders as "F", but the posted *value* is `W` — `gender=F` silently returns zero rows.

### Age category (`cat` on `getintbestlist.php`)

Gender-prefixed tokens, paired with the `gender` value:

- Male list (`gender=M`): `all`, `MU23`, `M23`, `M35`, `M40`, `M45`, `M50`, `M55`, `M60`, `M65`, `M70`, `M75`, `M80`, `M85`, `M90`
- Female list (`gender=W`): `all`, `WU23`, `W23`, `W35`, … `W90`

### IAU label (`label`)

Filters to IAU-labelled events only. The form *value* differs between the two endpoints — same concept, different token:

- `geteventlist.php` → `label=Y`
- `getintbestlist.php` → `label=IAU`

Omit the param (or pass empty) for "all events". The dropdown label "IAU-Label" is the visible text, not the value — passing `label=IAU-Label` silently drops the filter on both endpoints, and `label=Y` silently drops it on `getintbestlist.php`.

## Endpoint reference

### `searchrunner.php` — runner search

```
curl -sL "https://statistik.d-u-v.org/searchrunner.php?sname=Jablonkai&language=EN"
```

- `sname` — full-text, ≥2 characters. Can be surname, firstname, or substring.
- **One match** → 302 redirect to `getresultperson.php?runner=<id>`. Use `curl -L` and `-w "%{url_effective}"` to see the resolved id.
- **Many matches** → HTML list of `getresultperson.php?runner=<id>` links. Parse with `getresultperson\.php\?runner=[0-9]+`.
- Accent-insensitive on most characters; try both accented and non-accented forms if nothing comes back.

### `getresultperson.php` — runner profile

```
curl -s "https://statistik.d-u-v.org/getresultperson.php?runner=401716&language=EN"
```

- `runner=<id>` is the only meaningful param (besides `language`). No filter controls.
- The page is split into three blocks worth knowing about:
  1. **Header** — DOB, nationality, club, age-group categories (German + international) computed from DOB.
  2. **Per-year results** — chronological list of every performance, grouped by year. This is the only place to find non-standard distances (e.g. an 81 km or 111 km race finish) — they don't appear in the PB table below.
  3. **Personal bests** table — best time per *officially-rankable* distance (50 km, 100 km, 6 h, 12 h, 24 h, 48 h, 6 d, …), with the year of that PB and the runner's rank that year (international/national, in parentheses). This is the canonical answer to "what's their best 100 km?" — but only when there is an actual `100 km` row. Do not infer a 100 km PB from an 81 km, 111 km, 100 mi, or split-looking result unless the page explicitly lists a 100 km performance. For "best result longer than 100 km" or any odd distance, scan the per-year listing instead.
  4. **Comparison table** — for races the runner has finished multiple times, a year-by-year grid of their times. Useful for trend-spotting on a single runner; you don't need to fetch a second runner to render it.

### `searchevent.php` — event search

```
curl -sL "https://statistik.d-u-v.org/searchevent.php?sname=Spartathlon&language=EN"
```

- `sname` — ≥3 characters. Matches **event name OR start town/location**.
- Same one-match-302 / many-match-list behavior as `searchrunner.php`.
- Result links: `getresultevent.php?event=<id>`.

### `getresultevent.php` — event results

```
curl -s "https://statistik.d-u-v.org/getresultevent.php?event=100580&language=EN"
```

- `event=<id>` is the main param.
- Each finisher row links to `getresultperson.php?runner=<id>`.
- The header gives date, event name, distance/type, finisher count, ranking eligibility, and source, but it may not expose the start town as a clean field.
- Follow the page's "More details of this race" link to `eventdetail.php?event=<id>` when the user asks for host town, start location, organizer, address, status, participant limit, course notes, or other event metadata.
- The page also surfaces view toggles (avg-speed unit km/h vs min/km, category scheme: German / international / event-specific, nation highlight). In practice, scrape the default view and compute derivations locally — the page URL params for these toggles are unstable.
- Some events bundle several races (e.g. 50k + 100k on the same day) under separate event IDs — resolve each via `searchevent.php` or `geteventlist.php` rather than guessing.

### `eventdetail.php` — event metadata/details

```
curl -s "https://statistik.d-u-v.org/eventdetail.php?event=111652&language=EN"
```

- `event=<id>` is the main param.
- Use this endpoint after `geteventlist.php`, `calendar.php`, `searchevent.php`, or `getresultevent.php` when the user needs fields beyond the result row.
- The stable metadata labels include **Date**, **Event**, **Start in (Country)**, **Length/Duration**, **Ranking eligible**, **IAU-Label**, **Status**, **Participants limit**, organizer/contact fields, and course details when available.
- `Start in (Country)` is the clean source for "host town" / "venue town" on past-event queries. Do not guess the town from the event name; some event names include sponsors, race formats, or series names rather than the actual start location.

### `geteventlist.php` — past-event browse/filter

```
curl -s "https://statistik.d-u-v.org/geteventlist.php?year=2024&country=HUN&dist=100km&language=EN"
```

Confirmed form field names (authoritative):

- `year` — 4-digit year, or `all`. Default = current year.
- `country` — IOC-3, or `all`.
- `dist` — shared `dist` vocabulary above (`100km`, `24h`, `6d`, range codes `1`/`2`/`4`/`8`, …). No `+` or spaces.
- `surface` — **NOT `racetype`**. Values: see the race-surface vocabulary above (`Road`, `Trail`, `Stage`, `Track`, `Indoo`, `Elim`, `Backy`, `Walk`, case-sensitive). Lowercase full words are not reliable.
- `label` — **NOT `iau`**. Values: omit (= all) or `Y` (= IAU-labelled). (Note: on `getintbestlist.php` the equivalent value is `IAU`, not `Y` — the two endpoints diverge here.)
- `from`, `to` — distance bounds in **kilometres** (text inputs in the form labelled "Length from X to Y km"), independent of the `dist` dropdown's range codes. `from=80&to=120` is valid and matches events in that km range. Omit either side for an open-ended bound. Time-based events (24h, 6d) won't match a km filter — for those use `dist=24h` etc. To filter on the dropdown's preset buckets instead, use `dist=1|2|4|8`.
- `sort` — `1` (Date — default) or `2` (Finishers). The form uses numeric values; passing the dropdown labels (`Date`, `Finishers`) silently falls back to default sort.
- `club` — optional filter by club (string, partial match).

Response: HTML table, one row per event, with `getresultevent.php?event=<id>` links. The list row has date, event name, distance, finisher count, and IAU label; it does **not** include a separate host-town column. If the user asks for town/venue/start location, follow each event ID to `eventdetail.php?event=<id>` and read `Start in (Country)`. The default page size is up to 1000; results beyond that require narrower filters.

### `calendar.php` — upcoming / future-race calendar

```
curl -s "https://statistik.d-u-v.org/calendar.php?year=futur&dist=6d&country=4&cups=0&rproof=0&mode=list&language=EN"
```

Use `calendar.php` — **not** `geteventlist.php` — whenever the user asks about upcoming, future, or scheduled races. `geteventlist.php` is tuned for completed events with results; `calendar.php` is the forward-looking view and exposes extra filters.

- `year` — `futur` (from today on), `past1` (1 year back), a specific 4-digit year (the dropdown offers 1990 through next year, e.g. `2026`, `2027`, `2014`), or `all`. Plain `past` is *not* a valid token.
- `country` — IOC-3 for a country, or numeric `1`–`6` for a continent (`1`=Europe, `2`=Asia, `3`=Africa, `4`=North America, `5`=South America, `6`=Oceania).
- `dist` — shared `dist` vocabulary above; also accepts surface tokens (`Road`, `Trail`, …) in this slot.
- `cups` — numeric token: `0`=all, `1`=DUV-Cup, `2`=DUV-50km-Cup, `3`=DUV-6h-Cup, `4`=IAU-50k-Trophy, `5`=Championships, `6`=ECU, `7`=Anglo Celtic Plate. (The form shows names; the posted value is the numeric id.)
- `rproof` (ranking-eligible) — `0`=all, `1`=yes, `2`=no.
- `mode` — `list` (tabular) or `map`.
- `radius` — kilometers around a location; only meaningful together with the site's lat/lon context. Leave blank unless reproducing a user-supplied URL.
- `norslt=1` — "without result list": hide events that already have posted results (useful when combined with past years to find events that haven't published results yet). Omit for normal behaviour.

Result table columns: **Date | Event | Distance/Duration | Venue (Country) | Status | IAU-Label | Results**. The "Results" column links to `getresultevent.php?event=<id>` for completed events; pre-race / upcoming events link to `eventdetail.php?event=<id>` instead. Use `eventdetail.php` for richer race metadata.

**Date windows need client-side filtering.** `calendar.php` has broad `year` modes but no exact `from`/`to` date filters. For requests like "next 30 days", "next year", or "between June and August", fetch a broad calendar set (`year=futur` or the relevant specific years), parse the row's start date, and filter locally to the requested window. State the cutoff you used. `year=futur` means "all future from today", not "the next 12 months".

Calendar dates can be single dates (`29.05.2026`) or ranges (`13.-14.06.2026`, `30.10.-02.11.2026`). Use the start date for window filtering, and keep the raw DUV date string in the answer if the range is awkward or appears inconsistent.

Result count is stated inline as `1 to N of M search results` — there is no pagination, so if `N < M` you need to narrow filters. In practice the hard cap is the same 1000-row ceiling as elsewhere on the site.

**Submit.x / Submit.y in pasted URLs.** When a user pastes a calendar URL from their browser you'll often see `Submit.x=<n>&Submit.y=<n>` tacked on — those are the pixel coordinates of the click on the form's image submit button and carry no filter meaning. Drop them when scripting; keeping them doesn't hurt but adds noise.

### `getintbestlist.php` — international rankings

```
curl -s "https://statistik.d-u-v.org/getintbestlist.php?year=2024&dist=100km&gender=M&nat=HUN&language=EN"
```

Confirmed form field names:

- `year` — 4-digit, or `all` for the all-time list. The dropdown shows 2005 onward, but earlier years still parse and return data (sparser as you go back, e.g. ~120 women on 24h in 1990).
- `dist` — shared `dist` vocabulary (`100km`, `24h`, `6d`, …) **plus** `1000km`, `1000mi` which only appear here. No `+` or spaces.
- `nat` — **NOT `country`** (different param name, same value vocabulary as the country/nation section above). `all` (or omit) for World; numeric `1`–`6` for continents (Europe=1, …, Oceania=6); IOC-3 country codes work even though they're not in the visible dropdown. The English labels (`World`, `Europe`, …) are *not* valid values.
- `gender` — `M` or `W`. (The form label reads "F" for the female list, but the posted value is `W`; `gender=F` silently returns zero rows.)
- `cat` — **NOT `AgeGrp`**. Age-group code, gender-prefixed: `all`, `MU23`/`WU23`, `M23`/`W23`, `M35`/`W35`, … up to `M90`/`W90`. Must match the `gender` value.
- `label` — omit for all events, or `IAU` for IAU-labelled only. (`Y` is the value on `geteventlist.php` but is silently dropped here. `IAU-Label` is the dropdown *text*, never the value.)
- `hili` (highlight) — overlay highlight for a country (IOC-3) or `none`/`GER`.
- `tt` (time type) — `netto` or `brutto`.
- `club` — optional club filter.

**Page cap on this endpoint is 4000 rows**, higher than the 1000-row cap elsewhere. The unfiltered all-time list is around 15 000 entries, so you still need filters to see the tail.

**The response table is self-contained — don't re-fetch what's already there.** Each row carries: rank, performance (distance or time), athlete name (linked to `getresultperson.php`), nation (IOC-3), date of birth, age category, performance date, and **event name with venue town** (linked to `getresultevent.php`). For "top-N" answers there is no need to follow each event link to `eventdetail.php` — the venue and event name are already inline. Only drill down when the user asks for a metadata field that the row doesn't carry (organizer, course notes, participant cap, etc.).

**`nat=` filters by athlete nationality, not race venue.** A query like `nat=1` (Europe) returns the year's best performances by *European-passport athletes*, including ones run on non-European tracks (e.g. a French runner setting a 24 h mark in Phoenix shows up in the Europe list). For "best performances at events held in Europe", `nat=` is the wrong tool — fetch the worldwide list and filter client-side by the venue / event country, or pull `geteventlist.php` for the year+continent and aggregate from there. When the user's phrasing is ambiguous (e.g. "best women's 24 h in Europe"), name the interpretation you picked and offer the other one.

**Multi-performance rows.** When an athlete has more than one ranking-eligible result in the year, DUV adds secondary rows tagged like `(2)`, `(3)` after their primary entry. These dilate the visible row count without adding distinct athletes — strip them before counting "top N runners" or you'll under-report unique names.

### `getresultclub.php` — club view

```
curl -s "https://statistik.d-u-v.org/getresultclub.php?club=<name-or-id>&year=2024&language=EN"
```

Confirmed form field names — note the value vocabularies here look nothing like `geteventlist.php`'s, and the param *names* are deceptive (`racetype` is not a surface filter, `aktype` is not ranking-eligibility):

- `club` — partial match on club name (3–25 chars), or a club id if you already have one. The page has no separate "find a club" search — start by `searchrunner.php`-ing one of the club's runners and reading their profile, or call this endpoint with a partial name and pick from the results.
- `sname` — optional runner-name filter within the club.
- `year` — 2001–current, or `all`.
- `racetype` — **ranking-eligibility flag**, despite the name. Values: `''` (omit) for all races, `Y` for ranking-eligible only. There is **no surface filter** on this endpoint — to get a club's road/trail-only results you have to filter client-side after fetching.
- `aktype` — **age-category scheme**, despite the name. Values: `1` (Cat. german, default), `2` (Cat. internat.), `3` (event-specific). This only changes how rows are categorised in the displayed table; it does not filter the result set.
- `sort` — `1` (Runner, Start date — default) or `2` (Distance, Performance). String values (`Distance`, `Performance`, etc.) silently fall back to default.

### `bulk_search.php` — POST-only bulk lookup

Paste a list of names (tab/semicolon/comma/space-separated) into the textarea and configure column mappings (surname, first name, gender, nationality, birth, age group, bib, DUVID). Supports a reference discipline (50km, 50mi, 100km, 100mi, 6h, 12h, 24h, 48h, 6 days, Backyard) and age-category scheme (international, German, French, Italian). Output is HTML; no documented CSV export.

For scripted use, `getresultperson.php` + `searchrunner.php` per name is usually simpler than automating the bulk form.

### Overview pages

`overview_intbestlist.php`, `overview_dtbestlist.php`, `overview_records.php`, `overview_champions.php`, `overview_cups.php` are navigation hubs — static landing pages that link into the filterable endpoints above. Follow the links rather than trying to parameterize them.

### RSS feeds

`latestresults_rss.php` and `xml/nextraces_rss.php` are the only structured-data endpoints on the whole site. Useful for "what's new" checks.

## Scraping tips

- Always append `&language=EN` so labels are predictable.
- Use `curl -sL` to follow the single-match redirects from search endpoints.
- Parse IDs with regex — the HTML is stable but not semantic.
- HTML entities: links contain `&amp;` — decode before following.
- Be polite: sequential requests with small delays. The site is community-run.
- If a param you expect isn't filtering, fetch the page and check both the `name='...'` attribute *and* the `<option value='...'>` text in the form HTML — param names *and* value tokens both diverge from user-facing labels. Recurring traps:
  - `nat` vs "Country" on rankings; the worldwide value is `all`, not `World`; continents are numeric `1`–`6`, not their English names.
  - `gender=W` (not `F`) for the women's list.
  - `surface=Indoo` / `Backy` / `Elim` / `Walk` (5-char truncation, case-sensitive) — full words like `Backyard` can fail with `Error - Invalid input`, and lowercase words can fail or get ignored.
  - `label` value differs by endpoint: `Y` on `geteventlist.php`, `IAU` on `getintbestlist.php`.
  - `sort` is numeric (`1`/`2`) on `geteventlist.php` and `getresultclub.php` — not the dropdown labels.
  - `racetype`/`aktype` on `getresultclub.php` are misleadingly named (see that section).
  - Page caps: 1000 rows on most endpoints, **4000** on `getintbestlist.php`. A wrong-looking value may parse as "no filter", partially apply other filters, return 0 rows, or produce a short invalid-input page.

## When unsure of an ID

Never guess runner, event, or club IDs — always resolve them via `searchrunner.php` / `searchevent.php` / `getresultclub.php` first, or via `geteventlist.php` filters. IDs are opaque and not derivable from names.
