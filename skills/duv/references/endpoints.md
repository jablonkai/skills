# DUV endpoint reference

Per-endpoint parameters and response shapes. Value vocabularies shared across endpoints
(country/nation, distance, surface, year, gender, age category, IAU label) live in
[parameters.md](parameters.md).

All endpoints are under `https://statistik.d-u-v.org/` and accept
`language=EN|DE|FR|ES|IT|RU|ZH|JA` — always pass `language=EN` for consistent parsing.

## `searchrunner.php` — runner search

```
curl -sL "https://statistik.d-u-v.org/searchrunner.php?sname=Jablonkai&language=EN"
```

- `sname` — full-text, ≥2 characters. Can be surname, firstname, or substring.
- **One match** → 302 redirect to `getresultperson.php?runner=<id>`. Use `curl -L` and
  `-w "%{url_effective}"` to see the resolved id.
- **Many matches** → HTML list of `getresultperson.php?runner=<id>` links. Parse with
  `getresultperson\.php\?runner=[0-9]+`.
- Accent-insensitive on most characters; try both accented and non-accented forms if nothing comes
  back.

## `getresultperson.php` — runner profile

```
curl -s "https://statistik.d-u-v.org/getresultperson.php?runner=401716&language=EN"
```

- `runner=<id>` is the only meaningful param (besides `language`). No filter controls.
- The page is split into blocks worth knowing about:
  1. **Header** — DOB, nationality, club, age-group categories (German + international) computed
     from DOB.
  2. **Per-year results** — chronological list of every performance, grouped by year. This is the
     only place to find non-standard distances (e.g. an 81 km or 111 km race finish) — they don't
     appear in the PB table below.
  3. **Personal bests** table — best time per *officially-rankable* distance (50 km, 100 km, 6 h,
     12 h, 24 h, 48 h, 6 d, …), with the year of that PB and the runner's rank that year
     (international/national, in parentheses). This is the canonical answer to "what's their best
     100 km?" — but only when there is an actual `100 km` row. Do not infer a 100 km PB from an
     81 km, 111 km, 100 mi, or split-looking result unless the page explicitly lists a 100 km
     performance. For "best result longer than 100 km" or any odd distance, scan the per-year
     listing instead.
  4. **Comparison table** — for races the runner has finished multiple times, a year-by-year grid of
     their times. Useful for trend-spotting on a single runner; you don't need to fetch a second
     runner to render it.

## `searchevent.php` — event search

```
curl -sL "https://statistik.d-u-v.org/searchevent.php?sname=Spartathlon&language=EN"
```

- `sname` — ≥3 characters. Matches **event name OR start town/location**.
- Same one-match-302 / many-match-list behavior as `searchrunner.php`.
- Result links: `getresultevent.php?event=<id>`.

## `getresultevent.php` — event results

```
curl -s "https://statistik.d-u-v.org/getresultevent.php?event=100580&language=EN"
```

- `event=<id>` is the main param.
- Each finisher row links to `getresultperson.php?runner=<id>`.
- The header gives date, event name, distance/type, finisher count, ranking eligibility, and source,
  but it may not expose the start town as a clean field.
- Follow the page's "More details of this race" link to `eventdetail.php?event=<id>` when the user
  asks for host town, start location, organizer, address, status, participant limit, course notes,
  or other event metadata.
- The page also surfaces view toggles (avg-speed unit km/h vs min/km, category scheme: German /
  international / event-specific, nation highlight). In practice, scrape the default view and
  compute derivations locally — the page URL params for these toggles are unstable.
- Some events bundle several races (e.g. 50k + 100k on the same day) under separate event IDs —
  resolve each via `searchevent.php` or `geteventlist.php` rather than guessing.

## `eventdetail.php` — event metadata/details

```
curl -s "https://statistik.d-u-v.org/eventdetail.php?event=111652&language=EN"
```

- `event=<id>` is the main param.
- Use this endpoint after `geteventlist.php`, `calendar.php`, `searchevent.php`, or
  `getresultevent.php` when the user needs fields beyond the result row.
- The stable metadata labels include **Date**, **Event**, **Start in (Country)**,
  **Length/Duration**, **Ranking eligible**, **IAU-Label**, **Status**, **Participants limit**,
  organizer/contact fields, and course details when available.
- `Start in (Country)` is the clean source for "host town" / "venue town" on past-event queries. Do
  not guess the town from the event name; some event names include sponsors, race formats, or series
  names rather than the actual start location.

## `geteventlist.php` — past-event browse/filter

```
curl -s "https://statistik.d-u-v.org/geteventlist.php?year=2024&country=HUN&dist=100km&language=EN"
```

Confirmed form field names (authoritative):

- `year` — 4-digit year, or `all`. Default = current year.
- `country` — IOC-3, or `all`.
- `dist` — shared `dist` vocabulary (`100km`, `24h`, `6d`, range codes `1`/`2`/`4`/`8`, …). No `+` or
  spaces.
- `surface` — **NOT `racetype`**. Values: see the race-surface vocabulary in
  [parameters.md](parameters.md) (`Road`, `Trail`, `Stage`, `Track`, `Indoo`, `Elim`, `Backy`,
  `Walk`, case-sensitive). Lowercase full words are not reliable.
- `label` — **NOT `iau`**. Values: omit (= all) or `Y` (= IAU-labelled). (Note: on
  `getintbestlist.php` the equivalent value is `IAU`, not `Y` — the two endpoints diverge here.)
- `from`, `to` — distance bounds in **kilometres** (text inputs in the form labelled "Length from X
  to Y km"), independent of the `dist` dropdown's range codes. `from=80&to=120` is valid and matches
  events in that km range. Omit either side for an open-ended bound. Time-based events (24h, 6d)
  won't match a km filter — for those use `dist=24h` etc. To filter on the dropdown's preset buckets
  instead, use `dist=1|2|4|8`.
- `sort` — `1` (Date — default) or `2` (Finishers). The form uses numeric values; passing the
  dropdown labels (`Date`, `Finishers`) silently falls back to default sort.
- `club` — optional filter by club (string, partial match).

Response: HTML table, one row per event, with `getresultevent.php?event=<id>` links. The list row has
date, event name, distance, finisher count, and IAU label; it does **not** include a separate
host-town column. If the user asks for town/venue/start location, follow each event ID to
`eventdetail.php?event=<id>` and read `Start in (Country)`. The default page size is up to 1000;
results beyond that require narrower filters.

## `calendar.php` — upcoming / future-race calendar

```
curl -s "https://statistik.d-u-v.org/calendar.php?year=futur&dist=6d&country=4&cups=0&rproof=0&mode=list&language=EN"
```

Use `calendar.php` — **not** `geteventlist.php` — whenever the user asks about upcoming, future, or
scheduled races. `geteventlist.php` is tuned for completed events with results; `calendar.php` is the
forward-looking view and exposes extra filters.

- `year` — `futur` (from today on), `past1` (1 year back), a specific 4-digit year (the dropdown
  offers 1990 through next year, e.g. `2026`, `2027`, `2014`), or `all`. Plain `past` is *not* a
  valid token.
- `country` — IOC-3 for a country, or numeric `1`–`6` for a continent (`1`=Europe, `2`=Asia,
  `3`=Africa, `4`=North America, `5`=South America, `6`=Oceania).
- `dist` — shared `dist` vocabulary; also accepts surface tokens (`Road`, `Trail`, …) in this slot.
- `cups` — numeric token: `0`=all, `1`=DUV-Cup, `2`=DUV-50km-Cup, `3`=DUV-6h-Cup, `4`=IAU-50k-Trophy,
  `5`=Championships, `6`=ECU, `7`=Anglo Celtic Plate. (The form shows names; the posted value is the
  numeric id.)
- `rproof` (ranking-eligible) — `0`=all, `1`=yes, `2`=no.
- `mode` — `list` (tabular) or `map`.
- `radius` — kilometers around a location; only meaningful together with the site's lat/lon context.
  Leave blank unless reproducing a user-supplied URL.
- `norslt=1` — "without result list": hide events that already have posted results (useful when
  combined with past years to find events that haven't published results yet). Omit for normal
  behaviour.

Result table columns: **Date | Event | Distance/Duration | Venue (Country) | Status | IAU-Label |
Results**. The "Results" column links to `getresultevent.php?event=<id>` for completed events;
pre-race / upcoming events link to `eventdetail.php?event=<id>` instead. Use `eventdetail.php` for
richer race metadata.

**Date windows need client-side filtering.** `calendar.php` has broad `year` modes but no exact
`from`/`to` date filters. For requests like "next 30 days", "next year", or "between June and
August", fetch a broad calendar set (`year=futur` or the relevant specific years), parse the row's
start date, and filter locally to the requested window. State the cutoff you used. `year=futur` means
"all future from today", not "the next 12 months".

Calendar dates can be single dates (`29.05.2026`) or ranges (`13.-14.06.2026`, `30.10.-02.11.2026`).
Use the start date for window filtering, and keep the raw DUV date string in the answer if the range
is awkward or appears inconsistent.

Result count is stated inline as `1 to N of M search results` — there is no pagination, so if `N < M`
you need to narrow filters. In practice the hard cap is the same 1000-row ceiling as elsewhere on the
site.

**Submit.x / Submit.y in pasted URLs.** When a user pastes a calendar URL from their browser you'll
often see `Submit.x=<n>&Submit.y=<n>` tacked on — those are the pixel coordinates of the click on the
form's image submit button and carry no filter meaning. Drop them when scripting; keeping them
doesn't hurt but adds noise.

## `getintbestlist.php` — international rankings

```
curl -s "https://statistik.d-u-v.org/getintbestlist.php?year=2024&dist=100km&gender=M&nat=HUN&language=EN"
```

Confirmed form field names:

- `year` — 4-digit, or `all` for the all-time list. The dropdown shows 2005 onward, but earlier years
  still parse and return data (sparser as you go back, e.g. ~120 women on 24h in 1990).
- `dist` — shared `dist` vocabulary (`100km`, `24h`, `6d`, …) **plus** `1000km`, `1000mi` which only
  appear here. No `+` or spaces.
- `nat` — **NOT `country`** (different param name, same value vocabulary as the country/nation
  section in [parameters.md](parameters.md)). `all` (or omit) for World; numeric `1`–`6` for
  continents (Europe=1, …, Oceania=6); IOC-3 country codes work even though they're not in the
  visible dropdown. The English labels (`World`, `Europe`, …) are *not* valid values.
- `gender` — `M` or `W`. (The form label reads "F" for the female list, but the posted value is `W`;
  `gender=F` silently returns zero rows.)
- `cat` — **NOT `AgeGrp`**. Age-group code, gender-prefixed: `all`, `MU23`/`WU23`, `M23`/`W23`,
  `M35`/`W35`, … up to `M90`/`W90`. Must match the `gender` value.
- `label` — omit for all events, or `IAU` for IAU-labelled only. (`Y` is the value on
  `geteventlist.php` but is silently dropped here. `IAU-Label` is the dropdown *text*, never the
  value.)
- `hili` (highlight) — overlay highlight for a country (IOC-3) or `none`/`GER`.
- `tt` (time type) — `netto` or `brutto`.
- `club` — optional club filter.

**Page cap on this endpoint is 4000 rows**, higher than the 1000-row cap elsewhere. The unfiltered
all-time list is around 15 000 entries, so you still need filters to see the tail.

**The response table is self-contained — don't re-fetch what's already there.** Each row carries:
rank, performance (distance or time), athlete name (linked to `getresultperson.php`), nation (IOC-3),
date of birth, age category, performance date, and **event name with venue town** (linked to
`getresultevent.php`). For "top-N" answers there is no need to follow each event link to
`eventdetail.php` — the venue and event name are already inline. Only drill down when the user asks
for a metadata field that the row doesn't carry (organizer, course notes, participant cap, etc.).

**`nat=` filters by athlete nationality, not race venue.** A query like `nat=1` (Europe) returns the
year's best performances by *European-passport athletes*, including ones run on non-European tracks
(e.g. a French runner setting a 24 h mark in Phoenix shows up in the Europe list). For "best
performances at events held in Europe", `nat=` is the wrong tool — fetch the worldwide list and
filter client-side by the venue / event country, or pull `geteventlist.php` for the year+continent
and aggregate from there. When the user's phrasing is ambiguous (e.g. "best women's 24 h in Europe"),
name the interpretation you picked and offer the other one.

**Multi-performance rows.** When an athlete has more than one ranking-eligible result in the year,
DUV adds secondary rows tagged like `(2)`, `(3)` after their primary entry. These dilate the visible
row count without adding distinct athletes — strip them before counting "top N runners" or you'll
under-report unique names.

## `getresultclub.php` — club view

```
curl -s "https://statistik.d-u-v.org/getresultclub.php?club=<name-or-id>&year=2024&language=EN"
```

Confirmed form field names — note the value vocabularies here look nothing like
`geteventlist.php`'s, and the param *names* are deceptive (`racetype` is not a surface filter,
`aktype` is not ranking-eligibility):

- `club` — partial match on club name (3–25 chars), or a club id if you already have one. The page
  has no separate "find a club" search — start by `searchrunner.php`-ing one of the club's runners
  and reading their profile, or call this endpoint with a partial name and pick from the results.
- `sname` — optional runner-name filter within the club.
- `year` — 2001–current, or `all`.
- `racetype` — **ranking-eligibility flag**, despite the name. Values: `''` (omit) for all races, `Y`
  for ranking-eligible only. There is **no surface filter** on this endpoint — to get a club's
  road/trail-only results you have to filter client-side after fetching.
- `aktype` — **age-category scheme**, despite the name. Values: `1` (Cat. german, default), `2`
  (Cat. internat.), `3` (event-specific). This only changes how rows are categorised in the
  displayed table; it does not filter the result set.
- `sort` — `1` (Runner, Start date — default) or `2` (Distance, Performance). String values
  (`Distance`, `Performance`, etc.) silently fall back to default.

## `bulk_search.php` — POST-only bulk lookup

Paste a list of names (tab/semicolon/comma/space-separated) into the textarea and configure column
mappings (surname, first name, gender, nationality, birth, age group, bib, DUVID). Supports a
reference discipline (50km, 50mi, 100km, 100mi, 6h, 12h, 24h, 48h, 6 days, Backyard) and
age-category scheme (international, German, French, Italian). Output is HTML; no documented CSV
export.

For scripted use, `getresultperson.php` + `searchrunner.php` per name is usually simpler than
automating the bulk form.

## Overview pages

`overview_intbestlist.php`, `overview_dtbestlist.php`, `overview_records.php`,
`overview_champions.php`, `overview_cups.php` are navigation hubs — static landing pages that link
into the filterable endpoints above. Follow the links rather than trying to parameterize them.

## RSS feeds

`latestresults_rss.php` and `xml/nextraces_rss.php` are the only structured-data endpoints on the
whole site. Useful for "what's new" checks.
