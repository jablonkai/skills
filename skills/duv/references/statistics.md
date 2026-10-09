# DUV statistics, championships and cups (HTML only)

The pages linked from **Summary**, **Championships**, **Cups** and **German rankings** in the
site menu. None has a JSON twin. `duv.py stats`, `duv.py champions`, `duv.py multiple-finishers`
and `duv.py event-list` scrape the common ones into CSV. Use `fetch` plus a parser for the rest.
Every page takes `language=EN`. An unknown token gives an empty table, not an error.

Contents: [Statistics pages](#statistics-pages-duvpy-stats-kind) ·
[Summary page](#summaryphp--counts-per-country-and-year) ·
[Championships](#championships-duvpy-champions) · [Cups](#cups) ·
[German lists](#german-lists) · [Per-event pages](#per-event-pages)

## Statistics pages (`duv.py stats <kind>`)

`country` here means the **runner's nationality** (IOC-3, continent `1`–`6`, or `all`). The
exceptions are `long-running-races`, where it is the venue country, and `top-abroad`, where it
is the runner's nation and the races are held outside it.

| `kind` → page | Filters | Columns / meaning |
|---|---|---|
| `lifetime-mileage` → `lifetimemileage.php` | `country gender` | rank, name, yob, gender, nat, time_span ("2007 - 2026"), years, events, km, km_year, km_race. Lifetime ultra km. **Top 2000 only.** |
| `year-km` → `yearkm.php` | `country year gender` | rank, name, yob, gender, nat, year, count, km_year. Ultra km in one year. `year=all` ranks the best single years ever. **Top 1000.** |
| `oldest-finishers` → `oldestfinishers.php` | `country year gender` | rank, age_years_days ("87 y, 019 d"), last_finish, name, gender, yob, nat. The oldest age at which each runner finished an ultra. |
| `timespan` → `timespan.php` | `country type years` | Longest span between two ultras. `type`: `1` wins, `2` finishes ≥160 km, `3` ≥100 km, `4` ≥80 km, `5` ≥45 km. `years`: minimum span (`20`,`25`…`45`). `date/km/event` is the **latest** race and `date_2/km_2/event_2` the **earliest**. |
| `female-winners` → `femalewinners.php` | `country year dist` | Races a woman won **outright**: name, yob, nat, date, event, country, length, performance. `dist` also takes `Stage`. |
| `top-abroad` → `toprankabroad.php` | `country year dist gender cnt` | Results of country X's runners at races held abroad. `cnt`: `1` wins, `3` podiums, `10` top-10, `10000` all. Columns: group (month), date, event, distance, rank, rank_gender, finishers_m/f, name, performance. |
| `long-running-races` → `longrunningraces.php` | `country dist` | Race series by number of editions: count, event, country, distance, time_span. Links go to `eventdetail.php`. |
| `100x100mi` → `100x100miclub.php` | `country gender` | Runners with 100+ finishes of ≥100 mi, then "aspirants" (80+). The table has no person links. |
| `doping` → `doping.php` | `country gender` | Suspended athletes, with the suspension and the disqualified period in free text (sometimes in German). |

The `dist` filter on these pages uses the shared vocabulary in [parameters.md](parameters.md).
`top-abroad` and `long-running-races` also accept range codes `1/2/4/8` and the surface
tokens.

## `summary.php` — counts per country and year

`summary.php?country=HUN` holds four aggregate blocks. They are drawn as bar charts and tables,
so parse them yourself:

- **Count of runners by nation**: all runners in the database (M/F) and those active last year.
- **Count of performances by runners with nationality X**: per year, the performances, persons,
  performances per runner for men and women, M:F ratio, and totals. This is the answer to
  "how many Hungarian ultra runners were there in 2019?".
- **Count of performances by distance in races in X**: by venue country.
- **Count of races by distance**: per year.

`country=ALL` gives worldwide totals. The page also links to all the statistics pages above.

## Championships (`duv.py champions`)

`championsIAU.php?dist=<code>&cnt=1|3|10`: every edition, newest first. Each edition has a
`Date:` / `Event:` / `Finishers:` block and then the top N men and women.

| `dist` | Championship |
|---|---|
| `100kmWC` / `100kmEC` / `100kmAC` | IAU 100 km World / European / Asian Championships |
| `24hWC` / `24hEC` / `24hAC` | IAU 24 h World / European / Asia-Oceania Championships |
| `TrailWC` | IAU Trail World Championships |
| `50kmWC` | IAU 50 km World Championships |

`rank` is the overall place. `rank_gender` is the medal position, so women's winners show
`rank_gender=1` with an overall rank like `23`. Count medals by `rank_gender ≤ 3`.

`championsGER.php?dist=…&cat=…&cnt=…` (`--ger`) lists German championships: `50km`,
`50km Track`, `100km`, `100km Track`, `6h`, `24h`, `Ultratrail`. The `cat` age groups are
`all`, `JUN`, `20`, `35` … `90`. Other national championships are not collected on one page: use
`calendar --year 2024 --cupname "NC"` (the race's `Cupname`, e.g. `NC 24h Hungary`), or search by
event name ("HUN Championship", "országos bajnokság"). The JSON calendar ignores `--cups`.

## Cups

| Page | Content |
|---|---|
| `duvcups19.php?year=Y&gender=M\|W` | DUV-Cup from 2019 on: points table per runner and race |
| `duvcups14-18.php?…`, `duvcups05-13.php?dist=50km&year=Y&gender=G` | Earlier DUV-Cup seasons (the old pages also have a 50 km cup) |
| `cups_ecu.php?year=2004..2009&gender=G` | European Challenge of Ultrarunning (ECU), 2004–2009 only |
| `bundesliga2020.php?year=Y` (also `…2015/2017/2018.php`) | German ultra team league |

Cup tables have one column per race, so their width changes from year to year. Read the
header row before mapping columns. `calendar --year Y --cupname DUV-Cup` lists the races that count for a cup.

## German lists

- `getdtbestlist.php?dist=&year=&gender=&label=IAU`: the German national ranking (DUV's own),
  for `50km 100km 100mi 6h 12h 24h 48h 6d`. Same columns as the international list. Secondary
  results show as `(2)`.
- `alltimebestGER.php?dist=&gender=`: German all-time list (`50km 100km 6h 12h 24h 48h 6d`).
- `recordsGER.php?dist=`: official German records, described in [records.md](records.md).

For any country other than Germany, use the international list with `nat=XXX`.

## Per-event pages

- `multiplefinish.php?event=<id>&gender=all|M|W` (`duv.py multiple-finishers`): runners ranked
  by finishes of that race series, with count, years and best–worst time range.
- `getresulteventalltime.php?event=<id>`: the "all-time list" link is still on every result
  page, but the server answers **404** (checked 2026-10). Use `duv.py event-history`, which gets
  the course record from the winners of every edition, or fetch the editions' result lists and
  merge them.
- `eventdetail.php` / `json/meventdetail.php`: also has `valuation` (runner ratings of the race)
  and `LinkURLs`, besides the fields in [json-api.md](json-api.md).
