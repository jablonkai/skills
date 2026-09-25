# DUV records: national, continental, German — and why there is no "world" list

DUV publishes *best performances*, not ratified records. Every records page carries the
disclaimer that the national federation (or the IAU) approves records, DUV only lists the best
performance in its database. Say so when you report a "national record" from here — the number
is usually right, but a runner's result can be missing, unratified, or run on a course that the
federation doesn't accept. For an official world record, go to the IAU.

## Which source for which question

| Question | Source |
|---|---|
| National record / best performance for country X at distance D | `records --nat X --dist D` → `json/mbestperfcountry.php` |
| Same, per age group (M40, W55 …) | same call — every age group is in one response |
| Continental best (Europe, Asia …) | `records --nat 1..6 --dist D` (1=Europe, 2=Asia, 3=Africa, 4=N. America, 5=S. America, 6=Oceania) |
| Road-only / track-only / indoor-only bests | add `--type road` / `track` / `indoor` |
| German records (official DLV/DUV list) | `recordsGER.php?dist=D` (HTML only, both genders) |
| World record | not on DUV — IAU records table at `https://iau-ultramarathon.org/iau-records.html` (PDFs linked from `overview_records.php`) |
| "Best ever performance in the world" (unofficial, incl. non-ratified) | `rankings --year all --dist D --gender G` — the first row of the all-time list |
| Record *progression* / who held it before | not exposed — fetch the all-time ranking and sort by date client-side |
| Course record of one event | `getresulteventalltime.php?event=<id>` (HTML) — all-time list for that event |

`nat=all` on the records endpoint returns nothing: the endpoint has no world scope, by design.

## `json/mbestperfcountry.php` — the records endpoint

```
https://statistik.d-u-v.org/json/mbestperfcountry.php?nat=HUN&dist=100km&type=0&cat=DOB&language=EN
```

| Param | Values | Notes |
|---|---|---|
| `nat` | IOC-3 (`HUN`, `GER`, `USA` …) or continent `1`–`6` | Uppercase. Lowercase still filters but the page heading loses the country name. No `all`. |
| `dist` | `50km` `50mi` `100km` `100mi` `1000km` `1000mi` `6h` `12h` `24h` `48h` `6d` | Exactly these eleven tokens; anything else (`6days`, `100+km`, `72h`) returns an **empty body**. |
| `type` | `0` overall (default), `1` road, `2` track, `3` indoor | Surface filter. |
| `cat` | `DOB` or `YOB` | Age-group scheme — see below. Omitted = `YOB`. |

There is **no `gender` parameter** — every response carries both genders. Filter client-side on
the first letter of the age-group key.

### Age-group schemes

- `cat=DOB` — **IAU / international** groups, age on race day: `WOverall WU23 W23 W35 W40 … W90`
  and the `M` mirror. Use this for anything international or when the user says "masters",
  "age group", "W45" etc. without further context.
- `cat=YOB` — **German** scheme by year of birth: `WU20 W20 W30 W35 W40 …`. Same overall row,
  different young/veteran cut-offs, so the U23 / 23 / 30 rows differ between the two schemes.

Age-group rows are *not* independent of the overall row: the overall best also appears under the
age group the athlete was in on that day, and the same athlete can hold several groups.

### Response shape

```json
{"HitCnt": 25,
 "TitleW": "Best Performances 100 km  women for HUN",
 "TitleM": "Best Performances 100 km  men for HUN",
 "Disclaimer": "Please note: This is not an official record list ...",
 "Records": {
   "WOverall": {"AK": "WOverall", "Perf": "07:25:21", "PerfID": "...", "PersonID": "5752",
                "FirstName": "Edit", "LastName": "Berces", "DOB": "16.05.1964", "YOB": "1964",
                "Club": "", "Nat": "HUN", "EventID": "2345", "Eventname": "IAU 100km WC Winschoten",
                "City": "Winschoten", "Country": "NED", "Startdate": "09.09.2000",
                "Enddate": "00.00.0000", "Split": ""},
   "WU23": {...}, "W23": {...}, ..., "MOverall": {...}, "MU23": {...}, ...}}
```

- `Records` is a dict keyed by age group, in W-then-M order. A group with no performance is
  simply absent (small countries have gaps).
- `Perf` is `h:mm:ss` for fixed distances and kilometres (`250.106`) for timed events.
- `Split` is a letter code, up to three letters: `S` = split time/distance recorded inside a longer
  race (e.g. a 100 km split of a 24 h), `T` = track, `I` = indoor. A split is *not* a stand-alone
  race result, which matters when the user wants records set in dedicated races.
- `Club` is free text as entered with the result — prefixes like `(NR)` are part of the club
  string, not a DUV marker.
- `PerfID` identifies the single performance; `EventID` → `getresultevent.php` (HTML; the JSON twin needs a login),
  `PersonID` → `json/mgetresultperson.php`.

## Bulk download with the shipped script

`scripts/duv.py records` loops nat × dist, flattens `Records` into one row per age group and
tags each row with `nat`, `dist`, `type`, `scheme`, `gender`, `cat`. The site itself shows only
one country × one distance per page, so this is the practical way to answer "all Hungarian
records", "Europe's 24 h track bests by age group", or "compare the women's 100 km record across
V4 countries":

```bash
duv.py records --nat HUN --dist all                       # everything for one country
duv.py records --nat HUN --dist all --overall-only --format md   # just the open records
duv.py records --nat HUN --nat SVK --nat CZE --nat POL --dist 100km --gender W --overall-only
duv.py records --nat 1 --dist 24h --type track --cat YOB --out europe-24h-track.csv
duv.py records --nat GER --dist 6d --format json          # raw payload, disclaimer included
```

`--dist all` is eleven requests per country at the default 0.5 s spacing.

## `recordsGER.php` — official German records (HTML only)

```
https://statistik.d-u-v.org/recordsGER.php?dist=100km&language=EN
```

`dist` accepts `50km 100km 6h 12h 24h 48h 6d`. Table layout matches the records page
(`Cat | Performance | flag | Name | DOB | Club | Date | Venue (Country)`), women first, men second,
German age groups. There is no JSON counterpart; a frozen 2016 PDF split by surface is linked from
`overview_records.php`. Unlike `bestperfcountry.php`, this list *is* the DUV-maintained German
record list, so the "not official" caveat does not apply.

## Reporting records well

- Name the scope you used: country/continent, distance, surface (`type`), age scheme, and whether
  splits were included. Two people asking for "the Hungarian 100 km record" may want the road-only
  non-split figure or the overall best — if it matters, show both rows.
- Quote DUV's disclaimer in one short sentence for national/continental lists.
- The records page and event result lists show the *brutto* time; the rankings default to
  *netto* and can be a few seconds off for the same performance (e.g. 7:43:52 vs 7:43:55).
  Prefer the records endpoint for a record value, and don't treat the gap as a data error.
- Dates come as `dd.mm.yyyy` on this endpoint (ISO `yyyy-mm-dd` on most other JSON endpoints) —
  normalise before sorting or comparing across endpoints.
- `Startdate` is the race start; `Enddate` (`00.00.0000` when absent) is the finish. The HTML
  records page and the rankings print the **end** date for timed races — so a 24 h that started
  on 18.10 shows as 19.10 there. Quote both, or say which one you mean, for 24 h+ records.
