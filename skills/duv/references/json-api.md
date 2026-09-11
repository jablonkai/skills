# DUV JSON API (`json/m*.php`)

The endpoints that power DUV's mobile app. Undocumented but stable, public, and far easier to
consume than the HTML pages: no regex parsing, IDs are plain fields, and rankings are paginated
instead of capped. Prefer them for everything they cover; fall back to the HTML endpoints in
[endpoints.md](endpoints.md) only for the few pages with no JSON twin (`geteventlist.php`,
`getresultclub.php`, `recordsGER.php`, `bulk_search.php`, `getresulteventalltime.php`).

`scripts/duv.py` wraps all of these — read [../SKILL.md](../SKILL.md) for the subcommand list.
This file is for when you need a field the script doesn't surface, or want to call the API
directly.

## Conventions that apply to every endpoint

- Base: `https://statistik.d-u-v.org/json/`. Always add `language=EN` — the `nlsText` label
  dictionary and a few display strings are localised.
- Some responses start with a **UTF-8 BOM**. `json.loads` chokes on it; decode with `utf-8-sig`
  or strip `﻿` first (`jq` copes).
- **Bad parameter values return an empty 200 body** (0 bytes), not an error and not `[]`. An
  empty body means "fix your tokens", never "no data".
- Parameter names and value vocabularies are the same as the HTML forms — see
  [parameters.md](parameters.md). Nation is `nat` on rankings/records and `country` on the
  calendar, exactly like the HTML pages.
- Every list response embeds its own filter vocabularies (`FltDistValue`, `FltCountryValues`,
  `FltAgeCat`, …). When a token isn't listed here, fetch once and read the `Flt*` arrays.
- Most endpoints return a `nlsText` dict of UI labels — ignore it (`duv.py get` drops it).
- Dates are ISO `yyyy-mm-dd` (sometimes with a time) on most endpoints, but `dd.mm.yyyy` on
  `mbestperfcountry.php` and in `EvtDate`/`EvtdateShort` fields. Normalise before comparing.
- Numeric-looking fields are strings. `Privacy: "1"` marks runners who asked to be anonymised —
  respect it and don't try to de-anonymise.

## Endpoint summary

| Endpoint | Params | Returns | HTML twin |
|---|---|---|---|
| `msearchrunner.php` | `sname` | `HitCnt`, `Hitlist[]` of runners | `searchrunner.php` |
| `mgetresultperson.php` | `runner` | `PersonHeader`, `AllPerfs[]`, `AllPBs[]`, `CompTable[]` | `getresultperson.php` |
| `msearchevent.php` | `sname` | `HitCnt`, `Hitlist[]` of events (full metadata) | `searchevent.php` |
| `mgetresultevent.php` | `event` | `EvtHeader`, `Resultlist[]` | `getresultevent.php` |
| `meventdetail.php` | `event` | `raceDetails`, `editions[]`, `winnerList[]`, `gpsTracks[]` | `eventdetail.php` |
| `mgetintbestlist.php` | `year dist gender nat cat label page` | `Pagination`, `RankingList[]` | `getintbestlist.php` |
| `mbestperfcountry.php` | `nat dist type cat` | `Records{}` keyed by age group | `bestperfcountry.php` |
| `mcalendar.php` | `year country dist cups rproof` | `HitCnt`, `Races[]` | `calendar.php` |

No JSON exists for `geteventlist.php` (past-event browse) — but `mcalendar.php` accepts past
years and marks finished events with `Results: "C"`, which covers most "which 100 km races were
held in Hungary in 2024" questions. Its `dist` slot takes the same range codes and surface tokens.

## `msearchrunner.php`

```
json/msearchrunner.php?sname=Berces,Edit&language=EN
```

- `sname` — `Smith` matches `Smith*`; `Smith, John` matches `Smith*, *John*`. Greek, Cyrillic and
  Hebrew work; for CJK names write surname and given name without a separator.
- Hit: `PersonID, LastName, FirstName, OrigName, Club, City, Nationality, YOB, Gender (M/F),
  Privacy, ActivRange ("2013-2020")`. `ActivRange` is the quickest way to tell namesakes apart.
- Unlike the HTML page there is no redirect on a single hit — `HitCnt` is 1 and the ID is in the
  list.

## `mgetresultperson.php`

```
json/mgetresultperson.php?runner=5752&language=EN
```

- `PersonHeader` — `PersonName ("Berces, Edit"), DOB, DOBiso, NationalityShort, Club, Residence,
  CatINT, CatNAT, TotalEvtCnt, TotalKm, SearchRslts`.
- `AllPerfs[]` — one entry per year: `Year, EvtCnt, KmSum, PerfsPerYear[]`. Each performance:
  `EvtDate, EvtDateIso, EvtID, EvtName, EvtCity, EvtCountryCode, EvtType, EvtDist ("6h", "100km",
  "81km"), Perf ("57.765 km" / "7:25:21 h"), PerfNum, RankOverall, RankMW, Gender, Cat, RankCat`.
  This is the *only* place non-standard distances appear.
- `AllPBs[]` — list of single-key dicts `{"100km": {"PB": "7:25:21", "2011": {"Perf":..,
  "RankIntNat": " (91/1)"}, ...}}` — the PB per ranking-eligible distance plus the best per year
  with that year's international/national rank. Only distances the runner actually raced are
  present; never infer a 100 km PB from a 100 mi or a split.
- `CompTable[]` — per event the runner finished more than once: `EvtID, EvtName, EvtCnt` and a
  key per year with that year's time.

## `msearchevent.php`

```
json/msearchevent.php?sname=York,100,USA&language=EN
```

- `sname` — matches event name **or** town. `York,100,USA` narrows to 100 km/100 mi events in a
  town matching *York* in the USA (name, length, country — comma-separated, any subset in order).
- Hits carry the full `raceDetails` set (see `meventdetail.php`): `EventID, EventName, Edition,
  Startdate, Length, Duration, City, Country, EventType, IAULabel, RecordProof, PromOrg, URL …`,
  so a search result is usually enough without a detail call. Newest first.

## `mgetresultevent.php`

```
json/mgetresultevent.php?event=100580&language=EN
```

- `EvtHeader` — `EvtID, EventName, EvtDate, City, Country, EvtDistance ("54km trail race"),
  EvtDist, NormLen, EvtType, FinisherCnt ("334 (231 M, 103 F)"), RecordEligible, Resultsource,
  EvtDetailLink, AllTimeLink, MultFinishLink`.
- `Resultlist[]` — `RankTotal, Performance ("4:09:21 h"), PerformanceNumeric, PersonID,
  AthleteName ("Orolin, Pavol"), FirstName, LastName, Club, Nationality, YOB, DOB, Gender,
  RankMW, Cat, RankCat, Speed, AgeGradePerf`. Every finisher — big races run to thousands of rows
  in one response.
- Multi-race events (50 k + 100 k on the same day) are separate event IDs sharing a `ParentID`.

## `meventdetail.php`

```
json/meventdetail.php?event=100580&language=EN
```

- `raceDetails` — organizer/contact block (`PromOrg, Contact, Address, Phone, Email, URL`),
  `Startdate, Enddate, Length, Duration, AltitudeDiff, City, Country, CountryName, CourseDesc,
  TimeLimit, FieldLimit, Fee, IAULabel (N/B/S/G), RecordProof (Y/N), FinisherM, FinisherW,
  Results (C = complete, P = partial, N = none), Future`. `City`+`Country` is the host town — do not
  guess it from the event name.
- `editions[]` — every edition of the same series with its own `EventID`, date, finishers and
  `Results` flag: the cheap way to walk a race's history.
- `winnerList[]` — `Winner_M`, `Winner_W` per edition.
- `gpsTracks[]`, `raceReports[]` — linked GPX/KML and reports when present.

## `mgetintbestlist.php` — rankings, paginated

```
json/mgetintbestlist.php?year=2024&dist=100km&gender=W&nat=HUN&language=EN&page=1
```

- Params as the HTML form: `year` (4-digit or `all`), `dist`, `gender` (`M`/`W`), `nat`
  (`all`, `1`–`6`, IOC-3), `cat` (`M40`, `WU23` … matching `gender`), `label=IAU`,
  `tt=netto|brutto` (time type, default `netto`).
- **Ranking times can differ by a few seconds from the same performance on the event result list
  or the records page**, which show the `brutto` time. Pass `tt=brutto` when cross-checking
  against those pages; either way say which one you quoted.
- **400 rows per page.** `Pagination: {CurrPage, MaxPage, PageSize, NextPageURL}` — loop `page=`
  up to `MaxPage`. The all-time men's 100 km list is ~38 pages. There is no 1000/4000 cap here.
- Row: `Rank, Perf (" 7:56:15 h"), Time, Distance, PersonID, FirstName, LastName, Nationality,
  DOB_Display, CatInt, CatRank, Startdate (ISO), EvtdateShort, EventID, City, Country, EventType,
  IAULabel, AgeGradePerf, AgeGradePct`.
- Secondary results of the same athlete come as `Rank: "(2)"`, `"(3)"` … — strings in parentheses.
  Drop them when counting distinct athletes.
- `nat` filters by **athlete nationality**, not venue — filter `Country` client-side for
  "performances run in X".

## `mbestperfcountry.php` — records

Covered in full in [records.md](records.md).

## `mcalendar.php`

```
json/mcalendar.php?year=2024&country=HUN&dist=100km&language=EN
```

- `year` — 4-digit, `futur`, `past1`, `all`. `country` — IOC-3 or continent `1`–`6`, `all`.
  `dist` — distance token, range code `1/2/4/8`, or surface `Road/Trail/Stage/Track/Indoo/Elim/
  Backy/Walk`. `cups` `0`–`7`, `rproof` `0/1/2` as on the HTML form.
- `Races[]` — `EventID, ParentID, EventName, Edition, City, Country, EventType (numeric, see
  `FltEventTypes` for labels: 1 road, 2 trail, 3 road loop <5 km, 4 stage, 5 track, 6 indoor …),
  Length, Duration, RecordProof, IAULabel, Results (C/P/N), Startdate, Enddate, Cupname`.
- `HitCnt` vs `len(Races)` — when they differ, the list was truncated; narrow the filters.
- No date-range parameters: fetch the year and filter `Startdate` locally for "next 30 days".
