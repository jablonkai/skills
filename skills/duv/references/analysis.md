# Answering analytical questions from DUV data

DUV answers lookups directly, but many real questions combine several calls. This file maps
common question types to a recipe. Each recipe names its source, its limits, and how to word
the answer. Run every command from the skill directory.

## Recipes

| Question | Recipe |
|---|---|
| "Who has the course record at race X?" | `event-history --id <any edition>`. It takes the best **winning** time per gender per course length. Editions with different lengths are kept apart. Trail courses change even when the nominal length stays the same, so say "fastest winning time on the 54 km course" rather than "record" when the course has been rerouted. |
| "How has race X developed?" | `event-history`: finishers per edition (M/W), winners, cancelled years (0 finishers, `results` not `C`). |
| "Who has finished race X most often?" | `multiple-finishers --id <id>` |
| "How did the Hungarian 24 h record develop?" | `progression --nat HUN --dist 24h --gender W`. It replays the all-time ranking by date and keeps each new best. **Limits:** only ranking-eligible results (no splits, no trail), and a performance missing from DUV is missing from the history. The records page can show a better split value. Mention both if they differ. |
| "World best progression" | `progression --dist 100km --gender M` (nat defaults to `all`) |
| "Masters record history" | `progression … --cat W50`. Note that the age group is the one on race day. |
| "A vs B: who's better?" | `head-to-head --runner A --runner B` for the shared races and who finished ahead. Then `runner --id` for both to compare PBs per distance. Mention the ranking-year context (`AllPBs` carries the int/nat rank per year). |
| "A runner's career / form curve" | `runner --id … --format json`. Group `AllPerfs` by year (`EvtCnt`, `KmSum`) and by distance. `CompTable` already gives per-race year-by-year times. |
| "Who ran the most km in 2025 (Hungary)?" | `stats year-km --country HUN --year 2025` |
| "Lifetime ultra km leaders" | `stats lifetime-mileage --country HUN` |
| "Oldest finisher / longest career" | `stats oldest-finishers`, `stats timespan --type 2 --years 30` |
| "Women who won races outright" | `stats female-winners --country HUN --year 2024` (`country` = runner nationality) |
| "Hungarians' wins/podiums abroad this year" | `stats top-abroad --country HUN --year 2025 --cnt 1` (or `3`) |
| "Oldest / longest-running races in X" | `stats long-running-races --country HUN` |
| "IAU world championship medallists" | `champions --dist 24hWC --cnt 3`. Count medals per nation by `nat` with `rank_gender ≤ 3`. |
| "Hungarian championship races in 2024" | `calendar --year 2024 --cupname "Hungary"` (national championships carry `Cupname` `NC <dist> <country>`; shared ones read e.g. `NC 24h Serbia & Hungary`) |
| "Biggest races in X" | `event-list --year 2025 --country HUN --sort finishers` |
| "Races 80–120 km in Hungary in 2024" | `event-list --year 2024 --country HUN --from 80 --to 120` |
| "How many runners / performances per year" | `summary.php?country=HUN` (see [statistics.md](statistics.md)) |
| "Was runner X suspended?" | `stats doping --country X`. Report only what DUV lists, with its date range. |
| "Best age-graded performances" | `rankings` rows carry `age_graded` (performance converted with DUV's age factors). Sort on it client-side. Say that it is DUV's age grading. |
| "What is the level of a race?" | `search-event` / `event-detail`: `IAULabel` (N none, B bronze, S silver, G gold), `RecordProof` (Y = ranking-eligible), finisher counts, altitude difference |

## Domain notes for good answers

- **Ranking-eligible ("record proof")** events are the measured road, track and indoor courses
  and the timed events. Only these feed the rankings, PBs and records. Trail, stage and most
  backyard results are in the database but are never ranked. So "best 100 km" ignores a
  100 km trail race, and you should say so when the user's runner mostly runs trails.
- **Fixed-distance vs fixed-time.** For 50 km, 100 km and 100 mi a lower time is better. For
  6 h, 12 h, 24 h, 48 h and 6 days, more km is better. Backyard results appear as hours
  (`51h`) in event lists and as km in performances. A backyard winner is the last runner left,
  so km here measure laps survived, not speed.
- **Splits.** DUV files an intermediate time (the 100 km split of a 24 h, the 50 km split of a
  100 km) as its own event with "Split" in the name. These splits can hold national records
  (`S` flag) but are not stand-alone races. `head-to-head` leaves them out unless `--splits` is
  given.
- **netto vs brutto.** Rankings default to netto (chip) time, while event results and records
  show brutto (gun) time. The two can differ by a few seconds. `progression` asks for brutto, so
  it matches the records page.
- **Age groups.** IAU groups use the age on race day (`W35` = 35–39). German `YOB` groups use
  the year of birth. A runner's `cat` in a row is the group on that day, not today.
- **Names.** DUV stores names as `Surname, Given` without diacritics in most fields, and keeps
  the original spelling in `OrigName` or the hidden span. Search without accents if the first
  search finds nothing. For a double surname, try each part.
- **Coverage.** DUV is volunteer-maintained and strongest for Europe, Japan and North America.
  Small or recent races can be missing or added weeks late (`whatsnew.php`,
  `xml/latestresults_rss.php`). Before saying "never finished a race", check that the race
  itself is in DUV.

## Wording

State the source and the scope in one line, for example: *"Source: DUV, ranking-eligible
results only, as of 2026-10-10."* Always give the DUV IDs or links
(`https://statistik.d-u-v.org/getresultperson.php?runner=<id>`) so the user can check. For
derived views (course record from winners, progression from the ranking), say that the result
is derived, and how.
